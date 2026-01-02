"""
Configuration Management Module

Provides framework configuration, environment variable loading, and validation.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Try to load dotenv
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


# Framework root directory (config/ is inside claude_agent_framework/)
FRAMEWORK_ROOT = Path(__file__).parent.parent
PROMPTS_DIR = FRAMEWORK_ROOT / "prompts"
FILES_DIR = FRAMEWORK_ROOT / "files"
LOGS_DIR = FRAMEWORK_ROOT / "logs"


@dataclass
class AgentConfig:
    """
    Single agent configuration.

    Attributes:
        name: Agent name (used as subagent_type)
        description: Agent description (when to use)
        tools: List of allowed tools
        prompt_file: Prompt filename (relative to prompts directory)
        model: Model to use
    """

    name: str
    description: str
    tools: list[str]
    prompt_file: str
    model: str = "haiku"

    def load_prompt(self) -> str:
        """Load prompt content."""
        prompt_path = PROMPTS_DIR / self.prompt_file
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        return prompt_path.read_text(encoding="utf-8").strip()


@dataclass
class FrameworkConfig:
    """
    Framework global configuration.

    Attributes:
        lead_agent_prompt_file: Lead agent prompt file
        lead_agent_tools: Lead agent allowed tools
        lead_agent_model: Lead agent model
        subagents: List of subagent configurations
        permission_mode: Permission mode
        setting_sources: Configuration sources
        enable_logging: Whether to enable logging
        logs_dir: Logs directory
        files_dir: Files directory
    """

    # Lead agent configuration
    lead_agent_prompt_file: str = "lead_agent.txt"
    lead_agent_tools: list[str] = field(default_factory=lambda: ["Task"])
    lead_agent_model: str = "haiku"

    # Subagent configuration
    subagents: list[AgentConfig] = field(default_factory=list)

    # SDK configuration
    permission_mode: str = "bypassPermissions"
    setting_sources: list[str] = field(default_factory=lambda: ["project"])

    # Logging configuration
    enable_logging: bool = True
    logs_dir: Path = field(default_factory=lambda: LOGS_DIR)
    files_dir: Path = field(default_factory=lambda: FILES_DIR)

    def __post_init__(self) -> None:
        """Post-initialization processing."""
        # Convert path types
        if isinstance(self.logs_dir, str):
            self.logs_dir = Path(self.logs_dir)
        if isinstance(self.files_dir, str):
            self.files_dir = Path(self.files_dir)

        # Use default configuration if no subagents configured
        if not self.subagents:
            self.subagents = self._default_subagents()

    def _default_subagents(self) -> list[AgentConfig]:
        """Default subagent configuration."""
        return [
            AgentConfig(
                name="researcher",
                description="Gather research data via web search, save to files/research_notes/",
                tools=["WebSearch", "Write"],
                prompt_file="researcher.txt",
                model="haiku",
            ),
            AgentConfig(
                name="data-analyst",
                description="Analyze research data and generate visualizations, save to files/charts/",
                tools=["Glob", "Read", "Bash", "Write"],
                prompt_file="data_analyst.txt",
                model="haiku",
            ),
            AgentConfig(
                name="report-writer",
                description="Generate final PDF reports, save to files/reports/",
                tools=["Skill", "Write", "Glob", "Read", "Bash"],
                prompt_file="report_writer.txt",
                model="haiku",
            ),
        ]

    def load_lead_agent_prompt(self) -> str:
        """Load lead agent prompt."""
        prompt_path = PROMPTS_DIR / self.lead_agent_prompt_file
        if not prompt_path.exists():
            raise FileNotFoundError(f"Lead agent prompt not found: {prompt_path}")
        return prompt_path.read_text(encoding="utf-8").strip()

    def to_agents_dict(self) -> dict[str, Any]:
        """
        Convert to claude_agent_sdk.AgentDefinition dictionary.

        Returns:
            Dictionary that can be passed directly to ClaudeAgentOptions agents parameter
        """
        # Delayed import to avoid circular dependency
        from claude_agent_sdk import AgentDefinition

        return {
            agent.name: AgentDefinition(
                description=agent.description,
                tools=agent.tools,
                prompt=agent.load_prompt(),
                model=agent.model,
            )
            for agent in self.subagents
        }

    def ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.files_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        for subdir in ["research_notes", "data", "charts", "reports"]:
            (self.files_dir / subdir).mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls) -> FrameworkConfig:
        """Create configuration from environment variables."""
        return cls(
            lead_agent_model=os.getenv("LEAD_MODEL", "haiku"),
            permission_mode=os.getenv("PERMISSION_MODE", "bypassPermissions"),
            enable_logging=os.getenv("ENABLE_LOGGING", "true").lower() == "true",
        )


def validate_api_key() -> bool:
    """
    Validate if API Key is configured.

    Returns:
        True if API Key is configured
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return False
    return True


def get_api_key() -> str | None:
    """Get API Key."""
    return os.getenv("ANTHROPIC_API_KEY")


# Default configuration instance
default_config = FrameworkConfig()
