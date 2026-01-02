"""Tests for CLI commands."""

import json
from unittest.mock import MagicMock, patch

import pytest

from claude_agent_framework.cli import cmd_metrics, cmd_report, cmd_view


class TestCLICommands:
    """Test CLI command functions."""

    @pytest.fixture
    def sample_events_file(self, tmp_path):
        """Create a sample events JSON file."""
        events_data = {
            "session_id": "test-session-123",
            "events": [
                {
                    "timestamp": "2025-01-01T10:00:00Z",
                    "event": "session_start",
                    "session_id": "test-session-123",
                    "message": "Session started",
                    "metadata": {"architecture": "research"},
                    "level": "INFO",
                },
                {
                    "timestamp": "2025-01-01T10:01:00Z",
                    "event": "agent_spawn",
                    "session_id": "test-session-123",
                    "message": "Agent spawned",
                    "metadata": {"agent_type": "researcher"},
                    "level": "INFO",
                },
                {
                    "timestamp": "2025-01-01T10:02:00Z",
                    "event": "tool_call",
                    "session_id": "test-session-123",
                    "message": "Tool called",
                    "metadata": {"tool_name": "WebSearch"},
                    "level": "INFO",
                },
            ],
            "summary": {
                "total_events": 3,
                "event_counts": {
                    "session_start": 1,
                    "agent_spawn": 1,
                    "tool_call": 1,
                },
                "level_counts": {"INFO": 3},
                "session_id": "test-session-123",
            },
        }

        events_file = tmp_path / "events.json"
        with events_file.open("w") as f:
            json.dump(events_data, f)

        return events_file

    def test_cmd_metrics_success(self, sample_events_file, capsys):
        """Test metrics command with valid file."""
        args = MagicMock()
        args.session_file = str(sample_events_file)

        cmd_metrics(args)

        captured = capsys.readouterr()
        assert "SESSION METRICS" in captured.out
        assert "test-session-123" in captured.out
        assert "Total Events: 3" in captured.out

    def test_cmd_metrics_file_not_found(self, tmp_path, capsys):
        """Test metrics command with missing file."""
        args = MagicMock()
        args.session_file = str(tmp_path / "nonexistent.json")

        cmd_metrics(args)

        captured = capsys.readouterr()
        assert "Error" in captured.out
        assert "not found" in captured.out

    def test_cmd_metrics_invalid_json(self, tmp_path, capsys):
        """Test metrics command with invalid JSON."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("not valid json{")

        args = MagicMock()
        args.session_file = str(invalid_file)

        cmd_metrics(args)

        captured = capsys.readouterr()
        assert "Error" in captured.out
        assert "Invalid JSON" in captured.out

    @patch("claude_agent_framework.observability.SessionVisualizer")
    @patch("claude_agent_framework.cli.webbrowser")
    def test_cmd_view_success(
        self, mock_webbrowser, mock_visualizer, sample_events_file, tmp_path, capsys
    ):
        """Test view command success."""
        args = MagicMock()
        args.session_file = str(sample_events_file)
        args.output = str(tmp_path / "dashboard.html")
        args.no_browser = False

        # Mock visualizer
        mock_viz_instance = MagicMock()
        mock_visualizer.return_value = mock_viz_instance

        cmd_view(args)

        captured = capsys.readouterr()
        assert "Dashboard generated" in captured.out
        assert "Opening in browser" in captured.out

        # Verify visualizer was used correctly
        mock_viz_instance.load_from_json.assert_called_once()
        mock_viz_instance.generate_dashboard.assert_called_once()
        mock_webbrowser.open.assert_called_once()

    @patch("claude_agent_framework.observability.SessionVisualizer")
    def test_cmd_view_no_browser(self, mock_visualizer, sample_events_file, tmp_path, capsys):
        """Test view command without opening browser."""
        args = MagicMock()
        args.session_file = str(sample_events_file)
        args.output = str(tmp_path / "dashboard.html")
        args.no_browser = True

        # Mock visualizer
        mock_viz_instance = MagicMock()
        mock_visualizer.return_value = mock_viz_instance

        cmd_view(args)

        captured = capsys.readouterr()
        assert "Dashboard generated" in captured.out
        assert "Opening in browser" not in captured.out

    def test_cmd_view_file_not_found(self, tmp_path, capsys):
        """Test view command with missing file."""
        args = MagicMock()
        args.session_file = str(tmp_path / "nonexistent.json")
        args.output = None
        args.no_browser = True

        cmd_view(args)

        captured = capsys.readouterr()
        assert "Error" in captured.out
        assert "not found" in captured.out

    @patch("claude_agent_framework.observability.SessionVisualizer")
    @patch("claude_agent_framework.cli.webbrowser")
    def test_cmd_report_success(
        self, mock_webbrowser, mock_visualizer, sample_events_file, tmp_path, capsys
    ):
        """Test report command success."""
        args = MagicMock()
        args.session_file = str(sample_events_file)
        args.output = str(tmp_path / "report")
        args.no_browser = False

        # Mock visualizer
        mock_viz_instance = MagicMock()
        mock_visualizer.return_value = mock_viz_instance
        mock_viz_instance.generate_full_report.return_value = {
            "dashboard": tmp_path / "report" / "dashboard.html",
            "timeline": tmp_path / "report" / "timeline.html",
            "tool_graph": tmp_path / "report" / "tool_graph.html",
            "events": tmp_path / "report" / "events.json",
        }

        cmd_report(args)

        captured = capsys.readouterr()
        assert "Report generated" in captured.out
        assert "Generated files:" in captured.out
        assert "dashboard:" in captured.out
        assert "Opening dashboard in browser" in captured.out

        # Verify visualizer was used correctly
        mock_viz_instance.load_from_json.assert_called_once()
        mock_viz_instance.generate_full_report.assert_called_once()
        mock_webbrowser.open.assert_called_once()

    @patch("claude_agent_framework.observability.SessionVisualizer")
    def test_cmd_report_no_browser(self, mock_visualizer, sample_events_file, tmp_path, capsys):
        """Test report command without opening browser."""
        args = MagicMock()
        args.session_file = str(sample_events_file)
        args.output = str(tmp_path / "report")
        args.no_browser = True

        # Mock visualizer
        mock_viz_instance = MagicMock()
        mock_visualizer.return_value = mock_viz_instance
        mock_viz_instance.generate_full_report.return_value = {
            "dashboard": tmp_path / "report" / "dashboard.html",
            "timeline": tmp_path / "report" / "timeline.html",
        }

        cmd_report(args)

        captured = capsys.readouterr()
        assert "Report generated" in captured.out
        assert "Opening dashboard in browser" not in captured.out

    def test_cmd_report_file_not_found(self, tmp_path, capsys):
        """Test report command with missing file."""
        args = MagicMock()
        args.session_file = str(tmp_path / "nonexistent.json")
        args.output = None
        args.no_browser = True

        cmd_report(args)

        captured = capsys.readouterr()
        assert "Error" in captured.out
        assert "not found" in captured.out
