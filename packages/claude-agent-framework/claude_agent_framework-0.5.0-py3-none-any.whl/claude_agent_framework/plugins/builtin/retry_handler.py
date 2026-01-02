"""
Retry handler plugin for Claude Agent Framework.

Provides automatic retry logic for failed operations with configurable
retry strategies, backoff policies, and error filtering.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from claude_agent_framework.plugins.base import BasePlugin, PluginContext

if TYPE_CHECKING:
    pass


class RetryStrategy:
    """Base class for retry strategies."""

    def should_retry(self, attempt: int, error: Exception) -> bool:
        """Determine if retry should be attempted."""
        raise NotImplementedError

    def get_delay(self, attempt: int) -> float:
        """Get delay before next retry in seconds."""
        raise NotImplementedError


class ExponentialBackoff(RetryStrategy):
    """Exponential backoff retry strategy."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        multiplier: float = 2.0,
    ):
        """
        Initialize exponential backoff strategy.

        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            multiplier: Backoff multiplier
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.multiplier = multiplier

    def should_retry(self, attempt: int, error: Exception) -> bool:
        """Check if should retry based on attempt count."""
        return attempt < self.max_retries

    def get_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay."""
        delay = self.initial_delay * (self.multiplier**attempt)
        return min(delay, self.max_delay)


class FixedDelay(RetryStrategy):
    """Fixed delay retry strategy."""

    def __init__(self, max_retries: int = 3, delay: float = 1.0):
        """
        Initialize fixed delay strategy.

        Args:
            max_retries: Maximum number of retry attempts
            delay: Fixed delay between retries in seconds
        """
        self.max_retries = max_retries
        self.delay = delay

    def should_retry(self, attempt: int, error: Exception) -> bool:
        """Check if should retry based on attempt count."""
        return attempt < self.max_retries

    def get_delay(self, attempt: int) -> float:
        """Return fixed delay."""
        return self.delay


class RetryHandlerPlugin(BasePlugin):
    """
    Plugin to handle automatic retries for failed operations.

    Provides configurable retry logic with:
    - Multiple retry strategies (exponential backoff, fixed delay)
    - Error type filtering
    - Retry statistics tracking
    - Custom retry conditions
    """

    name = "retry_handler"
    version = "1.0.0"
    description = "Automatic retry handling for failed operations"

    def __init__(
        self,
        strategy: RetryStrategy | None = None,
        retryable_errors: set[type[Exception]] | None = None,
        non_retryable_errors: set[type[Exception]] | None = None,
        retry_condition: Callable[[Exception], bool] | None = None,
    ) -> None:
        """
        Initialize retry handler plugin.

        Args:
            strategy: Retry strategy (default: ExponentialBackoff)
            retryable_errors: Set of error types that should trigger retry
            non_retryable_errors: Set of error types that should NOT be retried
            retry_condition: Custom function to determine if error should be retried
        """
        self.strategy = strategy or ExponentialBackoff()
        self.retryable_errors = retryable_errors or set()
        self.non_retryable_errors = non_retryable_errors or {KeyboardInterrupt, SystemExit}
        self.retry_condition = retry_condition

        # Statistics
        self._retry_stats: dict[str, dict[str, Any]] = {}
        self._total_retries = 0
        self._total_failures = 0

    async def on_session_start(self, context: PluginContext) -> None:
        """Initialize retry tracking for session."""
        self._retry_stats = {}
        self._total_retries = 0
        self._total_failures = 0
        context.shared_state["retry_handler_initialized"] = True

    async def on_session_end(self, context: PluginContext) -> None:
        """Log retry statistics."""
        stats = self.get_retry_stats()
        context.shared_state["retry_stats"] = stats

    async def on_error(self, error: Exception, context: PluginContext) -> bool:
        """
        Handle error with retry logic.

        Args:
            error: The exception that occurred
            context: Plugin context

        Returns:
            True to continue execution (retry), False to abort
        """
        # Get current attempt count from context
        error_key = f"{type(error).__name__}_{str(error)[:50]}"
        attempt = context.shared_state.get(f"retry_attempt_{error_key}", 0)

        # Check if error should be retried
        if not self._should_retry_error(error, attempt):
            self._total_failures += 1
            return False

        # Update statistics
        if error_key not in self._retry_stats:
            self._retry_stats[error_key] = {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "retry_count": 0,
                "first_seen": time.time(),
                "last_retry": time.time(),
            }

        self._retry_stats[error_key]["retry_count"] += 1
        self._retry_stats[error_key]["last_retry"] = time.time()
        self._total_retries += 1

        # Calculate and apply delay
        delay = self.strategy.get_delay(attempt)
        await asyncio.sleep(delay)

        # Update attempt count
        context.shared_state[f"retry_attempt_{error_key}"] = attempt + 1

        # Return True to continue (retry)
        return True

    def _should_retry_error(self, error: Exception, attempt: int) -> bool:
        """
        Determine if error should be retried.

        Args:
            error: The exception
            attempt: Current attempt number

        Returns:
            True if should retry, False otherwise
        """
        # Check non-retryable errors first
        if any(isinstance(error, err_type) for err_type in self.non_retryable_errors):
            return False

        # Check retry strategy
        if not self.strategy.should_retry(attempt, error):
            return False

        # If retryable_errors specified, only retry those
        if self.retryable_errors:
            if not any(isinstance(error, err_type) for err_type in self.retryable_errors):
                return False

        # Check custom retry condition
        if self.retry_condition and not self.retry_condition(error):
            return False

        return True

    def get_retry_stats(self) -> dict[str, Any]:
        """
        Get retry statistics.

        Returns:
            Dictionary with retry statistics
        """
        return {
            "total_retries": self._total_retries,
            "total_failures": self._total_failures,
            "unique_errors": len(self._retry_stats),
            "errors": list(self._retry_stats.values()),
        }

    def reset(self) -> None:
        """Reset retry statistics."""
        self._retry_stats = {}
        self._total_retries = 0
        self._total_failures = 0
