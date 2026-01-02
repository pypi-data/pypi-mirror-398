"""
Pipeline architecture configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from claude_agent_framework.core.base import AgentDefinitionConfig


@dataclass
class StageConfig:
    """
    Configuration for a single pipeline stage.

    Attributes:
        name: Stage identifier
        agent: Agent configuration for this stage
        transform_output: Whether to transform output before passing to next stage
        required: Whether this stage is required (skip if False and conditions not met)
    """

    name: str
    agent: AgentDefinitionConfig
    transform_output: bool = True
    required: bool = True


@dataclass
class PipelineConfig:
    """
    Configuration for the Pipeline architecture.

    Attributes:
        stages: List of pipeline stages in order
        stop_on_failure: Whether to stop pipeline on stage failure
        pass_full_context: Whether to pass full context or just stage output
        lead_model: Model for pipeline coordinator
    """

    stages: list[StageConfig] = field(default_factory=list)
    stop_on_failure: bool = True
    pass_full_context: bool = False
    lead_model: str = "haiku"

    def __post_init__(self) -> None:
        """Initialize default stages if none provided."""
        if not self.stages:
            self.stages = self._default_stages()

    def _default_stages(self) -> list[StageConfig]:
        """Default code review pipeline stages."""
        return [
            StageConfig(
                name="architect",
                agent=AgentDefinitionConfig(
                    name="architect",
                    description="设计实现方案和架构",
                    tools=["Read", "Glob", "Write"],
                    prompt_file="architect.txt",
                ),
            ),
            StageConfig(
                name="coder",
                agent=AgentDefinitionConfig(
                    name="coder",
                    description="根据设计实现代码",
                    tools=["Read", "Write", "Edit", "Bash"],
                    prompt_file="coder.txt",
                ),
            ),
            StageConfig(
                name="reviewer",
                agent=AgentDefinitionConfig(
                    name="reviewer",
                    description="审查代码质量和规范",
                    tools=["Read", "Glob", "Grep"],
                    prompt_file="reviewer.txt",
                ),
            ),
            StageConfig(
                name="tester",
                agent=AgentDefinitionConfig(
                    name="tester",
                    description="编写和运行测试",
                    tools=["Read", "Write", "Bash"],
                    prompt_file="tester.txt",
                ),
            ),
        ]

    def get_stage_names(self) -> list[str]:
        """Get ordered list of stage names."""
        return [s.name for s in self.stages]

    def get_stage(self, name: str) -> StageConfig | None:
        """Get stage by name."""
        for stage in self.stages:
            if stage.name == name:
                return stage
        return None
