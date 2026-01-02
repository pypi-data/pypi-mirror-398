"""
Cost tracking plugin for Claude Agent Framework.

Tracks token usage and estimates costs across agent executions,
with configurable pricing models and budget warnings.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from claude_agent_framework.plugins.base import BasePlugin, PluginContext

if TYPE_CHECKING:
    pass


class CostTrackerPlugin(BasePlugin):
    """
    Plugin to track and estimate costs of Claude API usage.

    Monitors token usage across all agents and provides:
    - Real-time cost estimation
    - Budget warnings
    - Per-agent cost breakdown
    - Configurable pricing models
    """

    name = "cost_tracker"
    version = "1.0.0"
    description = "Track token usage and estimate API costs"

    def __init__(
        self,
        input_price_per_mtok: float = 3.0,
        output_price_per_mtok: float = 15.0,
        budget_limit_usd: float | None = None,
        warn_at_percent: float = 0.8,
    ) -> None:
        """
        Initialize cost tracker plugin.

        Args:
            input_price_per_mtok: Price per million input tokens (default: $3 for Sonnet)
            output_price_per_mtok: Price per million output tokens (default: $15 for Sonnet)
            budget_limit_usd: Optional budget limit in USD
            warn_at_percent: Warn when cost reaches this percentage of budget (default: 0.8)
        """
        self.input_price_per_mtok = input_price_per_mtok
        self.output_price_per_mtok = output_price_per_mtok
        self.budget_limit_usd = budget_limit_usd
        self.warn_at_percent = warn_at_percent

        # Tracking state
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._agent_costs: dict[str, dict[str, Any]] = {}
        self._budget_warning_shown = False

    @property
    def total_cost_usd(self) -> float:
        """Calculate total cost in USD."""
        input_cost = (self._total_input_tokens / 1_000_000) * self.input_price_per_mtok
        output_cost = (self._total_output_tokens / 1_000_000) * self.output_price_per_mtok
        return input_cost + output_cost

    @property
    def budget_remaining_usd(self) -> float | None:
        """Calculate remaining budget in USD."""
        if self.budget_limit_usd is None:
            return None
        return self.budget_limit_usd - self.total_cost_usd

    @property
    def budget_usage_percent(self) -> float | None:
        """Calculate budget usage percentage."""
        if self.budget_limit_usd is None:
            return None
        return (self.total_cost_usd / self.budget_limit_usd) * 100

    async def on_session_start(self, context: PluginContext) -> None:
        """Initialize cost tracking for session."""
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._agent_costs = {}
        self._budget_warning_shown = False

        context.shared_state["cost_tracker_initialized"] = True

    async def on_session_end(self, context: PluginContext) -> None:
        """Log final cost summary."""
        summary = self.get_cost_summary()
        context.shared_state["cost_summary"] = summary

    async def on_agent_spawn(
        self, agent_type: str, agent_prompt: str, context: PluginContext
    ) -> str:
        """Initialize cost tracking for agent."""
        if agent_type not in self._agent_costs:
            self._agent_costs[agent_type] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "call_count": 0,
            }
        self._agent_costs[agent_type]["call_count"] += 1
        return agent_prompt

    async def on_agent_complete(self, agent_type: str, result: Any, context: PluginContext) -> Any:
        """Update cost tracking after agent completion."""
        # In a real implementation, would extract token usage from result
        # For now, this is a placeholder for the integration point
        return result

    def record_tokens(
        self, input_tokens: int, output_tokens: int, agent_type: str | None = None
    ) -> None:
        """
        Record token usage.

        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used
            agent_type: Optional agent type for per-agent tracking
        """
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens

        if agent_type and agent_type in self._agent_costs:
            self._agent_costs[agent_type]["input_tokens"] += input_tokens
            self._agent_costs[agent_type]["output_tokens"] += output_tokens

        # Check budget warning
        self._check_budget_warning()

    def _check_budget_warning(self) -> None:
        """Check if budget warning should be issued."""
        if self.budget_limit_usd is None or self._budget_warning_shown:
            return

        usage_percent = self.budget_usage_percent
        if usage_percent is not None and usage_percent >= self.warn_at_percent * 100:
            self._budget_warning_shown = True
            # In a real implementation, would log or raise a warning
            # For now, this is a placeholder

    def get_cost_summary(self) -> dict[str, Any]:
        """
        Get comprehensive cost summary.

        Returns:
            Dictionary with cost breakdown and statistics
        """
        agent_costs = {}
        for agent_type, data in self._agent_costs.items():
            input_cost = (data["input_tokens"] / 1_000_000) * self.input_price_per_mtok
            output_cost = (data["output_tokens"] / 1_000_000) * self.output_price_per_mtok
            agent_costs[agent_type] = {
                "input_tokens": data["input_tokens"],
                "output_tokens": data["output_tokens"],
                "total_tokens": data["input_tokens"] + data["output_tokens"],
                "call_count": data["call_count"],
                "cost_usd": input_cost + output_cost,
            }

        return {
            "total_cost_usd": self.total_cost_usd,
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "total_tokens": self._total_input_tokens + self._total_output_tokens,
            "budget_limit_usd": self.budget_limit_usd,
            "budget_remaining_usd": self.budget_remaining_usd,
            "budget_usage_percent": self.budget_usage_percent,
            "pricing": {
                "input_price_per_mtok": self.input_price_per_mtok,
                "output_price_per_mtok": self.output_price_per_mtok,
            },
            "agent_costs": agent_costs,
        }

    def reset(self) -> None:
        """Reset all cost tracking."""
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._agent_costs = {}
        self._budget_warning_shown = False
