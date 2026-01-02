"""Tests for built-in plugins (cost tracker and retry handler)."""

import pytest

from claude_agent_framework.plugins.base import PluginContext
from claude_agent_framework.plugins.builtin import (
    CostTrackerPlugin,
    ExponentialBackoff,
    FixedDelay,
    RetryHandlerPlugin,
)


class TestCostTrackerPlugin:
    """Tests for CostTrackerPlugin."""

    def test_initialization(self):
        """Test plugin initialization with default pricing."""
        plugin = CostTrackerPlugin()
        assert plugin.name == "cost_tracker"
        assert plugin.input_price_per_mtok == 3.0
        assert plugin.output_price_per_mtok == 15.0
        assert plugin.budget_limit_usd is None

    def test_initialization_with_custom_pricing(self):
        """Test plugin initialization with custom pricing."""
        plugin = CostTrackerPlugin(
            input_price_per_mtok=5.0,
            output_price_per_mtok=10.0,
            budget_limit_usd=100.0,
        )
        assert plugin.input_price_per_mtok == 5.0
        assert plugin.output_price_per_mtok == 10.0
        assert plugin.budget_limit_usd == 100.0

    def test_record_tokens(self):
        """Test recording token usage."""
        plugin = CostTrackerPlugin()
        plugin.record_tokens(1_000_000, 500_000)

        assert plugin._total_input_tokens == 1_000_000
        assert plugin._total_output_tokens == 500_000

    def test_cost_calculation(self):
        """Test cost calculation."""
        plugin = CostTrackerPlugin(input_price_per_mtok=3.0, output_price_per_mtok=15.0)
        plugin.record_tokens(1_000_000, 500_000)

        # 1M * $3/M + 0.5M * $15/M = $3 + $7.5 = $10.5
        assert plugin.total_cost_usd == 10.5

    def test_per_agent_tracking(self):
        """Test per-agent cost tracking."""
        plugin = CostTrackerPlugin()

        # Record tokens for different agents
        plugin._agent_costs["researcher"] = {
            "input_tokens": 0,
            "output_tokens": 0,
            "call_count": 0,
        }
        plugin.record_tokens(1_000_000, 500_000, "researcher")

        summary = plugin.get_cost_summary()
        assert "researcher" in summary["agent_costs"]
        assert summary["agent_costs"]["researcher"]["input_tokens"] == 1_000_000
        assert summary["agent_costs"]["researcher"]["output_tokens"] == 500_000

    def test_budget_remaining(self):
        """Test budget remaining calculation."""
        plugin = CostTrackerPlugin(budget_limit_usd=100.0)
        plugin.record_tokens(1_000_000, 500_000)  # $10.5

        assert plugin.budget_remaining_usd == 89.5
        assert abs(plugin.budget_usage_percent - 10.5) < 0.01

    def test_no_budget_limit(self):
        """Test with no budget limit."""
        plugin = CostTrackerPlugin()
        plugin.record_tokens(1_000_000, 500_000)

        assert plugin.budget_remaining_usd is None
        assert plugin.budget_usage_percent is None

    @pytest.mark.asyncio
    async def test_session_lifecycle(self):
        """Test session lifecycle hooks."""
        plugin = CostTrackerPlugin()
        context = PluginContext(
            session_id="test",
            architecture_name="research",
        )

        # Session start
        await plugin.on_session_start(context)
        assert context.shared_state["cost_tracker_initialized"] is True

        # Record some tokens
        plugin.record_tokens(1_000_000, 500_000)

        # Session end
        await plugin.on_session_end(context)
        assert "cost_summary" in context.shared_state
        assert context.shared_state["cost_summary"]["total_cost_usd"] == 10.5

    @pytest.mark.asyncio
    async def test_agent_lifecycle(self):
        """Test agent lifecycle hooks."""
        plugin = CostTrackerPlugin()
        context = PluginContext(
            session_id="test",
            architecture_name="research",
        )

        # Spawn agent
        prompt = await plugin.on_agent_spawn("researcher", "Test prompt", context)
        assert prompt == "Test prompt"
        assert "researcher" in plugin._agent_costs
        assert plugin._agent_costs["researcher"]["call_count"] == 1

        # Spawn again
        await plugin.on_agent_spawn("researcher", "Test prompt", context)
        assert plugin._agent_costs["researcher"]["call_count"] == 2

    def test_get_cost_summary(self):
        """Test cost summary generation."""
        plugin = CostTrackerPlugin(budget_limit_usd=100.0)
        plugin._agent_costs["researcher"] = {
            "input_tokens": 1_000_000,
            "output_tokens": 500_000,
            "call_count": 2,
        }
        plugin._total_input_tokens = 1_000_000
        plugin._total_output_tokens = 500_000

        summary = plugin.get_cost_summary()

        assert summary["total_cost_usd"] == 10.5
        assert summary["total_input_tokens"] == 1_000_000
        assert summary["total_output_tokens"] == 500_000
        assert summary["budget_limit_usd"] == 100.0
        assert "researcher" in summary["agent_costs"]

    def test_reset(self):
        """Test reset functionality."""
        plugin = CostTrackerPlugin()
        plugin.record_tokens(1_000_000, 500_000)
        plugin._agent_costs["test"] = {"input_tokens": 100, "output_tokens": 50, "call_count": 1}

        plugin.reset()

        assert plugin._total_input_tokens == 0
        assert plugin._total_output_tokens == 0
        assert len(plugin._agent_costs) == 0


class TestRetryStrategy:
    """Tests for retry strategies."""

    def test_exponential_backoff_initialization(self):
        """Test ExponentialBackoff initialization."""
        strategy = ExponentialBackoff(max_retries=5, initial_delay=2.0)
        assert strategy.max_retries == 5
        assert strategy.initial_delay == 2.0

    def test_exponential_backoff_should_retry(self):
        """Test ExponentialBackoff retry decision."""
        strategy = ExponentialBackoff(max_retries=3)
        error = ValueError("test")

        assert strategy.should_retry(0, error) is True
        assert strategy.should_retry(1, error) is True
        assert strategy.should_retry(2, error) is True
        assert strategy.should_retry(3, error) is False

    def test_exponential_backoff_delay(self):
        """Test ExponentialBackoff delay calculation."""
        strategy = ExponentialBackoff(
            initial_delay=1.0,
            multiplier=2.0,
            max_delay=10.0,
        )

        assert strategy.get_delay(0) == 1.0  # 1.0 * 2^0
        assert strategy.get_delay(1) == 2.0  # 1.0 * 2^1
        assert strategy.get_delay(2) == 4.0  # 1.0 * 2^2
        assert strategy.get_delay(3) == 8.0  # 1.0 * 2^3
        assert strategy.get_delay(4) == 10.0  # capped at max_delay

    def test_fixed_delay_initialization(self):
        """Test FixedDelay initialization."""
        strategy = FixedDelay(max_retries=5, delay=2.0)
        assert strategy.max_retries == 5
        assert strategy.delay == 2.0

    def test_fixed_delay_should_retry(self):
        """Test FixedDelay retry decision."""
        strategy = FixedDelay(max_retries=3)
        error = ValueError("test")

        assert strategy.should_retry(0, error) is True
        assert strategy.should_retry(2, error) is True
        assert strategy.should_retry(3, error) is False

    def test_fixed_delay_delay(self):
        """Test FixedDelay returns constant delay."""
        strategy = FixedDelay(delay=5.0)

        assert strategy.get_delay(0) == 5.0
        assert strategy.get_delay(1) == 5.0
        assert strategy.get_delay(10) == 5.0


class TestRetryHandlerPlugin:
    """Tests for RetryHandlerPlugin."""

    def test_initialization(self):
        """Test plugin initialization."""
        plugin = RetryHandlerPlugin()
        assert plugin.name == "retry_handler"
        assert isinstance(plugin.strategy, ExponentialBackoff)
        assert KeyboardInterrupt in plugin.non_retryable_errors

    def test_initialization_with_custom_strategy(self):
        """Test initialization with custom strategy."""
        strategy = FixedDelay(max_retries=5, delay=2.0)
        plugin = RetryHandlerPlugin(strategy=strategy)
        assert plugin.strategy == strategy

    @pytest.mark.asyncio
    async def test_session_lifecycle(self):
        """Test session lifecycle hooks."""
        plugin = RetryHandlerPlugin()
        context = PluginContext(
            session_id="test",
            architecture_name="research",
        )

        await plugin.on_session_start(context)
        assert context.shared_state["retry_handler_initialized"] is True
        assert plugin._total_retries == 0

        # Simulate some retries
        plugin._total_retries = 5
        plugin._total_failures = 2

        await plugin.on_session_end(context)
        assert "retry_stats" in context.shared_state
        assert context.shared_state["retry_stats"]["total_retries"] == 5

    @pytest.mark.asyncio
    async def test_on_error_retry(self):
        """Test error handling with retry."""
        plugin = RetryHandlerPlugin(strategy=FixedDelay(max_retries=3, delay=0.01))
        context = PluginContext(
            session_id="test",
            architecture_name="research",
        )

        error = ValueError("test error")

        # First attempt should retry
        should_continue = await plugin.on_error(error, context)
        assert should_continue is True
        assert plugin._total_retries == 1

    @pytest.mark.asyncio
    async def test_on_error_max_retries_exceeded(self):
        """Test error handling when max retries exceeded."""
        plugin = RetryHandlerPlugin(strategy=FixedDelay(max_retries=1, delay=0.01))
        context = PluginContext(
            session_id="test",
            architecture_name="research",
        )

        error = ValueError("test error")
        error_key = f"{type(error).__name__}_{str(error)[:50]}"

        # First attempt - should retry
        context.shared_state[f"retry_attempt_{error_key}"] = 0
        should_continue = await plugin.on_error(error, context)
        assert should_continue is True

        # Second attempt - max retries reached
        context.shared_state[f"retry_attempt_{error_key}"] = 1
        should_continue = await plugin.on_error(error, context)
        assert should_continue is False
        assert plugin._total_failures == 1

    @pytest.mark.asyncio
    async def test_non_retryable_error(self):
        """Test handling of non-retryable errors."""
        plugin = RetryHandlerPlugin()
        context = PluginContext(
            session_id="test",
            architecture_name="research",
        )

        error = KeyboardInterrupt()

        should_continue = await plugin.on_error(error, context)
        assert should_continue is False
        assert plugin._total_retries == 0

    @pytest.mark.asyncio
    async def test_retryable_errors_filter(self):
        """Test retryable errors filter."""
        plugin = RetryHandlerPlugin(
            strategy=FixedDelay(max_retries=3, delay=0.01),
            retryable_errors={ValueError},
        )
        context = PluginContext(
            session_id="test",
            architecture_name="research",
        )

        # ValueError should be retried
        error1 = ValueError("test")
        should_continue = await plugin.on_error(error1, context)
        assert should_continue is True

        # TypeError should not be retried
        error2 = TypeError("test")
        should_continue = await plugin.on_error(error2, context)
        assert should_continue is False

    def test_get_retry_stats(self):
        """Test retry statistics retrieval."""
        plugin = RetryHandlerPlugin()
        plugin._total_retries = 10
        plugin._total_failures = 2
        plugin._retry_stats = {
            "error1": {
                "error_type": "ValueError",
                "error_message": "test",
                "retry_count": 3,
                "first_seen": 1.0,
                "last_retry": 2.0,
            }
        }

        stats = plugin.get_retry_stats()

        assert stats["total_retries"] == 10
        assert stats["total_failures"] == 2
        assert stats["unique_errors"] == 1
        assert len(stats["errors"]) == 1

    def test_reset(self):
        """Test reset functionality."""
        plugin = RetryHandlerPlugin()
        plugin._total_retries = 10
        plugin._total_failures = 2
        plugin._retry_stats = {"test": {}}

        plugin.reset()

        assert plugin._total_retries == 0
        assert plugin._total_failures == 0
        assert len(plugin._retry_stats) == 0
