"""
Interactive debugging tools for Claude Agent Framework.

Provides debugging utilities for analyzing agent sessions,
inspecting events, and troubleshooting issues.
"""

from __future__ import annotations

from typing import Any

from claude_agent_framework.observability.logger import EventLogger, EventType, LogEvent


class SessionDebugger:
    """
    Interactive debugger for agent sessions.

    Provides:
    - Event inspection and filtering
    - Error analysis
    - Tool call tracing
    - Agent execution flow analysis
    """

    def __init__(self, logger: EventLogger) -> None:
        """
        Initialize session debugger.

        Args:
            logger: EventLogger instance
        """
        self.logger = logger
        self._events = logger.get_events()

    def inspect_event(self, index: int) -> dict[str, Any]:
        """
        Inspect a specific event by index.

        Args:
            index: Event index

        Returns:
            Event details as dictionary
        """
        if not (0 <= index < len(self._events)):
            raise ValueError(f"Invalid event index: {index}")

        event = self._events[index]
        return {
            "index": index,
            "timestamp": event.timestamp,
            "event_type": event.event,
            "level": event.level,
            "message": event.message,
            "metadata": event.metadata,
            "session_id": event.session_id,
        }

    def find_events(
        self,
        event_type: EventType | None = None,
        level: str | None = None,
        search_term: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Find events matching criteria.

        Args:
            event_type: Filter by event type
            level: Filter by log level
            search_term: Search in message and metadata

        Returns:
            List of matching events with indices
        """
        results = []

        for i, event in enumerate(self._events):
            # Type filter
            if event_type and event.event != event_type:
                continue

            # Level filter
            if level and event.level != level:
                continue

            # Search term
            if search_term:
                search_lower = search_term.lower()
                message_match = event.message and search_lower in event.message.lower()
                metadata_match = search_lower in str(event.metadata).lower()

                if not (message_match or metadata_match):
                    continue

            results.append(
                {
                    "index": i,
                    "timestamp": event.timestamp,
                    "event_type": event.event,
                    "level": event.level,
                    "message": event.message,
                    "metadata": event.metadata,
                }
            )

        return results

    def analyze_errors(self) -> dict[str, Any]:
        """
        Analyze all errors in the session.

        Returns:
            Error analysis report
        """
        errors = self.logger.get_events(EventType.ERROR)

        if not errors:
            return {"error_count": 0, "errors": []}

        error_types = {}
        error_details = []

        for i, error in enumerate(errors):
            error_type = error.metadata.get("error_type", "unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1

            error_details.append(
                {
                    "index": i,
                    "timestamp": error.timestamp,
                    "error_type": error_type,
                    "error_message": error.metadata.get("error_message", ""),
                    "message": error.message,
                    "metadata": error.metadata,
                }
            )

        return {
            "error_count": len(errors),
            "error_types": error_types,
            "errors": error_details,
        }

    def trace_tool_calls(self, tool_name: str | None = None) -> list[dict[str, Any]]:
        """
        Trace tool calls throughout the session.

        Args:
            tool_name: Optional tool name filter

        Returns:
            List of tool call traces
        """
        tool_calls = []

        for i, event in enumerate(self._events):
            if event.event == EventType.TOOL_CALL:
                call_tool = event.metadata.get("tool_name", "")

                if tool_name and call_tool != tool_name:
                    continue

                # Find corresponding result
                result_event = None
                for j in range(i + 1, min(i + 10, len(self._events))):
                    if (
                        self._events[j].event == EventType.TOOL_RESULT
                        and self._events[j].metadata.get("tool_name") == call_tool
                    ):
                        result_event = self._events[j]
                        break

                tool_calls.append(
                    {
                        "call_index": i,
                        "tool_name": call_tool,
                        "timestamp": event.timestamp,
                        "input": event.metadata.get("tool_input", {}),
                        "result": result_event.metadata if result_event else None,
                        "success": result_event.metadata.get("success", False)
                        if result_event
                        else None,
                    }
                )

        return tool_calls

    def trace_agent_execution(self, agent_type: str | None = None) -> list[dict[str, Any]]:
        """
        Trace agent execution flow.

        Args:
            agent_type: Optional agent type filter

        Returns:
            List of agent execution traces
        """
        agent_traces = []

        for i, event in enumerate(self._events):
            if event.event == EventType.AGENT_SPAWN:
                spawn_agent = event.metadata.get("agent_type", "")

                if agent_type and spawn_agent != agent_type:
                    continue

                # Find corresponding completion
                complete_event = None
                for j in range(i + 1, len(self._events)):
                    if (
                        self._events[j].event == EventType.AGENT_COMPLETE
                        and self._events[j].metadata.get("agent_type") == spawn_agent
                    ):
                        complete_event = self._events[j]
                        break

                agent_traces.append(
                    {
                        "spawn_index": i,
                        "agent_type": spawn_agent,
                        "spawn_timestamp": event.timestamp,
                        "complete_timestamp": complete_event.timestamp if complete_event else None,
                        "metadata": event.metadata,
                        "result": complete_event.metadata if complete_event else None,
                    }
                )

        return agent_traces

    def get_session_flow(self) -> list[dict[str, Any]]:
        """
        Get high-level session execution flow.

        Returns:
            Ordered list of major session events
        """
        flow = []

        for i, event in enumerate(self._events):
            if event.event in [
                EventType.SESSION_START,
                EventType.SESSION_END,
                EventType.AGENT_SPAWN,
                EventType.AGENT_COMPLETE,
                EventType.ERROR,
            ]:
                flow.append(
                    {
                        "index": i,
                        "timestamp": event.timestamp,
                        "event_type": event.event,
                        "message": event.message,
                        "key_metadata": self._extract_key_metadata(event),
                    }
                )

        return flow

    def _extract_key_metadata(self, event: LogEvent) -> dict[str, Any]:
        """Extract key metadata based on event type."""
        if event.event == EventType.AGENT_SPAWN:
            return {"agent_type": event.metadata.get("agent_type")}
        elif event.event == EventType.AGENT_COMPLETE:
            return {"agent_type": event.metadata.get("agent_type")}
        elif event.event == EventType.ERROR:
            return {
                "error_type": event.metadata.get("error_type"),
                "error_message": event.metadata.get("error_message"),
            }
        elif event.event == EventType.SESSION_START:
            return {"architecture": event.metadata.get("architecture")}

        return {}

    def print_summary(self) -> str:
        """
        Generate human-readable session summary.

        Returns:
            Formatted summary string
        """
        summary = self.logger.get_event_summary()

        lines = [
            "=" * 60,
            "SESSION DEBUG SUMMARY",
            "=" * 60,
            f"Session ID: {summary.get('session_id', 'N/A')}",
            f"Total Events: {summary['total_events']}",
            f"First Event: {summary.get('first_event', 'N/A')}",
            f"Last Event: {summary.get('last_event', 'N/A')}",
            "",
            "Event Counts:",
        ]

        for event_type, count in summary.get("event_counts", {}).items():
            lines.append(f"  {event_type}: {count}")

        lines.append("")
        lines.append("Log Levels:")
        for level, count in summary.get("level_counts", {}).items():
            lines.append(f"  {level}: {count}")

        lines.append("")
        lines.append("Errors:")
        error_analysis = self.analyze_errors()
        lines.append(f"  Total Errors: {error_analysis['error_count']}")
        for error_type, count in error_analysis.get("error_types", {}).items():
            lines.append(f"    {error_type}: {count}")

        lines.append("=" * 60)

        return "\n".join(lines)
