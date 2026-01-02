"""Unit tests for competitive intelligence main module."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import _build_analysis_prompt, run_competitive_intelligence


class TestBuildAnalysisPrompt:
    """Test prompt building functionality."""

    def test_basic_prompt_structure(self):
        """Test basic prompt structure."""
        competitors = [
            {
                "name": "AWS",
                "website": "https://aws.amazon.com",
                "focus_areas": ["Compute", "Storage"],
            }
        ]
        dimensions = ["Product Features", "Pricing Model"]

        prompt = _build_analysis_prompt(competitors, dimensions)

        assert "AWS" in prompt
        assert "https://aws.amazon.com" in prompt
        assert "Product Features" in prompt
        assert "Pricing Model" in prompt
        assert "WebSearch" in prompt

    def test_multiple_competitors(self):
        """Test prompt with multiple competitors."""
        competitors = [
            {"name": "AWS", "website": "https://aws.amazon.com"},
            {"name": "Azure", "website": "https://azure.microsoft.com"},
        ]
        dimensions = ["Features"]

        prompt = _build_analysis_prompt(competitors, dimensions)

        assert "AWS" in prompt
        assert "Azure" in prompt

    def test_competitor_without_focus_areas(self):
        """Test competitor without focus areas."""
        competitors = [{"name": "AWS", "website": "https://aws.amazon.com"}]
        dimensions = ["Features"]

        prompt = _build_analysis_prompt(competitors, dimensions)

        assert "General analysis" in prompt


@pytest.mark.asyncio
class TestRunCompetitiveIntelligence:
    """Test main analysis execution."""

    async def test_successful_analysis(self):
        """Test successful analysis execution."""
        config = {
            "competitors": [
                {
                    "name": "AWS",
                    "website": "https://aws.amazon.com",
                    "focus_areas": ["Compute"],
                }
            ],
            "analysis_dimensions": ["Features", "Pricing"],
            "models": {"lead": "haiku", "agents": "haiku"},
        }

        # Mock session
        mock_session = MagicMock()
        mock_session.session_dir = Path("/tmp/test_session")

        async def mock_run(prompt):
            """Mock async generator."""
            yield "Analysis result 1"
            yield "Analysis result 2"

        mock_session.run = mock_run
        mock_session.teardown = AsyncMock()

        with patch("main.init", return_value=mock_session):
            result = await run_competitive_intelligence(config)

            assert result["title"] == "Competitive Intelligence Analysis Report"
            assert result["competitors"] == ["AWS"]
            assert result["dimensions"] == ["Features", "Pricing"]
            assert "Analysis result 1" in result["content"]
            assert "Analysis result 2" in result["content"]
            assert result["metadata"]["total_competitors"] == 1
            assert result["metadata"]["total_dimensions"] == 2

    async def test_analysis_with_error(self):
        """Test analysis with error handling."""
        config = {
            "competitors": [{"name": "AWS", "website": "https://aws.amazon.com"}],
            "analysis_dimensions": ["Features"],
        }

        with patch("main.init", side_effect=Exception("API Error")):
            from common import ExecutionError

            with pytest.raises(ExecutionError) as exc_info:
                await run_competitive_intelligence(config)

            assert "Analysis failed" in str(exc_info.value)

    async def test_default_model_config(self):
        """Test default model configuration."""
        config = {
            "competitors": [{"name": "AWS", "website": "https://aws.amazon.com"}],
            "analysis_dimensions": ["Features"],
            # No models config - should use defaults
        }

        mock_session = MagicMock()
        mock_session.session_dir = None

        async def mock_run(prompt):
            yield "Result"

        mock_session.run = mock_run
        mock_session.teardown = AsyncMock()

        with patch("main.init", return_value=mock_session) as mock_init:
            await run_competitive_intelligence(config)

            # Verify init was called with default model
            assert mock_init.called
            call_kwargs = mock_init.call_args[1]
            assert call_kwargs["model"] == "sonnet"  # default lead model
