"""Tests for advanced configuration system."""

import os
from pathlib import Path

import pytest
import yaml

from claude_agent_framework.config.loader import ConfigLoader
from claude_agent_framework.config.schema import (
    AgentConfigSchema,
    FrameworkConfigSchema,
    ModelType,
    PermissionMode,
)
from claude_agent_framework.config.validator import ConfigValidator


class TestAgentConfigSchema:
    """Tests for AgentConfigSchema validation."""

    def test_valid_agent_config(self):
        """Test valid agent configuration."""
        config = AgentConfigSchema(
            name="test-agent",
            description="Test agent for validation",
            tools=["Read", "Write"],
            prompt="Test prompt content",
            model=ModelType.HAIKU,
        )

        assert config.name == "test-agent"
        assert config.description == "Test agent for validation"
        assert config.tools == ["Read", "Write"]
        assert config.prompt == "Test prompt content"
        assert config.model == ModelType.HAIKU

    def test_agent_name_validation(self):
        """Test agent name must match pattern."""
        # Valid names
        AgentConfigSchema(
            name="my-agent",
            description="Valid agent name",
            prompt="Test",
        )

        # Invalid names (should raise)
        with pytest.raises(ValueError, match="pattern"):
            AgentConfigSchema(
                name="MyAgent",  # Uppercase not allowed
                description="Invalid name",
                prompt="Test",
            )

        with pytest.raises(ValueError, match="pattern"):
            AgentConfigSchema(
                name="my_agent",  # Underscore not allowed
                description="Invalid name",
                prompt="Test",
            )

    def test_tool_validation(self):
        """Test tool validation."""
        # Valid tools
        config = AgentConfigSchema(
            name="test-agent",
            description="Test agent",
            tools=["Read", "Write", "Bash"],
            prompt="Test",
        )
        assert config.tools == ["Read", "Write", "Bash"]

        # Invalid tools
        with pytest.raises(ValueError, match="Invalid tools"):
            AgentConfigSchema(
                name="test-agent",
                description="Test agent",
                tools=["Read", "InvalidTool"],
                prompt="Test",
            )

    def test_prompt_validation(self):
        """Test prompt source validation."""
        # Valid: prompt provided
        AgentConfigSchema(
            name="test-agent",
            description="Test agent",
            prompt="Test prompt",
        )

        # Valid: prompt_file provided
        AgentConfigSchema(
            name="test-agent",
            description="Test agent",
            prompt_file="test.txt",
        )

        # Invalid: neither provided
        with pytest.raises(ValueError, match="Either 'prompt' or 'prompt_file'"):
            AgentConfigSchema(
                name="test-agent",
                description="Test agent",
            )

        # Invalid: both provided
        with pytest.raises(ValueError, match="Cannot specify both"):
            AgentConfigSchema(
                name="test-agent",
                description="Test agent",
                prompt="Test",
                prompt_file="test.txt",
            )


class TestFrameworkConfigSchema:
    """Tests for FrameworkConfigSchema validation."""

    def test_valid_framework_config(self):
        """Test valid framework configuration."""
        config = FrameworkConfigSchema(
            lead_agent_model=ModelType.SONNET,
            enable_logging=True,
            max_parallel_agents=5,
        )

        assert config.lead_agent_model == ModelType.SONNET
        assert config.enable_logging is True
        assert config.max_parallel_agents == 5

    def test_default_values(self):
        """Test default configuration values."""
        config = FrameworkConfigSchema()

        assert config.lead_agent_model == ModelType.HAIKU
        assert config.lead_agent_tools == ["Task"]
        assert config.permission_mode == PermissionMode.BYPASS
        assert config.enable_logging is True
        assert config.max_parallel_agents == 5

    def test_max_parallel_agents_validation(self):
        """Test max_parallel_agents must be in valid range."""
        # Valid values
        FrameworkConfigSchema(max_parallel_agents=1)
        FrameworkConfigSchema(max_parallel_agents=10)
        FrameworkConfigSchema(max_parallel_agents=20)

        # Invalid values
        with pytest.raises(ValueError):
            FrameworkConfigSchema(max_parallel_agents=0)  # Too low

        with pytest.raises(ValueError):
            FrameworkConfigSchema(max_parallel_agents=21)  # Too high

    def test_lead_agent_tools_validation(self):
        """Test lead agent must have at least one tool."""
        # Valid
        FrameworkConfigSchema(lead_agent_tools=["Task"])

        # Invalid: empty list
        with pytest.raises(ValueError, match="at least one tool"):
            FrameworkConfigSchema(lead_agent_tools=[])

    def test_path_conversion(self):
        """Test string paths are converted to Path objects."""
        config = FrameworkConfigSchema(
            logs_dir="logs",
            files_dir="files",
        )

        assert isinstance(config.logs_dir, Path)
        assert isinstance(config.files_dir, Path)


class TestConfigLoader:
    """Tests for ConfigLoader."""

    def test_from_dict(self):
        """Test loading from dictionary."""
        data = {
            "lead_agent_model": "sonnet",
            "enable_logging": True,
            "max_parallel_agents": 7,
        }

        config = ConfigLoader.from_dict(data)

        assert config.lead_agent_model == ModelType.SONNET
        assert config.enable_logging is True
        assert config.max_parallel_agents == 7

    def test_from_yaml(self, tmp_path):
        """Test loading from YAML file."""
        # Create test YAML file
        yaml_path = tmp_path / "test_config.yaml"
        config_data = {
            "lead_agent_model": "sonnet",
            "enable_logging": False,
            "max_parallel_agents": 8,
        }

        with yaml_path.open("w") as f:
            yaml.dump(config_data, f)

        # Load config
        config = ConfigLoader.from_yaml(yaml_path)

        assert config.lead_agent_model == ModelType.SONNET
        assert config.enable_logging is False
        assert config.max_parallel_agents == 8

    def test_from_yaml_file_not_found(self):
        """Test error when YAML file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.from_yaml("nonexistent.yaml")

    def test_from_env(self):
        """Test loading from environment variables."""
        # Set environment variables
        os.environ["CLAUDE_LEAD_AGENT_MODEL"] = "opus"
        os.environ["CLAUDE_ENABLE_LOGGING"] = "false"
        os.environ["CLAUDE_MAX_PARALLEL_AGENTS"] = "15"

        try:
            config = ConfigLoader.from_env()

            assert config.lead_agent_model == ModelType.OPUS
            assert config.enable_logging is False
            assert config.max_parallel_agents == 15
        finally:
            # Cleanup
            os.environ.pop("CLAUDE_LEAD_AGENT_MODEL", None)
            os.environ.pop("CLAUDE_ENABLE_LOGGING", None)
            os.environ.pop("CLAUDE_MAX_PARALLEL_AGENTS", None)

    def test_merge_configs(self):
        """Test merging multiple configurations."""
        base = FrameworkConfigSchema(
            lead_agent_model=ModelType.HAIKU,
            enable_logging=True,
            max_parallel_agents=5,
        )

        override = FrameworkConfigSchema(
            lead_agent_model=ModelType.SONNET,
            max_parallel_agents=10,
        )

        merged = ConfigLoader.merge_configs(base, override)

        # Override values should win
        assert merged.lead_agent_model == ModelType.SONNET
        assert merged.max_parallel_agents == 10
        # Base values preserved if not overridden
        assert merged.enable_logging is True

    def test_load_with_profile(self):
        """Test loading with environment profile."""
        # This uses the built-in development profile
        config = ConfigLoader.load_with_profile(profile="development")

        assert config.lead_agent_model == ModelType.HAIKU
        assert config.max_parallel_agents == 3
        assert config.enable_metrics is True


class TestConfigValidator:
    """Tests for ConfigValidator."""

    def test_validate_valid_config(self, tmp_path):
        """Test validation passes for valid config."""
        # Create prompt file
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "lead_agent.txt").write_text("Lead prompt")

        config = FrameworkConfigSchema()

        errors = ConfigValidator.validate_config(config, prompts_dir=prompts_dir, check_files=True)

        assert len(errors) == 0

    def test_validate_missing_task_tool(self):
        """Test validation fails if lead agent missing Task tool."""
        config = FrameworkConfigSchema(lead_agent_tools=["Read", "Write"])

        errors = ConfigValidator.validate_config(config, check_files=False)

        assert any("Task" in error for error in errors)

    def test_validate_duplicate_agents(self):
        """Test validation detects duplicate agent names."""
        config = FrameworkConfigSchema(
            subagents=[
                AgentConfigSchema(
                    name="duplicate",
                    description="First agent",
                    prompt="Test",
                ),
                AgentConfigSchema(
                    name="duplicate",
                    description="Second agent",
                    prompt="Test",
                ),
            ]
        )

        errors = ConfigValidator.validate_config(config, check_files=False)

        assert any("Duplicate" in error for error in errors)

    def test_validate_agent_no_tools(self):
        """Test validation fails if agent has no tools."""
        config = FrameworkConfigSchema(
            subagents=[
                AgentConfigSchema(
                    name="test-agent",
                    description="Agent with no tools",
                    tools=[],
                    prompt="Test",
                )
            ]
        )

        errors = ConfigValidator.validate_config(config, check_files=False)

        assert any("at least one tool" in error for error in errors)

    def test_validate_and_raise(self):
        """Test validate_and_raise raises on invalid config."""
        config = FrameworkConfigSchema(lead_agent_tools=["Read"])  # Missing Task

        with pytest.raises(ValueError, match="validation failed"):
            ConfigValidator.validate_and_raise(config, strict=False)


class TestProfileIntegration:
    """Integration tests for profile system."""

    def test_development_profile(self):
        """Test development profile loads correctly."""
        config = ConfigLoader.load_with_profile(profile="development")

        assert config.lead_agent_model == ModelType.HAIKU
        assert config.max_parallel_agents == 3
        assert config.enable_metrics is True

    def test_staging_profile(self):
        """Test staging profile loads correctly."""
        config = ConfigLoader.load_with_profile(profile="staging")

        assert config.lead_agent_model == ModelType.SONNET
        assert config.max_parallel_agents == 5

    def test_production_profile(self):
        """Test production profile loads correctly."""
        config = ConfigLoader.load_with_profile(profile="production")

        assert config.lead_agent_model == ModelType.SONNET
        assert config.max_parallel_agents == 10
