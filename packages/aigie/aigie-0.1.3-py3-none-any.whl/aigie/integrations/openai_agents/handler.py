"""
OpenAI Agents SDK Handler for Aigie integration.

Provides event-driven tracing for OpenAI Agents SDK workflows.
"""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class OpenAIAgentsHandler:
    """Handler for OpenAI Agents SDK tracing integration.

    This handler provides lifecycle methods for tracing agent workflows,
    generations, tool calls, handoffs, and guardrails.

    Example:
        handler = OpenAIAgentsHandler(trace_name="Agent Workflow")
        handler.set_trace_context(trace)

        # Track workflow
        workflow_id = await handler.handle_workflow_start("main_workflow")

        # Track agent
        agent_id = await handler.handle_agent_start("assistant", model="gpt-4o")

        # Track generation
        gen_id = await handler.handle_generation_start("gpt-4o", messages)
        await handler.handle_generation_end(gen_id, response, tokens)

        # Track tool call
        tool_id = await handler.handle_tool_start("search", args)
        await handler.handle_tool_end(tool_id, result)

        await handler.handle_agent_end(agent_id, output)
        await handler.handle_workflow_end(workflow_id)
    """

    def __init__(
        self,
        trace_name: str = "OpenAI Agents Workflow",
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """Initialize the handler.

        Args:
            trace_name: Name for the trace
            metadata: Additional metadata to attach
            tags: Tags for filtering
            user_id: User identifier
            session_id: Session identifier
        """
        self.trace_name = trace_name
        self.metadata = metadata or {}
        self.tags = tags or []
        self.user_id = user_id
        self.session_id = session_id

        # State tracking
        self.trace_id: Optional[str] = None
        self.span_map: Dict[str, Dict[str, Any]] = {}
        self._current_span_id: Optional[str] = None
        self._trace_context: Any = None
        self._aigie: Any = None

        # Statistics
        self.total_tokens = 0
        self.total_cost = 0.0
        self.generation_count = 0
        self.tool_call_count = 0
        self.handoff_count = 0
        self.agent_count = 0

    def set_trace_context(self, trace: Any) -> None:
        """Set the trace context for this handler."""
        self._trace_context = trace
        if hasattr(trace, 'id'):
            self.trace_id = trace.id

    async def handle_workflow_start(
        self,
        workflow_name: str,
        agents: Optional[List[str]] = None,
        input_data: Optional[Any] = None,
    ) -> str:
        """Handle workflow start event.

        Args:
            workflow_name: Name of the workflow
            agents: List of agent names in the workflow
            input_data: Initial input to the workflow

        Returns:
            Workflow span ID
        """
        workflow_id = str(uuid.uuid4())

        span_data = {
            "name": f"workflow:{workflow_name}",
            "type": "chain",
            "start_time": time.time(),
            "metadata": {
                "workflow_name": workflow_name,
                "agents": agents or [],
                "agent_count": len(agents) if agents else 0,
            },
        }

        if input_data:
            span_data["input"] = self._safe_str(input_data)

        self.span_map[workflow_id] = span_data
        self._current_span_id = workflow_id

        logger.debug(f"Started workflow trace: {workflow_name}")

        # Create span via aigie if available
        if self._aigie and self._aigie._initialized:
            try:
                from ...buffer import EventType
                self._aigie._buffer.add_event(
                    EventType.CREATE_SPAN,
                    trace_id=self.trace_id,
                    span_id=workflow_id,
                    name=span_data["name"],
                    span_type=span_data["type"],
                    metadata=span_data["metadata"],
                )
            except Exception as e:
                logger.debug(f"Error creating workflow span: {e}")

        return workflow_id

    async def handle_workflow_end(
        self,
        workflow_id: str,
        output: Optional[Any] = None,
        error: Optional[str] = None,
    ) -> None:
        """Handle workflow end event.

        Args:
            workflow_id: Workflow span ID
            output: Workflow output
            error: Error message if failed
        """
        if workflow_id not in self.span_map:
            return

        span_data = self.span_map[workflow_id]
        span_data["end_time"] = time.time()
        span_data["duration"] = span_data["end_time"] - span_data["start_time"]

        if output:
            span_data["output"] = self._safe_str(output)
        if error:
            span_data["error"] = error
            span_data["status"] = "error"
        else:
            span_data["status"] = "success"

        # Add statistics
        span_data["metadata"].update({
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "generation_count": self.generation_count,
            "tool_call_count": self.tool_call_count,
            "handoff_count": self.handoff_count,
            "agent_count": self.agent_count,
        })

        logger.debug(f"Ended workflow trace: {span_data['name']}")

        # Update span via aigie
        if self._aigie and self._aigie._initialized:
            try:
                from ...buffer import EventType
                self._aigie._buffer.add_event(
                    EventType.UPDATE_SPAN,
                    span_id=workflow_id,
                    output=span_data.get("output"),
                    metadata=span_data["metadata"],
                    status=span_data.get("status", "success"),
                )
            except Exception as e:
                logger.debug(f"Error updating workflow span: {e}")

    async def handle_agent_start(
        self,
        agent_name: str,
        model: Optional[str] = None,
        instructions: Optional[str] = None,
        tools: Optional[List[str]] = None,
        handoffs: Optional[List[str]] = None,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """Handle agent start event.

        Args:
            agent_name: Name of the agent
            model: Model used by the agent
            instructions: Agent instructions
            tools: List of available tools
            handoffs: List of possible handoff targets
            parent_span_id: Parent span ID

        Returns:
            Agent span ID
        """
        agent_id = str(uuid.uuid4())
        self.agent_count += 1

        span_data = {
            "name": f"agent:{agent_name}",
            "type": "agent",
            "start_time": time.time(),
            "parent_span_id": parent_span_id or self._current_span_id,
            "metadata": {
                "agent_name": agent_name,
                "model": model,
                "tools": tools or [],
                "tool_count": len(tools) if tools else 0,
                "handoffs": handoffs or [],
                "handoff_count": len(handoffs) if handoffs else 0,
            },
        }

        if instructions:
            span_data["metadata"]["instructions_preview"] = instructions[:500]

        self.span_map[agent_id] = span_data
        self._current_span_id = agent_id

        logger.debug(f"Started agent trace: {agent_name}")

        # Create span via aigie
        if self._aigie and self._aigie._initialized:
            try:
                from ...buffer import EventType
                self._aigie._buffer.add_event(
                    EventType.CREATE_SPAN,
                    trace_id=self.trace_id,
                    span_id=agent_id,
                    parent_span_id=span_data.get("parent_span_id"),
                    name=span_data["name"],
                    span_type="agent",
                    metadata=span_data["metadata"],
                )
            except Exception as e:
                logger.debug(f"Error creating agent span: {e}")

        return agent_id

    async def handle_agent_end(
        self,
        agent_id: str,
        output: Optional[Any] = None,
        error: Optional[str] = None,
    ) -> None:
        """Handle agent end event."""
        if agent_id not in self.span_map:
            return

        span_data = self.span_map[agent_id]
        span_data["end_time"] = time.time()
        span_data["duration"] = span_data["end_time"] - span_data["start_time"]

        if output:
            span_data["output"] = self._safe_str(output)
        if error:
            span_data["error"] = error
            span_data["status"] = "error"
        else:
            span_data["status"] = "success"

        # Restore parent span as current
        self._current_span_id = span_data.get("parent_span_id")

        logger.debug(f"Ended agent trace: {span_data['name']}")

        # Update span via aigie
        if self._aigie and self._aigie._initialized:
            try:
                from ...buffer import EventType
                self._aigie._buffer.add_event(
                    EventType.UPDATE_SPAN,
                    span_id=agent_id,
                    output=span_data.get("output"),
                    metadata=span_data["metadata"],
                    status=span_data.get("status", "success"),
                )
            except Exception as e:
                logger.debug(f"Error updating agent span: {e}")

    async def handle_generation_start(
        self,
        model: str,
        messages: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """Handle LLM generation start event.

        Args:
            model: Model name
            messages: Input messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            parent_span_id: Parent span ID

        Returns:
            Generation span ID
        """
        gen_id = str(uuid.uuid4())
        self.generation_count += 1

        span_data = {
            "name": f"llm:{model}",
            "type": "llm",
            "start_time": time.time(),
            "parent_span_id": parent_span_id or self._current_span_id,
            "metadata": {
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "message_count": len(messages) if messages else 0,
            },
        }

        if messages:
            span_data["input"] = self._format_messages(messages)

        self.span_map[gen_id] = span_data

        logger.debug(f"Started generation trace: {model}")

        # Create span via aigie
        if self._aigie and self._aigie._initialized:
            try:
                from ...buffer import EventType
                self._aigie._buffer.add_event(
                    EventType.CREATE_SPAN,
                    trace_id=self.trace_id,
                    span_id=gen_id,
                    parent_span_id=span_data.get("parent_span_id"),
                    name=span_data["name"],
                    span_type="llm",
                    input=span_data.get("input"),
                    metadata=span_data["metadata"],
                )
            except Exception as e:
                logger.debug(f"Error creating generation span: {e}")

        return gen_id

    async def handle_generation_end(
        self,
        gen_id: str,
        response: Optional[str] = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost: float = 0.0,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        error: Optional[str] = None,
    ) -> None:
        """Handle LLM generation end event."""
        if gen_id not in self.span_map:
            return

        span_data = self.span_map[gen_id]
        span_data["end_time"] = time.time()
        span_data["duration"] = span_data["end_time"] - span_data["start_time"]

        # Update tokens
        self.total_tokens += input_tokens + output_tokens
        self.total_cost += cost

        span_data["metadata"].update({
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost": cost,
            "tool_calls_count": len(tool_calls) if tool_calls else 0,
        })

        if response:
            span_data["output"] = self._safe_str(response)
        if error:
            span_data["error"] = error
            span_data["status"] = "error"
        else:
            span_data["status"] = "success"

        logger.debug(f"Ended generation trace: {span_data['name']}")

        # Update span via aigie
        if self._aigie and self._aigie._initialized:
            try:
                from ...buffer import EventType
                self._aigie._buffer.add_event(
                    EventType.UPDATE_SPAN,
                    span_id=gen_id,
                    output=span_data.get("output"),
                    metadata=span_data["metadata"],
                    status=span_data.get("status", "success"),
                    usage={
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": input_tokens + output_tokens,
                        "cost": cost,
                    },
                )
            except Exception as e:
                logger.debug(f"Error updating generation span: {e}")

    async def handle_tool_start(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """Handle tool call start event.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            parent_span_id: Parent span ID

        Returns:
            Tool span ID
        """
        tool_id = str(uuid.uuid4())
        self.tool_call_count += 1

        span_data = {
            "name": f"tool:{tool_name}",
            "type": "tool",
            "start_time": time.time(),
            "parent_span_id": parent_span_id or self._current_span_id,
            "metadata": {
                "tool_name": tool_name,
            },
        }

        if arguments:
            span_data["input"] = self._safe_str(arguments)
            span_data["metadata"]["arg_count"] = len(arguments)

        self.span_map[tool_id] = span_data

        logger.debug(f"Started tool trace: {tool_name}")

        # Create span via aigie
        if self._aigie and self._aigie._initialized:
            try:
                from ...buffer import EventType
                self._aigie._buffer.add_event(
                    EventType.CREATE_SPAN,
                    trace_id=self.trace_id,
                    span_id=tool_id,
                    parent_span_id=span_data.get("parent_span_id"),
                    name=span_data["name"],
                    span_type="tool",
                    input=span_data.get("input"),
                    metadata=span_data["metadata"],
                )
            except Exception as e:
                logger.debug(f"Error creating tool span: {e}")

        return tool_id

    async def handle_tool_end(
        self,
        tool_id: str,
        result: Optional[Any] = None,
        error: Optional[str] = None,
    ) -> None:
        """Handle tool call end event."""
        if tool_id not in self.span_map:
            return

        span_data = self.span_map[tool_id]
        span_data["end_time"] = time.time()
        span_data["duration"] = span_data["end_time"] - span_data["start_time"]

        if result is not None:
            span_data["output"] = self._safe_str(result)
        if error:
            span_data["error"] = error
            span_data["status"] = "error"
        else:
            span_data["status"] = "success"

        logger.debug(f"Ended tool trace: {span_data['name']}")

        # Update span via aigie
        if self._aigie and self._aigie._initialized:
            try:
                from ...buffer import EventType
                self._aigie._buffer.add_event(
                    EventType.UPDATE_SPAN,
                    span_id=tool_id,
                    output=span_data.get("output"),
                    metadata=span_data["metadata"],
                    status=span_data.get("status", "success"),
                )
            except Exception as e:
                logger.debug(f"Error updating tool span: {e}")

    async def handle_handoff_start(
        self,
        source_agent: str,
        target_agent: str,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """Handle agent handoff start event.

        Args:
            source_agent: Agent initiating handoff
            target_agent: Agent receiving handoff
            reason: Reason for handoff
            context: Context being passed
            parent_span_id: Parent span ID

        Returns:
            Handoff span ID
        """
        handoff_id = str(uuid.uuid4())
        self.handoff_count += 1

        span_data = {
            "name": f"handoff:{source_agent}->{target_agent}",
            "type": "chain",
            "start_time": time.time(),
            "parent_span_id": parent_span_id or self._current_span_id,
            "metadata": {
                "source_agent": source_agent,
                "target_agent": target_agent,
                "reason": reason,
                "handoff_depth": self.handoff_count,
            },
        }

        if context:
            span_data["input"] = self._safe_str(context)

        self.span_map[handoff_id] = span_data

        logger.debug(f"Started handoff trace: {source_agent} -> {target_agent}")

        # Create span via aigie
        if self._aigie and self._aigie._initialized:
            try:
                from ...buffer import EventType
                self._aigie._buffer.add_event(
                    EventType.CREATE_SPAN,
                    trace_id=self.trace_id,
                    span_id=handoff_id,
                    parent_span_id=span_data.get("parent_span_id"),
                    name=span_data["name"],
                    span_type="chain",
                    metadata=span_data["metadata"],
                )
            except Exception as e:
                logger.debug(f"Error creating handoff span: {e}")

        return handoff_id

    async def handle_handoff_end(
        self,
        handoff_id: str,
        success: bool = True,
        error: Optional[str] = None,
    ) -> None:
        """Handle agent handoff end event."""
        if handoff_id not in self.span_map:
            return

        span_data = self.span_map[handoff_id]
        span_data["end_time"] = time.time()
        span_data["duration"] = span_data["end_time"] - span_data["start_time"]

        if error:
            span_data["error"] = error
            span_data["status"] = "error"
        else:
            span_data["status"] = "success" if success else "error"

        logger.debug(f"Ended handoff trace: {span_data['name']}")

        # Update span via aigie
        if self._aigie and self._aigie._initialized:
            try:
                from ...buffer import EventType
                self._aigie._buffer.add_event(
                    EventType.UPDATE_SPAN,
                    span_id=handoff_id,
                    metadata=span_data["metadata"],
                    status=span_data.get("status", "success"),
                )
            except Exception as e:
                logger.debug(f"Error updating handoff span: {e}")

    async def handle_guardrail_start(
        self,
        guardrail_name: str,
        guardrail_type: str = "validation",
        input_data: Optional[Any] = None,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """Handle guardrail check start event.

        Args:
            guardrail_name: Name of the guardrail
            guardrail_type: Type (input/output/validation)
            input_data: Data being validated
            parent_span_id: Parent span ID

        Returns:
            Guardrail span ID
        """
        guardrail_id = str(uuid.uuid4())

        span_data = {
            "name": f"guardrail:{guardrail_name}",
            "type": "tool",
            "start_time": time.time(),
            "parent_span_id": parent_span_id or self._current_span_id,
            "metadata": {
                "guardrail_name": guardrail_name,
                "guardrail_type": guardrail_type,
            },
        }

        if input_data:
            span_data["input"] = self._safe_str(input_data)

        self.span_map[guardrail_id] = span_data

        logger.debug(f"Started guardrail trace: {guardrail_name}")

        # Create span via aigie
        if self._aigie and self._aigie._initialized:
            try:
                from ...buffer import EventType
                self._aigie._buffer.add_event(
                    EventType.CREATE_SPAN,
                    trace_id=self.trace_id,
                    span_id=guardrail_id,
                    parent_span_id=span_data.get("parent_span_id"),
                    name=span_data["name"],
                    span_type="tool",
                    metadata=span_data["metadata"],
                )
            except Exception as e:
                logger.debug(f"Error creating guardrail span: {e}")

        return guardrail_id

    async def handle_guardrail_end(
        self,
        guardrail_id: str,
        passed: bool = True,
        result: Optional[Any] = None,
        error: Optional[str] = None,
    ) -> None:
        """Handle guardrail check end event."""
        if guardrail_id not in self.span_map:
            return

        span_data = self.span_map[guardrail_id]
        span_data["end_time"] = time.time()
        span_data["duration"] = span_data["end_time"] - span_data["start_time"]

        span_data["metadata"]["passed"] = passed

        if result is not None:
            span_data["output"] = self._safe_str(result)
        if error:
            span_data["error"] = error
            span_data["status"] = "error"
        else:
            span_data["status"] = "success" if passed else "error"

        logger.debug(f"Ended guardrail trace: {span_data['name']} (passed={passed})")

        # Update span via aigie
        if self._aigie and self._aigie._initialized:
            try:
                from ...buffer import EventType
                self._aigie._buffer.add_event(
                    EventType.UPDATE_SPAN,
                    span_id=guardrail_id,
                    output=span_data.get("output"),
                    metadata=span_data["metadata"],
                    status=span_data.get("status", "success"),
                )
            except Exception as e:
                logger.debug(f"Error updating guardrail span: {e}")

    def _safe_str(self, value: Any, max_length: int = 2000) -> str:
        """Safely convert value to string with length limit."""
        try:
            if value is None:
                return ""
            s = str(value)
            if len(s) > max_length:
                return s[:max_length] + "..."
            return s
        except Exception:
            return "<error converting to string>"

    def _format_messages(self, messages: List[Dict[str, Any]]) -> str:
        """Format messages for tracing."""
        try:
            formatted = []
            for msg in messages[-5:]:  # Last 5 messages
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                if isinstance(content, str):
                    preview = content[:200] + "..." if len(content) > 200 else content
                else:
                    preview = str(content)[:200]
                formatted.append(f"{role}: {preview}")
            return "\n".join(formatted)
        except Exception:
            return str(messages)[:1000]

    def get_statistics(self) -> Dict[str, Any]:
        """Get current tracing statistics."""
        return {
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "generation_count": self.generation_count,
            "tool_call_count": self.tool_call_count,
            "handoff_count": self.handoff_count,
            "agent_count": self.agent_count,
            "span_count": len(self.span_map),
        }
