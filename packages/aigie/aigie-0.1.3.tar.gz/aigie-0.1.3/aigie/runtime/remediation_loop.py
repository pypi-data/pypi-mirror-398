"""
Remediation Loop for detect-fix-retry cycle.

Supports two operational modes:
1. RECOMMENDATION MODE (default): Learn workflows, analyze, provide recommendations
2. AUTONOMOUS MODE (opt-in): Active interception and automatic fixes in runtime

Customers start in recommendation mode to learn their workflows,
then can enable autonomous mode when ready for automatic fixes.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ..judge.evaluator import LLMJudge, SpanEvaluation
    from ..judge.context_aggregator import ContextAggregator, AggregatedContext
    from .span_interceptor import SpanInterceptor, SpanInterceptionResult

logger = logging.getLogger("aigie.runtime")


class OperationalMode(Enum):
    """Operational mode of the remediation system."""

    RECOMMENDATION = "recommendation"
    """
    Recommendation mode (default):
    - Collect data and track all spans
    - Detect issues and show what Aigie WOULD fix
    - Display proposed fixes to build trust
    - DO NOT automatically apply fixes
    - Goal: Build trust and push user toward autonomous mode
    """

    AUTONOMOUS = "autonomous"
    """
    Autonomous mode (opt-in):
    - Active interception of all spans
    - Automatic retry with remediation
    - Step-level fixes applied in runtime
    - User has clicked "autonomous" button
    """

    LEARNING = "learning"
    """
    Learning mode (transitional):
    - Collecting data to learn workflows
    - Building pattern library
    - Preparing for autonomous mode
    """


class RemediationStrategy(Enum):
    """Strategies for remediation."""

    RETRY_WITH_CONTEXT = "retry_with_context"
    """Retry with additional context/instructions."""

    MODIFY_PROMPT = "modify_prompt"
    """Modify the prompt to fix issues."""

    FALLBACK_MODEL = "fallback_model"
    """Try a different/fallback model."""

    TRUNCATE_CONTEXT = "truncate_context"
    """Truncate context to reduce token count."""

    INJECT_INSTRUCTION = "inject_instruction"
    """Inject corrective instruction."""

    ROLLBACK_AND_RETRY = "rollback_and_retry"
    """Rollback to last good state and retry."""

    SKIP_STEP = "skip_step"
    """Skip this step and continue."""

    ESCALATE = "escalate"
    """Escalate to human/backend."""


@dataclass
class RemediationConfig:
    """Configuration for the remediation loop."""

    # Mode settings
    mode: OperationalMode = OperationalMode.RECOMMENDATION
    """Operational mode - recommendation (default) or autonomous."""

    # Learning settings
    learning_threshold: int = 100
    """Number of traces before suggesting autonomous mode."""

    min_workflow_confidence: float = 0.8
    """Minimum confidence in workflow understanding before autonomous mode."""

    # Autonomous settings
    auto_fix_enabled: bool = False
    """Whether automatic fixes are enabled (requires autonomous mode)."""

    max_auto_fixes_per_trace: int = 5
    """Maximum automatic fixes per trace."""

    stop_on_repeated_fix_failure: bool = True
    """Stop if same fix fails multiple times."""

    # Strategy selection
    preferred_strategies: List[RemediationStrategy] = field(
        default_factory=lambda: [
            RemediationStrategy.RETRY_WITH_CONTEXT,
            RemediationStrategy.MODIFY_PROMPT,
            RemediationStrategy.INJECT_INSTRUCTION,
        ]
    )
    """Preferred remediation strategies in order."""

    # Thresholds
    confidence_threshold_for_auto_fix: float = 0.7
    """Minimum confidence to apply auto-fix."""

    max_retries_per_strategy: int = 2
    """Maximum retries per strategy."""

    # Callbacks
    on_recommendation: Optional[Callable] = None
    """Callback when recommendation is generated (recommendation mode)."""

    on_auto_fix: Optional[Callable] = None
    """Callback when auto-fix is applied (autonomous mode)."""

    on_escalation: Optional[Callable] = None
    """Callback when issue is escalated."""

    # Integration
    report_to_backend: bool = True
    """Report fixes and recommendations to backend."""

    learn_from_manual_fixes: bool = True
    """Learn from manual fixes applied by user."""


@dataclass
class RemediationResult:
    """Result of a remediation attempt."""

    span_id: str
    """ID of the span that was remediated."""

    mode: OperationalMode
    """Mode in which remediation was performed."""

    # Outcome
    success: bool
    """Whether remediation was successful."""

    action_taken: str
    """Description of action taken."""

    # For recommendation mode
    recommendation: Optional[str] = None
    """Recommended fix (in recommendation mode)."""

    recommended_strategy: Optional[RemediationStrategy] = None
    """Recommended strategy."""

    confidence: float = 0.0
    """Confidence in the recommendation/fix."""

    # For autonomous mode
    fix_applied: bool = False
    """Whether a fix was automatically applied."""

    strategy_used: Optional[RemediationStrategy] = None
    """Strategy that was used."""

    retry_count: int = 0
    """Number of retries performed."""

    original_output: Optional[str] = None
    """Original output before fix."""

    fixed_output: Optional[str] = None
    """Output after fix was applied."""

    # Metadata
    issues_addressed: List[str] = field(default_factory=list)
    """Issues that were addressed."""

    remaining_issues: List[str] = field(default_factory=list)
    """Issues that remain after remediation."""

    time_ms: float = 0.0
    """Time taken for remediation."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata."""


@dataclass
class WorkflowPattern:
    """A learned workflow pattern."""

    pattern_id: str
    """Unique pattern identifier."""

    name: str
    """Pattern name."""

    description: str
    """Pattern description."""

    # Pattern components
    span_sequence: List[str]
    """Typical sequence of span types."""

    common_issues: List[str]
    """Commonly occurring issues."""

    successful_fixes: List[Dict[str, Any]]
    """Fixes that worked for this pattern."""

    # Metrics
    occurrence_count: int = 0
    """Number of times this pattern occurred."""

    fix_success_rate: float = 0.0
    """Success rate of fixes for this pattern."""

    avg_fix_time_ms: float = 0.0
    """Average time to fix issues."""

    # Confidence
    confidence: float = 0.0
    """Confidence in pattern recognition."""


class RemediationLoop:
    """
    Orchestrates the detect-fix-retry cycle with dual-mode support.

    In RECOMMENDATION MODE:
    - Monitors all spans and collects data
    - Detects issues using LLM Judge
    - Generates recommendations for manual review
    - Learns workflows and patterns

    In AUTONOMOUS MODE:
    - Actively intercepts spans with issues
    - Automatically applies fixes
    - Retries failed steps with remediation
    - Reports fixes to backend for learning

    Customers typically start in recommendation mode to build trust,
    then enable autonomous mode when ready.
    """

    def __init__(
        self,
        config: Optional[RemediationConfig] = None,
        judge: Optional["LLMJudge"] = None,
        context_aggregator: Optional["ContextAggregator"] = None,
        span_interceptor: Optional["SpanInterceptor"] = None,
        backend_client: Optional[Any] = None,
    ):
        """
        Initialize the remediation loop.

        Args:
            config: Remediation configuration
            judge: LLM Judge for evaluation
            context_aggregator: Context aggregator for history
            span_interceptor: Span interceptor for step-level retry
            backend_client: Backend client for reporting
        """
        self.config = config or RemediationConfig()
        self._judge = judge
        self._context_aggregator = context_aggregator
        self._span_interceptor = span_interceptor
        self._backend_client = backend_client

        # Learning storage
        self._workflow_patterns: Dict[str, WorkflowPattern] = {}
        self._issue_fix_history: List[Dict[str, Any]] = []
        self._traces_processed: int = 0

        # Recommendations storage
        self._pending_recommendations: List[RemediationResult] = []

        # Stats
        self._stats = {
            "recommendations_generated": 0,
            "recommendations_accepted": 0,
            "auto_fixes_attempted": 0,
            "auto_fixes_successful": 0,
            "patterns_learned": 0,
            "traces_analyzed": 0,
            "mode_switches": 0,
        }

    @property
    def mode(self) -> OperationalMode:
        """Current operational mode."""
        return self.config.mode

    def enable_autonomous_mode(self) -> bool:
        """
        Enable autonomous mode (user clicked "autonomous" button).

        Returns True if autonomous mode was enabled successfully.
        """
        # Check if we have enough learning
        if self._traces_processed < self.config.learning_threshold:
            logger.warning(
                f"Not enough traces processed ({self._traces_processed}/{self.config.learning_threshold}) "
                "for autonomous mode. Continuing in recommendation mode."
            )
            return False

        # Check workflow confidence
        if self._workflow_patterns:
            avg_confidence = sum(
                p.confidence for p in self._workflow_patterns.values()
            ) / len(self._workflow_patterns)
            if avg_confidence < self.config.min_workflow_confidence:
                logger.warning(
                    f"Workflow confidence ({avg_confidence:.2f}) below threshold "
                    f"({self.config.min_workflow_confidence}). "
                    "Continuing in recommendation mode."
                )
                return False

        # Enable autonomous mode
        self.config.mode = OperationalMode.AUTONOMOUS
        self.config.auto_fix_enabled = True
        self._stats["mode_switches"] += 1
        logger.info("Autonomous mode enabled - automatic fixes will be applied")
        return True

    def disable_autonomous_mode(self) -> None:
        """Disable autonomous mode, return to recommendation mode."""
        self.config.mode = OperationalMode.RECOMMENDATION
        self.config.auto_fix_enabled = False
        self._stats["mode_switches"] += 1
        logger.info("Autonomous mode disabled - returning to recommendation mode")

    async def process_span(
        self,
        span_id: str,
        trace_id: str,
        input_messages: List[Dict[str, Any]],
        output_content: str,
        evaluation: Optional["SpanEvaluation"] = None,
        error: Optional[Exception] = None,
        llm_call: Optional[Callable] = None,
    ) -> RemediationResult:
        """
        Process a span through the remediation loop.

        In recommendation mode: Analyzes and generates recommendations.
        In autonomous mode: Automatically applies fixes.

        Args:
            span_id: ID of the span
            trace_id: ID of the trace
            input_messages: Input messages
            output_content: Output content
            evaluation: Evaluation from LLM Judge (if already done)
            error: Error if span failed
            llm_call: Callable for retry (autonomous mode)

        Returns:
            RemediationResult with outcome and any fixes/recommendations
        """
        start_time = time.perf_counter()
        self._stats["traces_analyzed"] += 1
        self._traces_processed += 1

        # Get or create evaluation
        if not evaluation and self._judge:
            full_history = None
            if self._context_aggregator:
                ctx = self._context_aggregator.get_context_for_span(span_id)
                if ctx:
                    full_history = ctx.all_messages

            evaluation = await self._judge.evaluate_span(
                span_id=span_id,
                input_messages=input_messages,
                output_content=output_content,
                full_history=full_history,
            )

        # Check if there are issues to address
        has_issues = (
            error is not None
            or (evaluation and evaluation.result.has_issues)
        )

        if not has_issues:
            # No issues - continue normally
            return RemediationResult(
                span_id=span_id,
                mode=self.config.mode,
                success=True,
                action_taken="No issues detected",
                time_ms=(time.perf_counter() - start_time) * 1000,
            )

        # Extract issues
        issues = []
        if error:
            issues.append(f"Error: {str(error)}")
        if evaluation and evaluation.result.issues:
            issues.extend([i.description for i in evaluation.result.issues])

        # Process based on mode
        if self.config.mode == OperationalMode.AUTONOMOUS and self.config.auto_fix_enabled:
            result = await self._process_autonomous(
                span_id=span_id,
                trace_id=trace_id,
                input_messages=input_messages,
                output_content=output_content,
                evaluation=evaluation,
                issues=issues,
                llm_call=llm_call,
            )
        else:
            result = await self._process_recommendation(
                span_id=span_id,
                trace_id=trace_id,
                input_messages=input_messages,
                output_content=output_content,
                evaluation=evaluation,
                issues=issues,
            )

        result.time_ms = (time.perf_counter() - start_time) * 1000

        # Learn from this interaction
        await self._learn_from_interaction(
            span_id=span_id,
            trace_id=trace_id,
            issues=issues,
            result=result,
        )

        return result

    async def _process_recommendation(
        self,
        span_id: str,
        trace_id: str,
        input_messages: List[Dict[str, Any]],
        output_content: str,
        evaluation: Optional["SpanEvaluation"],
        issues: List[str],
    ) -> RemediationResult:
        """Process span in recommendation mode - generate recommendations only."""
        # Select best strategy based on issues
        strategy = self._select_strategy(issues, output_content)

        # Generate recommendation
        recommendation = self._generate_recommendation(
            issues=issues,
            strategy=strategy,
            evaluation=evaluation,
            context=self._get_context_for_recommendation(trace_id),
        )

        result = RemediationResult(
            span_id=span_id,
            mode=OperationalMode.RECOMMENDATION,
            success=True,
            action_taken="Recommendation generated",
            recommendation=recommendation,
            recommended_strategy=strategy,
            confidence=evaluation.confidence if evaluation else 0.5,
            issues_addressed=issues,
            fix_applied=False,
        )

        # Store recommendation
        self._pending_recommendations.append(result)
        self._stats["recommendations_generated"] += 1

        # Notify via callback
        if self.config.on_recommendation:
            try:
                await self._safe_callback(
                    self.config.on_recommendation,
                    span_id=span_id,
                    recommendation=recommendation,
                    strategy=strategy.value if strategy else None,
                    issues=issues,
                )
            except Exception as e:
                logger.warning(f"Recommendation callback error: {e}")

        # Report to backend
        if self.config.report_to_backend and self._backend_client:
            await self._report_recommendation(result)

        return result

    async def _process_autonomous(
        self,
        span_id: str,
        trace_id: str,
        input_messages: List[Dict[str, Any]],
        output_content: str,
        evaluation: Optional["SpanEvaluation"],
        issues: List[str],
        llm_call: Optional[Callable] = None,
    ) -> RemediationResult:
        """Process span in autonomous mode - automatically apply fixes."""
        self._stats["auto_fixes_attempted"] += 1

        # Check if we can auto-fix
        confidence = evaluation.confidence if evaluation else 0.5
        if confidence < self.config.confidence_threshold_for_auto_fix:
            # Confidence too low - escalate
            return await self._escalate(
                span_id=span_id,
                reason=f"Confidence ({confidence:.2f}) below threshold for auto-fix",
                issues=issues,
            )

        # Select strategy
        strategy = self._select_strategy(issues, output_content)

        # Try to apply fix using span interceptor
        if self._span_interceptor and llm_call:
            interception_result = await self._span_interceptor.intercept_span(
                span_id=span_id,
                trace_id=trace_id,
                input_messages=input_messages,
                output_content=output_content,
                error=None,
                llm_call=llm_call,
            )

            if interception_result.modified_output:
                # Fix was applied successfully
                result = RemediationResult(
                    span_id=span_id,
                    mode=OperationalMode.AUTONOMOUS,
                    success=True,
                    action_taken="Auto-fix applied successfully",
                    fix_applied=True,
                    strategy_used=strategy,
                    retry_count=interception_result.retry_count,
                    original_output=output_content,
                    fixed_output=interception_result.modified_output,
                    issues_addressed=issues,
                    confidence=confidence,
                )
                self._stats["auto_fixes_successful"] += 1

                # Notify via callback
                if self.config.on_auto_fix:
                    await self._safe_callback(
                        self.config.on_auto_fix,
                        span_id=span_id,
                        strategy=strategy.value if strategy else None,
                        issues=issues,
                        fixed_output=interception_result.modified_output,
                    )

                return result

        # Couldn't fix - fall back to recommendation
        return await self._process_recommendation(
            span_id=span_id,
            trace_id=trace_id,
            input_messages=input_messages,
            output_content=output_content,
            evaluation=evaluation,
            issues=issues,
        )

    async def _escalate(
        self,
        span_id: str,
        reason: str,
        issues: List[str],
    ) -> RemediationResult:
        """Escalate an issue for manual review."""
        result = RemediationResult(
            span_id=span_id,
            mode=self.config.mode,
            success=False,
            action_taken=f"Escalated: {reason}",
            issues_addressed=[],
            remaining_issues=issues,
        )

        # Notify via callback
        if self.config.on_escalation:
            await self._safe_callback(
                self.config.on_escalation,
                span_id=span_id,
                reason=reason,
                issues=issues,
            )

        return result

    def _select_strategy(
        self,
        issues: List[str],
        output_content: str,
    ) -> RemediationStrategy:
        """Select the best remediation strategy for the issues."""
        issues_lower = " ".join(issues).lower()

        # Error patterns
        if "error" in issues_lower or "exception" in issues_lower:
            return RemediationStrategy.RETRY_WITH_CONTEXT

        # Drift patterns
        if "drift" in issues_lower or "off-topic" in issues_lower:
            return RemediationStrategy.INJECT_INSTRUCTION

        # Hallucination patterns
        if "hallucination" in issues_lower or "made up" in issues_lower:
            return RemediationStrategy.MODIFY_PROMPT

        # Token/length patterns
        if "token" in issues_lower or "length" in issues_lower or "truncat" in issues_lower:
            return RemediationStrategy.TRUNCATE_CONTEXT

        # Quality patterns
        if "quality" in issues_lower or "incomplete" in issues_lower:
            return RemediationStrategy.RETRY_WITH_CONTEXT

        # Repetition patterns
        if "repetition" in issues_lower or "loop" in issues_lower:
            return RemediationStrategy.MODIFY_PROMPT

        # Default to first preferred strategy
        if self.config.preferred_strategies:
            return self.config.preferred_strategies[0]

        return RemediationStrategy.RETRY_WITH_CONTEXT

    def _generate_recommendation(
        self,
        issues: List[str],
        strategy: RemediationStrategy,
        evaluation: Optional["SpanEvaluation"],
        context: Optional[Dict[str, Any]],
    ) -> str:
        """
        Generate a preview of what Aigie WOULD do in autonomous mode.

        This shows the customer the fix we would apply, building trust
        and encouraging them to enable autonomous mode.
        """
        strategy_actions = {
            RemediationStrategy.RETRY_WITH_CONTEXT: "Retry this step with additional context",
            RemediationStrategy.MODIFY_PROMPT: "Modify the prompt to fix the issue",
            RemediationStrategy.FALLBACK_MODEL: "Switch to a fallback model",
            RemediationStrategy.TRUNCATE_CONTEXT: "Truncate context to fit limits",
            RemediationStrategy.INJECT_INSTRUCTION: "Inject corrective instruction",
            RemediationStrategy.ROLLBACK_AND_RETRY: "Rollback and retry from last good state",
            RemediationStrategy.SKIP_STEP: "Skip this non-critical step",
            RemediationStrategy.ESCALATE: "Escalate for manual review",
        }

        # Build "what we would do" message
        recommendation = f"🔍 **Issues Detected:**\n"
        for i, issue in enumerate(issues[:5], 1):
            recommendation += f"  {i}. {issue}\n"

        recommendation += f"\n🔧 **What Aigie Would Do (Autonomous Mode):**\n"
        recommendation += f"  → {strategy_actions.get(strategy, 'Apply automatic fix')}\n"

        if evaluation and evaluation.remediation:
            suggested = evaluation.remediation.get("suggested_remediation")
            if suggested:
                recommendation += f"\n📋 **Specific Fix:**\n  {suggested}\n"

        # Show success rate from similar fixes
        similar_fixes = self._find_similar_fixes(issues)
        if similar_fixes:
            success_count = sum(1 for f in similar_fixes if f.get("success", False))
            success_rate = success_count / len(similar_fixes) * 100
            recommendation += f"\n📊 **Historical Success Rate:** {success_rate:.0f}% ({success_count}/{len(similar_fixes)} similar fixes succeeded)\n"

        # Encourage autonomous mode
        ready_info = self.is_ready_for_autonomous()
        if ready_info["ready"]:
            recommendation += f"\n✅ **Ready for Autonomous Mode!** Enable to have Aigie fix issues automatically.\n"
        else:
            pct = min(100, (ready_info["traces_processed"] / max(ready_info["traces_needed"], 1)) * 100)
            recommendation += f"\n⏳ **Learning Progress:** {pct:.0f}% - {ready_info['traces_needed'] - ready_info['traces_processed']} more traces needed\n"

        return recommendation

    def _find_similar_fixes(self, issues: List[str]) -> List[Dict[str, Any]]:
        """Find similar fixes from history."""
        similar = []
        issues_set = set(i.lower()[:50] for i in issues)

        for fix in self._issue_fix_history[-100:]:  # Last 100 fixes
            fix_issues = set(i.lower()[:50] for i in fix.get("issues", []))
            if issues_set & fix_issues:  # Any overlap
                similar.append(fix)

        return similar

    def _get_context_for_recommendation(
        self, trace_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get context for generating recommendation."""
        if self._context_aggregator:
            ctx = self._context_aggregator.get_context(trace_id)
            if ctx:
                return {
                    "total_spans": len(ctx.spans),
                    "total_issues": ctx.total_issues,
                    "avg_score": ctx.avg_evaluation_score,
                    "quality_degradation": ctx.quality_degradation,
                }
        return None

    async def _learn_from_interaction(
        self,
        span_id: str,
        trace_id: str,
        issues: List[str],
        result: RemediationResult,
    ) -> None:
        """Learn from this interaction to improve future remediation."""
        # Store in history
        self._issue_fix_history.append({
            "span_id": span_id,
            "trace_id": trace_id,
            "issues": issues,
            "strategy": result.strategy_used.value if result.strategy_used else None,
            "success": result.success,
            "fix_applied": result.fix_applied,
            "timestamp": time.time(),
        })

        # Limit history size
        if len(self._issue_fix_history) > 1000:
            self._issue_fix_history = self._issue_fix_history[-500:]

        # Update workflow patterns
        if self._context_aggregator:
            ctx = self._context_aggregator.get_context(trace_id)
            if ctx:
                await self._update_workflow_pattern(ctx, result)

    async def _update_workflow_pattern(
        self,
        ctx: "AggregatedContext",
        result: RemediationResult,
    ) -> None:
        """Update workflow pattern based on observed trace."""
        # Create pattern signature from span sequence
        span_sequence = [s.span_type for s in ctx.spans[:10]]
        pattern_key = "_".join(span_sequence)

        if pattern_key not in self._workflow_patterns:
            self._workflow_patterns[pattern_key] = WorkflowPattern(
                pattern_id=pattern_key,
                name=f"Pattern {len(self._workflow_patterns) + 1}",
                description=f"Workflow with {len(span_sequence)} spans",
                span_sequence=span_sequence,
                common_issues=[],
                successful_fixes=[],
            )
            self._stats["patterns_learned"] += 1

        pattern = self._workflow_patterns[pattern_key]
        pattern.occurrence_count += 1

        # Track issues
        if result.issues_addressed:
            for issue in result.issues_addressed:
                if issue not in pattern.common_issues:
                    pattern.common_issues.append(issue)

        # Track successful fixes
        if result.fix_applied and result.success:
            pattern.successful_fixes.append({
                "strategy": result.strategy_used.value if result.strategy_used else None,
                "issues": result.issues_addressed,
                "description": result.action_taken,
            })

            # Update success rate
            total_fixes = len(pattern.successful_fixes)
            pattern.fix_success_rate = (
                pattern.fix_success_rate * (total_fixes - 1) + 1.0
            ) / total_fixes

        # Update confidence
        pattern.confidence = min(
            1.0,
            pattern.occurrence_count / self.config.learning_threshold,
        )

    async def _report_recommendation(self, result: RemediationResult) -> None:
        """Report recommendation to backend."""
        if not self._backend_client:
            return

        try:
            if hasattr(self._backend_client, "report_recommendation"):
                await self._backend_client.report_recommendation(
                    span_id=result.span_id,
                    recommendation=result.recommendation,
                    strategy=result.recommended_strategy.value if result.recommended_strategy else None,
                    issues=result.issues_addressed,
                    confidence=result.confidence,
                )
        except Exception as e:
            logger.warning(f"Failed to report recommendation to backend: {e}")

    async def _safe_callback(self, callback: Callable, **kwargs) -> None:
        """Safely call a callback function."""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(**kwargs)
            else:
                await asyncio.get_event_loop().run_in_executor(
                    None, lambda: callback(**kwargs)
                )
        except Exception as e:
            logger.warning(f"Callback error: {e}")

    def get_pending_recommendations(self) -> List[RemediationResult]:
        """Get pending recommendations for user review."""
        return list(self._pending_recommendations)

    def clear_pending_recommendations(self) -> None:
        """Clear pending recommendations."""
        self._pending_recommendations.clear()

    def accept_recommendation(self, span_id: str) -> bool:
        """Mark a recommendation as accepted (user applied it manually)."""
        for rec in self._pending_recommendations:
            if rec.span_id == span_id:
                self._stats["recommendations_accepted"] += 1

                # Learn from acceptance
                if self.config.learn_from_manual_fixes:
                    self._issue_fix_history.append({
                        "span_id": span_id,
                        "issues": rec.issues_addressed,
                        "strategy": rec.recommended_strategy.value if rec.recommended_strategy else None,
                        "success": True,
                        "manual": True,
                        "timestamp": time.time(),
                    })

                self._pending_recommendations.remove(rec)
                return True
        return False

    def get_workflow_patterns(self) -> List[WorkflowPattern]:
        """Get learned workflow patterns."""
        return list(self._workflow_patterns.values())

    def is_ready_for_autonomous(self) -> Dict[str, Any]:
        """Check if the system is ready for autonomous mode."""
        traces_ready = self._traces_processed >= self.config.learning_threshold

        patterns_ready = False
        avg_confidence = 0.0
        if self._workflow_patterns:
            avg_confidence = sum(
                p.confidence for p in self._workflow_patterns.values()
            ) / len(self._workflow_patterns)
            patterns_ready = avg_confidence >= self.config.min_workflow_confidence

        return {
            "ready": traces_ready and patterns_ready,
            "traces_processed": self._traces_processed,
            "traces_needed": self.config.learning_threshold,
            "patterns_learned": len(self._workflow_patterns),
            "avg_pattern_confidence": avg_confidence,
            "confidence_needed": self.config.min_workflow_confidence,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get remediation loop statistics."""
        return {
            **self._stats,
            "current_mode": self.config.mode.value,
            "auto_fix_enabled": self.config.auto_fix_enabled,
            "patterns_learned": len(self._workflow_patterns),
            "pending_recommendations": len(self._pending_recommendations),
            "fix_history_size": len(self._issue_fix_history),
            "ready_for_autonomous": self.is_ready_for_autonomous()["ready"],
        }

    def reset_stats(self) -> None:
        """Reset statistics."""
        self._stats = {
            "recommendations_generated": 0,
            "recommendations_accepted": 0,
            "auto_fixes_attempted": 0,
            "auto_fixes_successful": 0,
            "patterns_learned": 0,
            "traces_analyzed": 0,
            "mode_switches": 0,
        }
