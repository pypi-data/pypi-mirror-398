"""Integration tests for Codebase Analysis."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.mark.asyncio
class TestEndToEndAnalysis:
    """Test complete end-to-end analysis workflow."""

    async def test_successful_large_scale_analysis(self):
        """Test successful analysis of large codebase."""
        from main import run_codebase_analysis

        config = {
            "architecture": "mapreduce",
            "analysis": {
                "max_parallel_mappers": 10,
                "chunk_size": 50,
                "aggregation_strategy": "weighted",
                "min_confidence": 0.7,
            },
            "mapreduce_config": {
                "mapper": {
                    "name": "code_analyzer",
                    "role": "Analyze code chunks",
                    "tools": ["Read", "Bash", "Grep"],
                },
                "reducer": {
                    "name": "results_aggregator",
                    "role": "Aggregate results",
                    "capabilities": ["Deduplication", "Prioritization"],
                },
                "coordinator": {
                    "name": "analysis_coordinator",
                    "role": "Orchestrate analysis",
                    "responsibilities": ["Intelligent chunking"],
                },
            },
            "analysis_types": {
                "code_quality": {"enabled": True, "priority": 1, "checks": ["complexity"]},
                "security": {"enabled": True, "priority": 1, "checks": ["sql_injection"]},
            },
            "models": {"coordinator": "haiku"},
        }

        codebase_path = "/path/to/large/codebase"

        # Mock session with realistic large-scale analysis output
        mock_session = MagicMock()

        async def mock_run(prompt):
            yield """
**Analysis Report for /path/to/large/codebase**

## Chunks Analyzed

**Chunk 1 Analysis** (Files: ['auth/models.py', 'auth/views.py', 'auth/serializers.py'])

Issues Found:
- [Critical] [security] in auth/models.py:45 - SQL injection vulnerability in raw query
- [High] [quality] in auth/views.py:123 - Cyclomatic complexity 25 exceeds threshold
- [Medium] [quality] in auth/serializers.py:67 - Missing input validation

**Chunk 2 Analysis** (Files: ['api/endpoints.py', 'api/middleware.py'])

Issues Found:
- [High] [security] in api/endpoints.py:89 - Missing authentication check
- [Medium] [performance] in api/middleware.py:34 - N+1 query pattern detected

**Chunk 3 Analysis** (Files: ['utils/helpers.py', 'utils/validators.py'])

Issues Found:
- [Low] [quality] in utils/helpers.py:12 - Function naming convention violation
- [Medium] [maintainability] in utils/validators.py:56 - Deprecated API usage

## Metrics Summary

**Overall Metrics**:
- Total files analyzed: 250
- Total lines of code: 35000
- Average complexity: 6.8
- Test coverage: 72.5%
- Quality score: 78
- Security score: 68
- Maintainability score: 82
- Performance score: 85

**Module Health**:
- auth_module: 65/100
- api_module: 78/100
- utils_module: 88/100
- core_module: 92/100
- tests_module: 95/100

**Trends**:
- New issues introduced: 23
- Issues resolved: 18
- Net change: +5

**Top Recommendations**:

1. Fix SQL injection vulnerability in auth/models.py
   Reason: Critical security risk
   Effort: Medium
   Impact: High

2. Reduce cyclomatic complexity in auth/views.py
   Reason: Code maintainability and testing
   Effort: High
   Impact: Medium

3. Add authentication checks to all API endpoints
   Reason: Security best practice
   Effort: Medium
   Impact: High

4. Increase test coverage to target 80%
   Reason: Quality assurance
   Effort: High
   Impact: Medium

5. Replace deprecated API usage in validators
   Reason: Future compatibility
   Effort: Low
   Impact: Low
        """

        mock_session.run = mock_run
        mock_session.teardown = AsyncMock()

        with patch("main.init", return_value=mock_session):
            result = await run_codebase_analysis(config, codebase_path)

            # Verify complete result structure
            assert "analysis_id" in result
            assert "title" in result
            assert "summary" in result
            assert "codebase" in result
            assert "execution" in result
            assert "issues" in result
            assert "metrics" in result
            assert "scores" in result
            assert "module_health" in result
            assert "trends" in result
            assert "recommendations" in result

            # Verify issues parsed correctly
            assert result["issues"]["total"] == 7
            assert len(result["issues"]["critical"]) == 1
            assert len(result["issues"]["high"]) == 2
            assert len(result["issues"]["medium"]) == 3
            assert len(result["issues"]["low"]) == 1

            # Verify metrics
            assert result["metrics"]["total_files"] == 250
            assert result["metrics"]["total_lines"] == 35000
            assert result["metrics"]["average_complexity"] == 6.8
            assert result["metrics"]["test_coverage"] == 72.5

            # Verify scores
            assert result["scores"]["quality"] == 78
            assert result["scores"]["security"] == 68
            assert result["scores"]["maintainability"] == 82
            assert 0 <= result["scores"]["overall"] <= 100

            # Verify chunks
            assert len(result["execution"]["chunks_analyzed"]) == 3
            assert result["execution"]["chunks_analyzed"][0]["chunk_id"] == 1
            assert result["execution"]["chunks_analyzed"][0]["file_count"] == 3

            # Verify module health
            assert len(result["module_health"]) == 5
            assert result["module_health"][0]["name"] == "auth_module"
            assert result["module_health"][0]["score"] == 65
            assert result["module_health"][0]["status"] == "needs_attention"

            # Verify trends
            assert result["trends"]["new_issues"] == 23
            assert result["trends"]["resolved_issues"] == 18
            assert result["trends"]["net_change"] == 5

            # Verify recommendations
            assert len(result["recommendations"]) >= 5  # At least 5 recommendations extracted

            # Verify execution metadata
            assert result["execution"]["parallel_mappers"] == 3


@pytest.mark.asyncio
class TestConfigurationValidation:
    """Test configuration validation."""

    async def test_missing_required_fields(self):
        """Test error when required config fields are missing."""
        from main import ConfigurationError, run_codebase_analysis

        # Missing analysis field
        config = {
            "architecture": "mapreduce",
            "mapreduce_config": {
                "mapper": {"name": "test", "role": "test"},
                "reducer": {"name": "test", "role": "test"},
                "coordinator": {"name": "test", "role": "test"},
            },
            "analysis_types": {},
        }

        with pytest.raises((ConfigurationError, ValueError, KeyError)):
            await run_codebase_analysis(config, "/path")

    async def test_wrong_architecture_type(self):
        """Test error when architecture is not mapreduce."""
        from main import ConfigurationError, run_codebase_analysis

        config = {
            "architecture": "pipeline",  # Wrong architecture
            "analysis": {},
            "mapreduce_config": {
                "mapper": {"name": "test", "role": "test"},
                "reducer": {"name": "test", "role": "test"},
                "coordinator": {"name": "test", "role": "test"},
            },
            "analysis_types": {},
        }

        with pytest.raises((ConfigurationError, ValueError)):
            await run_codebase_analysis(config, "/path")

    async def test_missing_mapreduce_roles(self):
        """Test error when mapreduce roles are incomplete."""
        from main import ConfigurationError, run_codebase_analysis

        # Missing reducer
        config = {
            "architecture": "mapreduce",
            "analysis": {},
            "mapreduce_config": {
                "mapper": {"name": "test", "role": "test"},
                "coordinator": {"name": "test", "role": "test"},
            },
            "analysis_types": {},
        }

        with pytest.raises((ConfigurationError, ValueError, KeyError)):
            await run_codebase_analysis(config, "/path")


@pytest.mark.asyncio
class TestRealWorldScenarios:
    """Test real-world analysis scenarios."""

    async def test_security_focused_analysis(self):
        """Test analysis focused on security issues."""
        from main import run_codebase_analysis

        config = {
            "architecture": "mapreduce",
            "analysis": {
                "max_parallel_mappers": 5,
                "chunk_size": 30,
                "aggregation_strategy": "weighted",
                "min_confidence": 0.8,
            },
            "mapreduce_config": {
                "mapper": {
                    "name": "security_analyzer",
                    "role": "Analyze security",
                    "tools": ["Read", "Bash"],
                },
                "reducer": {
                    "name": "security_aggregator",
                    "role": "Aggregate",
                    "capabilities": ["Deduplication"],
                },
                "coordinator": {
                    "name": "coordinator",
                    "role": "Orchestrate",
                    "responsibilities": ["Chunking"],
                },
            },
            "analysis_types": {
                "security": {
                    "enabled": True,
                    "priority": 1,
                    "checks": ["sql_injection", "xss", "hardcoded_secrets"],
                }
            },
            "models": {"coordinator": "haiku"},
        }

        mock_session = MagicMock()

        async def mock_run(prompt):
            yield """
**Security Analysis Report**

**Chunk 1 Analysis** (Files: ['app.py', 'db.py'])

Issues Found:
- [Critical] [security] in app.py:12 - Hardcoded API key in source code
- [Critical] [security] in db.py:45 - SQL injection via string formatting
- [High] [security] in app.py:67 - Missing CSRF protection

**Metrics Summary**:
- Total files analyzed: 50
- Total lines of code: 5000
- Security score: 45

**Top Recommendations**:
1. Remove hardcoded credentials immediately
2. Use parameterized queries for all database access
        """

        mock_session.run = mock_run
        mock_session.teardown = AsyncMock()

        with patch("main.init", return_value=mock_session):
            result = await run_codebase_analysis(config, "/path/to/app")

            # Verify security focus
            assert result["issues"]["total"] >= 3
            critical = [i for i in result["issues"]["all_issues"] if i["severity"] == "critical"]
            assert len(critical) >= 2
            assert any("sql injection" in i["description"].lower() for i in critical)


@pytest.mark.asyncio
class TestResultParsing:
    """Test parsing of various result formats."""

    async def test_parse_multiple_issue_formats(self):
        """Test parsing issues in different formats."""
        from main import run_codebase_analysis

        config = {
            "architecture": "mapreduce",
            "analysis": {},
            "mapreduce_config": {
                "mapper": {"name": "test", "role": "test", "tools": ["Read"]},
                "reducer": {"name": "test", "role": "test", "capabilities": []},
                "coordinator": {"name": "test", "role": "test", "responsibilities": []},
            },
            "analysis_types": {"code_quality": {"enabled": True, "priority": 1, "checks": []}},
            "models": {"coordinator": "haiku"},
        }

        mock_session = MagicMock()

        async def mock_run(prompt):
            yield """
Issues Found:
- [Critical] [security] in auth.py:45 - SQL injection
- [High] [performance] in api.py:123 - N+1 queries

**Top 5 Critical Issues**:
1. Memory leak in session_manager.py:89
2. XSS vulnerability in template.py:34
3. Unvalidated redirect in login.py:56

**Metrics Summary**:
- Total files analyzed: 100
- Total lines of code: 10000
        """

        mock_session.run = mock_run
        mock_session.teardown = AsyncMock()

        with patch("main.init", return_value=mock_session):
            result = await run_codebase_analysis(config, "/path")

            # Should parse both formats
            assert result["issues"]["total"] >= 5


@pytest.mark.asyncio
class TestEdgeCases:
    """Test edge cases and error handling."""

    async def test_empty_analysis_results(self):
        """Test handling when no issues are found."""
        from main import run_codebase_analysis

        config = {
            "architecture": "mapreduce",
            "analysis": {},
            "mapreduce_config": {
                "mapper": {"name": "test", "role": "test", "tools": ["Read"]},
                "reducer": {"name": "test", "role": "test", "capabilities": []},
                "coordinator": {"name": "test", "role": "test", "responsibilities": []},
            },
            "analysis_types": {"code_quality": {"enabled": True, "priority": 1, "checks": []}},
            "models": {"coordinator": "haiku"},
        }

        mock_session = MagicMock()

        async def mock_run(prompt):
            yield """
**Analysis Complete**

**Chunk 1 Analysis** (Files: ['clean_code.py'])

Issues Found: None

**Metrics Summary**:
- Total files analyzed: 10
- Total lines of code: 1000
- Quality score: 95
        """

        mock_session.run = mock_run
        mock_session.teardown = AsyncMock()

        with patch("main.init", return_value=mock_session):
            result = await run_codebase_analysis(config, "/path")

            # Should handle gracefully
            assert result["issues"]["total"] == 0
            assert len(result["issues"]["critical"]) == 0
            assert result["metrics"]["quality_score"] == 95

    async def test_partial_metrics_parsing(self):
        """Test handling when only some metrics are available."""
        from main import run_codebase_analysis

        config = {
            "architecture": "mapreduce",
            "analysis": {},
            "mapreduce_config": {
                "mapper": {"name": "test", "role": "test", "tools": ["Read"]},
                "reducer": {"name": "test", "role": "test", "capabilities": []},
                "coordinator": {"name": "test", "role": "test", "responsibilities": []},
            },
            "analysis_types": {"code_quality": {"enabled": True, "priority": 1, "checks": []}},
            "models": {"coordinator": "haiku"},
        }

        mock_session = MagicMock()

        async def mock_run(prompt):
            yield """
**Metrics Summary**:
- Total files analyzed: 50
- Quality score: 80
        """

        mock_session.run = mock_run
        mock_session.teardown = AsyncMock()

        with patch("main.init", return_value=mock_session):
            result = await run_codebase_analysis(config, "/path")

            # Should use defaults for missing metrics
            assert result["metrics"]["total_files"] == 50
            assert result["metrics"]["quality_score"] == 80
            assert "total_lines" in result["metrics"]  # Should have default

    async def test_malformed_chunk_info(self):
        """Test handling malformed chunk information."""
        from main import run_codebase_analysis

        config = {
            "architecture": "mapreduce",
            "analysis": {},
            "mapreduce_config": {
                "mapper": {"name": "test", "role": "test", "tools": ["Read"]},
                "reducer": {"name": "test", "role": "test", "capabilities": []},
                "coordinator": {"name": "test", "role": "test", "responsibilities": []},
            },
            "analysis_types": {"code_quality": {"enabled": True, "priority": 1, "checks": []}},
            "models": {"coordinator": "haiku"},
        }

        mock_session = MagicMock()

        async def mock_run(prompt):
            yield """
**Chunk Analysis** (Files: malformed data)

**Metrics Summary**:
- Total files analyzed: 10
- Total lines of code: 1000
        """

        mock_session.run = mock_run
        mock_session.teardown = AsyncMock()

        with patch("main.init", return_value=mock_session):
            result = await run_codebase_analysis(config, "/path")

            # Should handle gracefully, chunks_analyzed might have placeholder data
            assert "execution" in result
            assert "chunks_analyzed" in result["execution"]
