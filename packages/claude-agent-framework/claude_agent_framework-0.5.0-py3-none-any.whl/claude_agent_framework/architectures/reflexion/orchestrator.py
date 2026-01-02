"""
Reflexion architecture orchestrator.

Implements execute-reflect-improve cycle:
1. Executor attempts the task
2. Reflector analyzes the result
3. If failed, Reflector provides improved strategy
4. Repeat until success or max attempts
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

from claude_agent_framework.architectures.reflexion.config import ReflexionConfig
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
class ReflectionRecord:
    """Record of a single reflection cycle."""

    attempt: int
    action: str
    result: str
    success: bool
    lessons_learned: list[str] = field(default_factory=list)
    next_strategy: str = ""


@register_architecture("reflexion")
class ReflexionArchitecture(BaseArchitecture):
    """
    Reflexion architecture for iterative problem solving.

    Pattern: Execute-Reflect-Improve
    - Executor: Attempts to solve the problem
    - Reflector: Analyzes results and provides insights
    - Loop: Iterate with improved strategies

    Usage:
        arch = ReflexionArchitecture()
        async for msg in arch.execute("Debug why tests are failing"):
            print(msg)
    """

    name = "reflexion"
    description = "Execute-reflect-improve cycle for complex problem solving and debugging"

    def __init__(
        self,
        config: ReflexionConfig | None = None,
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
        Initialize reflexion architecture.

        Args:
            config: Reflexion-specific configuration
            model_config: Model configuration
            prompts_dir: Custom prompts directory
            files_dir: Custom files directory
            agent_instances: List of agent instance configurations (role-based)
            business_template: Name of business template to use (optional)
            custom_prompts_dir: Application-level custom prompts directory (optional)
            prompt_overrides: Dict of agent_name -> override prompt content
            template_vars: Dict of template variables for ${var} substitution
        """
        self.reflexion_config = config or ReflexionConfig()

        if model_config is None:
            model_config = AgentModelConfig(
                default=self.reflexion_config.executor_model,
                overrides=self.reflexion_config.get_model_overrides(),
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

        self._reflection_history: list[ReflectionRecord] = []

    def get_role_definitions(self) -> dict[str, RoleDefinition]:
        """
        Get role definitions for reflexion architecture.

        Returns:
            Dict mapping role_id to RoleDefinition
        """
        return {
            "executor": RoleDefinition(
                role_type=RoleType.EXECUTOR,
                description="Execute tasks and attempt problem solutions",
                required_tools=["Read", "Write", "Edit", "Bash"],
                optional_tools=["Glob", "Grep", "Skill"],
                cardinality=RoleCardinality.EXACTLY_ONE,
                default_model=self.reflexion_config.executor_model,
                prompt_file="executor.txt",
            ),
            "reflector": RoleDefinition(
                role_type=RoleType.REFLECTOR,
                description="Analyze results and provide improvement strategies",
                required_tools=["Read"],
                optional_tools=["Glob", "Skill"],
                cardinality=RoleCardinality.EXACTLY_ONE,
                default_model=self.reflexion_config.reflector_model,
                prompt_file="reflector.txt",
            ),
        }

    def get_lead_prompt(self) -> str:
        """Get lead agent prompt with runtime configuration injected."""
        # Build agent list for template substitution
        executors = self.get_agents_by_role("executor")
        reflectors = self.get_agents_by_role("reflector")

        agent_lines = []
        if executors:
            agent_lines.append(f"- Executor: {', '.join(executors)}")
        if reflectors:
            agent_lines.append(f"- Reflector: {', '.join(reflectors)}")
        agent_list = "\n".join(agent_lines) if agent_lines else "- (using defaults)"

        # Inject runtime configuration into template variables
        self._template_vars.update({
            "max_iterations": str(self.reflexion_config.max_attempts),
            "success_indicators": ", ".join(self.reflexion_config.success_indicators),
            "failure_indicators": ", ".join(self.reflexion_config.failure_indicators),
            "agent_list": agent_list,
        })

        return super().get_lead_prompt()

    def _customize_prompt(self, prompt: str) -> str:
        """Wrap prompt as task."""
        return f"Task: {prompt}"

    async def execute(
        self,
        prompt: str,
        tracker: SubagentTracker | None = None,
        transcript: TranscriptWriter | None = None,
    ) -> AsyncIterator[Any]:
        """Execute reflexion loop."""
        prompt = self._apply_before_execute(prompt)
        task_prompt = self._customize_prompt(prompt)
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
            await client.query(prompt=task_prompt)

            async for msg in client.receive_response():
                yield msg

                if hasattr(msg, "content") and msg.content:
                    self._result = msg.content

    def get_reflection_history(self) -> list[ReflectionRecord]:
        """Get history of all reflection cycles."""
        return self._reflection_history

    def clear_history(self) -> None:
        """Clear reflection history."""
        self._reflection_history.clear()
