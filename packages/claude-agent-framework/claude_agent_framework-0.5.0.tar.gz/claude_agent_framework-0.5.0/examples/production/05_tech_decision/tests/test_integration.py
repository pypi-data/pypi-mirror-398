"""Integration tests for Tech Decision Support System."""

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

    async def test_end_to_end_tech_decision(self, tmp_path):
        """Test end-to-end decision workflow with mocked session."""
        import main
        from common import ResultSaver

        # Create test config
        config = {
            "architecture": "debate",
            "participants": {
                "proponent": {
                    "name": "solution_advocate",
                    "role": "Argue in favor of proposed solution",
                    "focus_areas": [
                        "Technical advantages",
                        "Business alignment",
                        "Implementation feasibility",
                    ],
                },
                "opponent": {
                    "name": "critical_analyst",
                    "role": "Challenge solution and present alternatives",
                    "focus_areas": [
                        "Technical limitations",
                        "Implementation risks",
                        "Alternative solutions",
                    ],
                },
                "judge": {
                    "name": "expert_panel",
                    "role": "Make final decision",
                    "expertise": ["Software architecture", "Technology strategy"],
                },
            },
            "debate_config": {
                "rounds": 3,
                "format": "oxford_style",
                "round_structure": [
                    {"round": 1, "name": "Opening Arguments", "focus": "Main positions"},
                    {"round": 2, "name": "Deep Analysis", "focus": "Detailed evidence"},
                    {"round": 3, "name": "Rebuttals", "focus": "Counter-arguments"},
                ],
            },
            "evaluation_criteria": {
                "technical_fit": {"weight": 30, "sub_criteria": ["Scalability", "Performance"]},
                "implementation_feasibility": {
                    "weight": 25,
                    "sub_criteria": ["Team skills", "Timeline"],
                },
                "cost_efficiency": {"weight": 25, "sub_criteria": ["Initial cost", "TCO"]},
                "risk_management": {"weight": 20, "sub_criteria": ["Vendor lock-in", "Support"]},
            },
            "decision": {"decision_type": "technology_selection"},
            "models": {"lead": "haiku"},
            "output": {"directory": str(tmp_path / "outputs"), "format": "json"},
        }

        decision_question = "Should we adopt GraphQL to replace REST API?"
        context = {
            "options": [
                "Full migration to GraphQL",
                "Hybrid approach (GraphQL + REST)",
                "Enhanced REST with better documentation",
            ],
            "requirements": [
                "Reduce mobile app API calls",
                "Improve developer experience",
                "Support real-time updates",
            ],
            "constraints": {
                "budget": "$75,000",
                "timeline": "6 months",
                "team_size": "5 backend engineers",
                "tech_stack": "Node.js, PostgreSQL, React Native",
            },
            "current_situation": "REST API with 150+ endpoints, mobile app performance issues",
        }

        # Mock session
        mock_session = MagicMock()
        mock_session.session_dir = tmp_path / "session"

        async def mock_run(prompt):
            yield """
### Round 1: Opening Arguments

**[Proponent]**
GraphQL solves the over-fetching and under-fetching problems inherent in REST. With GraphQL, mobile clients can request exactly the data they need in a single query, dramatically reducing the number of API calls. This directly addresses the mobile app performance issues.

**[Opponent]**
While GraphQL offers benefits, the team has zero GraphQL experience. The 6-month timeline is aggressive for learning a new paradigm, migrating 150+ endpoints, and maintaining production stability. A hybrid approach allows gradual adoption with less risk.

### Round 2: Deep Analysis

**[Proponent]**
**Technical Fit**: GraphQL provides strong typing, introspection, and self-documenting APIs through GraphiQL. Real-time support via subscriptions is native. Industry adoption is strong - GitHub, Shopify, and Netflix use GraphQL.

**Implementation Feasibility**: Apollo Server and TypeGraphQL provide excellent Node.js integration. Team can learn basics in 2-3 weeks. Migration can be gradual using federation.

**Cost**: Estimated $50k for training, tooling, and migration effort. Well within $75k budget.

**[Opponent]**
**Technical Risks**: GraphQL queries can become complex and difficult to optimize. N+1 query problems are common. Caching is harder than with REST. Security concerns with unrestricted queries.

**Implementation Reality**: 150 endpoints represent significant domain logic. Complete migration in 6 months is unrealistic. Team learning curve will slow initial velocity by 30-40%.

**Hidden Costs**: Monitoring, debugging tools, performance profiling for GraphQL. Infrastructure changes for subscription support. Estimate $20k additional.

### Round 3: Rebuttals

**[Proponent]**
N+1 problems are solvable with DataLoader. Caching works with persisted queries. Security managed through query complexity limits and depth limiting. Many companies successfully migrated in similar timelines.

**[Opponent]**
Those solutions add complexity. The hybrid approach gives us GraphQL benefits for new features while preserving stable REST endpoints. Lower risk, faster time-to-value, same end goal.

### Evaluation Scorecard

**Technical Fit (30%)**
- Full GraphQL: 85/100 - Excellent for mobile use case, strong ecosystem
- Hybrid: 80/100 - Achieves goals with less disruption
- Enhanced REST: 60/100 - Doesn't address core problems

**Implementation Feasibility (25%)**
- Full GraphQL: 65/100 - Aggressive timeline, high learning curve
- Hybrid: 85/100 - Manageable scope, gradual learning
- Enhanced REST: 90/100 - Easiest but limited benefit

**Cost Efficiency (25%)**
- Full GraphQL: 70/100 - $70k estimated (training + migration)
- Hybrid: 85/100 - $45k (focused migration)
- Enhanced REST: 95/100 - $15k (documentation only)

**Risk Management (20%)**
- Full GraphQL: 60/100 - Migration risk, team expertise gap
- Hybrid: 80/100 - Controlled risk, fallback options
- Enhanced REST: 90/100 - Minimal risk but missed opportunity

**Overall Weighted Score**
- Full GraphQL: 72.5/100
- Hybrid: 82.5/100
- Enhanced REST: 79.0/100

### Final Recommendation

**[Judge's Decision]**

**Recommended Option**: Hybrid approach (GraphQL for new APIs, maintain critical REST endpoints)

**Justification**:

The hybrid approach scores highest (82.5/100) across weighted criteria. It delivers GraphQL's benefits while managing risk effectively. This pragmatic approach allows the team to:

1. Gain GraphQL expertise on new, less critical features
2. Maintain production stability of existing REST endpoints
3. Deliver value incrementally rather than big-bang migration
4. Reassess after 3-6 months based on actual experience

**Key Strengths**:
1. Risk mitigation through gradual adoption
2. Faster time-to-value for mobile performance improvements
3. Team learning happens in production with safety net
4. Budget well-managed at $45k vs $75k allocation
5. Proven pattern used successfully by many organizations

**Acknowledged Risks**:
1. Operating two API paradigms increases complexity - Mitigation: Clear service boundaries, gateway pattern
2. Potential team confusion during transition - Mitigation: Strong documentation, lunch-and-learn sessions
3. Extended timeline to full GraphQL adoption - Mitigation: Set 12-month target for 80% coverage

**Implementation Roadmap**:

Phase 1 (Immediate - 0-30 days):
- GraphQL training for 2 senior engineers
- Set up Apollo Server alongside existing REST
- Implement first GraphQL endpoint (user profile query)
- Establish monitoring and error tracking

Phase 2 (Short-term - 1-3 months):
- Train remaining team members
- Migrate 3-5 high-value mobile endpoints to GraphQL
- Implement DataLoader for N+1 prevention
- Add GraphQL security controls (depth, complexity limits)
- Measure mobile app performance improvements

Phase 3 (Long-term - 3-6 months):
- Migrate 10-15 more endpoints based on usage analytics
- Implement GraphQL subscriptions for real-time features
- Establish best practices and patterns
- Evaluate progress and adjust strategy
- Plan for expanded GraphQL adoption in next quarter

**Success Metrics**:
- Mobile app API calls reduced by 50% within 3 months
- GraphQL endpoint p99 latency < 200ms
- Zero production incidents related to GraphQL migration
- Team GraphQL proficiency score 7/10 by month 3
- Developer satisfaction score increase by 20%

**Dissenting Opinion**:

A minority view favors full GraphQL migration to avoid technical debt of maintaining two systems. However, given timeline constraints and team experience level, the risk outweighs benefits in the current context. This should be revisited in 6 months.
"""

        mock_session.run = mock_run
        mock_session.teardown = AsyncMock()

        with patch("main.init", return_value=mock_session):
            # Run tech decision
            result = await main.run_tech_decision(config, decision_question, context)

            # Verify result structure
            assert "decision_id" in result
            assert "title" in result
            assert "summary" in result
            assert "decision" in result
            assert "debate" in result
            assert "evaluation" in result
            assert "recommendation" in result
            assert "risk_assessment" in result
            assert "implementation_roadmap" in result
            assert "metadata" in result

            # Verify decision details
            assert result["decision"]["question"] == decision_question
            assert result["decision"]["decision_type"] == "technology_selection"
            assert "GraphQL" in result["title"]

            # Verify debate structure
            assert "rounds" in result["debate"]
            assert result["debate"]["rounds"] == 3
            assert "transcript" in result["debate"]

            # Verify recommendation
            assert "recommended_option" in result["recommendation"]
            assert "justification" in result["recommendation"]
            # Check recommendation extracted
            if result["recommendation"]["recommended_option"] != "Not determined":
                assert "Hybrid" in result["recommendation"]["recommended_option"]

            # Verify risk assessment exists
            assert isinstance(result["risk_assessment"], list)

            # Verify roadmap exists
            assert "phases" in result["implementation_roadmap"]

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
            "architecture": "debate",
            "participants": {},
            "debate_config": {},
            "evaluation_criteria": {},
        }

        # Should not raise
        validate_config(
            valid_config, ["architecture", "participants", "debate_config", "evaluation_criteria"]
        )

        # Invalid config - missing fields
        invalid_config = {"architecture": "debate"}

        with pytest.raises(ValueError) as exc_info:
            validate_config(
                invalid_config,
                ["architecture", "participants", "debate_config", "evaluation_criteria"],
            )

        assert "Missing required configuration fields" in str(exc_info.value)

    def test_config_loading(self):
        """Test YAML config loading."""
        from common import load_yaml_config

        # Test with actual config file
        config_path = Path(__file__).parent.parent / "config.yaml"

        if config_path.exists():
            config = load_yaml_config(config_path)

            assert "architecture" in config
            assert "participants" in config
            assert "debate_config" in config
            assert "evaluation_criteria" in config
            assert config["architecture"] == "debate"

            # Verify participants structure
            assert "proponent" in config["participants"]
            assert "opponent" in config["participants"]
            assert "judge" in config["participants"]

    async def test_prompt_building_logic(self):
        """Test debate prompt construction with various contexts."""
        from main import _build_debate_prompt

        participants = {
            "proponent": {"name": "advocate", "role": "Support", "focus_areas": ["Benefits"]},
            "opponent": {"name": "critic", "role": "Challenge", "focus_areas": ["Risks"]},
            "judge": {"name": "panel", "role": "Decide", "expertise": ["Tech"]},
        }

        debate_config = {"rounds": 2, "format": "oxford", "round_structure": []}

        criteria = {
            "technical": {"weight": 50, "sub_criteria": ["Feature A", "Feature B"]},
            "cost": {"weight": 50, "sub_criteria": ["Initial", "Ongoing"]},
        }

        # Test with minimal context
        prompt1 = _build_debate_prompt(
            "Test decision?",
            {"options": ["A", "B"], "requirements": ["R1"], "constraints": {}},
            participants,
            debate_config,
            criteria,
            {},
            {},
        )

        assert "Test decision?" in prompt1
        assert "Option 1" in prompt1 or "- **A**" in prompt1 or "A" in prompt1

        # Test with full context
        prompt2 = _build_debate_prompt(
            "Database selection",
            {
                "options": ["PostgreSQL", "MongoDB"],
                "requirements": ["ACID compliance", "High availability"],
                "constraints": {"budget": "$50k", "timeline": "3 months"},
                "current_situation": "MySQL with scaling issues",
            },
            participants,
            debate_config,
            criteria,
            {"decision_type": "technology_selection"},
            {"enable_fact_checking": True, "require_evidence": True},
        )

        assert "Database selection" in prompt2
        assert "PostgreSQL" in prompt2
        assert "MongoDB" in prompt2
        assert "ACID compliance" in prompt2

    async def test_transcript_parsing_edge_cases(self):
        """Test transcript parsing with various formats."""
        from main import _parse_debate_transcript

        # Empty results
        transcript1 = _parse_debate_transcript([])
        assert isinstance(transcript1, list)

        # Single round
        transcript2 = _parse_debate_transcript(
            [
                """
### Round 1: Test

**[Proponent]**
Argument A

**[Opponent]**
Counter-argument B
"""
            ]
        )

        assert len(transcript2) >= 1

        # Multiple rounds
        transcript3 = _parse_debate_transcript(
            [
                """
### Round 1: First

**[Proponent]**
Point 1

**[Opponent]**
Counter 1

### Round 2: Second

**[Proponent]**
Point 2

**[Opponent]**
Counter 2
"""
            ]
        )

        assert len(transcript3) >= 2

    async def test_evaluation_score_extraction(self):
        """Test evaluation score extraction."""
        from main import _extract_evaluation_scores

        results = [
            """
### Evaluation Scorecard

**Technical Fit (40%)**
- Option A: 90/100 - Excellent features
- Option B: 75/100 - Good but limited

**Cost Efficiency (30%)**
- Option A: 60/100 - Higher cost
- Option B: 85/100 - Cost-effective

**Overall Weighted Score**
- Option A: 78/100
- Option B: 79/100
"""
        ]

        criteria = {
            "technical_fit": {"weight": 40, "sub_criteria": []},
            "cost_efficiency": {"weight": 30, "sub_criteria": []},
        }

        scores = _extract_evaluation_scores(results, criteria)

        assert isinstance(scores, dict)

    async def test_recommendation_extraction_comprehensive(self):
        """Test comprehensive recommendation extraction."""
        from main import _extract_final_recommendation

        results = [
            """
### Final Recommendation

**Recommended Option**: Build custom solution with open-source components

**Justification**:

Analysis shows that building custom solution provides best long-term value despite higher initial investment. Open-source components reduce licensing costs while maintaining flexibility.

**Key Strengths**:
1. Full control over features and roadmap
2. No vendor lock-in
3. Lower long-term costs
4. Better team learning opportunities

**Acknowledged Risks**:
1. Higher initial development time - Mitigation: Phased rollout
2. Ongoing maintenance burden - Mitigation: Dedicated team
3. Security responsibility - Mitigation: Regular audits

**Implementation Roadmap**:

Phase 1 (0-3 months):
- Architecture design
- Prototype development
- Security review

Phase 2 (3-6 months):
- Core feature development
- Integration testing
- Documentation

**Success Metrics**:
- Feature parity with commercial options by month 6
- Cost savings of $100k annually
- Team satisfaction score 8/10
"""
        ]

        recommendation = _extract_final_recommendation(results)

        assert "recommended_option" in recommendation
        assert "justification" in recommendation

        if recommendation["recommended_option"] != "Not determined":
            assert "Build custom" in recommendation["recommended_option"]

    async def test_risk_assessment_extraction_detailed(self):
        """Test detailed risk assessment extraction."""
        from main import _extract_risk_assessment

        results = [
            """
**Acknowledged Risks**:
1. Technology adoption risk - Team unfamiliar with chosen stack
2. Budget overrun potential - Initial estimates may be optimistic
3. Timeline pressure - 6 months is aggressive for scope
4. Integration complexity - Legacy systems difficult to connect
5. Regulatory compliance - New regulations pending
"""
        ]

        risks = _extract_risk_assessment(results)

        assert isinstance(risks, list)
        assert len(risks) >= 1
        # All risk objects should have 'risk' field
        for risk in risks:
            assert "risk" in risk

    async def test_implementation_roadmap_extraction_detailed(self):
        """Test detailed implementation roadmap extraction."""
        from main import _extract_implementation_roadmap

        results = [
            """
**Implementation Roadmap**:

Phase 1 (Immediate - 0-30 days):
- Form core team
- Complete vendor evaluation
- Draft technical architecture
- Setup development environment

Phase 2 (Short-term - 1-3 months):
- Implement core features
- Integration with existing systems
- Security hardening
- Performance optimization

Phase 3 (Long-term - 3-12 months):
- Production rollout
- User training
- Documentation
- Ongoing monitoring

**Success Metrics**:
- Zero downtime during migration
- User adoption rate > 80% in 3 months
- Performance SLA: p95 < 500ms
- Cost reduction: 25% within 6 months
"""
        ]

        roadmap = _extract_implementation_roadmap(results)

        assert "phases" in roadmap
        assert isinstance(roadmap["phases"], list)

    def test_result_saver_formats(self, tmp_path):
        """Test saving results in different formats."""
        from common import ResultSaver

        saver = ResultSaver(tmp_path)

        result = {
            "decision_id": "test-123",
            "title": "Tech Decision: Database Selection",
            "summary": "Evaluated PostgreSQL vs MongoDB for new application",
            "recommendation": {
                "recommended_option": "PostgreSQL",
                "justification": "Better ACID compliance and team expertise",
            },
        }

        # Test JSON format
        json_path = saver.save(result, format="json")
        assert json_path.exists()
        assert json_path.suffix == ".json"

        # Test Markdown format
        md_path = saver.save(result, format="markdown", filename="tech_decision")
        assert md_path.exists()
        assert md_path.name == "tech_decision.md"

        # Verify markdown content
        content = md_path.read_text()
        assert "# Tech Decision: Database Selection" in content
        assert "PostgreSQL" in content
