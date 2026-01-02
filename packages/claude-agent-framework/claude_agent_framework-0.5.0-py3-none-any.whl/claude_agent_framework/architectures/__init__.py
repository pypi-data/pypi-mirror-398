"""
Multi-architecture agent framework.

Available architectures:
- research: Master-worker pattern for deep research
- pipeline: Sequential stage processing
- critic_actor: Generate-evaluate iteration loop
- specialist_pool: Expert routing and dispatch
- debate: Pro-con deliberation with judge
- reflexion: Execute-reflect-improve cycle
- mapreduce: Parallel map with aggregation
"""

# Import architectures to trigger registration
from claude_agent_framework.architectures.critic_actor import CriticActorArchitecture
from claude_agent_framework.architectures.debate import DebateArchitecture
from claude_agent_framework.architectures.mapreduce import MapReduceArchitecture
from claude_agent_framework.architectures.pipeline import PipelineArchitecture
from claude_agent_framework.architectures.reflexion import ReflexionArchitecture
from claude_agent_framework.architectures.research import ResearchArchitecture
from claude_agent_framework.architectures.specialist_pool import SpecialistPoolArchitecture

__all__ = [
    "ResearchArchitecture",
    "PipelineArchitecture",
    "CriticActorArchitecture",
    "SpecialistPoolArchitecture",
    "DebateArchitecture",
    "ReflexionArchitecture",
    "MapReduceArchitecture",
]
