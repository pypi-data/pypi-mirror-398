"""
Context Aggregator for LLM Judge.

Aggregates full context from the trace including all spans, messages,
tool results, and metadata for comprehensive evaluation.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from collections import defaultdict

if TYPE_CHECKING:
    from ..interceptor.protocols import InterceptionContext

logger = logging.getLogger("aigie.judge")


@dataclass
class SpanHistory:
    """History of a single span."""

    span_id: str
    """Unique span identifier."""

    parent_span_id: Optional[str] = None
    """Parent span ID if nested."""

    span_type: str = "llm"
    """Type of span: 'llm', 'tool', 'chain', 'agent'."""

    name: Optional[str] = None
    """Human-readable span name."""

    # Input/Output
    input_messages: List[Dict[str, Any]] = field(default_factory=list)
    """Input messages for this span."""

    output_content: Optional[str] = None
    """Output content from this span."""

    # Tool-specific
    tool_name: Optional[str] = None
    """Tool name if this is a tool span."""

    tool_input: Optional[Dict[str, Any]] = None
    """Tool input arguments."""

    tool_output: Optional[Any] = None
    """Tool output/result."""

    tool_error: Optional[str] = None
    """Tool error if failed."""

    # Timing
    started_at: Optional[datetime] = None
    """When the span started."""

    ended_at: Optional[datetime] = None
    """When the span ended."""

    duration_ms: float = 0.0
    """Duration in milliseconds."""

    # Token usage
    input_tokens: int = 0
    """Input tokens used."""

    output_tokens: int = 0
    """Output tokens generated."""

    cost: float = 0.0
    """Cost of this span."""

    # Model info
    model: Optional[str] = None
    """Model used for this span."""

    provider: Optional[str] = None
    """Provider (openai, anthropic, etc.)."""

    # Status
    status: str = "unknown"
    """Status: 'pending', 'running', 'success', 'error'."""

    error: Optional[str] = None
    """Error message if failed."""

    # Evaluation
    evaluation_score: Optional[float] = None
    """Evaluation score from judge."""

    issues_detected: List[str] = field(default_factory=list)
    """Issues detected by judge."""

    retry_count: int = 0
    """Number of retries for this span."""

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata."""


@dataclass
class AggregatedContext:
    """
    Aggregated context for a trace.

    Contains full history of all spans, messages, tool results,
    and derived metrics for comprehensive evaluation.
    """

    trace_id: str
    """Trace identifier."""

    # Spans
    spans: List[SpanHistory] = field(default_factory=list)
    """All spans in chronological order."""

    current_span: Optional[SpanHistory] = None
    """Currently executing span."""

    # Messages
    all_messages: List[Dict[str, Any]] = field(default_factory=list)
    """All messages across the trace."""

    system_prompt: Optional[str] = None
    """System prompt if available."""

    # Tool calls
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    """All tool calls with inputs/outputs."""

    tool_errors: List[Dict[str, Any]] = field(default_factory=list)
    """Tool calls that resulted in errors."""

    # Derived metrics
    total_input_tokens: int = 0
    """Total input tokens across all spans."""

    total_output_tokens: int = 0
    """Total output tokens across all spans."""

    total_cost: float = 0.0
    """Total cost across all spans."""

    total_duration_ms: float = 0.0
    """Total duration in milliseconds."""

    # Quality metrics
    avg_evaluation_score: float = 0.0
    """Average evaluation score across spans."""

    total_issues: int = 0
    """Total issues detected across spans."""

    total_retries: int = 0
    """Total retries across spans."""

    # Context analysis
    topic_drift_detected: bool = False
    """Whether topic drift was detected."""

    repetition_detected: bool = False
    """Whether repetition was detected."""

    quality_degradation: bool = False
    """Whether quality degradation was detected."""

    # Metadata
    started_at: Optional[datetime] = None
    """When the trace started."""

    user_id: Optional[str] = None
    """User ID if available."""

    session_id: Optional[str] = None
    """Session ID if available."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata."""

    def get_recent_messages(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent messages."""
        return self.all_messages[-count:] if self.all_messages else []

    def get_recent_tool_calls(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get the most recent tool calls."""
        return self.tool_calls[-count:] if self.tool_calls else []

    def get_spans_by_type(self, span_type: str) -> List[SpanHistory]:
        """Get spans of a specific type."""
        return [s for s in self.spans if s.span_type == span_type]

    def get_failed_spans(self) -> List[SpanHistory]:
        """Get spans that failed."""
        return [s for s in self.spans if s.status == "error"]

    def get_span_chain(self, span_id: str) -> List[SpanHistory]:
        """Get the chain of spans leading to a specific span."""
        chain = []
        span_map = {s.span_id: s for s in self.spans}

        current_id = span_id
        while current_id:
            span = span_map.get(current_id)
            if span:
                chain.insert(0, span)
                current_id = span.parent_span_id
            else:
                break

        return chain


class ContextAggregator:
    """
    Aggregates context from traces for comprehensive evaluation.

    Collects and organizes all span data, messages, tool results,
    and metrics for the LLM Judge to make informed decisions.
    """

    def __init__(
        self,
        max_history_size: int = 100,
        max_message_length: int = 5000,
        include_tool_outputs: bool = True,
        track_metrics: bool = True,
    ):
        """
        Initialize the context aggregator.

        Args:
            max_history_size: Maximum number of spans to track per trace
            max_message_length: Maximum length for message content
            include_tool_outputs: Whether to include tool outputs
            track_metrics: Whether to track quality metrics
        """
        self.max_history_size = max_history_size
        self.max_message_length = max_message_length
        self.include_tool_outputs = include_tool_outputs
        self.track_metrics = track_metrics

        # Storage
        self._traces: Dict[str, AggregatedContext] = {}
        self._span_to_trace: Dict[str, str] = {}

    def get_or_create_context(self, trace_id: str) -> AggregatedContext:
        """Get or create an aggregated context for a trace."""
        if trace_id not in self._traces:
            self._traces[trace_id] = AggregatedContext(
                trace_id=trace_id,
                started_at=datetime.utcnow(),
            )
        return self._traces[trace_id]

    def add_span(
        self,
        trace_id: str,
        span_id: str,
        span_type: str = "llm",
        parent_span_id: Optional[str] = None,
        name: Optional[str] = None,
        input_messages: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SpanHistory:
        """
        Add a new span to the context.

        Returns the created SpanHistory.
        """
        ctx = self.get_or_create_context(trace_id)

        # Create span
        span = SpanHistory(
            span_id=span_id,
            parent_span_id=parent_span_id,
            span_type=span_type,
            name=name,
            input_messages=input_messages or [],
            model=model,
            provider=provider,
            started_at=datetime.utcnow(),
            status="running",
            metadata=metadata or {},
        )

        # Add to context
        ctx.spans.append(span)
        ctx.current_span = span
        self._span_to_trace[span_id] = trace_id

        # Add messages to all_messages
        if input_messages:
            for msg in input_messages:
                # Truncate content if needed
                if msg.get("content") and len(str(msg["content"])) > self.max_message_length:
                    msg = msg.copy()
                    msg["content"] = str(msg["content"])[: self.max_message_length] + "..."
                ctx.all_messages.append(msg)

            # Extract system prompt
            for msg in input_messages:
                if msg.get("role") == "system":
                    ctx.system_prompt = str(msg.get("content", ""))
                    break

        # Enforce max history
        if len(ctx.spans) > self.max_history_size:
            ctx.spans = ctx.spans[-self.max_history_size :]

        return span

    def complete_span(
        self,
        span_id: str,
        output_content: Optional[str] = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost: float = 0.0,
        status: str = "success",
        error: Optional[str] = None,
    ) -> Optional[SpanHistory]:
        """
        Complete a span with output information.

        Returns the updated SpanHistory.
        """
        trace_id = self._span_to_trace.get(span_id)
        if not trace_id:
            logger.warning(f"Span {span_id} not found in any trace")
            return None

        ctx = self._traces.get(trace_id)
        if not ctx:
            return None

        # Find and update span
        for span in ctx.spans:
            if span.span_id == span_id:
                span.output_content = output_content
                span.input_tokens = input_tokens
                span.output_tokens = output_tokens
                span.cost = cost
                span.status = status
                span.error = error
                span.ended_at = datetime.utcnow()

                if span.started_at:
                    span.duration_ms = (
                        span.ended_at - span.started_at
                    ).total_seconds() * 1000

                # Add output as assistant message
                if output_content:
                    ctx.all_messages.append(
                        {
                            "role": "assistant",
                            "content": output_content[: self.max_message_length]
                            if len(output_content) > self.max_message_length
                            else output_content,
                        }
                    )

                # Update metrics
                if self.track_metrics:
                    self._update_metrics(ctx)

                # Clear current span if this was it
                if ctx.current_span and ctx.current_span.span_id == span_id:
                    ctx.current_span = None

                return span

        return None

    def add_tool_call(
        self,
        trace_id: str,
        span_id: Optional[str],
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: Optional[Any] = None,
        tool_error: Optional[str] = None,
    ) -> None:
        """Add a tool call to the context."""
        ctx = self.get_or_create_context(trace_id)

        tool_call = {
            "span_id": span_id,
            "tool_name": tool_name,
            "tool_input": tool_input,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if self.include_tool_outputs and tool_output is not None:
            # Truncate tool output if needed
            output_str = str(tool_output)
            if len(output_str) > self.max_message_length:
                output_str = output_str[: self.max_message_length] + "..."
            tool_call["tool_output"] = output_str

        if tool_error:
            tool_call["tool_error"] = tool_error
            ctx.tool_errors.append(tool_call)

        ctx.tool_calls.append(tool_call)

        # Update span if provided
        if span_id:
            for span in ctx.spans:
                if span.span_id == span_id:
                    span.tool_name = tool_name
                    span.tool_input = tool_input
                    span.tool_output = tool_output
                    span.tool_error = tool_error
                    break

    def record_evaluation(
        self,
        span_id: str,
        score: float,
        issues: Optional[List[str]] = None,
        retry_triggered: bool = False,
    ) -> None:
        """Record an evaluation result for a span."""
        trace_id = self._span_to_trace.get(span_id)
        if not trace_id:
            return

        ctx = self._traces.get(trace_id)
        if not ctx:
            return

        for span in ctx.spans:
            if span.span_id == span_id:
                span.evaluation_score = score
                span.issues_detected = issues or []
                if retry_triggered:
                    span.retry_count += 1
                break

        # Update metrics
        if self.track_metrics:
            self._update_metrics(ctx)

    def _update_metrics(self, ctx: AggregatedContext) -> None:
        """Update derived metrics for a context."""
        # Token and cost totals
        ctx.total_input_tokens = sum(s.input_tokens for s in ctx.spans)
        ctx.total_output_tokens = sum(s.output_tokens for s in ctx.spans)
        ctx.total_cost = sum(s.cost for s in ctx.spans)
        ctx.total_duration_ms = sum(s.duration_ms for s in ctx.spans)

        # Quality metrics
        evaluated_spans = [s for s in ctx.spans if s.evaluation_score is not None]
        if evaluated_spans:
            ctx.avg_evaluation_score = sum(
                s.evaluation_score for s in evaluated_spans
            ) / len(evaluated_spans)

        ctx.total_issues = sum(len(s.issues_detected) for s in ctx.spans)
        ctx.total_retries = sum(s.retry_count for s in ctx.spans)

        # Quality degradation detection
        if len(evaluated_spans) >= 3:
            recent_scores = [s.evaluation_score for s in evaluated_spans[-3:]]
            if all(s < 0.7 for s in recent_scores):
                ctx.quality_degradation = True

        # Repetition detection
        if ctx.all_messages:
            recent_contents = [
                m.get("content", "")[:200] for m in ctx.all_messages[-10:]
            ]
            unique_contents = set(recent_contents)
            if len(unique_contents) < len(recent_contents) * 0.6:
                ctx.repetition_detected = True

    def get_context(self, trace_id: str) -> Optional[AggregatedContext]:
        """Get the aggregated context for a trace."""
        return self._traces.get(trace_id)

    def get_context_for_span(self, span_id: str) -> Optional[AggregatedContext]:
        """Get the aggregated context for a span's trace."""
        trace_id = self._span_to_trace.get(span_id)
        if trace_id:
            return self._traces.get(trace_id)
        return None

    def build_context_for_judge(
        self,
        span_id: str,
        include_full_history: bool = True,
        history_window: int = 10,
    ) -> Dict[str, Any]:
        """
        Build context dictionary for the judge.

        Returns a dictionary with all relevant context for evaluation.
        """
        ctx = self.get_context_for_span(span_id)
        if not ctx:
            return {}

        # Find current span
        current_span = None
        for span in ctx.spans:
            if span.span_id == span_id:
                current_span = span
                break

        # Build context
        context = {
            "trace_id": ctx.trace_id,
            "span_id": span_id,
            "system_prompt": ctx.system_prompt,
            "current_span": {
                "input_messages": current_span.input_messages if current_span else [],
                "output_content": current_span.output_content if current_span else None,
                "model": current_span.model if current_span else None,
                "provider": current_span.provider if current_span else None,
                "retry_count": current_span.retry_count if current_span else 0,
            },
            "metrics": {
                "total_input_tokens": ctx.total_input_tokens,
                "total_output_tokens": ctx.total_output_tokens,
                "total_cost": ctx.total_cost,
                "total_duration_ms": ctx.total_duration_ms,
                "avg_evaluation_score": ctx.avg_evaluation_score,
                "total_issues": ctx.total_issues,
                "total_retries": ctx.total_retries,
            },
            "quality_flags": {
                "topic_drift_detected": ctx.topic_drift_detected,
                "repetition_detected": ctx.repetition_detected,
                "quality_degradation": ctx.quality_degradation,
            },
        }

        # Add history
        if include_full_history:
            context["full_history"] = ctx.all_messages
            context["all_tool_calls"] = ctx.tool_calls
        else:
            context["recent_messages"] = ctx.get_recent_messages(history_window)
            context["recent_tool_calls"] = ctx.get_recent_tool_calls(5)

        # Add tool errors
        if ctx.tool_errors:
            context["tool_errors"] = ctx.tool_errors

        # Add failed spans
        failed_spans = ctx.get_failed_spans()
        if failed_spans:
            context["failed_spans"] = [
                {
                    "span_id": s.span_id,
                    "name": s.name,
                    "error": s.error,
                    "tool_name": s.tool_name,
                }
                for s in failed_spans
            ]

        # Add span chain
        if current_span:
            chain = ctx.get_span_chain(span_id)
            if chain:
                context["span_chain"] = [
                    {
                        "span_id": s.span_id,
                        "name": s.name,
                        "span_type": s.span_type,
                        "status": s.status,
                    }
                    for s in chain
                ]

        return context

    def cleanup_trace(self, trace_id: str) -> None:
        """Remove a trace from memory."""
        if trace_id in self._traces:
            ctx = self._traces[trace_id]
            # Clean up span mapping
            for span in ctx.spans:
                if span.span_id in self._span_to_trace:
                    del self._span_to_trace[span.span_id]
            del self._traces[trace_id]

    def cleanup_old_traces(self, max_age_seconds: int = 3600) -> int:
        """
        Remove traces older than max_age_seconds.

        Returns the number of traces cleaned up.
        """
        cutoff = datetime.utcnow()
        old_traces = []

        for trace_id, ctx in self._traces.items():
            if ctx.started_at:
                age = (cutoff - ctx.started_at).total_seconds()
                if age > max_age_seconds:
                    old_traces.append(trace_id)

        for trace_id in old_traces:
            self.cleanup_trace(trace_id)

        return len(old_traces)

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregator statistics."""
        return {
            "active_traces": len(self._traces),
            "tracked_spans": len(self._span_to_trace),
            "total_messages": sum(
                len(ctx.all_messages) for ctx in self._traces.values()
            ),
            "total_tool_calls": sum(
                len(ctx.tool_calls) for ctx in self._traces.values()
            ),
        }
