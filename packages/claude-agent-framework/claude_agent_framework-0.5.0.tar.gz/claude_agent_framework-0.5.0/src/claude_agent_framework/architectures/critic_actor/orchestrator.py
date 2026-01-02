"""
Critic-Actor architecture orchestrator.

Implements generate-evaluate loop:
1. Actor generates content
2. Critic evaluates with feedback
3. Actor improves based on feedback
4. Repeat until quality threshold or max iterations

Role-based architecture:
- actor: Content generator/improver (exactly 1)
- critic: Quality evaluator (exactly 1)
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

from claude_agent_framework.architectures.critic_actor.config import CriticActorConfig
from claude_agent_framework.core.base import (
    AgentModelConfig,
    BaseArchitecture,
)
from claude_agent_framework.core.registry import register_architecture
from claude_agent_framework.core.roles import AgentInstanceConfig, RoleDefinition
from claude_agent_framework.core.types import RoleCardinality, RoleType

if TYPE_CHECKING:
    from claude_agent_framework.utils import SubagentTracker, TranscriptWriter


@dataclass
class IterationRecord:
    """Record of a single iteration."""

    iteration: int
    actor_output: str
    critic_feedback: str
    quality_score: float
    approved: bool


@register_architecture("critic_actor")
class CriticActorArchitecture(BaseArchitecture):
    """
    Critic-Actor architecture for iterative improvement.

    Pattern: Generate-Evaluate Loop
    - Actor: Generates or improves content
    - Critic: Evaluates and provides feedback
    - Loop: Iterate until quality threshold

    Role Definitions:
        actor: Generate or improve content (required, exactly 1)
        critic: Evaluate quality and provide feedback (required, exactly 1)

    Usage:
        agents = [
            AgentInstanceConfig(name="content_creator", role="actor", ...),
            AgentInstanceConfig(name="brand_reviewer", role="critic", ...),
        ]
        arch = CriticActorArchitecture(agent_instances=agents)
        async for msg in arch.execute("Write a Python function for sorting"):
            print(msg)
    """

    name = "critic_actor"
    description = "Generate-evaluate iteration loop for code optimization and quality"

    def __init__(
        self,
        config: CriticActorConfig | None = None,
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
        Initialize critic-actor architecture.

        Args:
            config: Critic-Actor specific configuration
            model_config: Model configuration
            prompts_dir: Custom prompts directory
            files_dir: Custom files directory
            agent_instances: List of agent instance configurations (role-based)
            business_template: Name of business template to use (optional)
            custom_prompts_dir: Application-level custom prompts directory (optional)
            prompt_overrides: Dict of agent_name -> override prompt content
            template_vars: Dict of template variables for ${var} substitution
        """
        self.critic_config = config or CriticActorConfig()

        if model_config is None:
            model_config = AgentModelConfig(
                default=self.critic_config.actor_model,
                overrides=self.critic_config.get_model_overrides(),
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

        self._iteration_history: list[IterationRecord] = []

    def get_role_definitions(self) -> dict[str, RoleDefinition]:
        """
        Get role definitions for critic-actor architecture.

        Returns:
            Dict mapping role_id to RoleDefinition
        """
        return {
            "actor": RoleDefinition(
                role_type=RoleType.EXECUTOR,
                description="Generate or improve content based on task and feedback",
                required_tools=["Read", "Write", "Edit"],
                optional_tools=["Glob", "Bash", "Skill"],
                cardinality=RoleCardinality.EXACTLY_ONE,
                default_model=self.critic_config.actor_model,
                prompt_file="actor.txt",
            ),
            "critic": RoleDefinition(
                role_type=RoleType.CRITIC,
                description="Evaluate content quality and provide improvement feedback",
                required_tools=["Read"],
                optional_tools=["Glob", "Grep", "Skill"],
                cardinality=RoleCardinality.EXACTLY_ONE,
                default_model=self.critic_config.critic_model,
                prompt_file="critic.txt",
            ),
        }

    def get_lead_prompt(self) -> str:
        """Get lead agent prompt with runtime configuration injected."""
        # Build agent list for template substitution
        actors = self.get_agents_by_role("actor")
        critics = self.get_agents_by_role("critic")

        agent_lines = []
        if actors:
            agent_lines.append(f"- Actor: {', '.join(actors)}")
        if critics:
            agent_lines.append(f"- Critic: {', '.join(critics)}")
        agent_list = "\n".join(agent_lines) if agent_lines else "- (using defaults)"

        # Inject runtime configuration into template variables
        self._template_vars.update({
            "max_iterations": str(self.critic_config.max_iterations),
            "quality_threshold": str(self.critic_config.quality_threshold),
            "agent_list": agent_list,
        })

        return super().get_lead_prompt()

    async def execute(
        self,
        prompt: str,
        tracker: SubagentTracker | None = None,
        transcript: TranscriptWriter | None = None,
    ) -> AsyncIterator[Any]:
        """Execute critic-actor iteration loop."""
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

    def get_iteration_history(self) -> list[IterationRecord]:
        """Get history of all iterations."""
        return self._iteration_history

    def clear_history(self) -> None:
        """Clear iteration history."""
        self._iteration_history.clear()
