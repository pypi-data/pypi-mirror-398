"""
Debate architecture orchestrator.

Implements pro-con deliberation:
1. Proponent presents supporting arguments
2. Opponent presents counter-arguments
3. Multiple rounds of debate
4. Judge evaluates and decides
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

from claude_agent_framework.architectures.debate.config import DebateConfig
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
class DebateRound:
    """Record of a single debate round."""

    round_number: int
    proponent_argument: str
    opponent_argument: str


@dataclass
class Verdict:
    """Judge's final verdict."""

    decision: str  # pro, con, neutral
    confidence: str  # high, medium, low
    reasoning: str
    scores: dict[str, float] = field(default_factory=dict)


@register_architecture("debate")
class DebateArchitecture(BaseArchitecture):
    """
    Debate architecture for decision support.

    Pattern: Pro-Con Deliberation
    - Proponent: Argues in favor
    - Opponent: Argues against
    - Judge: Evaluates and decides

    Usage:
        arch = DebateArchitecture()
        async for msg in arch.execute("Should we use microservices?"):
            print(msg)
    """

    name = "debate"
    description = "Pro-con deliberation with judge for decision support and risk assessment"

    def __init__(
        self,
        config: DebateConfig | None = None,
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
        Initialize debate architecture.

        Args:
            config: Debate-specific configuration
            model_config: Model configuration
            prompts_dir: Custom prompts directory
            files_dir: Custom files directory
            agent_instances: List of agent instance configurations (role-based)
            business_template: Name of business template to use (optional)
            custom_prompts_dir: Application-level custom prompts directory (optional)
            prompt_overrides: Dict of agent_name -> override prompt content
            template_vars: Dict of template variables for ${var} substitution
        """
        self.debate_config = config or DebateConfig()

        if model_config is None:
            model_config = AgentModelConfig(
                default=self.debate_config.proponent_model,
                overrides=self.debate_config.get_model_overrides(),
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

        self._debate_history: list[DebateRound] = []
        self._verdict: Verdict | None = None

    def get_role_definitions(self) -> dict[str, RoleDefinition]:
        """
        Get role definitions for debate architecture.

        Returns:
            Dict mapping role_id to RoleDefinition
        """
        return {
            "proponent": RoleDefinition(
                role_type=RoleType.ADVOCATE,
                description="Argue the pro position with evidence-based reasoning",
                required_tools=["Read"],
                optional_tools=["WebSearch", "Skill"],
                cardinality=RoleCardinality.EXACTLY_ONE,
                default_model=self.debate_config.proponent_model,
                prompt_file="proponent.txt",
            ),
            "opponent": RoleDefinition(
                role_type=RoleType.ADVOCATE,
                description="Argue the con position with counter-evidence",
                required_tools=["Read"],
                optional_tools=["WebSearch", "Skill"],
                cardinality=RoleCardinality.EXACTLY_ONE,
                default_model=self.debate_config.opponent_model,
                prompt_file="opponent.txt",
            ),
            "judge": RoleDefinition(
                role_type=RoleType.JUDGE,
                description="Evaluate arguments and render final verdict",
                required_tools=["Read"],
                optional_tools=["Skill"],
                cardinality=RoleCardinality.EXACTLY_ONE,
                default_model=self.debate_config.judge_model,
                prompt_file="judge.txt",
            ),
        }

    def get_lead_prompt(self) -> str:
        """Get lead agent prompt with runtime configuration injected."""
        # Build agent list for template substitution
        proponents = self.get_agents_by_role("proponent")
        opponents = self.get_agents_by_role("opponent")
        judges = self.get_agents_by_role("judge")

        agent_lines = []
        if proponents:
            agent_lines.append(f"- Proponent: {', '.join(proponents)}")
        if opponents:
            agent_lines.append(f"- Opponent: {', '.join(opponents)}")
        if judges:
            agent_lines.append(f"- Judge: {', '.join(judges)}")
        agent_list = "\n".join(agent_lines) if agent_lines else "- (using defaults)"

        # Inject runtime configuration into template variables
        self._template_vars.update({
            "max_rounds": str(self.debate_config.debate_rounds),
            "agent_list": agent_list,
        })

        return super().get_lead_prompt()

    def _customize_prompt(self, prompt: str) -> str:
        """Wrap prompt as debate topic."""
        return f"Debate Topic: {prompt}"

    async def execute(
        self,
        prompt: str,
        tracker: SubagentTracker | None = None,
        transcript: TranscriptWriter | None = None,
    ) -> AsyncIterator[Any]:
        """Execute debate workflow."""
        prompt = self._apply_before_execute(prompt)
        debate_prompt = self._customize_prompt(prompt)
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
            await client.query(prompt=debate_prompt)

            async for msg in client.receive_response():
                yield msg

                if hasattr(msg, "content") and msg.content:
                    self._result = msg.content

    def get_debate_history(self) -> list[DebateRound]:
        """Get history of all debate rounds."""
        return self._debate_history

    def get_verdict(self) -> Verdict | None:
        """Get the final verdict."""
        return self._verdict
