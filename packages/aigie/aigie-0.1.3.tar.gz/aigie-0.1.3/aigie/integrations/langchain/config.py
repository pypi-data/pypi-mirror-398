"""
Configuration for LangChain tracing.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class LangChainConfig:
    """Configuration for LangChain tracing behavior.

    Attributes:
        trace_chains: Whether to trace chain executions
        trace_agents: Whether to trace agent executions
        trace_llm_calls: Whether to trace LLM calls
        trace_tool_calls: Whether to trace tool invocations
        trace_retrievers: Whether to trace retriever operations
        capture_inputs: Whether to capture input data
        capture_outputs: Whether to capture output data
        capture_prompts: Whether to capture LLM prompts
        max_content_length: Maximum content length to capture
        mask_sensitive_data: Whether to mask potentially sensitive data
        chain_timeout: Timeout in seconds for chain operations
        llm_timeout: Timeout in seconds for LLM calls
        tool_timeout: Timeout in seconds for tool executions
        max_retries: Maximum number of retries for failed operations
        retry_delay: Initial delay between retries in seconds (exponential backoff)
        retry_on_errors: List of error types to retry on (empty = retry all transient)
    """

    # Tracing toggles
    trace_chains: bool = True
    trace_agents: bool = True
    trace_llm_calls: bool = True
    trace_tool_calls: bool = True
    trace_retrievers: bool = True

    # Data capture settings
    capture_inputs: bool = True
    capture_outputs: bool = True
    capture_prompts: bool = True
    max_content_length: int = 2000

    # Privacy
    mask_sensitive_data: bool = False

    # Span naming
    span_prefix: str = "langchain"

    # Timeout settings (in seconds)
    chain_timeout: float = 300.0  # 5 minutes for chains
    llm_timeout: float = 120.0  # 2 minutes for LLM calls
    tool_timeout: float = 60.0  # 1 minute for tools

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
        if self.chain_timeout <= 0:
            raise ValueError("chain_timeout must be positive")
        if self.llm_timeout <= 0:
            raise ValueError("llm_timeout must be positive")
        if self.tool_timeout <= 0:
            raise ValueError("tool_timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.retry_delay < 0:
            raise ValueError("retry_delay must be non-negative")
