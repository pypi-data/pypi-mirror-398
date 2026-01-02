# Competitive Intelligence Analysis System

Automated competitor intelligence gathering and analysis system built on Claude Agent Framework's Research architecture.

## Overview

This example demonstrates how to use the Research architecture for parallel data collection and comprehensive analysis, suitable for:

- **SaaS Competitive Analysis** - Automate competitor product, pricing, and market performance analysis
- **Market Research** - Parallel research of multiple targets for quick industry insights
- **Product Planning** - Make data-driven product decisions based on competitive analysis

### Core Features

- ✅ **Parallel Competitor Research** - Simultaneously research multiple competitors (AWS, Azure, Google Cloud, etc.)
- ✅ **Multi-Channel Data Collection** - Official websites, market reports, customer reviews
- ✅ **Multi-Dimensional Analysis** - Feature comparison, pricing analysis, market share, tech stack, etc.
- ✅ **Structured Reports** - Generate analysis reports in JSON/Markdown/PDF format
- ✅ **SWOT Analysis** - Automatically generate Strengths, Weaknesses, Opportunities, Threats analysis

## Quick Start

### 1. Install Dependencies

```bash
# Install from project root directory
cd /path/to/claude-agent-framework
pip install -e ".[all]"

# Or install only basic dependencies
pip install -e .
```

### 2. Configure API Key

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

### 3. Configure Analysis Parameters

Edit the `config.yaml` file:

```yaml
competitors:
  - name: "AWS"
    website: "https://aws.amazon.com"
    focus_areas:
      - "Compute services"
      - "Storage solutions"
      - "Database offerings"

analysis_dimensions:
  - "Product Features"
  - "Pricing Model"
  - "Market Share"

output:
  directory: "outputs"
  format: "markdown"  # json, markdown, pdf
```

### 4. Run Analysis

```bash
cd examples/production/01_competitive_intelligence
python main.py
```

## Output Example

After analysis completes, the following output will be generated:

```
outputs/competitive_intelligence_report_20250125_143022.md
```

**Report Contents:**

```markdown
# Competitive Intelligence Analysis Report

## Summary
Analyzed 3 competitors across 6 dimensions

## Competitors
- AWS
- Microsoft Azure
- Google Cloud

## Analysis by Dimension

### Product Features
AWS: Leading in breadth of services...
Azure: Strong integration with Microsoft ecosystem...
Google Cloud: Advanced data analytics and ML...

### Pricing Model
AWS: Pay-as-you-go with volume discounts...
Azure: Hybrid benefit for Windows/SQL Server...
Google Cloud: Sustained use discounts...

### Market Share
AWS: 32% market leader...
Azure: 23% second position...
Google Cloud: 10% growing rapidly...

## SWOT Analysis

### AWS
**Strengths:** Market leader, extensive services
**Weaknesses:** Complex pricing, steep learning curve
**Opportunities:** Growing enterprise market
**Threats:** Intense competition from Azure/GCP

...

## Recommendations
1. Consider AWS for enterprise-scale deployments
2. Azure best for Microsoft-centric organizations
3. Google Cloud for data-intensive workloads
```

## Configuration

### Competitor Configuration

```yaml
competitors:
  - name: "Competitor Name"
    website: "Official Website URL"
    focus_areas:
      - "Focus Area 1"
      - "Focus Area 2"
```

### Analysis Dimensions

Configurable analysis dimensions include:

- **Product Features** - Product feature comparison
- **Pricing Model** - Pricing strategy analysis
- **Market Share** - Market share statistics
- **Technology Stack** - Technology stack
- **Customer Reviews** - Customer feedback
- **Recent Updates** - Latest developments

### Output Formats

Three output formats are supported:

1. **JSON** - Structured data, easy for programmatic processing
2. **Markdown** - Human-readable, easy to share
3. **PDF** - Professional report format (requires `pip install ".[pdf]"`)

## Architecture

This example uses the **Research** architecture with the following workflow:

```
Lead Agent (Research Coordinator)
    ├─> Industry Researcher (research industry trends)
    ├─> Competitor Analyst 1 (deep analysis of Competitor A)
    ├─> Competitor Analyst 2 (deep analysis of Competitor B)
    ├─> Competitor Analyst 3 (deep analysis of Competitor C)
    └─> Report Generator (synthesize comprehensive report)
```

**Advantages:**

- **Parallel Processing** - Multiple analysis tasks run simultaneously, significantly improving efficiency
- **Specialized Division** - Each subagent focuses on a specific competitor or dimension
- **Automatic Aggregation** - Lead Agent automatically integrates all analysis results

## Customization

### Add Custom Competitors

Add to `config.yaml`:

```yaml
competitors:
  - name: "Your Competitor"
    website: "https://example.com"
    focus_areas:
      - "Custom area 1"
      - "Custom area 2"
```

### Custom Analysis Dimensions

```yaml
analysis_dimensions:
  - "Security & Compliance"
  - "Developer Experience"
  - "Community Support"
```

### Adjust Model Configuration

```yaml
models:
  lead: "opus"     # Use more powerful model for lead agent
  agents: "haiku"  # Use cost-effective model for subagents
```

## Testing

```bash
# Run unit tests
pytest tests/test_main.py -v

# Run integration tests
pytest tests/test_integration.py -v
```

## FAQ

### Q: How to reduce API costs?

A: Adjust model configuration to use `haiku` for subagents:

```yaml
models:
  lead: "sonnet"
  agents: "haiku"
```

### Q: Analysis takes too long?

A: Reduce the number of competitors or analysis dimensions, or use faster models (haiku).

### Q: How to save to PDF?

A: Install PDF dependencies and configure output format:

```bash
pip install "claude-agent-framework[pdf]"
```

```yaml
output:
  format: "pdf"
```

### Q: How to view detailed logs?

A: Configure log level to DEBUG:

```yaml
logging:
  level: "DEBUG"
  file: "logs/analysis.log"
```

## Related Resources

- [Research Architecture Documentation](../../docs/BEST_PRACTICES.md#research-architecture)
- [Production Examples Design Document](../../docs/PRODUCTION_EXAMPLES_DESIGN.md)
- [Claude Agent Framework Documentation](../../README.md)

## License

MIT License
