"""
Evaluation criteria for LLM Judge.

Defines the types of issues that can be detected and the criteria
for evaluating LLM outputs in real-time.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List


class IssueType(Enum):
    """Types of issues that can be detected by the judge."""

    # Errors
    ERROR_RUNTIME = "error_runtime"
    """Runtime error in tool call or function execution."""

    ERROR_VALIDATION = "error_validation"
    """Validation error in input/output format."""

    ERROR_API = "error_api"
    """API error from LLM provider."""

    # Drift
    DRIFT_CONTEXT = "drift_context"
    """Context drift - agent deviating from original task."""

    DRIFT_TOPIC = "drift_topic"
    """Topic drift - conversation going off-topic."""

    DRIFT_BEHAVIOR = "drift_behavior"
    """Behavior drift - agent acting differently than expected."""

    # Hallucination
    HALLUCINATION_FACTUAL = "hallucination_factual"
    """Factual hallucination - stating false information as fact."""

    HALLUCINATION_TOOL = "hallucination_tool"
    """Tool hallucination - referring to non-existent tools/functions."""

    HALLUCINATION_REFERENCE = "hallucination_reference"
    """Reference hallucination - citing non-existent sources."""

    # Quality
    QUALITY_COHERENCE = "quality_coherence"
    """Coherence issue - response doesn't make logical sense."""

    QUALITY_RELEVANCE = "quality_relevance"
    """Relevance issue - response not relevant to the query."""

    QUALITY_COMPLETENESS = "quality_completeness"
    """Completeness issue - response missing required information."""

    # Safety
    SAFETY_HARMFUL = "safety_harmful"
    """Potentially harmful content detected."""

    SAFETY_PII = "safety_pii"
    """PII (Personally Identifiable Information) exposure."""

    SAFETY_INJECTION = "safety_injection"
    """Prompt injection attempt detected."""

    # Loop Detection
    LOOP_REPETITION = "loop_repetition"
    """Repetitive output detected (agent stuck in loop)."""

    LOOP_CIRCULAR = "loop_circular"
    """Circular reasoning or logic detected."""

    # Other
    OTHER = "other"
    """Other issue type not covered above."""


class IssueSeverity(Enum):
    """Severity levels for detected issues."""

    CRITICAL = "critical"
    """Critical issue - must stop and retry immediately."""

    HIGH = "high"
    """High severity - should trigger remediation."""

    MEDIUM = "medium"
    """Medium severity - may need intervention."""

    LOW = "low"
    """Low severity - log and monitor."""

    INFO = "info"
    """Informational only."""


@dataclass
class DetectedIssue:
    """A single issue detected by the judge."""

    issue_type: IssueType
    """Type of issue detected."""

    severity: IssueSeverity
    """Severity of the issue."""

    description: str
    """Human-readable description of the issue."""

    confidence: float = 0.0
    """Confidence score for this detection (0.0-1.0)."""

    evidence: Optional[str] = None
    """Evidence or specific text that triggered detection."""

    span_id: Optional[str] = None
    """ID of the span where issue was detected."""

    suggested_fix: Optional[str] = None
    """Suggested remediation for this issue."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata about the issue."""


@dataclass
class EvaluationResult:
    """Result of evaluating a span output."""

    has_issues: bool
    """Whether any issues were detected."""

    should_retry: bool
    """Whether the span should be retried."""

    should_stop: bool
    """Whether execution should stop completely."""

    issues: List[DetectedIssue] = field(default_factory=list)
    """List of detected issues."""

    overall_score: float = 1.0
    """Overall quality score (0.0 = bad, 1.0 = good)."""

    reasoning: Optional[str] = None
    """Judge's reasoning for the evaluation."""

    suggested_remediation: Optional[str] = None
    """Overall suggested remediation if issues detected."""

    latency_ms: float = 0.0
    """Time taken for evaluation in milliseconds."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional evaluation metadata."""

    @classmethod
    def passed(cls, score: float = 1.0, latency_ms: float = 0.0) -> "EvaluationResult":
        """Create a passing evaluation result."""
        return cls(
            has_issues=False,
            should_retry=False,
            should_stop=False,
            overall_score=score,
            latency_ms=latency_ms,
        )

    @classmethod
    def failed(
        cls,
        issues: List[DetectedIssue],
        should_retry: bool = True,
        should_stop: bool = False,
        reasoning: Optional[str] = None,
        suggested_remediation: Optional[str] = None,
        latency_ms: float = 0.0,
    ) -> "EvaluationResult":
        """Create a failing evaluation result."""
        # Calculate overall score based on issues
        if not issues:
            score = 1.0
        else:
            severity_weights = {
                IssueSeverity.CRITICAL: 0.0,
                IssueSeverity.HIGH: 0.3,
                IssueSeverity.MEDIUM: 0.6,
                IssueSeverity.LOW: 0.8,
                IssueSeverity.INFO: 0.95,
            }
            worst_severity = min(i.severity for i in issues)
            score = severity_weights.get(worst_severity, 0.5)

        return cls(
            has_issues=True,
            should_retry=should_retry,
            should_stop=should_stop,
            issues=issues,
            overall_score=score,
            reasoning=reasoning,
            suggested_remediation=suggested_remediation,
            latency_ms=latency_ms,
        )


@dataclass
class JudgeCriteria:
    """
    Configuration for what the judge should evaluate.

    Allows customization of which issue types to detect
    and what thresholds to use.
    """

    # Issue types to check
    check_errors: bool = True
    """Check for runtime/validation errors."""

    check_drift: bool = True
    """Check for context/topic/behavior drift."""

    check_hallucination: bool = True
    """Check for hallucinations."""

    check_quality: bool = True
    """Check for quality issues (coherence, relevance)."""

    check_safety: bool = True
    """Check for safety issues (harmful content, PII)."""

    check_loops: bool = True
    """Check for repetition loops."""

    # Thresholds
    drift_threshold: float = 0.7
    """Threshold for drift detection (0.0-1.0)."""

    hallucination_threshold: float = 0.6
    """Threshold for hallucination detection (0.0-1.0)."""

    quality_threshold: float = 0.5
    """Minimum quality score threshold (0.0-1.0)."""

    repetition_threshold: float = 0.8
    """Threshold for repetition detection (0.0-1.0)."""

    # Retry behavior
    auto_retry_on_critical: bool = True
    """Automatically retry on critical issues."""

    auto_retry_on_high: bool = True
    """Automatically retry on high severity issues."""

    max_retries: int = 3
    """Maximum number of retries per span."""

    # Context
    include_full_history: bool = True
    """Include full conversation history in evaluation."""

    history_window: int = 10
    """Number of previous messages to include if not full history."""

    include_tool_results: bool = True
    """Include tool call results in evaluation."""

    include_system_prompt: bool = True
    """Include system prompt in evaluation context."""

    # Custom criteria
    custom_instructions: Optional[str] = None
    """Custom evaluation instructions for the judge."""

    blocked_patterns: List[str] = field(default_factory=list)
    """Patterns that should always trigger issues."""

    required_patterns: List[str] = field(default_factory=list)
    """Patterns that must be present in valid responses."""

    @classmethod
    def strict(cls) -> "JudgeCriteria":
        """Create strict criteria for high-reliability scenarios."""
        return cls(
            check_errors=True,
            check_drift=True,
            check_hallucination=True,
            check_quality=True,
            check_safety=True,
            check_loops=True,
            drift_threshold=0.5,
            hallucination_threshold=0.4,
            quality_threshold=0.7,
            repetition_threshold=0.6,
            auto_retry_on_critical=True,
            auto_retry_on_high=True,
            max_retries=3,
            include_full_history=True,
        )

    @classmethod
    def balanced(cls) -> "JudgeCriteria":
        """Create balanced criteria for general use."""
        return cls(
            check_errors=True,
            check_drift=True,
            check_hallucination=True,
            check_quality=True,
            check_safety=True,
            check_loops=True,
            drift_threshold=0.7,
            hallucination_threshold=0.6,
            quality_threshold=0.5,
            repetition_threshold=0.8,
            auto_retry_on_critical=True,
            auto_retry_on_high=False,
            max_retries=2,
            include_full_history=False,
            history_window=10,
        )

    @classmethod
    def permissive(cls) -> "JudgeCriteria":
        """Create permissive criteria for low-risk scenarios."""
        return cls(
            check_errors=True,
            check_drift=False,
            check_hallucination=False,
            check_quality=False,
            check_safety=True,
            check_loops=True,
            drift_threshold=0.9,
            hallucination_threshold=0.8,
            quality_threshold=0.3,
            repetition_threshold=0.9,
            auto_retry_on_critical=True,
            auto_retry_on_high=False,
            max_retries=1,
            include_full_history=False,
            history_window=5,
        )
