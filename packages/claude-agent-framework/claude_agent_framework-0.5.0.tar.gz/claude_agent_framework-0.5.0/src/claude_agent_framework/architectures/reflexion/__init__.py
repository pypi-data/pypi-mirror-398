"""
Reflexion architecture implementation.

An execute-reflect-improve cycle for complex problem solving.
Executor attempts, Reflector analyzes, loop until success.
"""

from claude_agent_framework.architectures.reflexion.config import ReflexionConfig
from claude_agent_framework.architectures.reflexion.orchestrator import (
    ReflexionArchitecture,
)

__all__ = [
    "ReflexionArchitecture",
    "ReflexionConfig",
]
