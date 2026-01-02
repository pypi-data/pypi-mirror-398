"""Integration tests for IT support platform."""

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
            "architecture": "specialist_pool",
            "specialists": [
                {
                    "name": "network_specialist",
                    "description": "Network infrastructure expert",
                    "keywords": ["network", "vpn", "connectivity"],
                    "priority": 1,
                },
                {
                    "name": "security_specialist",
                    "description": "Security expert",
                    "keywords": ["security", "breach", "authentication"],
                    "priority": 1,
                },
            ],
            "routing": {
                "strategy": "keyword_match",
                "min_keyword_matches": 1,
                "allow_multiple": True,
                "max_specialists": 2,
            },
            "categorization": {
                "urgency_levels": [
                    {"name": "critical", "sla_hours": 1, "keywords": ["down", "breach"]},
                    {"name": "high", "sla_hours": 4, "keywords": ["urgent"]},
                ]
            },
            "response_template": {
                "include_diagnosis": True,
                "include_steps": True,
                "include_prevention": True,
            },
            "models": {"lead": "haiku"},
            "output": {"directory": str(tmp_path / "outputs"), "format": "json"},
        }

        # Mock session
        mock_session = MagicMock()
        mock_session.session_dir = tmp_path / "session"

        async def mock_run(prompt):
            yield """
### security_specialist

**Analysis**: Security breach detected from suspicious IP addresses.

**Root Cause**: Weak password policy allowed brute force attacks.

**Resolution Steps**:
1. Block suspicious IP addresses immediately
2. Force password reset for affected accounts
3. Enable MFA for all users

**Prevention**: Implement stricter password policies and rate limiting.

**Confidence**: High

### Consolidated Solution

**Primary Root Cause**: Inadequate authentication security

**Recommended Action Plan**:
1. Immediate: Block attacking IPs
2. Short-term: Force password resets
3. Long-term: Implement MFA

**Expected Resolution Time**: 2 hours

**Risk Assessment**: High risk if not addressed immediately
"""

        mock_session.run = mock_run
        mock_session.teardown = AsyncMock()

        with patch("main.init", return_value=mock_session):
            # Run IT support
            result = await main.run_it_support(
                config,
                "Security breach detected",  # "breach" keyword for critical urgency
                "Multiple failed login attempts from unusual IPs",
            )

            # Verify result structure
            assert "title" in result
            assert "summary" in result
            assert "issue" in result
            assert "routing" in result
            assert "specialist_responses" in result
            assert "consolidated_solution" in result
            assert "metadata" in result

            # Verify routing
            assert result["metadata"]["urgency"] == "critical"
            assert result["metadata"]["sla_hours"] == 1

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
            "architecture": "specialist_pool",
            "specialists": [],
            "routing": {},
            "output": {},
        }

        # Should not raise
        validate_config(valid_config, ["architecture", "specialists", "routing", "output"])

        # Invalid config - missing fields
        invalid_config = {"architecture": "specialist_pool"}

        with pytest.raises(ValueError) as exc_info:
            validate_config(invalid_config, ["architecture", "specialists", "routing", "output"])

        assert "Missing required configuration fields" in str(exc_info.value)

    def test_config_loading(self):
        """Test YAML config loading."""
        from common import load_yaml_config

        # Test with actual config file
        config_path = Path(__file__).parent.parent / "config.yaml"

        if config_path.exists():
            config = load_yaml_config(config_path)

            assert "architecture" in config
            assert "specialists" in config
            assert "routing" in config
            assert config["architecture"] == "specialist_pool"
            assert len(config["specialists"]) > 0

    async def test_specialist_routing_logic(self):
        """Test specialist routing with different scenarios."""
        from main import _route_to_specialists

        specialists = [
            {
                "name": "network_specialist",
                "keywords": ["network", "vpn", "firewall"],
                "priority": 1,
            },
            {
                "name": "database_specialist",
                "keywords": ["database", "sql", "query"],
                "priority": 1,
            },
            {
                "name": "cloud_specialist",
                "keywords": ["cloud", "aws", "kubernetes"],
                "priority": 2,
            },
        ]

        routing_config = {
            "min_keyword_matches": 1,
            "allow_multiple": True,
            "max_specialists": 3,
        }

        # Test network issue
        selected = _route_to_specialists(
            "VPN not connecting",
            "Cannot establish VPN connection",
            specialists,
            routing_config,
        )

        specialist_names = [s["name"] for s in selected]
        assert "network_specialist" in specialist_names

        # Test database issue
        selected = _route_to_specialists(
            "Slow SQL queries",
            "Database performance degradation",
            specialists,
            routing_config,
        )

        specialist_names = [s["name"] for s in selected]
        assert "database_specialist" in specialist_names

    async def test_urgency_categorization_logic(self):
        """Test urgency categorization."""
        from main import _categorize_urgency

        categorization_config = {
            "urgency_levels": [
                {"name": "critical", "sla_hours": 1, "keywords": ["down", "outage", "breach"]},
                {"name": "high", "sla_hours": 4, "keywords": ["urgent", "production"]},
                {"name": "medium", "sla_hours": 24, "keywords": ["bug", "issue"]},
                {"name": "low", "sla_hours": 72, "keywords": ["request", "question"]},
            ]
        }

        # Critical
        urgency, sla = _categorize_urgency("System down", "Complete outage", categorization_config)
        assert urgency == "critical"
        assert sla == 1

        # High
        urgency, sla = _categorize_urgency(
            "Urgent production issue", "Customer impact", categorization_config
        )
        assert urgency == "high"
        assert sla == 4

        # Medium
        urgency, sla = _categorize_urgency(
            "Bug in feature", "Minor issue reported", categorization_config
        )
        assert urgency == "medium"
        assert sla == 24

    async def test_response_parsing(self):
        """Test specialist response parsing."""
        from main import _consolidate_solutions, _parse_specialist_responses

        specialists = [
            {"name": "network_specialist", "description": "Network expert"},
            {"name": "security_specialist", "description": "Security expert"},
        ]

        results = [
            """
### network_specialist

**Analysis**: Network configuration issue

**Confidence**: High

### security_specialist

**Analysis**: No security concerns

**Confidence**: Medium

### Consolidated Solution

**Primary Root Cause**: Network configuration

**Recommended Action Plan**:
1. Fix configuration
2. Test connectivity

**Expected Resolution Time**: 1 hour
"""
        ]

        responses = _parse_specialist_responses(results, specialists)

        assert len(responses) == 2
        assert responses[0]["specialist"] == "network_specialist"
        assert responses[0]["confidence"] == "High"
        assert responses[1]["specialist"] == "security_specialist"
        assert responses[1]["confidence"] == "Medium"

        # Test consolidation
        consolidated = _consolidate_solutions(responses, results)
        assert "Consolidated Solution" in consolidated
        assert "Network configuration" in consolidated

    def test_specialist_configuration(self):
        """Test specialist configuration structure."""
        from common import load_yaml_config

        config_path = Path(__file__).parent.parent / "config.yaml"

        if config_path.exists():
            config = load_yaml_config(config_path)

            specialists = config["specialists"]
            assert len(specialists) > 0

            # Verify required fields
            for specialist in specialists:
                assert "name" in specialist
                assert "description" in specialist
                assert "keywords" in specialist
                assert "priority" in specialist
                assert isinstance(specialist["keywords"], list)
                assert isinstance(specialist["priority"], int)

    def test_routing_configuration(self):
        """Test routing configuration."""
        from common import load_yaml_config

        config_path = Path(__file__).parent.parent / "config.yaml"

        if config_path.exists():
            config = load_yaml_config(config_path)

            routing = config["routing"]

            assert "strategy" in routing
            assert "min_keyword_matches" in routing
            assert "allow_multiple" in routing
            assert "max_specialists" in routing
            assert "use_fallback" in routing

    def test_result_saver_markdown(self, tmp_path):
        """Test ResultSaver with Markdown format for IT support."""
        from common import ResultSaver

        saver = ResultSaver(tmp_path)

        result = {
            "title": "IT Support Resolution: VPN Issue",
            "summary": "Resolved network issue with 2 specialists",
            "issue": {"title": "VPN problem", "urgency": "high"},
            "routing": {"specialists": ["network_specialist"]},
        }

        output_path = saver.save(result, format="markdown", filename="it_support")

        assert output_path.exists()
        assert output_path.name == "it_support.md"

        # Verify content
        content = output_path.read_text()
        assert "# IT Support Resolution: VPN Issue" in content
        assert "Resolved network issue" in content

    async def test_fallback_specialist_usage(self):
        """Test fallback specialist when no specialists match."""
        from main import _get_fallback_specialist, _route_to_specialists

        specialists = [
            {"name": "network_specialist", "keywords": ["network"], "priority": 1},
            {"name": "general_specialist", "keywords": [], "priority": 5},
        ]

        routing_config = {
            "min_keyword_matches": 1,
            "allow_multiple": False,
            "max_specialists": 1,
        }

        # Issue with no matching keywords
        selected = _route_to_specialists(
            "Random issue",
            "Something unrelated to any specialist",
            specialists,
            routing_config,
        )

        # Should be empty (no matches)
        assert len(selected) == 0

        # Get fallback
        fallback = _get_fallback_specialist(specialists)
        assert fallback["name"] == "general_specialist"
        assert fallback["priority"] == 5
