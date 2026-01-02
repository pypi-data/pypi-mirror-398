"""
Tests for business templates module.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from claude_agent_framework.business_templates import (
    TemplateNotFoundError,
    TemplatePromptNotFoundError,
    get_template_path,
    get_template_prompt_or_raise,
    list_template_agents,
    list_templates,
    load_template_prompt,
    template_exists,
)


class TestListTemplates:
    """Tests for list_templates function."""

    def test_returns_list(self) -> None:
        """Test that list_templates returns a list."""
        templates = list_templates()
        assert isinstance(templates, list)

    def test_templates_exist(self) -> None:
        """Test that expected templates are listed."""
        templates = list_templates()
        # At minimum, competitive_intelligence should exist
        assert "competitive_intelligence" in templates

    def test_templates_sorted(self) -> None:
        """Test that templates are sorted alphabetically."""
        templates = list_templates()
        assert templates == sorted(templates)

    def test_excludes_private_dirs(self) -> None:
        """Test that directories starting with _ are excluded."""
        templates = list_templates()
        for template in templates:
            assert not template.startswith("_")


class TestTemplateExists:
    """Tests for template_exists function."""

    def test_existing_template(self) -> None:
        """Test that existing template returns True."""
        assert template_exists("competitive_intelligence") is True

    def test_nonexistent_template(self) -> None:
        """Test that nonexistent template returns False."""
        assert template_exists("nonexistent_template") is False


class TestGetTemplatePath:
    """Tests for get_template_path function."""

    def test_valid_template(self) -> None:
        """Test getting path for valid template."""
        path = get_template_path("competitive_intelligence")
        assert isinstance(path, Path)
        assert path.is_dir()

    def test_invalid_template_raises_error(self) -> None:
        """Test that invalid template raises TemplateNotFoundError."""
        with pytest.raises(TemplateNotFoundError) as exc_info:
            get_template_path("nonexistent_template")
        assert "nonexistent_template" in str(exc_info.value)


class TestLoadTemplatePrompt:
    """Tests for load_template_prompt function."""

    def test_load_existing_prompt(self) -> None:
        """Test loading existing prompt."""
        prompt = load_template_prompt("competitive_intelligence", "researcher")
        assert prompt is not None
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_load_nonexistent_prompt(self) -> None:
        """Test loading nonexistent prompt returns None."""
        prompt = load_template_prompt("competitive_intelligence", "nonexistent_agent")
        assert prompt is None

    def test_load_from_invalid_template(self) -> None:
        """Test loading from invalid template raises error."""
        with pytest.raises(TemplateNotFoundError):
            load_template_prompt("nonexistent_template", "researcher")


class TestGetTemplatePromptOrRaise:
    """Tests for get_template_prompt_or_raise function."""

    def test_get_existing_prompt(self) -> None:
        """Test getting existing prompt."""
        prompt = get_template_prompt_or_raise("competitive_intelligence", "researcher")
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_get_nonexistent_prompt_raises(self) -> None:
        """Test that nonexistent prompt raises TemplatePromptNotFoundError."""
        with pytest.raises(TemplatePromptNotFoundError):
            get_template_prompt_or_raise("competitive_intelligence", "nonexistent_agent")


class TestListTemplateAgents:
    """Tests for list_template_agents function."""

    def test_list_agents(self) -> None:
        """Test listing agents in a template."""
        agents = list_template_agents("competitive_intelligence")
        assert isinstance(agents, list)
        assert "researcher" in agents
        assert "data_analyst" in agents

    def test_list_agents_sorted(self) -> None:
        """Test that agents are sorted alphabetically."""
        agents = list_template_agents("competitive_intelligence")
        assert agents == sorted(agents)

    def test_list_agents_invalid_template(self) -> None:
        """Test listing agents from invalid template raises error."""
        with pytest.raises(TemplateNotFoundError):
            list_template_agents("nonexistent_template")


class TestTemplateContent:
    """Tests for template content validity."""

    def test_competitive_intelligence_has_expected_agents(self) -> None:
        """Test that competitive_intelligence has expected agents."""
        agents = list_template_agents("competitive_intelligence")
        expected = ["data_analyst", "lead_agent", "report_writer", "researcher"]
        assert sorted(agents) == sorted(expected)

    def test_prompts_contain_template_vars(self) -> None:
        """Test that prompts contain template variables."""
        prompt = load_template_prompt("competitive_intelligence", "researcher")
        assert prompt is not None
        # Check for template variable placeholders
        assert "${company_name}" in prompt or "${industry}" in prompt

    def test_all_templates_have_lead_agent(self) -> None:
        """Test that all templates have a lead_agent prompt."""
        templates = list_templates()
        for template in templates:
            agents = list_template_agents(template)
            assert "lead_agent" in agents, f"Template '{template}' missing lead_agent"
