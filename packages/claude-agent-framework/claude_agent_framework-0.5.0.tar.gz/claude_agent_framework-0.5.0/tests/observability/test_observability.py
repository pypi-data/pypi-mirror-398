"""Tests for observability module."""

import json

import pytest

from claude_agent_framework.observability import (
    EventLogger,
    EventType,
    LogEvent,
    SessionDebugger,
    SessionVisualizer,
)


class TestLogEvent:
    """Test LogEvent model."""

    def test_create_log_event(self):
        """Test creating a log event."""
        event = LogEvent(
            event=EventType.SESSION_START,
            session_id="test-123",
            message="Session started",
            metadata={"architecture": "research"},
        )

        assert event.event == EventType.SESSION_START
        assert event.session_id == "test-123"
        assert event.message == "Session started"
        assert event.metadata["architecture"] == "research"
        assert event.level == "INFO"
        assert event.timestamp is not None

    def test_to_json(self):
        """Test converting event to JSON."""
        event = LogEvent(
            event=EventType.AGENT_SPAWN,
            session_id="test-123",
            message="Agent spawned",
        )

        json_str = event.to_json()
        assert isinstance(json_str, str)
        assert "agent_spawn" in json_str
        assert "test-123" in json_str

    def test_to_dict(self):
        """Test converting event to dictionary."""
        event = LogEvent(
            event=EventType.TOOL_CALL,
            session_id="test-123",
            metadata={"tool_name": "WebSearch"},
        )

        event_dict = event.to_dict()
        assert isinstance(event_dict, dict)
        assert event_dict["event"] == EventType.TOOL_CALL
        assert event_dict["session_id"] == "test-123"
        assert event_dict["metadata"]["tool_name"] == "WebSearch"


class TestEventLogger:
    """Test EventLogger."""

    def test_initialization(self, tmp_path):
        """Test logger initialization."""
        log_file = tmp_path / "test.log"
        logger = EventLogger(session_id="test-session", log_file=log_file, console_output=False)

        assert logger.session_id == "test-session"
        assert logger.log_file == log_file
        assert logger.console_output is False

    def test_log_event(self):
        """Test logging an event."""
        logger = EventLogger(session_id="test-123", console_output=False)

        event = logger.log_event(EventType.CUSTOM, message="Test message", test_key="test_value")

        assert event.event == EventType.CUSTOM
        assert event.session_id == "test-123"
        assert event.message == "Test message"
        assert event.metadata["test_key"] == "test_value"

    def test_session_start(self):
        """Test session start logging."""
        logger = EventLogger(session_id="test-123", console_output=False)

        event = logger.session_start(architecture="research")

        assert event.event == EventType.SESSION_START
        assert event.metadata["architecture"] == "research"
        assert "research" in event.message

    def test_session_end(self):
        """Test session end logging."""
        logger = EventLogger(session_id="test-123", console_output=False)

        event = logger.session_end(duration=10.5)

        assert event.event == EventType.SESSION_END
        assert event.metadata["duration"] == 10.5

    def test_agent_spawn(self):
        """Test agent spawn logging."""
        logger = EventLogger(session_id="test-123", console_output=False)

        event = logger.agent_spawn(agent_type="researcher", agent_prompt="Test prompt")

        assert event.event == EventType.AGENT_SPAWN
        assert event.metadata["agent_type"] == "researcher"
        assert event.metadata["agent_prompt"] == "Test prompt"

    def test_agent_complete(self):
        """Test agent completion logging."""
        logger = EventLogger(session_id="test-123", console_output=False)

        event = logger.agent_complete(agent_type="researcher", status="success")

        assert event.event == EventType.AGENT_COMPLETE
        assert event.metadata["agent_type"] == "researcher"
        assert event.metadata["status"] == "success"

    def test_tool_call(self):
        """Test tool call logging."""
        logger = EventLogger(session_id="test-123", console_output=False)

        event = logger.tool_call(tool_name="WebSearch", tool_input={"query": "test query"})

        assert event.event == EventType.TOOL_CALL
        assert event.metadata["tool_name"] == "WebSearch"
        assert event.metadata["tool_input"]["query"] == "test query"

    def test_tool_result(self):
        """Test tool result logging."""
        logger = EventLogger(session_id="test-123", console_output=False)

        event = logger.tool_result(tool_name="WebSearch", success=True)

        assert event.event == EventType.TOOL_RESULT
        assert event.metadata["tool_name"] == "WebSearch"
        assert event.metadata["success"] is True

    def test_error_logging(self):
        """Test error logging."""
        logger = EventLogger(session_id="test-123", console_output=False)

        error = ValueError("Test error")
        event = logger.error(error)

        assert event.event == EventType.ERROR
        assert event.level == "ERROR"
        assert event.metadata["error_type"] == "ValueError"
        assert event.metadata["error_message"] == "Test error"

    def test_plugin_hook(self):
        """Test plugin hook logging."""
        logger = EventLogger(session_id="test-123", console_output=False)

        event = logger.plugin_hook(hook_name="on_session_start", plugin_name="test_plugin")

        assert event.event == EventType.PLUGIN_HOOK
        assert event.metadata["hook_name"] == "on_session_start"
        assert event.metadata["plugin_name"] == "test_plugin"

    def test_get_events(self):
        """Test getting events."""
        logger = EventLogger(session_id="test-123", console_output=False)

        logger.log_event(EventType.SESSION_START, message="Start")
        logger.log_event(EventType.AGENT_SPAWN, message="Spawn")
        logger.log_event(EventType.ERROR, message="Error", level="ERROR")

        all_events = logger.get_events()
        assert len(all_events) == 3

        agent_events = logger.get_events(event_type=EventType.AGENT_SPAWN)
        assert len(agent_events) == 1
        assert agent_events[0].event == EventType.AGENT_SPAWN

        error_events = logger.get_events(level="ERROR")
        assert len(error_events) == 1
        assert error_events[0].level == "ERROR"

    def test_get_event_summary(self):
        """Test getting event summary."""
        logger = EventLogger(session_id="test-123", console_output=False)

        logger.log_event(EventType.SESSION_START)
        logger.log_event(EventType.AGENT_SPAWN)
        logger.log_event(EventType.AGENT_SPAWN)
        logger.log_event(EventType.ERROR, level="ERROR")

        summary = logger.get_event_summary()

        assert summary["total_events"] == 4
        assert summary["event_counts"][EventType.AGENT_SPAWN] == 2
        assert summary["level_counts"]["ERROR"] == 1
        assert summary["session_id"] == "test-123"

    def test_export_json(self, tmp_path):
        """Test exporting events to JSON."""
        logger = EventLogger(session_id="test-123", console_output=False)

        logger.log_event(EventType.SESSION_START, message="Start")
        logger.log_event(EventType.AGENT_SPAWN, message="Spawn")

        output_file = tmp_path / "events.json"
        logger.export_json(output_file)

        assert output_file.exists()

        with output_file.open() as f:
            data = json.load(f)

        assert data["session_id"] == "test-123"
        assert len(data["events"]) == 2
        assert "summary" in data

    def test_clear_events(self):
        """Test clearing events."""
        logger = EventLogger(session_id="test-123", console_output=False)

        logger.log_event(EventType.SESSION_START)
        logger.log_event(EventType.AGENT_SPAWN)

        assert len(logger.get_events()) == 2

        logger.clear_events()

        assert len(logger.get_events()) == 0


class TestSessionVisualizer:
    """Test SessionVisualizer."""

    @pytest.fixture
    def sample_logger(self):
        """Create a sample logger with events."""
        logger = EventLogger(session_id="test-123", console_output=False)
        logger.session_start(architecture="research")
        logger.agent_spawn(agent_type="researcher")
        logger.tool_call(tool_name="WebSearch", tool_input={"query": "test"})
        logger.tool_result(tool_name="WebSearch", success=True)
        logger.agent_complete(agent_type="researcher")
        logger.session_end()
        return logger

    def test_initialization(self, sample_logger):
        """Test visualizer initialization."""
        visualizer = SessionVisualizer(sample_logger)

        assert visualizer.logger == sample_logger
        assert len(visualizer._events) == 6

    def test_load_events(self):
        """Test loading events from list."""
        events = [
            LogEvent(event=EventType.SESSION_START, session_id="test"),
            LogEvent(event=EventType.SESSION_END, session_id="test"),
        ]

        visualizer = SessionVisualizer()
        visualizer.load_events(events)

        assert len(visualizer._events) == 2

    def test_load_from_json(self, tmp_path, sample_logger):
        """Test loading events from JSON file."""
        json_file = tmp_path / "events.json"
        sample_logger.export_json(json_file)

        visualizer = SessionVisualizer()
        visualizer.load_from_json(json_file)

        assert len(visualizer._events) == 6

    def test_calculate_statistics(self, sample_logger):
        """Test statistics calculation."""
        visualizer = SessionVisualizer(sample_logger)
        stats = visualizer._calculate_statistics()

        assert stats["total_events"] == 6
        assert stats["session_id"] == "test-123"
        assert EventType.SESSION_START in stats["event_counts"]
        assert stats["total_agents"] == 1
        assert stats["total_tools"] == 1

    def test_prepare_timeline_data(self, sample_logger):
        """Test timeline data preparation."""
        visualizer = SessionVisualizer(sample_logger)
        timeline_data = visualizer._prepare_timeline_data()

        assert len(timeline_data) == 6
        assert all("timestamp" in item for item in timeline_data)
        assert all("event_type" in item for item in timeline_data)

    def test_prepare_tool_graph_data(self, sample_logger):
        """Test tool graph data preparation."""
        visualizer = SessionVisualizer(sample_logger)
        tool_data = visualizer._prepare_tool_graph_data()

        assert tool_data["total_calls"] == 1
        assert "WebSearch" in tool_data["tool_counts"]
        assert tool_data["tool_counts"]["WebSearch"] == 1

    def test_generate_dashboard(self, tmp_path, sample_logger):
        """Test dashboard HTML generation."""
        visualizer = SessionVisualizer(sample_logger)

        # Generate without saving
        html = visualizer.generate_dashboard()
        assert isinstance(html, str)
        assert "Session Dashboard" in html
        assert "test-123" in html

        # Generate with saving
        output_file = tmp_path / "dashboard.html"
        html = visualizer.generate_dashboard(output_file)
        assert output_file.exists()

    def test_generate_timeline(self, tmp_path, sample_logger):
        """Test timeline HTML generation."""
        visualizer = SessionVisualizer(sample_logger)

        html = visualizer.generate_timeline()
        assert isinstance(html, str)
        assert "Session Timeline" in html

        output_file = tmp_path / "timeline.html"
        visualizer.generate_timeline(output_file)
        assert output_file.exists()

    def test_generate_tool_graph(self, tmp_path, sample_logger):
        """Test tool graph HTML generation."""
        visualizer = SessionVisualizer(sample_logger)

        html = visualizer.generate_tool_graph()
        assert isinstance(html, str)
        assert "Tool Call Analysis" in html

        output_file = tmp_path / "tool_graph.html"
        visualizer.generate_tool_graph(output_file)
        assert output_file.exists()

    def test_generate_full_report(self, tmp_path, sample_logger):
        """Test full report generation."""
        visualizer = SessionVisualizer(sample_logger)

        output_dir = tmp_path / "report"
        files = visualizer.generate_full_report(output_dir)

        assert "dashboard" in files
        assert "timeline" in files
        assert "tool_graph" in files
        assert "events" in files

        assert files["dashboard"].exists()
        assert files["timeline"].exists()
        assert files["tool_graph"].exists()
        assert files["events"].exists()


class TestSessionDebugger:
    """Test SessionDebugger."""

    @pytest.fixture
    def sample_logger(self):
        """Create a sample logger with events."""
        logger = EventLogger(session_id="test-123", console_output=False)
        logger.session_start(architecture="research")
        logger.agent_spawn(agent_type="researcher")
        logger.tool_call(tool_name="WebSearch", tool_input={"query": "test"})
        logger.tool_result(tool_name="WebSearch", success=True)
        logger.agent_complete(agent_type="researcher")
        logger.error(ValueError("Test error"))
        logger.session_end()
        return logger

    def test_initialization(self, sample_logger):
        """Test debugger initialization."""
        debugger = SessionDebugger(sample_logger)

        assert debugger.logger == sample_logger
        assert len(debugger._events) == 7

    def test_inspect_event(self, sample_logger):
        """Test inspecting a specific event."""
        debugger = SessionDebugger(sample_logger)

        event_details = debugger.inspect_event(0)

        assert event_details["index"] == 0
        assert "timestamp" in event_details
        assert "event_type" in event_details
        assert "metadata" in event_details

    def test_inspect_event_invalid_index(self, sample_logger):
        """Test inspecting with invalid index."""
        debugger = SessionDebugger(sample_logger)

        with pytest.raises(ValueError, match="Invalid event index"):
            debugger.inspect_event(999)

    def test_find_events_by_type(self, sample_logger):
        """Test finding events by type."""
        debugger = SessionDebugger(sample_logger)

        tool_events = debugger.find_events(event_type=EventType.TOOL_CALL)

        assert len(tool_events) == 1
        assert tool_events[0]["event_type"] == EventType.TOOL_CALL

    def test_find_events_by_level(self, sample_logger):
        """Test finding events by level."""
        debugger = SessionDebugger(sample_logger)

        error_events = debugger.find_events(level="ERROR")

        assert len(error_events) == 1
        assert error_events[0]["level"] == "ERROR"

    def test_find_events_by_search_term(self, sample_logger):
        """Test finding events by search term."""
        debugger = SessionDebugger(sample_logger)

        search_results = debugger.find_events(search_term="WebSearch")

        assert len(search_results) >= 2  # tool_call and tool_result

    def test_analyze_errors(self, sample_logger):
        """Test error analysis."""
        debugger = SessionDebugger(sample_logger)

        error_analysis = debugger.analyze_errors()

        assert error_analysis["error_count"] == 1
        assert "ValueError" in error_analysis["error_types"]
        assert error_analysis["error_types"]["ValueError"] == 1
        assert len(error_analysis["errors"]) == 1

    def test_analyze_errors_no_errors(self):
        """Test error analysis with no errors."""
        logger = EventLogger(session_id="test-123", console_output=False)
        logger.session_start(architecture="research")

        debugger = SessionDebugger(logger)
        error_analysis = debugger.analyze_errors()

        assert error_analysis["error_count"] == 0
        assert error_analysis["errors"] == []

    def test_trace_tool_calls(self, sample_logger):
        """Test tracing tool calls."""
        debugger = SessionDebugger(sample_logger)

        tool_traces = debugger.trace_tool_calls()

        assert len(tool_traces) == 1
        assert tool_traces[0]["tool_name"] == "WebSearch"
        assert tool_traces[0]["success"] is True

    def test_trace_tool_calls_filtered(self, sample_logger):
        """Test tracing specific tool."""
        debugger = SessionDebugger(sample_logger)

        traces = debugger.trace_tool_calls(tool_name="WebSearch")

        assert len(traces) == 1
        assert traces[0]["tool_name"] == "WebSearch"

    def test_trace_agent_execution(self, sample_logger):
        """Test tracing agent execution."""
        debugger = SessionDebugger(sample_logger)

        agent_traces = debugger.trace_agent_execution()

        assert len(agent_traces) == 1
        assert agent_traces[0]["agent_type"] == "researcher"
        assert agent_traces[0]["complete_timestamp"] is not None

    def test_trace_agent_execution_filtered(self, sample_logger):
        """Test tracing specific agent type."""
        debugger = SessionDebugger(sample_logger)

        traces = debugger.trace_agent_execution(agent_type="researcher")

        assert len(traces) == 1
        assert traces[0]["agent_type"] == "researcher"

    def test_get_session_flow(self, sample_logger):
        """Test getting session flow."""
        debugger = SessionDebugger(sample_logger)

        flow = debugger.get_session_flow()

        # Should include SESSION_START, AGENT_SPAWN, AGENT_COMPLETE, ERROR, SESSION_END
        assert len(flow) == 5

        event_types = [item["event_type"] for item in flow]
        assert EventType.SESSION_START in event_types
        assert EventType.SESSION_END in event_types
        assert EventType.AGENT_SPAWN in event_types
        assert EventType.ERROR in event_types

    def test_print_summary(self, sample_logger):
        """Test printing summary."""
        debugger = SessionDebugger(sample_logger)

        summary = debugger.print_summary()

        assert isinstance(summary, str)
        assert "SESSION DEBUG SUMMARY" in summary
        assert "test-123" in summary
        assert "Total Events: 7" in summary
