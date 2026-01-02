"""
Research architecture implementation.

A master-worker coordination pattern for deep research tasks.
Lead agent decomposes tasks and dispatches specialized subagents.
"""

from claude_agent_framework.architectures.research.config import ResearchConfig
from claude_agent_framework.architectures.research.orchestrator import (
    ResearchArchitecture,
)

__all__ = [
    "ResearchArchitecture",
    "ResearchConfig",
]
