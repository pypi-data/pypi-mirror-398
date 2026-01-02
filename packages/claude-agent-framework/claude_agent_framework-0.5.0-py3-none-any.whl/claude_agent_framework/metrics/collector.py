"""
Metrics collector for performance tracking.

Collects comprehensive metrics during session execution including:
- Execution time (total, per-stage, per-agent)
- Agent statistics (spawn count, type distribution)
- Tool usage (call count, types, error rates)
- Token consumption (input/output, estimated cost)
- Memory usage (peak, average)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class AgentMetrics:
    """Metrics for a single agent execution."""

    agent_type: str
    started_at: float
    completed_at: float | None = None
    status: str = "running"  # running, completed, failed
    error: str | None = None

    @property
    def duration_ms(self) -> float:
        """Get execution duration in milliseconds."""
        if self.completed_at is None:
            return (time.time() - self.started_at) * 1000
        return (self.completed_at - self.started_at) * 1000


@dataclass
class ToolMetrics:
    """Metrics for a single tool call."""

    tool_name: str
    called_at: float
    completed_at: float | None = None
    status: str = "pending"  # pending, success, failed
    error: str | None = None

    @property
    def duration_ms(self) -> float:
        """Get tool call duration in milliseconds."""
        if self.completed_at is None:
            return (time.time() - self.called_at) * 1000
        return (self.completed_at - self.called_at) * 1000


@dataclass
class TokenMetrics:
    """Token usage metrics."""

    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return self.input_tokens + self.output_tokens

    def estimate_cost_usd(
        self,
        input_price_per_mtok: float = 3.0,  # Sonnet pricing
        output_price_per_mtok: float = 15.0,
    ) -> float:
        """
        Estimate cost in USD.

        Default prices are for Claude Sonnet 4.5 (as of Dec 2025):
        - Input: $3 per million tokens
        - Output: $15 per million tokens
        """
        input_cost = (self.input_tokens / 1_000_000) * input_price_per_mtok
        output_cost = (self.output_tokens / 1_000_000) * output_price_per_mtok
        return input_cost + output_cost


@dataclass
class SessionMetrics:
    """
    Comprehensive metrics for an entire session.

    Tracks all aspects of session execution for performance analysis.
    """

    session_id: str
    architecture_name: str
    started_at: float = field(default_factory=time.time)
    completed_at: float | None = None

    # Agent metrics
    agents: list[AgentMetrics] = field(default_factory=list)

    # Tool metrics
    tools: list[ToolMetrics] = field(default_factory=list)

    # Token metrics
    tokens: TokenMetrics = field(default_factory=TokenMetrics)

    # Memory metrics (in bytes)
    peak_memory_bytes: int = 0
    memory_samples: list[int] = field(default_factory=list)

    # Error tracking
    errors: list[dict[str, Any]] = field(default_factory=list)

    @property
    def duration_ms(self) -> float:
        """Total session duration in milliseconds."""
        if self.completed_at is None:
            return (time.time() - self.started_at) * 1000
        return (self.completed_at - self.started_at) * 1000

    @property
    def agent_count(self) -> int:
        """Total number of agents spawned."""
        return len(self.agents)

    @property
    def tool_call_count(self) -> int:
        """Total number of tool calls."""
        return len(self.tools)

    @property
    def successful_tool_calls(self) -> int:
        """Number of successful tool calls."""
        return sum(1 for tool in self.tools if tool.status == "success")

    @property
    def failed_tool_calls(self) -> int:
        """Number of failed tool calls."""
        return sum(1 for tool in self.tools if tool.status == "failed")

    @property
    def tool_error_rate(self) -> float:
        """Tool call error rate (0.0 to 1.0)."""
        if self.tool_call_count == 0:
            return 0.0
        return self.failed_tool_calls / self.tool_call_count

    @property
    def average_memory_bytes(self) -> float:
        """Average memory usage in bytes."""
        if not self.memory_samples:
            return 0.0
        return sum(self.memory_samples) / len(self.memory_samples)

    @property
    def estimated_cost_usd(self) -> float:
        """Estimated total cost in USD."""
        return self.tokens.estimate_cost_usd()

    def agent_type_distribution(self) -> dict[str, int]:
        """Get distribution of agent types."""
        distribution: dict[str, int] = {}
        for agent in self.agents:
            distribution[agent.agent_type] = distribution.get(agent.agent_type, 0) + 1
        return distribution

    def tool_type_distribution(self) -> dict[str, int]:
        """Get distribution of tool types."""
        distribution: dict[str, int] = {}
        for tool in self.tools:
            distribution[tool.tool_name] = distribution.get(tool.tool_name, 0) + 1
        return distribution

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary format."""
        return {
            "session_id": self.session_id,
            "architecture_name": self.architecture_name,
            "started_at": datetime.fromtimestamp(self.started_at).isoformat(),
            "completed_at": (
                datetime.fromtimestamp(self.completed_at).isoformat() if self.completed_at else None
            ),
            "duration_ms": self.duration_ms,
            "agents": {
                "total_count": self.agent_count,
                "type_distribution": self.agent_type_distribution(),
                "details": [
                    {
                        "type": agent.agent_type,
                        "duration_ms": agent.duration_ms,
                        "status": agent.status,
                        "error": agent.error,
                    }
                    for agent in self.agents
                ],
            },
            "tools": {
                "total_calls": self.tool_call_count,
                "successful": self.successful_tool_calls,
                "failed": self.failed_tool_calls,
                "error_rate": self.tool_error_rate,
                "type_distribution": self.tool_type_distribution(),
                "details": [
                    {
                        "name": tool.tool_name,
                        "duration_ms": tool.duration_ms,
                        "status": tool.status,
                        "error": tool.error,
                    }
                    for tool in self.tools
                ],
            },
            "tokens": {
                "input": self.tokens.input_tokens,
                "output": self.tokens.output_tokens,
                "total": self.tokens.total_tokens,
                "estimated_cost_usd": self.estimated_cost_usd,
            },
            "memory": {
                "peak_bytes": self.peak_memory_bytes,
                "average_bytes": self.average_memory_bytes,
                "peak_mb": self.peak_memory_bytes / (1024 * 1024),
                "average_mb": self.average_memory_bytes / (1024 * 1024),
            },
            "errors": self.errors,
        }


class MetricsCollector:
    """
    Collects metrics during session execution.

    Can be used standalone or as part of a plugin.
    """

    def __init__(self, session_id: str, architecture_name: str) -> None:
        """
        Initialize metrics collector.

        Args:
            session_id: Unique session identifier
            architecture_name: Name of the architecture being executed
        """
        self.metrics = SessionMetrics(session_id=session_id, architecture_name=architecture_name)
        self._active_agents: dict[str, AgentMetrics] = {}
        self._active_tools: dict[str, ToolMetrics] = {}

    def start_session(self) -> None:
        """Mark session start."""
        self.metrics.started_at = time.time()

    def end_session(self) -> None:
        """Mark session end."""
        self.metrics.completed_at = time.time()

    def start_agent(self, agent_type: str, agent_id: str | None = None) -> str:
        """
        Record agent spawn.

        Args:
            agent_type: Type of agent being spawned
            agent_id: Optional unique identifier for this agent instance

        Returns:
            Agent ID for tracking
        """
        if agent_id is None:
            agent_id = f"{agent_type}_{len(self.metrics.agents)}"

        agent_metrics = AgentMetrics(
            agent_type=agent_type, started_at=time.time(), status="running"
        )
        self.metrics.agents.append(agent_metrics)
        self._active_agents[agent_id] = agent_metrics

        return agent_id

    def end_agent(self, agent_id: str, status: str = "completed", error: str | None = None) -> None:
        """
        Record agent completion.

        Args:
            agent_id: Agent identifier from start_agent
            status: Completion status (completed/failed)
            error: Error message if failed
        """
        if agent_id in self._active_agents:
            agent_metrics = self._active_agents[agent_id]
            agent_metrics.completed_at = time.time()
            agent_metrics.status = status
            agent_metrics.error = error
            del self._active_agents[agent_id]

    def start_tool_call(self, tool_name: str, call_id: str | None = None) -> str:
        """
        Record tool call start.

        Args:
            tool_name: Name of the tool being called
            call_id: Optional unique identifier for this call

        Returns:
            Call ID for tracking
        """
        if call_id is None:
            call_id = f"{tool_name}_{len(self.metrics.tools)}"

        tool_metrics = ToolMetrics(tool_name=tool_name, called_at=time.time(), status="pending")
        self.metrics.tools.append(tool_metrics)
        self._active_tools[call_id] = tool_metrics

        return call_id

    def end_tool_call(
        self, call_id: str, status: str = "success", error: str | None = None
    ) -> None:
        """
        Record tool call completion.

        Args:
            call_id: Call identifier from start_tool_call
            status: Completion status (success/failed)
            error: Error message if failed
        """
        if call_id in self._active_tools:
            tool_metrics = self._active_tools[call_id]
            tool_metrics.completed_at = time.time()
            tool_metrics.status = status
            tool_metrics.error = error
            del self._active_tools[call_id]

    def record_tokens(self, input_tokens: int, output_tokens: int) -> None:
        """
        Record token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        """
        self.metrics.tokens.input_tokens += input_tokens
        self.metrics.tokens.output_tokens += output_tokens

    def record_memory_sample(self, memory_bytes: int) -> None:
        """
        Record memory usage sample.

        Args:
            memory_bytes: Current memory usage in bytes
        """
        self.metrics.memory_samples.append(memory_bytes)
        if memory_bytes > self.metrics.peak_memory_bytes:
            self.metrics.peak_memory_bytes = memory_bytes

    def record_error(
        self, error_type: str, error_message: str, context: dict[str, Any] | None = None
    ) -> None:
        """
        Record an error occurrence.

        Args:
            error_type: Type/category of error
            error_message: Error message
            context: Additional context information
        """
        self.metrics.errors.append(
            {
                "timestamp": datetime.now().isoformat(),
                "type": error_type,
                "message": error_message,
                "context": context or {},
            }
        )

    def get_metrics(self) -> SessionMetrics:
        """Get current metrics snapshot."""
        return self.metrics

    def reset(self) -> None:
        """Reset all metrics."""
        self.metrics = SessionMetrics(
            session_id=self.metrics.session_id,
            architecture_name=self.metrics.architecture_name,
        )
        self._active_agents.clear()
        self._active_tools.clear()
