"""
Span Interceptor for step-level retry and remediation.

Intercepts each span (LLM call) after execution, evaluates the output
using the LLM Judge, and triggers retry with remediation if issues detected.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ..judge.evaluator import LLMJudge, SpanEvaluation, JudgeDecision
    from ..judge.context_aggregator import ContextAggregator
    from ..interceptor.protocols import InterceptionContext

logger = logging.getLogger("aigie.runtime")


class SpanDecision(Enum):
    """Decision for a span after evaluation."""

    CONTINUE = "continue"
    """Continue to next span normally."""

    RETRY = "retry"
    """Retry this span with remediation."""

    STOP = "stop"
    """Stop execution completely."""

    ESCALATE = "escalate"
    """Escalate to human/backend for decision."""


@dataclass
class SpanInterceptorConfig:
    """Configuration for the span interceptor."""

    # Retry settings
    max_retries: int = 3
    """Maximum retries per span."""

    retry_delay_ms: float = 100.0
    """Delay between retries in milliseconds."""

    exponential_backoff: bool = True
    """Use exponential backoff for retries."""

    max_retry_delay_ms: float = 5000.0
    """Maximum retry delay in milliseconds."""

    # Evaluation settings
    evaluate_all_spans: bool = True
    """Evaluate all spans (vs only on error)."""

    skip_evaluation_on_success: bool = False
    """Skip evaluation if span completed without error."""

    # Threshold settings
    stop_on_critical: bool = True
    """Stop execution on critical issues."""

    stop_on_repeated_failure: bool = True
    """Stop if same issue repeats multiple times."""

    repeated_failure_threshold: int = 3
    """Number of repeated failures before stopping."""

    # Performance settings
    async_evaluation: bool = True
    """Run evaluation asynchronously where possible."""

    evaluation_timeout_ms: float = 500.0
    """Timeout for evaluation in milliseconds."""

    # Integration
    notify_on_retry: bool = True
    """Notify on retry (via callback)."""

    notify_on_stop: bool = True
    """Notify on stop (via callback)."""


@dataclass
class SpanInterceptionResult:
    """Result of span interception."""

    span_id: str
    """ID of the intercepted span."""

    decision: SpanDecision
    """Decision made for this span."""

    original_output: Optional[str] = None
    """Original output before any modification."""

    modified_output: Optional[str] = None
    """Modified output after remediation."""

    retry_count: int = 0
    """Number of retries attempted."""

    issues_detected: List[str] = field(default_factory=list)
    """Issues detected during evaluation."""

    remediation_applied: Optional[str] = None
    """Description of remediation applied."""

    evaluation_score: float = 1.0
    """Final evaluation score."""

    total_time_ms: float = 0.0
    """Total time including retries."""

    retry_history: List[Dict[str, Any]] = field(default_factory=list)
    """History of retry attempts."""


class SpanInterceptor:
    """
    Intercepts spans for step-level evaluation and retry.

    Works with the LLM Judge to evaluate each span's output
    and trigger retry with remediation when issues are detected.

    Features:
    - Step-level interception after each LLM call
    - Automatic retry with remediation
    - Issue tracking and history
    - Configurable retry policies
    - Integration with context aggregator
    """

    def __init__(
        self,
        config: Optional[SpanInterceptorConfig] = None,
        judge: Optional["LLMJudge"] = None,
        context_aggregator: Optional["ContextAggregator"] = None,
        retry_callback: Optional[Callable] = None,
        stop_callback: Optional[Callable] = None,
    ):
        """
        Initialize the span interceptor.

        Args:
            config: Interceptor configuration
            judge: LLM Judge for evaluation
            context_aggregator: Context aggregator for full history
            retry_callback: Callback when retry is triggered
            stop_callback: Callback when execution is stopped
        """
        self.config = config or SpanInterceptorConfig()
        self._judge = judge
        self._context_aggregator = context_aggregator
        self._retry_callback = retry_callback
        self._stop_callback = stop_callback

        # State tracking
        self._span_retry_counts: Dict[str, int] = {}
        self._issue_history: Dict[str, List[str]] = {}  # span_id -> issues
        self._repeated_issues: Dict[str, int] = {}  # issue_type -> count

        # Stats
        self._stats = {
            "spans_intercepted": 0,
            "retries_triggered": 0,
            "stops_triggered": 0,
            "issues_detected": 0,
            "successful_remediations": 0,
            "failed_remediations": 0,
            "total_retry_time_ms": 0.0,
        }

    def set_judge(self, judge: "LLMJudge") -> None:
        """Set the LLM Judge."""
        self._judge = judge

    def set_context_aggregator(self, aggregator: "ContextAggregator") -> None:
        """Set the context aggregator."""
        self._context_aggregator = aggregator

    async def intercept_span(
        self,
        span_id: str,
        trace_id: str,
        input_messages: List[Dict[str, Any]],
        output_content: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        error: Optional[Exception] = None,
        context: Optional["InterceptionContext"] = None,
        llm_call: Optional[Callable] = None,
    ) -> SpanInterceptionResult:
        """
        Intercept a span after execution for evaluation and potential retry.

        Args:
            span_id: ID of the span
            trace_id: ID of the trace
            input_messages: Input messages sent to LLM
            output_content: Output content from LLM
            model: Model used
            provider: Provider used
            error: Error if span failed
            context: Full interception context
            llm_call: Callable to retry the LLM call if needed

        Returns:
            SpanInterceptionResult with decision and any modifications
        """
        start_time = time.perf_counter()
        self._stats["spans_intercepted"] += 1

        # Initialize result
        result = SpanInterceptionResult(
            span_id=span_id,
            original_output=output_content,
            retry_count=0,
        )

        # Track span in context aggregator
        if self._context_aggregator:
            self._context_aggregator.add_span(
                trace_id=trace_id,
                span_id=span_id,
                span_type="llm",
                input_messages=input_messages,
                model=model,
                provider=provider,
            )

        # Check if we should skip evaluation
        if (
            self.config.skip_evaluation_on_success
            and not error
            and output_content
            and len(output_content.strip()) > 10
        ):
            result.decision = SpanDecision.CONTINUE
            result.evaluation_score = 1.0
            return result

        # Handle error case
        if error:
            result.issues_detected.append(f"Error: {str(error)}")
            self._stats["issues_detected"] += 1

            # Decide whether to retry or stop
            if llm_call and self._can_retry(span_id):
                result.decision = SpanDecision.RETRY
            else:
                result.decision = SpanDecision.STOP
                self._stats["stops_triggered"] += 1
                if self.config.notify_on_stop and self._stop_callback:
                    await self._safe_callback(
                        self._stop_callback,
                        span_id=span_id,
                        reason="Max retries exceeded" if self._span_retry_counts.get(span_id, 0) >= self.config.max_retries else str(error),
                    )

            result.total_time_ms = (time.perf_counter() - start_time) * 1000
            return result

        # Evaluate with judge if available
        if self._judge and self.config.evaluate_all_spans:
            evaluation = await self._evaluate_span(
                span_id=span_id,
                input_messages=input_messages,
                output_content=output_content,
                context=context,
            )

            result.evaluation_score = evaluation.result.overall_score if evaluation else 1.0

            if evaluation and evaluation.result.has_issues:
                result.issues_detected = [
                    issue.description for issue in evaluation.result.issues
                ]
                self._stats["issues_detected"] += len(result.issues_detected)

                # Track repeated issues
                self._track_issues(result.issues_detected)

                # Check for repeated failure
                if self._should_stop_on_repeated_failure():
                    result.decision = SpanDecision.STOP
                    self._stats["stops_triggered"] += 1
                    if self.config.notify_on_stop and self._stop_callback:
                        await self._safe_callback(
                            self._stop_callback,
                            span_id=span_id,
                            reason="Repeated failures detected",
                        )
                    result.total_time_ms = (time.perf_counter() - start_time) * 1000
                    return result

                # Decide based on evaluation
                from ..judge.evaluator import JudgeDecision

                if evaluation.decision == JudgeDecision.STOP:
                    result.decision = SpanDecision.STOP
                    self._stats["stops_triggered"] += 1
                    if self.config.notify_on_stop and self._stop_callback:
                        await self._safe_callback(
                            self._stop_callback,
                            span_id=span_id,
                            reason="Critical issue detected",
                        )
                elif evaluation.decision == JudgeDecision.RETRY:
                    if llm_call and self._can_retry(span_id):
                        # Attempt retry with remediation
                        retry_result = await self._retry_with_remediation(
                            span_id=span_id,
                            trace_id=trace_id,
                            input_messages=input_messages,
                            evaluation=evaluation,
                            llm_call=llm_call,
                            context=context,
                        )
                        result.retry_count = retry_result.retry_count
                        result.modified_output = retry_result.modified_output
                        result.decision = retry_result.decision
                        result.retry_history = retry_result.retry_history
                        result.remediation_applied = retry_result.remediation_applied
                    else:
                        # Can't retry - continue with warning
                        result.decision = SpanDecision.CONTINUE
                        logger.warning(
                            f"Cannot retry span {span_id}: "
                            f"{'no llm_call' if not llm_call else 'max retries reached'}"
                        )
                elif evaluation.decision == JudgeDecision.CONSULT:
                    result.decision = SpanDecision.ESCALATE
                else:
                    result.decision = SpanDecision.CONTINUE
            else:
                result.decision = SpanDecision.CONTINUE
        else:
            # No judge - continue by default
            result.decision = SpanDecision.CONTINUE

        # Complete span in context aggregator
        if self._context_aggregator:
            self._context_aggregator.complete_span(
                span_id=span_id,
                output_content=result.modified_output or output_content,
                status="success" if result.decision == SpanDecision.CONTINUE else "retry",
            )
            self._context_aggregator.record_evaluation(
                span_id=span_id,
                score=result.evaluation_score,
                issues=result.issues_detected,
                retry_triggered=result.retry_count > 0,
            )

        result.total_time_ms = (time.perf_counter() - start_time) * 1000
        return result

    async def _evaluate_span(
        self,
        span_id: str,
        input_messages: List[Dict[str, Any]],
        output_content: str,
        context: Optional["InterceptionContext"] = None,
    ) -> Optional["SpanEvaluation"]:
        """Evaluate a span using the LLM Judge."""
        if not self._judge:
            return None

        try:
            # Get full history if available
            full_history = None
            tool_results = None
            if self._context_aggregator:
                ctx = self._context_aggregator.get_context_for_span(span_id)
                if ctx:
                    full_history = ctx.all_messages
                    tool_results = ctx.tool_calls

            evaluation = await asyncio.wait_for(
                self._judge.evaluate_span(
                    span_id=span_id,
                    input_messages=input_messages,
                    output_content=output_content,
                    context=context,
                    full_history=full_history,
                    tool_results=tool_results,
                ),
                timeout=self.config.evaluation_timeout_ms / 1000.0,
            )
            return evaluation

        except asyncio.TimeoutError:
            logger.warning(f"Evaluation timed out for span {span_id}")
            return None
        except Exception as e:
            logger.error(f"Evaluation error for span {span_id}: {e}")
            return None

    async def _retry_with_remediation(
        self,
        span_id: str,
        trace_id: str,
        input_messages: List[Dict[str, Any]],
        evaluation: "SpanEvaluation",
        llm_call: Callable,
        context: Optional["InterceptionContext"] = None,
    ) -> SpanInterceptionResult:
        """Retry the span with remediation applied."""
        result = SpanInterceptionResult(
            span_id=span_id,
            original_output=evaluation.result.suggested_remediation,
        )

        retry_count = 0
        current_messages = input_messages.copy()
        current_delay = self.config.retry_delay_ms

        while retry_count < self.config.max_retries:
            retry_count += 1
            self._span_retry_counts[span_id] = self._span_retry_counts.get(span_id, 0) + 1
            self._stats["retries_triggered"] += 1

            # Apply remediation to messages
            modified_messages = self._apply_remediation(
                messages=current_messages,
                evaluation=evaluation,
                retry_count=retry_count,
            )

            # Notify about retry
            if self.config.notify_on_retry and self._retry_callback:
                await self._safe_callback(
                    self._retry_callback,
                    span_id=span_id,
                    retry_count=retry_count,
                    remediation=evaluation.remediation,
                )

            # Wait before retry
            if current_delay > 0:
                await asyncio.sleep(current_delay / 1000.0)

            # Track retry in history
            retry_entry = {
                "retry_number": retry_count,
                "delay_ms": current_delay,
                "remediation_applied": str(evaluation.remediation)[:200] if evaluation.remediation else None,
            }

            try:
                # Retry the LLM call
                retry_start = time.perf_counter()

                if asyncio.iscoroutinefunction(llm_call):
                    new_output = await llm_call(modified_messages)
                else:
                    new_output = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: llm_call(modified_messages)
                    )

                retry_entry["success"] = True
                retry_entry["duration_ms"] = (time.perf_counter() - retry_start) * 1000
                result.retry_history.append(retry_entry)

                # Re-evaluate the new output
                new_evaluation = await self._evaluate_span(
                    span_id=f"{span_id}_retry_{retry_count}",
                    input_messages=modified_messages,
                    output_content=new_output,
                    context=context,
                )

                if new_evaluation and not new_evaluation.result.has_issues:
                    # Success!
                    result.decision = SpanDecision.CONTINUE
                    result.modified_output = new_output
                    result.retry_count = retry_count
                    result.evaluation_score = new_evaluation.result.overall_score
                    result.remediation_applied = (
                        str(evaluation.remediation)[:200]
                        if evaluation.remediation
                        else "Automatic retry"
                    )
                    self._stats["successful_remediations"] += 1
                    self._stats["total_retry_time_ms"] += sum(
                        e.get("duration_ms", 0) for e in result.retry_history
                    )
                    return result

                # Still has issues - update evaluation for next retry
                if new_evaluation:
                    evaluation = new_evaluation

            except Exception as e:
                retry_entry["success"] = False
                retry_entry["error"] = str(e)
                result.retry_history.append(retry_entry)
                logger.warning(f"Retry {retry_count} failed for span {span_id}: {e}")

            # Increase delay for next retry
            if self.config.exponential_backoff:
                current_delay = min(
                    current_delay * 2,
                    self.config.max_retry_delay_ms,
                )

        # All retries exhausted
        result.decision = SpanDecision.STOP
        result.retry_count = retry_count
        self._stats["failed_remediations"] += 1
        self._stats["stops_triggered"] += 1

        if self.config.notify_on_stop and self._stop_callback:
            await self._safe_callback(
                self._stop_callback,
                span_id=span_id,
                reason=f"Max retries ({retry_count}) exhausted",
            )

        return result

    def _apply_remediation(
        self,
        messages: List[Dict[str, Any]],
        evaluation: "SpanEvaluation",
        retry_count: int,
    ) -> List[Dict[str, Any]]:
        """Apply remediation to messages for retry."""
        modified = messages.copy()

        # Add remediation instruction to system prompt or last user message
        remediation_instruction = None

        if evaluation.retry_prompt:
            remediation_instruction = evaluation.retry_prompt
        elif evaluation.remediation:
            # Build instruction from remediation
            issues = evaluation.remediation.get("issues_to_address", [])
            suggestion = evaluation.remediation.get("suggested_remediation", "")
            if issues or suggestion:
                remediation_instruction = f"Please address the following issues:\n"
                if issues:
                    remediation_instruction += "\n".join(f"- {i}" for i in issues[:5])
                if suggestion:
                    remediation_instruction += f"\n\nSuggested approach: {suggestion}"

        if remediation_instruction:
            # Try to inject into system prompt
            for i, msg in enumerate(modified):
                if msg.get("role") == "system":
                    modified[i] = msg.copy()
                    modified[i]["content"] = (
                        str(msg.get("content", ""))
                        + f"\n\n[RETRY {retry_count}] {remediation_instruction}"
                    )
                    return modified

            # No system prompt - add to beginning
            modified.insert(
                0,
                {
                    "role": "system",
                    "content": f"[RETRY {retry_count}] {remediation_instruction}",
                },
            )

        return modified

    def _can_retry(self, span_id: str) -> bool:
        """Check if a span can be retried."""
        current_retries = self._span_retry_counts.get(span_id, 0)
        return current_retries < self.config.max_retries

    def _track_issues(self, issues: List[str]) -> None:
        """Track issues for repeated failure detection."""
        for issue in issues:
            # Extract issue type (first word or category)
            issue_type = issue.split(":")[0].strip().lower()[:50]
            self._repeated_issues[issue_type] = (
                self._repeated_issues.get(issue_type, 0) + 1
            )

    def _should_stop_on_repeated_failure(self) -> bool:
        """Check if we should stop due to repeated failures."""
        if not self.config.stop_on_repeated_failure:
            return False

        for issue_type, count in self._repeated_issues.items():
            if count >= self.config.repeated_failure_threshold:
                logger.warning(
                    f"Repeated failure detected: {issue_type} ({count} times)"
                )
                return True

        return False

    async def _safe_callback(
        self, callback: Callable, **kwargs
    ) -> None:
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

    def reset_for_trace(self, trace_id: str) -> None:
        """Reset state for a new trace."""
        self._span_retry_counts.clear()
        self._issue_history.clear()
        self._repeated_issues.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get interceptor statistics."""
        return {
            **self._stats,
            "active_retry_counts": dict(self._span_retry_counts),
            "repeated_issues": dict(self._repeated_issues),
            "avg_retry_time_ms": (
                self._stats["total_retry_time_ms"]
                / max(self._stats["successful_remediations"], 1)
            ),
        }

    def reset_stats(self) -> None:
        """Reset interceptor statistics."""
        self._stats = {
            "spans_intercepted": 0,
            "retries_triggered": 0,
            "stops_triggered": 0,
            "issues_detected": 0,
            "successful_remediations": 0,
            "failed_remediations": 0,
            "total_retry_time_ms": 0.0,
        }
