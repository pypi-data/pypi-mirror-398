# PR Code Review Pipeline Example

This example demonstrates using the **Pipeline** architecture to implement an automated Pull Request code review system with sequential analysis stages.

## Overview

The PR code review pipeline executes a series of review stages in sequence:

1. **Architecture Review** - Analyze design patterns, dependencies, architecture
2. **Code Quality** - Check code style, complexity, maintainability
3. **Security Scan** - Scan for security vulnerabilities (SAST)
4. **Performance Analysis** - Analyze performance impact and bottlenecks
5. **Test Coverage** - Validate test coverage and quality

Each stage builds on the previous stage's findings to provide comprehensive code review feedback.

## Features

- ✅ Sequential pipeline processing (5 configurable stages)
- ✅ Support for GitHub PR URLs or local git repositories
- ✅ Configurable analysis thresholds (complexity, coverage, etc.)
- ✅ Multiple failure strategies (stop on critical vs. continue)
- ✅ Structured review report with overall status
- ✅ Actionable recommendations extraction
- ✅ Multiple output formats (JSON, Markdown, PDF)
- ✅ Comprehensive error handling and logging

## Quick Start

### Installation

```bash
cd examples/production/02_pr_code_review
pip install -e ".[all]"
```

### Basic Usage

1. **Review a local PR** (comparing current branch to main):

```bash
python main.py
```

2. **Review with custom configuration**:

```bash
python main.py --config my_config.yaml
```

3. **Review a GitHub PR**:

Edit `config.yaml` to set:
```yaml
pr_source:
  pr_url: "https://github.com/owner/repo/pull/123"
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
architecture: pipeline

# Review stages (executed sequentially)
stages:
  - name: "architecture_review"
    description: "Analyze design patterns, dependencies, and architecture"
    required: true
    timeout: 300

  - name: "code_quality"
    description: "Check code style, complexity, and maintainability"
    required: true
    timeout: 180

  - name: "security_scan"
    description: "Scan for security vulnerabilities (SAST)"
    required: true
    timeout: 240

  - name: "performance_analysis"
    description: "Analyze performance impact and bottlenecks"
    required: false  # Optional stage
    timeout: 180

  - name: "test_coverage"
    description: "Validate test coverage and quality"
    required: true
    timeout: 120

# PR source (choose one)
pr_source:
  # Option 1: Local git repository
  local_path: "."
  base_branch: "main"

  # Option 2: GitHub PR URL
  # pr_url: "https://github.com/owner/repo/pull/123"

# Analysis thresholds
analysis:
  max_complexity: 10           # Maximum cyclomatic complexity
  max_function_length: 50      # Maximum lines per function
  min_coverage: 80             # Minimum test coverage percentage
  max_file_size: 500           # Maximum lines per file

# Failure strategy
failure_strategy: "stop_on_critical"  # or "continue_all"

# Model configuration
models:
  lead: "sonnet"   # Lead orchestrator model
  agents: "haiku"  # Stage analyzer model

# Output configuration
output:
  directory: "outputs"
  format: "markdown"  # json, markdown, or pdf

# Logging
logging:
  level: "INFO"
  file: "logs/pr_review.log"
```

### Configuration Options

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `architecture` | string | Must be "pipeline" | "pipeline" |
| `stages` | list | Review stages to execute | See example |
| `pr_source.local_path` | string | Local git repository path | "." |
| `pr_source.base_branch` | string | Base branch to compare against | "main" |
| `pr_source.pr_url` | string | GitHub PR URL (alternative to local) | - |
| `analysis.max_complexity` | int | Maximum cyclomatic complexity | 10 |
| `analysis.min_coverage` | int | Minimum test coverage (%) | 80 |
| `failure_strategy` | string | "stop_on_critical" or "continue_all" | "stop_on_critical" |
| `models.lead` | string | Lead model: haiku, sonnet, opus | "sonnet" |
| `output.format` | string | Output format: json, markdown, pdf | "markdown" |

## Output Example

### Markdown Report

```markdown
# Pull Request Code Review Report

**Overall Status**: ✅ APPROVED WITH COMMENTS

## Summary
- 5 stages executed
- 4 stages passed
- 1 stage with warnings
- 0 stages failed

## PR Information
- **Files Changed**: 15
- **Lines Added**: 450
- **Lines Deleted**: 120
- **Base Branch**: main

## Review Stages

### 1. Architecture Review ✅ PASS
- Clean separation of concerns
- Appropriate use of design patterns
- Dependencies well-managed

### 2. Code Quality ⚠️ WARNING
- 3 functions exceed complexity threshold (>10)
- Recommend refactoring: `process_data()`, `validate_input()`
- Overall maintainability: Good

### 3. Security Scan ✅ PASS
- No SQL injection vulnerabilities detected
- No XSS vulnerabilities found
- Input validation present

### 4. Performance Analysis ✅ PASS
- No obvious bottlenecks
- Database queries optimized
- Caching strategy appropriate

### 5. Test Coverage ✅ PASS
- Coverage: 85% (threshold: 80%)
- Critical paths tested
- Edge cases covered

## Recommendations

1. **High Priority**: Refactor `process_data()` to reduce complexity (current: 15, max: 10)
2. **Medium Priority**: Add error handling in `api_client.py:45`
3. **Low Priority**: Consider adding integration tests for new API endpoints

## Metadata
- **Review Duration**: 45.2 seconds
- **Timestamp**: 2024-01-15 14:30:00
- **Reviewer**: Claude Code Review Bot
```

## Architecture

This example uses the **Pipeline** architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                     Lead Orchestrator                        │
│  (Coordinates sequential stage execution)                    │
└────────────┬────────────────────────────────────────────────┘
             │
             ├─► Stage 1: Architecture Review
             │   └─► Output: Design patterns, architecture feedback
             │
             ├─► Stage 2: Code Quality
             │   └─► Output: Style issues, complexity warnings
             │
             ├─► Stage 3: Security Scan
             │   └─► Output: Vulnerability findings
             │
             ├─► Stage 4: Performance Analysis
             │   └─► Output: Performance impact assessment
             │
             └─► Stage 5: Test Coverage
                 └─► Output: Coverage metrics, test quality
```

### Pipeline Characteristics

- **Sequential Processing**: Each stage executes in order
- **Data Flow**: Each stage can use outputs from previous stages
- **Failure Handling**: Can stop on critical failures or continue all
- **Stage Independence**: Each stage focuses on specific aspect
- **Aggregated Results**: Final report combines all stage findings

## Customization

### Adding Custom Review Stages

Add new stages to `config.yaml`:

```yaml
stages:
  # ... existing stages ...

  - name: "documentation_check"
    description: "Verify documentation completeness and quality"
    required: false
    timeout: 60
```

### Custom Analysis Rules

Modify thresholds in `config.yaml`:

```yaml
analysis:
  max_complexity: 15        # More lenient
  min_coverage: 90          # Stricter
  max_file_size: 300        # Stricter

  # Add custom rules
  custom_rules:
    - "no-console-log"
    - "prefer-const"
    - "no-implicit-any"
```

### Integration with CI/CD

Example GitHub Actions workflow:

```yaml
name: PR Code Review

on:
  pull_request:
    branches: [ main, develop ]

jobs:
  code-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          cd examples/production/02_pr_code_review
          pip install -e ".[all]"

      - name: Run PR Review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python main.py --output-format markdown --output-file review.md

      - name: Comment PR
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const review = fs.readFileSync('review.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: review
            });
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

### Custom Prompt Templates

Create custom prompts for specific stage types:

```python
# prompts/security_scan.txt
You are a security expert reviewing code for vulnerabilities.

Focus on:
- SQL injection vulnerabilities
- XSS vulnerabilities
- Authentication/authorization issues
- Sensitive data exposure
- Cryptographic weaknesses

For each finding, provide:
- Severity (Critical/High/Medium/Low)
- Location (file:line)
- Description
- Remediation steps
```

### Programmatic Usage

```python
from claude_agent_framework import init
from common import load_yaml_config, ResultSaver

# Load configuration
config = load_yaml_config("config.yaml")

# Run review
result = await run_pr_review(config)

# Process results
if result["overall_status"] == "APPROVED":
    print("✅ PR approved!")
elif result["overall_status"] == "APPROVED_WITH_COMMENTS":
    print("⚠️ PR approved with comments")
    for rec in result["recommendations"]:
        print(f"  - {rec}")
else:
    print("❌ Changes requested")
    sys.exit(1)
```

## Troubleshooting

### Common Issues

1. **Git not found**
   ```
   Error: git command not found
   Solution: Install git or use pr_url instead of local_path
   ```

2. **No changes detected**
   ```
   Error: No changes found between branches
   Solution: Ensure you're on a feature branch, not main
   ```

3. **Timeout errors**
   ```
   Error: Stage timeout after 300s
   Solution: Increase timeout in stage configuration
   ```

### Debug Mode

Enable detailed logging:

```bash
python main.py --log-level DEBUG
```

## FAQ

**Q: Can I use this with Bitbucket or GitLab?**
A: Currently supports GitHub URLs and local git repos. For other platforms, use local_path mode.

**Q: How do I customize the review criteria?**
A: Modify the `analysis` section in config.yaml or create custom stage prompts.

**Q: Can I skip certain stages?**
A: Yes, set `required: false` for optional stages, or remove them from the stages list.

**Q: How long does a typical review take?**
A: 30-60 seconds for small PRs (<500 lines), 2-3 minutes for large PRs (>2000 lines).

**Q: Does this replace human code review?**
A: No, it's designed to augment human review by catching common issues and providing preliminary feedback.

## Related Examples

- [01_competitive_intelligence](../01_competitive_intelligence/) - Research architecture
- [03_marketing_content](../03_marketing_content/) - Critic-Actor architecture
- [07_codebase_analysis](../07_codebase_analysis/) - MapReduce architecture

## License

MIT License - see [LICENSE](../../../LICENSE) for details.
