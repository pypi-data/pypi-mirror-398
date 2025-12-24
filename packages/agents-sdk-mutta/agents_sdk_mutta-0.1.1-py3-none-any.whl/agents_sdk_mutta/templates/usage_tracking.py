"""Template for usage tracking module."""


USAGE_TRACKING_TEMPLATE = '''"""
Usage Tracking - Token usage and cost tracking for agent runs.

This module provides hooks and utilities to track token usage and costs
when running agents. Works with Django for database persistence.

Usage:
    # Option 1: Using hooks (automatic tracking per agent)
    hooks = TokenUsageHook(user=request.user, tag="service:agent_name")
    await Runner.run(agent, input=..., hooks=hooks)
    
    # Option 2: Manual tracking (after run completes)
    result = await Runner.run(agent, input=...)
    await persist_token_usage(
        user=request.user,
        tag="service:workflow",
        model_name="gpt-5",
        usage=result.usage,
    )

Tag format: "service_name:subsystem:agent_name"
    e.g., "research:planning:planner_agent"
"""

from agents import Usage, RunHooks, RunContextWrapper, Agent
from typing import Any, Optional, TYPE_CHECKING
if TYPE_CHECKING:  # Only for type hints; avoid importing Django at runtime
    from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)


def calculate_cost(usage: Usage, model: str = "gpt-5") -> float:
    """
    Compute USD cost for a run given an Agents SDK `usage` object and a model key.
    Supported models include gpt-5.2, gpt-5.1, gpt-5, gpt-4.1, o4-mini, o3, o1, etc.

    Assumes standard API token billing. Prices are per 1M tokens.
    """

    PRICING = {
        # GPT-5 family
        "gpt-5.2": {"input": 1.75, "cached_input": 0.175, "output": 14.00},
        "gpt-5.1": {"input": 1.25, "cached_input": 0.125, "output": 10.00},
        "gpt-5": {"input": 1.25, "cached_input": 0.125, "output": 10.00},
        "gpt-5-mini": {"input": 0.25, "cached_input": 0.025, "output": 2.00},
        "gpt-5-nano": {"input": 0.05, "cached_input": 0.005, "output": 0.40},
        "gpt-5.2-chat-latest": {"input": 1.75, "cached_input": 0.175, "output": 14.00},
        "gpt-5.1-chat-latest": {"input": 1.25, "cached_input": 0.125, "output": 10.00},
        "gpt-5-chat-latest": {"input": 1.25, "cached_input": 0.125, "output": 10.00},
        "gpt-5.1-codex-max": {"input": 1.25, "cached_input": 0.125, "output": 10.00},
        "gpt-5.1-codex": {"input": 1.25, "cached_input": 0.125, "output": 10.00},
        "gpt-5.1-codex-mini": {"input": 0.25, "cached_input": 0.025, "output": 2.00},
        "gpt-5-codex": {"input": 1.25, "cached_input": 0.125, "output": 10.00},
        "gpt-5.2-pro": {"input": 21.00, "cached_input": 21.00, "output": 168.00},
        "gpt-5-pro": {"input": 15.00, "cached_input": 15.00, "output": 120.00},
        "gpt-5-search-api": {"input": 1.25, "cached_input": 0.125, "output": 10.00},

        # GPT-4 family
        "gpt-4.1": {"input": 2.00, "cached_input": 0.50, "output": 8.00},
        "gpt-4.1-mini": {"input": 0.40, "cached_input": 0.10, "output": 1.60},
        "gpt-4.1-nano": {"input": 0.10, "cached_input": 0.025, "output": 0.40},
        "gpt-4o": {"input": 2.50, "cached_input": 1.25, "output": 10.00},
        "gpt-4o-2024-05-13": {"input": 5.00, "cached_input": 5.00, "output": 15.00},
        "gpt-4o-mini": {"input": 0.15, "cached_input": 0.075, "output": 0.60},
        "gpt-4o-search-preview": {"input": 2.50, "cached_input": 2.50, "output": 10.00},
        "gpt-4o-mini-search-preview": {"input": 0.15, "cached_input": 0.15, "output": 0.60},

        # Realtime / Audio
        "gpt-realtime": {"input": 4.00, "cached_input": 0.40, "output": 16.00},
        "gpt-realtime-mini": {"input": 0.60, "cached_input": 0.06, "output": 2.40},
        "gpt-4o-realtime-preview": {"input": 5.00, "cached_input": 2.50, "output": 20.00},
        "gpt-4o-mini-realtime-preview": {"input": 0.60, "cached_input": 0.30, "output": 2.40},
        "gpt-audio": {"input": 2.50, "cached_input": 2.50, "output": 10.00},
        "gpt-audio-mini": {"input": 0.60, "cached_input": 0.60, "output": 2.40},
        "gpt-4o-audio-preview": {"input": 2.50, "cached_input": 2.50, "output": 10.00},
        "gpt-4o-mini-audio-preview": {"input": 0.15, "cached_input": 0.15, "output": 0.60},

        # o-series (Reasoning)
        "o1": {"input": 15.00, "cached_input": 7.50, "output": 60.00},
        "o1-pro": {"input": 150.00, "cached_input": 150.00, "output": 600.00},
        "o1-mini": {"input": 1.10, "cached_input": 0.55, "output": 4.40},
        "o3": {"input": 2.00, "cached_input": 0.50, "output": 8.00},
        "o3-pro": {"input": 20.00, "cached_input": 20.00, "output": 80.00},
        "o3-mini": {"input": 1.10, "cached_input": 0.55, "output": 4.40},
        "o3-deep-research": {"input": 10.00, "cached_input": 2.50, "output": 40.00},
        "o4-mini": {"input": 1.10, "cached_input": 0.275, "output": 4.40},
        "o4-mini-deep-research": {"input": 2.00, "cached_input": 0.50, "output": 8.00},

        # Other / Specialized
        "codex-mini-latest": {"input": 1.50, "cached_input": 0.375, "output": 6.00},
        "computer-use-preview": {"input": 3.00, "cached_input": 3.00, "output": 12.00},
        "gpt-image-1.5": {"input": 5.00, "cached_input": 1.25, "output": 10.00},
        "chatgpt-image-latest": {"input": 5.00, "cached_input": 1.25, "output": 10.00},
        "gpt-image-1": {"input": 5.00, "cached_input": 1.25, "output": 40.00},
        "gpt-image-1-mini": {"input": 2.00, "cached_input": 0.20, "output": 8.00},
    }

    if model not in PRICING:
        logger.error(f"Unknown model '{model}'. Supported: {list(PRICING.keys())}")
        logger.error(f"Assuming gpt-5")
        model = "gpt-5"

    rates = PRICING[model]
    input_tokens  = getattr(usage, "input_tokens", 0) or 0
    output_tokens = getattr(usage, "output_tokens", 0) or 0
    cached_tokens = getattr(getattr(usage, "input_tokens_details", None), "cached_tokens", 0) or 0

    # Guard: cached tokens can't exceed input tokens
    cached_tokens = min(cached_tokens, input_tokens)

    input_cost   = (input_tokens - cached_tokens) / 1_000_000 * rates["input"]
    cached_cost  = cached_tokens / 1_000_000 * rates["cached_input"]
    output_cost  = output_tokens / 1_000_000 * rates["output"]

    return input_cost + cached_cost + output_cost


async def persist_token_usage(
    user: Optional[Any] = None,
    tag: Optional[str] = None,
    model_name: str = "gpt-5",
    usage: Optional[Usage] = None,
    requests: int = 0,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cached_input_tokens: int = 0,
    reasoning_tokens: int = 0,
    total_tokens: int = 0,
) -> None:
    """
    Persist token usage and cost to the database without using hooks.

    Can be called with either a Usage object or individual token counts.
    If both are provided, individual token counts take precedence.

    Args:
        user: Optional user associated with the usage
        tag: Optional tag for categorizing usage (e.g., "marketing:generate-brief")
        model_name: Model name used for pricing calculation
        usage: Optional Usage object from Agents SDK
        requests: Number of requests made
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        cached_input_tokens: Number of cached input tokens
        reasoning_tokens: Number of reasoning tokens
        total_tokens: Total tokens (calculated if not provided)
    """
    # Extract values from Usage object if provided
    if usage:
        requests = getattr(usage, "requests", 0) or requests or 0
        input_tokens = getattr(usage, "input_tokens", 0) or input_tokens or 0
        output_tokens = getattr(usage, "output_tokens", 0) or output_tokens or 0
        total_tokens = getattr(usage, "total_tokens", 0) or total_tokens or 0
        cached_input_tokens = getattr(getattr(usage, "input_tokens_details", None), "cached_tokens", 0) or cached_input_tokens or 0
        reasoning_tokens = getattr(getattr(usage, "output_tokens_details", None), "reasoning_tokens", 0) or reasoning_tokens or 0

    # Calculate total tokens if not provided
    if total_tokens == 0:
        total_tokens = input_tokens + output_tokens

    # Create a minimal Usage object for cost calculation
    class MinimalUsage:
        def __init__(self, input_tokens, output_tokens, cached_tokens):
            self.input_tokens = input_tokens
            self.output_tokens = output_tokens
            self.input_tokens_details = type('obj', (object,), {'cached_tokens': cached_tokens})()

    minimal_usage = MinimalUsage(input_tokens, output_tokens, cached_input_tokens)

    # Compute cost
    try:
        cost = calculate_cost(minimal_usage, model=model_name)
    except Exception as e:
        logger.exception("Failed to calculate usage cost")
        cost = 0.0

    # Persist to database
    try:
        # Import lazily to avoid requiring Django at import-time
        from .models import TokenUsageLog  # type: ignore
        from django.contrib.auth.models import User as DjangoUser  # type: ignore
        from asgiref.sync import sync_to_async  # type: ignore

        await sync_to_async(TokenUsageLog.objects.create)(
            user=user if isinstance(user, DjangoUser) else None,
            tag=tag,
            model_name=model_name,
            requests=int(requests),
            input_tokens=int(input_tokens),
            cached_input_tokens=int(min(max(cached_input_tokens, 0), input_tokens)),
            output_tokens=int(output_tokens),
            reasoning_tokens=int(max(reasoning_tokens, 0)),
            total_tokens=int(total_tokens),
            cost_usd=cost,
        )
    except Exception:
        logger.exception("Failed to persist TokenUsageLog")


class TokenUsageHook(RunHooks):
    """Run hook to persist per-run token usage and cost.

    Usage:
        hooks = TokenUsageHook(user=request.user, tag="marketing:generate-brief")
        await Runner.run(starting_agent, input=..., hooks=hooks)

    Tag format: "service:subsystem:agent" (e.g., "blog:pipeline:writer_agent")
    """

    def __init__(self, user: Optional[Any] = None, tag: Optional[str] = None, model_name: Optional[str] = None):
        self.user = user
        self.tag = tag
        self.model_name_override = model_name

    def set_user(self, user: Any):
        self.user = user

    def set_tag(self, tag: str):
        self.tag = tag

    def _extract_model_name(self, agent: Agent[Any]) -> str:
        # Try provided override first
        if self.model_name_override:
            return self.model_name_override
        # Agent.model can be str | Model | None
        try:
            if isinstance(agent.model, str) and agent.model:
                return agent.model
        except Exception:
            pass
        # Fallback to gpt-5
        return "gpt-5"

    async def on_agent_end(self, context: RunContextWrapper, agent: Agent, output: Any) -> None:
        usage: Usage = getattr(context, "usage", None)
        if not usage:
            return

        model_name = self._extract_model_name(agent)

        # Pull fields safely
        requests = getattr(usage, "requests", 0) or 0
        input_tokens = getattr(usage, "input_tokens", 0) or 0
        output_tokens = getattr(usage, "output_tokens", 0) or 0
        total_tokens = getattr(usage, "total_tokens", 0) or 0
        cached_input = getattr(getattr(usage, "input_tokens_details", None), "cached_tokens", 0) or 0
        reasoning_tokens = getattr(getattr(usage, "output_tokens_details", None), "reasoning_tokens", 0) or 0

        # Compute cost
        try:
            cost = calculate_cost(usage, model=model_name)
        except Exception as e:
            logging.getLogger(__name__).exception("Failed to calculate usage cost")
            cost = 0.0

        # Persist
        try:
            # Import lazily to avoid requiring Django at import-time of this module
            from .models import TokenUsageLog  # type: ignore
            from django.contrib.auth.models import User as DjangoUser  # type: ignore
            from asgiref.sync import sync_to_async  # type: ignore

            await sync_to_async(TokenUsageLog.objects.create)(
                user=self.user if isinstance(self.user, DjangoUser) else None,
                tag=self.tag,
                model_name=model_name,
                requests=int(requests),
                input_tokens=int(input_tokens),
                cached_input_tokens=int(min(max(cached_input, 0), input_tokens)),
                output_tokens=int(output_tokens),
                reasoning_tokens=int(max(reasoning_tokens, 0)),
                total_tokens=int(total_tokens),
                cost_usd=cost,
            )
        except Exception:
            logging.getLogger(__name__).exception("Failed to persist TokenUsageLog")
'''


