# IT Support Platform Example

A production-ready intelligent IT support issue routing and resolution system using the **Specialist Pool** architecture from Claude Agent Framework.

## Overview

This example demonstrates how to build an enterprise-grade IT support platform that:

- Automatically categorizes issue urgency based on keywords and SLA policies
- Intelligently routes issues to appropriate specialist agents (network, database, security, cloud, etc.)
- Leverages parallel specialist consultation for complex cross-domain issues
- Provides consolidated solutions with confidence levels and action plans
- Tracks metrics including resolution time, specialist utilization, and SLA compliance

## Architecture: Specialist Pool

The Specialist Pool architecture is ideal for scenarios requiring domain expertise routing:

```
User Issue
    ↓
Urgency Categorization (Critical/High/Medium/Low)
    ↓
Keyword-Based Routing
    ↓
┌─────────────┬─────────────┬─────────────┬─────────────┐
│  Network    │  Database   │  Security   │   Cloud     │ (Parallel)
│  Specialist │  Specialist │  Specialist │  Specialist │
└─────────────┴─────────────┴─────────────┴─────────────┘
    ↓
Consolidated Solution + Recommendation
```

**Key Characteristics**:
- Expert routing based on keyword matching
- Priority-based specialist selection
- Parallel specialist collaboration
- Fallback to general specialist when no matches
- SLA-aware urgency categorization

## Use Case: Enterprise IT Support

### Real-World Scenario

**Problem**: IT support teams handle hundreds of diverse issues daily - from network outages to database performance, security incidents to cloud infrastructure problems. Manual routing is slow and often misroutes issues to wrong specialists.

**Solution**: This system automatically:
1. Categorizes urgency (Critical: 1hr SLA, High: 4hr, Medium: 24hr, Low: 72hr)
2. Routes to 1-3 relevant specialists based on issue keywords
3. Collects parallel expert analyses
4. Consolidates into actionable solution with confidence levels

### Specialists Available

| Specialist | Keywords | Priority | Expertise |
|-----------|----------|----------|-----------|
| **Network** | network, vpn, firewall, dns, ip address, routing | 1 | Connectivity, VPN, firewalls |
| **Database** | database, sql, query, table, index, deadlock | 1 | SQL, performance, data integrity |
| **Security** | security, breach, vulnerability, authentication | 1 | Security incidents, access control |
| **Cloud** | cloud, aws, kubernetes, docker, scaling | 2 | Cloud infrastructure, containers |
| **Application** | application, error, crash, bug, timeout | 2 | Application code, runtime issues |
| **DevOps** | deployment, cicd, jenkins, pipeline, build | 3 | CI/CD, build systems |
| **General IT** | (fallback) | 5 | General technical support |

## Installation

```bash
# Install Claude Agent Framework
pip install claude-agent-framework

# Or install from source
cd claude-agent-framework
pip install -e .
```

## Configuration

The `config.yaml` file defines specialists, routing rules, and urgency categorization:

```yaml
architecture: specialist_pool

specialists:
  - name: "network_specialist"
    description: "Network infrastructure expert"
    keywords: ["network", "vpn", "firewall", "dns"]
    priority: 1  # Lower = higher priority

  - name: "database_specialist"
    keywords: ["database", "sql", "query"]
    priority: 1

routing:
  strategy: "keyword_match"
  min_keyword_matches: 1      # Minimum keyword matches to select specialist
  allow_multiple: true         # Allow multiple specialists per issue
  max_specialists: 3           # Maximum concurrent specialists
  use_fallback: true           # Use general specialist if no matches

categorization:
  urgency_levels:
    - name: "critical"
      sla_hours: 1
      keywords: ["down", "outage", "breach", "critical"]
    - name: "high"
      sla_hours: 4
      keywords: ["urgent", "production"]
    - name: "medium"
      sla_hours: 24
      keywords: ["bug", "issue"]
    - name: "low"
      sla_hours: 72
      keywords: ["request", "question"]

models:
  lead: "sonnet"              # Lead agent model
  specialists: "haiku"         # Specialist agents model (cost-efficient)
```

## Usage

### Basic Usage

```python
import asyncio
from pathlib import Path
from main import run_it_support
from common import load_yaml_config

async def main():
    # Load configuration
    config = load_yaml_config(Path(__file__).parent / "config.yaml")

    # Define IT issue
    issue_title = "VPN connection failing for remote users"
    issue_description = """
    Multiple remote employees report unable to connect to company VPN.
    Error: "Connection timeout after 30 seconds"
    Affected users: ~20 people
    Started: 2 hours ago
    """

    # Run IT support resolution
    result = await run_it_support(config, issue_title, issue_description)

    # Access results
    print(f"Urgency: {result['metadata']['urgency']}")
    print(f"SLA: {result['metadata']['sla_hours']} hours")
    print(f"Specialists: {result['routing']['specialist_names']}")
    print(f"\nConsolidated Solution:\n{result['consolidated_solution']}")

    # Save result
    from common import ResultSaver
    saver = ResultSaver(config["output"]["directory"])
    output_path = saver.save(result, format="json")
    print(f"\nSaved to: {output_path}")

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
Title: Database queries running extremely slow
Description: Customer dashboard loading takes 30+ seconds.
             Multiple users reporting timeout errors.
             Production database affected.
```

### Routing Decision

```
Urgency: HIGH (4-hour SLA)
Keywords matched: database, queries, slow, production
Selected specialists:
  - database_specialist (3 keyword matches, priority 1)
  - application_specialist (1 keyword match, priority 2)
```

### Consolidated Solution

```markdown
### database_specialist

**Analysis**: Database performance degradation due to missing indexes and inefficient queries.

**Root Cause**:
- Missing index on customer_orders.created_at column
- Full table scans on 10M+ row table
- No query optimization for dashboard endpoints

**Resolution Steps**:
1. Create composite index: `CREATE INDEX idx_orders_created_user ON customer_orders(created_at, user_id)`
2. Optimize query using EXPLAIN ANALYZE
3. Implement query result caching (Redis, 5min TTL)
4. Add database query performance monitoring

**Prevention**:
- Implement automated index recommendations
- Add query performance budgets to CI/CD
- Regular EXPLAIN analysis in code review

**Confidence**: High

---

### Consolidated Solution

**Primary Root Cause**: Missing database indexes causing full table scans

**Recommended Action Plan**:
1. **Immediate** (< 1hr): Create missing index on customer_orders table
2. **Short-term** (< 4hrs): Implement query result caching
3. **Long-term** (< 1 week): Add automated performance monitoring

**Expected Resolution Time**: 2-4 hours

**Risk Assessment**: Low risk - index creation is online operation

**Follow-up Actions**:
- Monitor query performance for 48 hours
- Review other slow queries for similar issues
- Update database maintenance runbook
```

## Customization

### Adding Custom Specialists

Add to `config.yaml`:

```yaml
specialists:
  - name: "mobile_app_specialist"
    description: "iOS and Android mobile app expert"
    keywords: ["mobile", "ios", "android", "app crash", "push notification"]
    priority: 2
    tools: ["WebSearch", "Read"]  # Optional: custom tool set
```

### Custom Routing Logic

Modify `main.py`:

```python
def _route_to_specialists(title, description, specialists_config, routing_config):
    """Custom routing with machine learning scoring."""
    # Your custom logic here
    # Example: Use embeddings for semantic matching
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')

    issue_embedding = model.encode(f"{title} {description}")

    specialist_scores = []
    for specialist in specialists_config:
        specialist_text = " ".join(specialist["keywords"])
        specialist_embedding = model.encode(specialist_text)
        similarity = cosine_similarity(issue_embedding, specialist_embedding)
        specialist_scores.append((specialist, similarity))

    # Return top-k specialists
    specialist_scores.sort(key=lambda x: x[1], reverse=True)
    return [s[0] for s in specialist_scores[:routing_config["max_specialists"]]]
```

### Custom Urgency Rules

```yaml
categorization:
  urgency_levels:
    - name: "p0_incident"
      sla_hours: 0.5           # 30 minutes
      keywords: ["p0", "sev0", "complete outage"]
      auto_escalate: true
      notify: ["on-call-engineer", "engineering-manager"]

    - name: "critical"
      sla_hours: 1
      keywords: ["down", "breach", "data loss"]
      auto_escalate: true
```

## Advanced Features

### 1. Multi-Specialist Coordination

For complex cross-domain issues:

```python
routing_config = {
    "strategy": "keyword_match",
    "allow_multiple": True,     # Enable multiple specialists
    "max_specialists": 5,       # Allow up to 5 specialists
    "require_consensus": True,  # Require agreement on solution
    "consensus_threshold": 0.75 # 75% agreement required
}
```

### 2. Historical Learning

Track specialist performance:

```python
result = await run_it_support(config, issue_title, issue_description)

# Track specialist effectiveness
specialist_metrics = {
    "specialist": "database_specialist",
    "issue_id": result["metadata"]["issue_id"],
    "confidence": "High",
    "resolution_time": result["metadata"]["actual_resolution_hours"],
    "sla_met": result["metadata"]["sla_met"]
}

# Store for future routing optimization
tracker.record_specialist_performance(specialist_metrics)
```

### 3. Escalation Rules

```python
def _should_escalate(result):
    """Determine if issue needs escalation."""
    if result["metadata"]["urgency"] == "critical":
        if not result["metadata"].get("sla_met", True):
            return True, "SLA breach on critical issue"

    if all(r["confidence"] == "Low" for r in result["specialist_responses"]):
        return True, "All specialists have low confidence"

    return False, None

should_escalate, reason = _should_escalate(result)
if should_escalate:
    await escalate_to_senior_engineer(result, reason)
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run unit tests only
pytest tests/test_main.py -v

# Run integration tests
pytest tests/test_integration.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

## Performance Characteristics

| Metric | Value |
|--------|-------|
| Average routing time | < 1 second |
| Specialist consultation (parallel) | 10-30 seconds |
| Total resolution time | 15-45 seconds |
| Cost per issue (Haiku specialists) | $0.01-0.05 |
| Cost per issue (Sonnet specialists) | $0.10-0.30 |
| Concurrent issues supported | 100+ |

## Best Practices

### 1. Specialist Design

- **Focused Expertise**: Each specialist should have clear, non-overlapping domain
- **Keyword Selection**: Use 10-20 specific keywords per specialist
- **Priority Tuning**: Set priority based on specialist availability and expertise depth
- **Model Selection**: Use Haiku for routine issues, Sonnet for complex analysis

### 2. Routing Optimization

- **Keyword Coverage**: Ensure at least 80% of common issues match a specialist
- **Fallback Specialist**: Always have a general specialist with priority 5
- **Max Specialists**: Limit to 3 to avoid noise and reduce cost
- **Min Matches**: Set to 1 for broad coverage, 2+ for precision

### 3. Urgency Calibration

- **Keyword Tuning**: Review historical issues to refine urgency keywords
- **SLA Monitoring**: Track actual vs. expected resolution times
- **False Positive Review**: Check for issues incorrectly marked as critical
- **Escalation Paths**: Define clear escalation rules for SLA breaches

### 4. Cost Management

```python
# Use tiered model selection
models:
  lead: "sonnet"              # Lead needs reasoning capability
  specialists: "haiku"         # Specialists execute focused tasks
  fallback: "haiku"           # Fallback handles routine issues

# Enable caching for similar issues
caching:
  enabled: true
  ttl_hours: 24
  similarity_threshold: 0.85   # Cache hit if 85% similar to previous issue
```

## Troubleshooting

### Issue: No specialists selected

**Symptom**: All issues route to fallback specialist

**Solutions**:
1. Check keyword coverage: `python analyze_keywords.py --issues issues.jsonl`
2. Lower `min_keyword_matches` to 1
3. Add more keywords to specialists
4. Review issue descriptions for unexpected terminology

### Issue: Wrong specialist selected

**Symptom**: Network issues routed to database specialist

**Solutions**:
1. Add negative keywords: `exclude_keywords: ["network", "vpn"]` to database specialist
2. Increase `min_keyword_matches` to 2 for precision
3. Review keyword overlap between specialists
4. Use priority to prefer more specific specialists

### Issue: Slow response time

**Symptom**: > 60 seconds per issue

**Solutions**:
1. Reduce `max_specialists` to 2
2. Use Haiku model for specialists
3. Implement result caching for common issues
4. Set specialist timeouts in config

## License

MIT License - See main repository for details

## Related Examples

- [Competitive Intelligence](../01_competitive_intelligence/) - Research architecture
- [PR Code Review](../02_pr_code_review/) - Pipeline architecture
- [Marketing Content](../03_marketing_content/) - Critic-Actor architecture

## Support

For issues and questions:
- GitHub Issues: https://github.com/anthropics/claude-agent-framework/issues
- Documentation: https://github.com/anthropics/claude-agent-framework/docs
