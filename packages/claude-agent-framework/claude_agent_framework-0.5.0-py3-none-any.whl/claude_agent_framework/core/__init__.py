"""
Core abstraction layer for multi-architecture agent framework.

Provides:
- BaseArchitecture: Abstract base class for all architectures
- AgentSession: Unified session management
- Registry: Architecture registration and discovery
- Type definitions: Framework-wide type aliases and enums
- Role definitions: Role-based architecture abstractions
"""

from claude_agent_framework.core.base import (
    AgentDefinitionConfig,
    BaseArchitecture,
)
from claude_agent_framework.core.registry import (
    get_architecture,
    list_architectures,
    register_architecture,
)
from claude_agent_framework.core.roles import (
    AgentInstanceConfig,
    RoleDefinition,
    RoleRegistry,
)
from claude_agent_framework.core.session import AgentSession
from claude_agent_framework.core.types import (
    ArchitectureType,
    ModelType,
    ModelTypeStr,
    RoleCardinality,
    RoleType,
    RoleTypeStr,
)

__all__ = [
    # Base classes
    "BaseArchitecture",
    "AgentDefinitionConfig",
    # Session management
    "AgentSession",
    # Registry
    "register_architecture",
    "get_architecture",
    "list_architectures",
    # Type definitions
    "ArchitectureType",
    "ModelType",
    "ModelTypeStr",
    # Role definitions
    "RoleType",
    "RoleTypeStr",
    "RoleCardinality",
    "RoleDefinition",
    "AgentInstanceConfig",
    "RoleRegistry",
]
