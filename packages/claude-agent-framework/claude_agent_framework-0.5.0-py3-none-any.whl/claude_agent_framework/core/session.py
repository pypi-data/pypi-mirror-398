"""
Unified session management for architectures.

Provides AgentSession class that wraps architecture execution with:
- Lifecycle management (setup, execute, teardown)
- Logging and tracking
- Error handling
- Resource cleanup
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

from claude_agent_sdk import HookMatcher

from claude_agent_framework.config import FrameworkConfig, validate_api_key
from claude_agent_framework.utils import (
    SubagentTracker,
    TranscriptWriter,
    process_message,
    setup_session,
)

if TYPE_CHECKING:
    from claude_agent_framework.core.base import BaseArchitecture

logger = logging.getLogger(__name__)


class AgentSession:
    """
    Unified session management for any architecture.

    Handles:
    - SDK client lifecycle
    - Hook configuration
    - Logging and tracking
    - Resource cleanup

    Usage:
        arch = get_architecture("pipeline")()
        session = AgentSession(arch)

        async for msg in session.run("Implement feature X"):
            print(msg)
    """

    def __init__(
        self,
        architecture: BaseArchitecture,
        config: FrameworkConfig | None = None,
    ) -> None:
        """
        Initialize session with an architecture.

        Args:
            architecture: Architecture instance to use
            config: Framework configuration (uses default if None)
        """
        self.architecture = architecture
        self.config = config or FrameworkConfig()
        self._tracker: SubagentTracker | None = None
        self._transcript: TranscriptWriter | None = None
        self._session_dir: Path | None = None
        self._initialized = False

    async def setup(self) -> None:
        """Initialize session resources."""
        if self._initialized:
            return

        # Validate API key
        if not validate_api_key():
            raise RuntimeError(
                "ANTHROPIC_API_KEY environment variable is not set. Please set it before running."
            )

        # Ensure directories exist
        self.config.ensure_directories()

        # Setup session logging
        session_dir, transcript_path, tool_log_path = setup_session(self.config.logs_dir)
        self._session_dir = session_dir

        # Initialize utilities
        self._transcript = TranscriptWriter(transcript_path)
        self._tracker = SubagentTracker(tool_log_path, self._transcript)

        # Setup architecture
        await self.architecture.setup()

        self._initialized = True
        logger.info(f"Session initialized: {session_dir}")

    async def teardown(self) -> None:
        """Cleanup session resources."""
        if not self._initialized:
            return

        # Cleanup architecture
        await self.architecture.teardown()

        # Close utilities
        if self._transcript:
            self._transcript.close()
        if self._tracker:
            self._tracker.close()

        self._initialized = False
        if self._session_dir:
            logger.info(f"Session saved to: {self._session_dir}")

    def _build_hooks(self) -> dict[str, list]:
        """Build hook configuration combining architecture and tracker hooks."""
        hooks: dict[str, list] = {}

        # Add tracker hooks
        if self._tracker:
            hooks["PreToolUse"] = [
                HookMatcher(
                    matcher=None,
                    hooks=[self._tracker.pre_tool_use_hook],
                )
            ]
            hooks["PostToolUse"] = [
                HookMatcher(
                    matcher=None,
                    hooks=[self._tracker.post_tool_use_hook],
                )
            ]

        # Merge architecture-specific hooks
        arch_hooks = self.architecture.get_hooks()
        for hook_type, matchers in arch_hooks.items():
            if hook_type not in hooks:
                hooks[hook_type] = []
            hooks[hook_type].extend(matchers)

        return hooks

    async def run(self, prompt: str) -> AsyncIterator[Any]:
        """
        Run the session with given prompt.

        Args:
            prompt: User input prompt

        Yields:
            Messages from the architecture execution
        """
        # Ensure setup is done
        await self.setup()

        # Log user input
        if self._transcript:
            self._transcript.user_input(prompt)

        try:
            # Execute architecture
            async for msg in self.architecture.execute(
                prompt,
                tracker=self._tracker,
                transcript=self._transcript,
            ):
                # Process and yield message
                if self._tracker and self._transcript:
                    process_message(msg, self._tracker, self._transcript)
                yield msg

        except Exception as e:
            logger.error(f"Session error: {e}")
            raise

    async def query(self, prompt: str) -> list[Any]:
        """
        Convenience method to run and collect all messages.

        Args:
            prompt: User input prompt

        Returns:
            List of all messages from execution
        """
        messages = []
        async for msg in self.run(prompt):
            messages.append(msg)
        return messages

    async def __aenter__(self) -> AgentSession:
        """Async context manager entry."""
        await self.setup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.teardown()

    @property
    def session_dir(self) -> Path | None:
        """Get current session directory."""
        return self._session_dir

    @property
    def tracker(self) -> SubagentTracker | None:
        """Get tracker instance."""
        return self._tracker

    @property
    def transcript(self) -> TranscriptWriter | None:
        """Get transcript writer instance."""
        return self._transcript


class CompositeSession:
    """
    Session that combines multiple architectures in sequence.

    Usage:
        # Pipeline followed by Critic-Actor
        session = CompositeSession([
            get_architecture("pipeline")(),
            get_architecture("critic_actor")(),
        ])

        async for msg in session.run("Implement and refine feature X"):
            print(msg)
    """

    def __init__(
        self,
        architectures: list[BaseArchitecture],
        config: FrameworkConfig | None = None,
    ) -> None:
        """
        Initialize composite session.

        Args:
            architectures: List of architectures to execute in order
            config: Framework configuration
        """
        self.architectures = architectures
        self.config = config or FrameworkConfig()
        self._sessions: list[AgentSession] = []
        self._initialized = False

    async def setup(self) -> None:
        """Initialize all architecture sessions."""
        if self._initialized:
            return

        for arch in self.architectures:
            session = AgentSession(arch, self.config)
            await session.setup()
            self._sessions.append(session)

        self._initialized = True

    async def teardown(self) -> None:
        """Cleanup all sessions."""
        for session in reversed(self._sessions):
            await session.teardown()
        self._sessions.clear()
        self._initialized = False

    async def run(self, prompt: str) -> AsyncIterator[Any]:
        """
        Run all architectures in sequence.

        The output of each architecture becomes input for the next.

        Args:
            prompt: Initial user prompt

        Yields:
            Messages from all architecture executions
        """
        await self.setup()

        current_input = prompt

        for i, session in enumerate(self._sessions):
            logger.info(
                f"Running architecture {i + 1}/{len(self._sessions)}: {session.architecture.name}"
            )

            async for msg in session.run(current_input):
                yield msg

            # Use architecture result as next input
            result = session.architecture.get_result()
            if result:
                current_input = str(result)

    async def __aenter__(self) -> CompositeSession:
        await self.setup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.teardown()
