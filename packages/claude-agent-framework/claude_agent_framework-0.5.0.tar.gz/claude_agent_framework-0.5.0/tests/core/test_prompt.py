"""
Tests for PromptComposer.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from claude_agent_framework.config import FRAMEWORK_ROOT
from claude_agent_framework.core.prompt import PromptComposer


class TestPromptComposer:
    """Tests for PromptComposer class."""

    @pytest.fixture
    def research_prompts_dir(self) -> Path:
        """Get the research architecture prompts directory."""
        return FRAMEWORK_ROOT / "architectures" / "research" / "prompts"

    def test_initialization(self, research_prompts_dir: Path) -> None:
        """Test PromptComposer initialization."""
        composer = PromptComposer(architecture_prompts_dir=research_prompts_dir)
        assert composer.architecture_prompts_dir == research_prompts_dir
        assert composer.business_template is None
        assert composer.custom_prompts_dir is None
        assert composer.prompt_overrides == {}
        assert composer.template_vars == {}

    def test_initialization_with_all_params(self, research_prompts_dir: Path) -> None:
        """Test initialization with all parameters."""
        composer = PromptComposer(
            architecture_prompts_dir=research_prompts_dir,
            business_template="competitive_intelligence",
            custom_prompts_dir=Path("/custom"),
            prompt_overrides={"researcher": "custom prompt"},
            template_vars={"company_name": "Test Corp"},
        )
        assert composer.business_template == "competitive_intelligence"
        assert composer.custom_prompts_dir == Path("/custom")
        assert composer.prompt_overrides == {"researcher": "custom prompt"}
        assert composer.template_vars == {"company_name": "Test Corp"}


class TestPromptComposerCompose:
    """Tests for PromptComposer.compose() method."""

    @pytest.fixture
    def research_prompts_dir(self) -> Path:
        """Get the research architecture prompts directory."""
        return FRAMEWORK_ROOT / "architectures" / "research" / "prompts"

    def test_compose_core_only(self, research_prompts_dir: Path) -> None:
        """Test composing with only core prompt (no business template)."""
        composer = PromptComposer(architecture_prompts_dir=research_prompts_dir)
        prompt = composer.compose("worker")
        assert prompt is not None
        assert len(prompt) > 0
        # Should contain core prompt content (worker.txt)
        assert "Research Worker" in prompt or "web searches" in prompt.lower()

    def test_compose_with_business_template(self, research_prompts_dir: Path) -> None:
        """Test composing with business template."""
        composer = PromptComposer(
            architecture_prompts_dir=research_prompts_dir,
            business_template="competitive_intelligence",
        )
        # Note: business_template still uses old agent names (researcher)
        # This tests the backward compatibility of PromptComposer
        prompt = composer.compose("researcher")
        # Should contain business prompt content
        assert "Competitive Intelligence" in prompt or "competitor" in prompt.lower()

    def test_compose_with_template_vars(self, research_prompts_dir: Path) -> None:
        """Test template variable substitution."""
        composer = PromptComposer(
            architecture_prompts_dir=research_prompts_dir,
            business_template="competitive_intelligence",
            template_vars={"company_name": "Tesla Inc", "industry": "Electric Vehicles"},
        )
        prompt = composer.compose("researcher")
        # Template vars should be substituted
        assert "Tesla Inc" in prompt
        assert "Electric Vehicles" in prompt

    def test_compose_with_prompt_override(self, research_prompts_dir: Path) -> None:
        """Test prompt override takes priority."""
        custom_prompt = "This is my custom researcher prompt"
        composer = PromptComposer(
            architecture_prompts_dir=research_prompts_dir,
            business_template="competitive_intelligence",
            prompt_overrides={"researcher": custom_prompt},
        )
        # When override is provided, it should be used as business prompt
        prompt = composer.compose("researcher")
        # Business override should be present (no core prompt for "researcher" in new structure)
        assert custom_prompt in prompt

    def test_compose_nonexistent_agent(self, research_prompts_dir: Path) -> None:
        """Test composing for nonexistent agent returns empty."""
        composer = PromptComposer(architecture_prompts_dir=research_prompts_dir)
        prompt = composer.compose("nonexistent_agent")
        assert prompt == ""


class TestPromptComposerLoadCore:
    """Tests for PromptComposer._load_core() method."""

    @pytest.fixture
    def research_prompts_dir(self) -> Path:
        """Get the research architecture prompts directory."""
        return FRAMEWORK_ROOT / "architectures" / "research" / "prompts"

    def test_load_core_existing(self, research_prompts_dir: Path) -> None:
        """Test loading existing core prompt."""
        composer = PromptComposer(architecture_prompts_dir=research_prompts_dir)
        # Use "worker" which exists in the new structure
        prompt = composer._load_core("worker")
        assert prompt is not None
        assert len(prompt) > 0

    def test_load_core_nonexistent(self, research_prompts_dir: Path) -> None:
        """Test loading nonexistent core prompt returns empty."""
        composer = PromptComposer(architecture_prompts_dir=research_prompts_dir)
        prompt = composer._load_core("nonexistent")
        assert prompt == ""


class TestPromptComposerLoadBusiness:
    """Tests for PromptComposer._load_business() method."""

    @pytest.fixture
    def research_prompts_dir(self) -> Path:
        """Get the research architecture prompts directory."""
        return FRAMEWORK_ROOT / "architectures" / "research" / "prompts"

    def test_load_business_from_template(self, research_prompts_dir: Path) -> None:
        """Test loading business prompt from template."""
        composer = PromptComposer(
            architecture_prompts_dir=research_prompts_dir,
            business_template="competitive_intelligence",
        )
        prompt = composer._load_business("researcher")
        assert prompt is not None
        assert "Competitive Intelligence" in prompt or "competitor" in prompt.lower()

    def test_load_business_from_override(self, research_prompts_dir: Path) -> None:
        """Test prompt override takes priority over template."""
        custom_prompt = "Custom business prompt"
        composer = PromptComposer(
            architecture_prompts_dir=research_prompts_dir,
            business_template="competitive_intelligence",
            prompt_overrides={"researcher": custom_prompt},
        )
        prompt = composer._load_business("researcher")
        assert prompt == custom_prompt

    def test_load_business_no_template(self, research_prompts_dir: Path) -> None:
        """Test loading business prompt when no template specified."""
        composer = PromptComposer(architecture_prompts_dir=research_prompts_dir)
        prompt = composer._load_business("researcher")
        assert prompt == ""


class TestPromptComposerTemplateVars:
    """Tests for template variable substitution."""

    @pytest.fixture
    def research_prompts_dir(self) -> Path:
        """Get the research architecture prompts directory."""
        return FRAMEWORK_ROOT / "architectures" / "research" / "prompts"

    def test_apply_template_vars(self, research_prompts_dir: Path) -> None:
        """Test _apply_template_vars method."""
        composer = PromptComposer(
            architecture_prompts_dir=research_prompts_dir,
            template_vars={"name": "Test", "value": "123"},
        )
        result = composer._apply_template_vars("Hello ${name}, value is ${value}")
        assert result == "Hello Test, value is 123"

    def test_apply_template_vars_unmatched(self, research_prompts_dir: Path) -> None:
        """Test unmatched template vars remain unchanged."""
        composer = PromptComposer(
            architecture_prompts_dir=research_prompts_dir,
            template_vars={"name": "Test"},
        )
        result = composer._apply_template_vars("Hello ${name}, value is ${unknown}")
        assert result == "Hello Test, value is ${unknown}"

    def test_apply_template_vars_empty(self, research_prompts_dir: Path) -> None:
        """Test empty template vars leaves content unchanged."""
        composer = PromptComposer(architecture_prompts_dir=research_prompts_dir)
        content = "Hello ${name}"
        result = composer._apply_template_vars(content)
        assert result == content
