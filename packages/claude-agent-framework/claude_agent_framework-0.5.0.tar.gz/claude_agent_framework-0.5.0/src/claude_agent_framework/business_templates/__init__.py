"""
Business templates module for Claude Agent Framework.

Provides a library of pre-built business prompt templates that can be used
with any architecture. Templates are organized by business type and are
independent of specific architectures.

Directory Structure:
    business_templates/
    ├── __init__.py
    ├── competitive_intelligence/
    │   ├── _meta.yaml
    │   ├── researcher.txt
    │   ├── data_analyst.txt
    │   └── report_writer.txt
    ├── market_research/
    │   └── ...
    └── financial_analysis/
        └── ...

Usage:
    from claude_agent_framework.business_templates import (
        list_templates,
        get_template_path,
        load_template_prompt,
        get_template_metadata,
    )

    # List available templates
    templates = list_templates()

    # Load a specific agent prompt from a template
    prompt = load_template_prompt("competitive_intelligence", "researcher")
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Optional yaml import for metadata reading
try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# Directory containing all business templates
TEMPLATES_DIR = Path(__file__).parent


class TemplateNotFoundError(Exception):
    """Raised when a business template is not found."""

    pass


class TemplatePromptNotFoundError(Exception):
    """Raised when a prompt file is not found in a business template."""

    pass


def get_template_path(template_name: str) -> Path:
    """
    Get the directory path for a business template.

    Args:
        template_name: Name of the business template (e.g., "competitive_intelligence")

    Returns:
        Path to the template directory

    Raises:
        TemplateNotFoundError: If template does not exist
    """
    template_path = TEMPLATES_DIR / template_name
    if not template_path.is_dir():
        available = list_templates()
        raise TemplateNotFoundError(
            f"Business template '{template_name}' not found. "
            f"Available templates: {', '.join(available) if available else 'none'}"
        )
    return template_path


def list_templates() -> list[str]:
    """
    List all available business templates.

    Returns:
        List of template names (directory names that don't start with '_')
    """
    if not TEMPLATES_DIR.exists():
        return []
    return sorted(
        d.name
        for d in TEMPLATES_DIR.iterdir()
        if d.is_dir() and not d.name.startswith("_") and not d.name.startswith(".")
    )


def load_template_prompt(template_name: str, agent_name: str) -> str | None:
    """
    Load a specific agent's business prompt from a template.

    Args:
        template_name: Name of the business template
        agent_name: Name of the agent (e.g., "researcher", "data_analyst")

    Returns:
        Prompt content as string, or None if prompt file doesn't exist

    Raises:
        TemplateNotFoundError: If template does not exist
    """
    template_path = get_template_path(template_name)
    prompt_file = template_path / f"{agent_name}.txt"

    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8").strip()
    return None


def get_template_prompt_or_raise(template_name: str, agent_name: str) -> str:
    """
    Load a specific agent's business prompt from a template.

    Like load_template_prompt but raises an error if prompt is not found.

    Args:
        template_name: Name of the business template
        agent_name: Name of the agent

    Returns:
        Prompt content as string

    Raises:
        TemplateNotFoundError: If template does not exist
        TemplatePromptNotFoundError: If prompt file does not exist
    """
    prompt = load_template_prompt(template_name, agent_name)
    if prompt is None:
        template_path = get_template_path(template_name)
        raise TemplatePromptNotFoundError(
            f"Prompt file for agent '{agent_name}' not found in template '{template_name}'. "
            f"Expected file: {template_path / f'{agent_name}.txt'}"
        )
    return prompt


def get_template_metadata(template_name: str) -> dict[str, Any]:
    """
    Get metadata for a business template.

    Reads the _meta.yaml file if it exists.

    Args:
        template_name: Name of the business template

    Returns:
        Dictionary with template metadata, or empty dict if no metadata file
        or yaml package not installed
    """
    if not YAML_AVAILABLE:
        return {}

    template_path = get_template_path(template_name)
    meta_file = template_path / "_meta.yaml"

    if meta_file.exists():
        with open(meta_file, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def list_template_agents(template_name: str) -> list[str]:
    """
    List all agent prompts available in a template.

    Args:
        template_name: Name of the business template

    Returns:
        List of agent names (without .txt extension)
    """
    template_path = get_template_path(template_name)
    return sorted(
        f.stem
        for f in template_path.glob("*.txt")
        if not f.name.startswith("_")
    )


def template_exists(template_name: str) -> bool:
    """
    Check if a business template exists.

    Args:
        template_name: Name of the business template

    Returns:
        True if template exists, False otherwise
    """
    template_path = TEMPLATES_DIR / template_name
    return template_path.is_dir()


def get_template_default_query(
    template_name: str,
    template_vars: dict[str, Any] | None = None,
) -> str | None:
    """
    Get the default query for a business template with variable substitution.

    Args:
        template_name: Name of the business template
        template_vars: Dict of template variables for ${var} substitution

    Returns:
        Default query string with variables substituted, or None if not defined
    """
    metadata = get_template_metadata(template_name)
    default_query = metadata.get("default_query")

    if default_query and template_vars:
        # Apply variable substitution
        for key, value in template_vars.items():
            default_query = default_query.replace(f"${{{key}}}", str(value))

    return default_query


__all__ = [
    "TEMPLATES_DIR",
    "TemplateNotFoundError",
    "TemplatePromptNotFoundError",
    "get_template_path",
    "list_templates",
    "load_template_prompt",
    "get_template_prompt_or_raise",
    "get_template_metadata",
    "list_template_agents",
    "template_exists",
    "get_template_default_query",
]
