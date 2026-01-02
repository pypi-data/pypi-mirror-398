# Codebase Analysis - MapReduce Architecture Example

This example demonstrates using the **MapReduce architecture** for large-scale static code analysis and technical debt detection. It analyzes entire codebases (hundreds of files) in parallel, identifies quality issues, security vulnerabilities, and provides actionable recommendations.

## Architecture Overview

The MapReduce architecture divides large codebases into manageable chunks, analyzes them in parallel (map phase), and aggregates results (reduce phase):

```
                    ┌─────────────────┐
                    │   Coordinator   │
                    │  (Orchestrates) │
                    └────────┬────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
         ┌──────▼──────┐ ┌──▼────────┐ ┌▼──────────┐
         │  Mapper 1   │ │ Mapper 2  │ │ Mapper N  │
         │ (Analyze    │ │ (Analyze  │ │ (Analyze  │
         │  Chunk 1)   │ │  Chunk 2) │ │  Chunk N) │
         └──────┬──────┘ └──┬────────┘ └┬──────────┘
                │            │            │
                └────────────┼────────────┘
                             │
                    ┌────────▼────────┐
                    │    Reducer      │
                    │  (Aggregate &   │
                    │   Prioritize)   │
                    └─────────────────┘
```

## Real-World Use Cases

### 1. Enterprise Codebase Audit

**Scenario**: Software company needs to assess technical debt across 500+ Python files before a major refactoring.

**Configuration Focus**:
- Enable all analysis types (quality, security, performance, maintainability, testing)
- Use `by_module` chunking strategy to respect project organization
- Set high confidence threshold (0.8) to focus on critical issues
- Generate comprehensive report with visualizations

**Expected Results**:
- 250+ files analyzed in 10 parallel chunks
- ~50 critical security vulnerabilities identified
- ~120 high-priority technical debt items
- Per-module health scores for targeted refactoring
- Estimated 80 hours to address critical issues

### 2. Open Source Project Security Review

**Scenario**: Security team needs to audit a popular open-source library before adoption.

**Configuration Focus**:
- Enable security and testing analysis types only
- Use `bandit` and `safety` tools for automated scanning
- Filter out test files and build artifacts
- Generate security-focused report

**Expected Results**:
- SQL injection vulnerabilities detected
- Hardcoded secrets found and flagged
- Dependency vulnerabilities identified
- Test coverage gaps in critical paths
- Security score and remediation priorities

### 3. Pre-Release Quality Gate

**Scenario**: DevOps team implements automated quality checks before each major release.

**Configuration Focus**:
- Incremental analysis (only changed files since last release)
- Baseline comparison to track quality trends
- Auto-fix suggestions enabled
- Export results to CI/CD dashboard (JSON format)

**Expected Results**:
- +15 new issues introduced since last release
- -22 issues resolved
- Overall quality score: 82/100 (up from 78/100)
- 4 blocking issues requiring immediate attention
- Automated fix suggestions for 12 issues

## Configuration

Complete `config.yaml` structure:

```yaml
architecture: mapreduce

analysis:
  max_parallel_mappers: 10       # Parallel analysis tasks (10 recommended)
  chunk_size: 50                 # Files per chunk (auto-adjusts based on total)
  aggregation_strategy: weighted # weighted, average, or max
  min_confidence: 0.7            # Confidence threshold for reporting (0.0-1.0)
  enable_caching: true           # Cache results for incremental analysis
  output_format: structured      # structured, markdown, or json

mapreduce_config:
  mapper:
    name: code_analyzer
    role: Analyze code chunks for quality issues, technical debt, and patterns
    tools:
      - Read         # Read source files
      - Bash         # Run static analysis tools
      - Grep         # Search for patterns
    analysis_depth: comprehensive  # quick, standard, or comprehensive

  reducer:
    name: results_aggregator
    role: Aggregate and prioritize analysis results across all chunks
    capabilities:
      - Deduplication   # Remove duplicate findings
      - Prioritization  # Rank by severity and impact
      - Categorization  # Group by type and location
      - Trend analysis  # Identify patterns across codebase

  coordinator:
    name: analysis_coordinator
    role: Orchestrate analysis workflow and ensure completeness
    responsibilities:
      - Intelligent chunking based on file relationships
      - Load balancing across mappers
      - Progress tracking
      - Quality assurance

# Chunking strategies (choose one via options.chunking_strategy)
chunking_strategies:
  by_module:          # Group by module/package structure (default)
    description: Group files by module/package structure
    when_to_use: Well-organized codebase with clear modules
    benefits:
      - Respects code organization
      - Better context for analysis
      - Easier to understand results

  by_file_type:       # Group by language/extension
    description: Group files by extension/language
    when_to_use: Multi-language codebase
    benefits:
      - Language-specific analysis
      - Parallel language processing
      - Specialized tool usage

  by_size:            # Balance chunks by file size
    description: Balance chunks by total file size
    when_to_use: Files vary greatly in size
    benefits:
      - Even workload distribution
      - Predictable execution time
      - Better resource utilization

  by_git_history:     # Focus on frequently changed files
    description: Group files by change frequency
    when_to_use: Focus on frequently changed code
    benefits:
      - Prioritize high-risk areas
      - Find hotspots
      - Target refactoring efforts

# Analysis types (enable/disable as needed)
analysis_types:
  code_quality:
    enabled: true
    priority: 1
    checks:
      - complexity          # Cyclomatic complexity
      - duplication         # Code duplication
      - naming_conventions  # Variable/function naming
      - code_smells         # Common anti-patterns
      - documentation       # Missing docstrings/comments
    tools:
      - pylint
      - radon
      - flake8
    thresholds:
      max_complexity: 10
      max_duplication: 5
      min_documentation: 0.7

  security:
    enabled: true
    priority: 1
    checks:
      - sql_injection       # SQL injection vulnerabilities
      - xss                 # Cross-site scripting
      - hardcoded_secrets   # Passwords, API keys in code
      - unsafe_functions    # Dangerous function usage
      - dependency_vulnerabilities
    tools:
      - bandit
      - safety
    severity_levels:
      - critical
      - high
      - medium
      - low

  performance:
    enabled: true
    priority: 2
    checks:
      - n_plus_one_queries  # Database query patterns
      - inefficient_loops   # Nested loops, unnecessary iterations
      - memory_leaks        # Potential memory issues
      - blocking_operations # Blocking I/O in async code

  maintainability:
    enabled: true
    priority: 2
    checks:
      - technical_debt      # TODOs, FIXMEs, HACKs
      - deprecated_usage    # Use of deprecated APIs
      - dead_code           # Unreachable code
      - long_methods        # Methods exceeding length limits
      - god_classes         # Classes with too many responsibilities
    thresholds:
      max_method_lines: 50
      max_class_lines: 300
      max_parameters: 5

  testing:
    enabled: true
    priority: 3
    checks:
      - test_coverage       # Code coverage percentage
      - missing_tests       # Untested critical paths
      - test_quality        # Assertion count, test isolation
      - flaky_tests         # Tests with inconsistent results
    target_coverage: 0.8

# Advanced settings
advanced:
  incremental_analysis: true    # Only analyze changed files
  git_integration: true         # Use git history for context
  baseline_comparison: true     # Compare against previous runs
  auto_fix_suggestions: true    # Suggest automated fixes
  confidence_scoring: true      # Score each finding

  performance:
    timeout_per_chunk: 300      # 5 minutes per chunk
    max_memory_per_mapper: 1024 # 1GB memory limit
    retry_on_failure: 3         # Retry failed chunks

  filters:
    exclude_paths:
      - "*/tests/*"             # Exclude test files
      - "*/migrations/*"        # Exclude migrations
      - "*/build/*"            # Exclude build artifacts
      - "*/node_modules/*"     # Exclude dependencies

    include_extensions:
      - .py
      - .js
      - .ts
      - .java
      - .go
      - .rb

    min_file_size: 10          # Bytes
    max_file_size: 1000000     # 1MB

models:
  coordinator: sonnet          # Complex orchestration (recommended: sonnet)
  mapper: haiku                # Fast, parallel analysis (recommended: haiku)
  reducer: sonnet              # Complex aggregation logic (recommended: sonnet)
```

## Output Structure

The analysis returns a comprehensive result dictionary:

```python
{
    "analysis_id": "abc123...",
    "title": "Codebase Analysis: my-project",
    "summary": "Executive summary with 75/100 health score...",

    "codebase": {
        "path": "/path/to/codebase",
        "files_analyzed": 250,
        "lines_of_code": 35000,
        "languages": ["Python", "JavaScript"]
    },

    "execution": {
        "chunks_analyzed": [
            {
                "chunk_id": 1,
                "file_count": 50,
                "files": ["file1.py", "file2.py", ...]
            },
            ...
        ],
        "parallel_mappers": 5,
        "chunking_strategy": "by_module"
    },

    "issues": {
        "total": 87,
        "by_severity": {
            "critical": 5,
            "high": 18,
            "medium": 42,
            "low": 22
        },
        "critical": [
            {
                "severity": "critical",
                "type": "security",
                "file": "auth/models.py",
                "line": 45,
                "description": "SQL injection vulnerability",
                "confidence": "High",
                "fix_effort": "Medium"
            },
            ...
        ],
        "high": [...],
        "medium": [...],
        "low": [...],
        "all_issues": [...]
    },

    "metrics": {
        "total_files": 250,
        "total_lines": 35000,
        "average_complexity": 6.8,
        "test_coverage": 72.5,
        "quality_score": 78,
        "security_score": 68,
        "maintainability_score": 82
    },

    "module_health": [
        {
            "name": "auth_module",
            "score": 65,
            "status": "needs_attention"  # healthy, needs_attention, critical
        },
        ...
    ],

    "trends": {
        "new_issues": 12,
        "resolved_issues": 18,
        "net_change": -6
    },

    "recommendations": [
        {
            "action": "Fix SQL injection in auth/models.py",
            "reason": "Critical security risk",
            "effort": "Medium",
            "impact": "High",
            "priority": "High"
        },
        ...
    ],

    "scores": {
        "overall": 75,
        "quality": 78,
        "security": 68,
        "maintainability": 82,
        "test_coverage": 72.5
    },

    "metadata": {
        "timestamp": "2025-12-25T10:30:00Z",
        "analysis_config": {
            "types_enabled": ["code_quality", "security", "performance"],
            "parallel_mappers": 10,
            "chunk_size": 50
        },
        "models": {
            "coordinator": "sonnet",
            "mapper": "haiku",
            "reducer": "sonnet"
        }
    }
}
```

## Customization Examples

### 1. Security-Only Analysis

```python
from claude_agent_framework import init
from main import run_codebase_analysis
import yaml

with open("config.yaml") as f:
    config = yaml.safe_load(f)

# Disable all except security
config["analysis_types"] = {
    "security": {
        "enabled": True,
        "priority": 1,
        "checks": ["sql_injection", "xss", "hardcoded_secrets"]
    }
}

result = await run_codebase_analysis(config, "/path/to/codebase")
print(f"Security score: {result['scores']['security']}/100")
print(f"Critical vulnerabilities: {len(result['issues']['critical'])}")
```

### 2. Fast Quality Check (Quick Mode)

```python
# Use fast model and minimal checks
config["mapreduce_config"]["mapper"]["analysis_depth"] = "quick"
config["models"] = {"coordinator": "haiku", "mapper": "haiku", "reducer": "haiku"}
config["analysis"]["chunk_size"] = 100  # Larger chunks

result = await run_codebase_analysis(config, "/path/to/codebase")
```

### 3. Incremental Analysis with Baseline

```python
# Analyze only changed files since last run
config["advanced"]["incremental_analysis"] = True
config["advanced"]["baseline_comparison"] = True
config["advanced"]["git_integration"] = True

result = await run_codebase_analysis(config, "/path/to/codebase")

# Compare with baseline
trends = result["trends"]
print(f"New issues: +{trends['new_issues']}")
print(f"Resolved: -{trends['resolved_issues']}")
print(f"Net change: {trends['net_change']}")
```

### 4. Custom Chunking Strategy

```python
# Use git history to prioritize frequently changed files
options = {"chunking_strategy": "by_git_history"}
result = await run_codebase_analysis(config, "/path/to/codebase", options)
```

### 5. Export to CI/CD Pipeline

```python
import json

result = await run_codebase_analysis(config, "/path/to/codebase")

# Export for CI/CD
with open("analysis_report.json", "w") as f:
    json.dump(result, f, indent=2)

# Fail build if critical issues found
critical_count = len(result["issues"]["critical"])
if critical_count > 0:
    print(f"❌ Build failed: {critical_count} critical issues found")
    exit(1)
else:
    print(f"✅ Build passed: Quality score {result['scores']['overall']}/100")
```

## Best Practices

### 1. Choose Appropriate Chunk Size

- **Small codebases (< 50 files)**: chunk_size = 10-20
- **Medium codebases (50-200 files)**: chunk_size = 30-50
- **Large codebases (200-500 files)**: chunk_size = 50-100
- **Very large codebases (> 500 files)**: chunk_size = 100-200

### 2. Parallel Mapper Optimization

- **Local development**: max_parallel_mappers = 3-5 (avoid overwhelming API rate limits)
- **CI/CD pipelines**: max_parallel_mappers = 8-12 (faster execution)
- **Production audits**: max_parallel_mappers = 10-15 (balance speed vs cost)

### 3. Analysis Type Selection

For **daily checks**: Enable only `code_quality` and `security` (priority 1)
For **release gates**: Enable `code_quality`, `security`, `testing` (priorities 1-3)
For **comprehensive audits**: Enable all analysis types
For **security reviews**: Enable only `security` with all checks

### 4. Model Selection Strategy

- **Coordinator**: Always use `sonnet` (complex orchestration logic)
- **Mapper**: Use `haiku` for speed, `sonnet` for accuracy
- **Reducer**: Use `sonnet` for complex aggregation, `haiku` if simple deduplication

### 5. Confidence Threshold Tuning

- **High confidence (0.8-1.0)**: For critical production audits (fewer false positives)
- **Medium confidence (0.6-0.8)**: For regular code reviews (balanced)
- **Low confidence (0.4-0.6)**: For exploratory analysis (more findings, some false positives)

### 6. Incremental Analysis

Enable `incremental_analysis` for:
- Daily/hourly CI checks
- Pre-commit hooks
- Continuous monitoring

Disable for:
- Initial audits
- Major refactoring validations
- Quarterly comprehensive reviews

## Performance Metrics

Based on testing with a 500-file Python codebase:

| Configuration | Files | Chunks | Parallel | Time | Cost |
|--------------|-------|--------|----------|------|------|
| Quick (Haiku) | 500 | 5 | 5 | ~3 min | ~$0.50 |
| Standard (Mixed) | 500 | 10 | 10 | ~5 min | ~$1.20 |
| Comprehensive (Sonnet) | 500 | 10 | 10 | ~8 min | ~$2.50 |

**Scalability estimates**:
- 100 files: 1-2 minutes
- 500 files: 3-8 minutes
- 1000 files: 6-15 minutes
- 5000 files: 25-60 minutes

## Troubleshooting

### Issue: Empty or Missing Results

**Symptom**: Analysis completes but returns no issues or metrics

**Causes**:
1. `exclude_paths` filter too aggressive
2. `min_confidence` threshold too high
3. Analysis types disabled

**Solutions**:
```python
# Check filters
config["advanced"]["filters"]["exclude_paths"] = []  # Remove all exclusions temporarily

# Lower confidence threshold
config["analysis"]["min_confidence"] = 0.5

# Enable all analysis types
for analysis_type in config["analysis_types"].values():
    analysis_type["enabled"] = True
```

### Issue: Timeout Errors

**Symptom**: `TimeoutError` or chunks failing

**Causes**:
1. Chunk size too large
2. Timeout too short for complex files
3. Too many parallel mappers overloading API

**Solutions**:
```python
# Reduce chunk size
config["analysis"]["chunk_size"] = 20  # Smaller chunks

# Increase timeout
config["advanced"]["performance"]["timeout_per_chunk"] = 600  # 10 minutes

# Reduce parallelism
config["analysis"]["max_parallel_mappers"] = 3
```

### Issue: High False Positive Rate

**Symptom**: Too many low-priority or irrelevant issues

**Causes**:
1. Confidence threshold too low
2. Analysis depth too comprehensive
3. Tools generating noise

**Solutions**:
```python
# Raise confidence threshold
config["analysis"]["min_confidence"] = 0.8

# Use standard depth instead of comprehensive
config["mapreduce_config"]["mapper"]["analysis_depth"] = "standard"

# Disable noisy checks
config["analysis_types"]["code_quality"]["checks"] = ["complexity", "security"]  # Remove "naming_conventions"
```

### Issue: Memory Errors

**Symptom**: Out of memory errors during analysis

**Causes**:
1. Too many parallel mappers
2. Chunk size too large
3. Very large files in codebase

**Solutions**:
```python
# Reduce parallelism
config["analysis"]["max_parallel_mappers"] = 3

# Limit file size
config["advanced"]["filters"]["max_file_size"] = 500000  # 500KB

# Use "by_size" chunking to balance load
options = {"chunking_strategy": "by_size"}
```

## Complete Example

```python
import asyncio
import yaml
from main import run_codebase_analysis

async def analyze_codebase():
    # Load configuration
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    # Customize for your needs
    config["analysis"]["max_parallel_mappers"] = 5
    config["analysis"]["min_confidence"] = 0.7

    # Enable specific analysis types
    config["analysis_types"]["security"]["enabled"] = True
    config["analysis_types"]["code_quality"]["enabled"] = True

    # Run analysis
    print("🔍 Starting codebase analysis...")
    result = await run_codebase_analysis(
        config,
        "/path/to/your/codebase",
        options={"chunking_strategy": "by_module"}
    )

    # Print summary
    print(f"\n{'='*60}")
    print(f"📊 Analysis Complete: {result['title']}")
    print(f"{'='*60}")
    print(f"\n📁 Codebase:")
    print(f"  - Files analyzed: {result['codebase']['files_analyzed']}")
    print(f"  - Lines of code: {result['codebase']['lines_of_code']:,}")

    print(f"\n🎯 Overall Score: {result['scores']['overall']}/100")
    print(f"  - Quality: {result['scores']['quality']}/100")
    print(f"  - Security: {result['scores']['security']}/100")
    print(f"  - Maintainability: {result['scores']['maintainability']}/100")

    print(f"\n⚠️  Issues Found: {result['issues']['total']}")
    print(f"  - Critical: {result['issues']['by_severity']['critical']}")
    print(f"  - High: {result['issues']['by_severity']['high']}")
    print(f"  - Medium: {result['issues']['by_severity']['medium']}")
    print(f"  - Low: {result['issues']['by_severity']['low']}")

    if result['issues']['critical']:
        print(f"\n🚨 Critical Issues (Top 5):")
        for issue in result['issues']['critical'][:5]:
            print(f"  - {issue['file']}:{issue['line']} - {issue['description']}")

    print(f"\n📈 Module Health:")
    for module in result['module_health'][:5]:
        status_icon = "✅" if module['status'] == "healthy" else "⚠️" if module['status'] == "needs_attention" else "❌"
        print(f"  {status_icon} {module['name']}: {module['score']}/100")

    if result['recommendations']:
        print(f"\n💡 Top Recommendations:")
        for i, rec in enumerate(result['recommendations'][:5], 1):
            print(f"  {i}. {rec['action']}")
            print(f"     Effort: {rec['effort']} | Impact: {rec['impact']}")

    return result

if __name__ == "__main__":
    result = asyncio.run(analyze_codebase())
```

**Sample Output**:

```
🔍 Starting codebase analysis...

============================================================
📊 Analysis Complete: Codebase Analysis: my-project
============================================================

📁 Codebase:
  - Files analyzed: 250
  - Lines of code: 35,000

🎯 Overall Score: 75/100
  - Quality: 78/100
  - Security: 68/100
  - Maintainability: 82/100

⚠️  Issues Found: 87
  - Critical: 5
  - High: 18
  - Medium: 42
  - Low: 22

🚨 Critical Issues (Top 5):
  - auth/models.py:45 - SQL injection vulnerability in raw query
  - api/endpoints.py:89 - Missing authentication check on admin endpoint
  - utils/crypto.py:23 - Hardcoded encryption key
  - payment/process.py:156 - Unvalidated user input in SQL query
  - session/manager.py:78 - Insecure session token generation

📈 Module Health:
  ❌ auth_module: 65/100
  ⚠️  api_module: 78/100
  ✅ utils_module: 88/100
  ✅ core_module: 92/100
  ✅ tests_module: 95/100

💡 Top Recommendations:
  1. Fix SQL injection vulnerability in auth/models.py
     Effort: Medium | Impact: High
  2. Add authentication checks to all API endpoints
     Effort: Medium | Impact: High
  3. Remove hardcoded credentials and use environment variables
     Effort: Low | Impact: High
  4. Reduce cyclomatic complexity in auth/views.py (complexity: 25)
     Effort: High | Impact: Medium
  5. Increase test coverage to target 80% (currently 72.5%)
     Effort: High | Impact: Medium
```

## Architecture Benefits

1. **Scalability**: Analyzes hundreds of files in parallel, handling codebases of any size
2. **Comprehensive**: Detects quality, security, performance, and maintainability issues
3. **Actionable**: Provides prioritized recommendations with effort/impact estimates
4. **Flexible**: Highly customizable chunking strategies and analysis types
5. **Efficient**: MapReduce pattern minimizes redundant work and optimizes resource usage
6. **Incremental**: Supports baseline comparison and incremental analysis for CI/CD
7. **Detailed**: Per-module health scores enable targeted refactoring efforts

## Next Steps

1. **Customize Configuration**: Adjust `config.yaml` for your codebase and priorities
2. **Run Initial Audit**: Perform comprehensive analysis to establish baseline
3. **Integrate with CI/CD**: Add automated checks to your deployment pipeline
4. **Set Quality Gates**: Define thresholds for build failures (e.g., no critical issues)
5. **Track Trends**: Monitor quality scores over time to measure progress
6. **Prioritize Fixes**: Address critical and high-priority issues first
7. **Iterate**: Re-run analysis regularly to catch new issues early
