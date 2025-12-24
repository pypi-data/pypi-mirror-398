"""
Configuration for OpenAI Agents SDK integration.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class OpenAIAgentsConfig:
    """Configuration for OpenAI Agents SDK tracing.

    Attributes:
        trace_agents: Enable agent execution tracing
        trace_generations: Enable LLM generation tracing
        trace_tool_calls: Enable tool/function call tracing
        trace_handoffs: Enable agent handoff tracing
        trace_guardrails: Enable guardrail validation tracing
        capture_inputs: Capture input messages
        capture_outputs: Capture output responses
        capture_tool_args: Capture tool call arguments
        capture_tool_results: Capture tool call results
        max_content_length: Maximum content length to capture
        agent_timeout: Timeout for agent execution in seconds
        generation_timeout: Timeout for LLM generation in seconds
        max_retries: Maximum retry attempts for failed operations
        retry_delay: Initial delay between retries in seconds
        sensitive_patterns: Patterns to mask in captured content
    """

    # Tracing toggles
    trace_agents: bool = True
    trace_generations: bool = True
    trace_tool_calls: bool = True
    trace_handoffs: bool = True
    trace_guardrails: bool = True

    # Capture settings
    capture_inputs: bool = True
    capture_outputs: bool = True
    capture_tool_args: bool = True
    capture_tool_results: bool = True
    max_content_length: int = 2000

    # Timeouts
    agent_timeout: float = 300.0  # 5 minutes per agent
    generation_timeout: float = 120.0  # 2 minutes per generation
    workflow_timeout: float = 1800.0  # 30 minutes total

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0

    # Privacy
    sensitive_patterns: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate configuration."""
        if self.max_content_length < 0:
            raise ValueError("max_content_length must be non-negative")
        if self.agent_timeout <= 0:
            raise ValueError("agent_timeout must be positive")
        if self.generation_timeout <= 0:
            raise ValueError("generation_timeout must be positive")
        if self.workflow_timeout <= 0:
            raise ValueError("workflow_timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.retry_delay < 0:
            raise ValueError("retry_delay must be non-negative")


# Default configuration
DEFAULT_CONFIG = OpenAIAgentsConfig()
