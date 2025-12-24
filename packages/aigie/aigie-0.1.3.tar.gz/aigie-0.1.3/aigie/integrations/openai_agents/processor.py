"""
Aigie Tracing Processor for OpenAI Agents SDK.

Implements the TracingProcessor interface from OpenAI Agents SDK
to send traces to Aigie backend.
"""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AigieTracingProcessor:
    """Tracing processor that sends OpenAI Agents SDK traces to Aigie.

    This implements the TracingProcessor interface from OpenAI Agents SDK,
    allowing seamless integration with their built-in tracing system.

    Usage:
        from agents import add_trace_processor
        from aigie.integrations.openai_agents import AigieTracingProcessor

        processor = AigieTracingProcessor()
        add_trace_processor(processor)  # Additive to existing tracing

        # Now all agent operations are automatically traced to Aigie
        result = await Runner.run(agent, "Hello!")
    """

    def __init__(
        self,
        trace_name: str = "OpenAI Agents Workflow",
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """Initialize the Aigie tracing processor.

        Args:
            trace_name: Default name for traces
            metadata: Additional metadata to attach to all traces
            tags: Tags for filtering traces
            user_id: User identifier
            session_id: Session identifier
        """
        self.trace_name = trace_name
        self.metadata = metadata or {}
        self.tags = tags or []
        self.user_id = user_id
        self.session_id = session_id

        # State
        self._aigie: Any = None
        self._trace_id: Optional[str] = None
        self._span_map: Dict[str, Dict[str, Any]] = {}
        self._trace_map: Dict[str, str] = {}  # Maps SDK trace IDs to Aigie trace IDs

        # Statistics
        self.total_tokens = 0
        self.total_cost = 0.0

        # Try to get aigie client
        self._init_aigie()

    def _init_aigie(self) -> None:
        """Initialize aigie client."""
        try:
            from ...client import get_aigie
            self._aigie = get_aigie()
        except Exception as e:
            logger.debug(f"Could not get aigie client: {e}")

    # TracingProcessor interface methods

    def on_trace_start(self, trace_id: str, name: str, **kwargs) -> None:
        """Called when a new trace starts.

        Args:
            trace_id: Unique trace identifier from SDK
            name: Trace name
            **kwargs: Additional trace metadata
        """
        aigie_trace_id = str(uuid.uuid4())
        self._trace_map[trace_id] = aigie_trace_id
        self._trace_id = aigie_trace_id

        trace_data = {
            "name": name or self.trace_name,
            "start_time": time.time(),
            "metadata": {
                "sdk_trace_id": trace_id,
                **self.metadata,
                **kwargs,
            },
        }

        self._span_map[aigie_trace_id] = trace_data

        logger.debug(f"Trace started: {name} (id={trace_id})")

        # Create trace via aigie
        if self._aigie and self._aigie._initialized:
            try:
                from ...buffer import EventType
                self._aigie._buffer.add_event(
                    EventType.CREATE_TRACE,
                    trace_id=aigie_trace_id,
                    name=trace_data["name"],
                    metadata=trace_data["metadata"],
                    tags=self.tags,
                    user_id=self.user_id,
                    session_id=self.session_id,
                )
            except Exception as e:
                logger.debug(f"Error creating trace: {e}")

    def on_trace_end(self, trace_id: str, **kwargs) -> None:
        """Called when a trace ends.

        Args:
            trace_id: Trace identifier from SDK
            **kwargs: Additional end metadata
        """
        aigie_trace_id = self._trace_map.get(trace_id)
        if not aigie_trace_id:
            return

        if aigie_trace_id in self._span_map:
            trace_data = self._span_map[aigie_trace_id]
            trace_data["end_time"] = time.time()
            trace_data["duration"] = trace_data["end_time"] - trace_data["start_time"]
            trace_data["metadata"].update({
                "total_tokens": self.total_tokens,
                "total_cost": self.total_cost,
                **kwargs,
            })

        logger.debug(f"Trace ended: {trace_id}")

        # Update trace via aigie
        if self._aigie and self._aigie._initialized:
            try:
                from ...buffer import EventType
                self._aigie._buffer.add_event(
                    EventType.END_TRACE,
                    trace_id=aigie_trace_id,
                    metadata=trace_data.get("metadata", {}),
                )
            except Exception as e:
                logger.debug(f"Error ending trace: {e}")

    def on_span_start(
        self,
        span_id: str,
        trace_id: str,
        parent_span_id: Optional[str],
        name: str,
        span_type: str,
        **kwargs,
    ) -> None:
        """Called when a new span starts.

        Args:
            span_id: Unique span identifier
            trace_id: Parent trace identifier
            parent_span_id: Parent span identifier (if nested)
            name: Span name
            span_type: Type of span (agent, llm, tool, etc.)
            **kwargs: Additional span metadata
        """
        aigie_trace_id = self._trace_map.get(trace_id, self._trace_id)

        span_data = {
            "name": name,
            "type": self._map_span_type(span_type),
            "start_time": time.time(),
            "trace_id": aigie_trace_id,
            "parent_span_id": parent_span_id,
            "metadata": kwargs,
        }

        self._span_map[span_id] = span_data

        logger.debug(f"Span started: {name} (type={span_type})")

        # Create span via aigie
        if self._aigie and self._aigie._initialized:
            try:
                from ...buffer import EventType
                self._aigie._buffer.add_event(
                    EventType.CREATE_SPAN,
                    trace_id=aigie_trace_id,
                    span_id=span_id,
                    parent_span_id=parent_span_id,
                    name=name,
                    span_type=span_data["type"],
                    metadata=kwargs,
                )
            except Exception as e:
                logger.debug(f"Error creating span: {e}")

    def on_span_end(self, span_id: str, **kwargs) -> None:
        """Called when a span ends.

        Args:
            span_id: Span identifier
            **kwargs: Additional end metadata (output, error, etc.)
        """
        if span_id not in self._span_map:
            return

        span_data = self._span_map[span_id]
        span_data["end_time"] = time.time()
        span_data["duration"] = span_data["end_time"] - span_data["start_time"]
        span_data["metadata"].update(kwargs)

        # Extract common fields
        output = kwargs.get("output")
        error = kwargs.get("error")
        status = "error" if error else "success"

        logger.debug(f"Span ended: {span_data['name']}")

        # Update span via aigie
        if self._aigie and self._aigie._initialized:
            try:
                from ...buffer import EventType
                self._aigie._buffer.add_event(
                    EventType.UPDATE_SPAN,
                    span_id=span_id,
                    output=output,
                    metadata=span_data["metadata"],
                    status=status,
                )
            except Exception as e:
                logger.debug(f"Error updating span: {e}")

    def on_generation(
        self,
        span_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        **kwargs,
    ) -> None:
        """Called when an LLM generation completes.

        Args:
            span_id: Span identifier
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            **kwargs: Additional generation metadata
        """
        # Update statistics
        self.total_tokens += input_tokens + output_tokens

        # Calculate cost
        try:
            from .cost_tracking import get_openai_agents_cost
            cost_info = get_openai_agents_cost(model, input_tokens, output_tokens)
            if cost_info:
                self.total_cost += cost_info.get("total_cost", 0.0)
        except Exception:
            pass

        if span_id in self._span_map:
            self._span_map[span_id]["metadata"].update({
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                **kwargs,
            })

        logger.debug(f"Generation recorded: {model} ({input_tokens}+{output_tokens} tokens)")

        # Update span with usage
        if self._aigie and self._aigie._initialized:
            try:
                from ...buffer import EventType
                self._aigie._buffer.add_event(
                    EventType.UPDATE_SPAN,
                    span_id=span_id,
                    usage={
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": input_tokens + output_tokens,
                        "model": model,
                    },
                )
            except Exception as e:
                logger.debug(f"Error updating generation span: {e}")

    def on_tool_call(
        self,
        span_id: str,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        result: Optional[Any] = None,
        **kwargs,
    ) -> None:
        """Called when a tool call completes.

        Args:
            span_id: Span identifier
            tool_name: Name of the tool
            arguments: Tool arguments
            result: Tool result
            **kwargs: Additional tool metadata
        """
        if span_id in self._span_map:
            self._span_map[span_id]["metadata"].update({
                "tool_name": tool_name,
                "has_arguments": arguments is not None,
                "has_result": result is not None,
                **kwargs,
            })

        logger.debug(f"Tool call recorded: {tool_name}")

    def on_handoff(
        self,
        span_id: str,
        source_agent: str,
        target_agent: str,
        **kwargs,
    ) -> None:
        """Called when an agent handoff occurs.

        Args:
            span_id: Span identifier
            source_agent: Agent initiating handoff
            target_agent: Agent receiving handoff
            **kwargs: Additional handoff metadata
        """
        if span_id in self._span_map:
            self._span_map[span_id]["metadata"].update({
                "handoff_source": source_agent,
                "handoff_target": target_agent,
                **kwargs,
            })

        logger.debug(f"Handoff recorded: {source_agent} -> {target_agent}")

    def on_guardrail(
        self,
        span_id: str,
        guardrail_name: str,
        passed: bool,
        **kwargs,
    ) -> None:
        """Called when a guardrail check completes.

        Args:
            span_id: Span identifier
            guardrail_name: Name of the guardrail
            passed: Whether the check passed
            **kwargs: Additional guardrail metadata
        """
        if span_id in self._span_map:
            self._span_map[span_id]["metadata"].update({
                "guardrail_name": guardrail_name,
                "guardrail_passed": passed,
                **kwargs,
            })

        logger.debug(f"Guardrail recorded: {guardrail_name} (passed={passed})")

    def _map_span_type(self, sdk_type: str) -> str:
        """Map SDK span type to Aigie span type.

        Args:
            sdk_type: Span type from SDK

        Returns:
            Aigie span type
        """
        type_mapping = {
            "agent": "agent",
            "llm": "llm",
            "generation": "llm",
            "tool": "tool",
            "function": "tool",
            "handoff": "chain",
            "guardrail": "tool",
            "workflow": "chain",
            "runner": "chain",
        }
        return type_mapping.get(sdk_type.lower(), "chain")

    def get_statistics(self) -> Dict[str, Any]:
        """Get current tracing statistics."""
        return {
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "trace_count": len(self._trace_map),
            "span_count": len(self._span_map),
        }

    def flush(self) -> None:
        """Flush any pending traces to the backend."""
        if self._aigie and self._aigie._initialized:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Schedule flush
                    asyncio.ensure_future(self._aigie._buffer.flush())
                else:
                    loop.run_until_complete(self._aigie._buffer.flush())
            except Exception as e:
                logger.debug(f"Error flushing traces: {e}")

    def shutdown(self) -> None:
        """Shutdown the processor and flush remaining traces."""
        self.flush()
        self._span_map.clear()
        self._trace_map.clear()
