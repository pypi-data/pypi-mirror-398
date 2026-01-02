"""Tests for metrics collector and exporter."""

import json
import time

from claude_agent_framework.metrics.collector import (
    AgentMetrics,
    MetricsCollector,
    SessionMetrics,
    TokenMetrics,
    ToolMetrics,
)
from claude_agent_framework.metrics.exporter import (
    MetricsExporter,
    export_to_csv,
    export_to_json,
    export_to_prometheus,
)


class TestTokenMetrics:
    """Tests for TokenMetrics."""

    def test_token_metrics_initialization(self):
        """Test TokenMetrics initialization."""
        tokens = TokenMetrics()
        assert tokens.input_tokens == 0
        assert tokens.output_tokens == 0
        assert tokens.total_tokens == 0

    def test_token_metrics_total(self):
        """Test total tokens calculation."""
        tokens = TokenMetrics(input_tokens=1000, output_tokens=500)
        assert tokens.total_tokens == 1500

    def test_estimate_cost_default_pricing(self):
        """Test cost estimation with default pricing."""
        tokens = TokenMetrics(input_tokens=1_000_000, output_tokens=500_000)
        # 1M input * $3/M + 0.5M output * $15/M = $3 + $7.5 = $10.5
        assert tokens.estimate_cost_usd() == 10.5

    def test_estimate_cost_custom_pricing(self):
        """Test cost estimation with custom pricing."""
        tokens = TokenMetrics(input_tokens=1_000_000, output_tokens=1_000_000)
        # 1M * $10/M + 1M * $20/M = $10 + $20 = $30
        cost = tokens.estimate_cost_usd(input_price_per_mtok=10.0, output_price_per_mtok=20.0)
        assert cost == 30.0


class TestAgentMetrics:
    """Tests for AgentMetrics."""

    def test_agent_metrics_initialization(self):
        """Test AgentMetrics initialization."""
        agent = AgentMetrics(agent_type="researcher", started_at=time.time())
        assert agent.agent_type == "researcher"
        assert agent.status == "running"
        assert agent.completed_at is None
        assert agent.error is None

    def test_agent_metrics_duration_running(self):
        """Test duration calculation for running agent."""
        start = time.time()
        agent = AgentMetrics(agent_type="researcher", started_at=start)
        time.sleep(0.05)  # 50ms
        duration = agent.duration_ms
        assert duration >= 50  # At least 50ms

    def test_agent_metrics_duration_completed(self):
        """Test duration calculation for completed agent."""
        start = time.time()
        agent = AgentMetrics(
            agent_type="researcher",
            started_at=start,
            completed_at=start + 0.1,  # 100ms later
        )
        assert 99 <= agent.duration_ms <= 101  # ~100ms with tolerance


class TestToolMetrics:
    """Tests for ToolMetrics."""

    def test_tool_metrics_initialization(self):
        """Test ToolMetrics initialization."""
        tool = ToolMetrics(tool_name="WebSearch", called_at=time.time())
        assert tool.tool_name == "WebSearch"
        assert tool.status == "pending"
        assert tool.completed_at is None

    def test_tool_metrics_duration(self):
        """Test tool call duration."""
        start = time.time()
        tool = ToolMetrics(
            tool_name="Read",
            called_at=start,
            completed_at=start + 0.05,
        )
        assert 49 <= tool.duration_ms <= 51  # ~50ms


class TestSessionMetrics:
    """Tests for SessionMetrics."""

    def test_session_metrics_initialization(self):
        """Test SessionMetrics initialization."""
        metrics = SessionMetrics(
            session_id="test-123",
            architecture_name="research",
        )
        assert metrics.session_id == "test-123"
        assert metrics.architecture_name == "research"
        assert metrics.agent_count == 0
        assert metrics.tool_call_count == 0

    def test_agent_count(self):
        """Test agent count calculation."""
        metrics = SessionMetrics(session_id="test", architecture_name="research")
        metrics.agents.append(AgentMetrics(agent_type="researcher", started_at=time.time()))
        metrics.agents.append(AgentMetrics(agent_type="analyst", started_at=time.time()))
        assert metrics.agent_count == 2

    def test_tool_call_statistics(self):
        """Test tool call statistics."""
        metrics = SessionMetrics(session_id="test", architecture_name="research")

        # Add successful tools
        metrics.tools.append(ToolMetrics(tool_name="Read", called_at=time.time(), status="success"))
        metrics.tools.append(
            ToolMetrics(tool_name="Write", called_at=time.time(), status="success")
        )

        # Add failed tool
        metrics.tools.append(ToolMetrics(tool_name="Bash", called_at=time.time(), status="failed"))

        assert metrics.tool_call_count == 3
        assert metrics.successful_tool_calls == 2
        assert metrics.failed_tool_calls == 1
        assert abs(metrics.tool_error_rate - 0.333) < 0.01

    def test_agent_type_distribution(self):
        """Test agent type distribution."""
        metrics = SessionMetrics(session_id="test", architecture_name="research")
        metrics.agents.append(AgentMetrics(agent_type="researcher", started_at=time.time()))
        metrics.agents.append(AgentMetrics(agent_type="researcher", started_at=time.time()))
        metrics.agents.append(AgentMetrics(agent_type="analyst", started_at=time.time()))

        distribution = metrics.agent_type_distribution()
        assert distribution["researcher"] == 2
        assert distribution["analyst"] == 1

    def test_tool_type_distribution(self):
        """Test tool type distribution."""
        metrics = SessionMetrics(session_id="test", architecture_name="research")
        metrics.tools.append(ToolMetrics(tool_name="Read", called_at=time.time()))
        metrics.tools.append(ToolMetrics(tool_name="Read", called_at=time.time()))
        metrics.tools.append(ToolMetrics(tool_name="Write", called_at=time.time()))

        distribution = metrics.tool_type_distribution()
        assert distribution["Read"] == 2
        assert distribution["Write"] == 1

    def test_to_dict(self):
        """Test conversion to dictionary."""
        metrics = SessionMetrics(session_id="test", architecture_name="research")
        metrics.agents.append(AgentMetrics(agent_type="researcher", started_at=time.time()))
        metrics.tools.append(ToolMetrics(tool_name="Read", called_at=time.time()))
        metrics.tokens.input_tokens = 1000
        metrics.tokens.output_tokens = 500

        data = metrics.to_dict()

        assert data["session_id"] == "test"
        assert data["architecture_name"] == "research"
        assert data["agents"]["total_count"] == 1
        assert data["tools"]["total_calls"] == 1
        assert data["tokens"]["input"] == 1000
        assert data["tokens"]["output"] == 500


class TestMetricsCollector:
    """Tests for MetricsCollector."""

    def test_collector_initialization(self):
        """Test MetricsCollector initialization."""
        collector = MetricsCollector(session_id="test-123", architecture_name="research")
        assert collector.metrics.session_id == "test-123"
        assert collector.metrics.architecture_name == "research"

    def test_session_lifecycle(self):
        """Test session start and end."""
        collector = MetricsCollector(session_id="test", architecture_name="research")

        collector.start_session()
        start_time = collector.metrics.started_at

        time.sleep(0.05)  # 50ms

        collector.end_session()
        assert collector.metrics.completed_at is not None
        assert collector.metrics.completed_at > start_time

    def test_agent_lifecycle(self):
        """Test agent spawn and completion tracking."""
        collector = MetricsCollector(session_id="test", architecture_name="research")

        # Start agent
        agent_id = collector.start_agent("researcher")
        assert len(collector.metrics.agents) == 1
        assert collector.metrics.agents[0].status == "running"

        time.sleep(0.02)  # 20ms

        # End agent
        collector.end_agent(agent_id, status="completed")
        assert collector.metrics.agents[0].status == "completed"
        assert collector.metrics.agents[0].completed_at is not None

    def test_agent_failure(self):
        """Test agent failure tracking."""
        collector = MetricsCollector(session_id="test", architecture_name="research")

        agent_id = collector.start_agent("researcher")
        collector.end_agent(agent_id, status="failed", error="Connection timeout")

        assert collector.metrics.agents[0].status == "failed"
        assert collector.metrics.agents[0].error == "Connection timeout"

    def test_tool_call_lifecycle(self):
        """Test tool call tracking."""
        collector = MetricsCollector(session_id="test", architecture_name="research")

        # Start tool call
        call_id = collector.start_tool_call("WebSearch")
        assert len(collector.metrics.tools) == 1
        assert collector.metrics.tools[0].status == "pending"

        time.sleep(0.02)  # 20ms

        # End tool call
        collector.end_tool_call(call_id, status="success")
        assert collector.metrics.tools[0].status == "success"
        assert collector.metrics.tools[0].completed_at is not None

    def test_token_recording(self):
        """Test token usage recording."""
        collector = MetricsCollector(session_id="test", architecture_name="research")

        collector.record_tokens(input_tokens=1000, output_tokens=500)
        assert collector.metrics.tokens.input_tokens == 1000
        assert collector.metrics.tokens.output_tokens == 500

        # Record more tokens
        collector.record_tokens(input_tokens=500, output_tokens=250)
        assert collector.metrics.tokens.input_tokens == 1500
        assert collector.metrics.tokens.output_tokens == 750

    def test_memory_recording(self):
        """Test memory usage recording."""
        collector = MetricsCollector(session_id="test", architecture_name="research")

        collector.record_memory_sample(1024 * 1024 * 100)  # 100MB
        collector.record_memory_sample(1024 * 1024 * 150)  # 150MB
        collector.record_memory_sample(1024 * 1024 * 120)  # 120MB

        assert collector.metrics.peak_memory_bytes == 1024 * 1024 * 150
        assert len(collector.metrics.memory_samples) == 3

    def test_error_recording(self):
        """Test error recording."""
        collector = MetricsCollector(session_id="test", architecture_name="research")

        collector.record_error(
            error_type="APIError",
            error_message="Rate limit exceeded",
            context={"retry_after": 60},
        )

        assert len(collector.metrics.errors) == 1
        error = collector.metrics.errors[0]
        assert error["type"] == "APIError"
        assert error["message"] == "Rate limit exceeded"
        assert error["context"]["retry_after"] == 60

    def test_reset(self):
        """Test metrics reset."""
        collector = MetricsCollector(session_id="test", architecture_name="research")

        # Add some data
        collector.start_agent("researcher")
        collector.record_tokens(1000, 500)

        # Reset
        collector.reset()

        assert len(collector.metrics.agents) == 0
        assert collector.metrics.tokens.total_tokens == 0


class TestMetricsExporter:
    """Tests for MetricsExporter."""

    def test_to_json(self):
        """Test JSON export."""
        metrics = SessionMetrics(session_id="test", architecture_name="research")
        metrics.tokens.input_tokens = 1000

        json_str = MetricsExporter.to_json(metrics)
        data = json.loads(json_str)

        assert data["session_id"] == "test"
        assert data["tokens"]["input"] == 1000

    def test_to_csv_summary(self):
        """Test CSV summary export."""
        metrics = SessionMetrics(session_id="test", architecture_name="research")
        metrics.tokens.input_tokens = 1000
        metrics.tokens.output_tokens = 500

        csv_str = MetricsExporter.to_csv_summary(metrics)

        assert "Session ID,test" in csv_str
        assert "Input Tokens,1000" in csv_str
        assert "Output Tokens,500" in csv_str

    def test_to_prometheus(self):
        """Test Prometheus export."""
        metrics = SessionMetrics(session_id="test", architecture_name="research")
        metrics.tokens.input_tokens = 1000
        metrics.agents.append(AgentMetrics(agent_type="researcher", started_at=time.time()))

        prom_str = MetricsExporter.to_prometheus(metrics)

        assert "claude_agent_session_duration_ms" in prom_str
        assert "claude_agent_agents_total" in prom_str
        assert "claude_agent_tokens_total" in prom_str
        assert 'session_id="test"' in prom_str

    def test_export_to_json_file(self, tmp_path):
        """Test JSON file export."""
        metrics = SessionMetrics(session_id="test", architecture_name="research")
        output_path = tmp_path / "metrics.json"

        export_to_json(metrics, output_path)

        assert output_path.exists()
        data = json.loads(output_path.read_text())
        assert data["session_id"] == "test"

    def test_export_to_csv_files(self, tmp_path):
        """Test CSV files export."""
        metrics = SessionMetrics(session_id="test", architecture_name="research")
        metrics.agents.append(AgentMetrics(agent_type="researcher", started_at=time.time()))
        metrics.tools.append(ToolMetrics(tool_name="Read", called_at=time.time()))

        files = export_to_csv(metrics, tmp_path, prefix="test")

        assert "summary" in files
        assert "agents" in files
        assert "tools" in files

        assert files["summary"].exists()
        assert files["agents"].exists()
        assert files["tools"].exists()

    def test_export_to_prometheus_file(self, tmp_path):
        """Test Prometheus file export."""
        metrics = SessionMetrics(session_id="test", architecture_name="research")
        output_path = tmp_path / "metrics.prom"

        export_to_prometheus(metrics, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "claude_agent" in content
