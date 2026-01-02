"""Unit tests for PR code review main module."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import (
    _build_pipeline_prompt,
    _determine_overall_status,
    _extract_recommendations,
    _generate_summary,
    _parse_stage_results,
    run_pr_review,
)


class TestBuildPipelinePrompt:
    """Test pipeline prompt building."""

    def test_basic_prompt_structure(self):
        """Test basic prompt structure."""
        stages = [
            {"name": "architecture_review", "description": "Review architecture"},
            {"name": "code_quality", "description": "Check code quality"},
        ]
        pr_data = {
            "files_changed": 5,
            "lines_added": 100,
            "lines_deleted": 20,
            "diff": "mock diff",
        }
        analysis_config = {"max_complexity": 10}

        prompt = _build_pipeline_prompt(stages, pr_data, analysis_config)

        assert "architecture_review" in prompt
        assert "code_quality" in prompt
        assert "Files Changed: 5" in prompt
        assert "Lines Added: 100" in prompt
        assert "Max Complexity: 10" in prompt

    def test_multiple_stages(self):
        """Test prompt with multiple stages."""
        stages = [
            {"name": "stage1", "description": "First stage"},
            {"name": "stage2", "description": "Second stage"},
            {"name": "stage3", "description": "Third stage"},
        ]
        pr_data = {
            "files_changed": 1,
            "lines_added": 10,
            "lines_deleted": 5,
        }
        analysis_config = {}

        prompt = _build_pipeline_prompt(stages, pr_data, analysis_config)

        assert "stage1" in prompt
        assert "stage2" in prompt
        assert "stage3" in prompt
        assert "Execute the following stages sequentially" in prompt


class TestResultParsing:
    """Test result parsing functions."""

    def test_generate_summary(self):
        """Test summary generation."""
        stages = [
            {"name": "stage1", "description": "Stage 1"},
            {"name": "stage2", "description": "Stage 2"},
        ]
        results = [
            "Stage 1: ✅ PASS - All good",
            "Stage 2: ⚠️ WARNING - Minor issues",
        ]

        summary = _generate_summary(stages, results)

        assert "Completed 2 review stages" in summary
        assert "1 passed" in summary
        assert "1 warnings" in summary

    def test_parse_stage_results(self):
        """Test stage result parsing."""
        stages = [
            {"name": "stage1", "description": "First stage"},
            {"name": "stage2", "description": "Second stage"},
        ]
        results = ["Stage 1 result", "Stage 2 result"]

        parsed = _parse_stage_results(stages, results)

        assert len(parsed) == 2
        assert parsed[0]["name"] == "stage1"
        assert parsed[1]["name"] == "stage2"
        assert all(s["status"] == "completed" for s in parsed)

    def test_determine_overall_status_approved(self):
        """Test overall status determination - approved."""
        results = [
            "Stage 1: ✅ PASS",
            "Stage 2: ✅ PASS",
        ]

        status = _determine_overall_status(results)

        assert status == "APPROVED"

    def test_determine_overall_status_warnings(self):
        """Test overall status determination - warnings."""
        results = [
            "Stage 1: ✅ PASS",
            "Stage 2: ⚠️ WARNING",
        ]

        status = _determine_overall_status(results)

        assert status == "APPROVED_WITH_COMMENTS"

    def test_determine_overall_status_failed(self):
        """Test overall status determination - failed."""
        results = [
            "Stage 1: ✅ PASS",
            "Stage 2: ❌ FAIL",
        ]

        status = _determine_overall_status(results)

        assert status == "CHANGES_REQUESTED"

    def test_extract_recommendations(self):
        """Test recommendation extraction."""
        results = ["Some results with recommendations"]

        recommendations = _extract_recommendations(results)

        assert len(recommendations) > 0
        assert all(isinstance(r, str) for r in recommendations)


@pytest.mark.asyncio
class TestRunPRReview:
    """Test main PR review execution."""

    async def test_successful_review(self):
        """Test successful review execution."""
        config = {
            "stages": [
                {
                    "name": "code_quality",
                    "description": "Check quality",
                    "required": True,
                }
            ],
            "pr_source": {
                "local_path": ".",
                "base_branch": "main",
            },
            "analysis": {"max_complexity": 10},
            "models": {"lead": "haiku"},
        }

        # Mock session
        mock_session = MagicMock()
        mock_session.session_dir = Path("/tmp/test_session")

        async def mock_run(prompt):
            yield "Stage 1: ✅ PASS"

        mock_session.run = mock_run
        mock_session.teardown = AsyncMock()

        with patch("main.init", return_value=mock_session):
            with patch("main._get_pr_changes") as mock_get_pr:
                mock_get_pr.return_value = {
                    "files_changed": 5,
                    "lines_added": 100,
                    "lines_deleted": 20,
                    "diff": "mock diff",
                }

                result = await run_pr_review(config)

                assert result["title"] == "Pull Request Code Review Report"
                assert "summary" in result
                assert "pr_info" in result
                assert "stages" in result
                assert "overall_status" in result
                assert result["metadata"]["total_stages"] == 1
                assert result["metadata"]["files_changed"] == 5

    async def test_review_with_error(self):
        """Test review with error handling."""
        config = {
            "stages": [{"name": "test", "description": "Test"}],
            "pr_source": {"local_path": "."},
        }

        with patch("main.init", side_effect=Exception("API Error")):
            from common import ExecutionError

            with pytest.raises(ExecutionError) as exc_info:
                await run_pr_review(config)

            assert "PR review failed" in str(exc_info.value)

    async def test_default_model_config(self):
        """Test default model configuration."""
        config = {
            "stages": [{"name": "test", "description": "Test"}],
            "pr_source": {"local_path": "."},
            # No models config - should use defaults
        }

        mock_session = MagicMock()
        mock_session.session_dir = None

        async def mock_run(prompt):
            yield "Result"

        mock_session.run = mock_run
        mock_session.teardown = AsyncMock()

        with patch("main.init", return_value=mock_session) as mock_init:
            with patch("main._get_pr_changes") as mock_get_pr:
                mock_get_pr.return_value = {
                    "files_changed": 0,
                    "lines_added": 0,
                    "lines_deleted": 0,
                    "diff": "",
                }

                await run_pr_review(config)

                # Verify init was called with default model
                assert mock_init.called
                call_kwargs = mock_init.call_args[1]
                assert call_kwargs["model"] == "sonnet"  # default lead model
