"""
Pytest configuration and shared fixtures for claude-agent-framework tests.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def temp_files_dir(tmp_path):
    """Provide a temporary files directory for tests."""
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    return files_dir


@pytest.fixture
def temp_logs_dir(tmp_path):
    """Provide a temporary logs directory for tests."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    return logs_dir


@pytest.fixture
def mock_api_key():
    """Mock ANTHROPIC_API_KEY environment variable."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-api-key"}):
        yield "test-api-key"


@pytest.fixture
def prompts_dir():
    """Get path to test prompts directory."""
    return Path(__file__).parent / "fixtures" / "prompts"
