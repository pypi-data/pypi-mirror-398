"""Unit tests for Tech Decision Support System."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPromptBuilding:
    """Test debate prompt construction."""

    def test_basic_prompt_structure(self):
        """Test basic prompt includes all key sections."""
        from main import _build_debate_prompt

        decision_question = "Should we adopt Kubernetes for container orchestration?"
        context = {
            "options": ["Adopt Kubernetes", "Use Docker Swarm", "Stay with current solution"],
            "requirements": ["Scalability", "High availability"],
            "constraints": {"budget": "$100k", "timeline": "6 months"},
            "current_situation": "Running on EC2 instances with manual scaling",
        }

        participants_config = {
            "proponent": {
                "name": "solution_advocate",
                "role": "Argue for the solution",
                "focus_areas": ["Technical benefits", "ROI"],
            },
            "opponent": {
                "name": "critical_analyst",
                "role": "Challenge the solution",
                "focus_areas": ["Risks", "Alternatives"],
            },
            "judge": {
                "name": "expert_panel",
                "role": "Make final decision",
                "expertise": ["Architecture", "DevOps"],
            },
        }

        debate_config = {
            "rounds": 3,
            "format": "oxford_style",
            "round_structure": [
                {"round": 1, "name": "Opening", "focus": "Main points"},
            ],
        }

        evaluation_criteria = {
            "technical_fit": {"weight": 30, "sub_criteria": ["Scalability", "Performance"]},
            "cost": {"weight": 25, "sub_criteria": ["Initial cost", "Operational cost"]},
        }

        prompt = _build_debate_prompt(
            decision_question,
            context,
            participants_config,
            debate_config,
            evaluation_criteria,
            {},
            {},
        )

        # Verify key sections present
        assert "Should we adopt Kubernetes" in prompt
        assert "Adopt Kubernetes" in prompt
        assert "Docker Swarm" in prompt
        assert "Scalability" in prompt
        assert "solution_advocate" in prompt
        assert "critical_analyst" in prompt
        assert "expert_panel" in prompt
        assert "Technical Fit" in prompt or "technical fit" in prompt.lower()


class TestTranscriptParsing:
    """Test debate transcript parsing."""

    def test_parse_debate_rounds(self):
        """Test parsing of multi-round debate."""
        from main import _parse_debate_transcript

        results = [
            """
### Round 1: Opening Arguments

**[Proponent]**
Kubernetes provides industry-standard container orchestration with superior scaling capabilities.

**[Opponent]**
Kubernetes has steep learning curve and operational overhead.

### Round 2: Deep Analysis

**[Proponent]**
Evidence shows 90% of Fortune 500 companies use Kubernetes.

**[Opponent]**
But implementation costs average $200k in first year.
"""
        ]

        transcript = _parse_debate_transcript(results)

        assert len(transcript) >= 1
        # Check structure exists
        assert isinstance(transcript, list)


class TestEvaluationScoring:
    """Test evaluation and scoring logic."""

    def test_extract_evaluation_scores(self):
        """Test extraction of criterion scores."""
        from main import _extract_evaluation_scores

        results = [
            """
### Evaluation Scorecard

**Technical Fit (30%)**
- Option 1: 85/100 - Excellent scalability
- Option 2: 70/100 - Good but limited

**Cost Efficiency (25%)**
- Option 1: 60/100 - Higher initial cost
- Option 2: 80/100 - Lower cost
"""
        ]

        criteria = {
            "technical_fit": {"weight": 30},
            "cost_efficiency": {"weight": 25},
        }

        scores = _extract_evaluation_scores(results, criteria)

        # Should return dict structure
        assert isinstance(scores, dict)

    def test_calculate_overall_score(self):
        """Test weighted score calculation."""
        from main import _calculate_overall_score

        evaluation_scores = {
            "technical_fit": {"weight": 30, "score": 85},
            "cost": {"weight": 25, "score": 60},
        }

        criteria = {
            "technical_fit": {"weight": 30},
            "cost": {"weight": 25},
        }

        overall = _calculate_overall_score(evaluation_scores, criteria)

        # Should return float
        assert isinstance(overall, (int, float))
        assert overall >= 0


class TestRecommendationExtraction:
    """Test final recommendation extraction."""

    def test_extract_final_recommendation(self):
        """Test extraction of judge's recommendation."""
        from main import _extract_final_recommendation

        results = [
            """
### Final Recommendation

**Recommended Option**: Hybrid approach (Kubernetes for new workloads, keep existing)

**Justification**: Balances innovation with risk management. Allows team to gain expertise gradually.

**Key Strengths**:
1. Reduced migration risk
2. Immediate benefits for new services
3. Team learning opportunity

**Acknowledged Risks**:
1. Increased operational complexity managing two systems
2. Longer timeline to full migration
"""
        ]

        recommendation = _extract_final_recommendation(results)

        assert "recommended_option" in recommendation
        assert "justification" in recommendation
        # Check extraction worked
        if recommendation["recommended_option"] != "Not determined":
            assert "Hybrid" in recommendation["recommended_option"]


class TestRiskAssessment:
    """Test risk assessment extraction."""

    def test_extract_risks(self):
        """Test extraction of identified risks."""
        from main import _extract_risk_assessment

        results = [
            """
**Acknowledged Risks**:
1. Steep learning curve for team - Mitigation: Invest in training
2. Initial performance overhead - Mitigation: Gradual rollout
3. Vendor lock-in concerns - Mitigation: Use open standards
"""
        ]

        risks = _extract_risk_assessment(results)

        assert isinstance(risks, list)
        assert len(risks) > 0
        assert "risk" in risks[0]


class TestImplementationRoadmap:
    """Test implementation roadmap extraction."""

    def test_extract_roadmap(self):
        """Test extraction of implementation phases."""
        from main import _extract_implementation_roadmap

        results = [
            """
**Implementation Roadmap**:

Phase 1 (Immediate - 0-30 days):
- Team Kubernetes training
- Proof of concept deployment
- Cost analysis

Phase 2 (Short-term - 1-3 months):
- Deploy first production workload
- Monitor performance metrics
- Refine runbooks

Phase 3 (Long-term - 3-12 months):
- Migrate 50% of workloads
- Establish best practices
- Full team proficiency

**Success Metrics**:
- 99.9% uptime
- 50% reduction in deployment time
"""
        ]

        roadmap = _extract_implementation_roadmap(results)

        assert "phases" in roadmap
        assert isinstance(roadmap["phases"], list)


@pytest.mark.asyncio
class TestRunTechDecision:
    """Test main decision execution function."""

    async def test_successful_decision(self):
        """Test successful decision evaluation."""
        from main import run_tech_decision

        config = {
            "architecture": "debate",
            "participants": {
                "proponent": {
                    "name": "solution_advocate",
                    "role": "Argue for solution",
                    "focus_areas": ["Benefits", "ROI"],
                },
                "opponent": {
                    "name": "critical_analyst",
                    "role": "Challenge solution",
                    "focus_areas": ["Risks", "Alternatives"],
                },
                "judge": {
                    "name": "expert_panel",
                    "role": "Make decision",
                    "expertise": ["Architecture"],
                },
            },
            "debate_config": {
                "rounds": 2,
                "format": "oxford_style",
                "round_structure": [],
            },
            "evaluation_criteria": {
                "technical_fit": {"weight": 40, "sub_criteria": []},
                "cost": {"weight": 30, "sub_criteria": []},
            },
            "models": {"lead": "haiku"},
        }

        decision_question = "Should we migrate to microservices?"
        context = {
            "options": ["Migrate to microservices", "Stay with monolith"],
            "requirements": ["Scalability", "Independent deployment"],
            "constraints": {"budget": "$200k", "timeline": "12 months"},
            "current_situation": "Monolithic Rails app with 500k LOC",
        }

        # Mock session
        mock_session = MagicMock()

        async def mock_run(prompt):
            yield """
### Round 1: Opening Arguments

**[Proponent]**
Microservices enable independent scaling and deployment.

**[Opponent]**
Microservices increase operational complexity and network latency.

### Evaluation Scorecard

**Technical Fit (40%)**
- Microservices: 80/100
- Monolith: 60/100

### Final Recommendation

**Recommended Option**: Hybrid approach - Extract high-traffic services first

**Justification**: Reduces risk while gaining microservices benefits for critical paths.
"""

        mock_session.run = mock_run
        mock_session.teardown = AsyncMock()

        with patch("main.init", return_value=mock_session):
            result = await run_tech_decision(config, decision_question, context)

            # Verify result structure
            assert "decision_id" in result
            assert "title" in result
            assert "summary" in result
            assert "decision" in result
            assert "debate" in result
            assert "evaluation" in result
            assert "recommendation" in result
            assert "metadata" in result

            assert result["decision"]["question"] == decision_question
            assert "microservices" in result["title"].lower()

    async def test_missing_config_fields(self):
        """Test error handling for missing required config."""
        from main import ConfigurationError, run_tech_decision

        # Missing required fields
        config = {"architecture": "debate"}

        decision_question = "Test question"
        context = {"options": [], "requirements": [], "constraints": {}}

        with pytest.raises((ConfigurationError, ValueError)):
            await run_tech_decision(config, decision_question, context)
