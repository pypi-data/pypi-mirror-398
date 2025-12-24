"""
Aigie Judge Module - LLM-based evaluation for real-time error detection.

This module provides LLM Judge capabilities to evaluate span outputs
and detect issues (errors, drift, hallucination) in real-time, enabling
step-level retry with remediation.
"""

from .criteria import (
    JudgeCriteria,
    EvaluationResult,
    IssueType,
    IssueSeverity,
    DetectedIssue,
)
from .evaluator import (
    LLMJudge,
    JudgeConfig,
    JudgeDecision,
    SpanEvaluation,
)
from .context_aggregator import (
    ContextAggregator,
    AggregatedContext,
    SpanHistory,
)

__all__ = [
    # Criteria
    "JudgeCriteria",
    "EvaluationResult",
    "IssueType",
    "IssueSeverity",
    "DetectedIssue",
    # Evaluator
    "LLMJudge",
    "JudgeConfig",
    "JudgeDecision",
    "SpanEvaluation",
    # Context
    "ContextAggregator",
    "AggregatedContext",
    "SpanHistory",
]

# Verify imports work
__version__ = "1.0.0"
