"""
Built-in metrics collector plugin.

Automatically collects comprehensive metrics during session execution.
"""

from __future__ import annotations

from typing import Any

from claude_agent_framework.metrics.collector import MetricsCollector, SessionMetrics
from claude_agent_framework.plugins.base import BasePlugin, PluginContext


class MetricsCollectorPlugin(BasePlugin):
    """
    Built-in plugin that collects comprehensive execution metrics.

    Automatically tracks:
    - Session duration
    - Agent spawns and completions
    - Tool calls
    - Errors

    Usage:
        from claude_agent_framework.plugins.builtin import MetricsCollectorPlugin
        from claude_agent_framework import init

        session = init("research")
        metrics_plugin = MetricsCollectorPlugin()
        session.architecture.add_plugin(metrics_plugin)

        # ... run session ...

        # Get metrics
        metrics = metrics_plugin.get_metrics()
        print(f"Duration: {metrics.duration_ms}ms")
        print(f"Agents: {metrics.agent_count}")
        print(f"Cost: ${metrics.estimated_cost_usd:.4f}")
    """

    name = "metrics_collector"
    version = "1.0.0"
    description = "Collects comprehensive execution metrics"

    def __init__(self) -> None:
        """Initialize metrics collector plugin."""
        self._collector: MetricsCollector | None = None
        self._agent_tracking: dict[str, str] = {}  # context_id -> collector_id
        self._tool_tracking: dict[str, str] = {}  # context_id -> collector_id

    async def on_session_start(self, context: PluginContext) -> None:
        """Initialize metrics collector when session starts."""
        self._collector = MetricsCollector(
            session_id=context.session_id,
            architecture_name=context.architecture_name,
        )
        self._collector.start_session()

    async def on_session_end(self, context: PluginContext) -> None:
        """Finalize metrics when session ends."""
        if self._collector:
            self._collector.end_session()

    async def on_agent_spawn(
        self, agent_type: str, agent_prompt: str, context: PluginContext
    ) -> str:
        """Record agent spawn."""
        if self._collector:
            # Generate unique context ID
            context_id = f"agent_{len(self._agent_tracking)}"

            # Start tracking in collector
            collector_id = self._collector.start_agent(agent_type)

            # Map context ID to collector ID
            self._agent_tracking[context_id] = collector_id

            # Store context ID for later retrieval
            context.shared_state[f"metrics_agent_{agent_type}"] = context_id

        return agent_prompt  # Return unmodified prompt

    async def on_agent_complete(self, agent_type: str, result: Any, context: PluginContext) -> None:
        """Record agent completion."""
        if self._collector:
            # Retrieve context ID
            context_id = context.shared_state.get(f"metrics_agent_{agent_type}")

            if context_id and context_id in self._agent_tracking:
                collector_id = self._agent_tracking[context_id]
                self._collector.end_agent(collector_id, status="completed")

                # Cleanup tracking
                del self._agent_tracking[context_id]

    async def on_tool_call(
        self, tool_name: str, tool_input: dict[str, Any], context: PluginContext
    ) -> None:
        """Record tool call start."""
        if self._collector:
            # Generate unique context ID
            context_id = f"tool_{len(self._tool_tracking)}"

            # Start tracking in collector
            collector_id = self._collector.start_tool_call(tool_name)

            # Map context ID to collector ID
            self._tool_tracking[context_id] = collector_id

            # Store in shared state for retrieval
            context.shared_state["metrics_tool_current"] = context_id

    async def on_tool_result(self, tool_name: str, result: Any, context: PluginContext) -> None:
        """Record tool call completion."""
        if self._collector:
            # Retrieve context ID
            context_id = context.shared_state.get("metrics_tool_current")

            if context_id and context_id in self._tool_tracking:
                collector_id = self._tool_tracking[context_id]
                self._collector.end_tool_call(collector_id, status="success")

                # Cleanup tracking
                del self._tool_tracking[context_id]
                context.shared_state.pop("metrics_tool_current", None)

    async def on_error(self, error: Exception, context: PluginContext) -> bool:
        """Record error occurrence."""
        if self._collector:
            self._collector.record_error(
                error_type=type(error).__name__,
                error_message=str(error),
                context={
                    "architecture": context.architecture_name,
                    "session_id": context.session_id,
                },
            )
        return True  # Continue execution

    def get_metrics(self) -> SessionMetrics | None:
        """
        Get collected metrics.

        Returns:
            SessionMetrics if collector initialized, None otherwise
        """
        if self._collector:
            return self._collector.get_metrics()
        return None

    def record_tokens(self, input_tokens: int, output_tokens: int) -> None:
        """
        Manually record token usage.

        Useful for integrating SDK token counts.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        """
        if self._collector:
            self._collector.record_tokens(input_tokens, output_tokens)

    def record_memory_sample(self, memory_bytes: int) -> None:
        """
        Record memory usage sample.

        Args:
            memory_bytes: Current memory usage in bytes
        """
        if self._collector:
            self._collector.record_memory_sample(memory_bytes)

    def reset(self) -> None:
        """Reset all metrics."""
        if self._collector:
            self._collector.reset()
            self._agent_tracking.clear()
            self._tool_tracking.clear()
