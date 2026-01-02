"""
Critic-Actor architecture implementation.

A generate-evaluate iteration loop for quality improvement.
Actor generates content, Critic evaluates, iterate until quality threshold.
"""

from claude_agent_framework.architectures.critic_actor.config import CriticActorConfig
from claude_agent_framework.architectures.critic_actor.orchestrator import (
    CriticActorArchitecture,
)

__all__ = [
    "CriticActorArchitecture",
    "CriticActorConfig",
]
