"""
Configuration for CrewAI tracing.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CrewAIConfig:
    """Configuration for CrewAI tracing behavior.

    Attributes:
        trace_crews: Whether to trace crew executions
        trace_agents: Whether to trace individual agent executions
        trace_tasks: Whether to trace task executions
        trace_llm_calls: Whether to trace LLM calls within agents
        trace_tool_calls: Whether to trace tool invocations
        trace_delegations: Whether to trace agent delegations
        capture_inputs: Whether to capture input data
        capture_outputs: Whether to capture output data
        capture_agent_thoughts: Whether to capture agent reasoning
        capture_tool_results: Whether to capture tool results
        max_content_length: Maximum content length to capture
        mask_sensitive_data: Whether to mask potentially sensitive data
        crew_timeout: Timeout in seconds for entire crew execution
        task_timeout: Timeout in seconds for individual tasks
        llm_timeout: Timeout in seconds for LLM calls
        max_retries: Maximum number of retries for failed operations
        retry_delay: Initial delay between retries in seconds (exponential backoff)
        retry_on_errors: List of error types to retry on (empty = retry all transient)
    """

    # Tracing toggles
    trace_crews: bool = True
    trace_agents: bool = True
    trace_tasks: bool = True
    trace_llm_calls: bool = True
    trace_tool_calls: bool = True
    trace_delegations: bool = True

    # Data capture settings
    capture_inputs: bool = True
    capture_outputs: bool = True
    capture_agent_thoughts: bool = True
    capture_tool_results: bool = True
    max_content_length: int = 2000

    # Privacy
    mask_sensitive_data: bool = False

    # Span naming
    span_prefix: str = "crewai"

    # Timeout settings (in seconds)
    crew_timeout: float = 1800.0  # 30 minutes for full crew
    task_timeout: float = 600.0  # 10 minutes per task
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
        if self.crew_timeout <= 0:
            raise ValueError("crew_timeout must be positive")
        if self.task_timeout <= 0:
            raise ValueError("task_timeout must be positive")
        if self.llm_timeout <= 0:
            raise ValueError("llm_timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.retry_delay < 0:
            raise ValueError("retry_delay must be non-negative")
