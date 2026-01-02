# Claude Agent Framework

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready multi-agent orchestration framework built on [Claude Agent SDK](https://github.com/anthropics/claude-code-sdk-python). Design, compose, and deploy complex AI workflows with pre-built architecture patterns.

[中文文档](README_CN.md)

## Overview

Claude Agent Framework addresses the fundamental challenge of complex tasks that require diverse specialized capabilities—research, analysis, code generation, decision-making—which cannot be effectively handled by a single LLM prompt. The framework decomposes these tasks into coordinated workflows where a **lead agent orchestrates specialized subagents**, each with focused prompts, constrained tool access, and appropriate model selection.

Built on Claude Agent SDK, it provides:

- **7 Battle-tested Patterns** — Research, Pipeline, Critic-Actor, Specialist Pool, Debate, Reflexion, MapReduce
- **Role-based Architecture** — Separate role definitions from agent instances for flexible configuration
- **Two-layer Prompt System** — Framework prompts + business prompts for reusable workflows
- **Production Plugin System** — Lifecycle hooks for metrics, cost tracking, retry handling
- **Full Observability** — Structured JSONL logging, session tracking, debugging tools
- **Simple API** — Go from concept to working system in minutes

```python
from claude_agent_framework import create_session

session = create_session("research")
async for msg in session.run("Analyze the competitive landscape of AI coding assistants"):
    print(msg)
```

---

## Why Multi-Agent?

Complex tasks require multiple specialized capabilities. A research task needs web searching, data analysis, and report writing—each requiring different tools, prompts, and models. A single LLM prompt cannot effectively handle this.

**The Problem with Monolithic Approaches:**
- Prompt bloat: One prompt trying to do everything becomes unwieldy
- Tool overload: Agent accesses tools it shouldn't use at certain stages
- Quality degradation: Generalist prompts underperform specialized ones
- Cost inefficiency: Expensive models used for simple subtasks

**The Solution: Agent Specialization and Orchestration**

```
User Request
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Lead Agent                               │
│  • Receives request, decomposes into subtasks                    │
│  • Can ONLY use Task tool to dispatch sub-agents                 │
│  • Never performs research/analysis/writing itself               │
└────────────────────────────┬────────────────────────────────────┘
                             │ Task tool calls (parallel)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Worker 1   │  │  Worker 2   │  │  Processor  │  ...         │
│  │  (haiku)    │  │  (haiku)    │  │  (sonnet)   │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         └────────────────┼────────────────┘                      │
│                          ▼                                       │
│                   files/ (filesystem)                            │
│              Loose coupling via files                            │
└─────────────────────────────────────────────────────────────────┘
```

**Key Principles:**

| Principle | Implementation |
|-----------|----------------|
| Separation of Concerns | Lead orchestrates, subagents execute |
| Tool Constraints | Each agent gets only the tools it needs |
| Loose Coupling | Filesystem-based data exchange |
| Cost Optimization | Match model capability to task complexity |

---

## Quick Start

```bash
pip install claude-agent-framework
export ANTHROPIC_API_KEY="your-api-key"
```

```python
from claude_agent_framework import create_session
import asyncio

async def main():
    session = create_session("research")
    async for msg in session.run("Analyze the competitive landscape of AI coding assistants"):
        print(msg)

asyncio.run(main())
```

---

## Architecture Patterns

The framework provides 7 pre-built architecture patterns:

| Architecture | Pattern | When to Use |
|--------------|---------|-------------|
| **research** | Master-worker parallel | Gathering data from multiple sources, market research, literature reviews |
| **pipeline** | Sequential stages | Code review, content workflows, multi-step approvals |
| **critic_actor** | Generate-evaluate loop | Quality improvement, iterative refinement |
| **specialist_pool** | Expert routing | Technical support, Q&A systems, diagnostics |
| **debate** | Pro-con deliberation | Decision support, risk assessment, vendor evaluation |
| **reflexion** | Execute-reflect-improve | Debugging, root cause analysis, optimization |
| **mapreduce** | Parallel map + reduce | Large-scale analysis (500+ files), batch processing |

Each architecture defines **roles** with specific constraints:

```python
# Research architecture roles
worker      → RoleCardinality.ONE_OR_MORE   # Parallel data gatherers
processor   → RoleCardinality.ZERO_OR_ONE   # Optional data processor
synthesizer → RoleCardinality.EXACTLY_ONE   # Required result aggregator
```

---

## Building Business Applications

Building a business application involves 5 steps:

### Step 1: Choose Architecture

Match your workflow pattern to an architecture:
- Parallel data gathering → **Research**
- Sequential stages → **Pipeline**
- Iterative improvement → **Critic-Actor**
- Expert routing → **Specialist Pool**
- Decision analysis → **Debate**
- Trial-and-error → **Reflexion**
- Large-scale processing → **MapReduce**

### Step 2: Define Agent Instances

Map your business roles to architecture roles:

```python
from claude_agent_framework.core.roles import AgentInstanceConfig

agents = [
    AgentInstanceConfig(
        name="market-researcher",      # Business name
        role="worker",                 # Architecture role
        description="Market data collection",
        prompt_file="researcher.txt",
    ),
    AgentInstanceConfig(
        name="report-writer",
        role="synthesizer",
    ),
]
```

### Step 3: Write Business Prompts

Create `prompts/` directory with business-specific context:

```
prompts/lead_agent.txt
```

```markdown
# Competitive Intelligence Coordinator

You are coordinating analysis for ${company_name}.

## Team & Skills
- **Researchers**: Use `competitive-research` Skill for methodology
- **Report Writer**: Uses `report-generation` Skill for formatting

## Deliverables
- Research notes → files/research_notes/
- Final report → files/reports/
```

The framework merges your business prompts with generic framework prompts:

```
Final Prompt = Framework Prompt (generic role rules)
             + Business Prompt (domain context)
             + Template Variables (${company_name} → "Acme Corp")
```

### Step 4: Create Skills (Optional)

Skills provide methodology guidance that agents invoke based on context:

```
.claude/skills/competitive-research/SKILL.md
```

```markdown
---
name: competitive-research
description: Competitive intelligence methodology
---

# Research Focus
- Product & Service Analysis
- Market Position
- Financial Indicators

# Data Collection Priority
1. Market Data (size, share, growth)
2. Financial Data (revenue, valuation)
3. Technical Metrics

# Output Specification
Save to: files/research_notes/{competitor}.md
```

### Step 5: Configure and Run

```python
from pathlib import Path
from claude_agent_framework import create_session
from claude_agent_framework.core.roles import AgentInstanceConfig

agents = [
    AgentInstanceConfig(name="market-researcher", role="worker"),
    AgentInstanceConfig(name="tech-researcher", role="worker"),
    AgentInstanceConfig(name="report-writer", role="synthesizer"),
]

session = create_session(
    "research",
    agent_instances=agents,
    prompts_dir=Path("prompts"),
    template_vars={
        "company_name": "Acme Corp",
        "industry": "Technology",
    },
)

async for msg in session.run("Analyze competitors X, Y, Z"):
    print(msg)
```

---

## Complete Example Structure

```
my_competitive_intel/
├── main.py                           # Entry point
├── config.yaml                       # Configuration
├── prompts/                          # Business prompts
│   ├── lead_agent.txt                # Coordination strategy
│   ├── researcher.txt                # Research methodology
│   └── report_writer.txt             # Report format
└── .claude/skills/                   # Methodology guidance
    ├── competitive-research/SKILL.md
    └── report-generation/SKILL.md
```

See [`examples/production/`](examples/production/) for 7 complete, production-ready examples.

---

## Two-Layer Prompt Architecture

Prompts are composed from two layers:

| Layer | Location | Purpose |
|-------|----------|---------|
| **Framework** | `architectures/*/prompts/` | Generic role capabilities, workflow rules, dispatching guidelines |
| **Business** | Your `prompts/` directory | Domain context, Skills references, deliverables, success criteria |

**Framework Prompt** (generic, reusable):
```markdown
# Role: Research Coordinator

## Core Rules
1. You may ONLY use the Task tool to dispatch sub-agents
2. NEVER perform research, analysis, or writing tasks yourself

## Workflow Phases
1. Plan Phase - Identify parallelizable subtopics
2. Research Phase - Dispatch workers in parallel
3. Processing Phase - Dispatch processor (if configured)
4. Synthesis Phase - Dispatch synthesizer for final output
```

**Business Prompt** (domain-specific):
```markdown
# Competitive Intelligence Coordinator

You are coordinating analysis for ${company_name} in the ${industry} sector.

## Team & Skills
- **Researchers**: Use `competitive-research` Skill
- **Report Writer**: Uses `report-generation` Skill

## Deliverables
- SWOT analysis for each competitor
- Comparative feature matrix
- Strategic recommendations
```

---

## Role-Based Configuration

The framework separates **role definitions** (architecture-level) from **agent instances** (business-level):

```python
# Architecture defines role constraints
class ResearchArchitecture(BaseArchitecture):
    def get_role_definitions(self) -> dict[str, RoleDefinition]:
        return {
            "worker": RoleDefinition(
                role_type=RoleType.WORKER,
                required_tools=["WebSearch"],
                cardinality=RoleCardinality.ONE_OR_MORE,  # 1-N workers
                default_model="haiku",
            ),
            "synthesizer": RoleDefinition(
                role_type=RoleType.SYNTHESIZER,
                required_tools=["Write"],
                cardinality=RoleCardinality.EXACTLY_ONE,  # Exactly 1
                default_model="sonnet",
            ),
        }

# Business configures concrete agents
agents = [
    AgentInstanceConfig(name="market-researcher", role="worker"),
    AgentInstanceConfig(name="tech-researcher", role="worker"),
    AgentInstanceConfig(name="report-writer", role="synthesizer", model="opus"),
]
```

---

## Custom Architecture

```python
from claude_agent_framework import register_architecture, BaseArchitecture
from claude_agent_framework.core.roles import RoleDefinition
from claude_agent_framework.core.types import RoleType, RoleCardinality

@register_architecture("my_workflow")
class MyWorkflow(BaseArchitecture):
    name = "my_workflow"
    description = "Custom workflow for my use case"

    def get_role_definitions(self) -> dict[str, RoleDefinition]:
        return {
            "executor": RoleDefinition(
                role_type=RoleType.EXECUTOR,
                description="Execute tasks",
                required_tools=["Read", "Write", "Bash"],
                cardinality=RoleCardinality.ONE_OR_MORE,
            ),
            "reviewer": RoleDefinition(
                role_type=RoleType.CRITIC,
                description="Review results",
                required_tools=["Read"],
                cardinality=RoleCardinality.EXACTLY_ONE,
            ),
        }

    async def execute(self, prompt, tracker=None, transcript=None):
        # Your orchestration logic here
        ...
```

---

## Plugin System

```python
from claude_agent_framework import create_session
from claude_agent_framework.plugins.builtin import (
    MetricsCollectorPlugin,
    CostTrackerPlugin,
)

session = create_session("research")

# Add metrics tracking
metrics = MetricsCollectorPlugin()
session.architecture.add_plugin(metrics)

# Add cost tracking with budget
cost = CostTrackerPlugin(budget_usd=5.0)
session.architecture.add_plugin(cost)

async for msg in session.run("Analyze market"):
    print(msg)

# Get results
print(f"Cost: ${metrics.get_metrics().estimated_cost_usd:.4f}")
```

---

## Session Lifecycle

```python
# Option 1: Manual management
session = create_session("research")
try:
    async for msg in session.run(prompt):
        process(msg)
finally:
    await session.teardown()

# Option 2: Context manager
async with create_session("research") as session:
    results = await session.query(prompt)
```

---

## Output

Each session generates:

```
logs/session_YYYYMMDD_HHMMSS/
├── transcript.txt      # Human-readable conversation log
└── tool_calls.jsonl    # Structured tool call records

files/
└── <architecture>/     # Architecture-specific outputs
```

---

## Installation

```bash
# Basic
pip install claude-agent-framework

# With PDF generation
pip install "claude-agent-framework[pdf]"

# With chart generation
pip install "claude-agent-framework[charts]"

# Full installation
pip install "claude-agent-framework[all]"
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Best Practices](docs/BEST_PRACTICES.md) | Pattern selection and implementation tips |
| [Role-Based Architecture](docs/ROLE_BASED_ARCHITECTURE.md) | Role types, constraints, and agent instantiation |
| [Prompt Writing Guide](docs/PROMPT_WRITING_GUIDE.md) | Two-layer prompt architecture |
| [Core API Reference](docs/api/core.md) | `create_session()`, `AgentSession`, `BaseArchitecture` |
| [Plugin API Reference](docs/api/plugins.md) | Plugin system and lifecycle hooks |
| [Architecture Selection](docs/guides/architecture_selection/GUIDE.md) | Choose the right architecture |

---

## Production Examples

All 7 examples in [`examples/production/`](examples/production/) are complete and production-ready:

| Example | Architecture | Business Scenario |
|---------|--------------|-------------------|
| [01_competitive_intelligence](examples/production/01_competitive_intelligence/) | Research | SaaS competitive analysis |
| [02_pr_code_review](examples/production/02_pr_code_review/) | Pipeline | Automated PR review |
| [03_marketing_content](examples/production/03_marketing_content/) | Critic-Actor | Marketing copy optimization |
| [04_it_support](examples/production/04_it_support/) | Specialist Pool | IT support routing |
| [05_tech_decision](examples/production/05_tech_decision/) | Debate | Technical decision support |
| [06_code_debugger](examples/production/06_code_debugger/) | Reflexion | Adaptive debugging |
| [07_codebase_analysis](examples/production/07_codebase_analysis/) | MapReduce | Large codebase analysis |

### Common Production Patterns

All production examples follow these proven patterns:

| Pattern | Implementation |
|---------|----------------|
| **Configuration-Driven** | YAML config files with validation, environment-specific settings, no hardcoded values |
| **Structured Results** | Consistent JSON schema, programmatic access, multiple formats (JSON/Markdown/PDF) |
| **Robust Error Handling** | Try/catch at I/O boundaries, graceful degradation, detailed error context |
| **Comprehensive Logging** | JSONL tool tracking, human-readable transcripts, session-based organization |
| **Production Testing** | Unit + integration tests, mock external dependencies, 100% pass requirement |

### When to Use Each Architecture

| Architecture | Use When | Example Scenarios |
|--------------|----------|-------------------|
| **Research** | Gathering data from multiple independent sources in parallel | Market research, competitive analysis, literature reviews |
| **Pipeline** | Clear sequential stages with quality gates | Code review, content workflows, multi-step approvals |
| **Critic-Actor** | Output needs iterative improvement against defined criteria | Content optimization, code refactoring, design iteration |
| **Specialist Pool** | Requests need routing to domain experts | Technical support, Q&A systems, diagnostics |
| **Debate** | Decision requires balanced pro/con analysis | Technology selection, architecture decisions, vendor evaluation |
| **Reflexion** | Problem requires trial-and-error with learning | Debugging, root cause analysis, optimization |
| **MapReduce** | Large dataset (500+ files) needs parallel processing | Codebase analysis, batch processing, large-scale audits |

---

## Requirements

- Python 3.10+
- `ANTHROPIC_API_KEY` environment variable

## License

MIT License - see [LICENSE](LICENSE)
