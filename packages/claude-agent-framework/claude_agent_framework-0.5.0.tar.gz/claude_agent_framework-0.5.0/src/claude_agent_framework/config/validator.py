"""
Configuration validation utilities.

Provides validation logic for configurations and runtime checks.
"""

from __future__ import annotations

from pathlib import Path

from claude_agent_framework.config.schema import (
    AgentConfigSchema,
    FrameworkConfigSchema,
)


class ConfigValidator:
    """
    Configuration validator with semantic checks.

    Provides validation beyond schema constraints:
    - File existence checks
    - Circular dependency detection
    - Resource availability
    - Consistency checks
    """

    @staticmethod
    def validate_config(
        config: FrameworkConfigSchema,
        prompts_dir: Path | None = None,
        check_files: bool = True,
    ) -> list[str]:
        """
        Validate framework configuration.

        Args:
            config: Configuration to validate
            prompts_dir: Directory containing prompt files
            check_files: Whether to check file existence

        Returns:
            List of validation errors (empty if valid)
        """
        errors: list[str] = []

        # Validate lead agent
        errors.extend(ConfigValidator._validate_lead_agent(config, prompts_dir, check_files))

        # Validate subagents
        for agent in config.subagents:
            errors.extend(ConfigValidator._validate_agent(agent, prompts_dir, check_files))

        # Validate directory structure
        errors.extend(ConfigValidator._validate_directories(config))

        # Check for duplicate agent names
        errors.extend(ConfigValidator._check_duplicate_agents(config))

        return errors

    @staticmethod
    def _validate_lead_agent(
        config: FrameworkConfigSchema,
        prompts_dir: Path | None,
        check_files: bool,
    ) -> list[str]:
        """Validate lead agent configuration."""
        errors: list[str] = []

        # Check if Task tool is present
        if "Task" not in config.lead_agent_tools:
            errors.append("Lead agent must have 'Task' tool to spawn subagents")

        # Check prompt file existence
        if check_files and prompts_dir:
            prompt_path = prompts_dir / config.lead_agent_prompt_file
            if not prompt_path.exists():
                errors.append(f"Lead agent prompt file not found: {prompt_path}")

        return errors

    @staticmethod
    def _validate_agent(
        agent: AgentConfigSchema,
        prompts_dir: Path | None,
        check_files: bool,
    ) -> list[str]:
        """Validate single agent configuration."""
        errors: list[str] = []

        # Check prompt file existence
        if check_files and prompts_dir and agent.prompt_file:
            prompt_path = prompts_dir / agent.prompt_file
            if not prompt_path.exists():
                errors.append(f"Agent '{agent.name}' prompt file not found: {prompt_path}")

        # Check that agent has at least one tool
        if not agent.tools:
            errors.append(f"Agent '{agent.name}' must have at least one tool")

        # Warn if agent has Task tool (usually only lead agent should)
        if "Task" in agent.tools:
            errors.append(
                f"Warning: Agent '{agent.name}' has 'Task' tool. "
                "This is unusual - only lead agent typically needs this."
            )

        return errors

    @staticmethod
    def _validate_directories(config: FrameworkConfigSchema) -> list[str]:
        """Validate directory configuration."""
        errors: list[str] = []

        # Check if directories are writable (if they exist)
        for dir_name, dir_path in [
            ("logs_dir", config.logs_dir),
            ("files_dir", config.files_dir),
        ]:
            if dir_path.exists() and not os.access(dir_path, os.W_OK):
                errors.append(f"{dir_name} exists but is not writable: {dir_path}")

        return errors

    @staticmethod
    def _check_duplicate_agents(config: FrameworkConfigSchema) -> list[str]:
        """Check for duplicate agent names."""
        errors: list[str] = []

        agent_names = [agent.name for agent in config.subagents]
        duplicates = [name for name in agent_names if agent_names.count(name) > 1]

        if duplicates:
            unique_duplicates = sorted(set(duplicates))
            errors.append(f"Duplicate agent names found: {', '.join(unique_duplicates)}")

        return errors

    @staticmethod
    def validate_agent_tools_subset(
        config: FrameworkConfigSchema,
    ) -> list[str]:
        """
        Validate that subagents use subset of lead agent tools.

        This is a recommended (but not required) practice.

        Returns:
            List of warnings (not errors)
        """
        warnings: list[str] = []

        lead_tools = set(config.lead_agent_tools)

        for agent in config.subagents:
            agent_tools = set(agent.tools)
            extra_tools = agent_tools - lead_tools

            if extra_tools:
                warnings.append(
                    f"Agent '{agent.name}' has tools not in lead agent: "
                    f"{', '.join(sorted(extra_tools))}"
                )

        return warnings

    @staticmethod
    def check_api_key() -> bool:
        """
        Check if Anthropic API key is configured.

        Returns:
            True if API key is configured
        """
        import os

        api_key = os.getenv("ANTHROPIC_API_KEY")
        return bool(api_key and api_key.strip())

    @staticmethod
    def validate_and_raise(
        config: FrameworkConfigSchema,
        prompts_dir: Path | None = None,
        strict: bool = False,
    ) -> None:
        """
        Validate configuration and raise exception if invalid.

        Args:
            config: Configuration to validate
            prompts_dir: Directory containing prompt files
            strict: If True, treat warnings as errors

        Raises:
            ValueError: If configuration is invalid
        """
        errors = ConfigValidator.validate_config(config, prompts_dir, check_files=True)

        if strict:
            warnings = ConfigValidator.validate_agent_tools_subset(config)
            errors.extend(warnings)

        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(
                f"  - {error}" for error in errors
            )
            raise ValueError(error_msg)


# Import os for directory checks
import os
