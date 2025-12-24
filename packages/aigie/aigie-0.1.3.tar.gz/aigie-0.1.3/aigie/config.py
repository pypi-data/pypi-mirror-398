"""
Configuration management for Aigie SDK.

Enhanced with:
- Data masking support for PII protection
- Debug mode with detailed logging
- I/O capture control defaults
- Query API configuration
"""

import os
import logging
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field


@dataclass
class Config:
    """
    Configuration for Aigie SDK.

    Usage:
        config = Config(
            api_url="https://portal.aigie.io/api",
            api_key="your-key",
            batch_size=100,
            flush_interval=5.0
        )
        aigie = Aigie(config=config)
    """
    
    # API Configuration
    api_url: str = field(default_factory=lambda: os.getenv("AIGIE_API_URL", "https://portal.aigie.io/api"))
    api_key: str = field(default_factory=lambda: os.getenv("AIGIE_API_KEY", ""))
    
    # Buffering Configuration
    enable_buffering: bool = True
    batch_size: int = 100
    flush_interval: float = 5.0  # seconds
    
    # Retry Configuration
    max_retries: int = 3
    retry_delay: float = 1.0  # base delay in seconds
    exponential_backoff: bool = True
    
    # HTTP Configuration
    timeout: float = 30.0
    max_connections: int = 10
    
    # OpenTelemetry Configuration
    enable_otel: bool = False
    otel_service_name: Optional[str] = None
    
    # Logging Configuration
    log_level: str = "INFO"
    enable_debug: bool = False
    
    # Advanced Configuration
    enable_circuit_breaker: bool = True
    circuit_breaker_threshold: int = 5  # failures before opening
    circuit_breaker_timeout: float = 60.0  # seconds before retry
    
    # Compression Configuration
    enable_compression: bool = field(
        default_factory=lambda: os.getenv("AIGIE_ENABLE_COMPRESSION", "true").lower() == "true"
    )
    compression_algorithm: str = field(
        default_factory=lambda: os.getenv("AIGIE_COMPRESSION_ALGORITHM", "zstd")
    )
    compression_level: Optional[int] = field(
        default_factory=lambda: int(os.getenv("AIGIE_COMPRESSION_LEVEL", "1")) if os.getenv("AIGIE_COMPRESSION_LEVEL") else 1
    )
    
    # Sampling Configuration
    sampling_rate: Optional[float] = field(
        default_factory=lambda: float(os.getenv("AIGIE_SAMPLING_RATE")) if os.getenv("AIGIE_SAMPLING_RATE") else None
    )

    # Auto-Instrumentation Configuration
    enable_auto_instrument: bool = field(
        default_factory=lambda: os.getenv("AIGIE_AUTO_INSTRUMENT", "true").lower() not in ("false", "0", "no")
    )
    disable_auto_instrument: bool = field(
        default_factory=lambda: os.getenv("AIGIE_DISABLE_AUTO_INSTRUMENT", "false").lower() in ("true", "1", "yes")
    )

    # Data Masking Configuration
    # Function to mask sensitive data before sending to API
    mask: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None

    # Default I/O Capture Control
    # Can be overridden per-decorator
    default_capture_input: bool = field(
        default_factory=lambda: os.getenv("AIGIE_CAPTURE_INPUT", "true").lower() == "true"
    )
    default_capture_output: bool = field(
        default_factory=lambda: os.getenv("AIGIE_CAPTURE_OUTPUT", "true").lower() == "true"
    )

    # Debug Mode
    debug: bool = field(
        default_factory=lambda: os.getenv("AIGIE_DEBUG", "false").lower() in ("true", "1", "yes")
    )

    # Blocked Instrumentation Scopes
    # List of instrumentation scope names to exclude from tracing
    blocked_instrumentation_scopes: List[str] = field(default_factory=list)

    # NEW: User/Session Defaults
    default_user_id: Optional[str] = field(
        default_factory=lambda: os.getenv("AIGIE_DEFAULT_USER_ID")
    )
    default_session_id: Optional[str] = field(
        default_factory=lambda: os.getenv("AIGIE_DEFAULT_SESSION_ID")
    )

    # NEW: Environment/Release Configuration
    environment: Optional[str] = field(
        default_factory=lambda: os.getenv("AIGIE_ENVIRONMENT") or os.getenv("ENVIRONMENT")
    )
    release: Optional[str] = field(
        default_factory=lambda: os.getenv("AIGIE_RELEASE") or os.getenv("RELEASE")
    )

    # =========================================================================
    # Real-Time Runtime Interception Configuration
    # =========================================================================

    # Enable/disable the interception layer
    enable_interception: bool = field(
        default_factory=lambda: os.getenv("AIGIE_ENABLE_INTERCEPTION", "true").lower() == "true"
    )

    # Enable real-time backend consultation via WebSocket
    enable_backend_realtime: bool = field(
        default_factory=lambda: os.getenv("AIGIE_ENABLE_BACKEND_REALTIME", "false").lower() == "true"
    )

    # Timeout for local hook execution (milliseconds)
    local_decision_timeout_ms: float = field(
        default_factory=lambda: float(os.getenv("AIGIE_LOCAL_DECISION_TIMEOUT_MS", "5"))
    )

    # Timeout for backend consultation (milliseconds)
    backend_consultation_timeout_ms: float = field(
        default_factory=lambda: float(os.getenv("AIGIE_BACKEND_CONSULTATION_TIMEOUT_MS", "500"))
    )

    # Cost limit per trace (None = no limit)
    cost_limit_per_trace: Optional[float] = field(
        default_factory=lambda: float(os.getenv("AIGIE_COST_LIMIT_PER_TRACE")) if os.getenv("AIGIE_COST_LIMIT_PER_TRACE") else None
    )

    # Cost limit per request (None = no limit)
    cost_limit_per_request: Optional[float] = field(
        default_factory=lambda: float(os.getenv("AIGIE_COST_LIMIT_PER_REQUEST")) if os.getenv("AIGIE_COST_LIMIT_PER_REQUEST") else None
    )

    # Token limit per request (None = no limit)
    token_limit_per_request: Optional[int] = field(
        default_factory=lambda: int(os.getenv("AIGIE_TOKEN_LIMIT_PER_REQUEST")) if os.getenv("AIGIE_TOKEN_LIMIT_PER_REQUEST") else None
    )

    # Drift detection threshold (0.0-1.0, higher = more sensitive)
    drift_threshold: float = field(
        default_factory=lambda: float(os.getenv("AIGIE_DRIFT_THRESHOLD", "0.7"))
    )

    # Enable automatic drift detection
    enable_drift_detection: bool = field(
        default_factory=lambda: os.getenv("AIGIE_ENABLE_DRIFT_DETECTION", "true").lower() == "true"
    )

    # Blocked patterns (regex patterns to block in requests)
    blocked_patterns: List[str] = field(default_factory=list)

    # Rate limit per minute (None = no limit)
    rate_limit_per_minute: Optional[int] = field(
        default_factory=lambda: int(os.getenv("AIGIE_RATE_LIMIT_PER_MINUTE")) if os.getenv("AIGIE_RATE_LIMIT_PER_MINUTE") else None
    )

    # Enable automatic fix application from backend
    enable_auto_fix: bool = field(
        default_factory=lambda: os.getenv("AIGIE_ENABLE_AUTO_FIX", "true").lower() == "true"
    )

    # Maximum retry attempts for auto-fix
    auto_fix_max_retries: int = field(
        default_factory=lambda: int(os.getenv("AIGIE_AUTO_FIX_MAX_RETRIES", "2"))
    )

    # =========================================================================
    # Aigie Token Configuration
    # =========================================================================

    # Aigie token for authentication (get yours at https://app.aigie.io)
    aigie_token: Optional[str] = field(
        default_factory=lambda: os.getenv("AIGIE_TOKEN")
    )

    # License server URL (defaults to Aigie's licensing server)
    license_server_url: str = field(
        default_factory=lambda: os.getenv("AIGIE_LICENSE_SERVER", "https://portal.aigie.io")
    )

    # Unique installation ID (auto-generated if not provided)
    installation_id: Optional[str] = field(
        default_factory=lambda: os.getenv("AIGIE_INSTALLATION_ID")
    )

    # Enable usage telemetry reporting to license server
    enable_usage_telemetry: bool = field(
        default_factory=lambda: os.getenv("AIGIE_USAGE_TELEMETRY", "true").lower() == "true"
    )

    # Skip license validation (for development/testing only)
    skip_license_validation: bool = field(
        default_factory=lambda: os.getenv("AIGIE_SKIP_LICENSE_VALIDATION", "false").lower() == "true"
    )

    def __post_init__(self):
        """Normalize configuration values."""
        # Ensure API URL doesn't end with /
        self.api_url = self.api_url.rstrip('/')

        # Validate batch size
        if self.batch_size < 1:
            self.batch_size = 1
        if self.batch_size > 1000:
            self.batch_size = 1000

        # Validate flush interval
        if self.flush_interval < 0.1:
            self.flush_interval = 0.1
        if self.flush_interval > 60:
            self.flush_interval = 60

        # Configure logging based on debug mode
        if self.debug:
            logging.getLogger("aigie").setLevel(logging.DEBUG)
            # Also set global debug mode for decorators
            from . import decorators_v3
            decorators_v3.set_debug_mode(True)

        # Set global mask function if provided
        if self.mask:
            from . import decorators_v3
            decorators_v3.set_global_mask_fn(self.mask)
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables."""
        # Parse blocked scopes from comma-separated env var
        blocked_scopes_str = os.getenv("AIGIE_BLOCKED_INSTRUMENTATION_SCOPES", "")
        blocked_scopes = [s.strip() for s in blocked_scopes_str.split(",") if s.strip()]

        return cls(
            api_url=os.getenv("AIGIE_API_URL", "https://portal.aigie.io/api"),
            api_key=os.getenv("AIGIE_API_KEY", ""),
            enable_buffering=os.getenv("AIGIE_ENABLE_BUFFERING", "true").lower() == "true",
            batch_size=int(os.getenv("AIGIE_BATCH_SIZE", "100")),
            flush_interval=float(os.getenv("AIGIE_FLUSH_INTERVAL", "5.0")),
            max_retries=int(os.getenv("AIGIE_MAX_RETRIES", "3")),
            log_level=os.getenv("AIGIE_LOG_LEVEL", "INFO"),
            enable_debug=os.getenv("AIGIE_DEBUG", "false").lower() == "true",
            # New fields
            debug=os.getenv("AIGIE_DEBUG", "false").lower() in ("true", "1", "yes"),
            default_capture_input=os.getenv("AIGIE_CAPTURE_INPUT", "true").lower() == "true",
            default_capture_output=os.getenv("AIGIE_CAPTURE_OUTPUT", "true").lower() == "true",
            blocked_instrumentation_scopes=blocked_scopes,
            default_user_id=os.getenv("AIGIE_DEFAULT_USER_ID"),
            default_session_id=os.getenv("AIGIE_DEFAULT_SESSION_ID"),
            environment=os.getenv("AIGIE_ENVIRONMENT") or os.getenv("ENVIRONMENT"),
            release=os.getenv("AIGIE_RELEASE") or os.getenv("RELEASE"),
        )
    
    def validate_self_hosted(self) -> List[str]:
        """
        Validate configuration for self-hosted deployments.

        Returns:
            List of validation warnings/errors (empty if valid)
        """
        warnings = []

        # Check if using cloud URL without token
        if "portal.aigie.io" in self.api_url or "app.aigie.io" in self.api_url:
            if not self.aigie_token:
                warnings.append(
                    "Using Aigie cloud URL but AIGIE_TOKEN is not set. "
                    "Get your token at https://portal.aigie.io"
                )

        # Check for HTTP (not HTTPS) in non-localhost URLs
        if self.api_url.startswith("http://"):
            is_local = any(host in self.api_url for host in ["localhost", "127.0.0.1", "0.0.0.0"])
            if not is_local:
                warnings.append(
                    f"API URL uses HTTP instead of HTTPS: {self.api_url}. "
                    "This is insecure for production deployments."
                )

        # Check license server URL security
        if self.license_server_url.startswith("http://"):
            is_local = any(host in self.license_server_url for host in ["localhost", "127.0.0.1", "0.0.0.0"])
            if not is_local:
                warnings.append(
                    f"License server URL uses HTTP instead of HTTPS: {self.license_server_url}. "
                    "This is insecure for production deployments."
                )

        # Check for empty API key in non-development scenarios
        if not self.api_key and not self.skip_license_validation:
            env = os.getenv("ENV", "development").lower()
            if env in ("production", "prod", "staging"):
                warnings.append(
                    "AIGIE_API_KEY is not set in production/staging environment. "
                    "API authentication may fail."
                )

        # Check for sampling rate validity
        if self.sampling_rate is not None:
            if not (0.0 <= self.sampling_rate <= 1.0):
                warnings.append(
                    f"Invalid sampling_rate: {self.sampling_rate}. Must be between 0.0 and 1.0."
                )

        return warnings

    def validate_and_warn(self) -> None:
        """
        Validate configuration and log warnings.

        Call this during initialization to get early feedback on configuration issues.
        """
        warnings = self.validate_self_hosted()
        if warnings:
            for warning in warnings:
                logging.getLogger("aigie").warning(f"Configuration warning: {warning}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary (excluding sensitive data)."""
        return {
            "api_url": self.api_url,
            "enable_buffering": self.enable_buffering,
            "batch_size": self.batch_size,
            "flush_interval": self.flush_interval,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "log_level": self.log_level,
            "enable_debug": self.enable_debug,
            # New fields
            "debug": self.debug,
            "default_capture_input": self.default_capture_input,
            "default_capture_output": self.default_capture_output,
            "blocked_instrumentation_scopes": self.blocked_instrumentation_scopes,
            "environment": self.environment,
            "release": self.release,
            "has_mask_fn": self.mask is not None,
            # Interception fields
            "enable_interception": self.enable_interception,
            "enable_backend_realtime": self.enable_backend_realtime,
            "local_decision_timeout_ms": self.local_decision_timeout_ms,
            "backend_consultation_timeout_ms": self.backend_consultation_timeout_ms,
            "cost_limit_per_trace": self.cost_limit_per_trace,
            "cost_limit_per_request": self.cost_limit_per_request,
            "token_limit_per_request": self.token_limit_per_request,
            "drift_threshold": self.drift_threshold,
            "enable_drift_detection": self.enable_drift_detection,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "enable_auto_fix": self.enable_auto_fix,
            "auto_fix_max_retries": self.auto_fix_max_retries,
            # Token fields (mask the token)
            "has_aigie_token": self.aigie_token is not None,
            "license_server_url": self.license_server_url,
            "enable_usage_telemetry": self.enable_usage_telemetry,
            "skip_license_validation": self.skip_license_validation,
        }








