"""Integration tests for marketing content optimization."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.mark.asyncio
class TestIntegration:
    """Integration tests."""

    async def test_end_to_end_with_mock(self, tmp_path):
        """Test end-to-end flow with mocked session."""
        import main
        from common import ResultSaver

        # Create test config
        config = {
            "architecture": "critic_actor",
            "content": {
                "type": "ad_copy",
                "brief": "Create ad for new product launch",
                "keywords": ["innovation", "technology"],
                "target_length": {"min_words": 50, "max_words": 100},
            },
            "brand": {
                "voice": "energetic",
                "tone": ["exciting", "forward-thinking"],
                "values": ["Innovation"],
                "prohibited_phrases": ["cheap"],
            },
            "evaluation": {
                "seo": {"weight": 20, "criteria": ["Keywords"]},
                "engagement": {"weight": 40, "criteria": ["Hook"]},
                "brand_consistency": {"weight": 20, "criteria": ["Voice"]},
                "accuracy": {"weight": 20, "criteria": ["Claims"]},
            },
            "iteration": {"max_iterations": 2, "quality_threshold": 80, "min_improvement": 5},
            "ab_testing": {"enabled": False},
            "models": {"lead": "haiku"},
            "output": {"directory": str(tmp_path / "outputs"), "format": "json"},
        }

        # Mock session
        mock_session = MagicMock()
        mock_session.session_dir = tmp_path / "session"

        async def mock_run(prompt):
            yield """
=== ITERATION 1 ===
**Content**:
Discover the future with our innovative tech solution!

**Critic Evaluation**:
- SEO: 75/100 - Good keyword usage
- Engagement: 80/100 - Strong hook
- Brand Consistency: 85/100 - Energetic voice
- Accuracy: 90/100 - Clear claims
- **Overall Score**: 82/100

=== FINAL CONTENT ===
Discover the future with our innovative tech solution!
"""

        mock_session.run = mock_run
        mock_session.teardown = AsyncMock()

        with patch("main.init", return_value=mock_session):
            # Run optimization
            result = await main.run_content_optimization(config)

            # Verify result structure
            assert "title" in result
            assert "summary" in result
            assert "content_type" in result
            assert "final_content" in result
            assert "final_score" in result
            assert "iterations" in result
            assert "ab_variants" in result
            assert "metadata" in result

            assert result["content_type"] == "ad_copy"
            assert result["final_score"] == 82.0
            assert len(result["iterations"]) >= 1

            # Save result
            saver = ResultSaver(config["output"]["directory"])
            output_path = saver.save(result, format="json")

            # Verify output file exists
            assert output_path.exists()
            assert output_path.suffix == ".json"

    async def test_config_validation(self):
        """Test configuration validation."""
        from common import validate_config

        # Valid config
        valid_config = {
            "architecture": "critic_actor",
            "content": {},
            "brand": {},
            "evaluation": {},
            "iteration": {},
            "output": {},
        }

        # Should not raise
        validate_config(
            valid_config, ["architecture", "content", "brand", "evaluation", "iteration", "output"]
        )

        # Invalid config - missing fields
        invalid_config = {"architecture": "critic_actor", "content": {}}

        with pytest.raises(ValueError) as exc_info:
            validate_config(
                invalid_config,
                ["architecture", "content", "brand", "evaluation", "iteration", "output"],
            )

        assert "Missing required configuration fields" in str(exc_info.value)

    def test_config_loading(self):
        """Test YAML config loading."""
        from common import load_yaml_config

        # Test with actual config file
        config_path = Path(__file__).parent.parent / "config.yaml"

        if config_path.exists():
            config = load_yaml_config(config_path)

            assert "architecture" in config
            assert "content" in config
            assert "brand" in config
            assert "evaluation" in config
            assert config["architecture"] == "critic_actor"
            assert "type" in config["content"]
            assert "brief" in config["content"]

    async def test_iteration_parsing(self):
        """Test iteration result parsing."""
        from main import _parse_optimization_results

        results = [
            """
=== ITERATION 1 ===
**Content**:
First draft content

**Critic Evaluation**:
- SEO: 65/100
- Engagement: 70/100
- Brand Consistency: 75/100
- Accuracy: 80/100
- **Overall Score**: 72/100

=== ITERATION 2 ===
**Content**:
Second draft content

**Critic Evaluation**:
- SEO: 80/100
- Engagement: 85/100
- Brand Consistency: 82/100
- Accuracy: 88/100
- **Overall Score**: 84/100

=== FINAL CONTENT ===
Second draft content
"""
        ]

        final_content, iterations, final_score = _parse_optimization_results(results)

        assert final_content == "Second draft content"
        assert len(iterations) == 2
        assert iterations[0]["overall_score"] == 72.0
        assert iterations[1]["overall_score"] == 84.0
        assert final_score == 84.0

    async def test_ab_variant_generation(self):
        """Test A/B variant generation."""
        from main import _generate_ab_variants

        base_content = "Original marketing content here"
        content_config = {"type": "blog_post"}
        brand_config = {"voice": "professional", "tone": ["innovative"]}
        models = {"actor": "haiku"}

        # Mock session for variants
        mock_session = MagicMock()

        async def mock_run(prompt):
            yield "Variant content based on " + ("features" if "Feature" in prompt else "benefits")

        mock_session.run = mock_run
        mock_session.teardown = AsyncMock()

        with patch("main.init", return_value=mock_session):
            variants = await _generate_ab_variants(
                base_content, content_config, brand_config, num_variants=2, models=models
            )

            assert len(variants) == 2
            assert variants[0]["variant"] == 1
            assert variants[1]["variant"] == 2
            assert "angle" in variants[0]
            assert "content" in variants[0]

    def test_evaluation_criteria_configuration(self):
        """Test evaluation criteria configuration."""
        from common import load_yaml_config

        config_path = Path(__file__).parent.parent / "config.yaml"

        if config_path.exists():
            config = load_yaml_config(config_path)

            evaluation = config["evaluation"]

            # Verify all dimensions present
            assert "seo" in evaluation
            assert "engagement" in evaluation
            assert "brand_consistency" in evaluation
            assert "accuracy" in evaluation

            # Verify structure
            for dimension in ["seo", "engagement", "brand_consistency", "accuracy"]:
                assert "weight" in evaluation[dimension]
                assert "criteria" in evaluation[dimension]
                assert isinstance(evaluation[dimension]["weight"], int)
                assert isinstance(evaluation[dimension]["criteria"], list)

            # Verify weights sum to 100
            total_weight = sum(
                eval_dim["weight"]
                for eval_dim in evaluation.values()
                if isinstance(eval_dim, dict) and "weight" in eval_dim
            )
            assert total_weight == 100

    def test_result_saver_markdown(self, tmp_path):
        """Test ResultSaver with Markdown format for content optimization."""
        from common import ResultSaver

        saver = ResultSaver(tmp_path)

        result = {
            "title": "Content Optimization Report",
            "summary": "Optimized ad_copy through 2 iterations with final score 88.5/100",
            "final_content": "Optimized marketing content",
            "final_score": 88.5,
            "iterations": [
                {"iteration": 1, "overall_score": 75.0},
                {"iteration": 2, "overall_score": 88.5},
            ],
        }

        output_path = saver.save(result, format="markdown", filename="content_optimization")

        assert output_path.exists()
        assert output_path.name == "content_optimization.md"

        # Verify content (ResultSaver writes title and summary in markdown)
        content = output_path.read_text()
        assert "# Content Optimization Report" in content
        assert "Optimized ad_copy through 2 iterations" in content
        assert "88.5" in content  # Now in the summary

    async def test_prompt_building(self):
        """Test critic-actor prompt building."""
        from main import _build_critic_actor_prompt

        content_config = {
            "type": "landing_page",
            "brief": "Create landing page for SaaS product",
            "keywords": ["cloud", "automation", "productivity"],
            "target_length": {"min_words": 300, "max_words": 500},
        }

        brand_config = {
            "voice": "authoritative yet friendly",
            "tone": ["trustworthy", "innovative"],
            "values": ["Customer success", "Innovation"],
            "prohibited_phrases": ["cheap", "best in class"],
        }

        evaluation_config = {
            "seo": {"weight": 25, "criteria": ["Keyword optimization", "Meta tags"]},
            "engagement": {"weight": 30, "criteria": ["Hook", "CTA clarity"]},
            "brand_consistency": {"weight": 25, "criteria": ["Voice", "Tone"]},
            "accuracy": {"weight": 20, "criteria": ["Technical accuracy"]},
        }

        iteration_config = {"max_iterations": 3, "quality_threshold": 85, "min_improvement": 5}

        prompt = _build_critic_actor_prompt(
            content_config, brand_config, evaluation_config, iteration_config
        )

        # Verify all key elements are in prompt
        assert "landing_page" in prompt
        assert "SaaS product" in prompt
        assert "cloud, automation, productivity" in prompt
        assert "300-500 words" in prompt
        assert "authoritative yet friendly" in prompt
        assert "Customer success" in prompt
        assert "cheap" in prompt and "best in class" in prompt
        assert "3 iterations" in prompt or "max_iterations" in prompt
        assert "85" in prompt
        assert "SEO" in prompt
        assert "Engagement" in prompt
