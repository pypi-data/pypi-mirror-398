"""
Structured logging for Claude Agent Framework.

Provides JSON-based structured logging with event types, session tracking,
and comprehensive metadata for debugging and analysis.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Types of events that can be logged."""

    SESSION_START = "session_start"
    SESSION_END = "session_end"
    AGENT_SPAWN = "agent_spawn"
    AGENT_COMPLETE = "agent_complete"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    PLUGIN_HOOK = "plugin_hook"
    CUSTOM = "custom"


class LogEvent(BaseModel):
    """Structured log event model."""

    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event: EventType
    session_id: str | None = None
    message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    level: str = "INFO"

    def to_json(self) -> str:
        """Convert to JSON string."""
        return self.model_dump_json()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()


class EventLogger:
    """
    Structured event logger for agent sessions.

    Provides:
    - JSON-based structured logging
    - Event type classification
    - Session tracking
    - File and console output
    - Configurable log levels
    """

    def __init__(
        self,
        session_id: str | None = None,
        log_file: Path | str | None = None,
        console_output: bool = True,
        log_level: str = "INFO",
    ) -> None:
        """
        Initialize event logger.

        Args:
            session_id: Optional session identifier
            log_file: Optional file path for log output
            console_output: Whether to output to console
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.session_id = session_id
        self.log_file = Path(log_file) if log_file else None
        self.console_output = console_output
        self.log_level = getattr(logging, log_level.upper())

        # Setup Python logger
        self._logger = logging.getLogger(f"claude_agent_framework.{session_id or 'default'}")
        self._logger.setLevel(self.log_level)
        self._logger.handlers.clear()

        # Add console handler if enabled
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(
                logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            )
            self._logger.addHandler(console_handler)

        # Add file handler if log file specified
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(logging.Formatter("%(message)s"))  # JSON only
            self._logger.addHandler(file_handler)

        # Event storage for analysis
        self._events: list[LogEvent] = []

    def log_event(
        self,
        event: EventType,
        message: str | None = None,
        level: str = "INFO",
        **metadata: Any,
    ) -> LogEvent:
        """
        Log a structured event.

        Args:
            event: Event type
            message: Optional message
            level: Log level
            **metadata: Additional metadata

        Returns:
            LogEvent object
        """
        log_event = LogEvent(
            event=event, session_id=self.session_id, message=message, level=level, metadata=metadata
        )

        # Store event
        self._events.append(log_event)

        # Log to Python logger
        log_method = getattr(self._logger, level.lower())
        log_method(log_event.to_json())

        return log_event

    def session_start(self, architecture: str, **metadata: Any) -> LogEvent:
        """Log session start event."""
        return self.log_event(
            EventType.SESSION_START,
            f"Session started with {architecture} architecture",
            architecture=architecture,
            **metadata,
        )

    def session_end(self, **metadata: Any) -> LogEvent:
        """Log session end event."""
        return self.log_event(EventType.SESSION_END, "Session ended", **metadata)

    def agent_spawn(
        self, agent_type: str, agent_prompt: str | None = None, **metadata: Any
    ) -> LogEvent:
        """Log agent spawn event."""
        return self.log_event(
            EventType.AGENT_SPAWN,
            f"Spawned {agent_type} agent",
            agent_type=agent_type,
            agent_prompt=agent_prompt,
            **metadata,
        )

    def agent_complete(self, agent_type: str, **metadata: Any) -> LogEvent:
        """Log agent completion event."""
        return self.log_event(
            EventType.AGENT_COMPLETE,
            f"Agent {agent_type} completed",
            agent_type=agent_type,
            **metadata,
        )

    def tool_call(
        self, tool_name: str, tool_input: dict[str, Any] | None = None, **metadata: Any
    ) -> LogEvent:
        """Log tool call event."""
        return self.log_event(
            EventType.TOOL_CALL,
            f"Tool called: {tool_name}",
            tool_name=tool_name,
            tool_input=tool_input,
            **metadata,
        )

    def tool_result(self, tool_name: str, success: bool = True, **metadata: Any) -> LogEvent:
        """Log tool result event."""
        return self.log_event(
            EventType.TOOL_RESULT,
            f"Tool {tool_name} {'succeeded' if success else 'failed'}",
            tool_name=tool_name,
            success=success,
            **metadata,
        )

    def error(self, error: Exception, **metadata: Any) -> LogEvent:
        """Log error event."""
        return self.log_event(
            EventType.ERROR,
            f"Error: {str(error)}",
            level="ERROR",
            error_type=type(error).__name__,
            error_message=str(error),
            **metadata,
        )

    def plugin_hook(self, hook_name: str, plugin_name: str, **metadata: Any) -> LogEvent:
        """Log plugin hook execution."""
        return self.log_event(
            EventType.PLUGIN_HOOK,
            f"Plugin hook: {plugin_name}.{hook_name}",
            hook_name=hook_name,
            plugin_name=plugin_name,
            **metadata,
        )

    def custom(self, message: str, level: str = "INFO", **metadata: Any) -> LogEvent:
        """Log custom event."""
        return self.log_event(EventType.CUSTOM, message, level=level, **metadata)

    def get_events(
        self, event_type: EventType | None = None, level: str | None = None
    ) -> list[LogEvent]:
        """
        Get logged events with optional filtering.

        Args:
            event_type: Filter by event type
            level: Filter by log level

        Returns:
            List of LogEvent objects
        """
        events = self._events

        if event_type:
            events = [e for e in events if e.event == event_type]

        if level:
            events = [e for e in events if e.level == level]

        return events

    def get_event_summary(self) -> dict[str, Any]:
        """
        Get summary statistics of logged events.

        Returns:
            Dictionary with event counts and statistics
        """
        event_counts = {}
        for event in self._events:
            event_counts[event.event] = event_counts.get(event.event, 0) + 1

        level_counts = {}
        for event in self._events:
            level_counts[event.level] = level_counts.get(event.level, 0) + 1

        return {
            "total_events": len(self._events),
            "event_counts": event_counts,
            "level_counts": level_counts,
            "session_id": self.session_id,
            "first_event": self._events[0].timestamp if self._events else None,
            "last_event": self._events[-1].timestamp if self._events else None,
        }

    def export_json(self, output_file: Path | str) -> None:
        """
        Export all events to JSON file.

        Args:
            output_file: Output file path
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        events_data = [event.to_dict() for event in self._events]

        with output_path.open("w") as f:
            json.dump(
                {
                    "session_id": self.session_id,
                    "events": events_data,
                    "summary": self.get_event_summary(),
                },
                f,
                indent=2,
            )

    def clear_events(self) -> None:
        """Clear stored events."""
        self._events.clear()
