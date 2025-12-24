"""
Aigie LangGraph Integration

Full workflow tracing for LangGraph stateful graphs with the Aigie SDK.
Traces graph executions, node transitions, state changes, and LLM calls.

Usage (Auto-Instrumentation - Recommended):
    import aigie
    from aigie.integrations.langgraph import patch_langgraph

    # Initialize Aigie
    aigie_client = aigie.Aigie()
    await aigie_client.initialize()

    # Enable auto-instrumentation
    patch_langgraph()

    # Now all LangGraph operations are automatically traced
    from langgraph.graph import StateGraph

    graph = StateGraph(MyState)
    # ... add nodes and edges
    app = graph.compile()
    result = await app.ainvoke({"input": "..."})  # Automatically traced!

Usage (Manual Callback Handler):
    from aigie.integrations.langgraph import LangGraphHandler
    from langgraph.graph import StateGraph

    # Create handler with trace context
    async with aigie.trace("My Workflow") as trace:
        handler = LangGraphHandler(trace_name="My Graph")
        handler._trace_context = trace
        result = await app.ainvoke(
            {"input": "..."},
            config={"callbacks": [handler]}
        )

Usage (Configuration):
    from aigie.integrations.langgraph import LangGraphConfig, patch_langgraph

    # Custom configuration
    config = LangGraphConfig(
        trace_graphs=True,
        trace_nodes=True,
        trace_edges=True,
        graph_timeout=600.0,
        max_retries=5,
    )

    # Apply configuration (config is used by handlers)
    patch_langgraph()

Usage (Decorators):
    from aigie.integrations.langgraph import trace_langgraph_node, trace_langgraph_edge

    @trace_langgraph_node
    async def my_node(state):
        # Node logic
        return {"result": "..."}

    @trace_langgraph_edge
    def my_conditional_edge(state):
        # Route logic
        return "next_node"
"""

__all__ = [
    # Handler
    "LangGraphHandler",
    # Wrapper functions
    "wrap_langgraph",
    "trace_langgraph_node",
    "trace_langgraph_edge",
    "create_langgraph_handler",
    # Configuration
    "LangGraphConfig",
    # Cost tracking
    "LANGGRAPH_MODEL_PRICING",
    "get_langgraph_cost",
    "extract_tokens_from_response",
    "extract_model_from_llm",
    "aggregate_workflow_costs",
    # Auto-instrumentation
    "patch_langgraph",
    "unpatch_langgraph",
    "is_langgraph_patched",
    # Utilities
    "is_langgraph_available",
    "get_langgraph_version",
    "safe_str",
    "extract_node_name",
    "extract_edge_name",
    "extract_graph_structure",
    "extract_state_info",
    "format_state_for_trace",
    "get_execution_path",
    "mask_sensitive_state",
    "calculate_state_diff",
    # Retry/Timeout utilities
    "RetryExhaustedError",
    "TimeoutExceededError",
    "GraphExecutionError",
    "with_timeout",
    "with_retry",
    "with_timeout_and_retry",
    "retry_decorator",
    "RetryContext",
    "GraphRetryContext",
]

from typing import TYPE_CHECKING, Any


def __getattr__(name: str) -> Any:
    """Lazy imports for performance."""

    # Handler
    if name == "LangGraphHandler":
        from .handler import LangGraphHandler
        return LangGraphHandler

    # Wrapper functions
    if name == "wrap_langgraph":
        from .handler import wrap_langgraph
        return wrap_langgraph

    if name == "trace_langgraph_node":
        from .handler import trace_langgraph_node
        return trace_langgraph_node

    if name == "trace_langgraph_edge":
        from .handler import trace_langgraph_edge
        return trace_langgraph_edge

    if name == "create_langgraph_handler":
        from .handler import create_langgraph_handler
        return create_langgraph_handler

    # Configuration
    if name == "LangGraphConfig":
        from .config import LangGraphConfig
        return LangGraphConfig

    # Cost tracking
    if name == "LANGGRAPH_MODEL_PRICING":
        from .cost_tracking import LANGGRAPH_MODEL_PRICING
        return LANGGRAPH_MODEL_PRICING

    if name == "get_langgraph_cost":
        from .cost_tracking import get_langgraph_cost
        return get_langgraph_cost

    if name == "extract_tokens_from_response":
        from .cost_tracking import extract_tokens_from_response
        return extract_tokens_from_response

    if name == "extract_model_from_llm":
        from .cost_tracking import extract_model_from_llm
        return extract_model_from_llm

    if name == "aggregate_workflow_costs":
        from .cost_tracking import aggregate_workflow_costs
        return aggregate_workflow_costs

    # Auto-instrumentation
    if name == "patch_langgraph":
        from .auto_instrument import patch_langgraph
        return patch_langgraph

    if name == "unpatch_langgraph":
        from .auto_instrument import unpatch_langgraph
        return unpatch_langgraph

    if name == "is_langgraph_patched":
        from .auto_instrument import is_langgraph_patched
        return is_langgraph_patched

    # Utilities
    if name == "is_langgraph_available":
        from .utils import is_langgraph_available
        return is_langgraph_available

    if name == "get_langgraph_version":
        from .utils import get_langgraph_version
        return get_langgraph_version

    if name == "safe_str":
        from .utils import safe_str
        return safe_str

    if name == "extract_node_name":
        from .utils import extract_node_name
        return extract_node_name

    if name == "extract_edge_name":
        from .utils import extract_edge_name
        return extract_edge_name

    if name == "extract_graph_structure":
        from .utils import extract_graph_structure
        return extract_graph_structure

    if name == "extract_state_info":
        from .utils import extract_state_info
        return extract_state_info

    if name == "format_state_for_trace":
        from .utils import format_state_for_trace
        return format_state_for_trace

    if name == "get_execution_path":
        from .utils import get_execution_path
        return get_execution_path

    if name == "mask_sensitive_state":
        from .utils import mask_sensitive_state
        return mask_sensitive_state

    if name == "calculate_state_diff":
        from .utils import calculate_state_diff
        return calculate_state_diff

    # Retry/Timeout utilities
    if name == "RetryExhaustedError":
        from .retry import RetryExhaustedError
        return RetryExhaustedError

    if name == "TimeoutExceededError":
        from .retry import TimeoutExceededError
        return TimeoutExceededError

    if name == "GraphExecutionError":
        from .retry import GraphExecutionError
        return GraphExecutionError

    if name == "with_timeout":
        from .retry import with_timeout
        return with_timeout

    if name == "with_retry":
        from .retry import with_retry
        return with_retry

    if name == "with_timeout_and_retry":
        from .retry import with_timeout_and_retry
        return with_timeout_and_retry

    if name == "retry_decorator":
        from .retry import retry_decorator
        return retry_decorator

    if name == "RetryContext":
        from .retry import RetryContext
        return RetryContext

    if name == "GraphRetryContext":
        from .retry import GraphRetryContext
        return GraphRetryContext

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


if TYPE_CHECKING:
    from .handler import (
        LangGraphHandler,
        wrap_langgraph,
        trace_langgraph_node,
        trace_langgraph_edge,
        create_langgraph_handler,
    )
    from .config import LangGraphConfig
    from .cost_tracking import (
        LANGGRAPH_MODEL_PRICING,
        get_langgraph_cost,
        extract_tokens_from_response,
        extract_model_from_llm,
        aggregate_workflow_costs,
    )
    from .auto_instrument import (
        patch_langgraph,
        unpatch_langgraph,
        is_langgraph_patched,
    )
    from .utils import (
        is_langgraph_available,
        get_langgraph_version,
        safe_str,
        extract_node_name,
        extract_edge_name,
        extract_graph_structure,
        extract_state_info,
        format_state_for_trace,
        get_execution_path,
        mask_sensitive_state,
        calculate_state_diff,
    )
    from .retry import (
        RetryExhaustedError,
        TimeoutExceededError,
        GraphExecutionError,
        with_timeout,
        with_retry,
        with_timeout_and_retry,
        retry_decorator,
        RetryContext,
        GraphRetryContext,
    )
