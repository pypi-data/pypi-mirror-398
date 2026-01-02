"""
Dynamic agent registration and runtime architecture creation.

This module provides capabilities to:
- Add agents dynamically at runtime
- Create custom architectures programmatically
- Validate agent configurations
"""

from claude_agent_framework.dynamic.agent_registry import DynamicAgentRegistry
from claude_agent_framework.dynamic.loader import create_dynamic_architecture
from claude_agent_framework.dynamic.validator import AgentConfigValidator, validate_agent_config

__all__ = [
    "DynamicAgentRegistry",
    "create_dynamic_architecture",
    "AgentConfigValidator",
    "validate_agent_config",
]
