"""
LangGraph integration for Aigie SDK

Provides automatic tracing for LangGraph applications with Python
"""

from typing import Any, Callable, Dict, List, Optional, TypeVar
from functools import wraps
import uuid
from datetime import datetime

from .context_manager import get_current_trace_context
from .buffer import EventType

# Try to import BaseCallbackHandler for compatibility
try:
    from langchain_core.callbacks import BaseCallbackHandler
    HAS_BASE_CALLBACK = True
except ImportError:
    HAS_BASE_CALLBACK = False
    BaseCallbackHandler = object  # Fallback

T = TypeVar('T', bound=Callable[..., Any])


class LangGraphHandler(BaseCallbackHandler if HAS_BASE_CALLBACK else object):
    """
    LangGraph callback handler for Aigie

    Automatically traces LangGraph workflow executions

    Example:
        >>> from langgraph.graph import StateGraph
        >>> from aigie.langgraph import LangGraphHandler
        >>>
        >>> handler = LangGraphHandler(
        ...     trace_name='my-graph',
        ...     metadata={'version': '1.0'}
        ... )
        >>>
        >>> graph = StateGraph(...)
        >>> app = graph.compile()
        >>>
        >>> result = await app.ainvoke(input, config={
        ...     'callbacks': [handler]
        ... })
    """

    def __init__(
        self,
        trace_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ):
        """
        Initialize LangGraph handler

        Args:
            trace_name: Name for the trace
            metadata: Additional metadata to attach
            tags: Tags to apply to trace and spans
        """
        # Initialize BaseCallbackHandler if available
        if HAS_BASE_CALLBACK:
            super().__init__()
        
        self.trace_name = trace_name
        self.metadata = metadata or {}
        self.tags = tags or []
        self.node_map: Dict[str, Dict[str, Any]] = {}  # node_name -> {spanId, startTime, parentId}
        self.tool_map: Dict[str, Dict[str, Any]] = {}  # run_id -> {spanId, startTime, parentSpanId}
        self.trace_id: Optional[str] = None
        self._aigie = None
        self._trace_context: Optional[Any] = None  # Store trace context if provided
        self._current_node_span_id: Optional[str] = None  # Track current node for parent relationships
        
        # Required properties for BaseCallbackHandler compatibility
        self.run_inline = False  # Don't run callbacks inline
        self.raise_error = False  # Don't raise errors in callbacks

    def _get_aigie(self):
        """Lazy load Aigie client"""
        if self._aigie is None:
            from .client import get_aigie
            self._aigie = get_aigie()
        return self._aigie

    async def handle_graph_start(self, graph_name: str, input: Any) -> None:
        """
        Called when graph execution starts

        Args:
            graph_name: Name of the graph
            input: Input to the graph
        """
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        # Use existing trace_id if set (from shared trace context)
        if not self.trace_id:
            if self._trace_context and hasattr(self._trace_context, 'id'):
                self.trace_id = str(self._trace_context.id)
            else:
                self.trace_id = str(uuid.uuid4())

        # Only create trace if we don't have a trace context
        # (trace context means trace was already created by AigieCallbackHandler)
        if not self._trace_context:
            trace_data = {
                'id': self.trace_id,
                'name': self.trace_name or graph_name,
                'type': 'chain',
                'input': input,
                'status': 'pending',
                'tags': [*self.tags, 'langgraph'],
                'metadata': {
                    **self.metadata,
                    'graphName': graph_name,
                    'framework': 'langgraph',
                },
                'start_time': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat(),
            }

        # Send trace via buffer
        if aigie._buffer:
            await aigie._buffer.add(
                EventType.TRACE_CREATE,
                trace_data
            )
        else:
            # Fallback: try direct API call (with error handling)
            try:
                if aigie.client:
                    await aigie.client.post(
                        f"{aigie.api_url}/v1/traces",
                        json=trace_data,
                        headers={"X-API-Key": aigie.api_key},
                        timeout=5.0
                    )
            except Exception:
                pass  # Silently fail if backend is not available

    async def handle_node_start(self, node_name: str, input: Any) -> None:
        """
        Called when a node starts executing

        Args:
            node_name: Name of the node
            input: Input to the node
        """
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized or not self.trace_id:
            return

        span_id = str(uuid.uuid4())
        start_time = datetime.now()

        self.node_map[node_name] = {
            'spanId': span_id,
            'startTime': start_time,
        }

        # Determine parent_id (previous node or None for first node)
        parent_id = None
        if self._current_node_span_id:
            parent_id = self._current_node_span_id

        span_data = {
            'id': span_id,
            'trace_id': self.trace_id,
            'parent_id': parent_id,  # Set parent to previous node
            'name': f'node:{node_name}',
            'type': 'chain',
            'input': input,
            'status': 'pending',
            'tags': self.tags or [],
            'metadata': {
                **self.metadata,
                'nodeName': node_name,
                'nodeType': 'langgraph_node',
            },
            'start_time': start_time.isoformat(),
            'created_at': start_time.isoformat(),
        }
        
        # Update current node for next node's parent
        self._current_node_span_id = span_id

        # Send span via buffer
        if aigie._buffer:
            await aigie._buffer.add(
                EventType.SPAN_CREATE,
                span_data
            )
        else:
            # Fallback: try direct API call (with error handling)
            try:
                if aigie.client:
                    await aigie.client.post(
                        f"{aigie.api_url}/v1/spans",
                        json=span_data,
                        headers={"X-API-Key": aigie.api_key},
                        timeout=5.0
                    )
            except Exception:
                pass  # Silently fail if backend is not available

    async def handle_node_end(self, node_name: str, output: Any) -> None:
        """
        Called when a node finishes executing

        Args:
            node_name: Name of the node
            output: Output from the node
        """
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        node_data = self.node_map.get(node_name)
        if not node_data:
            return

        end_time = datetime.now()
        duration = (end_time - node_data['startTime']).total_seconds()

        # Update span via buffer
        update_data = {
            'id': node_data['spanId'],
            'output': output,
            'status': 'success',
            'end_time': end_time.isoformat(),
            'duration_ns': int(duration * 1_000_000_000),
        }
        
        if aigie._buffer:
            await aigie._buffer.add(
                EventType.SPAN_UPDATE,
                update_data
            )
        else:
            # Fallback: try direct API call (with error handling)
            try:
                if aigie.client:
                    span_id = update_data.pop('id')
                    await aigie.client.put(
                        f"{aigie.api_url}/v1/spans/{span_id}",
                        json=update_data,
                        headers={"X-API-Key": aigie.api_key},
                        timeout=5.0
                    )
            except Exception:
                pass  # Silently fail if backend is not available

        del self.node_map[node_name]

    async def handle_node_error(self, node_name: str, error: Exception) -> None:
        """
        Called when a node encounters an error

        Args:
            node_name: Name of the node
            error: The error that occurred
        """
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        node_data = self.node_map.get(node_name)
        if not node_data:
            return

        end_time = datetime.now()
        duration = (end_time - node_data['startTime']).total_seconds()

        # Update span via buffer
        update_data = {
            'id': node_data['spanId'],
            'status': 'failed',
            'error': str(error),
            'error_message': str(error),
            'end_time': end_time.isoformat(),
            'duration_ns': int(duration * 1_000_000_000),
        }
        
        if aigie._buffer:
            await aigie._buffer.add(
                EventType.SPAN_UPDATE,
                update_data
            )
        else:
            # Fallback: try direct API call (with error handling)
            try:
                if aigie.client:
                    span_id = update_data.pop('id')
                    await aigie.client.put(
                        f"{aigie.api_url}/v1/spans/{span_id}",
                        json=update_data,
                        headers={"X-API-Key": aigie.api_key},
                        timeout=5.0
                    )
            except Exception:
                pass  # Silently fail if backend is not available

        del self.node_map[node_name]
        # Update current node for next node's parent (if this was the current node)
        if self._current_node_span_id == node_data.get('spanId'):
            # Find previous node as parent
            previous_node = None
            for node_name_key, node_data_item in self.node_map.items():
                if node_data_item.get('spanId') != self._current_node_span_id:
                    previous_node = node_data_item.get('spanId')
            self._current_node_span_id = previous_node

    async def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: str,
        parent_run_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool starts (from BaseCallbackHandler)."""
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized or not self.trace_id:
            return
        
        # Extract tool name
        tool_name = serialized.get("name", "Tool") if serialized else "Tool"
        
        # Determine parent span ID (current node or LLM span)
        parent_span_id = self._current_node_span_id
        
        span_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        self.tool_map[run_id] = {
            'spanId': span_id,
            'startTime': start_time,
            'parentSpanId': parent_span_id,
        }
        
        span_data = {
            'id': span_id,
            'trace_id': self.trace_id,
            'parent_id': parent_span_id,  # Set parent to current node
            'name': f'Tool: {tool_name}',
            'type': 'tool',
            'input': input_str,
            'tags': (self.tags or []) + (tags or []),
            'metadata': {
                **self.metadata,
                **(metadata or {}),
                'tool_name': tool_name,
                'tool_serialized': serialized,
            },
            'start_time': start_time.isoformat(),
            'created_at': start_time.isoformat(),
        }
        
        # Send span via buffer
        if aigie._buffer:
            await aigie._buffer.add(
                EventType.SPAN_CREATE,
                span_data
            )
        else:
            try:
                if aigie.client:
                    await aigie.client.post(
                        f"{aigie.api_url}/v1/spans",
                        json=span_data,
                        headers={"X-API-Key": aigie.api_key},
                        timeout=5.0
                    )
            except Exception:
                pass  # Silently fail if backend is not available
    
    async def on_tool_end(
        self,
        output: str,
        *,
        run_id: str,
        **kwargs: Any,
    ) -> None:
        """Called when a tool ends (from BaseCallbackHandler)."""
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return
        
        tool_data = self.tool_map.get(run_id)
        if not tool_data:
            return
        
        end_time = datetime.now()
        duration = (end_time - tool_data['startTime']).total_seconds()
        
        update_data = {
            'id': tool_data['spanId'],
            'output': output,
            'status': 'success',
            'end_time': end_time.isoformat(),
            'duration_ns': int(duration * 1_000_000_000),
        }
        
        if aigie._buffer:
            await aigie._buffer.add(
                EventType.SPAN_UPDATE,
                update_data
            )
        else:
            try:
                if aigie.client:
                    span_id = update_data.pop('id')
                    await aigie.client.put(
                        f"{aigie.api_url}/v1/spans/{span_id}",
                        json=update_data,
                        headers={"X-API-Key": aigie.api_key},
                        timeout=5.0
                    )
            except Exception:
                pass  # Silently fail if backend is not available
        
        del self.tool_map[run_id]
    
    async def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: str,
        parent_run_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when an LLM starts (from BaseCallbackHandler)."""
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized or not self.trace_id:
            return
        
        # Extract model name
        model_name = serialized.get("model_name") or serialized.get("model") or "LLM"
        
        span_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        # Store LLM span info (we'll track it for tool parent relationships)
        if not hasattr(self, '_llm_map'):
            self._llm_map = {}
        self._llm_map[run_id] = {
            'spanId': span_id,
            'startTime': start_time,
            'parentSpanId': self._current_node_span_id,  # Parent is current node
        }
        
        span_data = {
            'id': span_id,
            'trace_id': self.trace_id,
            'parent_id': self._current_node_span_id,  # Set parent to current node
            'name': f'LLM: {model_name}',
            'type': 'llm',
            'input': prompts[0] if prompts else None,
            'tags': (self.tags or []) + (tags or []),
            'metadata': {
                **self.metadata,
                **(metadata or {}),
                'model_name': model_name,
                'llm_serialized': serialized,
            },
            'start_time': start_time.isoformat(),
            'created_at': start_time.isoformat(),
        }
        
        # Send span via buffer
        if aigie._buffer:
            await aigie._buffer.add(
                EventType.SPAN_CREATE,
                span_data
            )
        else:
            try:
                if aigie.client:
                    await aigie.client.post(
                        f"{aigie.api_url}/v1/spans",
                        json=span_data,
                        headers={"X-API-Key": aigie.api_key},
                        timeout=5.0
                    )
            except Exception:
                pass  # Silently fail if backend is not available
    
    async def on_llm_end(
        self,
        response: Any,
        *,
        run_id: str,
        **kwargs: Any,
    ) -> None:
        """Called when an LLM ends (from BaseCallbackHandler)."""
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return
        
        if not hasattr(self, '_llm_map'):
            return
        
        llm_data = self._llm_map.get(run_id)
        if not llm_data:
            return
        
        end_time = datetime.now()
        duration = (end_time - llm_data['startTime']).total_seconds()
        
        # Extract output
        output = None
        if hasattr(response, 'generations') and response.generations:
            if response.generations[0] and response.generations[0][0]:
                output = response.generations[0][0].text
        elif hasattr(response, 'content'):
            output = response.content
        else:
            output = str(response)
        
        update_data = {
            'id': llm_data['spanId'],
            'output': output,
            'status': 'success',
            'end_time': end_time.isoformat(),
            'duration_ns': int(duration * 1_000_000_000),
        }
        
        if aigie._buffer:
            await aigie._buffer.add(
                EventType.SPAN_UPDATE,
                update_data
            )
        else:
            try:
                if aigie.client:
                    span_id = update_data.pop('id')
                    await aigie.client.put(
                        f"{aigie.api_url}/v1/spans/{span_id}",
                        json=update_data,
                        headers={"X-API-Key": aigie.api_key},
                        timeout=5.0
                    )
            except Exception:
                pass  # Silently fail if backend is not available
        
        del self._llm_map[run_id]

    async def handle_graph_end(self, output: Any) -> None:
        """
        Called when graph execution finishes

        Args:
            output: Output from the graph
        """
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized or not self.trace_id:
            return

        end_time = datetime.now()

        # Update trace via buffer
        update_data = {
            'id': self.trace_id,
            'output': output,
            'status': 'success',
            'end_time': end_time.isoformat(),
        }
        
        if aigie._buffer:
            await aigie._buffer.add(
                EventType.TRACE_UPDATE,
                update_data
            )
        else:
            # Fallback: try direct API call (with error handling)
            try:
                if aigie.client:
                    trace_id = update_data.pop('id')
                    await aigie.client.put(
                        f"{aigie.api_url}/v1/traces/{trace_id}",
                        json=update_data,
                        headers={"X-API-Key": aigie.api_key},
                        timeout=5.0
                    )
            except Exception:
                pass  # Silently fail if backend is not available

    async def handle_graph_error(self, error: Exception) -> None:
        """
        Called when graph execution encounters an error

        Args:
            error: The error that occurred
        """
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized or not self.trace_id:
            return

        end_time = datetime.now()

        # Update trace via buffer
        update_data = {
            'id': self.trace_id,
            'status': 'failed',
            'error': str(error),
            'error_message': str(error),
            'end_time': end_time.isoformat(),
        }
        
        if aigie._buffer:
            await aigie._buffer.add(
                EventType.TRACE_UPDATE,
                update_data
            )
        else:
            # Fallback: try direct API call (with error handling)
            try:
                if aigie.client:
                    trace_id = update_data.pop('id')
                    await aigie.client.put(
                        f"{aigie.api_url}/v1/traces/{trace_id}",
                        json=update_data,
                        headers={"X-API-Key": aigie.api_key},
                        timeout=5.0
                    )
            except Exception:
                pass  # Silently fail if backend is not available

    async def flush(self) -> None:
        """Clean up resources"""
        self.node_map.clear()
        self.trace_id = None


def wrap_langgraph(
    app: Any,
    trace_name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
) -> Any:
    """
    Wrap LangGraph application for automatic tracing

    Example:
        >>> from langgraph.graph import StateGraph
        >>> from aigie.langgraph import wrap_langgraph
        >>>
        >>> graph = StateGraph(...)
        >>> app = graph.compile()
        >>>
        >>> traced_app = wrap_langgraph(app, trace_name='my-graph')
        >>> result = await traced_app.ainvoke(input)

    Args:
        app: LangGraph compiled application
        trace_name: Name for the trace
        metadata: Additional metadata
        tags: Tags to apply

    Returns:
        Wrapped application with automatic tracing
    """
    from .client import get_aigie

    aigie = get_aigie()

    if not aigie or not aigie._initialized:
        return app

    # Store original invoke method
    original_ainvoke = getattr(app, 'ainvoke', None)
    if original_ainvoke:
        async def traced_ainvoke(input: Any, config: Optional[Dict[str, Any]] = None):
            """Traced version of ainvoke"""
            return await aigie.trace(
                trace_name or 'langgraph',
                lambda: original_ainvoke(input, config),
                type='chain',
                input=input,
                tags=[*(tags or []), 'langgraph'],
                metadata={
                    **(metadata or {}),
                    'framework': 'langgraph',
                },
            )

        app.ainvoke = traced_ainvoke

    # Store original invoke method (sync)
    original_invoke = getattr(app, 'invoke', None)
    if original_invoke:
        def traced_invoke(input: Any, config: Optional[Dict[str, Any]] = None):
            """Traced version of invoke"""
            # For sync invoke, we just call it directly
            # Tracing requires async context
            return original_invoke(input, config)

        app.invoke = traced_invoke

    # Store original stream method
    original_astream = getattr(app, 'astream', None)
    if original_astream:
        async def traced_astream(input: Any, config: Optional[Dict[str, Any]] = None):
            """Traced version of astream"""
            async for chunk in original_astream(input, config):
                yield chunk

        app.astream = traced_astream

    return app


def trace_langgraph_node(
    node_name: str,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
) -> Callable[[T], T]:
    """
    Decorator to trace a LangGraph node function

    Example:
        >>> from aigie.langgraph import trace_langgraph_node
        >>>
        >>> @trace_langgraph_node('my-node')
        >>> async def my_node(state):
        ...     # Node logic
        ...     return {'result': 'done'}

    Args:
        node_name: Name of the node
        metadata: Additional metadata
        tags: Tags to apply

    Returns:
        Decorator function
    """
    from .client import get_aigie

    def decorator(fn: T) -> T:
        @wraps(fn)
        async def async_wrapper(*args, **kwargs):
            aigie = get_aigie()

            if not aigie or not aigie._initialized:
                return await fn(*args, **kwargs)

            return await aigie.span(
                f'node:{node_name}',
                lambda: fn(*args, **kwargs),
                type='chain',
                input=args[0] if args else None,  # First arg is typically the state
                tags=[*(tags or []), 'langgraph', 'node'],
                metadata={
                    **(metadata or {}),
                    'nodeName': node_name,
                    'nodeType': 'langgraph_node',
                },
            )

        @wraps(fn)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, just call directly
            return fn(*args, **kwargs)

        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(fn):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


def trace_langgraph_edge(
    edge_name: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Callable[[T], T]:
    """
    Decorator to trace a LangGraph edge condition

    Example:
        >>> from aigie.langgraph import trace_langgraph_edge
        >>>
        >>> @trace_langgraph_edge('my-condition')
        >>> def should_continue(state):
        ...     return 'next_node' if state['count'] < 10 else 'end'

    Args:
        edge_name: Name of the edge
        metadata: Additional metadata

    Returns:
        Decorator function
    """
    from .client import get_aigie

    def decorator(fn: T) -> T:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            aigie = get_aigie()

            if not aigie or not aigie._initialized:
                return fn(*args, **kwargs)

            # For edge conditions, we execute and log the decision
            result = fn(*args, **kwargs)

            # Log edge decision as metadata
            context = get_current_trace_context()
            if context and context.get('spanId'):
                # Update current span with edge information
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Can't await in sync context, skip update
                        pass
                    else:
                        loop.run_until_complete(
                            aigie._update_span(context['spanId'], {
                                'metadata': {
                                    'edgeName': edge_name,
                                    'edgeResult': result,
                                    **(metadata or {}),
                                },
                            })
                        )
                except RuntimeError:
                    # No event loop, skip update
                    pass

            return result

        return wrapper  # type: ignore

    return decorator


def create_langgraph_handler(
    trace_name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
) -> LangGraphHandler:
    """
    Create LangGraph handler

    Args:
        trace_name: Name for the trace
        metadata: Additional metadata
        tags: Tags to apply

    Returns:
        LangGraph handler instance
    """
    return LangGraphHandler(
        trace_name=trace_name,
        metadata=metadata,
        tags=tags,
    )
