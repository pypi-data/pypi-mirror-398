"""
AutoFixApplicator - Applies automatic fixes from backend recommendations.

This module implements fix strategies including:
- Response modification
- Request retry with adjustments
- Model fallback
- Context truncation
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List, TYPE_CHECKING, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    from ..interceptor.protocols import (
        InterceptionContext,
        PostCallResult,
        FixAction,
        FixActionType,
    )

logger = logging.getLogger("aigie.realtime")


class FixStrategy(Enum):
    """Strategy for applying fixes."""

    MODIFY_RESPONSE = "modify_response"
    """Modify the response content directly."""

    RETRY_REQUEST = "retry_request"
    """Retry the request with modified parameters."""

    FALLBACK_MODEL = "fallback_model"
    """Fall back to a different model."""

    TRUNCATE_CONTEXT = "truncate_context"
    """Truncate context to reduce token count."""

    INJECT_INSTRUCTION = "inject_instruction"
    """Inject corrective instruction into messages."""

    OVERRIDE_RESPONSE = "override_response"
    """Completely override the response."""


@dataclass
class FixResult:
    """Result of applying a fix."""

    success: bool
    """Whether the fix was applied successfully."""

    strategy: FixStrategy
    """The strategy that was used."""

    modified_response: Optional[Any] = None
    """The modified response if applicable."""

    retry_kwargs: Optional[Dict[str, Any]] = None
    """Modified kwargs for retry if applicable."""

    reason: Optional[str] = None
    """Reason for success/failure."""

    latency_ms: float = 0.0
    """Time taken to apply the fix."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata about the fix."""


@dataclass
class FixConfig:
    """Configuration for fix application."""

    max_retries: int = 3
    """Maximum number of retry attempts."""

    retry_delay_ms: float = 100.0
    """Delay between retries in milliseconds."""

    fallback_models: List[str] = field(default_factory=list)
    """List of fallback models in priority order."""

    max_context_reduction_percent: float = 0.5
    """Maximum context reduction (50% default)."""

    enable_response_modification: bool = True
    """Whether to allow response modification."""

    enable_instruction_injection: bool = True
    """Whether to allow instruction injection."""


class AutoFixApplicator:
    """
    Applies automatic fixes to LLM calls based on backend recommendations.

    Features:
    - Multiple fix strategies
    - Priority-based strategy selection
    - Retry logic with backoff
    - Model fallback chain
    - Context management
    - Performance tracking
    """

    def __init__(self, config: Optional[FixConfig] = None):
        """
        Initialize the fix applicator.

        Args:
            config: Configuration for fix application
        """
        self._config = config or FixConfig()

        # Strategy handlers
        self._strategy_handlers: Dict[
            FixStrategy, Callable[["InterceptionContext", "FixAction"], Awaitable[FixResult]]
        ] = {
            FixStrategy.MODIFY_RESPONSE: self._apply_modify_response,
            FixStrategy.RETRY_REQUEST: self._apply_retry_request,
            FixStrategy.FALLBACK_MODEL: self._apply_fallback_model,
            FixStrategy.TRUNCATE_CONTEXT: self._apply_truncate_context,
            FixStrategy.INJECT_INSTRUCTION: self._apply_inject_instruction,
            FixStrategy.OVERRIDE_RESPONSE: self._apply_override_response,
        }

        # Statistics
        self._stats = {
            "fixes_attempted": 0,
            "fixes_successful": 0,
            "fixes_failed": 0,
            "retries_performed": 0,
            "fallbacks_used": 0,
            "total_latency_ms": 0.0,
        }

        # Retry executor (can be set externally)
        self._retry_executor: Optional[Callable[..., Awaitable[Any]]] = None

    def set_retry_executor(
        self, executor: Callable[..., Awaitable[Any]]
    ) -> None:
        """
        Set the executor function for retries.

        This should be the original LLM call function that can be retried
        with modified parameters.

        Args:
            executor: Async function to execute retries
        """
        self._retry_executor = executor

    async def apply_fixes(
        self,
        ctx: "InterceptionContext",
        fixes: List["FixAction"],
    ) -> FixResult:
        """
        Apply a list of fixes in priority order.

        Fixes are applied until one succeeds or all fail.

        Args:
            ctx: The interception context
            fixes: List of fix actions to apply

        Returns:
            FixResult with the outcome
        """
        from ..interceptor.protocols import FixActionType

        if not fixes:
            return FixResult(
                success=False,
                strategy=FixStrategy.MODIFY_RESPONSE,
                reason="No fixes provided",
            )

        self._stats["fixes_attempted"] += 1
        start_time = time.perf_counter()

        # Sort fixes by confidence (highest first)
        sorted_fixes = sorted(fixes, key=lambda f: f.confidence, reverse=True)

        for fix in sorted_fixes:
            strategy = self._map_action_to_strategy(fix.action_type)
            handler = self._strategy_handlers.get(strategy)

            if handler is None:
                logger.warning(f"No handler for strategy: {strategy}")
                continue

            try:
                result = await handler(ctx, fix)
                result.strategy = strategy
                result.latency_ms = (time.perf_counter() - start_time) * 1000

                if result.success:
                    self._stats["fixes_successful"] += 1
                    self._stats["total_latency_ms"] += result.latency_ms
                    logger.info(f"Fix applied successfully: {strategy.value}")
                    return result

                logger.debug(f"Fix failed: {strategy.value} - {result.reason}")

            except Exception as e:
                logger.error(f"Error applying fix {strategy.value}: {e}")

        # All fixes failed
        self._stats["fixes_failed"] += 1
        total_latency = (time.perf_counter() - start_time) * 1000
        self._stats["total_latency_ms"] += total_latency

        return FixResult(
            success=False,
            strategy=FixStrategy.MODIFY_RESPONSE,
            reason="All fix strategies failed",
            latency_ms=total_latency,
        )

    def _map_action_to_strategy(self, action_type: "FixActionType") -> FixStrategy:
        """Map FixActionType to FixStrategy."""
        from ..interceptor.protocols import FixActionType

        mapping = {
            FixActionType.MODIFY_RESPONSE: FixStrategy.MODIFY_RESPONSE,
            FixActionType.RETRY: FixStrategy.RETRY_REQUEST,
            FixActionType.FALLBACK: FixStrategy.FALLBACK_MODEL,
            FixActionType.TRUNCATE_CONTEXT: FixStrategy.TRUNCATE_CONTEXT,
            FixActionType.INJECT_INSTRUCTION: FixStrategy.INJECT_INSTRUCTION,
            FixActionType.OVERRIDE_RESPONSE: FixStrategy.OVERRIDE_RESPONSE,
        }
        return mapping.get(action_type, FixStrategy.MODIFY_RESPONSE)

    async def _apply_modify_response(
        self, ctx: "InterceptionContext", fix: "FixAction"
    ) -> FixResult:
        """Apply response modification fix."""
        if not self._config.enable_response_modification:
            return FixResult(
                success=False,
                strategy=FixStrategy.MODIFY_RESPONSE,
                reason="Response modification disabled",
            )

        params = fix.parameters
        modified_content = params.get("content")
        modifications = params.get("modifications", [])

        if modified_content:
            # Direct content replacement
            return FixResult(
                success=True,
                strategy=FixStrategy.MODIFY_RESPONSE,
                modified_response={"content": modified_content},
                reason=fix.reason or "Content replaced",
            )

        if modifications and ctx.response_content:
            # Apply incremental modifications
            content = ctx.response_content
            for mod in modifications:
                mod_type = mod.get("type")
                if mod_type == "replace":
                    content = content.replace(
                        mod.get("old", ""),
                        mod.get("new", ""),
                    )
                elif mod_type == "append":
                    content += mod.get("text", "")
                elif mod_type == "prepend":
                    content = mod.get("text", "") + content

            return FixResult(
                success=True,
                strategy=FixStrategy.MODIFY_RESPONSE,
                modified_response={"content": content},
                reason=fix.reason or "Content modified",
            )

        return FixResult(
            success=False,
            strategy=FixStrategy.MODIFY_RESPONSE,
            reason="No modification parameters provided",
        )

    async def _apply_retry_request(
        self, ctx: "InterceptionContext", fix: "FixAction"
    ) -> FixResult:
        """Apply retry with modified parameters."""
        if self._retry_executor is None:
            return FixResult(
                success=False,
                strategy=FixStrategy.RETRY_REQUEST,
                reason="No retry executor configured",
            )

        params = fix.parameters
        max_retries = params.get("max_retries", self._config.max_retries)
        retry_delay = params.get("retry_delay_ms", self._config.retry_delay_ms)

        # Build modified kwargs
        retry_kwargs = dict(ctx.original_kwargs) if ctx.original_kwargs else {}

        # Apply parameter modifications
        if "temperature" in params:
            retry_kwargs["temperature"] = params["temperature"]
        if "max_tokens" in params:
            retry_kwargs["max_tokens"] = params["max_tokens"]
        if "messages" in params:
            retry_kwargs["messages"] = params["messages"]

        for attempt in range(max_retries):
            self._stats["retries_performed"] += 1
            try:
                if attempt > 0:
                    await asyncio.sleep(retry_delay / 1000)

                # Execute retry
                response = await self._retry_executor(**retry_kwargs)

                return FixResult(
                    success=True,
                    strategy=FixStrategy.RETRY_REQUEST,
                    modified_response=response,
                    retry_kwargs=retry_kwargs,
                    reason=f"Retry successful on attempt {attempt + 1}",
                    metadata={"attempts": attempt + 1},
                )

            except Exception as e:
                logger.debug(f"Retry attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    return FixResult(
                        success=False,
                        strategy=FixStrategy.RETRY_REQUEST,
                        reason=f"All {max_retries} retry attempts failed: {e}",
                        metadata={"attempts": max_retries, "last_error": str(e)},
                    )

        return FixResult(
            success=False,
            strategy=FixStrategy.RETRY_REQUEST,
            reason="Retry logic exhausted",
        )

    async def _apply_fallback_model(
        self, ctx: "InterceptionContext", fix: "FixAction"
    ) -> FixResult:
        """Apply model fallback fix."""
        if self._retry_executor is None:
            return FixResult(
                success=False,
                strategy=FixStrategy.FALLBACK_MODEL,
                reason="No retry executor configured",
            )

        params = fix.parameters
        fallback_models = params.get("models", self._config.fallback_models)

        if not fallback_models:
            return FixResult(
                success=False,
                strategy=FixStrategy.FALLBACK_MODEL,
                reason="No fallback models configured",
            )

        # Build kwargs with fallback model
        retry_kwargs = dict(ctx.original_kwargs) if ctx.original_kwargs else {}

        for model in fallback_models:
            if model == ctx.model:
                continue  # Skip current model

            retry_kwargs["model"] = model
            self._stats["fallbacks_used"] += 1

            try:
                response = await self._retry_executor(**retry_kwargs)

                return FixResult(
                    success=True,
                    strategy=FixStrategy.FALLBACK_MODEL,
                    modified_response=response,
                    retry_kwargs=retry_kwargs,
                    reason=f"Fallback to {model} successful",
                    metadata={"fallback_model": model},
                )

            except Exception as e:
                logger.debug(f"Fallback to {model} failed: {e}")

        return FixResult(
            success=False,
            strategy=FixStrategy.FALLBACK_MODEL,
            reason="All fallback models failed",
        )

    async def _apply_truncate_context(
        self, ctx: "InterceptionContext", fix: "FixAction"
    ) -> FixResult:
        """Apply context truncation fix."""
        params = fix.parameters
        target_reduction = params.get(
            "reduction_percent",
            self._config.max_context_reduction_percent,
        )
        strategy = params.get("strategy", "keep_recent")

        messages = list(ctx.messages)
        original_count = len(messages)

        if original_count <= 2:
            return FixResult(
                success=False,
                strategy=FixStrategy.TRUNCATE_CONTEXT,
                reason="Cannot truncate: too few messages",
            )

        # Calculate target message count
        target_count = max(2, int(original_count * (1 - target_reduction)))

        if strategy == "keep_recent":
            # Keep system message + most recent messages
            system_msgs = [m for m in messages if m.get("role") == "system"]
            non_system = [m for m in messages if m.get("role") != "system"]
            truncated = system_msgs + non_system[-(target_count - len(system_msgs)):]

        elif strategy == "keep_important":
            # Keep system, first user message, and recent messages
            system_msgs = [m for m in messages if m.get("role") == "system"]
            user_msgs = [m for m in messages if m.get("role") == "user"]
            recent_count = target_count - len(system_msgs) - 1
            truncated = (
                system_msgs +
                (user_msgs[:1] if user_msgs else []) +
                messages[-recent_count:] if recent_count > 0 else []
            )

        else:
            # Default: simple tail truncation
            truncated = messages[-target_count:]

        return FixResult(
            success=True,
            strategy=FixStrategy.TRUNCATE_CONTEXT,
            retry_kwargs={"messages": truncated},
            reason=f"Truncated from {original_count} to {len(truncated)} messages",
            metadata={
                "original_count": original_count,
                "truncated_count": len(truncated),
                "strategy": strategy,
            },
        )

    async def _apply_inject_instruction(
        self, ctx: "InterceptionContext", fix: "FixAction"
    ) -> FixResult:
        """Apply instruction injection fix."""
        if not self._config.enable_instruction_injection:
            return FixResult(
                success=False,
                strategy=FixStrategy.INJECT_INSTRUCTION,
                reason="Instruction injection disabled",
            )

        params = fix.parameters
        instruction = params.get("instruction")
        position = params.get("position", "system")  # system, user_last, assistant_last

        if not instruction:
            return FixResult(
                success=False,
                strategy=FixStrategy.INJECT_INSTRUCTION,
                reason="No instruction provided",
            )

        messages = list(ctx.messages)

        if position == "system":
            # Append to system message or create one
            system_idx = next(
                (i for i, m in enumerate(messages) if m.get("role") == "system"),
                None,
            )
            if system_idx is not None:
                messages[system_idx]["content"] += f"\n\n{instruction}"
            else:
                messages.insert(0, {"role": "system", "content": instruction})

        elif position == "user_last":
            # Add as user message before last assistant turn
            messages.append({"role": "user", "content": instruction})

        elif position == "assistant_last":
            # Modify last assistant message if exists
            for i in range(len(messages) - 1, -1, -1):
                if messages[i].get("role") == "assistant":
                    messages[i]["content"] += f"\n\n{instruction}"
                    break
            else:
                # No assistant message, add as system instruction
                messages.insert(0, {"role": "system", "content": instruction})

        return FixResult(
            success=True,
            strategy=FixStrategy.INJECT_INSTRUCTION,
            retry_kwargs={"messages": messages},
            reason=f"Instruction injected at {position}",
            metadata={"position": position},
        )

    async def _apply_override_response(
        self, ctx: "InterceptionContext", fix: "FixAction"
    ) -> FixResult:
        """Apply complete response override."""
        params = fix.parameters
        response = params.get("response")

        if not response:
            return FixResult(
                success=False,
                strategy=FixStrategy.OVERRIDE_RESPONSE,
                reason="No response override provided",
            )

        return FixResult(
            success=True,
            strategy=FixStrategy.OVERRIDE_RESPONSE,
            modified_response=response,
            reason=fix.reason or "Response overridden",
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get applicator statistics."""
        return {
            **self._stats,
            "success_rate": (
                self._stats["fixes_successful"] /
                max(self._stats["fixes_attempted"], 1)
            ),
            "avg_latency_ms": (
                self._stats["total_latency_ms"] /
                max(self._stats["fixes_successful"], 1)
            ),
        }

    def reset_stats(self) -> None:
        """Reset statistics."""
        self._stats = {
            "fixes_attempted": 0,
            "fixes_successful": 0,
            "fixes_failed": 0,
            "retries_performed": 0,
            "fallbacks_used": 0,
            "total_latency_ms": 0.0,
        }
