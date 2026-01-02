# Tech Decision Support System Example

A production-ready technical decision-making support system using the **Debate** architecture from Claude Agent Framework. Provides structured deliberation for evaluating technology choices, architecture changes, build-vs-buy decisions, and vendor selection.

## Overview

This example demonstrates how to build an enterprise-grade tech decision platform that:

- Conducts structured debates with proponents and opponents
- Evaluates decisions across multiple weighted criteria
- Provides evidence-based recommendations with comprehensive justification
- Generates detailed implementation roadmaps with phased action plans
- Identifies risks and mitigation strategies
- Produces executive summaries for stakeholder review

## Architecture: Debate

The Debate architecture is ideal for technical decisions requiring balanced evaluation:

```
Decision Question + Context
    ↓
┌─────────────┬─────────────┬─────────────┐
│  Proponent  │  Opponent   │  Moderator  │
│  (Advocate) │  (Critic)   │  (Guide)    │
└─────────────┴─────────────┴─────────────┘
    ↓
Round 1: Opening Arguments (Pro vs Con)
    ↓
Round 2: Deep Analysis (Evidence-based)
    ↓
Round 3: Rebuttals (Counter-arguments)
    ↓
┌─────────────────────────┐
│  Expert Judge Panel     │
│  Weighted Evaluation    │
│  Final Recommendation   │
└─────────────────────────┘
```

**Key Characteristics**:
- Structured multi-round deliberation
- Pro and con perspectives ensure balanced analysis
- Evidence-based arguments with fact-checking
- Weighted criteria scoring (technical, cost, risk, business)
- Expert panel judgment with dissenting opinions

## Use Case: Technology Selection

### Real-World Scenario

**Problem**: Engineering teams face critical technology decisions daily - choosing databases, selecting frameworks, evaluating cloud providers, deciding build-vs-buy. These decisions have long-term consequences but are often made hastily or based on incomplete analysis.

**Solution**: This system provides:
1. Structured debate format ensuring all angles are explored
2. Weighted evaluation across technical, cost, risk, and business criteria
3. Evidence-based arguments with data and industry research
4. Final recommendation with implementation roadmap and risk mitigation

### Common Decision Types

| Decision Type | Example | Key Criteria |
|--------------|---------|--------------|
| **Technology Selection** | React vs Vue, PostgreSQL vs MongoDB | Technical fit, learning curve, ecosystem |
| **Architecture Change** | Monolith to microservices | Scalability, complexity, migration cost |
| **Build vs Buy** | Custom auth vs Auth0 | Development time, customization, TCO |
| **Vendor Selection** | AWS vs Azure vs GCP | Features, pricing, lock-in risk |

## Installation

```bash
# Install Claude Agent Framework
pip install claude-agent-framework

# Or install from source
cd claude-agent-framework
pip install -e .
```

## Configuration

The `config.yaml` file defines debate structure, participants, and evaluation criteria:

```yaml
architecture: debate

# Debate participants
participants:
  proponent:
    name: "solution_advocate"
    role: "Make the strongest case for the proposed solution"
    focus_areas:
      - "Technical advantages and capabilities"
      - "Business alignment and ROI"
      - "Implementation feasibility"

  opponent:
    name: "critical_analyst"
    role: "Identify weaknesses and present alternatives"
    focus_areas:
      - "Technical limitations and drawbacks"
      - "Implementation risks and challenges"
      - "Alternative solutions comparison"

  judge:
    name: "expert_panel"
    expertise:
      - "Software architecture"
      - "Technology strategy"
      - "Risk management"

# Debate structure
debate_config:
  rounds: 3
  round_structure:
    - round: 1
      name: "Opening Arguments"
      focus: "Present main positions"
    - round: 2
      name: "Deep Analysis"
      focus: "Evidence-based evaluation"
    - round: 3
      name: "Rebuttals"
      focus: "Counter-arguments and strengthening"

# Weighted evaluation criteria
evaluation_criteria:
  technical_fit:
    weight: 30
    sub_criteria:
      - "Meets functional requirements"
      - "Scalability and performance"
      - "Security features"

  implementation_feasibility:
    weight: 25
    sub_criteria:
      - "Team skill availability"
      - "Learning curve"
      - "Migration complexity"

  cost_efficiency:
    weight: 25
    sub_criteria:
      - "Initial costs"
      - "Operational costs"
      - "Total Cost of Ownership (3-year)"

  risk_management:
    weight: 20
    sub_criteria:
      - "Vendor lock-in risk"
      - "Support and community"
      - "Migration/exit strategy"

# Model configuration
models:
  lead: "sonnet"       # Moderator
  proponent: "sonnet"  # Strong argumentation
  opponent: "sonnet"   # Critical analysis
  judge: "opus"        # Best judgment
```

## Usage

### Basic Usage

```python
import asyncio
from pathlib import Path
from main import run_tech_decision
from common import load_yaml_config

async def main():
    # Load configuration
    config = load_yaml_config(Path(__file__).parent / "config.yaml")

    # Define decision question
    decision_question = "Should we migrate from REST API to GraphQL?"

    # Provide decision context
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
        "current_situation": """
        REST API with 150+ endpoints. Mobile app makes 20+ API calls per screen.
        Team has REST experience but no GraphQL knowledge.
        Customer complaints about slow mobile performance.
        """,
    }

    # Run decision process
    result = await run_tech_decision(config, decision_question, context)

    # Access results
    print(f"Decision: {result['decision']['question']}")
    print(f"Recommendation: {result['recommendation']['recommended_option']}")
    print(f"Justification: {result['recommendation']['justification'][:200]}...")

    # Save result
    from common import ResultSaver
    saver = ResultSaver(config["output"]["directory"])
    output_path = saver.save(result, format="json")
    print(f"Full decision report saved to: {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Command-Line Usage

```bash
# Run with default config
python main.py

# Specify custom config
python main.py --config custom_config.yaml

# Change output format
python main.py --output-format markdown  # Options: json, markdown, pdf
```

## Example Output

### Input

```
Question: Should we adopt Kubernetes for container orchestration?

Context:
- Options: Kubernetes, Docker Swarm, AWS ECS
- Requirements: Auto-scaling, high availability, multi-region
- Constraints: $100k budget, 6-month timeline
- Current: EC2 instances with manual scaling
```

### Debate Excerpt

```markdown
### Round 1: Opening Arguments

**[Proponent - solution_advocate]**

Kubernetes is the industry-standard container orchestration platform with unmatched ecosystem support. It provides:

- Automatic scaling based on CPU/memory metrics or custom metrics
- Self-healing with automatic container restarts and health checks
- Multi-cloud portability avoiding vendor lock-in
- Vast ecosystem: Helm, Istio, Prometheus integration
- 80%+ of Fortune 500 companies use Kubernetes

The learning curve investment pays dividends in operational efficiency and team marketability.

**[Opponent - critical_analyst]**

While Kubernetes offers powerful capabilities, the proposal overlooks critical challenges:

- Steep learning curve: 3-6 months for team proficiency
- Operational complexity: Requires dedicated DevOps resources
- Overkill for current scale: Current workload could run on simpler solutions
- Budget concerns: Training, tooling, and consulting easily exceed $100k
- AWS ECS provides 80% of benefits with fraction of the complexity

The "everyone uses it" argument is bandwagon fallacy. Choose based on actual needs, not hype.

### Round 2: Deep Analysis

**[Proponent]**

**Technical Fit (30%): 95/100**
- Native support for all requirements: auto-scaling (HPA), multi-region (federation), high availability (replica sets)
- Declarative configuration with GitOps support
- Battle-tested at massive scale (Google runs 2 billion containers/week)

**Implementation Feasibility (25%): 70/100**
- Managed Kubernetes (EKS, GKE, AKS) reduces operational burden
- Team can start with managed control plane, gradually increase sophistication
- Strong hiring pool: K8s skills are highly available

**Cost (25%): 65/100**
- Higher initial investment: $40k training, $20k consulting, $15k tooling
- Long-term savings: 40% infrastructure cost reduction via bin packing
- 3-year TCO competitive with alternatives

**Risk (20%): 75/100**
- Mature technology (CNCF graduated project)
- Multi-cloud strategy eliminates vendor lock-in
- Large community and enterprise support options

**[Opponent]**

**Reality Check on Scores:**

**Technical Fit**: Overrated at 95. Missing context that current workload is 10 services on 20 instances. K8s designed for 100s of services. More appropriate score: 75.

**Implementation**: 70 is generous. Managed K8s still requires deep understanding of pods, services, ingress, RBAC, network policies. Real proficiency: 9-12 months. Score: 50.

**Cost**: Underestimating operational overhead. Need dedicated SRE ($150k/year), monitoring tools ($10k/year), training refresh. 3-year TCO actually higher. Score: 55.

**Alternative Proposal**: AWS ECS with Fargate
- Technical Fit: 85/100 - Meets all requirements, AWS-native integration
- Implementation: 90/100 - Team already knows Docker, 2-week ramp-up
- Cost: 80/100 - No control plane costs, pay per container
- Risk: 70/100 - AWS lock-in concern, but current architecture already AWS-dependent

### Evaluation Scorecard

**Technical Fit (30%)**
- Kubernetes: 85/100 - Excellent but overpowered for current scale
- Docker Swarm: 70/100 - Simpler but limited ecosystem
- AWS ECS: 82/100 - AWS-native, meets requirements

**Implementation Feasibility (25%)**
- Kubernetes: 60/100 - Steep curve, aggressive timeline
- Docker Swarm: 85/100 - Easier learning, faster deployment
- AWS ECS: 88/100 - Minimal learning, team AWS experience

**Cost Efficiency (25%)**
- Kubernetes: 65/100 - High initial, long-term savings
- Docker Swarm: 90/100 - Lowest cost option
- AWS ECS: 80/100 - Moderate cost, no control plane fees

**Risk Management (20%)**
- Kubernetes: 80/100 - Mature, portable, strong community
- Docker Swarm: 60/100 - Declining community, uncertain future
- AWS ECS: 72/100 - Vendor lock-in, but strong support

**Overall Weighted Score**
- Kubernetes: 72.5/100
- Docker Swarm: 76.3/100
- AWS ECS: 81.0/100

### Final Recommendation

**[Judge's Decision]**

**Recommended Option**: AWS ECS with Fargate (transitional), plan Kubernetes migration in 18-24 months

**Justification**:

The weighted evaluation (ECS: 81.0, Kubernetes: 72.5) combined with context analysis leads to a staged approach:

**Phase 1 (Now - 18 months): Adopt AWS ECS**
- Immediate value: Containerization benefits with minimal friction
- Team learns container orchestration concepts with familiar AWS tools
- Timeline and budget constraints met
- Risk mitigation: Production stability maintained

**Phase 2 (18-24 months): Kubernetes Migration**
- By then: Team has container orchestration experience
- By then: Application architecture evolved to warrant K8s complexity
- By then: Larger team and budget for proper K8s investment

**Key Strengths of This Approach**:
1. Pragmatic: Solves immediate needs without over-engineering
2. Educational: Team builds orchestration expertise incrementally
3. Financial: Stays within budget, defers major K8s investment
4. Strategic: Positions for multi-cloud future when business requires it
5. Low Risk: Proven technology with existing team expertise

**Acknowledged Risks**:
1. ECS-to-K8s migration cost in 18 months - Mitigation: Use K8s-compatible patterns (12-factor app), containerization already 80% of work
2. AWS vendor lock-in during ECS phase - Mitigation: Avoid ECS-specific features, use open standards (Docker, CloudFormation → Terraform)
3. Team may resist eventual K8s transition - Mitigation: Include K8s learning in professional development plans starting month 6

**Implementation Roadmap**:

Phase 1 (Immediate - 0-30 days):
- Create ECS cluster with Fargate launch type
- Containerize first low-risk service (internal dashboard)
- Set up CI/CD pipeline for container deployments
- Establish monitoring and logging (CloudWatch + Datadog)

Phase 2 (Short-term - 1-3 months):
- Migrate 5 core services to ECS
- Implement auto-scaling policies
- Set up multi-region deployment (us-east-1, us-west-2)
- Team training on container best practices

Phase 3 (Long-term - 3-18 months):
- Migrate remaining services
- Optimize container sizing and costs
- Evaluate service mesh (AWS App Mesh)
- Month 12: Begin K8s evaluation for 18-month transition

**Success Metrics**:
- Zero production incidents during migration
- 99.9% uptime maintained
- Deployment time reduced from 30min to 5min
- Infrastructure costs reduced 20% via better resource utilization
- Team satisfaction score: 8/10 on orchestration experience

**Dissenting Opinion**:

A minority view advocates for immediate Kubernetes adoption, arguing that the ECS-to-K8s migration creates duplicate work. However, given the team's current expertise level and timeline constraints, the risk of failed K8s implementation outweighs the efficiency argument. This position should be revisited if timeline extends to 12 months.
```

## Customization

### Adding Custom Decision Templates

Extend `config.yaml`:

```yaml
decision_templates:
  ml_framework_selection:
    description: "Choosing ML/AI framework"
    required_info:
      - "Use case (NLP, Computer Vision, etc.)"
      - "Team ML expertise"
      - "Deployment environment"
      - "Performance requirements"
      - "Model complexity"

  database_selection:
    description: "RDBMS vs NoSQL vs NewSQL"
    required_info:
      - "Data model characteristics"
      - "Transaction requirements (ACID?)"
      - "Scale projections (reads/writes per second)"
      - "Query patterns"
      - "Consistency requirements"
```

### Custom Evaluation Criteria

```yaml
evaluation_criteria:
  # For open-source library selection
  community_health:
    weight: 15
    sub_criteria:
      - "GitHub stars and forks"
      - "Recent commit activity"
      - "Issue resolution time"
      - "Number of contributors"
      - "Documentation quality"

  license_compliance:
    weight: 10
    sub_criteria:
      - "License type (MIT, Apache, GPL)"
      - "Commercial use restrictions"
      - "Patent grants"
      - "Attribution requirements"
```

### Advanced Debate Options

```yaml
advanced:
  enable_fact_checking: true       # Verify claims with WebSearch
  require_evidence: true            # Arguments must cite sources
  allow_expert_consultation: true  # Spawn domain experts for specific questions
  structured_scoring: true          # Use detailed rubrics
  generate_alternatives: true       # AI suggests additional options
  sensitivity_analysis: true        # Test decision robustness to assumption changes
```

## Testing

```bash
# Run all tests
pytest examples/production/05_tech_decision/tests/ -v

# Run unit tests only
pytest examples/production/05_tech_decision/tests/test_main.py -v

# Run integration tests
pytest examples/production/05_tech_decision/tests/test_integration.py -v

# Run with coverage
pytest examples/production/05_tech_decision/tests/ --cov=. --cov-report=html
```

## Performance Characteristics

| Metric | Value |
|--------|-------|
| Average debate time | 45-90 seconds |
| Debate rounds | 2-4 (configurable) |
| Cost per decision (Sonnet debate, Opus judge) | $0.50-1.50 |
| Cost per decision (Haiku debate, Sonnet judge) | $0.10-0.30 |
| Supported decision types | 4 templates + custom |

## Best Practices

### 1. Decision Framing

**Good Decision Question**:
> "Should we migrate our monolithic Rails application to microservices architecture for the customer-facing platform?"

Specific, scoped, actionable.

**Poor Decision Question**:
> "Should we use microservices?"

Too vague, missing context.

### 2. Context Completeness

Provide comprehensive context:
- **Current Situation**: What's the problem driving this decision?
- **Options**: 2-4 concrete alternatives (not 10)
- **Requirements**: Specific, measurable needs
- **Constraints**: Budget, timeline, team size, existing tech stack
- **Stakeholders**: Who's affected by this decision?

### 3. Criteria Weighting

Align weights with business priorities:

```yaml
# For early-stage startup (speed over perfection)
evaluation_criteria:
  time_to_market: {weight: 40}
  cost: {weight: 30}
  technical_fit: {weight: 20}
  risk: {weight: 10}

# For regulated enterprise (risk mitigation critical)
evaluation_criteria:
  compliance_and_security: {weight: 35}
  risk_management: {weight: 30}
  technical_fit: {weight: 20}
  cost: {weight: 15}
```

### 4. Model Selection Strategy

```yaml
# Budget-conscious (minimize cost)
models:
  lead: "haiku"
  proponent: "haiku"
  opponent: "haiku"
  judge: "sonnet"

# Balanced (quality + cost)
models:
  lead: "sonnet"
  proponent: "sonnet"
  opponent: "sonnet"
  judge: "opus"

# High-stakes decisions (maximum quality)
models:
  lead: "opus"
  proponent: "opus"
  opponent: "opus"
  judge: "opus"
```

### 5. Iterative Refinement

For complex decisions, run multiple debates with refined criteria:

1. **Round 1**: Initial debate with broad criteria → Identify top 2-3 options
2. **Round 2**: Focused debate on finalists with detailed criteria → Make final decision
3. **Round 3** (optional): Validate decision with sensitivity analysis (vary assumptions)

## Troubleshooting

### Issue: Debates are too superficial

**Symptoms**: Recommendations lack depth, justifications feel generic

**Solutions**:
1. Increase debate rounds to 4-5
2. Require evidence: `require_evidence: true`
3. Enable fact-checking: `enable_fact_checking: true`
4. Use Sonnet/Opus models instead of Haiku
5. Provide more detailed context and specific requirements

### Issue: Debates favor status quo

**Symptoms**: Always recommends "keep current solution" or incremental changes

**Solutions**:
1. Explicitly ask opponent to "challenge status quo bias"
2. Add evaluation criterion: "Innovation and competitive advantage"
3. Require proponent to argue for most ambitious option
4. Provide market trend data showing industry direction

### Issue: Unclear recommendation

**Symptoms**: Judge presents "it depends" or lists all options as viable

**Solutions**:
1. Tighten constraints (budget, timeline) to force prioritization
2. Require single recommendation (not "hybrid" by default)
3. Use Opus model for judge (better decision-making)
4. Increase weight differentials in criteria (clearer priorities)

## License

MIT License - See main repository for details

## Related Examples

- [Competitive Intelligence](../01_competitive_intelligence/) - Research architecture
- [PR Code Review](../02_pr_code_review/) - Pipeline architecture
- [Marketing Content](../03_marketing_content/) - Critic-Actor architecture
- [IT Support Platform](../04_it_support/) - Specialist Pool architecture

## Support

For issues and questions:
- GitHub Issues: https://github.com/anthropics/claude-agent-framework/issues
- Documentation: https://github.com/anthropics/claude-agent-framework/docs
