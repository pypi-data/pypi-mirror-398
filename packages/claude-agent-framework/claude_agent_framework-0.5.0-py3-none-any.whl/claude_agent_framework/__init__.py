"""
Claude Agent Framework

A multi-architecture agent framework built on Claude Agent SDK.
Supports 7 architecture patterns for research, development, and decision support.

Quick Start:
    >>> from claude_agent_framework import create_session
    >>> from claude_agent_framework.core.roles import AgentInstanceConfig
    >>>
    >>> agents = [
    ...     AgentInstanceConfig(name="researcher", role="worker"),
    ...     AgentInstanceConfig(name="writer", role="synthesizer"),
    ... ]
    >>> session = create_session("research", agent_instances=agents)
    >>> async for msg in session.run("Analyze AI market trends"):
    ...     print(msg)

Available Architectures:
- research: Master-worker pattern for deep research
- pipeline: Sequential stage processing for code review
- critic_actor: Generate-evaluate iteration for quality improvement
- specialist_pool: Expert routing for technical support
- debate: Pro-con deliberation for decision support
- reflexion: Execute-reflect-improve for complex problem solving
- mapreduce: Parallel map with aggregation for large-scale analysis

CLI Usage:
    python -m claude_agent_framework.cli --arch research -q "Analyze AI trends"
    python -m claude_agent_framework.cli --list
"""

# Import architectures to trigger registration (MUST be first)
import claude_agent_framework.architectures  # noqa: F401

# Primary API - simplified initialization (recommended)
from claude_agent_framework.config import (
    AgentConfig,
    FrameworkConfig,
    default_config,
    validate_api_key,
)
from claude_agent_framework.core import (
    AgentInstanceConfig,
    AgentSession,
    ArchitectureType,
    BaseArchitecture,
    ModelType,
    ModelTypeStr,
    RoleCardinality,
    RoleDefinition,
    RoleRegistry,
    RoleType,
    RoleTypeStr,
    get_architecture,
    list_architectures,
    register_architecture,
)
from claude_agent_framework.session import (
    InitializationError,
    create_session,
)
from claude_agent_framework.utils import (
    QuietTranscriptWriter,
    SubagentSession,
    SubagentTracker,
    ToolCallRecord,
    TranscriptWriter,
    process_message,
    quick_query,
    setup_session,
)

__version__ = "0.4.0"
__all__ = [
    # Primary API (new simplified interface)
    "create_session",
    "quick_query",
    "InitializationError",
    # Type definitions
    "ArchitectureType",
    "ModelType",
    "ModelTypeStr",
    # Role-based types (new)
    "RoleType",
    "RoleTypeStr",
    "RoleCardinality",
    "RoleDefinition",
    "AgentInstanceConfig",
    "RoleRegistry",
    # Core architecture
    "BaseArchitecture",
    "AgentSession",
    "register_architecture",
    "get_architecture",
    "list_architectures",
    # Configuration
    "FrameworkConfig",
    "AgentConfig",
    "default_config",
    "validate_api_key",
    # Tracking
    "SubagentTracker",
    "SubagentSession",
    "ToolCallRecord",
    # Transcript
    "TranscriptWriter",
    "QuietTranscriptWriter",
    "setup_session",
    # Message handling
    "process_message",
]
