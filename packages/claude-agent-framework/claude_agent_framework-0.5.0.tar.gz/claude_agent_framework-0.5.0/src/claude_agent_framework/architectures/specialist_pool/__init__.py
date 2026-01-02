"""
Specialist Pool architecture implementation.

An expert routing and dispatch pattern for technical support.
Router analyzes queries and dispatches to appropriate domain experts.
"""

from claude_agent_framework.architectures.specialist_pool.config import (
    ExpertConfig,
    SpecialistPoolConfig,
)
from claude_agent_framework.architectures.specialist_pool.orchestrator import (
    SpecialistPoolArchitecture,
)
from claude_agent_framework.architectures.specialist_pool.router import ExpertRouter

__all__ = [
    "SpecialistPoolArchitecture",
    "SpecialistPoolConfig",
    "ExpertConfig",
    "ExpertRouter",
]
