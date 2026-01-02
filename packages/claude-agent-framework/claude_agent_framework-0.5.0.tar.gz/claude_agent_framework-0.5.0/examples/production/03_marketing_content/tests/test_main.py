"""Unit tests for marketing content optimization."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestBuildCriticActorPrompt:
    """Test critic-actor prompt building."""

    def test_basic_prompt_structure(self):
        """Test basic prompt structure with content and brand guidelines."""
        from main import _build_critic_actor_prompt

        content_config = {
            "type": "blog_post",
            "brief": "Test brief",
            "keywords": ["AI", "automation"],
            "target_length": {"min_words": 500, "max_words": 800},
        }

        brand_config = {
            "voice": "professional",
            "tone": ["innovative", "trustworthy"],
            "values": ["Technical excellence"],
            "prohibited_phrases": ["revolutionary"],
        }

        evaluation_config = {
            "seo": {"weight": 25, "criteria": ["Keyword density"]},
            "engagement": {"weight": 30, "criteria": ["Hook quality"]},
            "brand_consistency": {"weight": 25, "criteria": ["Voice alignment"]},
            "accuracy": {"weight": 20, "criteria": ["Factual correctness"]},
        }

        iteration_config = {"max_iterations": 3, "quality_threshold": 85, "min_improvement": 5}

        prompt = _build_critic_actor_prompt(
            content_config, brand_config, evaluation_config, iteration_config
        )

        # Verify prompt structure
        assert "Content Type**: blog_post" in prompt
        assert "Test brief" in prompt
        assert "AI, automation" in prompt
        assert "500-800 words" in prompt
        assert "professional" in prompt
        assert "innovative, trustworthy" in prompt
        assert "Technical excellence" in prompt
        assert "revolutionary" in prompt
        assert "max_iterations" or "3 iterations" in prompt
        assert "85" in prompt


class TestResultParsing:
    """Test result parsing functions."""

    def test_parse_optimization_results(self):
        """Test parsing optimization results."""
        from main import _parse_optimization_results

        results = [
            """
=== ITERATION 1 ===
**Content**:
Draft content here

**Critic Evaluation**:
- SEO: 60/100 - Needs improvement
- Engagement: 70/100 - Good start
- Brand Consistency: 65/100 - Mostly aligned
- Accuracy: 80/100 - Good
- **Overall Score**: 68/100

**Improvement Recommendations**:
1. Add more keywords
2. Improve hook
""",
            """
=== ITERATION 2 ===
**Content**:
Improved content here

**Critic Evaluation**:
- SEO: 80/100 - Much better
- Engagement: 85/100 - Excellent
- Brand Consistency: 82/100 - Well aligned
- Accuracy: 88/100 - Very good
- **Overall Score**: 84/100

=== FINAL CONTENT ===
Improved content here
""",
        ]

        final_content, iterations, final_score = _parse_optimization_results(results)

        assert final_content == "Improved content here"
        assert len(iterations) == 2
        assert iterations[0]["iteration"] == 1
        assert iterations[0]["overall_score"] == 68.0
        assert iterations[0]["scores"]["seo"] == 60.0
        assert iterations[1]["overall_score"] == 84.0
        assert final_score == 84.0

    def test_generate_summary(self):
        """Test summary generation."""
        from main import _generate_summary

        iterations = [
            {"iteration": 1, "overall_score": 60.0},
            {"iteration": 2, "overall_score": 85.0},
        ]

        content_config = {"type": "blog_post"}

        summary = _generate_summary(iterations, 85.0, content_config)

        assert "blog_post" in summary
        assert "2 iteration" in summary
        assert "60" in summary
        assert "85" in summary
        assert "+25" in summary or "25.0" in summary


@pytest.mark.asyncio
class TestRunContentOptimization:
    """Test main content optimization function."""

    async def test_successful_optimization(self):
        """Test successful optimization with mocked session."""
        from main import run_content_optimization

        config = {
            "architecture": "critic_actor",
            "content": {
                "type": "blog_post",
                "brief": "Test brief",
                "keywords": ["test"],
                "target_length": {"min_words": 500, "max_words": 800},
            },
            "brand": {
                "voice": "professional",
                "tone": ["innovative"],
                "values": ["Excellence"],
                "prohibited_phrases": [],
            },
            "evaluation": {
                "seo": {"weight": 25, "criteria": ["Test"]},
                "engagement": {"weight": 30, "criteria": ["Test"]},
                "brand_consistency": {"weight": 25, "criteria": ["Test"]},
                "accuracy": {"weight": 20, "criteria": ["Test"]},
            },
            "iteration": {"max_iterations": 2, "quality_threshold": 85, "min_improvement": 5},
            "models": {"lead": "haiku", "actor": "haiku", "critic": "haiku"},
            "ab_testing": {"enabled": False},
        }

        # Mock session
        mock_session = MagicMock()

        async def mock_run(prompt):
            yield """
=== ITERATION 1 ===
**Content**:
Test content

**Critic Evaluation**:
- SEO: 70/100 - Good
- Engagement: 75/100 - Good
- Brand Consistency: 80/100 - Good
- Accuracy: 85/100 - Good
- **Overall Score**: 77/100

=== ITERATION 2 ===
**Content**:
Improved test content

**Critic Evaluation**:
- SEO: 85/100 - Excellent
- Engagement: 88/100 - Excellent
- Brand Consistency: 90/100 - Excellent
- Accuracy: 90/100 - Excellent
- **Overall Score**: 88/100

=== FINAL CONTENT ===
Improved test content
"""

        mock_session.run = mock_run
        mock_session.teardown = AsyncMock()

        with patch("main.init", return_value=mock_session):
            result = await run_content_optimization(config)

            # Verify result structure
            assert "title" in result
            assert "summary" in result
            assert "final_content" in result
            assert "final_score" in result
            assert "iterations" in result
            assert "metadata" in result

            assert result["final_score"] == 88.0
            assert len(result["iterations"]) == 2
            assert "Improved test content" in result["final_content"]

    async def test_optimization_with_ab_variants(self):
        """Test optimization with A/B variant generation."""
        from main import run_content_optimization

        config = {
            "architecture": "critic_actor",
            "content": {
                "type": "email",
                "brief": "Test brief",
                "keywords": [],
            },
            "brand": {
                "voice": "casual",
                "tone": ["friendly"],
                "values": ["Simplicity"],
                "prohibited_phrases": [],
            },
            "evaluation": {
                "seo": {"weight": 25, "criteria": ["Test"]},
                "engagement": {"weight": 30, "criteria": ["Test"]},
                "brand_consistency": {"weight": 25, "criteria": ["Test"]},
                "accuracy": {"weight": 20, "criteria": ["Test"]},
            },
            "iteration": {"max_iterations": 1, "quality_threshold": 85},
            "models": {"lead": "haiku", "actor": "haiku"},
            "ab_testing": {"enabled": True, "num_variants": 2},
        }

        # Mock session
        mock_session = MagicMock()

        async def mock_run(prompt):
            if "variant" in prompt.lower():
                yield "Variant content"
            else:
                yield """
=== ITERATION 1 ===
**Content**:
Base content

**Critic Evaluation**:
- SEO: 90/100
- Engagement: 90/100
- Brand Consistency: 90/100
- Accuracy: 90/100
- **Overall Score**: 90/100

=== FINAL CONTENT ===
Base content
"""

        mock_session.run = mock_run
        mock_session.teardown = AsyncMock()

        with patch("main.init", return_value=mock_session):
            result = await run_content_optimization(config)

            # Verify A/B variants
            assert "ab_variants" in result
            assert len(result["ab_variants"]) == 2
            assert result["ab_variants"][0]["variant"] == 1
            assert "angle" in result["ab_variants"][0]
            assert "content" in result["ab_variants"][0]

    async def test_default_model_config(self):
        """Test default model configuration."""
        from main import run_content_optimization

        config = {
            "architecture": "critic_actor",
            "content": {"type": "blog_post", "brief": "Test"},
            "brand": {"voice": "professional", "tone": [], "values": [], "prohibited_phrases": []},
            "evaluation": {
                "seo": {"weight": 25, "criteria": []},
                "engagement": {"weight": 30, "criteria": []},
                "brand_consistency": {"weight": 25, "criteria": []},
                "accuracy": {"weight": 20, "criteria": []},
            },
            "iteration": {"max_iterations": 1, "quality_threshold": 85},
            "ab_testing": {"enabled": False},
        }

        mock_session = MagicMock()

        async def mock_run(prompt):
            yield """
=== ITERATION 1 ===
**Content**: Test
**Critic Evaluation**:
- SEO: 80/100
- Engagement: 80/100
- Brand Consistency: 80/100
- Accuracy: 80/100
- **Overall Score**: 80/100
"""

        mock_session.run = mock_run
        mock_session.teardown = AsyncMock()

        with patch("main.init", return_value=mock_session) as mock_init:
            await run_content_optimization(config)

            # Verify default model used
            mock_init.assert_called()
            args, kwargs = mock_init.call_args
            assert args[0] == "critic_actor"
            assert kwargs["model"] == "sonnet"  # Default
