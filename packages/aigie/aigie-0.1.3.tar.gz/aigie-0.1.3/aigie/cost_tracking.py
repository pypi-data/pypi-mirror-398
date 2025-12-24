"""
Automatic cost tracking for LLM API calls

Supports major providers: OpenAI, Anthropic, Google, Cohere, AWS Bedrock
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional


@dataclass
class UsageMetadata:
    """Usage metadata extracted from LLM responses"""

    input_tokens: int
    output_tokens: int
    total_tokens: int
    model: Optional[str] = None
    provider: Optional[str] = None


@dataclass
class CostBreakdown:
    """Cost breakdown for an LLM call"""

    input_cost: Decimal
    output_cost: Decimal
    total_cost: Decimal
    currency: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass
class ModelPricing:
    """Pricing information per model"""

    input_cost_per_1m: Decimal  # Cost per 1M input tokens
    output_cost_per_1m: Decimal  # Cost per 1M output tokens
    provider: str


# Comprehensive pricing table (updated as of January 2025)
MODEL_PRICING: Dict[str, ModelPricing] = {
    # OpenAI GPT-4 Family
    "gpt-4": ModelPricing(Decimal("30"), Decimal("60"), "openai"),
    "gpt-4-turbo": ModelPricing(Decimal("10"), Decimal("30"), "openai"),
    "gpt-4-turbo-preview": ModelPricing(Decimal("10"), Decimal("30"), "openai"),
    "gpt-4-0125-preview": ModelPricing(Decimal("10"), Decimal("30"), "openai"),
    "gpt-4-1106-preview": ModelPricing(Decimal("10"), Decimal("30"), "openai"),
    "gpt-4o": ModelPricing(Decimal("5"), Decimal("15"), "openai"),
    "gpt-4o-mini": ModelPricing(Decimal("0.15"), Decimal("0.6"), "openai"),
    "gpt-4o-2024-11-20": ModelPricing(Decimal("2.5"), Decimal("10"), "openai"),
    # OpenAI GPT-3.5 Family
    "gpt-3.5-turbo": ModelPricing(Decimal("0.5"), Decimal("1.5"), "openai"),
    "gpt-3.5-turbo-0125": ModelPricing(Decimal("0.5"), Decimal("1.5"), "openai"),
    "gpt-3.5-turbo-1106": ModelPricing(Decimal("1"), Decimal("2"), "openai"),
    # OpenAI O1 Family (Reasoning)
    "o1": ModelPricing(Decimal("15"), Decimal("60"), "openai"),
    "o1-preview": ModelPricing(Decimal("15"), Decimal("60"), "openai"),
    "o1-mini": ModelPricing(Decimal("3"), Decimal("12"), "openai"),
    # Anthropic Claude 3.5
    "claude-3-5-sonnet-20241022": ModelPricing(Decimal("3"), Decimal("15"), "anthropic"),
    "claude-3-5-sonnet-20240620": ModelPricing(Decimal("3"), Decimal("15"), "anthropic"),
    "claude-3-5-haiku-20241022": ModelPricing(Decimal("1"), Decimal("5"), "anthropic"),
    # Anthropic Claude 3
    "claude-3-opus-20240229": ModelPricing(Decimal("15"), Decimal("75"), "anthropic"),
    "claude-3-sonnet-20240229": ModelPricing(Decimal("3"), Decimal("15"), "anthropic"),
    "claude-3-haiku-20240307": ModelPricing(Decimal("0.25"), Decimal("1.25"), "anthropic"),
    # Google Gemini 2.5 (latest)
    "gemini-2.5-flash": ModelPricing(Decimal("0.15"), Decimal("0.6"), "google"),
    "gemini-2.5-flash-preview": ModelPricing(Decimal("0.15"), Decimal("0.6"), "google"),
    "gemini-2.5-pro": ModelPricing(Decimal("1.25"), Decimal("5"), "google"),
    "gemini-2.5-pro-preview": ModelPricing(Decimal("1.25"), Decimal("5"), "google"),
    # Google Gemini 2.0
    "gemini-2.0-flash": ModelPricing(Decimal("0"), Decimal("0"), "google"),
    "gemini-2.0-flash-exp": ModelPricing(Decimal("0"), Decimal("0"), "google"),
    # Google Gemini 1.5
    "gemini-1.5-pro": ModelPricing(Decimal("1.25"), Decimal("5"), "google"),
    "gemini-1.5-flash": ModelPricing(Decimal("0.075"), Decimal("0.3"), "google"),
    "gemini-1.5-flash-8b": ModelPricing(Decimal("0.0375"), Decimal("0.15"), "google"),
    # Cohere
    "command-r": ModelPricing(Decimal("0.15"), Decimal("0.6"), "cohere"),
    "command-r-plus": ModelPricing(Decimal("2.5"), Decimal("10"), "cohere"),
    "command-light": ModelPricing(Decimal("0.3"), Decimal("0.6"), "cohere"),
    "command": ModelPricing(Decimal("1"), Decimal("2"), "cohere"),
    # Mistral
    "mistral-large-latest": ModelPricing(Decimal("2"), Decimal("6"), "mistral"),
    "mistral-medium-latest": ModelPricing(Decimal("2.7"), Decimal("8.1"), "mistral"),
    "mistral-small-latest": ModelPricing(Decimal("0.2"), Decimal("0.6"), "mistral"),
    "open-mistral-7b": ModelPricing(Decimal("0.25"), Decimal("0.25"), "mistral"),
    "open-mixtral-8x7b": ModelPricing(Decimal("0.7"), Decimal("0.7"), "mistral"),
    # AWS Bedrock - Anthropic
    "anthropic.claude-v2": ModelPricing(Decimal("8"), Decimal("24"), "bedrock"),
    "anthropic.claude-v2:1": ModelPricing(Decimal("8"), Decimal("24"), "bedrock"),
    "anthropic.claude-3-sonnet-20240229-v1:0": ModelPricing(
        Decimal("3"), Decimal("15"), "bedrock"
    ),
    "anthropic.claude-3-haiku-20240307-v1:0": ModelPricing(
        Decimal("0.25"), Decimal("1.25"), "bedrock"
    ),
    "anthropic.claude-3-opus-20240229-v1:0": ModelPricing(
        Decimal("15"), Decimal("75"), "bedrock"
    ),
    # AWS Bedrock - Titan
    "amazon.titan-text-express-v1": ModelPricing(Decimal("0.2"), Decimal("0.6"), "bedrock"),
    "amazon.titan-text-lite-v1": ModelPricing(Decimal("0.15"), Decimal("0.2"), "bedrock"),
    # AWS Bedrock - Meta Llama
    "meta.llama3-70b-instruct-v1:0": ModelPricing(Decimal("0.99"), Decimal("0.99"), "bedrock"),
    "meta.llama3-8b-instruct-v1:0": ModelPricing(Decimal("0.3"), Decimal("0.6"), "bedrock"),
}


def extract_usage_from_response(
    response: Any, provider: Optional[str] = None
) -> Optional[UsageMetadata]:
    """
    Extract usage metadata from various provider response formats

    Args:
        response: LLM API response
        provider: Optional provider name

    Returns:
        UsageMetadata or None if extraction fails

    Example:
        >>> response = openai.chat.completions.create(...)
        >>> usage = extract_usage_from_response(response, 'openai')
        >>> print(f"Tokens used: {usage.total_tokens}")
    """
    try:
        # OpenAI format
        if hasattr(response, "usage") and response.usage:
            return UsageMetadata(
                input_tokens=getattr(response.usage, "prompt_tokens", 0),
                output_tokens=getattr(response.usage, "completion_tokens", 0),
                total_tokens=getattr(response.usage, "total_tokens", 0),
                model=getattr(response, "model", None),
                provider=provider or "openai",
            )

        # Anthropic format
        if hasattr(response, "usage") and hasattr(response.usage, "input_tokens"):
            return UsageMetadata(
                input_tokens=getattr(response.usage, "input_tokens", 0),
                output_tokens=getattr(response.usage, "output_tokens", 0),
                total_tokens=(
                    getattr(response.usage, "input_tokens", 0)
                    + getattr(response.usage, "output_tokens", 0)
                ),
                model=getattr(response, "model", None),
                provider=provider or "anthropic",
            )

        # Dictionary format (for API responses as dicts)
        if isinstance(response, dict):
            # OpenAI dict format
            if "usage" in response:
                usage = response["usage"]
                return UsageMetadata(
                    input_tokens=usage.get("prompt_tokens", 0),
                    output_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0),
                    model=response.get("model"),
                    provider=provider or "openai",
                )

            # Google Gemini format
            if "usageMetadata" in response:
                metadata = response["usageMetadata"]
                return UsageMetadata(
                    input_tokens=metadata.get("promptTokenCount", 0),
                    output_tokens=metadata.get("candidatesTokenCount", 0),
                    total_tokens=metadata.get("totalTokenCount", 0),
                    model=response.get("modelVersion"),
                    provider=provider or "google",
                )

            # Cohere format
            if "meta" in response and "billed_units" in response["meta"]:
                units = response["meta"]["billed_units"]
                return UsageMetadata(
                    input_tokens=units.get("input_tokens", 0),
                    output_tokens=units.get("output_tokens", 0),
                    total_tokens=units.get("input_tokens", 0) + units.get("output_tokens", 0),
                    model=response.get("model"),
                    provider=provider or "cohere",
                )

            # AWS Bedrock format
            if "amazon-bedrock-invocationMetrics" in response:
                metrics = response["amazon-bedrock-invocationMetrics"]
                return UsageMetadata(
                    input_tokens=metrics.get("inputTokenCount", 0),
                    output_tokens=metrics.get("outputTokenCount", 0),
                    total_tokens=(
                        metrics.get("inputTokenCount", 0) + metrics.get("outputTokenCount", 0)
                    ),
                    provider=provider or "bedrock",
                )

        return None

    except Exception as e:
        print(f"Warning: Failed to extract usage metadata: {e}")
        return None


def normalize_model_name(model: str) -> str:
    """
    Normalize model name for pricing lookup

    Args:
        model: Raw model name from API

    Returns:
        Normalized model name
    """
    import re

    # Remove common prefixes (e.g., Google's "models/" prefix)
    normalized = model
    if normalized.startswith("models/"):
        normalized = normalized[7:]  # Remove "models/" prefix

    # Remove common suffixes
    normalized = re.sub(r"-\d{8}$", "", normalized)  # Date suffixes
    normalized = re.sub(r"-v\d+:\d+$", "", normalized)  # Bedrock version suffixes
    normalized = normalized.lower()

    # Handle specific cases - OpenAI
    if "gpt-4o-mini" in normalized:
        return "gpt-4o-mini"
    if "gpt-4o" in normalized:
        return "gpt-4o"
    if "gpt-4-turbo" in normalized:
        return "gpt-4-turbo"
    if "gpt-4" in normalized:
        return "gpt-4"
    if "gpt-3.5-turbo" in normalized:
        return "gpt-3.5-turbo"

    # Handle specific cases - Google Gemini (after removing models/ prefix)
    if "gemini-2.5-flash" in normalized:
        return "gemini-2.5-flash"
    if "gemini-2.5-pro" in normalized:
        return "gemini-2.5-pro"
    if "gemini-1.5-flash" in normalized:
        return "gemini-1.5-flash"
    if "gemini-1.5-pro" in normalized:
        return "gemini-1.5-pro"
    if "gemini-pro" in normalized:
        return "gemini-pro"

    return normalized


def calculate_cost(
    usage: UsageMetadata, model_override: Optional[str] = None
) -> Optional[CostBreakdown]:
    """
    Calculate cost from usage metadata

    Args:
        usage: Usage metadata
        model_override: Optional model name override

    Returns:
        CostBreakdown or None if pricing not found

    Example:
        >>> usage = UsageMetadata(input_tokens=100, output_tokens=50, total_tokens=150, model="gpt-4")
        >>> cost = calculate_cost(usage)
        >>> print(f"Total cost: ${cost.total_cost}")
    """
    model = model_override or usage.model
    if not model:
        print("Warning: No model specified for cost calculation")
        return None

    # Normalize model name
    normalized_model = normalize_model_name(model)
    pricing = MODEL_PRICING.get(normalized_model)

    if not pricing:
        print(f"Warning: No pricing information for model: {model}")
        return None

    # Calculate costs (prices are per 1M tokens)
    input_cost = (Decimal(usage.input_tokens) / Decimal("1000000")) * pricing.input_cost_per_1m
    output_cost = (
        Decimal(usage.output_tokens) / Decimal("1000000")
    ) * pricing.output_cost_per_1m
    total_cost = input_cost + output_cost

    return CostBreakdown(
        input_cost=input_cost,
        output_cost=output_cost,
        total_cost=total_cost,
        currency="USD",
        model=normalized_model,
        provider=pricing.provider,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        total_tokens=usage.total_tokens,
    )


def extract_and_calculate_cost(
    response: Any, provider: Optional[str] = None, model_override: Optional[str] = None
) -> Optional[CostBreakdown]:
    """
    Extract and calculate cost from LLM response

    Args:
        response: LLM API response
        provider: Optional provider name
        model_override: Optional model name override

    Returns:
        CostBreakdown or None

    Example:
        >>> response = openai.chat.completions.create(...)
        >>> cost = extract_and_calculate_cost(response, 'openai')
        >>> print(f"Cost: ${cost.total_cost}")
    """
    usage = extract_usage_from_response(response, provider)
    if not usage:
        return None

    return calculate_cost(usage, model_override)


def add_model_pricing(model: str, input_cost_per_1m: float, output_cost_per_1m: float, provider: str) -> None:
    """
    Add model pricing (for custom models or updates)

    Args:
        model: Model name
        input_cost_per_1m: Input cost per 1M tokens (USD)
        output_cost_per_1m: Output cost per 1M tokens (USD)
        provider: Provider name

    Example:
        >>> add_model_pricing('custom-model-v1', 5.0, 10.0, 'custom')
    """
    MODEL_PRICING[model] = ModelPricing(
        Decimal(str(input_cost_per_1m)), Decimal(str(output_cost_per_1m)), provider
    )


def get_supported_models() -> List[str]:
    """Get all supported models"""
    return list(MODEL_PRICING.keys())


def get_model_pricing(model: str) -> Optional[ModelPricing]:
    """
    Get pricing for a specific model

    Args:
        model: Model name

    Returns:
        ModelPricing or None
    """
    normalized = normalize_model_name(model)
    return MODEL_PRICING.get(normalized)


class CostAggregator:
    """
    Cost aggregator for multiple LLM calls

    Example:
        >>> aggregator = CostAggregator()
        >>> aggregator.add_usage(usage1)
        >>> aggregator.add_usage(usage2)
        >>> summary = aggregator.get_summary()
        >>> print(f"Total cost: ${summary['total_cost']}")
    """

    def __init__(self):
        self.costs: List[CostBreakdown] = []

    def add(self, cost: CostBreakdown) -> None:
        """Add a cost breakdown to the aggregator"""
        self.costs.append(cost)

    def add_usage(self, usage: UsageMetadata, model_override: Optional[str] = None) -> None:
        """Add usage and calculate cost"""
        cost = calculate_cost(usage, model_override)
        if cost:
            self.costs.append(cost)

    def get_total(self) -> Decimal:
        """Get total cost across all calls"""
        return sum((cost.total_cost for cost in self.costs), Decimal("0"))

    def get_total_input_cost(self) -> Decimal:
        """Get total input cost"""
        return sum((cost.input_cost for cost in self.costs), Decimal("0"))

    def get_total_output_cost(self) -> Decimal:
        """Get total output cost"""
        return sum((cost.output_cost for cost in self.costs), Decimal("0"))

    def get_total_tokens(self) -> int:
        """Get total tokens used"""
        return sum(cost.total_tokens for cost in self.costs)

    def get_by_model(self) -> Dict[str, Dict[str, Any]]:
        """Get breakdown by model"""
        breakdown: Dict[str, Dict[str, Any]] = {}

        for cost in self.costs:
            if cost.model not in breakdown:
                breakdown[cost.model] = {"cost": Decimal("0"), "calls": 0, "tokens": 0}

            breakdown[cost.model]["cost"] += cost.total_cost
            breakdown[cost.model]["calls"] += 1
            breakdown[cost.model]["tokens"] += cost.total_tokens

        return breakdown

    def get_by_provider(self) -> Dict[str, Dict[str, Any]]:
        """Get breakdown by provider"""
        breakdown: Dict[str, Dict[str, Any]] = {}

        for cost in self.costs:
            if cost.provider not in breakdown:
                breakdown[cost.provider] = {"cost": Decimal("0"), "calls": 0, "tokens": 0}

            breakdown[cost.provider]["cost"] += cost.total_cost
            breakdown[cost.provider]["calls"] += 1
            breakdown[cost.provider]["tokens"] += cost.total_tokens

        return breakdown

    def get_costs(self) -> List[CostBreakdown]:
        """Get all cost breakdowns"""
        return self.costs.copy()

    def clear(self) -> None:
        """Clear all costs"""
        self.costs.clear()

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics

        Returns:
            Dictionary with comprehensive cost summary
        """
        total_input_tokens = sum(cost.input_tokens for cost in self.costs)
        total_output_tokens = sum(cost.output_tokens for cost in self.costs)
        total_calls = len(self.costs)

        return {
            "total_cost": float(self.get_total()),
            "total_input_cost": float(self.get_total_input_cost()),
            "total_output_cost": float(self.get_total_output_cost()),
            "total_tokens": self.get_total_tokens(),
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_calls": total_calls,
            "average_cost_per_call": (
                float(self.get_total() / total_calls) if total_calls > 0 else 0
            ),
            "by_model": {
                model: {
                    "cost": float(stats["cost"]),
                    "calls": stats["calls"],
                    "tokens": stats["tokens"],
                }
                for model, stats in self.get_by_model().items()
            },
            "by_provider": {
                provider: {
                    "cost": float(stats["cost"]),
                    "calls": stats["calls"],
                    "tokens": stats["tokens"],
                }
                for provider, stats in self.get_by_provider().items()
            },
        }
