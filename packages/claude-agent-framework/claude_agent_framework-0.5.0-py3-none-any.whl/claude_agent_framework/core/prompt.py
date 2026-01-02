"""
Prompt composition system for Claude Agent Framework.

Provides layered prompt composition with support for:
- Architecture core prompts (role + capabilities + constraints)
- Business templates (business-specific instructions)
- Custom overrides (application-level customization)
- Template variable substitution
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from string import Template
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


class PromptCompositionError(Exception):
    """Raised when prompt composition fails."""

    pass


@dataclass
class PromptComposer:
    """
    Prompt composer for layered prompt composition.

    Combines architecture core prompts with business prompts following
    a priority-based resolution strategy.

    Final Prompt = Architecture Core Prompt + Business Prompt

    Business Prompt Sources (highest to lowest priority):
    1. prompt_overrides[agent_name] - Code parameter override
    2. custom_prompts_dir/<agent>.txt - Application custom directory
    3. business_templates/<template>/<agent>.txt - Business template
    4. Empty (core prompt only)

    Attributes:
        architecture_prompts_dir: Directory containing architecture core prompts
        business_template: Name of business template to use (optional)
        custom_prompts_dir: Application-level custom prompts directory (optional)
        prompt_overrides: Dict of agent_name -> override prompt content
        template_vars: Dict of template variables for substitution
    """

    architecture_prompts_dir: Path
    business_template: str | None = None
    custom_prompts_dir: Path | None = None
    prompt_overrides: dict[str, str] = field(default_factory=dict)
    template_vars: dict[str, Any] = field(default_factory=dict)

    def compose(self, agent_name: str) -> str:
        """
        Compose final prompt for an agent.

        Combines architecture core prompt with business prompt,
        then applies template variable substitution.

        Args:
            agent_name: Name of the agent (e.g., "researcher", "data_analyst")

        Returns:
            Composed prompt string
        """
        core = self._load_core(agent_name)
        business = self._load_business(agent_name)

        # Combine core and business prompts
        if core and business:
            combined = f"{core}\n\n{business}"
        else:
            combined = core or business or ""

        # Apply template variable substitution
        if self.template_vars and combined:
            combined = self._apply_template_vars(combined)

        return combined

    def compose_lead(self) -> str:
        """
        Compose final prompt for the lead agent.

        Similar to compose() but uses "lead_agent" as the agent name.

        Returns:
            Composed lead agent prompt string
        """
        return self.compose("lead_agent")

    def _load_core(self, agent_name: str) -> str:
        """
        Load architecture core prompt.

        Core prompts define the agent's role, capabilities, and constraints.
        They are always loaded from the architecture's prompts directory.

        Args:
            agent_name: Name of the agent

        Returns:
            Core prompt content, or empty string if not found
        """
        prompt_file = self.architecture_prompts_dir / f"{agent_name}.txt"
        if prompt_file.exists():
            return prompt_file.read_text(encoding="utf-8").strip()
        return ""

    def _load_business(self, agent_name: str) -> str:
        """
        Load business prompt following priority resolution.

        Priority (highest to lowest):
        1. prompt_overrides[agent_name]
        2. custom_prompts_dir/<agent>.txt
        3. business_templates/<template>/<agent>.txt

        Args:
            agent_name: Name of the agent

        Returns:
            Business prompt content, or empty string if none found
        """
        # Priority 1: Code parameter override
        if agent_name in self.prompt_overrides:
            return self.prompt_overrides[agent_name]

        # Priority 2: Application custom directory
        if self.custom_prompts_dir:
            custom_file = self.custom_prompts_dir / f"{agent_name}.txt"
            if custom_file.exists():
                return custom_file.read_text(encoding="utf-8").strip()

        # Priority 3: Business template
        if self.business_template:
            from claude_agent_framework.business_templates import load_template_prompt

            template_prompt = load_template_prompt(self.business_template, agent_name)
            if template_prompt:
                return template_prompt

        # No business prompt found
        return ""

    def _apply_template_vars(self, content: str) -> str:
        """
        Apply template variable substitution.

        Uses Python's string.Template with safe_substitute for ${var} syntax.
        Missing variables are left as-is (not replaced).

        Args:
            content: Template content with ${var} placeholders

        Returns:
            Content with variables substituted
        """
        try:
            return Template(content).safe_substitute(self.template_vars)
        except Exception:
            # If substitution fails, return original content
            return content

    def get_available_agents(self) -> list[str]:
        """
        List all agents with available core prompts.

        Returns:
            List of agent names from architecture prompts directory
        """
        if not self.architecture_prompts_dir.exists():
            return []
        return sorted(
            f.stem
            for f in self.architecture_prompts_dir.glob("*.txt")
            if not f.name.startswith("_")
        )

    def get_business_agents(self) -> list[str]:
        """
        List all agents with available business prompts in current template.

        Returns:
            List of agent names from business template, or empty list if no template
        """
        if not self.business_template:
            return []

        from claude_agent_framework.business_templates import list_template_agents

        return list_template_agents(self.business_template)


def create_composer(
    architecture_prompts_dir: Path,
    business_template: str | None = None,
    custom_prompts_dir: Path | str | None = None,
    prompt_overrides: dict[str, str] | None = None,
    template_vars: dict[str, Any] | None = None,
) -> PromptComposer:
    """
    Create a PromptComposer with the given configuration.

    Factory function for convenient composer creation.

    Args:
        architecture_prompts_dir: Directory containing architecture core prompts
        business_template: Name of business template to use (optional)
        custom_prompts_dir: Application-level custom prompts directory (optional)
        prompt_overrides: Dict of agent_name -> override prompt content
        template_vars: Dict of template variables for substitution

    Returns:
        Configured PromptComposer instance
    """
    return PromptComposer(
        architecture_prompts_dir=architecture_prompts_dir,
        business_template=business_template,
        custom_prompts_dir=Path(custom_prompts_dir) if custom_prompts_dir else None,
        prompt_overrides=prompt_overrides or {},
        template_vars=template_vars or {},
    )


__all__ = [
    "PromptComposer",
    "PromptCompositionError",
    "create_composer",
]
