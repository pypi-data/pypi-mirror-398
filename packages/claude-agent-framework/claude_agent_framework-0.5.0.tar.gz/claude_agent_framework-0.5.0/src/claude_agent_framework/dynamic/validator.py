"""
Agent configuration validator for dynamic registration.

Validates agent configurations before they are registered dynamically.
"""

from __future__ import annotations

from typing import Any

# All available tools in Claude Agent Framework
ALLOWED_TOOLS = {
    # File operations
    "Read",
    "Write",
    "Edit",
    "Glob",
    "Grep",
    # Execution
    "Bash",
    "Task",
    # Web
    "WebSearch",
    "WebFetch",
    # Skills and other tools
    "Skill",
    "AskUserQuestion",
    "LSP",
    "NotebookEdit",
    "NotebookRead",
    "TodoWrite",
    "KillShell",
}

# Available models
ALLOWED_MODELS = {"haiku", "sonnet", "opus"}


class AgentConfigError(ValueError):
    """Raised when agent configuration is invalid."""

    pass


class AgentConfigValidator:
    """
    Validator for dynamic agent configurations.

    Ensures agent configs are valid before runtime registration.
    """

    @staticmethod
    def validate_name(name: str) -> None:
        """
        Validate agent name.

        Args:
            name: Agent name to validate

        Raises:
            AgentConfigError: If name is invalid
        """
        if not name:
            raise AgentConfigError("Agent name cannot be empty")

        if not isinstance(name, str):
            raise AgentConfigError(f"Agent name must be string, got {type(name)}")

        if not name.replace("_", "").replace("-", "").isalnum():
            raise AgentConfigError(
                f"Agent name must be alphanumeric with underscores/hyphens, got: {name}"
            )

        if name[0].isdigit():
            raise AgentConfigError(f"Agent name cannot start with digit: {name}")

    @staticmethod
    def validate_description(description: str) -> None:
        """
        Validate agent description.

        Args:
            description: Agent description to validate

        Raises:
            AgentConfigError: If description is invalid
        """
        if not description:
            raise AgentConfigError("Agent description cannot be empty")

        if not isinstance(description, str):
            raise AgentConfigError(f"Agent description must be string, got {type(description)}")

        if len(description) < 10:
            raise AgentConfigError(
                f"Agent description too short (min 10 chars): {len(description)}"
            )

    @staticmethod
    def validate_tools(tools: list[str]) -> None:
        """
        Validate agent tools list.

        Args:
            tools: List of tool names to validate

        Raises:
            AgentConfigError: If tools list is invalid
        """
        if not isinstance(tools, list):
            raise AgentConfigError(f"Tools must be a list, got {type(tools)}")

        if not tools:
            raise AgentConfigError("Agent must have at least one tool")

        invalid_tools = [t for t in tools if t not in ALLOWED_TOOLS]
        if invalid_tools:
            raise AgentConfigError(
                f"Invalid tools: {invalid_tools}. Allowed tools: {sorted(ALLOWED_TOOLS)}"
            )

    @staticmethod
    def validate_prompt(prompt: str) -> None:
        """
        Validate agent prompt.

        Args:
            prompt: Agent prompt to validate

        Raises:
            AgentConfigError: If prompt is invalid
        """
        if not prompt:
            raise AgentConfigError("Agent prompt cannot be empty")

        if not isinstance(prompt, str):
            raise AgentConfigError(f"Agent prompt must be string, got {type(prompt)}")

        if len(prompt) < 20:
            raise AgentConfigError(f"Agent prompt too short (min 20 chars): {len(prompt)}")

    @staticmethod
    def validate_model(model: str) -> None:
        """
        Validate model name.

        Args:
            model: Model name to validate

        Raises:
            AgentConfigError: If model is invalid
        """
        if not isinstance(model, str):
            raise AgentConfigError(f"Model must be string, got {type(model)}")

        if model not in ALLOWED_MODELS:
            raise AgentConfigError(
                f"Invalid model: {model}. Allowed models: {sorted(ALLOWED_MODELS)}"
            )

    @classmethod
    def validate_full(
        cls,
        name: str,
        description: str,
        tools: list[str],
        prompt: str,
        model: str = "haiku",
    ) -> None:
        """
        Validate full agent configuration.

        Args:
            name: Agent name
            description: Agent description
            tools: List of tool names
            prompt: Agent prompt
            model: Model name (default: haiku)

        Raises:
            AgentConfigError: If any field is invalid
        """
        cls.validate_name(name)
        cls.validate_description(description)
        cls.validate_tools(tools)
        cls.validate_prompt(prompt)
        cls.validate_model(model)


def validate_agent_config(config: dict[str, Any]) -> None:
    """
    Validate agent configuration dictionary.

    Args:
        config: Agent configuration dict with keys:
            - name (str): Agent name
            - description (str): Agent description
            - tools (list[str]): Tool names
            - prompt (str): Agent prompt
            - model (str, optional): Model name

    Raises:
        AgentConfigError: If configuration is invalid

    Example:
        >>> config = {
        ...     "name": "researcher",
        ...     "description": "Research data from web",
        ...     "tools": ["WebSearch", "Write"],
        ...     "prompt": "You are a research assistant...",
        ...     "model": "haiku"
        ... }
        >>> validate_agent_config(config)
    """
    required_fields = {"name", "description", "tools", "prompt"}
    missing_fields = required_fields - set(config.keys())

    if missing_fields:
        raise AgentConfigError(f"Missing required fields: {sorted(missing_fields)}")

    AgentConfigValidator.validate_full(
        name=config["name"],
        description=config["description"],
        tools=config["tools"],
        prompt=config["prompt"],
        model=config.get("model", "haiku"),
    )
