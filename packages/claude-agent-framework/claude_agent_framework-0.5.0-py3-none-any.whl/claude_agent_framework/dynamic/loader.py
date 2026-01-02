"""
Dynamic architecture loader and creation.

Provides functionality to create custom architectures at runtime
without needing to define a new architecture class.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from claude_agent_framework.core.base import BaseArchitecture
from claude_agent_framework.core.roles import RoleDefinition
from claude_agent_framework.core.types import RoleCardinality, RoleType
from claude_agent_framework.dynamic.validator import validate_agent_config

if TYPE_CHECKING:
    from pathlib import Path

    from claude_agent_sdk import AgentDefinition

    from claude_agent_framework.utils import SubagentTracker, TranscriptWriter


def create_dynamic_architecture(
    name: str,
    description: str,
    agents: dict[str, dict[str, Any]],
    lead_prompt: str,
    lead_tools: list[str] | None = None,
    lead_model: str = "haiku",
) -> type[BaseArchitecture]:
    """
    Create a custom architecture class dynamically.

    This function generates a new architecture class at runtime, allowing
    users to create custom multi-agent workflows without defining a new
    architecture class.

    Args:
        name: Architecture name (used for registration)
        description: Architecture description
        agents: Dictionary of agent configurations, where each key is the
            agent name and value is a dict with:
            - description (str): Agent description
            - tools (list[str]): Tool names
            - prompt (str): Agent prompt
            - model (str, optional): Model name (default: haiku)
        lead_prompt: Lead agent system prompt
        lead_tools: Lead agent tools (default: ["Task"])
        lead_model: Lead agent model (default: haiku)

    Returns:
        Dynamically created architecture class

    Raises:
        ValueError: If configuration is invalid

    Example:
        >>> CustomArch = create_dynamic_architecture(
        ...     name="custom_pipeline",
        ...     description="Custom data processing pipeline",
        ...     agents={
        ...         "collector": {
        ...             "description": "Collect data from sources",
        ...             "tools": ["WebSearch", "Write"],
        ...             "prompt": "You collect data from web sources...",
        ...         },
        ...         "processor": {
        ...             "description": "Process collected data",
        ...             "tools": ["Read", "Write"],
        ...             "prompt": "You process and analyze data...",
        ...             "model": "sonnet",
        ...         },
        ...     },
        ...     lead_prompt="You coordinate data collection and processing..."
        ... )
        >>> from claude_agent_framework import init
        >>> session = init(CustomArch)
    """
    # Validate inputs
    if not name or not isinstance(name, str):
        raise ValueError("Architecture name must be non-empty string")

    if not description or not isinstance(description, str):
        raise ValueError("Architecture description must be non-empty string")

    if not agents or not isinstance(agents, dict):
        raise ValueError("Agents must be non-empty dictionary")

    if not lead_prompt or not isinstance(lead_prompt, str):
        raise ValueError("Lead prompt must be non-empty string")

    # Validate each agent configuration
    for agent_name, agent_config in agents.items():
        # Add name to config for validation
        full_config = {"name": agent_name, **agent_config}
        validate_agent_config(full_config)

    # Set defaults
    if lead_tools is None:
        lead_tools = ["Task"]

    # Create dynamic architecture class
    class DynamicArchitecture(BaseArchitecture):
        """Dynamically created architecture."""

        def __init__(
            self,
            prompts_dir: Path | None = None,
            files_dir: Path | None = None,
            **kwargs: Any,
        ):
            """Initialize dynamic architecture."""
            super().__init__(prompts_dir=prompts_dir, files_dir=files_dir, **kwargs)
            self._lead_prompt = lead_prompt
            self._lead_tools = lead_tools
            self._lead_model = lead_model
            self._agent_configs = agents

        def get_role_definitions(self) -> dict[str, RoleDefinition]:
            """
            Get role definitions for dynamic architecture.

            Dynamic architectures use a single "agent" role that accepts
            any number of agents with any tools.

            Returns:
                Dict with a single "agent" role that allows all agent types
            """
            return {
                "agent": RoleDefinition(
                    role_type=RoleType.SPECIALIST,
                    description="Dynamic agent role - accepts any configuration",
                    required_tools=[],
                    optional_tools=[],
                    cardinality=RoleCardinality.ZERO_OR_MORE,
                    default_model="haiku",
                ),
            }

        def get_agents(self) -> dict[str, AgentDefinition]:
            """
            Get agent definitions.

            Returns:
                Dictionary mapping agent names to AgentDefinitions
            """
            from claude_agent_sdk import AgentDefinition

            return {
                name: AgentDefinition(
                    description=config["description"],
                    tools=config["tools"],
                    prompt=config["prompt"],
                    model=config.get("model", "haiku"),
                )
                for name, config in self._agent_configs.items()
            }

        async def execute(
            self,
            prompt: str,
            tracker: SubagentTracker | None = None,
            transcript: TranscriptWriter | None = None,
        ) -> Any:
            """
            Execute the dynamic architecture.

            By default, this is a simple sequential execution pattern.
            For custom execution logic, users should subclass and override.

            Args:
                prompt: User prompt
                tracker: Subagent tracker
                transcript: Transcript writer

            Returns:
                Execution result
            """
            # Simple implementation: spawn all agents in sequence
            # Users can override this method for custom logic
            results = {}

            # Apply before_execute hooks
            prompt = self._apply_before_execute(prompt)

            for agent_name in self._agent_configs.keys():
                if tracker:
                    # Track agent execution
                    await tracker.spawn(
                        agent_type=agent_name,
                        agent_prompt=f"Execute task: {prompt}",
                    )

                # In a real implementation, would call the agent here
                # For now, just record that it would be called
                results[agent_name] = f"Would execute {agent_name}"

            # Apply after_execute hooks
            results = self._apply_after_execute(results)

            return results

    # Set class attributes
    DynamicArchitecture.name = name
    DynamicArchitecture.description = description
    DynamicArchitecture.__name__ = name
    DynamicArchitecture.__qualname__ = name

    return DynamicArchitecture


def load_architecture_from_config(config: dict[str, Any]) -> type[BaseArchitecture]:
    """
    Load architecture from configuration dictionary.

    Args:
        config: Configuration dictionary with keys:
            - name (str): Architecture name
            - description (str): Architecture description
            - agents (dict): Agent configurations
            - lead_prompt (str): Lead agent prompt
            - lead_tools (list[str], optional): Lead tools
            - lead_model (str, optional): Lead model

    Returns:
        Dynamically created architecture class

    Example:
        >>> config = {
        ...     "name": "my_arch",
        ...     "description": "My custom architecture",
        ...     "agents": {...},
        ...     "lead_prompt": "..."
        ... }
        >>> Arch = load_architecture_from_config(config)
    """
    required_fields = {"name", "description", "agents", "lead_prompt"}
    missing = required_fields - set(config.keys())
    if missing:
        raise ValueError(f"Missing required fields: {sorted(missing)}")

    return create_dynamic_architecture(
        name=config["name"],
        description=config["description"],
        agents=config["agents"],
        lead_prompt=config["lead_prompt"],
        lead_tools=config.get("lead_tools"),
        lead_model=config.get("lead_model", "haiku"),
    )
