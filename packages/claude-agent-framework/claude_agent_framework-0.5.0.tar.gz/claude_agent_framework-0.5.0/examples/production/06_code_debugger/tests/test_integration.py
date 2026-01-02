"""Integration tests for Code Debugger."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.mark.asyncio
class TestEndToEnd:
    """Test complete debugging workflow."""

    async def test_full_debugging_session(self):
        """Test complete debugging session from bug to fix."""
        from main import run_code_debugger

        config = {
            "architecture": "reflexion",
            "debugging": {
                "max_iterations": 5,
                "success_threshold": 0.9,
                "enable_learning": True,
                "preserve_history": True,
            },
            "reflexion_config": {
                "executor": {
                    "name": "debug_executor",
                    "role": "Execute debugging strategies",
                    "tools": ["Read", "Bash"],
                },
                "reflector": {
                    "name": "debug_reflector",
                    "role": "Analyze results",
                    "focus_areas": ["Why failed?", "What assumptions?"],
                },
                "improver": {
                    "name": "strategy_improver",
                    "role": "Refine strategy",
                    "capabilities": [],
                },
            },
            "strategies": {
                "error_trace_analysis": {
                    "name": "error_trace_analysis",
                    "description": "Analyze error traces",
                    "tools": ["Read", "Bash"],
                    "priority": 1,
                },
                "code_inspection": {
                    "name": "code_inspection",
                    "description": "Review code",
                    "tools": ["Read"],
                    "priority": 2,
                },
            },
            "bug_categories": {
                "runtime_error": {
                    "patterns": ["AttributeError", "TypeError"],
                    "strategies": ["error_trace_analysis", "code_inspection"],
                },
            },
            "root_cause_analysis": {
                "categories": [
                    {
                        "name": "Code Logic",
                        "indicators": ["Missing check", "Incorrect condition"],
                    },
                    {
                        "name": "Data Issues",
                        "indicators": ["None value", "Missing data"],
                    },
                ]
            },
            "models": {"lead": "haiku"},
        }

        bug_description = "AttributeError when accessing user.email"
        context = {
            "error_message": "AttributeError: 'NoneType' object has no attribute 'get'",
            "file_path": "app.py",
            "code_snippet": "user_email = user.get('email')",
            "expected_behavior": "Should handle missing user",
            "actual_behavior": "Crashes with AttributeError",
            "reproduction_steps": [
                "Call with invalid user ID",
                "fetch_user returns None",
                "Code tries to call .get() on None",
            ],
        }

        # Mock session
        mock_session = MagicMock()

        async def mock_run(prompt):
            yield """
### Iteration 1: Initial Analysis

**[Executor]** Execute debugging strategy

Strategy: error_trace_analysis
Actions:
- Analyzed stack trace
- Found error at line 45 in app.py
- Error shows None.get() call

Result: Located error but need to understand why None

**[Reflector]** Reflect on attempt

What worked:
- Successfully located the error line
- Identified the problematic method call

What didn't work:
- Couldn't determine why user is None
- Need to see fetch_user implementation

New information:
- Error occurs when user_id is invalid
- No validation before accessing user object

**[Improver]** Improve strategy

Based on reflection, next strategy: code_inspection
Focus on fetch_user implementation and calling code

### Iteration 2: Code Inspection

**[Executor]** Execute debugging strategy

Strategy: code_inspection
Actions:
- Reviewed fetch_user implementation
- Found it returns None for invalid IDs
- Checked calling code - no None check

Result: Identified root cause

**Root Cause Identified**

Category: Data Issues

Description: The fetch_user function returns None when given an invalid user ID, but the calling code in process_user_data assumes it always returns a dictionary and immediately calls .get() on the result without checking for None.

Why it causes the bug: When fetch_user returns None for an invalid user ID, the code tries to call .get('email') on None, which raises AttributeError: 'NoneType' object has no attribute 'get'.

Confidence: High

Evidence:
1. Stack trace clearly shows AttributeError on None.get() call at line 45
2. fetch_user implementation confirms it returns None for missing users
3. process_user_data has no None check before accessing user object
4. Reproduction steps consistently trigger the error with invalid IDs

**Proposed Fix**

```python
# File: app.py

# Before (problematic code):
def process_user_data(user_id):
    user = fetch_user(user_id)
    user_email = user.get('email')
    return user_email

# After (fixed code):
def process_user_data(user_id):
    user = fetch_user(user_id)
    if user is None:
        raise ValueError(f"User {user_id} not found")
    user_email = user.get('email')
    return user_email

# Explanation:
# Add explicit None check before accessing user object to prevent AttributeError.
# Raise a more descriptive ValueError to indicate the actual problem (missing user).
```

Alternative Approaches:
1. Return a default value instead of raising exception
2. Modify fetch_user to raise exception instead of returning None
3. Use Optional type hints to make None returns explicit

**Fix Validation**

Validation Steps:
1. Add unit test for invalid user ID case
2. Test with valid user ID to ensure no regression
3. Verify error message is clear and actionable
4. Check that error is caught at appropriate level

Expected Outcome:
- No more AttributeError for invalid user IDs
- Clear ValueError with user ID in message
- Existing valid user ID cases continue to work

**Failed Attempts Summary**

Iteration 1: Tried error_trace_analysis - Partially successful but couldn't determine root cause from trace alone, needed to see implementation

Key learnings:
1. Always validate None returns before accessing object methods
2. fetch_user should document that it returns None for invalid IDs
3. Consider using Optional type hints to make None returns explicit
4. Error messages should be descriptive (ValueError better than AttributeError here)

**Prevention Recommendations**

To prevent similar bugs in the future:
1. Add type hints with Optional[dict] for functions that can return None
2. Use mypy or pyright for static type checking in CI/CD pipeline
3. Add linting rule to detect potential None access without checks
4. Create coding standard requiring None checks for all optional returns
5. Add unit tests specifically for None/error cases, not just happy paths
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

            # Verify bug information
            assert result["bug"]["description"] == bug_description
            assert result["bug"]["category"] == "runtime_error"
            assert result["bug"]["context"] == context

            # Verify root cause
            root_cause = result["root_cause"]
            assert root_cause["category"] != "Unknown"
            assert "Data Issues" in root_cause["category"]
            assert "fetch_user" in root_cause["description"].lower()
            assert root_cause["confidence"] == "High"
            assert len(root_cause["evidence"]) >= 3

            # Verify proposed fix
            proposed_fix = result["proposed_fix"]
            assert proposed_fix["file_path"] == "app.py"
            assert "if user is None" in proposed_fix["after_code"]
            assert "ValueError" in proposed_fix["after_code"]
            assert len(proposed_fix["explanation"]) > 0

            # Verify title and summary
            assert "AttributeError" in result["title"]
            assert len(result["summary"]) > 0


@pytest.mark.asyncio
class TestConfigValidation:
    """Test configuration validation."""

    async def test_missing_required_config(self):
        """Test error handling for missing required config."""
        from main import ConfigurationError, run_code_debugger

        config = {"architecture": "reflexion"}  # Missing required fields

        with pytest.raises((ConfigurationError, ValueError)):
            await run_code_debugger(config, "Test bug", {"error_message": "Test error"})

    async def test_invalid_architecture(self):
        """Test error for wrong architecture type."""
        from main import ConfigurationError, run_code_debugger

        config = {
            "architecture": "wrong_arch",  # Should be reflexion
            "debugging": {"max_iterations": 5},
            "reflexion_config": {"executor": {}, "reflector": {}, "improver": {}},
            "strategies": {},
            "models": {"lead": "haiku"},
        }

        with pytest.raises((ConfigurationError, ValueError)):
            await run_code_debugger(config, "Test bug", {"error_message": "Test error"})


@pytest.mark.asyncio
class TestBugCategorization:
    """Test bug categorization in real scenarios."""

    async def test_categorize_runtime_error(self):
        """Test runtime error categorization."""
        from main import _categorize_bug

        bug_categories = {
            "runtime_error": {"patterns": ["AttributeError", "TypeError"]},
            "logic_error": {"patterns": ["Incorrect output"]},
        }

        category = _categorize_bug(
            "Error in processing",
            {"error_message": "AttributeError: object has no attribute 'x'"},
            bug_categories,
        )

        assert category == "runtime_error"

    async def test_categorize_logic_error(self):
        """Test logic error categorization."""
        from main import _categorize_bug

        bug_categories = {
            "runtime_error": {"patterns": ["AttributeError"]},
            "logic_error": {"patterns": ["Incorrect output", "Wrong result"]},
        }

        category = _categorize_bug(
            "Function returns wrong result",
            {"error_message": ""},
            bug_categories,
        )

        assert category == "logic_error"


@pytest.mark.asyncio
class TestResultParsing:
    """Test parsing of debugging results."""

    async def test_parse_complete_debugging_output(self):
        """Test parsing of complete debugging session."""
        from main import (
            _extract_failed_attempts,
            _extract_learnings,
            _extract_prevention_recommendations,
            _extract_proposed_fix,
            _extract_root_cause,
            _parse_debugging_timeline,
        )

        results = [
            """
### Iteration 1: Analysis

**[Executor]** Tried error_trace_analysis

**[Reflector]** Failed because X

**[Improver]** Next: code_inspection

### Iteration 2: Fix

**[Executor]** Found issue

**Root Cause Identified**

Category: Data Issues
Description: Missing None check
Confidence: High
Evidence:
1. Stack trace shows None access
2. No validation in code

**Proposed Fix**

# File: app.py
# Explanation: Add None check

**Failed Attempts Summary**

Iteration 1: error_trace_analysis - Not enough info

Key learnings:
1. Always validate None
2. Use type hints

**Prevention Recommendations**

1. Add type hints
2. Use static analysis
"""
        ]

        # Test timeline parsing
        timeline = _parse_debugging_timeline(results)
        assert len(timeline) >= 1
        assert isinstance(timeline, list)

        # Test root cause extraction
        root_cause = _extract_root_cause(results)
        assert "category" in root_cause
        assert "Data Issues" in root_cause["category"]

        # Test proposed fix extraction
        proposed_fix = _extract_proposed_fix(results)
        assert "file_path" in proposed_fix
        assert proposed_fix["file_path"] == "app.py"

        # Test failed attempts extraction
        failed_attempts = _extract_failed_attempts(results)
        assert isinstance(failed_attempts, list)

        # Test learnings extraction
        learnings = _extract_learnings(results)
        assert isinstance(learnings, list)
        assert len(learnings) >= 1

        # Test prevention recommendations extraction
        recommendations = _extract_prevention_recommendations(results)
        assert isinstance(recommendations, list)
        assert len(recommendations) >= 1


@pytest.mark.asyncio
class TestEdgeCases:
    """Test edge cases and error conditions."""

    async def test_empty_context(self):
        """Test handling of minimal context."""
        from main import run_code_debugger

        config = {
            "architecture": "reflexion",
            "debugging": {"max_iterations": 5, "success_threshold": 0.9},
            "reflexion_config": {
                "executor": {"name": "executor", "role": "Execute", "tools": []},
                "reflector": {
                    "name": "reflector",
                    "role": "Reflect",
                    "focus_areas": [],
                },
                "improver": {"name": "improver", "role": "Improve", "capabilities": []},
            },
            "strategies": {},
            "models": {"lead": "haiku"},
        }

        bug_description = "Simple bug"
        context = {"error_message": "Simple error"}

        mock_session = MagicMock()

        async def mock_run(prompt):
            yield "Basic debugging output"

        mock_session.run = mock_run
        mock_session.teardown = AsyncMock()

        with patch("main.init", return_value=mock_session):
            result = await run_code_debugger(config, bug_description, context)

            assert "debug_session_id" in result
            assert result["bug"]["description"] == bug_description

    async def test_no_root_cause_found(self):
        """Test when no clear root cause is identified."""
        from main import _extract_root_cause

        results = ["No root cause information here"]

        root_cause = _extract_root_cause(results)

        assert root_cause["category"] == "Unknown"
        assert root_cause["confidence"] == "Unknown"

    async def test_no_proposed_fix(self):
        """Test when no fix is proposed."""
        from main import _extract_proposed_fix

        results = ["No fix proposed"]

        proposed_fix = _extract_proposed_fix(results)

        assert proposed_fix["file_path"] is None
        assert proposed_fix["before_code"] is None
