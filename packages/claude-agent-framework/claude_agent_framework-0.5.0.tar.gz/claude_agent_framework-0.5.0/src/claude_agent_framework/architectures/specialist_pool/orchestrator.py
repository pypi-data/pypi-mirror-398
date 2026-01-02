"""
Specialist Pool architecture orchestrator.

Implements expert routing and dispatch:
1. Router analyzes incoming query
2. Selects appropriate expert(s)
3. Dispatches query to expert(s)
4. Aggregates responses
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

from claude_agent_framework.architectures.specialist_pool.config import (
    SpecialistPoolConfig,
)
from claude_agent_framework.architectures.specialist_pool.router import ExpertRouter
from claude_agent_framework.core.base import (
    AgentModelConfig,
    BaseArchitecture,
)
from claude_agent_framework.core.registry import register_architecture
from claude_agent_framework.core.roles import AgentInstanceConfig, RoleDefinition
from claude_agent_framework.core.types import RoleCardinality, RoleType

if TYPE_CHECKING:
    from claude_agent_framework.utils import SubagentTracker, TranscriptWriter


@register_architecture("specialist_pool")
class SpecialistPoolArchitecture(BaseArchitecture):
    """
    Specialist Pool architecture for expert routing.

    Pattern: Expert Pool Dispatch
    - Specialists: Domain experts handle specific topics (1+ agents)

    Role Definitions:
        specialist: Domain expert for specific topics (required, 1+)

    Usage:
        agents = [
            AgentInstanceConfig(name="network-expert", role="specialist", ...),
            AgentInstanceConfig(name="security-expert", role="specialist", ...),
            AgentInstanceConfig(name="database-expert", role="specialist", ...),
        ]
        arch = SpecialistPoolArchitecture(agent_instances=agents)
        async for msg in arch.execute("How do I fix this SQL injection?"):
            print(msg)
    """

    name = "specialist_pool"
    description = "Expert routing and dispatch for technical support and diagnostics"

    def __init__(
        self,
        config: SpecialistPoolConfig | None = None,
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
        Initialize specialist pool architecture.

        Args:
            config: Specialist pool configuration
            model_config: Model configuration
            prompts_dir: Custom prompts directory
            files_dir: Custom files directory
            agent_instances: List of agent instance configurations (role-based)
            business_template: Name of business template to use (optional)
            custom_prompts_dir: Application-level custom prompts directory (optional)
            prompt_overrides: Dict of agent_name -> override prompt content
            template_vars: Dict of template variables for ${var} substitution
        """
        self.pool_config = config or SpecialistPoolConfig()
        self.router = ExpertRouter(self.pool_config)

        if model_config is None:
            model_config = AgentModelConfig(default=self.pool_config.router_model)

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
        Get role definitions for specialist pool architecture.

        Returns:
            Dict mapping role_id to RoleDefinition
        """
        return {
            "specialist": RoleDefinition(
                role_type=RoleType.SPECIALIST,
                description="Domain expert for specific technical topics",
                required_tools=["Read"],
                optional_tools=["WebSearch", "Bash", "Glob", "Grep", "Skill"],
                cardinality=RoleCardinality.ONE_OR_MORE,
                default_model=self.pool_config.router_model,
                prompt_file="specialist.txt",
            ),
        }

    def get_agents(self) -> dict[str, AgentDefinitionConfig]:
        """Get all expert agent definitions (legacy support)."""
        # This method is kept for backward compatibility with config-based experts
        from claude_agent_framework.core.base import AgentDefinitionConfig

        return {expert.agent.name: expert.agent for expert in self.pool_config.experts}

    def get_lead_prompt(self) -> str:
        """Get lead agent prompt with runtime configuration injected."""
        # Build expert list for template substitution
        expert_lines = []
        for e in self.pool_config.experts:
            expert_lines.append(f"### {e.name}")
            expert_lines.append(f"- Domain: {e.domain}")
            expert_lines.append(f"- Responsibility: {e.agent.description}")
            expert_lines.append("")
        expert_list = "\n".join(expert_lines) if expert_lines else "- (no specialists configured)"

        # Inject runtime configuration into template variables
        self._template_vars.update({
            "expert_list": expert_list,
        })

        return super().get_lead_prompt()

    def _customize_prompt(self, prompt: str) -> str:
        """Add routing analysis to the prompt."""
        routing = self.router.route(prompt)
        return f"""
User Question: {prompt}

Routing Analysis:
- Recommended Experts: {", ".join(routing.experts)}
- Confidence: {routing.confidence:.2f}
- Reasoning: {routing.reasoning}

Please dispatch tasks to appropriate experts based on the above analysis.
"""

    async def execute(
        self,
        prompt: str,
        tracker: SubagentTracker | None = None,
        transcript: TranscriptWriter | None = None,
    ) -> AsyncIterator[Any]:
        """Execute expert routing and dispatch."""
        prompt = self._apply_before_execute(prompt)

        # Apply prompt customization (adds routing analysis)
        enhanced_prompt = self._customize_prompt(prompt)

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
            await client.query(prompt=enhanced_prompt)

            async for msg in client.receive_response():
                yield msg

                if hasattr(msg, "content") and msg.content:
                    self._result = msg.content

    def add_expert(self, expert_config) -> None:
        """Add a new expert to the pool."""
        self.router.add_expert(expert_config)

    def remove_expert(self, name: str) -> bool:
        """Remove an expert from the pool."""
        return self.router.remove_expert(name)
