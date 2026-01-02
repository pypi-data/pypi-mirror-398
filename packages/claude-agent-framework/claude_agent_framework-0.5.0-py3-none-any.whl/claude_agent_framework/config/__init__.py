"""
Configuration system for Claude Agent Framework.

Provides both legacy dataclass-based config and new Pydantic-based config.
"""

# Legacy config (for backward compatibility) - exported first
from claude_agent_framework.config.legacy import (
    FILES_DIR,
    FRAMEWORK_ROOT,
    LOGS_DIR,
    PROMPTS_DIR,
    AgentConfig,
    FrameworkConfig,
    default_config,
    get_api_key,
    validate_api_key,
)

# New advanced config system (optional, requires pydantic)
try:
    from claude_agent_framework.config.loader import ConfigLoader
    from claude_agent_framework.config.schema import (
        AgentConfigSchema,
        AgentInstanceSchema,
        FrameworkConfigSchema,
        PermissionMode,
        RoleBasedConfigSchema,
    )
    from claude_agent_framework.config.validator import ConfigValidator
    from claude_agent_framework.core.types import ModelType

    _has_advanced_config = True
except ImportError:
    _has_advanced_config = False
    ConfigLoader = None  # type: ignore
    ConfigValidator = None  # type: ignore
    AgentConfigSchema = None  # type: ignore
    AgentInstanceSchema = None  # type: ignore
    RoleBasedConfigSchema = None  # type: ignore
    FrameworkConfigSchema = None  # type: ignore
    ModelType = None  # type: ignore
    PermissionMode = None  # type: ignore

__all__ = [
    # Legacy exports (always available)
    "AgentConfig",
    "FrameworkConfig",
    "FRAMEWORK_ROOT",
    "PROMPTS_DIR",
    "FILES_DIR",
    "LOGS_DIR",
    "default_config",
    "validate_api_key",
    "get_api_key",
    # Advanced config (only if pydantic installed)
    "ConfigLoader",
    "ConfigValidator",
    "AgentConfigSchema",
    "AgentInstanceSchema",
    "RoleBasedConfigSchema",
    "FrameworkConfigSchema",
    "ModelType",
    "PermissionMode",
]
