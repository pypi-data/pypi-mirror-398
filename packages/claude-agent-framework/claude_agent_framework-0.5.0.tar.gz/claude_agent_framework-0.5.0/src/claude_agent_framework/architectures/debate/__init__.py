"""
Debate architecture implementation.

A pro-con deliberation pattern with judge for decision support.
Proponent argues for, Opponent argues against, Judge makes final decision.
"""

from claude_agent_framework.architectures.debate.config import DebateConfig
from claude_agent_framework.architectures.debate.orchestrator import DebateArchitecture

__all__ = [
    "DebateArchitecture",
    "DebateConfig",
]
