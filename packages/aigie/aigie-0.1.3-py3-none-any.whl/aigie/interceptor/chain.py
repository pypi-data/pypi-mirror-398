"""
InterceptorChain - Orchestrates pre-call and post-call hooks for LLM interception.

The chain manages ordered lists of hooks and executes them with proper
priority ordering, short-circuit logic, and backend consultation when needed.
"""

import asyncio
import logging
import time
from typing import Optional, List, Callable, Any, Dict, TYPE_CHECKING
from dataclasses import dataclass, field

from .protocols import (
    InterceptionDecision,
    InterceptionContext,
    PreCallResult,
    PostCallResult,
    PreCallHook,
    PostCallHook,
    FixAction,
    InterceptionBlockedError,
)

if TYPE_CHECKING:
    from ..client import Aigie
    from ..realtime.connector import BackendConnector
    from ..rules.engine import LocalRulesEngine

logger = logging.getLogger("aigie.interceptor")


@dataclass
class HookEntry:
    """Entry in the hook chain with priority."""

    hook: Any  # PreCallHook or PostCallHook
    priority: int
    name: str
    enabled: bool = True


class InterceptorChain:
    """
    Orchestrates pre-call and post-call hooks for LLM interception.

    The chain executes hooks in priority order (lower = earlier) and
    handles decision routing between local rules and backend consultation.

    Features:
    - Priority-based hook ordering
    - Short-circuit on BLOCK decisions
    - Automatic backend consultation for CONSULT decisions
    - Aggregation of modifications from multiple hooks
    - Performance tracking (latency per hook)
    - Graceful fallback on errors
    """

    def __init__(
        self,
        aigie_client: Optional["Aigie"] = None,
        rules_engine: Optional["LocalRulesEngine"] = None,
        backend_connector: Optional["BackendConnector"] = None,
        local_timeout_ms: float = 5.0,
        backend_timeout_ms: float = 500.0,
        enable_backend_consultation: bool = True,
    ):
        """
        Initialize the interceptor chain.

        Args:
            aigie_client: Reference to the Aigie client for API calls
            rules_engine: Local rules engine for fast decisions
            backend_connector: Connector for real-time backend consultation
            local_timeout_ms: Timeout for local hook execution (default: 5ms)
            backend_timeout_ms: Timeout for backend consultation (default: 500ms)
            enable_backend_consultation: Whether to consult backend for CONSULT decisions
        """
        self._aigie = aigie_client
        self._rules_engine = rules_engine
        self._backend_connector = backend_connector
        self._local_timeout_ms = local_timeout_ms
        self._backend_timeout_ms = backend_timeout_ms
        self._enable_backend_consultation = enable_backend_consultation

        self._pre_hooks: List[HookEntry] = []
        self._post_hooks: List[HookEntry] = []

        # Statistics
        self._stats = {
            "pre_calls": 0,
            "post_calls": 0,
            "blocks": 0,
            "modifications": 0,
            "backend_consultations": 0,
            "errors": 0,
            "total_latency_ms": 0.0,
        }

    def set_aigie_client(self, client: "Aigie") -> None:
        """Set the Aigie client reference."""
        self._aigie = client

    def set_rules_engine(self, engine: "LocalRulesEngine") -> None:
        """Set the local rules engine."""
        self._rules_engine = engine

    def set_backend_connector(self, connector: "BackendConnector") -> None:
        """Set the backend connector for real-time consultation."""
        self._backend_connector = connector

    def add_pre_hook(
        self,
        hook: PreCallHook,
        priority: Optional[int] = None,
        name: Optional[str] = None,
    ) -> None:
        """
        Add a pre-call hook to the chain.

        Args:
            hook: The hook to add (must implement PreCallHook protocol)
            priority: Override priority (default: use hook.priority)
            name: Override name (default: use hook.name)
        """
        entry = HookEntry(
            hook=hook,
            priority=priority if priority is not None else getattr(hook, "priority", 50),
            name=name or getattr(hook, "name", hook.__class__.__name__),
        )
        self._pre_hooks.append(entry)
        self._pre_hooks.sort(key=lambda e: e.priority)
        logger.debug(f"Added pre-call hook: {entry.name} (priority: {entry.priority})")

    def add_post_hook(
        self,
        hook: PostCallHook,
        priority: Optional[int] = None,
        name: Optional[str] = None,
    ) -> None:
        """
        Add a post-call hook to the chain.

        Args:
            hook: The hook to add (must implement PostCallHook protocol)
            priority: Override priority (default: use hook.priority)
            name: Override name (default: use hook.name)
        """
        entry = HookEntry(
            hook=hook,
            priority=priority if priority is not None else getattr(hook, "priority", 50),
            name=name or getattr(hook, "name", hook.__class__.__name__),
        )
        self._post_hooks.append(entry)
        self._post_hooks.sort(key=lambda e: e.priority)
        logger.debug(f"Added post-call hook: {entry.name} (priority: {entry.priority})")

    def remove_pre_hook(self, name: str) -> bool:
        """Remove a pre-call hook by name. Returns True if found and removed."""
        for i, entry in enumerate(self._pre_hooks):
            if entry.name == name:
                del self._pre_hooks[i]
                logger.debug(f"Removed pre-call hook: {name}")
                return True
        return False

    def remove_post_hook(self, name: str) -> bool:
        """Remove a post-call hook by name. Returns True if found and removed."""
        for i, entry in enumerate(self._post_hooks):
            if entry.name == name:
                del self._post_hooks[i]
                logger.debug(f"Removed post-call hook: {name}")
                return True
        return False

    def enable_hook(self, name: str, enabled: bool = True) -> bool:
        """Enable or disable a hook by name. Returns True if found."""
        for entry in self._pre_hooks + self._post_hooks:
            if entry.name == name:
                entry.enabled = enabled
                logger.debug(f"{'Enabled' if enabled else 'Disabled'} hook: {name}")
                return True
        return False

    async def pre_call(self, ctx: InterceptionContext) -> PreCallResult:
        """
        Execute pre-call hooks on the context.

        Hooks are executed in priority order. The chain short-circuits on:
        - BLOCK: Request is blocked, no further hooks run
        - CONSULT: Backend is consulted before continuing

        MODIFY decisions are aggregated - all modifications are applied.
        DEFER decisions continue to the next hook.
        ALLOW from all hooks means the request proceeds.

        Args:
            ctx: The interception context with request information

        Returns:
            Aggregated PreCallResult with final decision and modifications
        """
        start_time = time.perf_counter()
        self._stats["pre_calls"] += 1

        # Compute context hash for drift detection
        ctx.context_hash = ctx.compute_context_hash()

        # First, run local rules engine if available
        if self._rules_engine:
            try:
                rules_result = await self._run_rules_engine(ctx)
                if rules_result.decision == InterceptionDecision.BLOCK:
                    self._stats["blocks"] += 1
                    return rules_result
                if rules_result.decision == InterceptionDecision.CONSULT:
                    # Rules engine says we need backend
                    backend_result = await self._consult_backend_pre_call(ctx)
                    if backend_result:
                        return backend_result
            except Exception as e:
                logger.warning(f"Rules engine error: {e}")
                self._stats["errors"] += 1

        # Run hooks in priority order
        aggregated_messages = None
        aggregated_kwargs = None
        all_fixes: List[FixAction] = []
        total_latency = 0.0

        for entry in self._pre_hooks:
            if not entry.enabled:
                continue

            try:
                hook_start = time.perf_counter()
                result = await asyncio.wait_for(
                    entry.hook(ctx),
                    timeout=self._local_timeout_ms / 1000.0,
                )
                hook_latency = (time.perf_counter() - hook_start) * 1000
                total_latency += hook_latency
                result.latency_ms = hook_latency
                result.hook_name = entry.name

                if result.decision == InterceptionDecision.BLOCK:
                    self._stats["blocks"] += 1
                    result.latency_ms = total_latency
                    return result

                if result.decision == InterceptionDecision.CONSULT:
                    # Consult backend
                    backend_result = await self._consult_backend_pre_call(ctx)
                    if backend_result:
                        if backend_result.decision == InterceptionDecision.BLOCK:
                            self._stats["blocks"] += 1
                            return backend_result
                        if backend_result.modified_messages:
                            aggregated_messages = backend_result.modified_messages
                        if backend_result.modified_kwargs:
                            aggregated_kwargs = {
                                **(aggregated_kwargs or {}),
                                **backend_result.modified_kwargs,
                            }
                        all_fixes.extend(backend_result.fixes_applied)

                if result.decision == InterceptionDecision.MODIFY:
                    self._stats["modifications"] += 1
                    if result.modified_messages:
                        aggregated_messages = result.modified_messages
                    if result.modified_kwargs:
                        aggregated_kwargs = {
                            **(aggregated_kwargs or {}),
                            **result.modified_kwargs,
                        }
                    all_fixes.extend(result.fixes_applied)

                # ALLOW and DEFER continue to next hook

            except asyncio.TimeoutError:
                logger.warning(f"Pre-call hook {entry.name} timed out")
                self._stats["errors"] += 1
            except Exception as e:
                logger.error(f"Pre-call hook {entry.name} error: {e}")
                self._stats["errors"] += 1

        # All hooks passed - determine final result
        total_latency = (time.perf_counter() - start_time) * 1000
        self._stats["total_latency_ms"] += total_latency

        if aggregated_messages or aggregated_kwargs or all_fixes:
            return PreCallResult(
                decision=InterceptionDecision.MODIFY,
                modified_messages=aggregated_messages,
                modified_kwargs=aggregated_kwargs,
                fixes_applied=all_fixes,
                latency_ms=total_latency,
            )

        return PreCallResult(
            decision=InterceptionDecision.ALLOW,
            latency_ms=total_latency,
        )

    async def post_call(self, ctx: InterceptionContext) -> PostCallResult:
        """
        Execute post-call hooks on the context.

        Hooks are executed in priority order. The chain handles:
        - MODIFY: Apply modifications to the response
        - CONSULT: Backend is consulted for fixes
        - Retry requests: If a hook requests retry, return that

        Args:
            ctx: The interception context with response information

        Returns:
            Aggregated PostCallResult with final decision and modifications
        """
        start_time = time.perf_counter()
        self._stats["post_calls"] += 1

        # Run hooks in priority order
        modified_response = None
        modified_content = None
        all_fixes: List[FixAction] = []
        should_retry = False
        retry_kwargs = None
        total_latency = 0.0

        for entry in self._post_hooks:
            if not entry.enabled:
                continue

            try:
                hook_start = time.perf_counter()
                result = await asyncio.wait_for(
                    entry.hook(ctx),
                    timeout=self._local_timeout_ms / 1000.0,
                )
                hook_latency = (time.perf_counter() - hook_start) * 1000
                total_latency += hook_latency
                result.latency_ms = hook_latency
                result.hook_name = entry.name

                if result.decision == InterceptionDecision.CONSULT:
                    # Consult backend for fixes
                    backend_result = await self._consult_backend_post_call(ctx)
                    if backend_result:
                        if backend_result.modified_response:
                            modified_response = backend_result.modified_response
                        if backend_result.modified_content:
                            modified_content = backend_result.modified_content
                        all_fixes.extend(backend_result.fixes_applied)
                        if backend_result.should_retry:
                            should_retry = True
                            retry_kwargs = backend_result.retry_kwargs

                if result.decision == InterceptionDecision.MODIFY:
                    self._stats["modifications"] += 1
                    if result.modified_response:
                        modified_response = result.modified_response
                    if result.modified_content:
                        modified_content = result.modified_content
                    all_fixes.extend(result.fixes_applied)

                if result.should_retry:
                    should_retry = True
                    retry_kwargs = result.retry_kwargs or retry_kwargs

            except asyncio.TimeoutError:
                logger.warning(f"Post-call hook {entry.name} timed out")
                self._stats["errors"] += 1
            except Exception as e:
                logger.error(f"Post-call hook {entry.name} error: {e}")
                self._stats["errors"] += 1

        # Determine final result
        total_latency = (time.perf_counter() - start_time) * 1000
        self._stats["total_latency_ms"] += total_latency

        if should_retry:
            return PostCallResult(
                decision=InterceptionDecision.RETRY,
                should_retry=True,
                retry_kwargs=retry_kwargs,
                fixes_applied=all_fixes,
                latency_ms=total_latency,
            )

        if modified_response or modified_content or all_fixes:
            return PostCallResult(
                decision=InterceptionDecision.MODIFY,
                modified_response=modified_response,
                modified_content=modified_content,
                fixes_applied=all_fixes,
                latency_ms=total_latency,
            )

        return PostCallResult(
            decision=InterceptionDecision.ALLOW,
            latency_ms=total_latency,
        )

    async def _run_rules_engine(self, ctx: InterceptionContext) -> PreCallResult:
        """Run the local rules engine for fast decisions."""
        if not self._rules_engine:
            return PreCallResult.defer()

        try:
            result = await self._rules_engine.evaluate(ctx)
            return result
        except Exception as e:
            logger.error(f"Rules engine error: {e}")
            return PreCallResult.defer()

    async def _consult_backend_pre_call(
        self, ctx: InterceptionContext
    ) -> Optional[PreCallResult]:
        """Consult backend for pre-call decision."""
        if not self._enable_backend_consultation or not self._backend_connector:
            return None

        if not self._backend_connector.is_connected:
            logger.debug("Backend not connected, skipping consultation")
            return None

        try:
            self._stats["backend_consultations"] += 1
            response = await asyncio.wait_for(
                self._backend_connector.consult_pre_call(ctx),
                timeout=self._backend_timeout_ms / 1000.0,
            )
            return response
        except asyncio.TimeoutError:
            logger.warning("Backend pre-call consultation timed out")
            return None
        except Exception as e:
            logger.error(f"Backend pre-call consultation error: {e}")
            return None

    async def _consult_backend_post_call(
        self, ctx: InterceptionContext
    ) -> Optional[PostCallResult]:
        """Consult backend for post-call decision and fixes."""
        if not self._enable_backend_consultation or not self._backend_connector:
            return None

        if not self._backend_connector.is_connected:
            logger.debug("Backend not connected, skipping consultation")
            return None

        try:
            self._stats["backend_consultations"] += 1

            # Use existing remediate/detect_precursors methods if available
            if self._aigie and ctx.error:
                # Error case - use remediation
                fix_result = await self._aigie.remediate(
                    trace_id=ctx.trace_id or "",
                    error=ctx.error,
                )
                if fix_result and fix_result.get("fix"):
                    return PostCallResult.modify(
                        reason="Backend remediation applied",
                        fixes=[
                            FixAction(
                                action_type=fix_result.get("action_type", "modify_response"),
                                parameters=fix_result.get("parameters", {}),
                                confidence=fix_result.get("confidence", 0.8),
                                source="backend",
                                reason=fix_result.get("description"),
                            )
                        ],
                    )

            if self._aigie and ctx.drift_score and ctx.drift_score > 0.5:
                # Drift detected - use prevention
                precursors = await self._aigie.detect_precursors(
                    context={
                        "trace_id": ctx.trace_id,
                        "span_id": ctx.span_id,
                        "drift_score": ctx.drift_score,
                        "messages": ctx.messages[-3:] if ctx.messages else [],
                    }
                )
                if precursors:
                    return PostCallResult.consult(
                        reason=f"Drift precursors detected: {len(precursors)} issues"
                    )

            # General backend consultation
            response = await asyncio.wait_for(
                self._backend_connector.consult_post_call(ctx),
                timeout=self._backend_timeout_ms / 1000.0,
            )
            return response

        except asyncio.TimeoutError:
            logger.warning("Backend post-call consultation timed out")
            return None
        except Exception as e:
            logger.error(f"Backend post-call consultation error: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Get interception statistics."""
        return {
            **self._stats,
            "pre_hooks_count": len(self._pre_hooks),
            "post_hooks_count": len(self._post_hooks),
            "avg_latency_ms": (
                self._stats["total_latency_ms"]
                / max(self._stats["pre_calls"] + self._stats["post_calls"], 1)
            ),
        }

    def reset_stats(self) -> None:
        """Reset interception statistics."""
        self._stats = {
            "pre_calls": 0,
            "post_calls": 0,
            "blocks": 0,
            "modifications": 0,
            "backend_consultations": 0,
            "errors": 0,
            "total_latency_ms": 0.0,
        }
