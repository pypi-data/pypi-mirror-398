# Architecture Selection Guide

**Version**: 1.0.0
**Last Updated**: 2025-12-26

This guide helps you choose the right architecture pattern for your task. Claude Agent Framework provides 7 pre-built architectures, each optimized for different problem domains.

---

## Quick Selection Flowchart

```
Start: What is your task?
    │
    ├─ Need comprehensive research/data collection?
    │  └─> Research (Fan-out/Fan-in)
    │
    ├─ Have sequential stages with dependencies?
    │  └─> Pipeline (Sequential Chain)
    │
    ├─ Need iterative quality improvement?
    │  └─> Critic-Actor (Generate-Evaluate Loop)
    │
    ├─ Need domain-specific expertise routing?
    │  └─> Specialist Pool (Dynamic Routing)
    │
    ├─ Need balanced analysis from multiple viewpoints?
    │  └─> Debate (Adversarial Deliberation)
    │
    ├─ Need adaptive problem-solving with learning?
    │  └─> Reflexion (Self-Improvement)
    │
    └─ Processing large-scale data in parallel?
       └─> MapReduce (Divide-Conquer)
```

---

## Architecture Comparison Matrix

| Architecture | Parallelism | Iteration | Best For | Example Use Cases |
|--------------|-------------|-----------|----------|-------------------|
| **Research** | High | No | Data gathering, analysis | Market research, competitor analysis, literature review |
| **Pipeline** | None | No | Sequential workflows | Code review, content creation, multi-stage processing |
| **Critic-Actor** | None | Yes | Quality improvement | Content optimization, bug fixing, design refinement |
| **Specialist Pool** | Medium | No | Domain expertise | Technical support, Q&A, multi-domain tasks |
| **Debate** | None | Structured | Decision making | Architecture decisions, risk assessment, options analysis |
| **Reflexion** | None | Yes | Complex problems | Debugging, optimization, adaptive planning |
| **MapReduce** | High | No | Large-scale processing | Log analysis, codebase auditing, data aggregation |

---

## Role-Based Configuration

Each architecture supports **Role-Based Configuration** allowing you to customize agent instances while respecting role constraints.

### Architecture Role Mappings

| Architecture | Roles | Cardinality | Description |
|--------------|-------|-------------|-------------|
| **research** | worker | 1+ | Data gathering workers |
| | processor | 0-1 | Optional data processor |
| | synthesizer | 1 | Result synthesizer |
| **pipeline** | stage_executor | 1+ | Sequential stage executors |
| **critic_actor** | actor | 1 | Content generator |
| | critic | 1 | Quality evaluator |
| **specialist_pool** | specialist | 1+ | Domain experts |
| **debate** | advocate | 2+ | Position advocates |
| | judge | 1 | Decision maker |
| **reflexion** | executor | 1 | Task executor |
| | reflector | 1 | Self-reflector |
| **mapreduce** | mapper | 1+ | Parallel mappers |
| | reducer | 1 | Result reducer |

### Configuration Example

```python
from claude_agent_framework import create_session
from claude_agent_framework.core.roles import AgentInstanceConfig

# Research architecture with custom agents
agents = [
    AgentInstanceConfig(
        name="market-researcher",
        role="worker",
        description="Market data collection",
        prompt_file="prompts/market.txt",
    ),
    AgentInstanceConfig(
        name="tech-researcher",
        role="worker",
        description="Technology trends",
    ),
    AgentInstanceConfig(
        name="analyst",
        role="processor",
        model="sonnet",
    ),
    AgentInstanceConfig(
        name="writer",
        role="synthesizer",
    ),
]

session = create_session("research", agent_instances=agents)
```

For detailed role configuration, see [Role-Based Architecture Guide](../../ROLE_BASED_ARCHITECTURE.md).

---

## Detailed Architecture Profiles

### 1. Research (Fan-out/Fan-in)

**Pattern**: Master orchestrator spawns multiple parallel workers, then aggregates results.

**When to Use**:
- ✅ Task can be decomposed into independent subtasks
- ✅ Need comprehensive coverage from multiple angles
- ✅ Results can be synthesized into unified output
- ✅ Time is valuable (parallel execution)

**When NOT to Use**:
- ❌ Subtasks have dependencies
- ❌ Need strict ordering of operations
- ❌ Single linear path to solution

**Key Characteristics**:
- **Parallelism**: High (5-10 concurrent workers typical)
- **Coordination**: Master aggregates results
- **Communication**: One-way (workers → master)
- **Scalability**: Excellent for I/O-bound tasks

**Example**:
```python
from claude_agent_framework import init

session = init("research")
result = await session.query(
    "Analyze the AI agent market: major players, trends, "
    "pricing models, and competitive landscape"
)
# Spawns: market_analyst, competitor_researcher,
#         pricing_analyst, trend_forecaster
```

**Production Example**: [Competitive Intelligence System](../../examples/production/01_competitive_intelligence/)

---

### 2. Pipeline (Sequential Chain)

**Pattern**: Task flows through ordered stages, each transforming the output.

**When to Use**:
- ✅ Clear sequential stages with dependencies
- ✅ Each stage needs previous stage's output
- ✅ Quality gates between stages
- ✅ Need stage-by-stage validation

**When NOT to Use**:
- ❌ Stages are independent
- ❌ Need parallel exploration
- ❌ Heavy iteration required

**Key Characteristics**:
- **Parallelism**: None (sequential by design)
- **Coordination**: Output → Input chaining
- **Communication**: Linear flow
- **Scalability**: Limited by longest stage

**Example**:
```python
session = init("pipeline")
result = await session.query(
    "Review PR #123: check architecture, code quality, "
    "security, and performance"
)
# Stages: architecture_reviewer → quality_checker →
#         security_scanner → performance_analyzer
```

**Production Example**: [PR Code Review Pipeline](../../examples/production/02_pr_code_review/)

---

### 3. Critic-Actor (Generate-Evaluate Loop)

**Pattern**: Actor generates output, Critic evaluates and provides feedback, repeat until quality threshold met.

**When to Use**:
- ✅ Quality matters more than speed
- ✅ Clear evaluation criteria exist
- ✅ Iterative refinement improves output
- ✅ Need to reach quality threshold

**When NOT to Use**:
- ❌ First draft is sufficient
- ❌ No clear quality metrics
- ❌ Time-sensitive tasks

**Key Characteristics**:
- **Parallelism**: None (sequential iteration)
- **Coordination**: Feedback loop
- **Communication**: Bidirectional (Actor ↔ Critic)
- **Scalability**: Limited by iteration count

**Example**:
```python
session = init("critic_actor")
result = await session.query(
    "Create a marketing email for our new AI product launch. "
    "Target: enterprise CTOs. Tone: professional yet innovative."
)
# Loop: Actor generates → Critic scores (SEO, clarity, tone)
#       → Actor improves → repeat until score ≥ threshold
```

**Production Example**: [Marketing Content Optimizer](../../examples/production/03_marketing_content/)

---

### 4. Specialist Pool (Dynamic Routing)

**Pattern**: Lead agent analyzes query, routes to appropriate specialist(s), orchestrates responses.

**When to Use**:
- ✅ Multi-domain problem space
- ✅ Need expert knowledge in specific areas
- ✅ Query domain can be determined upfront
- ✅ Specialists have non-overlapping expertise

**When NOT to Use**:
- ❌ Single domain problem
- ❌ All tasks require same expertise
- ❌ Routing logic is complex

**Key Characteristics**:
- **Parallelism**: Medium (parallel specialist queries possible)
- **Coordination**: Keyword-based routing
- **Communication**: Hub-and-spoke
- **Scalability**: Good (add specialists as needed)

**Example**:
```python
session = init("specialist_pool")
result = await session.query(
    "User reports: 'Cannot connect to database after upgrading to v2.5. "
    "Error: SSL handshake failed on port 5432'"
)
# Routes to: database_expert (primary), network_specialist (secondary)
```

**Production Example**: [IT Support Platform](../../examples/production/04_it_support/)

---

### 5. Debate (Adversarial Deliberation)

**Pattern**: Proponent and Opponent argue from different viewpoints, Judge evaluates and decides.

**When to Use**:
- ✅ Need balanced analysis
- ✅ Important decisions with trade-offs
- ✅ Risk assessment required
- ✅ Multiple valid perspectives exist

**When NOT to Use**:
- ❌ Clear-cut decisions
- ❌ Single correct answer
- ❌ Time-critical choices

**Key Characteristics**:
- **Parallelism**: None (structured debate rounds)
- **Coordination**: Multi-round argumentation
- **Communication**: Proponent ↔ Opponent → Judge
- **Scalability**: Limited by debate rounds

**Example**:
```python
session = init("debate")
result = await session.query(
    "Should we migrate from monolith to microservices? "
    "Context: 50-person team, 5-year-old codebase, "
    "growing performance issues"
)
# Debate: Proponent (benefits) vs Opponent (risks) →
#         Judge (recommendation with risk assessment)
```

**Production Example**: [Tech Decision Support](../../examples/production/05_tech_decision/)

---

### 6. Reflexion (Self-Improvement)

**Pattern**: Execute strategy, reflect on results, adapt approach, retry with improved strategy.

**When to Use**:
- ✅ Complex problems requiring learning
- ✅ Initial approach may fail
- ✅ Feedback informs better strategies
- ✅ Adaptive problem-solving needed

**When NOT to Use**:
- ❌ Problem has deterministic solution
- ❌ No learning from failures
- ❌ Cannot afford trial-and-error

**Key Characteristics**:
- **Parallelism**: None (sequential learning)
- **Coordination**: Reflect-and-adapt loop
- **Communication**: Executor → Reflector → Executor
- **Scalability**: Limited by reflection depth

**Example**:
```python
session = init("reflexion")
result = await session.query(
    "Debug why test_auth_flow is failing intermittently. "
    "Stack trace: [provided]. Codebase: /path/to/repo"
)
# Cycle: Try debugging strategy → Reflect on results →
#        Adapt strategy → Retry → Eventually find root cause
```

**Production Example**: [Code Debugger](../../examples/production/06_code_debugger/)

---

### 7. MapReduce (Divide-Conquer)

**Pattern**: Split data into chunks, process in parallel (Map), aggregate results (Reduce).

**When to Use**:
- ✅ Large datasets (hundreds of items)
- ✅ Embarrassingly parallel processing
- ✅ Results can be aggregated
- ✅ Per-item processing is independent

**When NOT to Use**:
- ❌ Small datasets (<50 items)
- ❌ Items have dependencies
- ❌ Cannot be aggregated meaningfully

**Key Characteristics**:
- **Parallelism**: Very high (10-50+ parallel mappers)
- **Coordination**: Sharding + aggregation
- **Communication**: Mappers → Reducer
- **Scalability**: Excellent for data processing

**Example**:
```python
session = init("mapreduce")
result = await session.query(
    "Analyze codebase at /path/to/large-repo for technical debt: "
    "code smells, security issues, performance problems, test coverage"
)
# Map: Split 500 files → 10 parallel analyzers
# Reduce: Aggregate + deduplicate + prioritize issues
```

**Production Example**: [Codebase Analysis](../../examples/production/07_codebase_analysis/)

---

## Decision Framework

### Step 1: Identify Task Characteristics

Ask yourself:

1. **Parallelization potential?**
   - High → Research or MapReduce
   - Medium → Specialist Pool
   - None → Pipeline, Critic-Actor, Debate, Reflexion

2. **Iteration requirement?**
   - Yes, quality-focused → Critic-Actor
   - Yes, learning-focused → Reflexion
   - Structured (debate) → Debate
   - No → Research, Pipeline, Specialist Pool, MapReduce

3. **Data scale?**
   - Large (100s-1000s) → MapReduce
   - Medium (10s) → Research
   - Small → Any other

4. **Domain expertise?**
   - Multi-domain → Specialist Pool
   - Single domain → Other architectures

### Step 2: Match Pattern

| Your Task Profile | Recommended Architecture |
|-------------------|--------------------------|
| Parallel + Aggregation | Research |
| Sequential + Stages | Pipeline |
| Iteration + Quality | Critic-Actor |
| Multi-domain + Routing | Specialist Pool |
| Balanced + Decision | Debate |
| Iteration + Learning | Reflexion |
| Large-scale + Parallel | MapReduce |

### Step 3: Validate Choice

Check these criteria:

- ✅ **Efficiency**: Does the pattern avoid unnecessary work?
- ✅ **Clarity**: Is the workflow easy to understand?
- ✅ **Scalability**: Can it handle growth in task complexity?
- ✅ **Cost**: Is the token usage reasonable?

---

## Common Patterns Combinations

You can combine patterns by using the output of one architecture as input to another:

### Pattern 1: Research → Critic-Actor

```python
# Stage 1: Gather data
research_session = init("research")
raw_data = await research_session.query("Research topic X")

# Stage 2: Refine into polished output
critic_session = init("critic_actor")
polished = await critic_session.query(
    f"Create executive summary from: {raw_data}"
)
```

**Use Case**: Market research → Polished report

### Pattern 2: MapReduce → Pipeline

```python
# Stage 1: Analyze all files
mapreduce_session = init("mapreduce")
issues = await mapreduce_session.query("Find all bugs in /repo")

# Stage 2: Prioritize and create tickets
pipeline_session = init("pipeline")
tickets = await pipeline_session.query(
    f"Triage these issues and create JIRA tickets: {issues}"
)
```

**Use Case**: Codebase audit → Issue tracking

### Pattern 3: Specialist Pool → Debate

```python
# Stage 1: Get expert opinions
pool_session = init("specialist_pool")
opinions = await pool_session.query("Evaluate cloud providers")

# Stage 2: Debate pros/cons
debate_session = init("debate")
decision = await debate_session.query(
    f"Decide best option from: {opinions}"
)
```

**Use Case**: Technical evaluation → Decision-making

---

## Anti-Patterns to Avoid

### ❌ Using Research for Sequential Tasks

**Problem**: Forces artificial parallelism where none exists.

**Example**: "Step 1: Read file, Step 2: Process, Step 3: Write output"

**Solution**: Use Pipeline instead.

### ❌ Using Pipeline for Independent Tasks

**Problem**: Serializes work that could be parallel.

**Example**: "Analyze code quality, security, and performance"

**Solution**: Use Research instead.

### ❌ Using Critic-Actor Without Clear Criteria

**Problem**: Loop never converges if Critic has vague standards.

**Example**: "Make this code better" (no definition of "better")

**Solution**: Define concrete metrics or use simple Pipeline.

### ❌ Using MapReduce for Small Datasets

**Problem**: Overhead of sharding exceeds benefits.

**Example**: "Analyze 10 files"

**Solution**: Use Research or simple Pipeline.

### ❌ Using Reflexion for Deterministic Problems

**Problem**: Wastes iterations on problems with known solutions.

**Example**: "Sort this list alphabetically"

**Solution**: Use direct code execution, not agent architecture.

---

## Performance Considerations

### Token Usage

Approximate token costs by architecture (relative scale):

```
MapReduce (large data): ████████████ (12x)
Research (10 workers):  ████████     (8x)
Reflexion (5 iter):     ██████       (6x)
Debate (3 rounds):      █████        (5x)
Critic-Actor (4 iter):  ████         (4x)
Specialist Pool:        ███          (3x)
Pipeline (4 stages):    ███          (3x)
Direct query:           █            (1x baseline)
```

### Execution Time

Approximate time by architecture (for I/O-bound tasks):

```
Pipeline (sequential):   ████████████ (slowest)
Debate (multi-round):    ██████████
Reflexion (iterative):   ██████████
Critic-Actor (iter):     ████████
Specialist Pool:         ████
Research (parallel):     ███
MapReduce (parallel):    ███          (fastest for large data)
```

**Note**: Actual performance depends on:
- Task complexity
- Network latency
- Model selection (haiku/sonnet/opus)
- Number of iterations/workers

---

## Model Selection by Architecture

| Architecture | Recommended Lead Model | Recommended Subagent Model |
|--------------|------------------------|----------------------------|
| Research | Sonnet (orchestration) | Haiku (data gathering) |
| Pipeline | Haiku (simple routing) | Sonnet (analysis stages) |
| Critic-Actor | Sonnet (evaluation) | Sonnet (generation) |
| Specialist Pool | Haiku (routing) | Sonnet (expertise) |
| Debate | Sonnet (moderation) | Sonnet (argumentation) |
| Reflexion | Sonnet (reflection) | Sonnet (execution) |
| MapReduce | Haiku (simple reduce) | Haiku (map tasks) |

**Model Tiers**:
- **Haiku**: Fast, cheap, good for simple tasks
- **Sonnet**: Balanced, recommended for most tasks
- **Opus**: Powerful, expensive, use for complex reasoning

---

## Further Reading

- [Production Examples](../../examples/production/) - Real-world implementations
- [Best Practices](../../BEST_PRACTICES.md) - In-depth technical patterns
- [Custom Architecture Guide](../customization/CUSTOM_ARCHITECTURE.md) - Build your own
- [Performance Tuning](../advanced/PERFORMANCE_TUNING.md) - Optimization techniques

---

## Quick Reference

```python
# Import
from claude_agent_framework import init

# Initialize any architecture
session = init("research")         # or "pipeline", "critic_actor", etc.

# Run query
result = await session.query("Your task here")

# Access results
print(result)
```

**Need help choosing?** Consider:
1. Can tasks run in parallel? → Research/MapReduce
2. Must tasks be sequential? → Pipeline
3. Need quality iteration? → Critic-Actor/Reflexion
4. Need domain experts? → Specialist Pool
5. Need balanced analysis? → Debate

---

**Questions?** See [Examples](../../examples/production/) or [Best Practices](../../BEST_PRACTICES.md).
