"""
Cost tracking utilities for LangChain integration.

Provides model pricing and token extraction for LangChain LLM calls.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Union
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelPricing:
    """Pricing information for a model."""
    input_cost_per_million: float  # Cost per 1M input tokens
    output_cost_per_million: float  # Cost per 1M output tokens
    provider: str = "unknown"


# LangChain-specific model pricing (commonly used models)
LANGCHAIN_MODEL_PRICING: Dict[str, ModelPricing] = {
    # OpenAI models
    "gpt-4o": ModelPricing(2.50, 10.00, "openai"),
    "gpt-4o-mini": ModelPricing(0.15, 0.60, "openai"),
    "gpt-4-turbo": ModelPricing(10.00, 30.00, "openai"),
    "gpt-4-turbo-preview": ModelPricing(10.00, 30.00, "openai"),
    "gpt-4": ModelPricing(30.00, 60.00, "openai"),
    "gpt-4-32k": ModelPricing(60.00, 120.00, "openai"),
    "gpt-3.5-turbo": ModelPricing(0.50, 1.50, "openai"),
    "gpt-3.5-turbo-16k": ModelPricing(3.00, 4.00, "openai"),
    "o1-preview": ModelPricing(15.00, 60.00, "openai"),
    "o1-mini": ModelPricing(3.00, 12.00, "openai"),

    # Anthropic models
    "claude-3-5-sonnet-20241022": ModelPricing(3.00, 15.00, "anthropic"),
    "claude-3-5-sonnet-latest": ModelPricing(3.00, 15.00, "anthropic"),
    "claude-3-5-haiku-20241022": ModelPricing(0.80, 4.00, "anthropic"),
    "claude-3-opus-20240229": ModelPricing(15.00, 75.00, "anthropic"),
    "claude-3-sonnet-20240229": ModelPricing(3.00, 15.00, "anthropic"),
    "claude-3-haiku-20240307": ModelPricing(0.25, 1.25, "anthropic"),

    # Google models
    "gemini-2.0-flash": ModelPricing(0.10, 0.40, "google"),
    "gemini-1.5-pro": ModelPricing(1.25, 5.00, "google"),
    "gemini-1.5-flash": ModelPricing(0.075, 0.30, "google"),
    "gemini-1.0-pro": ModelPricing(0.50, 1.50, "google"),

    # Cohere models
    "command-r-plus": ModelPricing(3.00, 15.00, "cohere"),
    "command-r": ModelPricing(0.50, 1.50, "cohere"),
    "command": ModelPricing(1.00, 2.00, "cohere"),

    # Mistral models
    "mistral-large-latest": ModelPricing(4.00, 12.00, "mistral"),
    "mistral-medium-latest": ModelPricing(2.70, 8.10, "mistral"),
    "mistral-small-latest": ModelPricing(1.00, 3.00, "mistral"),
    "open-mixtral-8x22b": ModelPricing(2.00, 6.00, "mistral"),
    "open-mixtral-8x7b": ModelPricing(0.70, 0.70, "mistral"),
}


def extract_tokens_from_response(response: Any) -> Dict[str, int]:
    """Extract token usage from various LangChain response formats.

    Args:
        response: The LLM response object

    Returns:
        Dictionary with input_tokens, output_tokens, total_tokens
    """
    input_tokens = 0
    output_tokens = 0

    try:
        # Method 1: LLMResult format (LangChain standard)
        if hasattr(response, "llm_output") and response.llm_output:
            llm_output = response.llm_output
            if isinstance(llm_output, dict):
                token_usage = llm_output.get("token_usage") or llm_output.get("usage")
                if token_usage:
                    input_tokens = token_usage.get("prompt_tokens") or token_usage.get("input_tokens") or 0
                    output_tokens = token_usage.get("completion_tokens") or token_usage.get("output_tokens") or 0

        # Method 2: response_metadata (newer LangChain format)
        if not (input_tokens or output_tokens) and hasattr(response, "response_metadata"):
            metadata = response.response_metadata
            if isinstance(metadata, dict):
                usage = metadata.get("usage") or metadata.get("token_usage")
                if usage:
                    input_tokens = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
                    output_tokens = usage.get("completion_tokens") or usage.get("output_tokens") or 0

        # Method 3: usage_metadata (some providers)
        if not (input_tokens or output_tokens) and hasattr(response, "usage_metadata"):
            usage = response.usage_metadata
            if usage:
                if hasattr(usage, "input_tokens"):
                    input_tokens = usage.input_tokens or 0
                if hasattr(usage, "output_tokens"):
                    output_tokens = usage.output_tokens or 0
                if isinstance(usage, dict):
                    input_tokens = usage.get("input_tokens") or usage.get("prompt_tokens") or 0
                    output_tokens = usage.get("output_tokens") or usage.get("completion_tokens") or 0

        # Method 4: Direct usage attribute (OpenAI style)
        if not (input_tokens or output_tokens) and hasattr(response, "usage"):
            usage = response.usage
            if hasattr(usage, "prompt_tokens"):
                input_tokens = usage.prompt_tokens or 0
                output_tokens = usage.completion_tokens or 0
            elif isinstance(usage, dict):
                input_tokens = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
                output_tokens = usage.get("completion_tokens") or usage.get("output_tokens") or 0

        # Method 5: Generations with usage (LangChain LLMResult)
        if not (input_tokens or output_tokens) and hasattr(response, "generations"):
            for gen_list in response.generations:
                for gen in gen_list if isinstance(gen_list, list) else [gen_list]:
                    if hasattr(gen, "message") and hasattr(gen.message, "usage_metadata"):
                        usage = gen.message.usage_metadata
                        if usage:
                            input_tokens = getattr(usage, "input_tokens", 0) or 0
                            output_tokens = getattr(usage, "output_tokens", 0) or 0
                            if input_tokens or output_tokens:
                                break
                if input_tokens or output_tokens:
                    break

    except Exception as e:
        logger.debug(f"Error extracting tokens from response: {e}")

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }


def get_langchain_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    fallback_to_aigie: bool = True,
) -> Optional[Dict[str, Any]]:
    """Calculate cost for a LangChain LLM call.

    Args:
        model: The model name/identifier
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        fallback_to_aigie: Whether to fallback to main aigie cost tracking

    Returns:
        Dictionary with cost breakdown or None if pricing not found
    """
    # Normalize model name (lowercase, handle variations)
    model_lower = model.lower() if model else ""

    # Try exact match first
    pricing = LANGCHAIN_MODEL_PRICING.get(model)

    # Try lowercase match
    if not pricing:
        pricing = LANGCHAIN_MODEL_PRICING.get(model_lower)

    # Try partial match for model families
    if not pricing:
        for model_key, model_pricing in LANGCHAIN_MODEL_PRICING.items():
            if model_key in model_lower or model_lower in model_key:
                pricing = model_pricing
                break

    # Fallback to main aigie cost tracking
    if not pricing and fallback_to_aigie:
        try:
            from ...cost_tracking import get_model_pricing
            pricing = get_model_pricing(model)
        except ImportError:
            pass

    if not pricing:
        return None

    # Calculate costs
    input_cost = (input_tokens / 1_000_000) * pricing.input_cost_per_million
    output_cost = (output_tokens / 1_000_000) * pricing.output_cost_per_million
    total_cost = input_cost + output_cost

    return {
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "model": model,
        "provider": pricing.provider,
        "input_cost_per_million": pricing.input_cost_per_million,
        "output_cost_per_million": pricing.output_cost_per_million,
    }


def extract_model_from_llm(llm: Any) -> Optional[str]:
    """Extract model name from a LangChain LLM object.

    Args:
        llm: The LangChain LLM object

    Returns:
        Model name or None
    """
    # Common attribute names for model
    model_attrs = [
        "model_name",
        "model",
        "model_id",
        "deployment_name",  # Azure
        "_model",
        "model_kwargs",
    ]

    for attr in model_attrs:
        if hasattr(llm, attr):
            value = getattr(llm, attr)
            if isinstance(value, str) and value:
                return value
            elif isinstance(value, dict) and "model" in value:
                return value["model"]

    # Try class name as fallback
    class_name = type(llm).__name__
    if class_name and "Chat" in class_name:
        # Extract provider from class name (e.g., ChatOpenAI -> openai)
        return class_name.replace("Chat", "").lower()

    return None
