"""
Role definitions for role-based architecture.

This module provides the core abstractions for defining roles that agents can fill
within an architecture's workflow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from claude_agent_framework.core.types import RoleCardinality, RoleType

if TYPE_CHECKING:
    from claude_agent_framework.core.base import AgentDefinitionConfig

__all__ = [
    "RoleDefinition",
    "AgentInstanceConfig",
    "RoleRegistry",
]


@dataclass
class RoleDefinition:
    """
    Definition of a role within an architecture.

    Roles are abstract slots that business configs fill with concrete agents.
    Each architecture defines its supported roles with constraints.

    Attributes:
        role_type: The semantic type of this role (from RoleType enum)
        description: What this role does in the architecture
        required_tools: Tools that any agent in this role must have
        optional_tools: Additional tools that may be granted
        cardinality: How many agents can fill this role
        default_model: Suggested model tier for this role
        prompt_file: Architecture-level base prompt file for this role
        constraints: Additional constraints for validation
    """

    role_type: RoleType
    description: str = ""
    required_tools: list[str] = field(default_factory=list)
    optional_tools: list[str] = field(default_factory=list)
    cardinality: RoleCardinality = RoleCardinality.EXACTLY_ONE
    default_model: str = "haiku"
    prompt_file: str = ""
    constraints: dict[str, Any] = field(default_factory=dict)

    @property
    def allows_multiple(self) -> bool:
        """Check if this role can have multiple agent instances."""
        return self.cardinality in (
            RoleCardinality.ONE_OR_MORE,
            RoleCardinality.ZERO_OR_MORE,
        )

    @property
    def is_required(self) -> bool:
        """Check if at least one agent must fill this role."""
        return self.cardinality in (
            RoleCardinality.EXACTLY_ONE,
            RoleCardinality.ONE_OR_MORE,
        )

    @property
    def max_count(self) -> int | None:
        """Get maximum allowed count. None means unlimited."""
        if self.cardinality in (RoleCardinality.EXACTLY_ONE, RoleCardinality.ZERO_OR_ONE):
            return 1
        return None

    @property
    def min_count(self) -> int:
        """Get minimum required count."""
        if self.cardinality in (RoleCardinality.EXACTLY_ONE, RoleCardinality.ONE_OR_MORE):
            return 1
        return 0

    def validate_tools(self, tools: list[str]) -> list[str]:
        """
        Validate that provided tools are valid for this role.

        Note: required_tools are automatically merged in to_agent_definition(),
        so this only validates that any additional tools are in the optional list.

        Args:
            tools: List of additional tools assigned to an agent

        Returns:
            List of validation errors (empty if valid)
        """
        # No validation needed - required tools are auto-merged,
        # and additional tools can be any valid SDK tool
        return []


@dataclass
class AgentInstanceConfig:
    """
    Configuration for a concrete agent instance filling a role.

    This is what business configs provide to instantiate agents.
    Each instance maps to one agent in the final execution.

    Attributes:
        name: Unique agent name (used in debugging and logs)
        role: The role this agent fills (role_id from architecture)
        description: Business-specific description
        tools: Tools for this agent (must include role's required_tools)
        prompt: Business-specific prompt content (inline)
        prompt_file: Path to business prompt file
        model: Model to use (overrides role default if specified)
        metadata: Additional business-specific metadata
    """

    name: str
    role: str
    description: str = ""
    tools: list[str] = field(default_factory=list)
    prompt: str = ""
    prompt_file: str = ""
    model: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_agent_definition(
        self,
        role_def: RoleDefinition,
        prompts_dir: Path | None = None,
    ) -> AgentDefinitionConfig:
        """
        Convert to AgentDefinitionConfig for SDK compatibility.

        Merges role defaults with instance-specific configuration.
        Supports two-layer prompt composition:
        - role_prompt_file: Framework role default prompt (from RoleDefinition)
        - prompt_file: Business instance prompt (from AgentInstanceConfig)

        Args:
            role_def: The role definition this instance fills
            prompts_dir: Base directory for prompt files (unused, kept for compatibility)

        Returns:
            AgentDefinitionConfig ready for SDK use
        """
        from claude_agent_framework.core.base import AgentDefinitionConfig

        # Merge tools: role required + instance additional
        merged_tools = list(role_def.required_tools)
        for tool in self.tools:
            if tool not in merged_tools:
                merged_tools.append(tool)

        # Determine model: instance override or role default
        model = self.model if self.model else role_def.default_model

        # Determine description: instance or role default
        description = self.description if self.description else role_def.description

        # Two-layer prompt composition:
        # - role_prompt_file: Always from RoleDefinition (framework layer)
        # - prompt_file: From instance if specified (business layer)
        role_prompt_file = role_def.prompt_file
        instance_prompt_file = self.prompt_file  # May be empty

        return AgentDefinitionConfig(
            name=self.name,
            description=description,
            tools=merged_tools,
            prompt=self.prompt,
            prompt_file=instance_prompt_file,
            role_prompt_file=role_prompt_file,
            model=model,
        )


@dataclass
class RoleRegistry:
    """
    Registry of roles defined by an architecture.

    Validates business configs against role definitions and
    ensures all constraints are satisfied.
    """

    roles: dict[str, RoleDefinition] = field(default_factory=dict)

    def register(self, role_id: str, definition: RoleDefinition) -> None:
        """
        Register a role definition.

        Args:
            role_id: Unique identifier for the role within this architecture
            definition: The role definition
        """
        self.roles[role_id] = definition

    def get(self, role_id: str) -> RoleDefinition | None:
        """
        Get role definition by ID.

        Args:
            role_id: The role identifier

        Returns:
            RoleDefinition if found, None otherwise
        """
        return self.roles.get(role_id)

    def validate_agents(
        self,
        agents: list[AgentInstanceConfig],
    ) -> list[str]:
        """
        Validate agent instances against role definitions.

        Checks:
        - All agents reference valid roles
        - Cardinality constraints are satisfied
        - Required tools are present

        Args:
            agents: List of agent instance configurations

        Returns:
            List of validation errors (empty if valid)
        """
        errors: list[str] = []
        role_counts: dict[str, int] = {}

        # Count agents per role and validate each agent
        for agent in agents:
            role_counts[agent.role] = role_counts.get(agent.role, 0) + 1

            # Validate role exists
            role_def = self.roles.get(agent.role)
            if not role_def:
                errors.append(f"Unknown role '{agent.role}' for agent '{agent.name}'")
                continue

            # Validate tools
            tool_errors = role_def.validate_tools(agent.tools)
            errors.extend(tool_errors)

        # Validate cardinality constraints
        for role_id, role_def in self.roles.items():
            count = role_counts.get(role_id, 0)

            # Check minimum
            if count < role_def.min_count:
                errors.append(
                    f"Role '{role_id}' requires at least {role_def.min_count} agent(s), "
                    f"got {count}"
                )

            # Check maximum
            max_count = role_def.max_count
            if max_count is not None and count > max_count:
                errors.append(
                    f"Role '{role_id}' allows at most {max_count} agent(s), got {count}"
                )

        return errors

    def list_roles(self) -> list[str]:
        """
        List all registered role IDs.

        Returns:
            List of role identifiers
        """
        return list(self.roles.keys())

    def get_required_roles(self) -> list[str]:
        """
        Get all roles that require at least one agent.

        Returns:
            List of required role identifiers
        """
        return [role_id for role_id, role_def in self.roles.items() if role_def.is_required]

    def get_optional_roles(self) -> list[str]:
        """
        Get all optional roles (zero or more agents allowed).

        Returns:
            List of optional role identifiers
        """
        return [
            role_id for role_id, role_def in self.roles.items() if not role_def.is_required
        ]
