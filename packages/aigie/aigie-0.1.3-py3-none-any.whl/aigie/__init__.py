"""
Aigie SDK - Production-Grade AI Agent Infrastructure

95% of AI agents never reach production due to context drift, tool errors, and
runtime instability. Aigie provides the infrastructure that makes autonomous AI
reliable and production-grade.

Unlike traditional observability tools that only monitor, Aigie:
- DETECTS context drift and errors before they impact users
- FIXES issues automatically through self-healing workflows
- PREVENTS failures with predictive intervention

Core Features:
- @traceable decorator for automatic tracing
- LLM auto-instrumentation (OpenAI, Anthropic, Gemini)
- Token counting and cost tracking
- Prompt management with versioning
- Online evaluation scoring
- Context propagation for nested traces
- Streaming support for generators

Reliability Features (Unique to Aigie):
- Context drift detection
- Auto-error correction
- Production guardrails
- Self-healing workflows
- Reliability scoring

Usage:
    from aigie import Aigie, traceable

    # Initialize client
    aigie = Aigie(api_key="your-key")
    await aigie.initialize()

    # Use decorator for automatic tracing
    @traceable(run_type="agent")
    async def my_agent(query: str):
        return await process(query)

    # Score traces for quality monitoring
    from aigie import score
    await score(trace_id, "accuracy", 0.95)

    # Manage prompts with versioning
    from aigie import Prompt
    prompt = Prompt.chat(
        name="research_agent",
        messages=[{"role": "system", "content": "You are helpful."}]
    )
"""

import sys
from typing import TYPE_CHECKING, Any

# Core exports (always available)
__all__ = [
    # Client
    "Aigie",
    "Config",
    "init",
    "get_aigie",

    # Context managers
    "TraceContext",
    "SpanContext",

    # Decorators (v3)
    "traceable",
    "trace",
    "create_traceable",
    "set_global_mask_fn",
    "set_debug_mode",

    # Context propagation (new!)
    "tracing_context",
    "get_current_trace_context",
    "get_current_span_context",
    "is_tracing_enabled",
    "set_tracing_enabled",

    # Wrappers (new!)
    "wrap_openai",
    "wrap_anthropic",
    "wrap_gemini",
    "wrap_bedrock",
    "create_traced_bedrock",
    "wrap_cohere",
    "create_traced_cohere",

    # Compression (new!)
    "Compressor",
    "is_compression_available",

    # Buffer
    "EventBuffer",

    # Feedback Collection (Intelligence)
    "FeedbackCollector",

    # W3C Trace Context
    "W3CTraceContext",
    "extract_trace_context",
    "inject_trace_context",

    # Prompts
    "Prompt",
    "PromptManager",
    "PromptFormat",
    "TextPrompt",
    "ChatPrompt",
    "get_prompt_manager",
    "register_prompt",
    "get_prompt",

    # Evaluation
    "EvaluationHook",
    "Evaluator",
    "EvaluationResult",
    "ScoreType",
    "Score",
    "ScoreDataType",
    "ScoreManager",
    "get_score_manager",
    "score",
    "feedback",

    # Metrics (new!)
    "BaseMetric",
    "DriftDetectionMetric",
    "RecoverySuccessMetric",
    "CheckpointValidityMetric",
    "NestedAgentHealthMetric",
    "ProductionReliabilityMetric",

    # Component-level evaluation (new!)
    "observe",

    # Streaming
    "StreamingSpan",

    # Evaluations API (NEW!)
    "EvaluationsClient",
    "EvaluationType",
    "EvaluationTemplate",
    "EvaluationScore",
    "EvaluationJob",
    "EvaluationRequest",
    "evaluate",

    # Judges API (NEW!)
    "JudgesClient",
    "JudgeType",
    "Judge",
    "JudgeResult",
    "JudgeConfig",
    "judge",
    "judge_all",

    # Phase 2 Features
    # Datasets
    "DatasetsClient",
    "Dataset",
    "DatasetExample",
    "DatasetRunResult",
    "DatasetRunSummary",

    # Sessions
    "SessionManager",
    "SessionAnalytics",
    "Session",
    "SessionMessage",
    "create_session_manager",

    # Phase 3 Features
    # LangGraph integration
    "LangGraphHandler",
    "wrap_langgraph",
    "trace_langgraph_node",
    "trace_langgraph_edge",
    "create_langgraph_handler",

    # Enhanced batch evaluation
    "enhanced_batch_evaluate",
    "generate_batch_report",
    "export_batch_results",
    "export_batch_results_to_csv",
    "BatchProgress",
    "TestCaseResult",
    "BatchStatistics",
    "BatchEvaluationResult",

    # Experiments API
    "ExperimentsClient",
    "create_experiments_client",
    "generate_experiment_report",
    "ExperimentVariant",
    "VariantResult",
    "VariantStatistics",
    "WinnerInfo",
    "ExperimentResult",

    # Cost Tracking (Gap Fix)
    "extract_usage_from_response",
    "extract_and_calculate_cost",
    "calculate_cost",
    "add_model_pricing",
    "get_supported_models",
    "get_model_pricing",
    "CostAggregator",
    "UsageMetadata",
    "CostBreakdown",

    # Summary Evaluators (Gap Fix)
    "SummaryEvaluator",
    "AccuracySummaryEvaluator",
    "PrecisionSummaryEvaluator",
    "AverageScoreSummaryEvaluator",
    "PassRateSummaryEvaluator",
    "CostSummaryEvaluator",
    "LatencySummaryEvaluator",
    "run_summary_evaluators",
    "create_standard_summary_evaluators",
    "RunData",
    "SummaryEvaluationResult",
    "SummaryEvaluatorFunction",

    # Safety Metrics (Gap Fix)
    "PIILeakageEvaluator",
    "ToxicityEvaluator",
    "BiasEvaluator",
    "PromptInjectionEvaluator",
    "JailbreakEvaluator",
    "RedTeamScanner",
    "create_safety_evaluators",

    # Pytest Integration (Gap Fix)
    "AigieTestCase",
    "aigie_assert",
    "assert_test",

    # UUID v7 (Gap Fix)
    "uuidv7",
    "extract_timestamp",
    "is_valid_uuidv7",
    "uuidv7_to_datetime",
    "compare_uuidv7",
    "generate_batch_uuidv7",
    "uuidv7_with_timestamp",
    "get_uuidv7_age",

    # Sampling System (Gap Fix)
    "Sampler",
    "SamplingConfig",
    "AdaptiveConfig",
    "create_smart_sampler",
    "create_adaptive_sampler",
    "create_importance_function",

    # Query API (Feature Parity)
    "QueryAPI",
    "TraceAPI",
    "ObservationsAPI",
    "SessionsAPI",
    "ScoresAPI",
    "Trace",
    "Observation",
    "ObservationType",
    "TraceFilter",
    "PaginatedResponse",

    # Human Annotations (Feature Parity)
    "AnnotationsAPI",
    "AnnotationQueue",
    "Annotation",
    "AnnotationType",
    "AnnotationTask",

    # Playground (Feature Parity)
    "Playground",
    "PromptRegistry",
    "PromptTemplate",
    "PlaygroundRun",
    "ComparisonResult",
    "ModelConfig",
    "ModelProvider",
    "create_playground",

    # Agent Graph View (Feature Parity)
    "AgentGraph",
    "GraphBuilder",
    "GraphNode",
    "GraphEdge",
    "NodeType",
    "EdgeType",
    "NodeStatus",
    "ExecutionPath",
    "GraphMetrics",
    "create_graph",
    "create_graph_builder",

    # Alerting (Feature Parity)
    "AlertManager",
    "AlertRule",
    "AlertEvent",
    "AlertCondition",
    "AlertSeverity",
    "AlertStatus",
    "MetricType",
    "ComparisonOperator",
    "AggregationWindow",
    "NotificationChannel",
    "SlackChannel",
    "EmailChannel",
    "WebhookChannel",
    "PagerDutyChannel",
    "create_alert_manager",

    # Span Replay (Feature Parity)
    "SpanReplay",
    "CapturedSpan",
    "ReplayResult",
    "ReplayExperiment",
    "ReplayStatus",
    "create_span_replay",

    # Leaderboards (Feature Parity)
    "LeaderboardManager",
    "Leaderboard",
    "LeaderboardEntry",
    "ComparisonPair",
    "EloRating",
    "RankingMetric",
    "AggregationType",
    "create_leaderboard_manager",
    "create_model_leaderboard",
    "create_prompt_leaderboard",

    # License Management (Self-Hosted)
    "LicenseValidator",
    "LicenseInfo",
    "UsageSummary",
    "LicenseError",
    "LicenseExpiredError",
    "LicenseRevokedError",
    "LicenseLimitExceededError",

    # Telemetry (SDK Feature Tracking)
    "track_feature",
    "record_error",
    "FeatureTracker",
    "ErrorCollector",
]

__version__ = "0.1.3"


# Lazy imports for performance
def __getattr__(name: str) -> Any:
    """
    Lazy import implementation for faster load times.

    Modules are only imported when actually used, reducing cold start penalty.
    """
    # Core client
    if name == "Aigie":
        from .client import Aigie
        return Aigie

    if name == "Config":
        from .config import Config
        return Config
    
    if name == "init":
        from .client import init
        return init
    
    if name == "get_aigie":
        from .client import get_aigie
        return get_aigie

    # Context managers
    if name == "TraceContext":
        from .trace import TraceContext
        return TraceContext

    if name == "SpanContext":
        from .span import SpanContext
        return SpanContext

    # Decorators (v3)
    if name in ("traceable", "trace"):
        from .decorators_v3 import traceable
        return traceable

    # Enhanced decorator utilities
    if name == "create_traceable":
        from .decorators_v3 import create_traceable
        return create_traceable

    if name == "set_global_mask_fn":
        from .decorators_v3 import set_global_mask_fn
        return set_global_mask_fn

    if name == "set_debug_mode":
        from .decorators_v3 import set_debug_mode
        return set_debug_mode

    # Context propagation
    if name == "tracing_context":
        from .context_manager import tracing_context
        return tracing_context

    if name == "get_current_trace_context":
        from .context_manager import get_current_trace_context
        return get_current_trace_context

    if name == "get_current_span_context":
        from .context_manager import get_current_span_context
        return get_current_span_context

    if name == "is_tracing_enabled":
        from .context_manager import is_tracing_enabled
        return is_tracing_enabled

    if name == "set_tracing_enabled":
        from .context_manager import set_tracing_enabled
        return set_tracing_enabled

    # Wrappers
    if name == "wrap_openai":
        from .wrappers import wrap_openai
        return wrap_openai

    if name == "wrap_anthropic":
        from .wrappers import wrap_anthropic
        return wrap_anthropic

    if name == "wrap_gemini":
        from .wrappers import wrap_gemini
        return wrap_gemini

    if name == "wrap_bedrock":
        from .wrappers_bedrock import wrap_bedrock
        return wrap_bedrock

    if name == "create_traced_bedrock":
        from .wrappers_bedrock import create_traced_bedrock
        return create_traced_bedrock

    if name == "wrap_cohere":
        from .wrappers_cohere import wrap_cohere
        return wrap_cohere

    if name == "create_traced_cohere":
        from .wrappers_cohere import create_traced_cohere
        return create_traced_cohere

    # Compression
    if name == "Compressor":
        from .compression import Compressor
        return Compressor

    if name == "is_compression_available":
        from .compression import is_compression_available
        return is_compression_available

    # Buffer
    if name == "EventBuffer":
        from .buffer import EventBuffer
        return EventBuffer

    # Feedback Collection
    if name == "FeedbackCollector":
        from .feedback import FeedbackCollector
        return FeedbackCollector

    # W3C Trace Context
    if name == "W3CTraceContext":
        from .context import TraceContext as W3CTraceContext
        return W3CTraceContext

    if name == "extract_trace_context":
        from .context import extract_trace_context
        return extract_trace_context

    if name == "inject_trace_context":
        from .context import inject_trace_context
        return inject_trace_context

    # Prompts
    if name == "Prompt":
        from .prompts import Prompt
        return Prompt

    if name == "PromptManager":
        from .prompts import PromptManager
        return PromptManager

    if name == "PromptFormat":
        from .prompts import PromptFormat
        return PromptFormat

    if name == "TextPrompt":
        from .prompts import TextPrompt
        return TextPrompt

    if name == "ChatPrompt":
        from .prompts import ChatPrompt
        return ChatPrompt

    if name == "get_prompt_manager":
        from .prompts import get_prompt_manager
        return get_prompt_manager

    if name == "register_prompt":
        from .prompts import register_prompt
        return register_prompt

    if name == "get_prompt":
        from .prompts import get_prompt
        return get_prompt

    # Evaluation
    if name == "EvaluationHook":
        from .evaluation import EvaluationHook
        return EvaluationHook

    if name == "Evaluator":
        from .evaluation import Evaluator
        return Evaluator

    if name == "EvaluationResult":
        from .evaluation import EvaluationResult
        return EvaluationResult

    if name == "ScoreType":
        from .evaluation import ScoreType
        return ScoreType

    if name == "Score":
        from .evaluation import Score
        return Score

    if name == "ScoreDataType":
        from .evaluation import ScoreDataType
        return ScoreDataType

    if name == "ScoreManager":
        from .evaluation import ScoreManager
        return ScoreManager

    if name == "get_score_manager":
        from .evaluation import get_score_manager
        return get_score_manager

    if name == "score":
        from .evaluation import score
        return score

    if name == "feedback":
        from .evaluation import feedback
        return feedback

    # Metrics (new!)
    if name == "BaseMetric":
        from .metrics.base import BaseMetric
        return BaseMetric

    if name == "DriftDetectionMetric":
        from .metrics.drift import DriftDetectionMetric
        return DriftDetectionMetric

    if name == "RecoverySuccessMetric":
        from .metrics.recovery import RecoverySuccessMetric
        return RecoverySuccessMetric

    if name == "CheckpointValidityMetric":
        from .metrics.checkpoint import CheckpointValidityMetric
        return CheckpointValidityMetric

    if name == "NestedAgentHealthMetric":
        from .metrics.nested import NestedAgentHealthMetric
        return NestedAgentHealthMetric

    if name == "ProductionReliabilityMetric":
        from .metrics.reliability import ProductionReliabilityMetric
        return ProductionReliabilityMetric

    # Component-level evaluation (new!)
    if name == "observe":
        from .observe import observe
        return observe

    # Streaming
    if name == "StreamingSpan":
        from .streaming import StreamingSpan
        return StreamingSpan

    # Evaluations API (NEW!)
    if name == "EvaluationsClient":
        from .evaluations import EvaluationsClient
        return EvaluationsClient

    if name == "EvaluationType":
        from .evaluations import EvaluationType
        return EvaluationType

    if name == "EvaluationTemplate":
        from .evaluations import EvaluationTemplate
        return EvaluationTemplate

    if name == "EvaluationScore":
        from .evaluations import EvaluationScore
        return EvaluationScore

    if name == "EvaluationJob":
        from .evaluations import EvaluationJob
        return EvaluationJob

    if name == "EvaluationRequest":
        from .evaluations import EvaluationRequest
        return EvaluationRequest

    if name == "evaluate":
        from .evaluations import evaluate
        return evaluate

    # Judges API (NEW!)
    if name == "JudgesClient":
        from .judges import JudgesClient
        return JudgesClient

    if name == "JudgeType":
        from .judges import JudgeType
        return JudgeType

    if name == "Judge":
        from .judges import Judge
        return Judge

    if name == "JudgeResult":
        from .judges import JudgeResult
        return JudgeResult

    if name == "JudgeConfig":
        from .judges import JudgeConfig
        return JudgeConfig

    if name == "judge":
        from .judges import judge
        return judge

    if name == "judge_all":
        from .judges import judge_all
        return judge_all

    # Phase 2: Datasets
    if name == "DatasetsClient":
        from .datasets import DatasetsClient
        return DatasetsClient

    if name == "Dataset":
        from .datasets import Dataset
        return Dataset

    if name == "DatasetExample":
        from .datasets import DatasetExample
        return DatasetExample

    if name == "DatasetRunResult":
        from .datasets import DatasetRunResult
        return DatasetRunResult

    if name == "DatasetRunSummary":
        from .datasets import DatasetRunSummary
        return DatasetRunSummary

    # Phase 2: Sessions
    if name == "SessionManager":
        from .sessions import SessionManager
        return SessionManager

    if name == "SessionAnalytics":
        from .sessions import SessionAnalytics
        return SessionAnalytics

    if name == "Session":
        from .sessions import Session
        return Session

    if name == "SessionMessage":
        from .sessions import SessionMessage
        return SessionMessage

    if name == "create_session_manager":
        from .sessions import create_session_manager
        return create_session_manager

    # Phase 3: LangGraph
    if name == "LangGraphHandler":
        from .langgraph import LangGraphHandler
        return LangGraphHandler

    if name == "wrap_langgraph":
        from .langgraph import wrap_langgraph
        return wrap_langgraph

    if name == "trace_langgraph_node":
        from .langgraph import trace_langgraph_node
        return trace_langgraph_node

    if name == "trace_langgraph_edge":
        from .langgraph import trace_langgraph_edge
        return trace_langgraph_edge

    if name == "create_langgraph_handler":
        from .langgraph import create_langgraph_handler
        return create_langgraph_handler

    # Enhanced batch evaluation
    if name == "enhanced_batch_evaluate":
        from .batch_evaluation import enhanced_batch_evaluate
        return enhanced_batch_evaluate

    if name == "generate_batch_report":
        from .batch_evaluation import generate_batch_report
        return generate_batch_report

    if name == "export_batch_results":
        from .batch_evaluation import export_batch_results
        return export_batch_results

    if name == "export_batch_results_to_csv":
        from .batch_evaluation import export_batch_results_to_csv
        return export_batch_results_to_csv

    if name == "BatchProgress":
        from .batch_evaluation import BatchProgress
        return BatchProgress

    if name == "TestCaseResult":
        from .batch_evaluation import TestCaseResult
        return TestCaseResult

    if name == "BatchStatistics":
        from .batch_evaluation import BatchStatistics
        return BatchStatistics

    if name == "BatchEvaluationResult":
        from .batch_evaluation import BatchEvaluationResult
        return BatchEvaluationResult

    # Experiments API
    if name == "ExperimentsClient":
        from .experiments import ExperimentsClient
        return ExperimentsClient

    if name == "create_experiments_client":
        from .experiments import create_experiments_client
        return create_experiments_client

    if name == "generate_experiment_report":
        from .experiments import generate_experiment_report
        return generate_experiment_report

    if name == "ExperimentVariant":
        from .experiments import ExperimentVariant
        return ExperimentVariant

    if name == "VariantResult":
        from .experiments import VariantResult
        return VariantResult

    if name == "VariantStatistics":
        from .experiments import VariantStatistics
        return VariantStatistics

    if name == "WinnerInfo":
        from .experiments import WinnerInfo
        return WinnerInfo

    if name == "ExperimentResult":
        from .experiments import ExperimentResult
        return ExperimentResult

    # Optional: LangChain callback handler
    if name == "AigieCallbackHandler":
        try:
            from .callback import AigieCallbackHandler
            return AigieCallbackHandler
        except ImportError:
            raise ImportError(
                "LangChain callback handler requires langchain-core. "
                "Install with: pip install langchain-core"
            )

    # Optional: Sync client
    if name == "AigieSync":
        try:
            from .sync_client import AigieSync
            return AigieSync
        except ImportError:
            raise ImportError(
                "Sync client not available. Use Aigie (async) instead."
            )

    # Optional: OpenTelemetry
    if name in ("AigieSpanExporter", "setup_opentelemetry"):
        try:
            from .opentelemetry import AigieSpanExporter, setup_opentelemetry
            return AigieSpanExporter if name == "AigieSpanExporter" else setup_opentelemetry
        except ImportError:
            raise ImportError(
                "OpenTelemetry support requires opentelemetry packages. "
                "Install with: pip install opentelemetry-api opentelemetry-sdk"
            )

    # Cost Tracking (Gap Fix)
    if name == "extract_usage_from_response":
        from .cost_tracking import extract_usage_from_response
        return extract_usage_from_response

    if name == "extract_and_calculate_cost":
        from .cost_tracking import extract_and_calculate_cost
        return extract_and_calculate_cost

    if name == "calculate_cost":
        from .cost_tracking import calculate_cost
        return calculate_cost

    if name == "add_model_pricing":
        from .cost_tracking import add_model_pricing
        return add_model_pricing

    if name == "get_supported_models":
        from .cost_tracking import get_supported_models
        return get_supported_models

    if name == "get_model_pricing":
        from .cost_tracking import get_model_pricing
        return get_model_pricing

    if name == "CostAggregator":
        from .cost_tracking import CostAggregator
        return CostAggregator

    if name == "UsageMetadata":
        from .cost_tracking import UsageMetadata
        return UsageMetadata

    if name == "CostBreakdown":
        from .cost_tracking import CostBreakdown
        return CostBreakdown

    # Summary Evaluators (Gap Fix)
    if name == "SummaryEvaluator":
        from .summary_evaluators import SummaryEvaluator
        return SummaryEvaluator

    if name == "AccuracySummaryEvaluator":
        from .summary_evaluators import AccuracySummaryEvaluator
        return AccuracySummaryEvaluator

    if name == "PrecisionSummaryEvaluator":
        from .summary_evaluators import PrecisionSummaryEvaluator
        return PrecisionSummaryEvaluator

    if name == "AverageScoreSummaryEvaluator":
        from .summary_evaluators import AverageScoreSummaryEvaluator
        return AverageScoreSummaryEvaluator

    if name == "PassRateSummaryEvaluator":
        from .summary_evaluators import PassRateSummaryEvaluator
        return PassRateSummaryEvaluator

    if name == "CostSummaryEvaluator":
        from .summary_evaluators import CostSummaryEvaluator
        return CostSummaryEvaluator

    if name == "LatencySummaryEvaluator":
        from .summary_evaluators import LatencySummaryEvaluator
        return LatencySummaryEvaluator

    if name == "run_summary_evaluators":
        from .summary_evaluators import run_summary_evaluators
        return run_summary_evaluators

    if name == "create_standard_summary_evaluators":
        from .summary_evaluators import create_standard_summary_evaluators
        return create_standard_summary_evaluators

    if name == "RunData":
        from .summary_evaluators import RunData
        return RunData

    if name == "SummaryEvaluationResult":
        from .summary_evaluators import SummaryEvaluationResult
        return SummaryEvaluationResult

    if name == "SummaryEvaluatorFunction":
        from .summary_evaluators import SummaryEvaluatorFunction
        return SummaryEvaluatorFunction

    # Safety Metrics (Gap Fix)
    if name == "PIILeakageEvaluator":
        from .safety_metrics import PIILeakageEvaluator
        return PIILeakageEvaluator

    if name == "ToxicityEvaluator":
        from .safety_metrics import ToxicityEvaluator
        return ToxicityEvaluator

    if name == "BiasEvaluator":
        from .safety_metrics import BiasEvaluator
        return BiasEvaluator

    if name == "PromptInjectionEvaluator":
        from .safety_metrics import PromptInjectionEvaluator
        return PromptInjectionEvaluator

    if name == "JailbreakEvaluator":
        from .safety_metrics import JailbreakEvaluator
        return JailbreakEvaluator

    if name == "RedTeamScanner":
        from .safety_metrics import RedTeamScanner
        return RedTeamScanner

    if name == "create_safety_evaluators":
        from .safety_metrics import create_safety_evaluators
        return create_safety_evaluators

    # Pytest Integration (Gap Fix)
    if name == "AigieTestCase":
        from .pytest_plugin import AigieTestCase
        return AigieTestCase

    if name == "aigie_assert":
        from .pytest_plugin import aigie_assert
        return aigie_assert

    if name == "assert_test":
        from .pytest_plugin import assert_test
        return assert_test

    # UUID v7 (Gap Fix)
    if name == "uuidv7":
        from .uuid7 import uuidv7
        return uuidv7

    if name == "extract_timestamp":
        from .uuid7 import extract_timestamp
        return extract_timestamp

    if name == "is_valid_uuidv7":
        from .uuid7 import is_valid_uuidv7
        return is_valid_uuidv7

    if name == "uuidv7_to_datetime":
        from .uuid7 import uuidv7_to_datetime
        return uuidv7_to_datetime

    if name == "compare_uuidv7":
        from .uuid7 import compare_uuidv7
        return compare_uuidv7

    if name == "generate_batch_uuidv7":
        from .uuid7 import generate_batch_uuidv7
        return generate_batch_uuidv7

    if name == "uuidv7_with_timestamp":
        from .uuid7 import uuidv7_with_timestamp
        return uuidv7_with_timestamp

    if name == "get_uuidv7_age":
        from .uuid7 import get_uuidv7_age
        return get_uuidv7_age

    # Sampling System (Gap Fix)
    if name == "Sampler":
        from .sampling import Sampler
        return Sampler

    if name == "SamplingConfig":
        from .sampling import SamplingConfig
        return SamplingConfig

    if name == "AdaptiveConfig":
        from .sampling import AdaptiveConfig
        return AdaptiveConfig

    if name == "create_smart_sampler":
        from .sampling import create_smart_sampler
        return create_smart_sampler

    if name == "create_adaptive_sampler":
        from .sampling import create_adaptive_sampler
        return create_adaptive_sampler

    if name == "create_importance_function":
        from .sampling import create_importance_function
        return create_importance_function

    # Query API (Feature Parity)
    if name == "QueryAPI":
        from .query_api import QueryAPI
        return QueryAPI

    if name == "TraceAPI":
        from .query_api import TraceAPI
        return TraceAPI

    if name == "ObservationsAPI":
        from .query_api import ObservationsAPI
        return ObservationsAPI

    if name == "SessionsAPI":
        from .query_api import SessionsAPI
        return SessionsAPI

    if name == "ScoresAPI":
        from .query_api import ScoresAPI
        return ScoresAPI

    if name == "Trace":
        from .query_api import Trace
        return Trace

    if name == "Observation":
        from .query_api import Observation
        return Observation

    if name == "ObservationType":
        from .query_api import ObservationType
        return ObservationType

    if name == "TraceFilter":
        from .query_api import TraceFilter
        return TraceFilter

    if name == "PaginatedResponse":
        from .query_api import PaginatedResponse
        return PaginatedResponse

    # Human Annotations (Feature Parity)
    if name == "AnnotationsAPI":
        from .annotations import AnnotationsAPI
        return AnnotationsAPI

    if name == "AnnotationQueue":
        from .annotations import AnnotationQueue
        return AnnotationQueue

    if name == "Annotation":
        from .annotations import Annotation
        return Annotation

    if name == "AnnotationType":
        from .annotations import AnnotationType
        return AnnotationType

    if name == "AnnotationTask":
        from .annotations import AnnotationTask
        return AnnotationTask

    # Playground (Feature Parity)
    if name == "Playground":
        from .playground import Playground
        return Playground

    if name == "PromptRegistry":
        from .playground import PromptRegistry
        return PromptRegistry

    if name == "PromptTemplate":
        from .playground import PromptTemplate
        return PromptTemplate

    if name == "PlaygroundRun":
        from .playground import PlaygroundRun
        return PlaygroundRun

    if name == "ComparisonResult":
        from .playground import ComparisonResult
        return ComparisonResult

    if name == "ModelConfig":
        from .playground import ModelConfig
        return ModelConfig

    if name == "ModelProvider":
        from .playground import ModelProvider
        return ModelProvider

    if name == "create_playground":
        from .playground import create_playground
        return create_playground

    # Agent Graph View (Feature Parity)
    if name == "AgentGraph":
        from .graph_view import AgentGraph
        return AgentGraph

    if name == "GraphBuilder":
        from .graph_view import GraphBuilder
        return GraphBuilder

    if name == "GraphNode":
        from .graph_view import GraphNode
        return GraphNode

    if name == "GraphEdge":
        from .graph_view import GraphEdge
        return GraphEdge

    if name == "NodeType":
        from .graph_view import NodeType
        return NodeType

    if name == "EdgeType":
        from .graph_view import EdgeType
        return EdgeType

    if name == "NodeStatus":
        from .graph_view import NodeStatus
        return NodeStatus

    if name == "ExecutionPath":
        from .graph_view import ExecutionPath
        return ExecutionPath

    if name == "GraphMetrics":
        from .graph_view import GraphMetrics
        return GraphMetrics

    if name == "create_graph":
        from .graph_view import create_graph
        return create_graph

    if name == "create_graph_builder":
        from .graph_view import create_graph_builder
        return create_graph_builder

    # Alerting (Feature Parity)
    if name == "AlertManager":
        from .alerting import AlertManager
        return AlertManager

    if name == "AlertRule":
        from .alerting import AlertRule
        return AlertRule

    if name == "AlertEvent":
        from .alerting import AlertEvent
        return AlertEvent

    if name == "AlertCondition":
        from .alerting import AlertCondition
        return AlertCondition

    if name == "AlertSeverity":
        from .alerting import AlertSeverity
        return AlertSeverity

    if name == "AlertStatus":
        from .alerting import AlertStatus
        return AlertStatus

    if name == "MetricType":
        from .alerting import MetricType
        return MetricType

    if name == "ComparisonOperator":
        from .alerting import ComparisonOperator
        return ComparisonOperator

    if name == "AggregationWindow":
        from .alerting import AggregationWindow
        return AggregationWindow

    if name == "NotificationChannel":
        from .alerting import NotificationChannel
        return NotificationChannel

    if name == "SlackChannel":
        from .alerting import SlackChannel
        return SlackChannel

    if name == "EmailChannel":
        from .alerting import EmailChannel
        return EmailChannel

    if name == "WebhookChannel":
        from .alerting import WebhookChannel
        return WebhookChannel

    if name == "PagerDutyChannel":
        from .alerting import PagerDutyChannel
        return PagerDutyChannel

    if name == "create_alert_manager":
        from .alerting import create_alert_manager
        return create_alert_manager

    # Span Replay (Feature Parity)
    if name == "SpanReplay":
        from .span_replay import SpanReplay
        return SpanReplay

    if name == "CapturedSpan":
        from .span_replay import CapturedSpan
        return CapturedSpan

    if name == "ReplayResult":
        from .span_replay import ReplayResult
        return ReplayResult

    if name == "ReplayExperiment":
        from .span_replay import ReplayExperiment
        return ReplayExperiment

    if name == "ReplayStatus":
        from .span_replay import ReplayStatus
        return ReplayStatus

    if name == "create_span_replay":
        from .span_replay import create_span_replay
        return create_span_replay

    # Leaderboards (Feature Parity)
    if name == "LeaderboardManager":
        from .leaderboards import LeaderboardManager
        return LeaderboardManager

    if name == "Leaderboard":
        from .leaderboards import Leaderboard
        return Leaderboard

    if name == "LeaderboardEntry":
        from .leaderboards import LeaderboardEntry
        return LeaderboardEntry

    if name == "ComparisonPair":
        from .leaderboards import ComparisonPair
        return ComparisonPair

    if name == "EloRating":
        from .leaderboards import EloRating
        return EloRating

    if name == "RankingMetric":
        from .leaderboards import RankingMetric
        return RankingMetric

    if name == "AggregationType":
        from .leaderboards import AggregationType
        return AggregationType

    if name == "create_leaderboard_manager":
        from .leaderboards import create_leaderboard_manager
        return create_leaderboard_manager

    if name == "create_model_leaderboard":
        from .leaderboards import create_model_leaderboard
        return create_model_leaderboard

    if name == "create_prompt_leaderboard":
        from .leaderboards import create_prompt_leaderboard
        return create_prompt_leaderboard

    # License Management (Self-Hosted)
    if name == "LicenseValidator":
        from .licensing import LicenseValidator
        return LicenseValidator

    if name == "LicenseInfo":
        from .licensing import LicenseInfo
        return LicenseInfo

    if name == "UsageSummary":
        from .licensing import UsageSummary
        return UsageSummary

    if name == "LicenseError":
        from .licensing import LicenseError
        return LicenseError

    if name == "LicenseExpiredError":
        from .licensing import LicenseExpiredError
        return LicenseExpiredError

    if name == "LicenseRevokedError":
        from .licensing import LicenseRevokedError
        return LicenseRevokedError

    if name == "LicenseLimitExceededError":
        from .licensing import LicenseLimitExceededError
        return LicenseLimitExceededError

    # Telemetry (SDK Feature Tracking)
    if name == "track_feature":
        from .licensing import track_feature
        return track_feature

    if name == "record_error":
        from .licensing import record_error
        return record_error

    if name == "FeatureTracker":
        from .licensing import FeatureTracker
        return FeatureTracker

    if name == "ErrorCollector":
        from .licensing import ErrorCollector
        return ErrorCollector

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# Type checking support
if TYPE_CHECKING:
    from .client import Aigie
    from .config import Config
    from .trace import TraceContext
    from .span import SpanContext
    from .decorators_v3 import traceable, trace, create_traceable, set_global_mask_fn, set_debug_mode
    from .context_manager import (
        tracing_context,
        get_current_trace_context,
        get_current_span_context,
        is_tracing_enabled,
        set_tracing_enabled,
    )
    from .wrappers import wrap_openai, wrap_anthropic, wrap_gemini
    from .wrappers_bedrock import wrap_bedrock, create_traced_bedrock
    from .wrappers_cohere import wrap_cohere, create_traced_cohere
    from .compression import Compressor, is_compression_available
    from .buffer import EventBuffer
    from .context import TraceContext as W3CTraceContext, extract_trace_context, inject_trace_context
    from .prompts import Prompt, PromptManager
    from .evaluation import EvaluationHook, Evaluator, EvaluationResult, ScoreType
    from .metrics.base import BaseMetric
    from .metrics.drift import DriftDetectionMetric
    from .metrics.recovery import RecoverySuccessMetric
    from .metrics.checkpoint import CheckpointValidityMetric
    from .metrics.nested import NestedAgentHealthMetric
    from .metrics.reliability import ProductionReliabilityMetric
    from .observe import observe
    from .streaming import StreamingSpan
    from .evaluations import (
        EvaluationsClient,
        EvaluationType,
        EvaluationTemplate,
        EvaluationScore,
        EvaluationJob,
        EvaluationRequest,
        evaluate,
    )
    from .judges import (
        JudgesClient,
        JudgeType,
        Judge,
        JudgeResult,
        JudgeConfig,
        judge,
        judge_all,
    )
    from .langgraph import (
        LangGraphHandler,
        wrap_langgraph,
        trace_langgraph_node,
        trace_langgraph_edge,
        create_langgraph_handler,
    )
    from .batch_evaluation import (
        enhanced_batch_evaluate,
        generate_batch_report,
        export_batch_results,
        export_batch_results_to_csv,
        BatchProgress,
        TestCaseResult,
        BatchStatistics,
        BatchEvaluationResult,
    )
    from .experiments import (
        ExperimentsClient,
        create_experiments_client,
        generate_experiment_report,
        ExperimentVariant,
        VariantResult,
        VariantStatistics,
        WinnerInfo,
        ExperimentResult,
    )
    from .cost_tracking import (
        extract_usage_from_response,
        extract_and_calculate_cost,
        calculate_cost,
        add_model_pricing,
        get_supported_models,
        get_model_pricing,
        CostAggregator,
        UsageMetadata,
        CostBreakdown,
    )
    from .summary_evaluators import (
        SummaryEvaluator,
        AccuracySummaryEvaluator,
        PrecisionSummaryEvaluator,
        AverageScoreSummaryEvaluator,
        PassRateSummaryEvaluator,
        CostSummaryEvaluator,
        LatencySummaryEvaluator,
        run_summary_evaluators,
        create_standard_summary_evaluators,
        RunData,
        SummaryEvaluationResult,
        SummaryEvaluatorFunction,
    )
    from .safety_metrics import (
        PIILeakageEvaluator,
        ToxicityEvaluator,
        BiasEvaluator,
        PromptInjectionEvaluator,
        JailbreakEvaluator,
        RedTeamScanner,
        create_safety_evaluators,
    )
    from .pytest_plugin import (
        AigieTestCase,
        aigie_assert,
        assert_test,
    )
    from .uuid7 import (
        uuidv7,
        extract_timestamp,
        is_valid_uuidv7,
        uuidv7_to_datetime,
        compare_uuidv7,
        generate_batch_uuidv7,
        uuidv7_with_timestamp,
        get_uuidv7_age,
    )
    from .sampling import (
        Sampler,
        SamplingConfig,
        AdaptiveConfig,
        create_smart_sampler,
        create_adaptive_sampler,
        create_importance_function,
    )
    from .query_api import (
        QueryAPI,
        TraceAPI,
        ObservationsAPI,
        SessionsAPI,
        ScoresAPI,
        Trace,
        Observation,
        ObservationType,
        TraceFilter,
        PaginatedResponse,
    )
    from .annotations import (
        AnnotationsAPI,
        AnnotationQueue,
        Annotation,
        AnnotationType,
        AnnotationTask,
    )
    from .playground import (
        Playground,
        PromptRegistry,
        PromptTemplate,
        PlaygroundRun,
        ComparisonResult,
        ModelConfig,
        ModelProvider,
        create_playground,
    )
    from .graph_view import (
        AgentGraph,
        GraphBuilder,
        GraphNode,
        GraphEdge,
        NodeType,
        EdgeType,
        NodeStatus,
        ExecutionPath,
        GraphMetrics,
        create_graph,
        create_graph_builder,
    )
    from .alerting import (
        AlertManager,
        AlertRule,
        AlertEvent,
        AlertCondition,
        AlertSeverity,
        AlertStatus,
        MetricType,
        ComparisonOperator,
        AggregationWindow,
        NotificationChannel,
        SlackChannel,
        EmailChannel,
        WebhookChannel,
        PagerDutyChannel,
        create_alert_manager,
    )
    from .span_replay import (
        SpanReplay,
        CapturedSpan,
        ReplayResult,
        ReplayExperiment,
        ReplayStatus,
        create_span_replay,
    )
    from .leaderboards import (
        LeaderboardManager,
        Leaderboard,
        LeaderboardEntry,
        ComparisonPair,
        EloRating,
        RankingMetric,
        AggregationType,
        create_leaderboard_manager,
        create_model_leaderboard,
        create_prompt_leaderboard,
    )
    from .licensing import (
        LicenseValidator,
        LicenseInfo,
        UsageSummary,
        LicenseError,
        LicenseExpiredError,
        LicenseRevokedError,
        LicenseLimitExceededError,
    )

