"""
Configuration for browser-use tracing.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class BrowserUseConfig:
    """Configuration for browser-use tracing behavior.

    Attributes:
        trace_screenshots: Whether to capture screenshots as span attachments
        trace_dom: Whether to capture DOM snapshots (can be large)
        trace_browser_actions: Whether to trace individual browser actions
        trace_llm_calls: Whether to trace LLM calls
        trace_agent_steps: Whether to trace each agent step
        compress_screenshots: Whether to compress screenshot images
        screenshot_quality: JPEG quality for screenshots (1-100)
        max_screenshot_size: Maximum screenshot size in bytes before downscaling
        include_action_selectors: Whether to include CSS selectors in action spans
        mask_sensitive_data: Whether to mask potentially sensitive data in traces
        action_timeout: Timeout in seconds for browser actions
        llm_timeout: Timeout in seconds for LLM calls
        step_timeout: Timeout in seconds for agent steps
        max_retries: Maximum number of retries for failed operations
        retry_delay: Initial delay between retries in seconds (exponential backoff)
        retry_on_errors: List of error types to retry on (empty = retry all)
    """

    # Tracing toggles
    trace_screenshots: bool = True
    trace_dom: bool = False
    trace_browser_actions: bool = True
    trace_llm_calls: bool = True
    trace_agent_steps: bool = True

    # Screenshot settings
    compress_screenshots: bool = True
    screenshot_quality: int = 80
    max_screenshot_size: int = 500_000  # 500KB

    # Action tracing
    include_action_selectors: bool = True

    # Privacy
    mask_sensitive_data: bool = False

    # Span naming
    span_prefix: str = "browser_use"

    # Timeout settings (in seconds)
    action_timeout: float = 30.0  # 30 seconds for browser actions
    llm_timeout: float = 120.0  # 2 minutes for LLM calls
    step_timeout: float = 300.0  # 5 minutes for agent steps

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0  # Initial delay, doubles each retry
    retry_on_errors: list = field(default_factory=list)  # Empty = retry all transient errors

    # Metadata
    default_tags: Dict[str, str] = field(default_factory=dict)
    default_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate configuration."""
        if not 1 <= self.screenshot_quality <= 100:
            raise ValueError("screenshot_quality must be between 1 and 100")
        if self.max_screenshot_size < 10_000:
            raise ValueError("max_screenshot_size must be at least 10KB")
        if self.action_timeout <= 0:
            raise ValueError("action_timeout must be positive")
        if self.llm_timeout <= 0:
            raise ValueError("llm_timeout must be positive")
        if self.step_timeout <= 0:
            raise ValueError("step_timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.retry_delay < 0:
            raise ValueError("retry_delay must be non-negative")
