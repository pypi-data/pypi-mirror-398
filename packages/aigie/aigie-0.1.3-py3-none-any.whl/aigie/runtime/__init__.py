"""
Aigie Runtime Module - Real-time span interception and remediation.

This module provides runtime capabilities for intercepting spans,
detecting issues, and applying remediation at the step level.
"""

from .span_interceptor import (
    SpanInterceptor,
    SpanInterceptorConfig,
    SpanDecision,
    SpanInterceptionResult,
)
from .remediation_loop import (
    RemediationLoop,
    RemediationConfig,
    RemediationResult,
    RemediationStrategy,
    OperationalMode,
    WorkflowPattern,
)

__all__ = [
    # Span Interceptor
    "SpanInterceptor",
    "SpanInterceptorConfig",
    "SpanDecision",
    "SpanInterceptionResult",
    # Remediation Loop
    "RemediationLoop",
    "RemediationConfig",
    "RemediationResult",
    "RemediationStrategy",
    "OperationalMode",
    "WorkflowPattern",
]
