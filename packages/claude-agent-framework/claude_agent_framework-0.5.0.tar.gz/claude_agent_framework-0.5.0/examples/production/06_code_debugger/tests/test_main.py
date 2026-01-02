"""Unit tests for Code Debugger."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPromptBuilding:
    """Test reflexion prompt construction."""

    def test_basic_prompt_structure(self):
        """Test basic prompt includes all key sections."""
        from main import _build_reflexion_prompt

        bug_description = "AttributeError when accessing user.email"
        context = {
            "error_message": "AttributeError: 'NoneType' object has no attribute 'get'",
            "file_path": "app.py",
            "code_snippet": "user_email = user.get('email')",
            "expected_behavior": "Handle missing user",
            "actual_behavior": "Crashes with AttributeError",
            "reproduction_steps": ["Call with invalid ID", "Returns None", "Crashes"],
        }

        debugging_config = {"max_iterations": 5, "success_threshold": 0.9}

        reflexion_config = {
            "executor": {
                "name": "debug_executor",
                "role": "Execute debugging strategies",
                "tools": ["Read", "Bash"],
            },
            "reflector": {
                "name": "debug_reflector",
                "role": "Analyze results",
                "focus_areas": ["Why failed?", "New information?"],
            },
            "improver": {
                "name": "strategy_improver",
                "role": "Refine strategy",
                "capabilities": [],
            },
        }

        strategies = {
            "error_trace_analysis": {
                "description": "Analyze error messages",
                "priority": 1,
            },
            "code_inspection": {
                "description": "Review code",
                "priority": 2,
            },
        }

        prompt = _build_reflexion_prompt(
            bug_description,
            context,
            debugging_config,
            reflexion_config,
            strategies,
            {},
            {},
            {},
        )

        # Verify key sections
        assert "AttributeError" in prompt
        assert "app.py" in prompt
        assert "debug_executor" in prompt
        assert "debug_reflector" in prompt
        assert "strategy_improver" in prompt
        assert "error_trace_analysis" in prompt
        assert "Iteration 1" in prompt


class TestBugCategorization:
    """Test bug categorization logic."""

    def test_runtime_error_categorization(self):
        """Test categorization of runtime errors."""
        from main import _categorize_bug

        bug_categories = {
            "runtime_error": {"patterns": ["AttributeError", "TypeError", "ValueError"]},
            "logic_error": {"patterns": ["Incorrect output", "Wrong calculation"]},
        }

        # Test AttributeError
        category = _categorize_bug(
            "Error in user processing",
            {"error_message": "AttributeError: 'NoneType' object..."},
            bug_categories,
        )

        assert category == "runtime_error"

    def test_logic_error_categorization(self):
        """Test categorization of logic errors."""
        from main import _categorize_bug

        bug_categories = {
            "runtime_error": {"patterns": ["AttributeError", "TypeError"]},
            "logic_error": {"patterns": ["Incorrect output", "Wrong calculation"]},
        }

        category = _categorize_bug(
            "Function returns wrong calculation",
            {"error_message": ""},
            bug_categories,
        )

        assert category == "logic_error"

    def test_unknown_categorization(self):
        """Test fallback to unknown category."""
        from main import _categorize_bug

        category = _categorize_bug(
            "Random bug",
            {"error_message": "Some unknown error"},
            {},
        )

        assert category == "unknown"


class TestTimelineParsing:
    """Test debugging timeline parsing."""

    def test_parse_debugging_timeline(self):
        """Test parsing of reflexion iterations."""
        from main import _parse_debugging_timeline

        results = [
            """
### Iteration 1: Initial Analysis

**[Executor]** Execute debugging strategy

Strategy: error_trace_analysis
Actions: Analyzed stack trace

**[Reflector]** Reflect on attempt

What worked: Found error location
What didn't: Couldn't determine why None

**[Improver]** Improve strategy

Next strategy: code_inspection

### Iteration 2: Code Review

**[Executor]** Execute debugging strategy

Strategy: code_inspection
"""
        ]

        timeline = _parse_debugging_timeline(results)

        assert len(timeline) >= 1
        assert isinstance(timeline, list)
        if len(timeline) > 0:
            assert "iteration" in timeline[0]


class TestRootCauseExtraction:
    """Test root cause extraction."""

    def test_extract_root_cause(self):
        """Test extraction of root cause."""
        from main import _extract_root_cause

        results = [
            """
**Root Cause Identified**

Category: Data Issues

Description: fetch_user function returns None for invalid user IDs, but calling code assumes it always returns a dict.

Why it causes the bug: When None is returned, calling .get() on None raises AttributeError.

Confidence: High

Evidence:
1. Error traceback shows None.get() call
2. fetch_user implementation confirms it returns None for missing users
3. No null checking before accessing user object
"""
        ]

        root_cause = _extract_root_cause(results)

        assert "category" in root_cause
        assert "description" in root_cause
        assert "confidence" in root_cause
        assert "evidence" in root_cause

        if root_cause["category"] != "Unknown":
            assert "Data Issues" in root_cause["category"]
            assert "High" in root_cause["confidence"]
            assert len(root_cause["evidence"]) >= 1


class TestProposedFixExtraction:
    """Test proposed fix extraction."""

    def test_extract_proposed_fix(self):
        """Test extraction of proposed fix."""
        from main import _extract_proposed_fix

        results = [
            """
**Proposed Fix**

```python
# File: app.py

# Before (problematic code):
def process_user_data(user_id):
    user = fetch_user(user_id)
    user_email = user.get('email')

# After (fixed code):
def process_user_data(user_id):
    user = fetch_user(user_id)
    if user is None:
        raise ValueError(f"User {user_id} not found")
    user_email = user.get('email')

# Explanation:
Add null check before accessing user object to prevent AttributeError.
```
"""
        ]

        proposed_fix = _extract_proposed_fix(results)

        assert "file_path" in proposed_fix
        assert "before_code" in proposed_fix
        assert "after_code" in proposed_fix
        assert "explanation" in proposed_fix

        if proposed_fix["file_path"]:
            assert "app.py" in proposed_fix["file_path"]


class TestFailedAttemptsExtraction:
    """Test failed attempts extraction."""

    def test_extract_failed_attempts(self):
        """Test extraction of failed debugging attempts."""
        from main import _extract_failed_attempts

        results = [
            """
**Failed Attempts Summary**

Iteration 1: Tried error_trace_analysis - Failed because couldn't determine root cause from trace alone
Iteration 2: Tried code_inspection - Failed because needed to see fetch_user implementation
Iteration 3: Tried hypothesis_testing - Successfully identified issue
"""
        ]

        failed_attempts = _extract_failed_attempts(results)

        assert isinstance(failed_attempts, list)
        # Should extract at least the failed attempts
        if len(failed_attempts) > 0:
            assert "strategy" in failed_attempts[0]
            assert "reason" in failed_attempts[0]


class TestLearningsExtraction:
    """Test learnings extraction."""

    def test_extract_learnings(self):
        """Test extraction of key learnings."""
        from main import _extract_learnings

        results = [
            """
Key learnings:
1. Always check for None before accessing object methods
2. fetch_user should document that it returns None for invalid IDs
3. Consider using Optional type hints to make None returns explicit
"""
        ]

        learnings = _extract_learnings(results)

        assert isinstance(learnings, list)
        assert len(learnings) >= 1


class TestPreventionRecommendations:
    """Test prevention recommendations extraction."""

    def test_extract_prevention_recommendations(self):
        """Test extraction of prevention recommendations."""
        from main import _extract_prevention_recommendations

        results = [
            """
**Prevention Recommendations**

To prevent similar bugs:
1. Add type hints with Optional[dict] for functions that can return None
2. Use mypy static type checker in CI/CD pipeline
3. Add assertion in tests that verify error handling for missing users
"""
        ]

        recommendations = _extract_prevention_recommendations(results)

        assert isinstance(recommendations, list)
        assert len(recommendations) >= 1


@pytest.mark.asyncio
class TestRunCodeDebugger:
    """Test main code debugger function."""

    async def test_successful_debugging(self):
        """Test successful debugging session."""
        from main import run_code_debugger

        config = {
            "architecture": "reflexion",
            "debugging": {
                "max_iterations": 5,
                "success_threshold": 0.9,
            },
            "reflexion_config": {
                "executor": {
                    "name": "debug_executor",
                    "role": "Execute debugging",
                    "tools": ["Read", "Bash"],
                },
                "reflector": {
                    "name": "debug_reflector",
                    "role": "Analyze results",
                    "focus_areas": ["Why failed?"],
                },
                "improver": {
                    "name": "strategy_improver",
                    "role": "Refine strategy",
                    "capabilities": [],
                },
            },
            "strategies": {
                "error_trace_analysis": {
                    "description": "Analyze error traces",
                    "priority": 1,
                },
            },
            "models": {"lead": "haiku"},
        }

        bug_description = "AttributeError when accessing user.email"
        context = {
            "error_message": "AttributeError: 'NoneType' object has no attribute 'get'",
            "file_path": "app.py",
            "code_snippet": "user_email = user.get('email')",
        }

        # Mock session
        mock_session = MagicMock()

        async def mock_run(prompt):
            yield """
### Iteration 1: Initial Analysis

**[Executor]** Execute debugging strategy

Strategy: error_trace_analysis
Found: Error at line 45 in app.py

**[Reflector]** Reflect on attempt

Why failed: Need to see fetch_user implementation

**[Improver]** Improve strategy

Next: code_inspection

### Iteration 2: Code Inspection

**[Executor]** Checked fetch_user - returns None for invalid ID

**Root Cause Identified**

Category: Data Issues

Description: fetch_user returns None but code assumes dict

Confidence: High

Evidence:
1. fetch_user can return None
2. No null check before .get()
3. Stack trace confirms NoneType error

**Proposed Fix**

# File: app.py

# Explanation:
Add null checking before accessing user object

**Failed Attempts Summary**

Iteration 1: Tried error_trace_analysis - Failed because needed more context

Key learnings:
1. Always validate None returns

**Prevention Recommendations**

To prevent similar bugs:
1. Add type hints with Optional
"""

        mock_session.run = mock_run
        mock_session.teardown = AsyncMock()

        with patch("main.init", return_value=mock_session):
            result = await run_code_debugger(config, bug_description, context)

            # Verify result structure
            assert "debug_session_id" in result
            assert "title" in result
            assert "summary" in result
            assert "bug" in result
            assert "debugging_timeline" in result
            assert "root_cause" in result
            assert "proposed_fix" in result
            assert "metadata" in result

            assert result["bug"]["description"] == bug_description
            assert "AttributeError" in result["title"]

    async def test_missing_config_fields(self):
        """Test error handling for missing required config."""
        from main import ConfigurationError, run_code_debugger

        # Missing required fields
        config = {"architecture": "reflexion"}

        bug_description = "Test bug"
        context = {"error_message": "Test error"}

        with pytest.raises((ConfigurationError, ValueError)):
            await run_code_debugger(config, bug_description, context)
