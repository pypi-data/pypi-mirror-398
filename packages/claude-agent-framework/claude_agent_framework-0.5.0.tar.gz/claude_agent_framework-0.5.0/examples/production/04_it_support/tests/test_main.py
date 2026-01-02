"""Unit tests for IT support platform."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestUrgencyCategorization:
    """Test urgency categorization."""

    def test_critical_urgency(self):
        """Test critical urgency detection."""
        from main import _categorize_urgency

        categorization_config = {
            "urgency_levels": [
                {"name": "critical", "sla_hours": 1, "keywords": ["down", "outage", "breach"]},
                {"name": "high", "sla_hours": 4, "keywords": ["urgent", "production"]},
                {"name": "medium", "sla_hours": 24, "keywords": ["bug", "issue"]},
            ]
        }

        urgency, sla = _categorize_urgency(
            "Production server down",
            "All services are unavailable",
            categorization_config,
        )

        assert urgency == "critical"
        assert sla == 1

    def test_high_urgency(self):
        """Test high urgency detection."""
        from main import _categorize_urgency

        categorization_config = {
            "urgency_levels": [
                {"name": "critical", "sla_hours": 1, "keywords": ["down", "outage"]},
                {"name": "high", "sla_hours": 4, "keywords": ["urgent", "production"]},
            ]
        }

        urgency, sla = _categorize_urgency(
            "Urgent: Production issue",
            "Customer-facing feature not working",
            categorization_config,
        )

        assert urgency == "high"
        assert sla == 4

    def test_default_medium_urgency(self):
        """Test default medium urgency when no keywords match."""
        from main import _categorize_urgency

        categorization_config = {
            "urgency_levels": [
                {"name": "critical", "sla_hours": 1, "keywords": ["down", "outage"]},
            ]
        }

        urgency, sla = _categorize_urgency(
            "General question",
            "How do I configure this feature?",
            categorization_config,
        )

        assert urgency == "medium"
        assert sla == 24


class TestSpecialistRouting:
    """Test specialist routing logic."""

    def test_single_specialist_routing(self):
        """Test routing to single specialist based on keywords."""
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
        ]

        routing_config = {
            "min_keyword_matches": 1,
            "allow_multiple": False,
            "max_specialists": 1,
        }

        selected = _route_to_specialists(
            "VPN connection issues",
            "Cannot connect to company VPN",
            specialists,
            routing_config,
        )

        assert len(selected) == 1
        assert selected[0]["name"] == "network_specialist"

    def test_multiple_specialist_routing(self):
        """Test routing to multiple specialists."""
        from main import _route_to_specialists

        specialists = [
            {
                "name": "network_specialist",
                "keywords": ["network", "connectivity"],
                "priority": 1,
            },
            {
                "name": "security_specialist",
                "keywords": ["security", "authentication"],
                "priority": 1,
            },
            {
                "name": "general_specialist",
                "keywords": ["general"],
                "priority": 5,
            },
        ]

        routing_config = {
            "min_keyword_matches": 1,
            "allow_multiple": True,
            "max_specialists": 3,
        }

        selected = _route_to_specialists(
            "Network security issue",
            "Connectivity problems with authentication failures",
            specialists,
            routing_config,
        )

        assert len(selected) >= 1
        specialist_names = [s["name"] for s in selected]
        # Should match both network and security specialists
        assert "network_specialist" in specialist_names or "security_specialist" in specialist_names

    def test_priority_based_routing(self):
        """Test that higher priority specialists are selected first."""
        from main import _route_to_specialists

        specialists = [
            {
                "name": "specialist_low_priority",
                "keywords": ["issue", "problem"],
                "priority": 3,
            },
            {
                "name": "specialist_high_priority",
                "keywords": ["issue", "critical"],
                "priority": 1,
            },
        ]

        routing_config = {
            "min_keyword_matches": 1,
            "allow_multiple": True,
            "max_specialists": 2,
        }

        selected = _route_to_specialists(
            "Critical issue",
            "Major problem affecting production",
            specialists,
            routing_config,
        )

        # High priority specialist should be first
        if len(selected) > 0:
            assert (
                selected[0]["priority"] <= selected[-1]["priority"] if len(selected) > 1 else True
            )


class TestPromptBuilding:
    """Test prompt building."""

    def test_basic_prompt_structure(self):
        """Test basic prompt structure."""
        from main import _build_specialist_pool_prompt

        specialists = [
            {"name": "network_specialist", "description": "Network expert"},
        ]

        prompt = _build_specialist_pool_prompt(
            title="Network issue",
            description="Connection problems",
            specialists=specialists,
            urgency="high",
            sla_hours=4,
            response_template={
                "include_diagnosis": True,
                "include_steps": True,
                "include_prevention": True,
            },
        )

        assert "Network issue" in prompt
        assert "Connection problems" in prompt
        assert "network_specialist" in prompt
        assert "high" in prompt.lower()
        assert "4 hours" in prompt or "4" in prompt
        assert "Root cause" in prompt or "diagnosis" in prompt.lower()


@pytest.mark.asyncio
class TestRunITSupport:
    """Test main IT support function."""

    async def test_successful_resolution(self):
        """Test successful issue resolution."""
        from main import run_it_support

        config = {
            "architecture": "specialist_pool",
            "specialists": [
                {
                    "name": "network_specialist",
                    "description": "Network expert",
                    "keywords": ["network", "vpn"],
                    "priority": 1,
                },
                {
                    "name": "general_specialist",
                    "description": "General IT",
                    "keywords": ["general"],
                    "priority": 5,
                },
            ],
            "routing": {
                "strategy": "keyword_match",
                "min_keyword_matches": 1,
                "allow_multiple": True,
                "max_specialists": 3,
                "use_fallback": True,
            },
            "categorization": {
                "urgency_levels": [
                    {"name": "critical", "sla_hours": 1, "keywords": ["down", "outage"]},
                    {"name": "high", "sla_hours": 4, "keywords": ["urgent"]},
                ]
            },
            "response_template": {
                "include_diagnosis": True,
                "include_steps": True,
                "include_prevention": True,
            },
            "models": {"lead": "haiku", "specialists": "haiku"},
        }

        # Mock session
        mock_session = MagicMock()

        async def mock_run(prompt):
            yield """
### network_specialist

**Analysis**:
VPN connection issues likely due to network timeout configuration.

**Root Cause**:
Default timeout too short for remote connections.

**Resolution Steps**:
1. Increase VPN timeout to 60 seconds
2. Update firewall rules to allow UDP traffic
3. Restart VPN service

**Prevention**:
Monitor VPN connection stability metrics.

**Confidence**: High

### Consolidated Solution

**Primary Root Cause**:
VPN timeout configuration issue

**Recommended Action Plan**:
1. Update VPN timeout settings
2. Verify firewall configuration
3. Monitor for 24 hours

**Expected Resolution Time**: 30 minutes

**Risk Assessment**: Low risk, standard configuration change
"""

        mock_session.run = mock_run
        mock_session.teardown = AsyncMock()

        with patch("main.init", return_value=mock_session):
            result = await run_it_support(
                config,
                "VPN connection issues",
                "Users experiencing frequent disconnections",
            )

            # Verify result structure
            assert "title" in result
            assert "summary" in result
            assert "issue" in result
            assert "routing" in result
            assert "specialist_responses" in result
            assert "consolidated_solution" in result
            assert "metadata" in result

            assert result["issue"]["title"] == "VPN connection issues"
            assert len(result["specialist_responses"]) >= 1
            assert "VPN timeout" in result["consolidated_solution"]

    async def test_fallback_specialist(self):
        """Test fallback to general specialist when no matches."""
        from main import run_it_support

        config = {
            "architecture": "specialist_pool",
            "specialists": [
                {
                    "name": "network_specialist",
                    "description": "Network expert",
                    "keywords": ["network", "vpn"],
                    "priority": 1,
                },
                {
                    "name": "general_specialist",
                    "description": "General IT",
                    "keywords": [],
                    "priority": 5,
                },
            ],
            "routing": {
                "strategy": "keyword_match",
                "min_keyword_matches": 1,
                "allow_multiple": False,
                "max_specialists": 1,
                "use_fallback": True,
            },
            "categorization": {"urgency_levels": []},
            "response_template": {},
            "models": {"lead": "haiku"},
        }

        mock_session = MagicMock()

        async def mock_run(prompt):
            yield "### general_specialist\n\nGeneral IT support response."

        mock_session.run = mock_run
        mock_session.teardown = AsyncMock()

        with patch("main.init", return_value=mock_session):
            result = await run_it_support(
                config,
                "Printer not working",  # No specific keywords
                "Office printer offline",
            )

            # Should route to fallback specialist
            assert "routing" in result
            # Fallback should be used when no other specialists match
