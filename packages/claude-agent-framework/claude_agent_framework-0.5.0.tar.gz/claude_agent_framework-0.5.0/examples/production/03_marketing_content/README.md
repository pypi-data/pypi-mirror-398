# Marketing Content Optimization Example

This example demonstrates using the **Critic-Actor** architecture to iteratively create and improve marketing content through multi-dimensional evaluation and feedback.

## Overview

The marketing content optimization system uses a generate-evaluate-improve loop:

1. **Actor** generates initial content based on brief and brand guidelines
2. **Critic** evaluates content across multiple dimensions (SEO, engagement, brand, accuracy)
3. **Actor** improves content based on specific feedback
4. **Repeat** until quality threshold is reached or max iterations exhausted

Additionally, the system can generate A/B test variants with different angles for the same message.

## Features

- ✅ Iterative content refinement using Critic-Actor pattern
- ✅ Multi-dimensional evaluation (SEO, engagement, brand consistency, technical accuracy)
- ✅ Weighted scoring system (customize importance of each dimension)
- ✅ Brand voice and tone enforcement
- ✅ Prohibited phrase detection
- ✅ Quality threshold and improvement tracking
- ✅ A/B test variant generation with different angles
- ✅ Multiple content types (blog posts, emails, ad copy, social media, landing pages)
- ✅ Multiple output formats (JSON, Markdown, PDF)
- ✅ Iteration history tracking

## Quick Start

### Installation

```bash
cd examples/production/03_marketing_content
pip install -e ".[all]"
```

### Basic Usage

1. **Optimize marketing content with default config**:

```bash
python main.py
```

2. **Use custom configuration**:

```bash
python main.py --config my_config.yaml
```

3. **Generate PDF report**:

```bash
python main.py --output-format pdf
```

### Command Line Options

```bash
python main.py [OPTIONS]

Options:
  --config PATH          Configuration file (default: config.yaml)
  --output-format STR    Output format: json, markdown, pdf (default: markdown)
  --output-file PATH     Output file path (default: auto-generated)
  --log-level STR        Logging level: DEBUG, INFO, WARNING, ERROR
```

## Configuration

### Basic Configuration (`config.yaml`)

```yaml
# Architecture type
architecture: critic_actor

# Content configuration
content:
  # Content type
  type: "blog_post"  # blog_post, email, ad_copy, social_media, landing_page

  # Content brief
  brief: |
    Create a blog post announcing our new AI-powered code review tool.
    Target audience: Software engineering teams and DevOps professionals.
    Key points:
    - Automated code quality checks
    - Security vulnerability detection
    - Integration with GitHub and GitLab
    - 50% reduction in review time
    Call-to-action: Sign up for free trial

  # Keywords (for SEO)
  keywords:
    - "AI code review"
    - "automated code analysis"
    - "code quality"

  # Target length
  target_length:
    min_words: 800
    max_words: 1200

# Brand guidelines
brand:
  voice: "professional yet approachable"

  tone:
    - "innovative"
    - "trustworthy"
    - "technical yet accessible"

  prohibited_phrases:
    - "revolutionary"
    - "game-changer"

  values:
    - "Technical excellence"
    - "Developer productivity"

# Evaluation criteria (weights must sum to 100)
evaluation:
  # SEO optimization
  seo:
    weight: 25
    criteria:
      - "Keyword density (1-2%)"
      - "Meta description (150-160 chars)"
      - "Header structure (H1, H2, H3)"

  # Engagement/readability
  engagement:
    weight: 30
    criteria:
      - "Hook quality (first paragraph)"
      - "Readability score (Flesch-Kincaid 60-80)"
      - "Call-to-action clarity"

  # Brand consistency
  brand_consistency:
    weight: 25
    criteria:
      - "Voice alignment"
      - "Tone consistency"
      - "No prohibited phrases"

  # Technical accuracy
  accuracy:
    weight: 20
    criteria:
      - "Factual correctness"
      - "Technical term usage"

# Iteration configuration
iteration:
  max_iterations: 3              # Stop after N iterations
  quality_threshold: 85          # Stop if score >= threshold
  min_improvement: 5             # Stop if improvement < X%

# A/B testing
ab_testing:
  enabled: true
  num_variants: 2

# Models
models:
  lead: "sonnet"       # Lead orchestrator
  actor: "sonnet"      # Content creator (needs creativity)
  critic: "haiku"      # Evaluator (can be faster/cheaper)

# Output
output:
  directory: "outputs"
  format: "markdown"
  include_evaluation: true
  include_history: true
```

### Configuration Options

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `content.type` | string | Content type (blog_post, email, ad_copy, etc.) | "blog_post" |
| `content.brief` | string | Content creation brief | Required |
| `content.keywords` | list | SEO keywords | [] |
| `content.target_length` | object | Min/max word counts | - |
| `brand.voice` | string | Brand voice description | Required |
| `brand.tone` | list | Tone attributes | [] |
| `brand.prohibited_phrases` | list | Phrases to avoid | [] |
| `evaluation.*.weight` | int | Dimension weight (sum=100) | Required |
| `iteration.max_iterations` | int | Maximum iterations | 3 |
| `iteration.quality_threshold` | int | Target score (0-100) | 85 |
| `ab_testing.enabled` | bool | Generate A/B variants | false |
| `ab_testing.num_variants` | int | Number of variants | 2 |

## Output Example

### Markdown Report

```markdown
# Marketing Content Optimization Report

**Overall Status**: ✅ Target quality achieved

## Summary
Optimized blog_post through 3 iterations
Initial score: 68/100
Final score: 88/100
Improvement: +20.0 points

## Final Content

[Optimized content here - ready for publication]

## Iteration History

### Iteration 1 (Score: 68/100)

**Evaluation**:
- SEO: 60/100 - Needs more keyword integration
- Engagement: 70/100 - Hook could be stronger
- Brand Consistency: 75/100 - Voice slightly too formal
- Accuracy: 80/100 - Good technical detail

**Improvements Made**:
- Increased keyword density to 1.5%
- Rewrote opening paragraph with stronger hook
- Adjusted tone to be more approachable

### Iteration 2 (Score: 82/100)

**Evaluation**:
- SEO: 85/100 - Much better keyword integration
- Engagement: 88/100 - Excellent hook and CTA
- Brand Consistency: 82/100 - Good voice alignment
- Accuracy: 85/100 - Clear, accurate claims

**Improvements Made**:
- Added H2/H3 subheadings for better structure
- Strengthened call-to-action
- Added supporting statistics

### Iteration 3 (Score: 88/100)

**Evaluation**:
- SEO: 90/100 - Excellent keyword placement
- Engagement: 92/100 - Highly engaging
- Brand Consistency: 88/100 - Perfect voice match
- Accuracy: 90/100 - Well-supported claims

**Final Result**: Content meets quality threshold (≥85)

## A/B Test Variants

### Variant 1: Feature-Focused
[Variant emphasizing product capabilities...]

### Variant 2: Benefit-Focused
[Variant emphasizing user outcomes...]

## Metadata
- Timestamp: 2024-01-15 14:30:00
- Iterations: 3
- Target Content Type: blog_post
- Quality Threshold: 85/100
```

## Architecture

This example uses the **Critic-Actor** architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Lead Orchestrator                         │
│  (Manages generate-evaluate-improve loop)                    │
└──────────┬──────────────────────────────────┬───────────────┘
           │                                  │
           ▼                                  ▼
    ┌──────────┐                      ┌──────────┐
    │  Actor   │◄─────feedback────────│  Critic  │
    │          │                      │          │
    │ Generate │──────content────────►│ Evaluate │
    │ content  │                      │ score &  │
    │          │                      │ feedback │
    └──────────┘                      └──────────┘
           │
           │ (repeat until threshold or max iterations)
           ▼
    Final Content
```

### Critic-Actor Characteristics

- **Iterative Improvement**: Content improves through multiple cycles
- **Specific Feedback**: Critic provides actionable recommendations
- **Multi-Dimensional**: Evaluation across SEO, engagement, brand, accuracy
- **Weighted Scoring**: Customize importance of different dimensions
- **Convergence Detection**: Stops when improvement becomes marginal

## Customization

### Adding Custom Evaluation Dimensions

Add new dimensions to `config.yaml`:

```yaml
evaluation:
  # ... existing dimensions ...

  accessibility:
    weight: 10  # Adjust other weights to maintain sum=100
    criteria:
      - "Alt text for images"
      - "Proper heading hierarchy"
      - "WCAG compliance"
```

### Custom Content Types

Create templates for new content types:

```python
# prompts/product_description.txt
Create a compelling product description following these guidelines:

**Product**: {product_name}
**Key Features**: {features}
**Target Audience**: {audience}
**Length**: {min_words}-{max_words} words

Focus on benefits over features, use sensory language, and include social proof.
```

### Brand Voice Examples

Different brand voice configurations:

```yaml
# Professional/Technical
brand:
  voice: "authoritative and expert"
  tone: ["technical", "precise", "trustworthy"]

# Casual/Friendly
brand:
  voice: "conversational and warm"
  tone: ["friendly", "accessible", "enthusiastic"]

# Luxury/Premium
brand:
  voice: "sophisticated and aspirational"
  tone: ["elegant", "exclusive", "refined"]
```

## Testing

### Run Unit Tests

```bash
pytest tests/test_main.py -v
```

### Run Integration Tests

```bash
pytest tests/test_integration.py -v
```

### Run All Tests

```bash
pytest tests/ -v --cov=. --cov-report=html
```

## Advanced Usage

### Programmatic Usage

```python
from claude_agent_framework import init
from common import load_yaml_config, ResultSaver

# Load configuration
config = load_yaml_config("config.yaml")

# Run optimization
result = await run_content_optimization(config)

# Access results
print(f"Final score: {result['final_score']}/100")
print(f"Iterations: {len(result['iterations'])}")

# Generate A/B variants if needed
if result['ab_variants']:
    for variant in result['ab_variants']:
        print(f"\nVariant {variant['variant']} ({variant['angle']}):")
        print(variant['content'])
```

### Custom Evaluation Logic

Extend the critic with custom evaluation:

```python
def custom_evaluation(content: str, brand: dict) -> dict:
    """Custom evaluation logic."""
    scores = {}

    # Check reading level
    from textstat import flesch_reading_ease
    readability = flesch_reading_ease(content)
    scores['readability'] = min(100, readability * 1.25)

    # Check brand voice compliance
    voice_keywords = brand.get('voice_keywords', [])
    matches = sum(1 for kw in voice_keywords if kw.lower() in content.lower())
    scores['brand_voice'] = min(100, (matches / len(voice_keywords)) * 100)

    return scores
```

## Troubleshooting

### Common Issues

1. **Score not improving**
   ```
   Issue: Score stays the same across iterations
   Solution: Reduce quality_threshold or increase max_iterations
   ```

2. **Content too short/long**
   ```
   Issue: Generated content doesn't meet length requirements
   Solution: Emphasize target_length in content brief
   ```

3. **Brand voice mismatch**
   ```
   Issue: Content doesn't match brand voice
   Solution: Provide more specific voice examples in brand config
   ```

### Debug Mode

Enable detailed logging:

```bash
python main.py --log-level DEBUG
```

## FAQ

**Q: How many iterations should I use?**
A: Start with 3. Increase to 5 for complex content or high quality standards.

**Q: Can I use this for content in languages other than English?**
A: Yes, just provide the brief and brand guidelines in your target language.

**Q: How do I weight evaluation dimensions?**
A: Adjust the `weight` field for each dimension. Weights must sum to 100.

**Q: Can I generate more than 2 A/B variants?**
A: Yes, set `ab_testing.num_variants` to any number (recommended: 2-4).

**Q: How long does optimization take?**
A: Typically 45-90 seconds per iteration, depending on content length and model.

## Related Examples

- [01_competitive_intelligence](../01_competitive_intelligence/) - Research architecture
- [02_pr_code_review](../02_pr_code_review/) - Pipeline architecture
- [05_tech_decision](../05_tech_decision/) - Debate architecture

## License

MIT License - see [LICENSE](../../../LICENSE) for details.
