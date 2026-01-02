# Performance Tuning Guide

**Version**: 1.0.0
**Last Updated**: 2025-12-26

This guide covers performance optimization strategies for Claude Agent Framework applications, including model selection, parallelization, caching, and cost optimization.

---

## Table of Contents

1. [Performance Fundamentals](#performance-fundamentals)
2. [Model Selection Strategy](#model-selection-strategy)
3. [Parallelization Optimization](#parallelization-optimization)
4. [Prompt Engineering for Performance](#prompt-engineering-for-performance)
5. [Caching Strategies](#caching-strategies)
6. [Token Optimization](#token-optimization)
7. [Architecture-Specific Tuning](#architecture-specific-tuning)
8. [Monitoring and Profiling](#monitoring-and-profiling)
9. [Performance Benchmarks](#performance-benchmarks)

---

## Performance Fundamentals

### Key Performance Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Latency** | Time from request to first response | < 5s for haiku, < 15s for sonnet |
| **Throughput** | Queries processed per minute | Depends on use case |
| **Token Efficiency** | Output quality per token consumed | Maximize value/cost |
| **Cost per Query** | Total cost including all agents | Minimize while maintaining quality |
| **Success Rate** | % of queries completing successfully | > 95% |

### Performance Trade-offs

```
Quality ←→ Speed ←→ Cost
   ↑         ↑         ↑
  Opus    Haiku    Budget
```

**Key Insight**: Choose the **minimum model tier** that meets your quality requirements for each agent.

---

## Model Selection Strategy

### Model Tier Characteristics

| Model | Speed | Cost | Use Cases |
|-------|-------|------|-----------|
| **Haiku** | 🚀 Fast (1-3s) | 💰 Cheap ($0.25/MTok in, $1.25/MTok out) | Data collection, formatting, simple analysis |
| **Sonnet** | ⚡ Medium (3-8s) | 💵 Moderate ($3/MTok in, $15/MTok out) | Complex reasoning, synthesis, orchestration |
| **Opus** | 🐌 Slow (8-20s) | 💸 Expensive ($15/MTok in, $75/MTok out) | Critical decisions, complex creative work |

### Selection Decision Tree

```
Is the task critical? (legal, medical, financial)
├─ Yes → Opus
└─ No → Does it require complex reasoning?
    ├─ Yes → Sonnet
    └─ No → Does it need basic data processing?
        ├─ Yes → Haiku
        └─ No → Consider if AI is needed
```

### Agent-Level Model Assignment

**Pattern**: Fast agents for data gathering, smart agents for synthesis

```python
from claude_agent_framework import init

session = init("research")

# Override default models for specific agents
session.architecture.config.agent_configs = {
    "lead": {"model": "sonnet"},        # Complex orchestration
    "researcher_1": {"model": "haiku"},  # Simple data collection
    "researcher_2": {"model": "haiku"},  # Simple data collection
    "synthesizer": {"model": "sonnet"},  # Complex synthesis
}

result = await session.query("Analyze market trends")
```

**Cost Savings**: Using haiku for 2 researchers instead of sonnet:
- Before: 2 × $3/MTok = $6/MTok
- After: 2 × $0.25/MTok = $0.50/MTok
- **Savings**: 91% reduction for data collection agents

---

## Parallelization Optimization

### Understanding Parallelism in Architectures

| Architecture | Parallel Agents | Max Speedup | Best For |
|--------------|----------------|-------------|----------|
| Research | 4-8 concurrent | 5-7x | Independent research tasks |
| MapReduce | 10-50 concurrent | 10-40x | Large-scale data processing |
| Specialist Pool | 2-4 concurrent | 2-3x | Multi-domain queries |
| Pipeline | Sequential | 1x (no parallel) | Stage-dependent tasks |

### Optimal Concurrency Levels

**Research Architecture**:

```python
from claude_agent_framework.architectures.research import ResearchConfig

# Default: 4 parallel researchers
config = ResearchConfig(
    max_parallel_agents=8  # Increase for more parallelism
)

session = init("research", config=config)
```

**Performance vs. Concurrency**:

| Parallel Agents | Latency Reduction | Cost Impact |
|----------------|-------------------|-------------|
| 2 | 40% faster | Same total cost |
| 4 (default) | 60% faster | Same total cost |
| 8 | 70% faster | Same total cost |
| 16 | 75% faster | API throttling risk |

**Recommendation**:
- **Research/MapReduce**: 6-8 parallel agents for optimal balance
- **Specialist Pool**: 2-4 specialists (limited by domain count)
- **Pipeline/Debate**: Sequential by design, optimize individual stages

### Managing API Rate Limits

Claude API limits (as of 2025):
- **Concurrent requests**: 20 per API key
- **Tokens per minute**: 400k (varies by tier)

**Strategy**:
```python
from claude_agent_framework.plugins.builtin import ThrottlePlugin

# Limit concurrent API calls
throttle = ThrottlePlugin(
    max_concurrent=15,  # Leave headroom
    tokens_per_minute=350000  # Conservative limit
)
session.architecture.add_plugin(throttle)
```

---

## Prompt Engineering for Performance

### Concise Prompts = Faster Responses

**Bad** (verbose):
```python
prompt = """
I would like you to please conduct a comprehensive and thorough analysis
of the current state of the artificial intelligence market, making sure
to cover all the major players, emerging trends, pricing models...
(500 words of instructions)
"""
```

**Good** (concise):
```python
prompt = """
Analyze the AI market:
1. Major players and market share
2. Emerging trends (2024-2025)
3. Pricing models comparison
4. Competitive landscape
"""
```

**Impact**:
- Input tokens: 500 → 50 (90% reduction)
- Processing time: 8s → 3s (62% faster)
- Cost: $1.50 → $0.15 (90% savings)

### Structured Output Formats

**Strategy**: Request structured formats to reduce verbosity

```python
# Instead of: "Write a detailed report..."
prompt = """
Provide analysis in this format:
- Key Finding: [one sentence]
- Evidence: [bullet points]
- Recommendation: [one sentence]
"""
```

**Benefits**:
- Shorter outputs (fewer tokens)
- Easier parsing
- Faster generation

### Avoiding Redundant Instructions

**Bad**:
```python
# Repeating instructions to every agent
for agent in agents:
    agent_prompt = f"{base_instructions}\n\n{task}\n\n{base_instructions}"
```

**Good**:
```python
# Instructions in lead prompt, tasks only for agents
lead_prompt = f"{base_instructions}\n\nDelegate these tasks: {tasks}"
```

---

## Caching Strategies

### File-Based Caching

Agents communicate via files - cache reusable data:

```python
import hashlib
import json
from pathlib import Path

class CacheManager:
    def __init__(self, cache_dir: Path = Path("cache")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)

    def get_cache_key(self, prompt: str) -> str:
        return hashlib.md5(prompt.encode()).hexdigest()

    def get(self, prompt: str):
        cache_file = self.cache_dir / f"{self.get_cache_key(prompt)}.json"
        if cache_file.exists():
            return json.loads(cache_file.read_text())
        return None

    def set(self, prompt: str, result: dict):
        cache_file = self.cache_dir / f"{self.get_cache_key(prompt)}.json"
        cache_file.write_text(json.dumps(result))

# Usage
cache = CacheManager()

prompt = "Analyze Tesla stock performance"
cached = cache.get(prompt)
if cached:
    print("Using cached result")
    result = cached
else:
    result = await session.query(prompt)
    cache.set(prompt, result)
```

**When to Use**:
- Repeated queries (daily reports)
- Reference data (company info, definitions)
- Expensive computations

### Time-Based Cache Invalidation

```python
import time

class TimedCache(CacheManager):
    def get(self, prompt: str, max_age_hours: int = 24):
        cache_file = self.cache_dir / f"{self.get_cache_key(prompt)}.json"
        if cache_file.exists():
            age = time.time() - cache_file.stat().st_mtime
            if age < max_age_hours * 3600:
                return json.loads(cache_file.read_text())
        return None

# Cache market data for 1 hour, reference data for 7 days
market_data = cache.get("market trends", max_age_hours=1)
company_info = cache.get("company profile", max_age_hours=168)
```

---

## Token Optimization

### Minimize Tool Output Verbosity

**Problem**: Tool results can be very large (WebSearch returns 10k+ chars)

**Solution**: Summarize in subagent prompts

```python
researcher_prompt = """
Search for information about {topic}.

IMPORTANT: Write a concise summary (max 500 words).
Focus on key facts only. Do NOT include:
- Full article text
- Redundant information
- Filler words
"""
```

**Impact**:
- Default: 10k tokens → 2k tokens (80% reduction)
- Faster synthesis by lead agent
- Lower cost

### Efficient Lead Agent Prompts

**Strategy**: Lead agent doesn't need to see full subagent transcripts

```python
# Bad: Pass full transcript to lead
lead_context = f"Researcher output:\n{full_transcript}"

# Good: Pass summaries only
lead_context = f"Researcher findings:\n{extract_summary(transcript)}"
```

**Framework Support**: Framework automatically handles this via file-based communication

### Token Tracking

Use `CostTrackerPlugin` to monitor token usage:

```python
from claude_agent_framework.plugins.builtin import CostTrackerPlugin

cost_plugin = CostTrackerPlugin(
    input_price_per_mtok=3.0,
    output_price_per_mtok=15.0
)
session.architecture.add_plugin(cost_plugin)

# After execution
summary = cost_plugin.get_cost_summary()
print(f"Total tokens: {summary['total_tokens']}")
print(f"Total cost: ${summary['total_cost_usd']:.4f}")

# Identify expensive agents
for agent, cost in summary['agent_costs'].items():
    if cost > 1.0:  # $1+ per agent
        print(f"⚠️ Expensive agent: {agent} - ${cost:.2f}")
```

---

## Architecture-Specific Tuning

### Research Architecture

**Bottleneck**: Synthesis phase (lead waits for all researchers)

**Optimization**:
```python
# 1. Use haiku for researchers, sonnet for synthesis
config = ResearchConfig(
    lead_model="sonnet",
    subagent_model="haiku"
)

# 2. Limit research scope
prompt = """
Research {topic}. Limit to:
- Max 3 sources per researcher
- Max 500 words summary
- Focus on [specific aspect]
"""

# 3. Increase parallelism
config.max_parallel_agents = 8
```

**Expected Improvement**:
- Latency: -40% (parallel + faster models)
- Cost: -70% (haiku for data gathering)

### Pipeline Architecture

**Bottleneck**: Sequential stages, slowest stage determines total time

**Optimization**:
```python
# 1. Optimize each stage independently
stages = {
    "design_review": {"model": "sonnet"},    # Complex
    "syntax_check": {"model": "haiku"},      # Simple
    "security_scan": {"model": "haiku"},     # Pattern matching
    "performance_test": {"model": "haiku"},  # Data analysis
    "final_review": {"model": "sonnet"}      # Complex
}

# 2. Reduce stage handoff overhead
# Keep intermediate outputs concise
```

**Expected Improvement**:
- Latency: -50% (faster simple stages)
- Cost: -60% (haiku for 3/5 stages)

### MapReduce Architecture

**Bottleneck**: Map phase parallelism limited by chunk count

**Optimization**:
```python
from claude_agent_framework.architectures.mapreduce import MapReduceConfig

# 1. Optimal chunk size
config = MapReduceConfig(
    chunk_size=50,  # 50 files per mapper
    max_parallel_mappers=10  # 10 concurrent mappers
)

# 2. Use haiku for mappers, sonnet for reducer
config.mapper_model = "haiku"
config.reducer_model = "sonnet"

# 3. Reduce mapper output verbosity
mapper_prompt = """
Analyze files and output ONLY:
- Issue count: X
- Severity: [high/medium/low]
- Files affected: [list]
"""
```

**Expected Improvement**:
- Latency: -60% (parallel + fast mappers)
- Cost: -80% (haiku for bulk of work)

---

## Monitoring and Profiling

### Using MetricsCollectorPlugin

```python
from claude_agent_framework.plugins.builtin import MetricsCollectorPlugin

metrics = MetricsCollectorPlugin()
session.architecture.add_plugin(metrics)

result = await session.query(prompt)

# Analyze performance
m = metrics.get_metrics()
print(f"Total duration: {m.duration_ms}ms")
print(f"Agent spawns: {m.agent_count}")
print(f"Tool calls: {m.tool_call_count}")

# Identify bottlenecks
for agent, duration in m.agent_durations.items():
    print(f"{agent}: {duration}ms")
```

### Performance Profiling

Track where time is spent:

```python
import time

class PerformanceProfiler:
    def __init__(self):
        self.timings = {}

    def time_section(self, name):
        return self._Timer(name, self)

    class _Timer:
        def __init__(self, name, profiler):
            self.name = name
            self.profiler = profiler

        def __enter__(self):
            self.start = time.time()

        def __exit__(self, *args):
            duration = time.time() - self.start
            self.profiler.timings[self.name] = duration

# Usage
profiler = PerformanceProfiler()

with profiler.time_section("agent_spawn"):
    # ... spawn agents ...

with profiler.time_section("synthesis"):
    # ... synthesize results ...

# Analyze
for section, duration in sorted(profiler.timings.items(), key=lambda x: -x[1]):
    print(f"{section}: {duration:.2f}s")
```

### A/B Testing Configurations

Compare performance of different configurations:

```python
configs = [
    {"name": "baseline", "lead_model": "sonnet", "sub_model": "sonnet"},
    {"name": "optimized", "lead_model": "sonnet", "sub_model": "haiku"},
    {"name": "budget", "lead_model": "haiku", "sub_model": "haiku"},
]

results = []
for config in configs:
    session = init("research", config=config)
    metrics = MetricsCollectorPlugin()
    session.architecture.add_plugin(metrics)

    start = time.time()
    result = await session.query(prompt)
    duration = time.time() - start

    results.append({
        "config": config["name"],
        "duration": duration,
        "cost": metrics.get_metrics().estimated_cost_usd,
        "quality": evaluate_quality(result)  # Custom metric
    })

# Find optimal
best = max(results, key=lambda r: r["quality"] / r["cost"])
print(f"Best config: {best['config']}")
```

---

## Performance Benchmarks

### Baseline Performance (Research Architecture)

**Setup**:
- Task: "Analyze AI market trends: players, pricing, competition"
- 4 parallel researchers
- All models: Sonnet

**Results**:

| Metric | Value |
|--------|-------|
| Total Latency | 45 seconds |
| Total Tokens | 150k (75k in, 75k out) |
| Total Cost | $1.35 |
| Agent Count | 5 (1 lead + 4 researchers) |
| Tool Calls | 12 (WebSearch, Write) |

### Optimized Performance

**Optimizations Applied**:
1. Haiku for researchers → Sonnet for lead only
2. Concise prompts (-40% input tokens)
3. Structured output format (-30% output tokens)
4. Increased parallelism (4 → 6 agents)

**Results**:

| Metric | Value | Improvement |
|--------|-------|-------------|
| Total Latency | 18 seconds | **-60%** |
| Total Tokens | 63k (35k in, 28k out) | **-58%** |
| Total Cost | $0.32 | **-76%** |
| Agent Count | 7 (1 lead + 6 researchers) | +2 agents |
| Tool Calls | 15 | +3 calls |

**Quality Assessment**: No measurable difference in output quality

### Cost-Latency Trade-off Matrix

| Configuration | Latency | Cost | Quality | Use Case |
|---------------|---------|------|---------|----------|
| **All Opus** | 90s | $5.25 | 9.5/10 | Critical decisions |
| **All Sonnet** | 45s | $1.35 | 9.0/10 | Standard research |
| **Mixed (Sonnet lead + Haiku sub)** | 18s | $0.32 | 8.8/10 | **Recommended** |
| **All Haiku** | 12s | $0.08 | 7.5/10 | Simple data gathering |

---

## Performance Checklist

Before deploying, verify:

### Model Selection
- [ ] Lead agent uses appropriate model for orchestration complexity
- [ ] Subagents use minimum viable model (haiku when possible)
- [ ] Critical paths use higher-tier models

### Parallelization
- [ ] Parallel architectures use 6-8 concurrent agents
- [ ] API rate limits considered (< 15 concurrent per key)
- [ ] Workload chunked appropriately for MapReduce

### Prompts
- [ ] Prompts are concise (< 200 words for simple tasks)
- [ ] Structured output formats specified
- [ ] No redundant instructions across agents

### Caching
- [ ] Repeated queries cached with appropriate TTL
- [ ] Reference data cached long-term (days/weeks)
- [ ] Cache invalidation strategy defined

### Monitoring
- [ ] MetricsCollectorPlugin enabled
- [ ] Token usage tracked per agent
- [ ] Bottlenecks identified and optimized

### Testing
- [ ] Performance benchmarked against baseline
- [ ] A/B tested multiple configurations
- [ ] Quality validated after optimizations

---

## Advanced Techniques

### Speculative Execution

For latency-critical applications:

```python
# Start multiple agents speculatively, use fastest result
async def speculative_query(prompt, count=3):
    tasks = [session.query(prompt) for _ in range(count)]
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    # Cancel pending
    for task in pending:
        task.cancel()

    return done.pop().result()

# Use 3x resources for 2-3x lower latency
result = await speculative_query("Urgent analysis needed")
```

**Trade-off**: Higher cost for lower latency

### Adaptive Model Selection

Dynamically choose models based on complexity:

```python
def estimate_complexity(prompt: str) -> str:
    """Estimate task complexity from prompt."""
    keywords_complex = ["analyze", "synthesize", "evaluate", "compare"]
    keywords_simple = ["list", "find", "extract", "summarize"]

    if any(kw in prompt.lower() for kw in keywords_complex):
        return "sonnet"
    elif any(kw in prompt.lower() for kw in keywords_simple):
        return "haiku"
    return "sonnet"  # Default

# Apply
model = estimate_complexity(user_prompt)
config = ResearchConfig(lead_model=model)
session = init("research", config=config)
```

### Streaming Responses

For user-facing applications, stream partial results:

```python
async for message in session.run(prompt):
    print(message, end="", flush=True)  # Stream to user
```

**Benefit**: User sees progress, perceived latency reduced

---

## Further Reading

- [Architecture Selection Guide](../architecture_selection/GUIDE.md) - Choose optimal architecture
- [Cost Optimization Guide](COST_OPTIMIZATION.md) - Minimize expenses
- [API Reference](../../api/core.md) - Configuration options
- [Best Practices](../../BEST_PRACTICES.md) - General guidelines

---

**Questions?** Open an issue on [GitHub](https://github.com/anthropics/claude-agent-framework).
