"""
Multi-source configuration loader.

Supports loading from YAML files, environment variables, and dictionaries.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

from claude_agent_framework.config.schema import (
    FrameworkConfigSchema,
    ProfileConfigSchema,
)


class ConfigLoader:
    """
    Multi-source configuration loader.

    Supports loading configuration from:
    - YAML files
    - Environment variables
    - Python dictionaries
    - Environment profiles (dev/staging/prod)
    """

    @staticmethod
    def from_yaml(path: str | Path) -> FrameworkConfigSchema:
        """
        Load configuration from YAML file.

        Args:
            path: Path to YAML file

        Returns:
            Validated configuration

        Raises:
            ImportError: If PyYAML is not installed
            FileNotFoundError: If file doesn't exist
            ValueError: If YAML is invalid
        """
        if yaml is None:
            raise ImportError(
                "PyYAML is required to load YAML configs. "
                "Install with: pip install 'claude-agent-framework[config]' or pip install pyyaml"
            )

        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError(f"YAML file must contain a dictionary, got {type(data)}")

        return FrameworkConfigSchema(**data)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> FrameworkConfigSchema:
        """
        Load configuration from dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            Validated configuration
        """
        return FrameworkConfigSchema(**data)

    @staticmethod
    def from_env(prefix: str = "CLAUDE_") -> FrameworkConfigSchema:
        """
        Load configuration from environment variables.

        Environment variables are mapped as follows:
        - CLAUDE_LEAD_AGENT_MODEL -> lead_agent_model
        - CLAUDE_PERMISSION_MODE -> permission_mode
        - CLAUDE_ENABLE_LOGGING -> enable_logging
        - CLAUDE_MAX_PARALLEL_AGENTS -> max_parallel_agents
        - CLAUDE_ENABLE_METRICS -> enable_metrics

        Args:
            prefix: Environment variable prefix

        Returns:
            Validated configuration
        """
        env_mapping = {
            f"{prefix}LEAD_AGENT_MODEL": "lead_agent_model",
            f"{prefix}PERMISSION_MODE": "permission_mode",
            f"{prefix}ENABLE_LOGGING": "enable_logging",
            f"{prefix}LOGS_DIR": "logs_dir",
            f"{prefix}FILES_DIR": "files_dir",
            f"{prefix}MAX_PARALLEL_AGENTS": "max_parallel_agents",
            f"{prefix}ENABLE_METRICS": "enable_metrics",
            f"{prefix}ENABLE_PLUGINS": "enable_plugins",
        }

        config_data: dict[str, Any] = {}

        for env_var, config_key in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                # Type conversion
                if config_key in ("enable_logging", "enable_metrics", "enable_plugins"):
                    config_data[config_key] = value.lower() in ("true", "1", "yes")
                elif config_key == "max_parallel_agents":
                    config_data[config_key] = int(value)
                else:
                    config_data[config_key] = value

        return FrameworkConfigSchema(**config_data)

    @staticmethod
    def load_profile(profile_name: str, profiles_dir: Path | None = None) -> ProfileConfigSchema:
        """
        Load environment profile configuration.

        Args:
            profile_name: Profile name (dev/staging/prod)
            profiles_dir: Directory containing profile YAML files

        Returns:
            Profile configuration

        Raises:
            ImportError: If PyYAML is not installed
            FileNotFoundError: If profile file doesn't exist
        """
        if yaml is None:
            raise ImportError(
                "PyYAML is required to load profiles. "
                "Install with: pip install 'claude-agent-framework[config]' or pip install pyyaml"
            )

        if profiles_dir is None:
            # Default profiles directory
            from pathlib import Path

            # Get the config package directory
            config_dir = Path(__file__).parent
            profiles_dir = config_dir / "profiles"

        profile_path = profiles_dir / f"{profile_name}.yaml"
        if not profile_path.exists():
            raise FileNotFoundError(f"Profile not found: {profile_path}")

        with profile_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError(f"Profile YAML must contain a dictionary, got {type(data)}")

        data["name"] = profile_name
        return ProfileConfigSchema(**data)

    @staticmethod
    def merge_configs(
        base: FrameworkConfigSchema,
        *overrides: FrameworkConfigSchema | dict[str, Any],
    ) -> FrameworkConfigSchema:
        """
        Merge multiple configurations with precedence.

        Later configurations override earlier ones.

        Args:
            base: Base configuration
            *overrides: Override configurations (FrameworkConfigSchema or dict)

        Returns:
            Merged configuration
        """
        # Start with base config as dict
        merged = base.model_dump()

        # Apply each override
        for override in overrides:
            if isinstance(override, FrameworkConfigSchema):
                override_dict = override.model_dump()
            else:
                override_dict = override

            # Deep merge
            ConfigLoader._deep_merge(merged, override_dict)

        return FrameworkConfigSchema(**merged)

    @staticmethod
    def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> None:
        """
        Deep merge override into base dictionary (in-place).

        Args:
            base: Base dictionary (modified in-place)
            override: Override dictionary
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                ConfigLoader._deep_merge(base[key], value)
            else:
                base[key] = value

    @staticmethod
    def load_with_profile(
        config_path: str | Path | None = None,
        profile: str | None = None,
    ) -> FrameworkConfigSchema:
        """
        Load configuration with optional profile override.

        Loading order (later sources override earlier):
        1. Base config from file (if provided)
        2. Environment variables
        3. Profile config (if provided)

        Args:
            config_path: Path to base YAML config (optional)
            profile: Profile name (dev/staging/prod) (optional)

        Returns:
            Merged configuration

        Examples:
            # Load defaults with env vars
            config = ConfigLoader.load_with_profile()

            # Load from file with env vars
            config = ConfigLoader.load_with_profile("config.yaml")

            # Load with profile
            config = ConfigLoader.load_with_profile(profile="production")

            # Load from file + profile + env vars
            config = ConfigLoader.load_with_profile("base.yaml", profile="staging")
        """
        # 1. Start with base config
        if config_path:
            base_config = ConfigLoader.from_yaml(config_path)
        else:
            base_config = FrameworkConfigSchema()

        # 2. Apply environment variables
        env_config = ConfigLoader.from_env()
        merged = ConfigLoader.merge_configs(base_config, env_config)

        # 3. Apply profile if specified
        if profile:
            profile_config = ConfigLoader.load_profile(profile)
            merged = profile_config.apply_to_config(merged)

        return merged


# Convenience function for backward compatibility
def load_config(
    config_path: str | Path | None = None,
    profile: str | None = None,
) -> FrameworkConfigSchema:
    """
    Load configuration (convenience wrapper).

    Args:
        config_path: Path to YAML config file (optional)
        profile: Environment profile (dev/staging/prod) (optional)

    Returns:
        Validated configuration
    """
    return ConfigLoader.load_with_profile(config_path, profile)
