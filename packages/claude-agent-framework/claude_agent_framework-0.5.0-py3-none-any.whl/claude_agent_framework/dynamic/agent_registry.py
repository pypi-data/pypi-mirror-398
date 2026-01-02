"""
Dynamic agent registry for runtime agent management.

Provides the DynamicAgentRegistry class to add, remove, and manage
agents dynamically during architecture execution.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from claude_agent_framework.dynamic.validator import validate_agent_config

if TYPE_CHECKING:
    from claude_agent_sdk import AgentDefinition


class DynamicAgentRegistry:
    """
    Registry for dynamically registered agents.

    Manages agents that are added at runtime, separate from
    the statically defined agents in architecture classes.
    """

    def __init__(self) -> None:
        """Initialize empty dynamic agent registry."""
        self._agents: dict[str, AgentDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        tools: list[str],
        prompt: str,
        model: str = "haiku",
    ) -> None:
        """
        Register a new agent dynamically.

        Args:
            name: Unique agent name (used as subagent_type)
            description: Description of when to use this agent
            tools: List of allowed tool names
            prompt: Agent system prompt
            model: Model to use (default: haiku)

        Raises:
            AgentConfigError: If configuration is invalid
            ValueError: If agent name already exists

        Example:
            >>> registry = DynamicAgentRegistry()
            >>> registry.register(
            ...     name="researcher",
            ...     description="Research web data",
            ...     tools=["WebSearch", "Write"],
            ...     prompt="You are a research assistant...",
            ...     model="haiku"
            ... )
        """
        # Validate configuration
        validate_agent_config(
            {
                "name": name,
                "description": description,
                "tools": tools,
                "prompt": prompt,
                "model": model,
            }
        )

        # Check for duplicates
        if name in self._agents:
            raise ValueError(f"Agent '{name}' is already registered")

        # Create AgentDefinition
        from claude_agent_sdk import AgentDefinition

        self._agents[name] = AgentDefinition(
            description=description,
            tools=tools,
            prompt=prompt,
            model=model,
        )

    def unregister(self, name: str) -> None:
        """
        Remove a dynamically registered agent.

        Args:
            name: Agent name to remove

        Raises:
            KeyError: If agent not found

        Example:
            >>> registry.unregister("researcher")
        """
        if name not in self._agents:
            raise KeyError(f"Agent '{name}' not found in registry")

        del self._agents[name]

    def get(self, name: str) -> AgentDefinition | None:
        """
        Get agent definition by name.

        Args:
            name: Agent name

        Returns:
            AgentDefinition if found, None otherwise

        Example:
            >>> agent = registry.get("researcher")
            >>> if agent:
            ...     print(agent.description)
        """
        return self._agents.get(name)

    def list_agents(self) -> list[str]:
        """
        List all registered agent names.

        Returns:
            List of agent names

        Example:
            >>> registry.list_agents()
            ['researcher', 'analyst', 'writer']
        """
        return list(self._agents.keys())

    def get_all(self) -> dict[str, AgentDefinition]:
        """
        Get all registered agents.

        Returns:
            Dictionary mapping agent names to AgentDefinitions

        Example:
            >>> agents = registry.get_all()
            >>> for name, agent in agents.items():
            ...     print(f"{name}: {agent.description}")
        """
        return self._agents.copy()

    def clear(self) -> None:
        """
        Clear all dynamically registered agents.

        Example:
            >>> registry.clear()
            >>> registry.list_agents()
            []
        """
        self._agents.clear()

    def __len__(self) -> int:
        """Return number of registered agents."""
        return len(self._agents)

    def __contains__(self, name: str) -> bool:
        """Check if agent is registered."""
        return name in self._agents

    def __repr__(self) -> str:
        """String representation."""
        return f"DynamicAgentRegistry(agents={len(self._agents)})"
