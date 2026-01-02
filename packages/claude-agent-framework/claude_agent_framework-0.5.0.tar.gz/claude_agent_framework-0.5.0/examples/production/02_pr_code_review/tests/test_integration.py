"""Integration tests for PR code review example."""

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
            "architecture": "pipeline",
            "stages": [
                {
                    "name": "code_quality",
                    "description": "Check code quality",
                    "required": True,
                },
                {
                    "name": "security_scan",
                    "description": "Scan security",
                    "required": True,
                },
            ],
            "pr_source": {"local_path": ".", "base_branch": "main"},
            "analysis": {"max_complexity": 10},
            "output": {"directory": str(tmp_path / "outputs"), "format": "json"},
            "models": {"lead": "haiku"},
        }

        # Mock session
        mock_session = MagicMock()
        mock_session.session_dir = tmp_path / "session"

        async def mock_run(prompt):
            yield "Code Quality: ✅ PASS"
            yield "Security Scan: ✅ PASS"

        mock_session.run = mock_run
        mock_session.teardown = AsyncMock()

        with patch("main.init", return_value=mock_session):
            with patch("main._get_pr_changes") as mock_get_pr:
                mock_get_pr.return_value = {
                    "files_changed": 3,
                    "lines_added": 50,
                    "lines_deleted": 10,
                    "diff": "mock diff",
                }

                # Run review
                result = await main.run_pr_review(config)

                # Verify result structure
                assert "title" in result
                assert "summary" in result
                assert "pr_info" in result
                assert "stages" in result
                assert "overall_status" in result
                assert "recommendations" in result
                assert "metadata" in result

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
            "architecture": "pipeline",
            "stages": [],
            "pr_source": {},
            "output": {},
        }

        # Should not raise
        validate_config(valid_config, ["architecture", "stages", "pr_source", "output"])

        # Invalid config - missing field
        invalid_config = {"architecture": "pipeline"}

        with pytest.raises(ValueError) as exc_info:
            validate_config(invalid_config, ["architecture", "stages", "pr_source", "output"])

        assert "Missing required configuration fields" in str(exc_info.value)

    def test_config_loading(self):
        """Test YAML config loading."""
        from common import load_yaml_config

        # Test with actual config file
        config_path = Path(__file__).parent.parent / "config.yaml"

        if config_path.exists():
            config = load_yaml_config(config_path)

            assert "architecture" in config
            assert "stages" in config
            assert "pr_source" in config
            assert config["architecture"] == "pipeline"
            assert len(config["stages"]) > 0

    async def test_pr_data_extraction_local(self):
        """Test PR data extraction from local path."""
        from main import _get_pr_changes

        pr_source = {"local_path": ".", "base_branch": "main"}

        pr_data = await _get_pr_changes(pr_source)

        assert "local_path" in pr_data
        assert "files_changed" in pr_data
        assert "lines_added" in pr_data
        assert "lines_deleted" in pr_data
        assert isinstance(pr_data["files_changed"], int)

    async def test_pr_data_extraction_url(self):
        """Test PR data extraction from URL."""
        from main import _get_pr_changes

        pr_source = {"pr_url": "https://github.com/owner/repo/pull/123"}

        pr_data = await _get_pr_changes(pr_source)

        assert "pr_url" in pr_data
        assert pr_data["pr_url"] == "https://github.com/owner/repo/pull/123"

    async def test_pr_source_missing(self):
        """Test PR source validation."""
        from main import _get_pr_changes

        pr_source = {}  # Missing both pr_url and local_path

        with pytest.raises(ValueError) as exc_info:
            await _get_pr_changes(pr_source)

        assert "PR source must specify" in str(exc_info.value)

    def test_stage_configuration(self):
        """Test stage configuration."""
        from common import load_yaml_config

        config_path = Path(__file__).parent.parent / "config.yaml"

        if config_path.exists():
            config = load_yaml_config(config_path)

            stages = config["stages"]
            assert len(stages) > 0

            # Verify required stage fields
            for stage in stages:
                assert "name" in stage
                assert "description" in stage
                assert "required" in stage
                assert "timeout" in stage

    def test_result_saver_markdown(self, tmp_path):
        """Test ResultSaver with Markdown format for PR review."""
        from common import ResultSaver

        saver = ResultSaver(tmp_path)

        result = {
            "title": "PR Review Report",
            "summary": "2 stages passed",
            "content": {
                "code_quality": "✅ PASS",
                "security_scan": "✅ PASS",
            },
        }

        output_path = saver.save(result, format="markdown", filename="pr_review")

        assert output_path.exists()
        assert output_path.name == "pr_review.md"

        # Verify content
        content = output_path.read_text()
        assert "# PR Review Report" in content
        assert "2 stages passed" in content
