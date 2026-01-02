"""
MapReduce architecture orchestrator.

Implements parallel map with aggregation:
1. Splitter divides task into chunks
2. Mappers process chunks in parallel
3. Reducer aggregates all results
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

from claude_agent_framework.architectures.mapreduce.config import MapReduceConfig
from claude_agent_framework.architectures.mapreduce.splitter import TaskSplitter
from claude_agent_framework.core.base import (
    AgentModelConfig,
    BaseArchitecture,
)
from claude_agent_framework.core.registry import register_architecture
from claude_agent_framework.core.roles import AgentInstanceConfig, RoleDefinition
from claude_agent_framework.core.types import RoleCardinality, RoleType

if TYPE_CHECKING:
    from claude_agent_framework.utils import SubagentTracker, TranscriptWriter


@register_architecture("mapreduce")
class MapReduceArchitecture(BaseArchitecture):
    """
    MapReduce architecture for parallel processing.

    Pattern: Parallel Map with Aggregation
    - Mappers: Process chunks in parallel (1+ agents)
    - Reducer: Aggregates results (1 agent)

    Role Definitions:
        mapper: Process assigned data chunks (required, 1+)
        reducer: Aggregate all results (required, exactly 1)

    Usage:
        agents = [
            AgentInstanceConfig(name="code-analyzer", role="mapper", ...),
            AgentInstanceConfig(name="metrics-collector", role="mapper", ...),
            AgentInstanceConfig(name="report-aggregator", role="reducer", ...),
        ]
        arch = MapReduceArchitecture(agent_instances=agents)
        async for msg in arch.execute("Analyze all Python files"):
            print(msg)
    """

    name = "mapreduce"
    description = "Parallel map with aggregation for large-scale analysis"

    def __init__(
        self,
        config: MapReduceConfig | None = None,
        model_config: AgentModelConfig | None = None,
        prompts_dir: Path | None = None,
        files_dir: Path | None = None,
        # Role-based configuration
        agent_instances: list[AgentInstanceConfig] | None = None,
        # Business template and prompt customization
        business_template: str | None = None,
        custom_prompts_dir: Path | str | None = None,
        prompt_overrides: dict[str, str] | None = None,
        template_vars: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize mapreduce architecture.

        Args:
            config: MapReduce-specific configuration
            model_config: Model configuration
            prompts_dir: Custom prompts directory
            files_dir: Custom files directory
            agent_instances: List of agent instance configurations (role-based)
            business_template: Name of business template to use (optional)
            custom_prompts_dir: Application-level custom prompts directory (optional)
            prompt_overrides: Dict of agent_name -> override prompt content
            template_vars: Dict of template variables for ${var} substitution
        """
        self.mapreduce_config = config or MapReduceConfig()
        self.splitter = TaskSplitter(chunk_size=self.mapreduce_config.chunk_size)

        if model_config is None:
            model_config = AgentModelConfig(
                default=self.mapreduce_config.mapper_model,
                overrides={},
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

        self._mapper_results: list[str] = []

    def get_role_definitions(self) -> dict[str, RoleDefinition]:
        """
        Get role definitions for mapreduce architecture.

        Returns:
            Dict mapping role_id to RoleDefinition
        """
        return {
            "mapper": RoleDefinition(
                role_type=RoleType.WORKER,
                description="Process assigned data chunks and generate intermediate results",
                required_tools=["Read", "Glob", "Grep"],
                optional_tools=["Write", "Skill"],
                cardinality=RoleCardinality.ONE_OR_MORE,
                default_model=self.mapreduce_config.mapper_model,
                prompt_file="mapper.txt",
            ),
            "reducer": RoleDefinition(
                role_type=RoleType.SYNTHESIZER,
                description="Aggregate all mapper results and generate final output",
                required_tools=["Read", "Write"],
                optional_tools=["Glob", "Skill"],
                cardinality=RoleCardinality.EXACTLY_ONE,
                default_model=self.mapreduce_config.reducer_model,
                prompt_file="reducer.txt",
            ),
        }

    def get_agents(self) -> dict[str, AgentDefinitionConfig]:
        """Get mapper and reducer agent definitions (legacy support)."""
        # This method is kept for backward compatibility
        # New code should use get_role_definitions() with agent_instances
        from claude_agent_framework.core.base import AgentDefinitionConfig

        return {
            "mapper": AgentDefinitionConfig(
                name="mapper",
                description="Process assigned data chunks and generate intermediate results",
                tools=["Read", "Glob", "Grep", "Write"],
                prompt_file="mapper.txt",
            ),
            "reducer": AgentDefinitionConfig(
                name="reducer",
                description="Aggregate all mapper results and generate final output",
                tools=["Read", "Glob", "Write"],
                prompt_file="reducer.txt",
            ),
        }

    def get_lead_prompt(self) -> str:
        """Get lead agent prompt with runtime configuration injected."""
        # Build agent list for template substitution
        mappers = self.get_agents_by_role("mapper")
        reducers = self.get_agents_by_role("reducer")

        agent_lines = []
        if mappers:
            agent_lines.append(f"- Mappers: {', '.join(mappers)}")
        if reducers:
            agent_lines.append(f"- Reducer: {', '.join(reducers)}")
        agent_list = "\n".join(agent_lines) if agent_lines else "- (using defaults)"

        # Inject runtime configuration into template variables
        self._template_vars.update({
            "max_mappers": str(self.mapreduce_config.max_mappers),
            "chunk_size": str(self.mapreduce_config.chunk_size),
            "split_strategy": self.mapreduce_config.split_strategy,
            "aggregation_method": self.mapreduce_config.aggregation_method,
            "agent_list": agent_list,
        })

        return super().get_lead_prompt()

    def _get_allowed_tools(self) -> list[str]:
        """MapReduce lead needs Glob for file discovery."""
        return ["Task", "Glob"]

    def _customize_prompt(self, prompt: str) -> str:
        """Wrap prompt as MapReduce task."""
        return f"MapReduce Task: {prompt}"

    async def execute(
        self,
        prompt: str,
        tracker: SubagentTracker | None = None,
        transcript: TranscriptWriter | None = None,
    ) -> AsyncIterator[Any]:
        """Execute mapreduce workflow."""
        prompt = self._apply_before_execute(prompt)
        mr_prompt = self._customize_prompt(prompt)
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
            await client.query(prompt=mr_prompt)

            async for msg in client.receive_response():
                yield msg

                if hasattr(msg, "content") and msg.content:
                    self._result = msg.content

    def get_mapper_results(self) -> list[str]:
        """Get results from all mappers."""
        return self._mapper_results
