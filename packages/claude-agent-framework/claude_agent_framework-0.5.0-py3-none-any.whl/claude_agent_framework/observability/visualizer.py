"""
Session visualization for Claude Agent Framework.

Generates interactive HTML visualizations of agent sessions including
dashboards, timelines, and tool call graphs.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from claude_agent_framework.observability.logger import EventLogger, EventType, LogEvent


class SessionVisualizer:
    """
    Generate interactive HTML visualizations of agent sessions.

    Provides:
    - Session dashboard with overview statistics
    - Timeline visualization of events
    - Tool call graph and analysis
    - Export to static HTML
    """

    def __init__(self, logger: EventLogger | None = None) -> None:
        """
        Initialize session visualizer.

        Args:
            logger: Optional EventLogger instance
        """
        self.logger = logger
        self._events: list[LogEvent] = logger.get_events() if logger else []

        # Setup Jinja2 environment
        template_dir = Path(__file__).parent / "templates"
        self._env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def load_events(self, events: list[LogEvent]) -> None:
        """
        Load events from list.

        Args:
            events: List of LogEvent objects
        """
        self._events = events

    def load_from_json(self, json_file: Path | str) -> None:
        """
        Load events from exported JSON file.

        Args:
            json_file: Path to JSON file
        """
        with open(json_file) as f:
            data = json.load(f)
            self._events = [LogEvent(**event) for event in data["events"]]

    def _calculate_statistics(self) -> dict[str, Any]:
        """Calculate session statistics."""
        if not self._events:
            return {}

        # Event counts by type
        event_counts = defaultdict(int)
        for event in self._events:
            event_counts[event.event] += 1

        # Level counts
        level_counts = defaultdict(int)
        for event in self._events:
            level_counts[event.level] += 1

        # Agent statistics
        agent_spawns = [e for e in self._events if e.event == EventType.AGENT_SPAWN]
        agent_types = defaultdict(int)
        for event in agent_spawns:
            agent_type = event.metadata.get("agent_type", "unknown")
            agent_types[agent_type] += 1

        # Tool statistics
        tool_calls = [e for e in self._events if e.event == EventType.TOOL_CALL]
        tool_counts = defaultdict(int)
        for event in tool_calls:
            tool_name = event.metadata.get("tool_name", "unknown")
            tool_counts[tool_name] += 1

        # Error statistics
        errors = [e for e in self._events if e.event == EventType.ERROR]
        error_types = defaultdict(int)
        for event in errors:
            error_type = event.metadata.get("error_type", "unknown")
            error_types[error_type] += 1

        # Time calculation
        first_event = min(self._events, key=lambda e: e.timestamp)
        last_event = max(self._events, key=lambda e: e.timestamp)

        first_time = datetime.fromisoformat(first_event.timestamp.replace("Z", "+00:00"))
        last_time = datetime.fromisoformat(last_event.timestamp.replace("Z", "+00:00"))
        duration_seconds = (last_time - first_time).total_seconds()

        return {
            "total_events": len(self._events),
            "event_counts": dict(event_counts),
            "level_counts": dict(level_counts),
            "agent_types": dict(agent_types),
            "tool_counts": dict(tool_counts),
            "error_types": dict(error_types),
            "total_agents": sum(agent_types.values()),
            "total_tools": sum(tool_counts.values()),
            "total_errors": len(errors),
            "duration_seconds": duration_seconds,
            "first_event_time": first_event.timestamp,
            "last_event_time": last_event.timestamp,
            "session_id": self._events[0].session_id if self._events else None,
        }

    def _prepare_timeline_data(self) -> list[dict[str, Any]]:
        """Prepare data for timeline visualization."""
        timeline_data = []

        for event in self._events:
            timeline_data.append(
                {
                    "timestamp": event.timestamp,
                    "event_type": event.event,
                    "level": event.level,
                    "message": event.message or "",
                    "metadata": event.metadata,
                }
            )

        return timeline_data

    def _prepare_tool_graph_data(self) -> dict[str, Any]:
        """Prepare data for tool call graph."""
        tool_calls = [e for e in self._events if e.event == EventType.TOOL_CALL]

        # Tool call timeline
        tool_timeline = []
        for event in tool_calls:
            tool_timeline.append(
                {
                    "timestamp": event.timestamp,
                    "tool_name": event.metadata.get("tool_name", "unknown"),
                    "tool_input": event.metadata.get("tool_input", {}),
                }
            )

        # Tool call counts
        tool_counts = defaultdict(int)
        for call in tool_timeline:
            tool_counts[call["tool_name"]] += 1

        return {
            "tool_timeline": tool_timeline,
            "tool_counts": dict(tool_counts),
            "total_calls": len(tool_timeline),
        }

    def generate_dashboard(self, output_file: Path | str | None = None) -> str:
        """
        Generate interactive dashboard HTML.

        Args:
            output_file: Optional file path to save HTML

        Returns:
            HTML string
        """
        stats = self._calculate_statistics()
        timeline_data = self._prepare_timeline_data()
        tool_data = self._prepare_tool_graph_data()

        template = self._env.get_template("dashboard.html")
        html = template.render(
            stats=stats,
            timeline_data=timeline_data,
            tool_data=tool_data,
            events=self._events,
        )

        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html)

        return html

    def generate_timeline(self, output_file: Path | str | None = None) -> str:
        """
        Generate timeline visualization HTML.

        Args:
            output_file: Optional file path to save HTML

        Returns:
            HTML string
        """
        timeline_data = self._prepare_timeline_data()
        stats = self._calculate_statistics()

        template = self._env.get_template("timeline.html")
        html = template.render(timeline_data=timeline_data, stats=stats)

        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html)

        return html

    def generate_tool_graph(self, output_file: Path | str | None = None) -> str:
        """
        Generate tool call graph HTML.

        Args:
            output_file: Optional file path to save HTML

        Returns:
            HTML string
        """
        tool_data = self._prepare_tool_graph_data()
        stats = self._calculate_statistics()

        template = self._env.get_template("tool_graph.html")
        html = template.render(tool_data=tool_data, stats=stats)

        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html)

        return html

    def generate_full_report(self, output_dir: Path | str) -> dict[str, Path]:
        """
        Generate complete visualization report with all components.

        Args:
            output_dir: Directory to save HTML files

        Returns:
            Dictionary mapping report types to file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        files = {}

        # Generate dashboard
        dashboard_file = output_path / "dashboard.html"
        self.generate_dashboard(dashboard_file)
        files["dashboard"] = dashboard_file

        # Generate timeline
        timeline_file = output_path / "timeline.html"
        self.generate_timeline(timeline_file)
        files["timeline"] = timeline_file

        # Generate tool graph
        tool_graph_file = output_path / "tool_graph.html"
        self.generate_tool_graph(tool_graph_file)
        files["tool_graph"] = tool_graph_file

        # Export events JSON
        events_file = output_path / "events.json"
        if self.logger:
            self.logger.export_json(events_file)
        else:
            events_data = [event.to_dict() for event in self._events]
            with events_file.open("w") as f:
                json.dump(
                    {"events": events_data, "summary": self._calculate_statistics()}, f, indent=2
                )
        files["events"] = events_file

        return files
