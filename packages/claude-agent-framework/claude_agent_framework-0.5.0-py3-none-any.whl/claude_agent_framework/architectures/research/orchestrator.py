"""
Research architecture orchestrator.

Implements master-worker coordination pattern:
1. Lead agent decomposes research task into subtopics
2. Multiple researcher agents gather information in parallel
3. Data analyst processes and visualizes findings
4. Report writer generates final output

Role-based architecture:
- worker: Parallel data gatherers (1 or more)
- processor: Data processor/analyzer (0 or 1)
- synthesizer: Report generator (exactly 1)
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

from claude_agent_framework.architectures.research.config import ResearchConfig
from claude_agent_framework.core.base import (
    AgentModelConfig,
    BaseArchitecture,
)
from claude_agent_framework.core.registry import register_architecture
from claude_agent_framework.core.roles import AgentInstanceConfig, RoleDefinition
from claude_agent_framework.core.types import RoleCardinality, RoleType

if TYPE_CHECKING:
    from claude_agent_framework.utils import SubagentTracker, TranscriptWriter


@register_architecture("research")
class ResearchArchitecture(BaseArchitecture):
    """
    Research architecture for deep research tasks.

    Pattern: Master-Worker Coordination
    - Lead agent: Task decomposition and orchestration
    - Workers: Parallel information gathering (1+ agents)
    - Processor: Data analysis and visualization (0-1 agent)
    - Synthesizer: Final report generation (1 agent)

    Role Definitions:
        worker: Gather research data via web search (required, 1+)
        processor: Analyze data and generate visualizations (optional, 0-1)
        synthesizer: Generate final reports (required, exactly 1)

    Usage:
        agents = [
            AgentInstanceConfig(name="market-researcher", role="worker", ...),
            AgentInstanceConfig(name="tech-researcher", role="worker", ...),
            AgentInstanceConfig(name="analyst", role="processor", ...),
            AgentInstanceConfig(name="writer", role="synthesizer", ...),
        ]
        arch = ResearchArchitecture(agent_instances=agents)
        async for msg in arch.execute("Research AI market trends"):
            print(msg)
    """

    name = "research"
    description = "Master-worker pattern for deep research with parallel data gathering"

    def __init__(
        self,
        config: ResearchConfig | None = None,
        model_config: AgentModelConfig | None = None,
        prompts_dir: Path | None = None,
        files_dir: Path | None = None,
        # Role-based configuration
        agent_instances: list[AgentInstanceConfig] | None = None,
        # Prompt customization (business_templates and skills support)
        business_template: str | None = None,
        custom_prompts_dir: Path | str | None = None,
        prompt_overrides: dict[str, str] | None = None,
        template_vars: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize research architecture.

        Args:
            config: Research-specific configuration
            model_config: Model configuration (overridden by config if provided)
            prompts_dir: Custom prompts directory
            files_dir: Custom files directory
            agent_instances: List of agent instance configurations (role-based)
            business_template: Name of business template for prompts
            custom_prompts_dir: Application-level custom prompts directory
            prompt_overrides: Dict of agent_name -> override prompt content
            template_vars: Dict of template variables for ${var} substitution
        """
        self.research_config = config or ResearchConfig()

        # Build model config from research config
        if model_config is None:
            model_config = AgentModelConfig(
                default=self.research_config.lead_model,
                overrides={},  # Overrides will come from agent instances
            )

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

    def get_role_definitions(self) -> dict[str, RoleDefinition]:
        """
        Get role definitions for research architecture.

        Returns:
            Dict mapping role_id to RoleDefinition
        """
        return {
            "worker": RoleDefinition(
                role_type=RoleType.WORKER,
                description="Gather research data via web search, save to files/research_notes/",
                required_tools=["WebSearch"],
                optional_tools=["Write", "Skill", "Read"],
                cardinality=RoleCardinality.ONE_OR_MORE,
                default_model=self.research_config.researcher_model,
                prompt_file="worker.txt",
            ),
            "processor": RoleDefinition(
                role_type=RoleType.PROCESSOR,
                description="Analyze research data and generate visualizations, save to files/charts/",
                required_tools=["Read", "Write"],
                optional_tools=["Glob", "Bash", "Skill"],
                cardinality=RoleCardinality.ZERO_OR_ONE,
                default_model=self.research_config.analyst_model,
                prompt_file="processor.txt",
            ),
            "synthesizer": RoleDefinition(
                role_type=RoleType.SYNTHESIZER,
                description="Generate final reports, save to files/reports/",
                required_tools=["Write"],
                optional_tools=["Skill", "Read", "Glob", "Bash"],
                cardinality=RoleCardinality.EXACTLY_ONE,
                default_model=self.research_config.writer_model,
                prompt_file="synthesizer.txt",
            ),
        }

    def get_lead_prompt(self) -> str:
        """Get lead agent prompt with research-specific context."""
        return super().get_lead_prompt()

    def _get_setting_sources(self) -> list[str]:
        """Research uses both project and user settings."""
        return ["project", "user"]

    async def setup(self) -> None:
        """Setup research directories."""
        await super().setup()

        # Create research-specific subdirectories
        for subdir in [
            self.research_config.research_notes_dir,
            self.research_config.data_dir,
            self.research_config.charts_dir,
            self.research_config.reports_dir,
        ]:
            (self.files_dir / subdir).mkdir(parents=True, exist_ok=True)

    async def execute(
        self,
        prompt: str,
        tracker: SubagentTracker | None = None,
        transcript: TranscriptWriter | None = None,
    ) -> AsyncIterator[Any]:
        """
        Execute research workflow.

        Args:
            prompt: Research topic or question
            tracker: Optional subagent tracker
            transcript: Optional transcript writer

        Yields:
            Messages from Claude SDK response stream
        """
        # Apply plugins
        prompt = self._apply_before_execute(prompt)

        # Apply prompt customization (extension point)
        prompt = self._customize_prompt(prompt)

        # Build hooks using base class method
        hooks = self._build_hooks(tracker)

        # Get lead prompt and agents
        lead_prompt = self.get_lead_prompt()
        agents = self.to_sdk_agents()

        # Configure SDK options using extension points
        options = ClaudeAgentOptions(
            permission_mode="bypassPermissions",
            setting_sources=self._get_setting_sources(),
            system_prompt=lead_prompt,
            allowed_tools=self._get_allowed_tools(),
            agents=agents,
            hooks=hooks,
            model=self.model_config.default,
        )

        # Execute with SDK client
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt=prompt)

            async for msg in client.receive_response():
                yield msg

                # Track result
                if hasattr(msg, "content") and msg.content:
                    self._result = msg.content
