"""
Type definitions for metric context parameters.

Provides TypedDict classes for type-safe context validation.
"""

from typing import TypedDict, Optional, Dict, Any, List


class MetricContextBase(TypedDict, total=False):
    """Base context type for all metrics."""
    trace_id: Optional[str]
    span_id: Optional[str]
    function_name: Optional[str]
    span_type: Optional[str]
    timestamp: Optional[str]
    api_url: Optional[str]
    aigie_client: Optional[Any]


class DriftContext(MetricContextBase, total=False):
    """Context type for drift detection metric."""
    baseline_context: str
    current_context: str
    drift_type: str  # "semantic", "structural", etc.
    baseline_trace_id: Optional[str]
    similarity_score: Optional[float]


class RecoveryContext(MetricContextBase, total=False):
    """Context type for recovery success metric."""
    original_error: str
    error: Optional[str]  # Alternative to original_error
    error_type: str
    recovery_strategy: str
    recovery_success: bool
    recovery_duration_ms: int
    recovery_metadata: Optional[Dict[str, Any]]
    recovery_result: Optional[str]


class CheckpointContext(MetricContextBase, total=False):
    """Context type for checkpoint validity metric."""
    checkpoint_id: str
    checkpoint_type: str
    state_snapshot: Dict[str, Any]
    execution_path: List[Any]


class NestedAgentContext(MetricContextBase, total=False):
    """Context type for nested agent health metric."""
    nested_depth: int
    agent_hierarchy: Dict[str, Any]
    nested_agents: List[Dict[str, Any]]
    parent_agent_id: Optional[str]
    agent_handoffs: Optional[List[Any]]


class ProductionReliabilityContext(MetricContextBase, total=False):
    """Context type for production reliability composite metric."""
    drift: Optional[DriftContext]
    recovery: Optional[RecoveryContext]
    checkpoint: Optional[CheckpointContext]
    nested: Optional[NestedAgentContext]







