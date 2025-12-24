"""
LangGraph callback handler for Aigie SDK.

This module provides the LangGraphHandler which implements LangChain's
BaseCallbackHandler protocol for automatic trace/span creation in
LangGraph workflows.

For full implementation, see aigie/langgraph.py which contains the main
LangGraphHandler class. This module re-exports it for convenience.
"""

# Re-export the main handler
from ...langgraph import (
    LangGraphHandler,
    wrap_langgraph,
    trace_langgraph_node,
    trace_langgraph_edge,
    create_langgraph_handler,
)

# Export for convenience
__all__ = [
    "LangGraphHandler",
    "wrap_langgraph",
    "trace_langgraph_node",
    "trace_langgraph_edge",
    "create_langgraph_handler",
]
