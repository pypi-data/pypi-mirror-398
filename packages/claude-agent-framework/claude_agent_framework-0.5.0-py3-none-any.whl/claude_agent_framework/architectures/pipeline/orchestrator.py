"""
Pipeline architecture orchestrator.

Implements sequential stage processing:
1. Each stage processes input and produces output
2. Output flows to next stage as input
3. Final stage produces the result
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

from claude_agent_framework.architectures.pipeline.config import PipelineConfig
from claude_agent_framework.core.base import (
    AgentModelConfig,
    BaseArchitecture,
)
from claude_agent_framework.core.registry import register_architecture
from claude_agent_framework.core.roles import AgentInstanceConfig, RoleDefinition
from claude_agent_framework.core.types import RoleCardinality, RoleType

if TYPE_CHECKING:
    from claude_agent_framework.utils import SubagentTracker, TranscriptWriter


@register_architecture("pipeline")
class PipelineArchitecture(BaseArchitecture):
    """
    Pipeline architecture for sequential processing.

    Pattern: Sequential Stage Processing
    - Stage executors: Process stages in sequence (1+ agents)

    Role Definitions:
        stage: Execute a pipeline stage (required, 1+)

    Each stage's output becomes input for the next.

    Usage:
        agents = [
            AgentInstanceConfig(name="architect", role="stage", ...),
            AgentInstanceConfig(name="coder", role="stage", ...),
            AgentInstanceConfig(name="reviewer", role="stage", ...),
            AgentInstanceConfig(name="tester", role="stage", ...),
        ]
        arch = PipelineArchitecture(agent_instances=agents)
        async for msg in arch.execute("Implement user authentication"):
            print(msg)
    """

    name = "pipeline"
    description = "Sequential stage processing for code review and content creation"

    def __init__(
        self,
        config: PipelineConfig | None = None,
        model_config: AgentModelConfig | None = None,
        prompts_dir: Path | None = None,
        files_dir: Path | None = None,
        stages: list[str] | None = None,
        # Role-based configuration
        agent_instances: list[AgentInstanceConfig] | None = None,
        # Business template and prompt customization
        business_template: str | None = None,
        custom_prompts_dir: Path | str | None = None,
        prompt_overrides: dict[str, str] | None = None,
        template_vars: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize pipeline architecture.

        Args:
            config: Pipeline-specific configuration
            model_config: Model configuration
            prompts_dir: Custom prompts directory
            files_dir: Custom files directory
            stages: Custom stage names (uses config stages if None)
            agent_instances: List of agent instance configurations (role-based)
            business_template: Name of business template to use (optional)
            custom_prompts_dir: Application-level custom prompts directory (optional)
            prompt_overrides: Dict of agent_name -> override prompt content
            template_vars: Dict of template variables for ${var} substitution
        """
        self.pipeline_config = config or PipelineConfig()

        # Allow overriding stages via constructor
        if stages:
            self.pipeline_config.stages = [
                s for s in self.pipeline_config.stages if s.name in stages
            ]

        if model_config is None:
            model_config = AgentModelConfig(default=self.pipeline_config.lead_model)

        super().__init__(
            model_config=model_config,
            prompts_dir=prompts_dir,
            files_dir=files_dir,
            agent_instances=agent_instances,
            business_template=business_template,
            custom_prompts_dir=custom_prompts_dir,
            prompt_overrides=prompt_overrides,
            template_vars=template_vars,
        )

        self._stage_results: dict[str, Any] = {}

    def get_role_definitions(self) -> dict[str, RoleDefinition]:
        """
        Get role definitions for pipeline architecture.

        Returns:
            Dict mapping role_id to RoleDefinition
        """
        return {
            "stage": RoleDefinition(
                role_type=RoleType.EXECUTOR,
                description="Execute a pipeline stage with specific responsibilities",
                required_tools=["Read"],
                optional_tools=["Write", "Edit", "Bash", "Glob", "Grep", "Skill"],
                cardinality=RoleCardinality.ONE_OR_MORE,
                default_model=self.pipeline_config.lead_model,
                prompt_file="stage.txt",
            ),
        }

    def get_agents(self) -> dict[str, AgentDefinitionConfig]:
        """Get agent definitions for all pipeline stages (legacy support)."""
        from claude_agent_framework.core.base import AgentDefinitionConfig

        return {stage.agent.name: stage.agent for stage in self.pipeline_config.stages}

    def get_lead_prompt(self) -> str:
        """Get lead agent prompt with runtime configuration injected."""
        # Build stage list for template substitution
        stage_lines = []
        for i, stage in enumerate(self.pipeline_config.stages, 1):
            stage_lines.append(f"### Stage {i}: {stage.name}")
            stage_lines.append(f"- {stage.agent.description}")
            stage_lines.append("")
        stage_list = "\n".join(stage_lines) if stage_lines else "- (no stages configured)"

        # Inject runtime configuration into template variables
        self._template_vars.update({
            "total_stages": str(len(self.pipeline_config.stages)),
            "stage_list": stage_list,
        })

        return super().get_lead_prompt()

    async def execute(
        self,
        prompt: str,
        tracker: SubagentTracker | None = None,
        transcript: TranscriptWriter | None = None,
    ) -> AsyncIterator[Any]:
        """
        Execute pipeline stages sequentially.

        Args:
            prompt: Initial task description
            tracker: Optional subagent tracker
            transcript: Optional transcript writer

        Yields:
            Messages from each stage's execution
        """
        prompt = self._apply_before_execute(prompt)
        prompt = self._customize_prompt(prompt)
        hooks = self._build_hooks(tracker)
        lead_prompt = self.get_lead_prompt()
        agents = self.to_sdk_agents()

        options = ClaudeAgentOptions(
            permission_mode="bypassPermissions",
            setting_sources=self._get_setting_sources(),
            system_prompt=lead_prompt,
            allowed_tools=self._get_allowed_tools(),
            agents=agents,
            hooks=hooks,
            model=self.model_config.default,
        )

        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt=prompt)

            async for msg in client.receive_response():
                yield msg

                if hasattr(msg, "content") and msg.content:
                    self._result = msg.content

    def get_stage_result(self, stage_name: str) -> Any:
        """Get result from a specific stage."""
        return self._stage_results.get(stage_name)

    def configure_stages(self, stages: list[str]) -> None:
        """
        Configure which stages to run.

        Args:
            stages: List of stage names to include
        """
        self.pipeline_config.stages = [s for s in self.pipeline_config.stages if s.name in stages]

    def transform_stage_output(self, stage: str, output: str) -> str:
        """
        Transform stage output before passing to next stage.

        Override in subclasses for custom transformation.

        Args:
            stage: Stage name
            output: Stage output content

        Returns:
            Transformed output for next stage
        """
        return f"## {stage} Stage Output\n{output}\n\nPlease continue with the next stage based on the above results."
