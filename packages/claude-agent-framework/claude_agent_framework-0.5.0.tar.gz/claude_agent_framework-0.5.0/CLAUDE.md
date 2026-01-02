# CLAUDE.md

Development guidance for Claude Agent Framework.

## Project Overview

Claude Agent Framework is a multi-architecture agent framework built on Claude Agent SDK. It provides 7 pre-built architecture patterns for common multi-agent workflows including research, development, decision support, and large-scale analysis.

### Core Design

The framework solves the problem of complex tasks requiring multiple specialized capabilities through **agent specialization and orchestration**:

- **Lead Agent**: Orchestrates workflow, decomposes tasks, dispatches subagents
- **Subagents**: Execute specific tasks with focused prompts and minimal tool access
- **Communication**: Agents exchange data via filesystem (loose coupling)
- **Observability**: Hook mechanism captures all tool calls for debugging and audit

### Key Principles

| Principle | Implementation |
|-----------|----------------|
| Separation of Concerns | Lead orchestrates, subagents execute |
| Tool Constraints | Each agent gets only needed tools |
| Loose Coupling | Filesystem-based data exchange |
| Cost Optimization | Match model to task complexity |

## Important Notes

- **Bilingual Documentation Required**: README and BEST_PRACTICES must have both English and Chinese versions (README.md/README_CN.md, BEST_PRACTICES.md/BEST_PRACTICES_CN.md)
- **Documentation Sync**: When major features are added or modified, all related documentation files must be updated synchronously

## Skills Support

**Skills are a built-in feature of Claude Agent SDK**, not a custom implementation of this framework.

- **Reference**: https://platform.claude.com/docs/en/agent-sdk/skills
- **Mechanism**: Skills are filesystem artifacts (`.claude/skills/*/SKILL.md`) automatically discovered and invoked by Claude
- **Loading**: Configured via `setting_sources=["user", "project"]` in SDK options
- **Enabling**: Add `"Skill"` to `allowed_tools` configuration

## Development Workflow

### Git Commit Strategy

**IMPORTANT**: Commit changes after each phase completion.

- ✅ **DO** commit immediately after completing each implementation phase
- ✅ **DO** include comprehensive commit messages with phase details
- ✅ **DO** ensure all tests pass before committing
- ✅ **DO** update work log (docs/dev/WORK_LOG.md) before committing

**Rationale**: Phase-by-phase commits provide:
- Clear development history and progress tracking
- Easy rollback to specific phase if needed
- Better code review and collaboration
- Atomic, well-documented changes

## Development Commands

```bash
# Sync dependencies (creates/updates uv.lock)
uv sync

# Sync with all optional groups
uv sync --all-groups

# Install package in editable mode
uv pip install -e .

# Install all dependencies (including dev, pdf, charts)
uv pip install -e ".[all]"

# Run tests
uv run pytest tests/ -v

# Run tests with coverage
uv run pytest tests/ -v --cov=claude_agent_framework --cov-report=html

# Lint code
uv run ruff check .

# Format code
uv run ruff format .

# Type check
uv run mypy claude_agent_framework

# Or use make commands (see Makefile)
make sync      # Sync dependencies
make dev       # Install with all groups
make test      # Run tests
make lint      # Lint code
make format    # Format code
```

## Project Structure

```
src/claude_agent_framework/
├── __init__.py              # Package exports (v0.4.0)
├── session.py               # create_session() entry point
├── cli.py                   # Command-line interface
├── architectures/           # 7 built-in architecture implementations
│   ├── research/            # ResearchArchitecture - master-worker pattern
│   ├── pipeline/            # PipelineArchitecture - sequential stages
│   ├── critic_actor/        # CriticActorArchitecture - generate-evaluate loop
│   ├── specialist_pool/     # SpecialistPoolArchitecture - expert routing
│   ├── debate/              # DebateArchitecture - pro-con deliberation
│   ├── reflexion/           # ReflexionArchitecture - execute-reflect cycle
│   └── mapreduce/           # MapReduceArchitecture - parallel map-reduce
├── config/                  # Configuration system
│   ├── __init__.py          # Exports FrameworkConfig, AgentConfig
│   ├── legacy.py            # Legacy configuration classes
│   └── schema.py            # Pydantic validation schemas
├── core/                    # Core abstractions
│   ├── __init__.py          # Core exports
│   ├── base.py              # BaseArchitecture, AgentDefinitionConfig, AgentModelConfig
│   ├── prompt.py            # PromptComposer - two-layer prompt composition
│   ├── registry.py          # @register_architecture, get_architecture, list_architectures
│   ├── roles.py             # RoleDefinition, AgentInstanceConfig, RoleRegistry
│   ├── session.py           # AgentSession, CompositeSession
│   └── types.py             # RoleType, RoleCardinality, ModelType, ArchitectureType
├── dynamic/                 # Dynamic agent registry (runtime registration)
├── metrics/                 # Performance tracking and cost estimation
├── observability/           # Structured logging and visualization
├── plugins/                 # Plugin system with lifecycle hooks
│   ├── base.py              # BasePlugin, PluginManager
│   └── builtin/             # MetricsCollector, CostTracker, RetryHandler
├── utils/                   # Utilities
│   ├── __init__.py          # Utils exports
│   ├── tracker.py           # SubagentTracker, SubagentSession, ToolCallRecord
│   ├── transcript.py        # TranscriptWriter, QuietTranscriptWriter, setup_session
│   ├── message_handler.py   # process_message, process_assistant_message
│   └── helpers.py           # quick_query convenience function
├── files/                   # Working directory for outputs
└── logs/                    # Session logs
```

## Key Patterns

### 1. Simplified Initialization

```python
from claude_agent_framework import create_session

session = create_session("research")  # Returns ready-to-use session
async for msg in session.run("Analyze AI trends"):
    print(msg)
```

### 2. Architecture Registration

```python
from claude_agent_framework import register_architecture, BaseArchitecture
from claude_agent_framework.core.roles import RoleDefinition
from claude_agent_framework.core.types import RoleType, RoleCardinality

@register_architecture("my_arch")
class MyArchitecture(BaseArchitecture):
    name = "my_arch"
    description = "Custom architecture"

    def get_role_definitions(self) -> dict[str, RoleDefinition]:
        return {
            "worker": RoleDefinition(
                role_type=RoleType.WORKER,
                description="Execute tasks",
                required_tools=["Read", "Write"],
                cardinality=RoleCardinality.ONE_OR_MORE,
            ),
        }

    async def execute(self, prompt, tracker=None, transcript=None):
        # Implementation
        ...
```

### 3. Session Lifecycle

```python
# Manual management
session = create_session("research")
try:
    async for msg in session.run(prompt):
        process(msg)
finally:
    await session.teardown()

# Context manager (AgentSession implements __aenter__/__aexit__)
async with create_session("research") as session:
    results = await session.query(prompt)
```

## Adding New Architectures

1. Create directory: `src/claude_agent_framework/architectures/new_arch/`
2. Create files:
   - `__init__.py` - exports
   - `config.py` - architecture-specific config
   - `orchestrator.py` - main architecture class
   - `prompts/` - agent prompts

3. Implement orchestrator:
```python
from claude_agent_framework.core import register_architecture, BaseArchitecture
from claude_agent_framework.core.roles import RoleDefinition
from claude_agent_framework.core.types import RoleType, RoleCardinality

@register_architecture("new_arch")
class NewArchitecture(BaseArchitecture):
    name = "new_arch"
    description = "Description of the architecture"

    def get_role_definitions(self) -> dict[str, RoleDefinition]:
        return {
            "executor": RoleDefinition(
                role_type=RoleType.EXECUTOR,
                description="Execute tasks",
                required_tools=["Bash", "Write"],
                optional_tools=["Read", "Glob"],
                cardinality=RoleCardinality.ONE_OR_MORE,
                default_model="haiku",
                prompt_file="executor.txt",
            ),
        }

    async def execute(self, prompt, tracker=None, transcript=None):
        # Implementation using ClaudeSDKClient
        ...
```

4. Add import to `architectures/__init__.py`
5. Add tests in `tests/architectures/`

## Role-Based Architecture

The framework uses a Role-Based Architecture that separates role definitions from agent instances.

### Core Types

```python
from claude_agent_framework.core.types import RoleType, RoleCardinality

# Role types define semantic roles
RoleType.COORDINATOR   # Orchestrates workflow
RoleType.WORKER        # Parallel task execution
RoleType.PROCESSOR     # Data processing
RoleType.SYNTHESIZER   # Result aggregation
RoleType.CRITIC        # Evaluates output
RoleType.JUDGE         # Makes final decisions
RoleType.SPECIALIST    # Domain-specific expert
RoleType.ADVOCATE      # Argues position
RoleType.EXECUTOR      # Executes actions
RoleType.REFLECTOR     # Reflects on results
RoleType.MAPPER        # Parallel mapping
RoleType.REDUCER       # Result reduction
RoleType.STAGE_EXECUTOR # Sequential stage execution

# Cardinality defines quantity constraints
RoleCardinality.EXACTLY_ONE   # Must have exactly 1
RoleCardinality.ONE_OR_MORE   # At least 1 (1-N)
RoleCardinality.ZERO_OR_MORE  # Any number (0-N)
RoleCardinality.ZERO_OR_ONE   # Optional (0-1)
```

### Implementing Role Definitions

When creating a new architecture, implement `get_role_definitions()`:

```python
from claude_agent_framework.core.roles import RoleDefinition
from claude_agent_framework.core.types import RoleType, RoleCardinality

@register_architecture("my_arch")
class MyArchitecture(BaseArchitecture):
    def get_role_definitions(self) -> dict[str, RoleDefinition]:
        return {
            "executor": RoleDefinition(
                role_type=RoleType.EXECUTOR,
                description="Execute tasks",
                required_tools=["Bash", "Write"],
                optional_tools=["Read", "Glob"],
                cardinality=RoleCardinality.ONE_OR_MORE,
                default_model="haiku",
                prompt_file="executor.txt",
            ),
            "reviewer": RoleDefinition(
                role_type=RoleType.CRITIC,
                description="Review results",
                required_tools=["Read"],
                cardinality=RoleCardinality.EXACTLY_ONE,
                default_model="sonnet",
                prompt_file="reviewer.txt",
            ),
        }
```

### Using Role-Based Configuration

```python
from claude_agent_framework import create_session
from claude_agent_framework.core.roles import AgentInstanceConfig

agents = [
    AgentInstanceConfig(name="task-runner", role="executor"),
    AgentInstanceConfig(name="code-checker", role="reviewer", model="opus"),
]

session = create_session("my_arch", agent_instances=agents)
```

For complete documentation, see [docs/ROLE_BASED_ARCHITECTURE.md](docs/ROLE_BASED_ARCHITECTURE.md).

## Two-Layer Prompt Architecture

The framework uses a **two-layer prompt composition** pattern that separates generic orchestration logic from business-specific context.

### Layer Overview

| Layer | Location | Purpose |
|-------|----------|---------|
| **Framework** | `architectures/*/prompts/` | Generic role capabilities, workflow phases, dispatching rules |
| **Business** | `examples/production/*/prompts/` | Domain context, template variables, Skills references |

### Prompt Composition Flow

```
┌─────────────────────────────────────────┐
│         Business Layer Prompt            │
│  (examples/production/*/prompts/)        │
│  - Domain-specific context               │
│  - Template variables: ${company}        │
│  - Skills references                     │
└────────────────────┬────────────────────┘
                     │ merged with
┌────────────────────▼────────────────────┐
│         Framework Layer Prompt           │
│  (architectures/*/prompts/)              │
│  - Role definition                       │
│  - Core rules                            │
│  - Workflow phases                       │
│  - Dispatching guidelines                │
└─────────────────────────────────────────┘
```

### Key Design Principles

1. **Framework prompts are generic**: Use role terminology (`actor role agent`) not specific names
2. **Business prompts add context**: Template variables, Skills, file locations
3. **Skills provide methodology**: Detailed frameworks invoked by agents based on context
4. **Template variables enable reuse**: `${company_name}`, `${quality_threshold}`

For complete prompt writing guide, see [docs/PROMPT_WRITING_GUIDE.md](docs/PROMPT_WRITING_GUIDE.md).

## Workflow Driving Mechanism

The framework uses a **Lead Agent + Task Tool** pattern to drive multi-agent workflows:

```
┌─────────────────────────────────────────────────────────────────┐
│                         Lead Agent                               │
│  (Receives user request, orchestrates workflow)                  │
│                                                                  │
│  System Prompt = Framework Prompt + Business Prompt              │
│  Available Tool = Task (ONLY)                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Task tool calls
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Sub-Agents                                 │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Worker 1   │  │  Worker 2   │  │  Processor  │  ...         │
│  │  (parallel) │  │  (parallel) │  │             │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         └────────────────┼────────────────┘                      │
│                          │                                       │
│                          ▼                                       │
│                   files/ (filesystem)                            │
│              (Loose coupling via files)                          │
└─────────────────────────────────────────────────────────────────┘
```

### Key Mechanism

1. **Lead Agent Constraint**: Lead agent can ONLY use Task tool to dispatch sub-agents
   - Cannot perform research, analysis, or writing tasks itself
   - Only orchestrates and coordinates

2. **Task Tool Dispatching**: Lead agent dispatches sub-agents by calling Task tool
   ```python
   # Framework prompt rule (in architectures/research/prompts/lead_agent.txt):
   # "You may ONLY use the Task tool to dispatch sub-agents"
   # "Dispatch multiple `worker` role agents in parallel"
   ```

3. **Filesystem Communication**: Sub-agents exchange data via files
   - Workers save results to `files/research_notes/`
   - Processors read from files, write to `files/charts/`
   - Synthesizers read all files, generate final output

4. **Parallel Execution**: Multiple Task tool calls in one response = parallel execution
   ```python
   # Lead agent can dispatch multiple workers simultaneously:
   # Task(agent="researcher_competitor_a", prompt="Research competitor A...")
   # Task(agent="researcher_competitor_b", prompt="Research competitor B...")
   ```

## Building Business Applications

### Step-by-Step Guide

Building a business application involves 5 key steps:

```
┌──────────────────────────────────────────────────────────────────────┐
│  Step 1: Choose Architecture                                          │
│  ──────────────────────────────────────────────────────────────────  │
│  Match your workflow pattern to an architecture:                      │
│  - Parallel data gathering → Research                                 │
│  - Sequential stages → Pipeline                                       │
│  - Iterative improvement → Critic-Actor                               │
│  - Expert routing → Specialist Pool                                   │
│  - Decision analysis → Debate                                         │
│  - Trial-and-error → Reflexion                                        │
│  - Large-scale processing → MapReduce                                 │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Step 2: Define Agent Instances                                       │
│  ──────────────────────────────────────────────────────────────────  │
│  Map your business roles to architecture roles:                       │
│                                                                       │
│  agents = [                                                           │
│      AgentInstanceConfig(                                             │
│          name="market-researcher",    # Business name                 │
│          role="worker",               # Architecture role             │
│          description="Market data collection",                        │
│          prompt_file="researcher.txt",                                │
│      ),                                                               │
│      AgentInstanceConfig(name="report-writer", role="synthesizer"),   │
│  ]                                                                    │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Step 3: Write Business Prompts                                       │
│  ──────────────────────────────────────────────────────────────────  │
│  Create prompts/ directory with business-specific context:            │
│                                                                       │
│  prompts/lead_agent.txt:                                              │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ # Competitive Intelligence Coordinator                         │  │
│  │                                                                 │  │
│  │ You are coordinating analysis for ${company_name}.             │  │
│  │                                                                 │  │
│  │ ## Team & Skills                                                │  │
│  │ - **Researchers**: Use `competitive-research` Skill            │  │
│  │ - **Report Writer**: Uses `report-generation` Skill            │  │
│  │                                                                 │  │
│  │ ## Deliverables                                                 │  │
│  │ - Research notes → files/research_notes/                        │  │
│  │ - Final report → files/reports/                                 │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Step 4: Create Skills                                                │
│  ──────────────────────────────────────────────────────────────────  │
│  Skills provide methodology guidance in .claude/skills/{name}/SKILL.md│
│                                                                       │
│  .claude/skills/competitive-research/SKILL.md:                        │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ ---                                                            │  │
│  │ name: competitive-research                                     │  │
│  │ description: Competitive intelligence methodology              │  │
│  │ ---                                                            │  │
│  │                                                                 │  │
│  │ # Research Focus                                                │  │
│  │ - Product & Service Analysis                                    │  │
│  │ - Market Position                                               │  │
│  │ - Financial Indicators                                          │  │
│  │                                                                 │  │
│  │ # Data Collection Priority                                      │  │
│  │ 1. Market Data (size, share, growth)                            │  │
│  │ 2. Financial Data (revenue, valuation)                          │  │
│  │ 3. Technical Metrics                                            │  │
│  │                                                                 │  │
│  │ # Output Specification                                          │  │
│  │ Save to: files/research_notes/{competitor}.md                   │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Step 5: Configure and Run                                            │
│  ──────────────────────────────────────────────────────────────────  │
│                                                                       │
│  session = create_session(                                            │
│      "research",                          # Architecture              │
│      agent_instances=agents,              # Business agents           │
│      prompts_dir=Path("prompts"),         # Business prompts          │
│      template_vars={                      # Dynamic values            │
│          "company_name": "Acme Corp",                                 │
│          "industry": "Technology",                                    │
│      },                                                               │
│  )                                                                    │
│                                                                       │
│  async for msg in session.run("Analyze competitors X, Y, Z"):         │
│      print(msg)                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

### Complete Example: Competitive Intelligence

```
examples/production/01_competitive_intelligence/
├── main.py                           # Application entry point
├── config.yaml                       # Business configuration
├── prompts/                          # Business prompts (Step 3)
│   ├── lead_agent.txt                # Coordination strategy
│   ├── researcher.txt                # Research methodology
│   ├── data_analyst.txt              # Analysis guidelines
│   └── report_writer.txt             # Report format
├── .claude/skills/                   # Skills (Step 4)
│   ├── competitive-research/SKILL.md # Research methodology
│   ├── data-analysis/SKILL.md        # Analysis frameworks
│   └── report-generation/SKILL.md    # Report standards
└── README.md
```

### Prompt Composition Flow

```
                    Final Agent System Prompt
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌───────────────────┐               ┌───────────────────┐
│ Framework Prompt  │               │ Business Prompt   │
│ (Generic Role)    │   + merged +  │ (Domain Context)  │
└───────────────────┘               └───────────────────┘
        │                                       │
        ▼                                       ▼
architectures/research/              examples/production/
prompts/lead_agent.txt               01_competitive_intelligence/
                                     prompts/lead_agent.txt
┌─────────────────────┐             ┌─────────────────────┐
│ # Research          │             │ # Competitive Intel │
│ # Coordinator       │             │ # Coordinator       │
│                     │             │                     │
│ ## Core Rules       │             │ You are coordinating│
│ 1. ONLY use Task    │             │ analysis for        │
│ 2. NEVER research   │             │ ${company_name}     │
│    yourself         │             │                     │
│                     │             │ ## Team & Skills    │
│ ## Workflow Phases  │             │ - Researchers: use  │
│ 1. Plan Phase       │             │   `competitive-     │
│ 2. Research Phase   │             │   research` Skill   │
│ 3. Processing Phase │             │                     │
│ 4. Synthesis Phase  │             │ ## Deliverables     │
│                     │             │ - Research notes    │
│ ## Dispatching      │             │ - Final report (PDF)│
│ Use agent names as  │             │                     │
│ configured          │             │ ## Success Criteria │
└─────────────────────┘             └─────────────────────┘
        │                                       │
        └───────────────────┬───────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Template Variable     │
                │ Substitution          │
                │ ${company_name} →     │
                │ "Acme Corp"           │
                └───────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Final System Prompt   │
                │ (Ready for Claude)    │
                └───────────────────────┘
```

### Skills Integration

Skills are **Claude Agent SDK built-in feature** that provide methodology guidance:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Agent Runtime                                 │
│                                                                      │
│  ┌──────────────────┐                                                │
│  │  System Prompt   │◄── Contains reference: "Use `competitive-      │
│  │  (merged)        │     research` Skill for methodology"           │
│  └────────┬─────────┘                                                │
│           │                                                          │
│           ▼                                                          │
│  ┌──────────────────┐                                                │
│  │  Claude Model    │                                                │
│  │  (Agent)         │                                                │
│  └────────┬─────────┘                                                │
│           │                                                          │
│           │ Automatically discovers and invokes based on context     │
│           ▼                                                          │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  .claude/skills/competitive-research/SKILL.md                │   │
│  │                                                               │   │
│  │  # Research Focus                                             │   │
│  │  - Product Analysis                                           │   │
│  │  - Market Position                                            │   │
│  │  - Financial Indicators                                       │   │
│  │                                                               │   │
│  │  # Output Specification                                       │   │
│  │  Save to: files/research_notes/{competitor}.md               │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

**Key Points**:
- Skills are filesystem artifacts (`.claude/skills/*/SKILL.md`)
- Automatically discovered by Claude when referenced in prompts
- Provide detailed methodology without bloating the system prompt
- Enable reusable domain knowledge across agents

## Production Example Design

Each production example demonstrates a complete business application of an architecture.

### Example Directory Structure

```
examples/production/{example_name}/
├── main.py                      # Entry point with agent_instances
├── config.yaml                  # Configuration with template variables
├── prompts/
│   ├── lead_agent.txt           # Business context for coordinator
│   └── {agent}.txt              # Business context for each role
├── .claude/skills/
│   └── {skill}/SKILL.md         # Methodology guidance
└── README.md                    # Documentation
```

### Agent Instance Configuration Pattern

```python
from claude_agent_framework.core.roles import AgentInstanceConfig

def _build_agent_instances(config: dict) -> list[AgentInstanceConfig]:
    return [
        AgentInstanceConfig(
            name="{business_agent_name}",  # e.g., "content_creator"
            role="{framework_role}",        # e.g., "actor"
            model=config.get("model", "sonnet"),
        ),
        # ... more agents
    ]

session = create_session(
    "{architecture}",
    agent_instances=_build_agent_instances(config),
    prompts_dir=Path(__file__).parent / "prompts",
    template_vars=template_vars,
)
```

## Code Style

- **Python version**: 3.10+
- **Line length**: 100 characters (enforced by ruff)
- **Type hints**: Required for all public APIs
- **Docstrings**: Google-style for public APIs
- **Async**: All I/O operations use async/await
- **Imports**: Use `TYPE_CHECKING` to avoid circular imports

## Testing

```python
import pytest
from claude_agent_framework import create_session

@pytest.mark.asyncio
async def test_architecture():
    session = create_session("research")
    assert session.architecture.name == "research"
    await session.teardown()
```

## Architecture Overview

| Architecture | Pattern | Use Case | Production Example | Status |
|--------------|---------|----------|-------------------|--------|
| research | Master-worker parallel | Deep research, data gathering | 01_competitive_intelligence | ✅ Complete |
| pipeline | Sequential stages | Code review, content creation | 02_pr_code_review | ✅ Complete |
| critic_actor | Generate-evaluate loop | Quality improvement, optimization | 03_marketing_content | ✅ Complete |
| specialist_pool | Expert routing | Technical support, Q&A | 04_it_support | ✅ Complete |
| debate | Pro-con deliberation | Decision support, risk assessment | 05_tech_decision | ✅ Complete |
| reflexion | Execute-reflect-improve | Complex problem solving | 06_code_debugger | ✅ Complete |
| mapreduce | Parallel map + reduce | Large-scale analysis | 07_codebase_analysis | ✅ Complete |

## Architecture Role Definitions

### Research Architecture
| Role | Type | Cardinality | Required Tools | Default Model |
|------|------|-------------|----------------|---------------|
| worker | WORKER | ONE_OR_MORE | WebSearch | haiku |
| processor | PROCESSOR | ZERO_OR_ONE | Read, Write | haiku |
| synthesizer | SYNTHESIZER | EXACTLY_ONE | Write | haiku |

### Pipeline Architecture
| Role | Type | Cardinality | Required Tools | Default Model |
|------|------|-------------|----------------|---------------|
| stage | EXECUTOR | ONE_OR_MORE | Read | haiku |

### Critic-Actor Architecture
| Role | Type | Cardinality | Required Tools | Default Model |
|------|------|-------------|----------------|---------------|
| actor | EXECUTOR | EXACTLY_ONE | Read, Write, Edit | haiku |
| critic | CRITIC | EXACTLY_ONE | Read | sonnet |

### Specialist Pool Architecture
| Role | Type | Cardinality | Required Tools | Default Model |
|------|------|-------------|----------------|---------------|
| specialist | SPECIALIST | ONE_OR_MORE | Read | haiku |

### Debate Architecture
| Role | Type | Cardinality | Required Tools | Default Model |
|------|------|-------------|----------------|---------------|
| proponent | ADVOCATE | EXACTLY_ONE | Read | haiku |
| opponent | ADVOCATE | EXACTLY_ONE | Read | haiku |
| judge | JUDGE | EXACTLY_ONE | Read | sonnet |

### Reflexion Architecture
| Role | Type | Cardinality | Required Tools | Default Model |
|------|------|-------------|----------------|---------------|
| executor | EXECUTOR | EXACTLY_ONE | Read, Write, Edit, Bash | haiku |
| reflector | REFLECTOR | EXACTLY_ONE | Read | sonnet |

### MapReduce Architecture
| Role | Type | Cardinality | Required Tools | Default Model |
|------|------|-------------|----------------|---------------|
| mapper | WORKER | ONE_OR_MORE | Read, Glob, Grep | haiku |
| reducer | SYNTHESIZER | EXACTLY_ONE | Read, Write | sonnet |

## Production Implementation Patterns

The framework includes **7 production-grade examples** (`examples/production/`) demonstrating real-world business scenarios. **All examples are complete and production-ready**, each showcasing proven implementation patterns:

**Location**: `examples/production/`
**Status**: All 7 examples complete
**Documentation**: Each includes bilingual README (EN/CN), config guide, architecture docs

### Common Patterns

1. **Configuration-Driven Design**
   - All parameters in YAML config files with validation
   - Environment-specific settings (development, staging, production)
   - No hardcoded values in source code

2. **Structured Results**
   - Consistent JSON output schema across all examples
   - Programmatic access for automation and integration
   - Multiple output formats (JSON, Markdown, PDF)

3. **Robust Error Handling**
   - Try/catch blocks at all I/O boundaries
   - Graceful degradation (partial results better than total failure)
   - Detailed error messages with context
   - Resource cleanup in finally blocks

4. **Comprehensive Logging**
   - Structured JSONL for tool call tracking
   - Human-readable transcript logs
   - Separate log levels (DEBUG, INFO, WARNING, ERROR)
   - Session-based log organization

5. **Production Testing**
   - Unit tests for core functions
   - Integration tests for end-to-end workflows
   - Mock-based testing for external dependencies
   - 100% test pass requirement before release

### When to Use Each Pattern

**Research Architecture** - Use when:
- Task requires gathering data from multiple independent sources
- Sources can be queried in parallel
- Final result needs aggregation from all sources
- Example: Market research, competitive analysis, literature reviews

**Pipeline Architecture** - Use when:
- Task has clear sequential stages
- Each stage depends on previous stage's output
- Need quality gates between stages
- Example: Code review, content creation workflows, multi-step approval processes

**Critic-Actor Architecture** - Use when:
- Output quality needs iterative improvement
- Can define clear evaluation criteria
- Have quality threshold to meet
- Example: Content optimization, code refactoring, design iteration

**Specialist Pool Architecture** - Use when:
- Requests need routing to domain experts
- Can define keywords/criteria for routing
- Multiple specialists may be needed for complex requests
- Example: Technical support, Q&A systems, diagnostic systems

**Debate Architecture** - Use when:
- Decision requires examining tradeoffs
- Want balanced pro/con analysis
- Need evidence-based evaluation
- Example: Technology selection, architecture decisions, vendor evaluation

**Reflexion Architecture** - Use when:
- Problem requires trial-and-error exploration
- Can learn from failed attempts
- Strategy needs adapting based on results
- Example: Debugging, root cause analysis, optimization problems

**MapReduce Architecture** - Use when:
- Large dataset needs processing (500+ files)
- Work can be divided into independent chunks
- Results need aggregation and deduplication
- Example: Codebase analysis, batch processing, large-scale audits

## Related Documentation

- README.md / README_CN.md - User documentation (English/Chinese)
- docs/BEST_PRACTICES.md / docs/BEST_PRACTICES_CN.md - Best practices guide (English/Chinese)
- docs/ROLE_BASED_ARCHITECTURE.md / docs/ROLE_BASED_ARCHITECTURE_CN.md - Role-based architecture guide (English/Chinese)
- docs/PROMPT_WRITING_GUIDE.md - Two-layer prompt architecture and writing specifications
- docs/api/core.md / docs/api/core_cn.md - Core API reference (English/Chinese)
- docs/api/plugins.md / docs/api/plugins_cn.md - Plugin system API reference (English/Chinese)
- docs/guides/architecture_selection/GUIDE.md / GUIDE_CN.md - Architecture selection guide (English/Chinese)
- docs/guides/advanced/PERFORMANCE_TUNING.md / PERFORMANCE_TUNING_CN.md - Performance tuning guide
- docs/guides/customization/CUSTOM_PLUGINS.md / CUSTOM_PLUGINS_CN.md - Custom plugin development
- examples/production/README.md - Production examples overview
- examples/production/*/README.md - Individual example documentation (all 7 examples complete)
