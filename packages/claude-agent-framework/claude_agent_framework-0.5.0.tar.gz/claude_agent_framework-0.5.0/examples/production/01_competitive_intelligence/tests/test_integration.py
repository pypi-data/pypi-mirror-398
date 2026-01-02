"""Integration tests for competitive intelligence example."""

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
            "architecture": "research",
            "competitors": [
                {
                    "name": "TestCompany",
                    "website": "https://test.com",
                    "focus_areas": ["Testing"],
                }
            ],
            "analysis_dimensions": ["Features"],
            "output": {"directory": str(tmp_path / "outputs"), "format": "json"},
            "models": {"lead": "haiku"},
        }

        # Mock session
        mock_session = MagicMock()
        mock_session.session_dir = tmp_path / "session"

        async def mock_run(prompt):
            yield "Test analysis result"

        mock_session.run = mock_run
        mock_session.teardown = AsyncMock()

        with patch("main.init", return_value=mock_session):
            # Run analysis
            result = await main.run_competitive_intelligence(config)

            # Verify result structure
            assert "title" in result
            assert "summary" in result
            assert "competitors" in result
            assert "dimensions" in result
            assert "content" in result
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
            "architecture": "research",
            "competitors": [],
            "analysis_dimensions": [],
            "output": {},
        }

        # Should not raise
        validate_config(
            valid_config, ["architecture", "competitors", "analysis_dimensions", "output"]
        )

        # Invalid config - missing field
        invalid_config = {"architecture": "research"}

        with pytest.raises(ValueError) as exc_info:
            validate_config(
                invalid_config,
                ["architecture", "competitors", "analysis_dimensions", "output"],
            )

        assert "Missing required configuration fields" in str(exc_info.value)

    def test_result_saver_json(self, tmp_path):
        """Test ResultSaver with JSON format."""
        from common import ResultSaver

        saver = ResultSaver(tmp_path)

        result = {
            "title": "Test Report",
            "summary": "Test summary",
            "content": "Test content",
        }

        output_path = saver.save(result, format="json", filename="test_report")

        assert output_path.exists()
        assert output_path.name == "test_report.json"

        # Verify content
        import json

        with output_path.open("r") as f:
            loaded = json.load(f)
            assert loaded["title"] == "Test Report"

    def test_result_saver_markdown(self, tmp_path):
        """Test ResultSaver with Markdown format."""
        from common import ResultSaver

        saver = ResultSaver(tmp_path)

        result = {
            "title": "Test Report",
            "summary": "Test summary",
            "content": "Test content",
        }

        output_path = saver.save(result, format="markdown", filename="test_report")

        assert output_path.exists()
        assert output_path.name == "test_report.md"

        # Verify content
        content = output_path.read_text()
        assert "# Test Report" in content
        assert "Test summary" in content

    def test_config_loading(self):
        """Test YAML config loading."""
        from common import load_yaml_config

        # Test with actual config file
        config_path = Path(__file__).parent.parent / "config.yaml"

        if config_path.exists():
            config = load_yaml_config(config_path)

            assert "architecture" in config
            assert "competitors" in config
            assert "analysis_dimensions" in config
            assert config["architecture"] == "research"

    def test_config_loading_missing_file(self):
        """Test config loading with missing file."""
        from common import load_yaml_config

        with pytest.raises(FileNotFoundError):
            load_yaml_config("/nonexistent/config.yaml")
