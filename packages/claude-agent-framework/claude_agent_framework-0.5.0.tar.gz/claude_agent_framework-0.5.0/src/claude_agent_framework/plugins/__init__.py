"""
Plugin system for Claude Agent Framework.

Provides extensibility through lifecycle hooks and custom behaviors.
"""

from claude_agent_framework.plugins.base import (
    BasePlugin,
    PluginContext,
    PluginManager,
)

__all__ = [
    "BasePlugin",
    "PluginContext",
    "PluginManager",
]
