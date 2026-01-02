"""
Tests for role-based architecture system.

Tests the RoleType, RoleCardinality, RoleDefinition, AgentInstanceConfig,
and RoleRegistry classes.
"""

import pytest

from claude_agent_framework.core.roles import (
    AgentInstanceConfig,
    RoleDefinition,
    RoleRegistry,
)
from claude_agent_framework.core.types import RoleCardinality, RoleType


class TestRoleType:
    """Tests for RoleType enum."""

    def test_all_role_types_exist(self):
        """Test that all expected role types are defined."""
        expected = [
            "coordinator",
            "worker",
            "processor",
            "synthesizer",
            "critic",
            "judge",
            "specialist",
            "advocate",
            "mapper",
            "reducer",
            "executor",
            "reflector",
        ]
        for role in expected:
            assert hasattr(RoleType, role.upper())

    def test_role_type_values(self):
        """Test that role type values are strings."""
        assert RoleType.WORKER.value == "worker"
        assert RoleType.COORDINATOR.value == "coordinator"
        assert RoleType.PROCESSOR.value == "processor"


class TestRoleCardinality:
    """Tests for RoleCardinality enum."""

    def test_all_cardinality_types_exist(self):
        """Test that all expected cardinality types are defined."""
        expected = ["exactly_one", "one_or_more", "zero_or_more", "zero_or_one"]
        for card in expected:
            assert hasattr(RoleCardinality, card.upper())

    def test_cardinality_values(self):
        """Test that cardinality values are strings."""
        assert RoleCardinality.EXACTLY_ONE.value == "exactly_one"
        assert RoleCardinality.ONE_OR_MORE.value == "one_or_more"
        assert RoleCardinality.ZERO_OR_ONE.value == "zero_or_one"


class TestRoleDefinition:
    """Tests for RoleDefinition dataclass."""

    def test_minimal_role_definition(self):
        """Test creating role definition with minimal fields."""
        role = RoleDefinition(
            role_type=RoleType.WORKER,
            description="Test worker",
        )
        assert role.role_type == RoleType.WORKER
        assert role.description == "Test worker"
        assert role.required_tools == []
        assert role.optional_tools == []
        assert role.cardinality == RoleCardinality.EXACTLY_ONE  # default
        assert role.default_model == "haiku"

    def test_full_role_definition(self):
        """Test creating role definition with all fields."""
        role = RoleDefinition(
            role_type=RoleType.SYNTHESIZER,
            description="Report generator",
            required_tools=["Write"],
            optional_tools=["Read", "Glob"],
            cardinality=RoleCardinality.EXACTLY_ONE,
            default_model="sonnet",
            prompt_file="synthesizer.txt",
        )
        assert role.role_type == RoleType.SYNTHESIZER
        assert role.required_tools == ["Write"]
        assert role.optional_tools == ["Read", "Glob"]
        assert role.default_model == "sonnet"
        assert role.prompt_file == "synthesizer.txt"


class TestAgentInstanceConfig:
    """Tests for AgentInstanceConfig dataclass."""

    def test_minimal_agent_instance(self):
        """Test creating agent instance with minimal fields."""
        agent = AgentInstanceConfig(
            name="market-researcher",
            role="worker",
        )
        assert agent.name == "market-researcher"
        assert agent.role == "worker"
        assert agent.description == ""
        assert agent.tools == []
        assert agent.prompt == ""

    def test_full_agent_instance(self):
        """Test creating agent instance with all fields."""
        agent = AgentInstanceConfig(
            name="tech-analyst",
            role="processor",
            description="Analyze technology trends",
            tools=["Read", "Write", "Glob"],
            prompt="You are a technology analyst.",
            prompt_file="tech_analyst.txt",
            model="sonnet",
            metadata={"priority": "high"},
        )
        assert agent.name == "tech-analyst"
        assert agent.role == "processor"
        assert agent.description == "Analyze technology trends"
        assert agent.tools == ["Read", "Write", "Glob"]
        assert agent.model == "sonnet"
        assert agent.metadata == {"priority": "high"}


class TestRoleRegistry:
    """Tests for RoleRegistry class."""

    @pytest.fixture
    def registry(self):
        """Create a registry with test roles."""
        reg = RoleRegistry()
        reg.register(
            "worker",
            RoleDefinition(
                role_type=RoleType.WORKER,
                description="Data gatherer",
                required_tools=["WebSearch"],
                cardinality=RoleCardinality.ONE_OR_MORE,
            ),
        )
        reg.register(
            "processor",
            RoleDefinition(
                role_type=RoleType.PROCESSOR,
                description="Data processor",
                required_tools=["Read", "Write"],
                cardinality=RoleCardinality.ZERO_OR_ONE,
            ),
        )
        reg.register(
            "synthesizer",
            RoleDefinition(
                role_type=RoleType.SYNTHESIZER,
                description="Report generator",
                required_tools=["Write"],
                cardinality=RoleCardinality.EXACTLY_ONE,
            ),
        )
        return reg

    def test_register_role(self, registry):
        """Test registering a new role."""
        assert len(registry.list_roles()) == 3
        assert "worker" in registry.list_roles()

    def test_get_role(self, registry):
        """Test getting a role definition."""
        role = registry.get("worker")
        assert role is not None
        assert role.role_type == RoleType.WORKER
        assert role.required_tools == ["WebSearch"]

    def test_get_nonexistent_role(self, registry):
        """Test getting a nonexistent role."""
        role = registry.get("nonexistent")
        assert role is None

    def test_list_roles(self, registry):
        """Test listing all roles."""
        roles = registry.list_roles()
        assert set(roles) == {"worker", "processor", "synthesizer"}

    def test_get_required_roles(self, registry):
        """Test getting required roles."""
        required = registry.get_required_roles()
        # worker (ONE_OR_MORE) and synthesizer (EXACTLY_ONE) are required
        assert "worker" in required
        assert "synthesizer" in required
        # processor (ZERO_OR_ONE) is optional
        assert "processor" not in required

    def test_get_optional_roles(self, registry):
        """Test getting optional roles."""
        optional = registry.get_optional_roles()
        # processor (ZERO_OR_ONE) is optional
        assert "processor" in optional
        # worker and synthesizer are required
        assert "worker" not in optional
        assert "synthesizer" not in optional


class TestRoleRegistryValidation:
    """Tests for RoleRegistry validation."""

    @pytest.fixture
    def registry(self):
        """Create a registry with test roles."""
        reg = RoleRegistry()
        reg.register(
            "worker",
            RoleDefinition(
                role_type=RoleType.WORKER,
                description="Data gatherer",
                required_tools=["WebSearch"],
                cardinality=RoleCardinality.ONE_OR_MORE,
            ),
        )
        reg.register(
            "synthesizer",
            RoleDefinition(
                role_type=RoleType.SYNTHESIZER,
                description="Report generator",
                required_tools=["Write"],
                cardinality=RoleCardinality.EXACTLY_ONE,
            ),
        )
        return reg

    def test_validate_valid_agents(self, registry):
        """Test validating a valid agent configuration."""
        agents = [
            AgentInstanceConfig(name="researcher", role="worker"),
            AgentInstanceConfig(name="writer", role="synthesizer"),
        ]
        errors = registry.validate_agents(agents)
        assert errors == []

    def test_validate_missing_required_role(self, registry):
        """Test validation fails when required role is missing."""
        agents = [
            AgentInstanceConfig(name="researcher", role="worker"),
            # Missing synthesizer (EXACTLY_ONE)
        ]
        errors = registry.validate_agents(agents)
        assert len(errors) > 0
        assert any("synthesizer" in e.lower() for e in errors)

    def test_validate_too_many_agents(self, registry):
        """Test validation fails when too many agents for role."""
        agents = [
            AgentInstanceConfig(name="researcher", role="worker"),
            AgentInstanceConfig(name="writer1", role="synthesizer"),
            AgentInstanceConfig(name="writer2", role="synthesizer"),  # Too many
        ]
        errors = registry.validate_agents(agents)
        assert len(errors) > 0
        assert any("synthesizer" in e.lower() for e in errors)

    def test_validate_unknown_role(self, registry):
        """Test validation fails for unknown role."""
        agents = [
            AgentInstanceConfig(name="researcher", role="worker"),
            AgentInstanceConfig(name="writer", role="synthesizer"),
            AgentInstanceConfig(name="unknown", role="unknown_role"),
        ]
        errors = registry.validate_agents(agents)
        assert len(errors) > 0
        assert any("unknown_role" in e.lower() for e in errors)

    def test_validate_multiple_workers_allowed(self, registry):
        """Test that ONE_OR_MORE allows multiple agents."""
        agents = [
            AgentInstanceConfig(name="researcher1", role="worker"),
            AgentInstanceConfig(name="researcher2", role="worker"),
            AgentInstanceConfig(name="researcher3", role="worker"),
            AgentInstanceConfig(name="writer", role="synthesizer"),
        ]
        errors = registry.validate_agents(agents)
        assert errors == []


class TestAgentInstanceConfigToAgentDefinition:
    """Tests for AgentInstanceConfig.to_agent_definition method."""

    @pytest.fixture
    def role_def(self):
        """Create a test role definition."""
        return RoleDefinition(
            role_type=RoleType.WORKER,
            description="Default worker description",
            required_tools=["WebSearch"],
            optional_tools=["Write"],
            cardinality=RoleCardinality.ONE_OR_MORE,
            default_model="haiku",
            prompt_file="worker.txt",
        )

    def test_to_agent_definition_minimal(self, role_def, tmp_path):
        """Test converting minimal agent instance."""
        agent = AgentInstanceConfig(name="researcher", role="worker")
        agent_def = agent.to_agent_definition(role_def, tmp_path)

        assert agent_def.name == "researcher"
        # Uses role's default description
        assert agent_def.description == "Default worker description"
        # Uses role's required tools
        assert "WebSearch" in agent_def.tools

    def test_to_agent_definition_with_override(self, role_def, tmp_path):
        """Test converting agent instance with overrides."""
        agent = AgentInstanceConfig(
            name="custom-researcher",
            role="worker",
            description="Custom description",
            tools=["WebSearch", "Write", "Read"],
            model="sonnet",
        )
        agent_def = agent.to_agent_definition(role_def, tmp_path)

        assert agent_def.name == "custom-researcher"
        assert agent_def.description == "Custom description"
        # Uses agent's tools, includes required tools
        assert "WebSearch" in agent_def.tools
        assert "Write" in agent_def.tools
        assert "Read" in agent_def.tools
        assert agent_def.model == "sonnet"
