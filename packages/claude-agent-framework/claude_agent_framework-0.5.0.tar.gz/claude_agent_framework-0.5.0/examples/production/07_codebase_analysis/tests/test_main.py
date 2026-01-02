"""Unit tests for Codebase Analysis."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPromptBuilding:
    """Test mapreduce prompt construction."""

    def test_basic_prompt_structure(self):
        """Test basic prompt includes all key sections."""
        from main import _build_mapreduce_prompt

        codebase_path = "/path/to/codebase"
        analysis_config = {
            "max_parallel_mappers": 10,
            "chunk_size": 50,
            "aggregation_strategy": "weighted",
            "min_confidence": 0.7,
        }
        mapreduce_config = {
            "mapper": {
                "name": "code_analyzer",
                "role": "Analyze code chunks",
                "tools": ["Read", "Bash"],
                "analysis_depth": "comprehensive",
            },
            "reducer": {
                "name": "results_aggregator",
                "role": "Aggregate results",
                "capabilities": ["Deduplication", "Prioritization"],
            },
            "coordinator": {
                "name": "analysis_coordinator",
                "role": "Orchestrate analysis",
                "responsibilities": ["Intelligent chunking", "Load balancing"],
            },
        }
        analysis_types = {
            "code_quality": {"enabled": True, "priority": 1, "checks": ["complexity"]},
            "security": {"enabled": True, "priority": 1, "checks": ["sql_injection"]},
        }
        chunking_strategies = {
            "by_module": {
                "description": "Group by module",
                "benefits": ["Respects organization"],
            }
        }
        aggregation_rules = {
            "deduplication": {"similarity_threshold": 0.85},
            "prioritization": {"criteria": {"severity": 0.4}},
        }
        output_config = {}
        advanced = {
            "filters": {
                "exclude_paths": ["*/tests/*"],
                "include_extensions": [".py", ".js"],
            }
        }
        options = {"chunking_strategy": "by_module"}

        prompt = _build_mapreduce_prompt(
            codebase_path,
            analysis_config,
            mapreduce_config,
            analysis_types,
            chunking_strategies,
            aggregation_rules,
            output_config,
            advanced,
            options,
        )

        # Verify key sections
        assert codebase_path in prompt
        assert "code_analyzer" in prompt
        assert "results_aggregator" in prompt
        assert "analysis_coordinator" in prompt
        assert "Code Quality" in prompt
        assert "Security" in prompt
        assert "by_module" in prompt


class TestChunkExtraction:
    """Test chunk information extraction."""

    def test_extract_chunks(self):
        """Test extraction of chunk information."""
        from main import _extract_chunks_analyzed

        results = [
            """
**Chunk 1 Analysis** (Files: ['file1.py', 'file2.py', 'file3.py'])

Issues Found:
- [High] [complexity] in file1.py:45 - Function too complex

**Chunk 2 Analysis** (Files: ['file4.py', 'file5.py'])

Issues Found:
- [Critical] [security] in file4.py:12 - SQL injection risk
        """
        ]

        chunks = _extract_chunks_analyzed(results)

        assert len(chunks) >= 1
        assert isinstance(chunks, list)
        if len(chunks) >= 2:
            assert chunks[0]["chunk_id"] == 1
            assert chunks[0]["file_count"] == 3
            assert chunks[1]["chunk_id"] == 2
            assert chunks[1]["file_count"] == 2


class TestIssueExtraction:
    """Test issue extraction."""

    def test_extract_issues_format1(self):
        """Test extraction of issues in standard format."""
        from main import _extract_issues

        results = [
            """
Issues Found:
- [Critical] [security] in auth.py:45 - SQL injection vulnerability
- [High] [performance] in api.py:123 - N+1 query problem
- [Medium] [quality] in utils.py:67 - High complexity
        """
        ]

        issues = _extract_issues(results)

        assert len(issues) >= 3
        critical_issues = [i for i in issues if i["severity"] == "critical"]
        assert len(critical_issues) >= 1
        assert critical_issues[0]["file"] == "auth.py"
        assert critical_issues[0]["line"] == 45

    def test_extract_issues_from_top_list(self):
        """Test extraction of issues from top issues list."""
        from main import _extract_issues

        results = [
            """
**Top 10 Critical Issues**:
1. SQL injection vulnerability in auth.py:45
2. Memory leak in session_manager.py:123
3. XSS vulnerability in template.py:67
        """
        ]

        issues = _extract_issues(results)

        assert len(issues) >= 3
        assert any("auth.py" in i["file"] for i in issues)
        assert any(i["line"] == 45 for i in issues)


class TestMetricsExtraction:
    """Test metrics extraction."""

    def test_extract_metrics(self):
        """Test extraction of code metrics."""
        from main import _extract_metrics

        results = [
            """
**Metrics Summary**:
- Total files analyzed: 150
- Total lines of code: 12500
- Average complexity: 5.2
- Test coverage: 78.5%
- Quality score: 82
- Security score: 91
- Maintainability score: 75
        """
        ]

        metrics = _extract_metrics(results)

        assert metrics["total_files"] == 150
        assert metrics["total_lines"] == 12500
        assert metrics["average_complexity"] == 5.2
        assert metrics["test_coverage"] == 78.5
        assert metrics["quality_score"] == 82
        assert metrics["security_score"] == 91
        assert metrics["maintainability_score"] == 75


class TestModuleHealthExtraction:
    """Test module health extraction."""

    def test_extract_module_health(self):
        """Test extraction of module health scores."""
        from main import _extract_module_health

        results = [
            """
**Module Health**:
- auth_module: 95/100
- api_module: 72/100
- utils_module: 58/100
        """
        ]

        modules = _extract_module_health(results)

        assert len(modules) >= 3
        assert modules[0]["name"] == "auth_module"
        assert modules[0]["score"] == 95
        assert modules[0]["status"] == "healthy"
        assert modules[1]["name"] == "api_module"
        assert modules[1]["score"] == 72
        assert modules[1]["status"] == "needs_attention"
        assert modules[2]["score"] == 58
        assert modules[2]["status"] == "critical"  # < 60 = critical


class TestTrendsExtraction:
    """Test trends extraction."""

    def test_extract_trends(self):
        """Test extraction of trend data."""
        from main import _extract_trends

        results = [
            """
**Trends**:
- New issues introduced: 12
- Issues resolved: 18
- Net change: -6
        """
        ]

        trends = _extract_trends(results)

        assert trends["new_issues"] == 12
        assert trends["resolved_issues"] == 18
        assert trends["net_change"] == -6


class TestRecommendationsExtraction:
    """Test recommendations extraction."""

    def test_extract_recommendations(self):
        """Test extraction of recommendations."""
        from main import _extract_recommendations

        results = [
            """
**Top Recommendations**:
1. Add input validation to all API endpoints
   Reason: Prevent injection attacks
   Effort: Medium
   Impact: High

2. Reduce cyclomatic complexity in auth module
   Reason: Improve maintainability
   Effort: High
   Impact: Medium

3. Increase test coverage to 80%
        """
        ]

        recommendations = _extract_recommendations(results)

        assert len(recommendations) >= 3
        assert "validation" in recommendations[0]["action"].lower()


class TestScoreCalculation:
    """Test score calculation."""

    def test_calculate_overall_score(self):
        """Test overall score calculation."""
        from main import _calculate_overall_score

        metrics = {
            "quality_score": 80,
            "security_score": 90,
            "maintainability_score": 70,
            "test_coverage": 75,
        }

        module_health = [
            {"score": 85},
            {"score": 75},
            {"score": 80},
        ]

        score = _calculate_overall_score(metrics, module_health)

        assert 0 <= score <= 100
        assert score > 70  # Should be relatively high given inputs


class TestIssueSummarization:
    """Test issue summarization."""

    def test_summarize_issues(self):
        """Test issue count by severity."""
        from main import _summarize_issues

        issues = [
            {"severity": "critical"},
            {"severity": "critical"},
            {"severity": "high"},
            {"severity": "high"},
            {"severity": "high"},
            {"severity": "medium"},
            {"severity": "low"},
        ]

        summary = _summarize_issues(issues)

        assert summary["critical"] == 2
        assert summary["high"] == 3
        assert summary["medium"] == 1
        assert summary["low"] == 1


class TestSummaryGeneration:
    """Test summary generation."""

    def test_generate_summary(self):
        """Test executive summary generation."""
        from main import _generate_summary

        issue_summary = {
            "critical": 5,
            "high": 10,
            "medium": 20,
            "low": 15,
        }
        overall_score = 75
        chunks = [{"chunk_id": 1}, {"chunk_id": 2}, {"chunk_id": 3}]

        summary = _generate_summary(issue_summary, overall_score, chunks)

        assert "75/100" in summary
        assert "3 chunks" in summary
        assert "5 critical" in summary or "critical" in summary.lower()


@pytest.mark.asyncio
class TestRunCodebaseAnalysis:
    """Test main analysis function."""

    async def test_successful_analysis(self):
        """Test successful analysis execution."""
        from main import run_codebase_analysis

        config = {
            "architecture": "mapreduce",
            "analysis": {
                "max_parallel_mappers": 5,
                "chunk_size": 50,
                "aggregation_strategy": "weighted",
                "min_confidence": 0.7,
            },
            "mapreduce_config": {
                "mapper": {
                    "name": "code_analyzer",
                    "role": "Analyze code",
                    "tools": ["Read", "Bash"],
                },
                "reducer": {
                    "name": "results_aggregator",
                    "role": "Aggregate results",
                    "capabilities": ["Deduplication"],
                },
                "coordinator": {
                    "name": "analysis_coordinator",
                    "role": "Coordinate",
                    "responsibilities": ["Chunking"],
                },
            },
            "analysis_types": {
                "code_quality": {"enabled": True, "priority": 1, "checks": ["complexity"]}
            },
            "models": {"coordinator": "haiku"},
        }

        codebase_path = "/path/to/codebase"

        # Mock session
        mock_session = MagicMock()

        async def mock_run(prompt):
            yield """
**Chunk 1 Analysis** (Files: ['file1.py', 'file2.py'])

Issues Found:
- [Critical] [security] in file1.py:45 - SQL injection
- [High] [quality] in file2.py:123 - High complexity

**Metrics Summary**:
- Total files analyzed: 100
- Total lines of code: 10000
- Quality score: 80
- Security score: 85

**Module Health**:
- main_module: 82/100

**Top Recommendations**:
1. Fix SQL injection in file1.py
2. Reduce complexity in file2.py
        """

        mock_session.run = mock_run
        mock_session.teardown = AsyncMock()

        with patch("main.init", return_value=mock_session):
            result = await run_codebase_analysis(config, codebase_path)

            # Verify result structure
            assert "analysis_id" in result
            assert "title" in result
            assert "summary" in result
            assert "codebase" in result
            assert "execution" in result
            assert "issues" in result
            assert "metrics" in result
            assert "scores" in result

            # Verify issues
            assert result["issues"]["total"] >= 2
            assert len(result["issues"]["critical"]) >= 1

            # Verify metrics
            assert result["metrics"]["total_files"] == 100
            assert result["metrics"]["total_lines"] == 10000

    async def test_missing_config_fields(self):
        """Test error handling for missing config."""
        from main import ConfigurationError, run_codebase_analysis

        config = {"architecture": "mapreduce"}  # Missing required fields

        with pytest.raises((ConfigurationError, ValueError)):
            await run_codebase_analysis(config, "/path/to/codebase")

    async def test_invalid_architecture(self):
        """Test error for wrong architecture."""
        from main import ConfigurationError, run_codebase_analysis

        config = {
            "architecture": "wrong_arch",
            "analysis": {},
            "mapreduce_config": {
                "mapper": {},
                "reducer": {},
                "coordinator": {},
            },
            "analysis_types": {},
        }

        with pytest.raises((ConfigurationError, ValueError)):
            await run_codebase_analysis(config, "/path/to/codebase")
