"""Tests for dynamic agent registration and validation."""

import pytest

from claude_agent_framework.dynamic import (
    AgentConfigValidator,
    DynamicAgentRegistry,
    create_dynamic_architecture,
    validate_agent_config,
)
from claude_agent_framework.dynamic.validator import AgentConfigError


class TestAgentConfigValidator:
    """Tests for AgentConfigValidator."""

    def test_validate_name_valid(self):
        """Test valid agent names."""
        AgentConfigValidator.validate_name("researcher")
        AgentConfigValidator.validate_name("data_analyst")
        AgentConfigValidator.validate_name("report-writer")
        AgentConfigValidator.validate_name("agent_123")

    def test_validate_name_empty(self):
        """Test empty name raises error."""
        with pytest.raises(AgentConfigError, match="cannot be empty"):
            AgentConfigValidator.validate_name("")

    def test_validate_name_invalid_chars(self):
        """Test invalid characters raise error."""
        with pytest.raises(AgentConfigError, match="alphanumeric"):
            AgentConfigValidator.validate_name("agent@123")

    def test_validate_name_starts_with_digit(self):
        """Test name starting with digit raises error."""
        with pytest.raises(AgentConfigError, match="cannot start with digit"):
            AgentConfigValidator.validate_name("123agent")

    def test_validate_description_valid(self):
        """Test valid description."""
        AgentConfigValidator.validate_description("Research data from web sources")

    def test_validate_description_empty(self):
        """Test empty description raises error."""
        with pytest.raises(AgentConfigError, match="cannot be empty"):
            AgentConfigValidator.validate_description("")

    def test_validate_description_too_short(self):
        """Test too short description raises error."""
        with pytest.raises(AgentConfigError, match="too short"):
            AgentConfigValidator.validate_description("short")

    def test_validate_tools_valid(self):
        """Test valid tools list."""
        AgentConfigValidator.validate_tools(["WebSearch", "Write"])
        AgentConfigValidator.validate_tools(["Read", "Bash", "Glob"])

    def test_validate_tools_empty(self):
        """Test empty tools list raises error."""
        with pytest.raises(AgentConfigError, match="at least one tool"):
            AgentConfigValidator.validate_tools([])

    def test_validate_tools_invalid(self):
        """Test invalid tool names raise error."""
        with pytest.raises(AgentConfigError, match="Invalid tools"):
            AgentConfigValidator.validate_tools(["InvalidTool"])

    def test_validate_prompt_valid(self):
        """Test valid prompt."""
        AgentConfigValidator.validate_prompt("You are a research assistant...")

    def test_validate_prompt_empty(self):
        """Test empty prompt raises error."""
        with pytest.raises(AgentConfigError, match="cannot be empty"):
            AgentConfigValidator.validate_prompt("")

    def test_validate_prompt_too_short(self):
        """Test too short prompt raises error."""
        with pytest.raises(AgentConfigError, match="too short"):
            AgentConfigValidator.validate_prompt("short")

    def test_validate_model_valid(self):
        """Test valid model names."""
        AgentConfigValidator.validate_model("haiku")
        AgentConfigValidator.validate_model("sonnet")
        AgentConfigValidator.validate_model("opus")

    def test_validate_model_invalid(self):
        """Test invalid model raises error."""
        with pytest.raises(AgentConfigError, match="Invalid model"):
            AgentConfigValidator.validate_model("gpt-4")

    def test_validate_full_valid(self):
        """Test full valid configuration."""
        AgentConfigValidator.validate_full(
            name="researcher",
            description="Research data from web sources",
            tools=["WebSearch", "Write"],
            prompt="You are a research assistant...",
            model="haiku",
        )

    def test_validate_agent_config_dict_valid(self):
        """Test validate_agent_config with valid dict."""
        config = {
            "name": "researcher",
            "description": "Research data from web sources",
            "tools": ["WebSearch", "Write"],
            "prompt": "You are a research assistant...",
            "model": "haiku",
        }
        validate_agent_config(config)

    def test_validate_agent_config_dict_missing_fields(self):
        """Test validate_agent_config with missing fields."""
        config = {
            "name": "researcher",
            "tools": ["WebSearch"],
        }
        with pytest.raises(AgentConfigError, match="Missing required fields"):
            validate_agent_config(config)


class TestDynamicAgentRegistry:
    """Tests for DynamicAgentRegistry."""

    def test_initialization(self):
        """Test registry initialization."""
        registry = DynamicAgentRegistry()
        assert len(registry) == 0
        assert registry.list_agents() == []

    def test_register_agent(self):
        """Test registering a new agent."""
        registry = DynamicAgentRegistry()
        registry.register(
            name="researcher",
            description="Research data from web sources",
            tools=["WebSearch", "Write"],
            prompt="You are a research assistant...",
            model="haiku",
        )

        assert len(registry) == 1
        assert "researcher" in registry
        assert registry.list_agents() == ["researcher"]

    def test_register_duplicate_agent(self):
        """Test registering duplicate agent raises error."""
        registry = DynamicAgentRegistry()
        registry.register(
            name="researcher",
            description="Research data from web sources",
            tools=["WebSearch", "Write"],
            prompt="You are a research assistant...",
        )

        with pytest.raises(ValueError, match="already registered"):
            registry.register(
                name="researcher",
                description="Another researcher description",
                tools=["WebSearch"],
                prompt="You are a different research assistant...",
            )

    def test_unregister_agent(self):
        """Test unregistering an agent."""
        registry = DynamicAgentRegistry()
        registry.register(
            name="researcher",
            description="Research data from web sources",
            tools=["WebSearch", "Write"],
            prompt="You are a research assistant...",
        )

        registry.unregister("researcher")
        assert len(registry) == 0
        assert "researcher" not in registry

    def test_unregister_nonexistent_agent(self):
        """Test unregistering nonexistent agent raises error."""
        registry = DynamicAgentRegistry()
        with pytest.raises(KeyError, match="not found"):
            registry.unregister("nonexistent")

    def test_get_agent(self):
        """Test getting an agent definition."""
        registry = DynamicAgentRegistry()
        registry.register(
            name="researcher",
            description="Research data from web sources",
            tools=["WebSearch", "Write"],
            prompt="You are a research assistant...",
        )

        agent = registry.get("researcher")
        assert agent is not None
        assert agent.description == "Research data from web sources"
        assert agent.tools == ["WebSearch", "Write"]

    def test_get_nonexistent_agent(self):
        """Test getting nonexistent agent returns None."""
        registry = DynamicAgentRegistry()
        assert registry.get("nonexistent") is None

    def test_get_all(self):
        """Test getting all agents."""
        registry = DynamicAgentRegistry()
        registry.register(
            name="researcher",
            description="Research data from web sources",
            tools=["WebSearch", "Write"],
            prompt="You are a research assistant...",
        )
        registry.register(
            name="analyst",
            description="Analyze data",
            tools=["Read", "Write"],
            prompt="You are a data analyst...",
        )

        agents = registry.get_all()
        assert len(agents) == 2
        assert "researcher" in agents
        assert "analyst" in agents

    def test_clear(self):
        """Test clearing all agents."""
        registry = DynamicAgentRegistry()
        registry.register(
            name="researcher",
            description="Research data from web sources",
            tools=["WebSearch", "Write"],
            prompt="You are a research assistant...",
        )

        registry.clear()
        assert len(registry) == 0


class TestCreateDynamicArchitecture:
    """Tests for create_dynamic_architecture."""

    def test_create_architecture(self):
        """Test creating a dynamic architecture."""
        CustomArch = create_dynamic_architecture(
            name="custom_pipeline",
            description="Custom data processing pipeline",
            agents={
                "collector": {
                    "description": "Collect data from web sources",
                    "tools": ["WebSearch", "Write"],
                    "prompt": "You collect data from web sources...",
                },
                "processor": {
                    "description": "Process collected data",
                    "tools": ["Read", "Write"],
                    "prompt": "You process and analyze data...",
                    "model": "sonnet",
                },
            },
            lead_prompt="You coordinate data collection and processing...",
        )

        assert CustomArch.name == "custom_pipeline"
        assert CustomArch.description == "Custom data processing pipeline"

    def test_create_architecture_instance(self):
        """Test creating an instance of dynamic architecture."""
        CustomArch = create_dynamic_architecture(
            name="custom_pipeline",
            description="Custom data processing pipeline",
            agents={
                "collector": {
                    "description": "Collect data from web sources",
                    "tools": ["WebSearch", "Write"],
                    "prompt": "You collect data from web sources...",
                },
            },
            lead_prompt="You coordinate data collection...",
        )

        instance = CustomArch()
        assert instance.name == "custom_pipeline"
        agents = instance.get_agents()
        assert len(agents) == 1
        assert "collector" in agents

    def test_create_architecture_invalid_name(self):
        """Test invalid name raises error."""
        with pytest.raises(ValueError, match="name must be non-empty"):
            create_dynamic_architecture(
                name="",
                description="Test",
                agents={"test": {}},
                lead_prompt="Test",
            )

    def test_create_architecture_invalid_agents(self):
        """Test invalid agents raises error."""
        with pytest.raises(ValueError, match="must be non-empty dictionary"):
            create_dynamic_architecture(
                name="test",
                description="Test",
                agents={},
                lead_prompt="Test",
            )

    def test_create_architecture_invalid_agent_config(self):
        """Test invalid agent configuration raises error."""
        with pytest.raises(AgentConfigError):
            create_dynamic_architecture(
                name="test",
                description="Test",
                agents={
                    "bad_agent": {
                        "description": "Test",
                        "tools": ["InvalidTool"],  # Invalid tool
                        "prompt": "Test prompt...",
                    }
                },
                lead_prompt="Test",
            )
