"""
Aigie Rules Module - Local rules engine for fast interception decisions.

This module provides a fast, local rules engine that can make interception
decisions without network calls, enabling sub-5ms decision latency.
"""

from .engine import LocalRulesEngine, Rule, RuleResult, RuleDecision
from .builtin import (
    CostLimitRule,
    TokenLimitRule,
    BlockedPatternsRule,
    RateLimitRule,
    ContextDriftRule,
)

__all__ = [
    # Core
    "LocalRulesEngine",
    "Rule",
    "RuleResult",
    "RuleDecision",
    # Built-in Rules
    "CostLimitRule",
    "TokenLimitRule",
    "BlockedPatternsRule",
    "RateLimitRule",
    "ContextDriftRule",
]
