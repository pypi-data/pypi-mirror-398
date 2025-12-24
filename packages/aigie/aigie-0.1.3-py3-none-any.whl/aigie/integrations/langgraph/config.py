"""
Configuration for LangGraph tracing.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class LangGraphConfig:
    """Configuration for LangGraph tracing behavior.

    Attributes:
        trace_graphs: Whether to trace graph executions
        trace_nodes: Whether to trace individual node executions
        trace_edges: Whether to trace edge decisions
        trace_llm_calls: Whether to trace LLM calls within nodes
        trace_tool_calls: Whether to trace tool invocations
        capture_inputs: Whether to capture input data
        capture_outputs: Whether to capture output data
        capture_state: Whether to capture state transitions
        max_content_length: Maximum content length to capture
        mask_sensitive_data: Whether to mask potentially sensitive data
        graph_timeout: Timeout in seconds for entire graph execution
        node_timeout: Timeout in seconds for individual nodes
        llm_timeout: Timeout in seconds for LLM calls
        max_retries: Maximum number of retries for failed operations
        retry_delay: Initial delay between retries in seconds (exponential backoff)
        retry_on_errors: List of error types to retry on (empty = retry all transient)
    """

    # Tracing toggles
    trace_graphs: bool = True
    trace_nodes: bool = True
    trace_edges: bool = True
    trace_llm_calls: bool = True
    trace_tool_calls: bool = True

    # Data capture settings
    capture_inputs: bool = True
    capture_outputs: bool = True
    capture_state: bool = True
    max_content_length: int = 2000

    # Privacy
    mask_sensitive_data: bool = False

    # Span naming
    span_prefix: str = "langgraph"

    # Timeout settings (in seconds)
    graph_timeout: float = 600.0  # 10 minutes for full graph
    node_timeout: float = 120.0  # 2 minutes per node
    llm_timeout: float = 120.0  # 2 minutes for LLM calls

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0  # Initial delay, doubles each retry
    retry_on_errors: List[str] = field(default_factory=list)  # Empty = retry all transient

    # Metadata
    default_tags: Dict[str, str] = field(default_factory=dict)
    default_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate configuration."""
        if self.max_content_length < 100:
            raise ValueError("max_content_length must be at least 100")
        if self.graph_timeout <= 0:
            raise ValueError("graph_timeout must be positive")
        if self.node_timeout <= 0:
            raise ValueError("node_timeout must be positive")
        if self.llm_timeout <= 0:
            raise ValueError("llm_timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.retry_delay < 0:
            raise ValueError("retry_delay must be non-negative")
