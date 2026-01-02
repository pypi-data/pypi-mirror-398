"""
Pipeline architecture implementation.

A sequential stage processing pattern for tasks like code review, content creation.
Each stage's output becomes the next stage's input.
"""

from claude_agent_framework.architectures.pipeline.config import (
    PipelineConfig,
    StageConfig,
)
from claude_agent_framework.architectures.pipeline.orchestrator import (
    PipelineArchitecture,
)

__all__ = [
    "PipelineArchitecture",
    "PipelineConfig",
    "StageConfig",
]
