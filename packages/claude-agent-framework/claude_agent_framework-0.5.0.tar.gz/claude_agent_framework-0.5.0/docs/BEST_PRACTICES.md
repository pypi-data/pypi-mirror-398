# Claude Agent Framework - Best Practices Guide

> Comprehensive development guide for building multi-agent systems with Claude Agent Framework

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [Architecture Patterns](#2-architecture-patterns)
3. [Core Components](#3-core-components)
4. [Multi-Agent Orchestration](#4-multi-agent-orchestration)
5. [Hook Mechanism](#5-hook-mechanism)
6. [Tool Assignment](#6-tool-assignment)
7. [Prompt Engineering](#7-prompt-engineering)
8. [State Management](#8-state-management)
9. [Error Handling](#9-error-handling)
10. [Logging and Auditing](#10-logging-and-auditing)
11. [Configuration Management](#11-configuration-management)
12. [Complete Examples](#12-complete-examples)

---

## 1. Design Philosophy

### 1.1 Why Multi-Agent?

Complex tasks often require multiple specialized capabilities that a single LLM prompt cannot effectively handle. Consider a research task: it needs web searching, data analysis, and report writing - each requiring different tools, prompts, and even models. A monolithic approach leads to:

- **Prompt bloat**: One prompt trying to do everything becomes unwieldy
- **Tool overload**: Agent has access to tools it shouldn't use at certain stages
- **Quality degradation**: Jack-of-all-trades prompts underperform specialized ones
- **Cost inefficiency**: Using expensive models for simple subtasks

The solution: **agent specialization and orchestration** - decompose complex tasks into specialized agents coordinated by a lead agent.

### 1.2 Framework Overview

Claude Agent Framework provides **7 distinct orchestration patterns** for multi-agent systems. While all architectures share common design principles, each implements a unique workflow pattern suited to specific problem domains.

### 1.3 Orchestration Patterns

Each architecture implements a distinct orchestration pattern:

| Architecture | Pattern | Flow | Best For |
|--------------|---------|------|----------|
| **Research** | Fan-out/Fan-in | Lead → [Workers parallel] → Aggregator | Data gathering, deep research |
| **Pipeline** | Sequential Chain | Stage A → B → C → D | Code review, content creation |
| **Critic-Actor** | Iterative Refinement | Generate ↔ Evaluate (loop) | Quality optimization |
| **Specialist Pool** | Dynamic Routing | Router → Expert(s) → Synthesize | Technical support, Q&A |
| **Debate** | Adversarial Deliberation | Pro ↔ Con (N rounds) → Judge | Decision support |
| **Reflexion** | Self-Improvement Loop | Execute → Reflect → Improve | Complex problem solving |
| **MapReduce** | Divide and Conquer | Split → [Map parallel] → Reduce | Large-scale analysis |

### 1.4 Pattern Diagrams

**Fan-out/Fan-in (Research)**
```
Lead Agent ─┬─→ Worker 1 ─┐
            ├─→ Worker 2 ─┼─→ Aggregator → Output
            └─→ Worker 3 ─┘
```

**Sequential Chain (Pipeline)**
```
Stage A → Stage B → Stage C → Stage D → Output
```

**Iterative Refinement (Critic-Actor)**
```
┌─────────────────────────┐
│  Actor ──→ Critic       │
│    ↑         │          │
│    └─────────┘ (repeat) │
└─────────────────────────┘
```

**Dynamic Routing (Specialist Pool)**
```
Query → Router ─┬─→ Expert A ─┐
                ├─→ Expert B ─┼─→ Synthesizer
                └─→ Expert C ─┘
```

**Adversarial Deliberation (Debate)**
```
Topic → Proponent ↔ Opponent (N rounds) → Judge → Verdict
```

**Self-Improvement Loop (Reflexion)**
```
┌─────────────────────────────────┐
│  Executor → Reflector → Improve │
│      ↑                    │     │
│      └────────────────────┘     │
└─────────────────────────────────┘
```

**Divide and Conquer (MapReduce)**
```
Task → Splitter ─┬─→ Mapper 1 ─┐
                 ├─→ Mapper 2 ─┼─→ Reducer → Result
                 └─→ Mapper 3 ─┘
```

### 1.5 Common Design Principles

Despite different orchestration patterns, all architectures share these core principles:

| Principle | Description | Implementation |
|-----------|-------------|----------------|
| **Separation of Concerns** | Each agent does one thing well | Lead orchestrates, subagents execute specific tasks |
| **Tool Constraints** | Limit available tool sets | Precise `allowed_tools` control per agent |
| **Loose Coupling** | Agents exchange data via filesystem | Standard directory structure + Glob/Read/Write |
| **Observability** | Full trace capability | Hook mechanism + JSONL logging |
| **Cost Optimization** | Choose models wisely | Subagents use Haiku for cost efficiency |
| **Extensibility** | Easy to add new patterns | Registry-based architecture system |
| **Type Safety** | Strong typing throughout | Pydantic models, type hints |

### 1.6 Choosing the Right Pattern

| Scenario | Recommended Pattern | Why |
|----------|---------------------|-----|
| Gathering information from multiple sources | **Research** (Fan-out/Fan-in) | Parallel data collection, then synthesis |
| Step-by-step processing with handoffs | **Pipeline** (Sequential) | Clear stage boundaries, progressive refinement |
| Quality improvement through feedback | **Critic-Actor** (Iterative) | Generate-evaluate loop until threshold met |
| Routing queries to domain experts | **Specialist Pool** (Dynamic) | Match query type to expert capabilities |
| Analyzing pros and cons of decisions | **Debate** (Adversarial) | Structured argumentation, balanced analysis |
| Complex problems requiring reflection | **Reflexion** (Self-Improvement) | Learn from attempts, refine strategy |
| Processing large datasets in parallel | **MapReduce** (Divide-Conquer) | Parallel processing, efficient aggregation |

---

## 2. Architecture Patterns

### 2.1 Pattern Selection Guide

| Pattern | Best For | Key Characteristic |
|---------|----------|-------------------|
| **Research** | Data gathering, analysis | Parallel workers → synthesis |
| **Pipeline** | Sequential workflows | Stage A → Stage B → Stage C |
| **Critic-Actor** | Quality iteration | Generate ↔ Evaluate loop |
| **Specialist Pool** | Expert routing | Dynamic dispatch by domain |
| **Debate** | Decision analysis | Pro ↔ Con with judge |
| **Reflexion** | Complex problem solving | Execute → Reflect → Improve |
| **MapReduce** | Large-scale processing | Split → Map parallel → Reduce |

### 2.2 Pattern Internals

#### Research Pattern

```
                    ┌──────────────┐
                    │  Lead Agent  │
                    │ (Coordinator)│
                    └──────┬───────┘
                           │ Task decomposition
            ┌──────────────┼──────────────┐
            ↓              ↓              ↓
      ┌──────────┐  ┌──────────┐  ┌──────────┐
      │Researcher│  │Researcher│  │Researcher│
      │    1     │  │    2     │  │    3     │
      └────┬─────┘  └────┬─────┘  └────┬─────┘
           │             │             │
           └──────┬──────┴──────┬──────┘
                  ↓             ↓
           files/research_notes/*.md
                        ↓
                ┌──────────────┐
                │ Data Analyst │
                └──────┬───────┘
                       ↓
                files/charts/*.png
                       ↓
                ┌──────────────┐
                │Report Writer │
                └──────┬───────┘
                       ↓
                files/reports/*.pdf
```

#### Pipeline Pattern

```
┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐
│Architect│ → │ Coder  │ → │Reviewer│ → │ Tester │
└────────┘   └────────┘   └────────┘   └────────┘
     │            │            │            │
     ↓            ↓            ↓            ↓
  Design      Implement    Feedback     Tests
```

#### Critic-Actor Pattern

```
┌─────────────────────────────────────────┐
│                                         │
│   ┌─────────┐         ┌─────────┐      │
│   │  Actor  │ ──────→ │  Critic │      │
│   └────┬────┘         └────┬────┘      │
│        ↑    Content        │           │
│        │                   │ Feedback  │
│        └───────────────────┘           │
│                                         │
│   while quality < threshold             │
└─────────────────────────────────────────┘
```

---

## 3. Core Components

### 3.1 Initialization

The framework provides a simplified entry point:

```python
from claude_agent_framework import init

# Minimal usage - 2 lines to get started
session = init("research")
async for msg in session.run("Analyze AI market trends"):
    print(msg)
```

### 3.2 Architecture Components

Each architecture consists of:

```
architectures/<name>/
├── __init__.py          # Exports
├── config.py            # Architecture-specific configuration
├── orchestrator.py      # Main architecture class
└── prompts/             # Agent prompts
    ├── lead_agent.txt
    ├── agent_a.txt
    └── agent_b.txt
```

### 3.3 BaseArchitecture Interface

```python
from claude_agent_framework.core import BaseArchitecture, register_architecture

@register_architecture("my_architecture")
class MyArchitecture(BaseArchitecture):
    """Custom architecture implementation."""

    name = "my_architecture"
    description = "Description shown in architecture listing"

    def get_agents(self) -> dict[str, AgentDefinitionConfig]:
        """Define subagents and their configurations."""
        return {
            "worker": AgentDefinitionConfig(
                name="worker",
                description="Executes specific tasks",
                tools=["Read", "Write"],
                prompt_file="worker.txt",
            ),
        }

    async def execute(
        self,
        prompt: str,
        tracker: SubagentTracker | None = None,
        transcript: TranscriptWriter | None = None,
    ) -> AsyncIterator[Any]:
        """Execute the architecture workflow."""
        # Implementation
        ...
```

### 3.4 AgentSession

Manages the complete session lifecycle:

```python
session = init("research")

try:
    async for msg in session.run("Query"):
        print(msg)
finally:
    await session.teardown()  # Cleanup

# Or use context manager
async with init("research") as session:
    results = await session.query("Query")
```

---

## 4. Multi-Agent Orchestration

### 4.1 Parallel Dispatch

Lead agents dispatch multiple subagents simultaneously:

```python
# In lead agent prompt:
"""
# Rules
1. You can ONLY use the Task tool to dispatch subagents
2. NEVER perform research, analysis, or writing yourself
3. Decompose requests into 2-4 independent subtopics
4. Dispatch researchers IN PARALLEL (not sequentially)
5. Wait for all research to complete before dispatching analyst
"""
```

### 4.2 Filesystem Coordination

Agents communicate via standard directory structure:

```python
FILE_STRUCTURE = {
    "files/research_notes/": "Researcher output → Analyst input",
    "files/data/":           "Analyst output → Reporter input",
    "files/charts/":         "Analyst charts → Reporter reference",
    "files/reports/":        "Reporter final output",
}
```

### 4.3 Lead Agent Template

```text
# Role Definition
You are the Research Coordinator, responsible for task decomposition
and subagent orchestration.

# Core Rules
1. You can ONLY use the Task tool to dispatch subagents
2. NEVER perform research, analysis, or writing yourself
3. Decompose research requests into 2-4 independent subtopics
4. Dispatch researchers IN PARALLEL (not sequentially)
5. Wait for all research to complete before dispatching analyst
6. Finally dispatch reporter to generate output

# Workflow
1. Analyze user request → Identify subtopics
2. Parallel dispatch researchers → Gather information
3. Dispatch analyst → Process data
4. Dispatch reporter → Generate report
5. Report completion status to user

# Available Subagents
- researcher: Web search and information gathering
- data-analyst: Data processing and visualization
- report-writer: Final report generation
```

---

## 5. Hook Mechanism

### 5.1 Hook Types

| Hook Type | Trigger Point | Purpose |
|-----------|---------------|---------|
| `PreToolUse` | Before tool execution | Input validation, permission checks, logging |
| `PostToolUse` | After tool execution | Result capture, error handling, metrics |
| `Notification` | Notification events | Status updates, progress reporting |

### 5.2 Hook Configuration

```python
from claude_agent_sdk import HookMatcher

hooks = {
    'PreToolUse': [
        HookMatcher(
            matcher=None,  # None = match all tools
            hooks=[tracker.pre_tool_use_hook]
        )
    ],
    'PostToolUse': [
        HookMatcher(
            matcher=None,
            hooks=[tracker.post_tool_use_hook]
        )
    ]
}
```

### 5.3 SubagentTracker Implementation

```python
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime

@dataclass
class ToolCallRecord:
    """Single tool call record."""
    timestamp: str
    tool_name: str
    tool_input: dict[str, Any]
    tool_use_id: str
    subagent_type: str
    parent_tool_use_id: str | None = None
    tool_output: Any = None
    error: str | None = None

class SubagentTracker:
    """Tracks subagent spawning and tool calls."""

    def __init__(self, log_file_path: str):
        self.sessions: dict[str, SubagentSession] = {}
        self.tool_call_records: dict[str, ToolCallRecord] = {}
        self._current_parent_id: str | None = None
        self.subagent_counters: dict[str, int] = {}
        self._log_file = open(log_file_path, 'w')

    def set_current_context(self, parent_tool_use_id: str | None):
        """Set current execution context."""
        self._current_parent_id = parent_tool_use_id

    async def pre_tool_use_hook(
        self,
        hook_input: dict[str, Any],
        tool_use_id: str,
        context: Any
    ) -> dict[str, Any]:
        """Pre-tool execution hook."""
        tool_name = hook_input['tool_name']
        tool_input = hook_input['tool_input']

        # Determine owning agent
        subagent_type = "LEAD"
        if self._current_parent_id and self._current_parent_id in self.sessions:
            subagent_type = self.sessions[self._current_parent_id].subagent_id

        # Create record
        record = ToolCallRecord(
            timestamp=datetime.now().isoformat(),
            tool_name=tool_name,
            tool_input=tool_input,
            tool_use_id=tool_use_id,
            subagent_type=subagent_type,
            parent_tool_use_id=self._current_parent_id
        )
        self.tool_call_records[tool_use_id] = record

        return {'continue_': True}

    async def post_tool_use_hook(
        self,
        hook_input: dict[str, Any],
        tool_use_id: str,
        context: Any
    ) -> dict[str, Any]:
        """Post-tool execution hook."""
        tool_response = hook_input.get('tool_response')
        record = self.tool_call_records.get(tool_use_id)

        if record:
            error = None
            if isinstance(tool_response, dict):
                error = tool_response.get('error')

            record.tool_output = tool_response
            record.error = error

        return {'continue_': True}
```

---

## 6. Tool Assignment

### 6.1 Built-in Tools

| Tool | Purpose | Typical Use Case |
|------|---------|------------------|
| `Task` | Dispatch subagent | Lead agent orchestration |
| `WebSearch` | Web search | Information gathering |
| `Read` | Read file | Load data |
| `Write` | Write file | Save results |
| `Glob` | File pattern matching | Discover files |
| `Grep` | Content search | Find information |
| `Bash` | Execute command | Run scripts |
| `Edit` | Edit file | Modify content |
| `Skill` | Call skill | Complex operations |

### 6.2 Tool Assignment by Role

```python
TOOL_ASSIGNMENTS = {
    "lead":       ["Task"],                              # Orchestration only
    "researcher": ["WebSearch", "Write"],                # Search and save
    "analyst":    ["Glob", "Read", "Bash", "Write"],     # Analyze and execute
    "reporter":   ["Glob", "Read", "Write", "Skill"],    # Generate reports
}
```

### 6.3 Principle of Least Privilege

```python
# BAD: Too many tools
bad_agent = AgentDefinitionConfig(
    tools=["WebSearch", "Read", "Write", "Bash", "Edit", "Glob", "Grep"],
    ...
)

# GOOD: Precise control
good_agent = AgentDefinitionConfig(
    tools=["WebSearch", "Write"],  # Only what's needed
    ...
)
```

---

## 7. Prompt Engineering

### 7.1 Prompt Structure Template

```text
# Role Definition
You are [ROLE NAME], responsible for [CORE RESPONSIBILITY].

# Capability Boundaries
- You CAN: [Specific capability list]
- You CANNOT: [Restriction list]

# Workflow
1. [Step 1]
2. [Step 2]
3. [Step 3]

# Output Specification
- Format: [Expected format]
- Location: [Output path]
- Naming: [Naming convention]

# Quality Standards
- [Standard 1]
- [Standard 2]

# Examples
[Concrete examples]
```

### 7.2 Researcher Prompt Example

```text
# Role Definition
You are a Professional Researcher, responsible for gathering quantitative
data and key information through web search.

# Core Tasks
1. Execute 5-10 targeted searches
2. Prioritize quantitative data (market size, growth rates, rankings)
3. Save research findings as Markdown files

# Search Strategy
- Use specific, targeted queries
- Seek authoritative sources (industry reports, official data)
- Collect multiple data points for cross-validation

# Output Specification
- Path: files/research_notes/{topic_name}.md
- Format: Markdown with structured headings
- Content: 10-15+ specific statistics

# Data Priority
1. Market size and share
2. Growth rates and forecasts
3. Key player rankings
4. Technical parameter comparisons
5. Investment and funding data
```

### 7.3 Prompt Loading

```python
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "prompts"

def load_prompt(filename: str) -> str:
    """Load prompt from prompts directory."""
    prompt_path = PROMPTS_DIR / filename
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8").strip()
```

### 7.4 Business Templates System

The framework provides a **layered prompt system** that separates architecture-level prompts from business-specific prompts:

```
┌─────────────────────────────────────────────────────────┐
│  Application Layer (examples/production/)               │
│  - Choose business template or fully customize          │
│  - Final decision on business prompts                   │
└─────────────────────────────────────────────────────────┘
                          ↓ select/override
┌─────────────────────────────────────────────────────────┐
│  Business Template Layer (business_templates/)          │
│  - Independent of architectures                         │
│  - Organized by business type                           │
│  - Pre-built templates for common use cases             │
└─────────────────────────────────────────────────────────┘
                          ↓ compose
┌─────────────────────────────────────────────────────────┐
│  Architecture Layer (architectures/)                    │
│  - Core agent role, capabilities, constraints           │
│  - No business-specific content                         │
└─────────────────────────────────────────────────────────┘
```

**Final Prompt = Core Prompt + Business Prompt**

#### Available Business Templates

| Template | Architecture | Use Case |
|----------|--------------|----------|
| `competitive_intelligence` | research | Competitive analysis |
| `market_research` | research | Market research |
| `pr_code_review` | pipeline | PR code review |
| `marketing_content` | critic_actor | Marketing content |
| `it_support` | specialist_pool | IT support |
| `tech_decision` | debate | Tech decisions |
| `code_debugger` | reflexion | Code debugging |
| `codebase_analysis` | mapreduce | Codebase analysis |

#### Using Business Templates

```python
from claude_agent_framework import create_session

# Method 1: Use a preset business template
session = create_session(
    "research",
    business_template="competitive_intelligence"
)

# Method 2: Use template with variable substitution
session = create_session(
    "research",
    business_template="competitive_intelligence",
    template_vars={
        "company_name": "Tesla Inc",
        "industry": "Electric Vehicles"
    }
)

# Method 3: Override specific agent prompts
session = create_session(
    "research",
    business_template="competitive_intelligence",
    prompt_overrides={
        "researcher": "Focus specifically on EV battery technology..."
    }
)

# Method 4: Fully custom prompts directory
session = create_session(
    "research",
    prompts_dir="./my_custom_prompts"
)
```

#### YAML Configuration

```yaml
# config.yaml
architecture: research
business_template: competitive_intelligence

prompts:
  template_vars:
    company_name: "Tesla Inc"
    industry: "Electric Vehicles"
  agents:
    researcher:
      business_prompt: |
        Focus on battery technology and EV market share.
```

#### Template Variables

Business template prompts can include `${variable}` placeholders:

```text
# Business Context: Competitive Intelligence

You are conducting competitive intelligence analysis for ${company_name}
in the ${industry} sector.

# Research Focus
...
```

#### Prompt Priority Resolution

When composing the final prompt, the system follows this priority order:

1. `prompt_overrides["agent_name"]` - Code parameter override (highest)
2. YAML `config.prompts.agents.xxx.business_prompt` - YAML inline
3. `custom_prompts_dir/<agent>.txt` - Application custom directory
4. `business_templates/<template>/<agent>.txt` - Business template
5. Empty (use only architecture core prompt) - Default

### 7.5 Role-Based Architecture

The framework supports a **Role-Based Architecture** that separates abstract role definitions from concrete agent instances, enabling flexible multi-business configuration.

#### Core Concepts

| Concept | Description |
|---------|-------------|
| **RoleType** | Semantic role type enum (WORKER, PROCESSOR, SYNTHESIZER, etc.) |
| **RoleCardinality** | Quantity constraints (EXACTLY_ONE, ONE_OR_MORE, ZERO_OR_MORE, ZERO_OR_ONE) |
| **RoleDefinition** | Architecture-level role specification with tools and constraints |
| **AgentInstanceConfig** | Business-level concrete agent configuration |
| **RoleRegistry** | Validates agent instances against role constraints |

#### Role Types

```python
from claude_agent_framework.core.types import RoleType

class RoleType(str, Enum):
    COORDINATOR = "coordinator"   # Task orchestrator
    WORKER = "worker"             # Data gatherer
    PROCESSOR = "processor"       # Data processor
    SYNTHESIZER = "synthesizer"   # Result synthesizer
    CRITIC = "critic"             # Quality evaluator
    JUDGE = "judge"               # Decision maker
    SPECIALIST = "specialist"     # Domain expert
    ADVOCATE = "advocate"         # Position advocate
    MAPPER = "mapper"             # Parallel mapper
    REDUCER = "reducer"           # Result reducer
    EXECUTOR = "executor"         # Task executor
    REFLECTOR = "reflector"       # Self-reflector
```

#### Agent Instance Configuration

```python
from claude_agent_framework import create_session
from claude_agent_framework.core.roles import AgentInstanceConfig

# Define agent instances for specific business needs
agents = [
    AgentInstanceConfig(
        name="market-researcher",
        role="worker",
        description="Market data collection specialist",
        prompt_file="prompts/market_researcher.txt",
    ),
    AgentInstanceConfig(
        name="tech-researcher",
        role="worker",
        description="Technology trends analyst",
        prompt_file="prompts/tech_researcher.txt",
    ),
    AgentInstanceConfig(
        name="data-analyst",
        role="processor",
        model="sonnet",
        description="Data analysis expert",
    ),
    AgentInstanceConfig(
        name="report-writer",
        role="synthesizer",
        description="Report generation specialist",
    ),
]

# Create session with role-based configuration
session = create_session(
    "research",
    agent_instances=agents,
    business_template="competitive_intelligence",
)
```

#### Architecture Role Mappings

Each architecture defines specific roles with cardinality constraints:

| Architecture | Role Definitions | Pattern |
|--------------|-----------------|---------|
| **research** | worker (1+), processor (0-1), synthesizer (1) | Master-worker |
| **pipeline** | stage_executor (1+) | Sequential stages |
| **critic_actor** | actor (1), critic (1) | Generate-evaluate |
| **specialist_pool** | specialist (1+) | Expert routing |
| **debate** | advocate (2+), judge (1) | Deliberation |
| **reflexion** | executor (1), reflector (1) | Execute-reflect |
| **mapreduce** | mapper (1+), reducer (1) | Parallel map-reduce |

#### Prompt Priority with Role-Based Architecture

When using role-based architecture, prompt composition follows this priority:

1. **AgentInstanceConfig.prompt** - Direct prompt content (highest)
2. **prompt_overrides[agent_name]** - Session-level override
3. **custom_prompts_dir/<agent_name>.txt** - Custom prompts directory
4. **business_templates/<template>/<agent_name>.txt** - Business template
5. **RoleDefinition.prompt_file** - Role base prompt (lowest)

For detailed documentation, see [Role-Based Architecture Guide](ROLE_BASED_ARCHITECTURE.md).

---

## 8. State Management

### 8.1 Session State

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class AgentSession:
    """Agent session state."""
    session_id: str
    started_at: str
    user_query: str
    subagents_spawned: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    current_phase: str = "init"  # init, researching, analyzing, reporting, done
    errors: List[str] = field(default_factory=list)
```

### 8.2 Phase Tracking

```python
class PhaseTracker:
    """Workflow phase tracker."""

    PHASES = ["init", "researching", "analyzing", "reporting", "done"]

    def __init__(self):
        self.current_phase = "init"
        self.phase_history = []

    def advance_phase(self, new_phase: str):
        """Advance to new phase."""
        if new_phase not in self.PHASES:
            raise ValueError(f"Unknown phase: {new_phase}")

        self.phase_history.append({
            "from": self.current_phase,
            "to": new_phase,
            "timestamp": datetime.now().isoformat()
        })
        self.current_phase = new_phase

    def is_complete(self) -> bool:
        return self.current_phase == "done"
```

---

## 9. Error Handling

### 9.1 Graceful Degradation

```python
async def post_tool_use_hook(self, hook_input, tool_use_id, context):
    """Error handling example."""
    tool_response = hook_input.get('tool_response')

    # Detect error
    error = None
    if isinstance(tool_response, dict):
        error = tool_response.get('error')

    if error:
        # Log error but don't interrupt execution
        logger.warning(f"Tool error: {error}")
        self.errors.append({
            "tool_use_id": tool_use_id,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })

    # Continue execution
    return {'continue_': True}
```

### 9.2 Resource Cleanup

```python
async def main():
    tracker = None
    transcript = None

    try:
        # Initialize resources
        transcript = TranscriptWriter(log_path)
        tracker = SubagentTracker(tool_log_path)

        # Execute main logic
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt=user_input)
            async for msg in client.receive_response():
                process_message(msg, tracker, transcript)

    except Exception as e:
        logger.error(f"Session failed: {e}")
        raise

    finally:
        # Ensure resource cleanup
        if transcript:
            transcript.close()
        if tracker:
            tracker.close()
```

### 9.3 Error Classification

```python
class AgentError(Exception):
    """Base agent error."""
    pass

class ConfigurationError(AgentError):
    """Configuration error."""
    pass

class ToolExecutionError(AgentError):
    """Tool execution error."""
    def __init__(self, tool_name: str, message: str):
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}' failed: {message}")

class SubagentError(AgentError):
    """Subagent error."""
    def __init__(self, subagent_id: str, message: str):
        self.subagent_id = subagent_id
        super().__init__(f"Subagent '{subagent_id}' failed: {message}")
```

---

## 10. Logging and Auditing

### 10.1 Dual-Format Logging

```python
class TranscriptWriter:
    """Dual-format log writer."""

    def __init__(self, file_path: Path):
        self.file = open(file_path, 'w', encoding='utf-8')

    def write(self, text: str, end: str = ""):
        """Output to both console and file."""
        print(text, end=end, flush=True)
        self.file.write(text + end)
        self.file.flush()

    def write_to_file_only(self, text: str):
        """Write to file only (detailed logs)."""
        self.file.write(text)
        self.file.flush()

    def close(self):
        self.file.close()
```

### 10.2 JSONL Structured Logging

```python
import json
from datetime import datetime

class ToolCallLogger:
    """Tool call JSONL logger."""

    def __init__(self, file_path: Path):
        self.file = open(file_path, 'w')

    def log_tool_start(self, agent_id: str, tool_name: str,
                       tool_input: dict, tool_use_id: str):
        entry = {
            "event": "tool_call_start",
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "tool_name": tool_name,
            "tool_use_id": tool_use_id,
            "input_summary": self._summarize_input(tool_input)
        }
        self._write(entry)

    def log_tool_complete(self, tool_use_id: str, success: bool,
                         output_size: int = 0, error: str = None):
        entry = {
            "event": "tool_call_complete",
            "timestamp": datetime.now().isoformat(),
            "tool_use_id": tool_use_id,
            "success": success,
            "output_size": output_size,
            "error": error
        }
        self._write(entry)

    def _write(self, entry: dict):
        self.file.write(json.dumps(entry, ensure_ascii=False) + '\n')
        self.file.flush()

    def close(self):
        self.file.close()
```

### 10.3 Session Directory Management

```python
from pathlib import Path
from datetime import datetime

def setup_session() -> tuple[Path, Path, Path]:
    """Create session directory and log files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = Path("logs") / f"session_{timestamp}"
    session_dir.mkdir(parents=True, exist_ok=True)

    transcript_file = session_dir / "transcript.txt"
    tool_log_file = session_dir / "tool_calls.jsonl"

    return session_dir, transcript_file, tool_log_file
```

---

## 11. Configuration Management

### 11.1 Architecture Configuration

```python
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class ResearchConfig:
    """Research architecture configuration."""

    # Model configuration
    lead_model: str = "haiku"
    researcher_model: str = "haiku"
    analyst_model: str = "haiku"
    reporter_model: str = "haiku"

    # Research depth
    research_depth: str = "standard"  # shallow, standard, deep
    max_researchers: int = 4

    # Output directories
    research_notes_dir: str = "research_notes"
    data_dir: str = "data"
    charts_dir: str = "charts"
    reports_dir: str = "reports"

    def get_model_overrides(self) -> dict[str, str]:
        """Get model overrides for agents."""
        return {
            "researcher": self.researcher_model,
            "data-analyst": self.analyst_model,
            "report-writer": self.reporter_model,
        }
```

### 11.2 Environment Configuration

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API configuration
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # Model configuration
    LEAD_MODEL = os.getenv("LEAD_MODEL", "haiku")
    SUBAGENT_MODEL = os.getenv("SUBAGENT_MODEL", "haiku")

    # Path configuration
    PROJECT_ROOT = Path(__file__).parent.parent
    FILES_DIR = PROJECT_ROOT / "files"
    LOGS_DIR = PROJECT_ROOT / "logs"
    PROMPTS_DIR = PROJECT_ROOT / "prompts"

    # Feature flags
    ENABLE_LOGGING = os.getenv("ENABLE_LOGGING", "true").lower() == "true"
    BYPASS_PERMISSIONS = os.getenv("BYPASS_PERMISSIONS", "true").lower() == "true"

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
```

---

## 12. Complete Examples

### 12.1 Basic Usage

```python
from claude_agent_framework import init
import asyncio

async def research_example():
    """Basic research example."""
    session = init("research")

    async for msg in session.run("Analyze AI market trends in 2024"):
        print(msg)

asyncio.run(research_example())
```

### 12.2 Custom Architecture

```python
from claude_agent_framework import register_architecture, BaseArchitecture, init
from claude_agent_framework.core.base import AgentDefinitionConfig

@register_architecture("qa_expert")
class QAExpertArchitecture(BaseArchitecture):
    """Custom Q&A expert architecture."""

    name = "qa_expert"
    description = "Q&A system with domain expert routing"

    def get_agents(self) -> dict[str, AgentDefinitionConfig]:
        return {
            "code_expert": AgentDefinitionConfig(
                name="code_expert",
                description="Expert in programming and software development",
                tools=["Read", "Write", "Glob", "Grep"],
                prompt_file="code_expert.txt",
            ),
            "data_expert": AgentDefinitionConfig(
                name="data_expert",
                description="Expert in data analysis and statistics",
                tools=["Read", "Write", "Bash"],
                prompt_file="data_expert.txt",
            ),
        }

    async def execute(self, prompt, tracker=None, transcript=None):
        """Execute Q&A workflow."""
        # Build SDK configuration
        options = ClaudeAgentOptions(
            permission_mode="bypassPermissions",
            setting_sources=["project"],
            system_prompt=self.get_lead_prompt(),
            allowed_tools=["Task"],
            agents=self.to_sdk_agents(),
            hooks=self._build_hooks(tracker),
            model=self.model_config.default,
        )

        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt=prompt)

            async for msg in client.receive_response():
                yield msg

# Use the custom architecture
async def main():
    session = init("qa_expert")
    async for msg in session.run("How do I optimize database queries?"):
        print(msg)
```

### 12.3 Programmatic Control

```python
from claude_agent_framework import init
from pathlib import Path

async def programmatic_example():
    """Full programmatic control."""

    # Initialize with custom options
    session = init(
        "research",
        model="sonnet",
        verbose=True,
        log_dir=Path("./custom_logs"),
    )

    # Access internal components
    print(f"Architecture: {session.architecture.name}")
    print(f"Session directory: {session.session_dir}")

    # Run query
    query = "Analyze cloud computing market trends"

    try:
        async for msg in session.run(query):
            print(msg)
    finally:
        await session.teardown()
        print(f"Session saved to: {session.session_dir}")
```

---

## 13. Production-Grade Examples Deep Analysis

The framework includes 7 production-ready examples (`examples/production/`) that demonstrate real-world business applications of each architecture pattern. This section provides deep technical analysis of their implementation patterns, design decisions, and extension strategies.

### 13.1 Example Overview

| Example | Architecture | Business Domain | Key Technical Patterns |
|---------|--------------|-----------------|------------------------|
| **01_competitive_intelligence** | Research | Market Research | Parallel dispatch, SWOT synthesis, multi-channel data aggregation |
| **02_pr_code_review** | Pipeline | Software Engineering | Sequential gating, configurable thresholds, structured reporting |
| **03_marketing_content** | Critic-Actor | Content Marketing | Weighted scoring, iterative refinement, A/B variant generation |
| **04_it_support** | Specialist Pool | IT Operations | Keyword routing, urgency categorization, expert orchestration |
| **05_tech_decision** | Debate | Technology Strategy | Multi-round deliberation, weighted criteria, structured verdict |
| **06_code_debugger** | Reflexion | Software Debugging | Strategy library, reflection-based adaptation, root cause analysis |
| **07_codebase_analysis** | MapReduce | Code Quality | Intelligent chunking, parallel analysis, issue aggregation |

### 13.2 Competitive Intelligence System (Research Pattern)

**Business Context**: Automated competitive intelligence gathering for SaaS companies

#### Architecture Application

```
Lead Coordinator
    ├─→ [Researcher 1: AWS]     ─┐
    ├─→ [Researcher 2: Azure]    ├─→ Data Analyst → SWOT Generator
    └─→ [Researcher 3: GCP]     ─┘                      ↓
                                                   Report Writer
                                                         ↓
                                              competitive_analysis.pdf
```

**Parallel Dispatch Strategy**:
```python
# config.yaml
analysis_dimensions:
  - features        # Product capabilities
  - pricing         # Pricing models
  - market          # Market position
  - technology      # Tech stack

competitors:
  - AWS
  - Azure
  - Google Cloud

max_parallel_researchers: 3  # Spawn 3 researchers simultaneously
```

#### Key Implementation Patterns

**1. Configuration-Driven Research Scope**:
```python
@dataclass
class CompetitorAnalysisConfig:
    competitors: list[str]
    dimensions: list[str]
    data_sources: list[str] = field(default_factory=lambda: [
        "official_website",
        "tech_blogs",
        "review_sites",
        "social_media"
    ])
    output_format: str = "pdf"  # pdf, markdown, html

    def validate(self):
        """Ensure valid configuration."""
        if len(self.competitors) < 2:
            raise ValueError("Need at least 2 competitors for analysis")
        if not self.dimensions:
            raise ValueError("Must specify analysis dimensions")
```

**2. Structured SWOT Analysis**:
```python
# Analyst generates structured JSON for SWOT
swot_schema = {
    "strengths": [
        {"category": "features", "items": [...], "evidence": [...]},
        {"category": "pricing", "items": [...], "evidence": [...]}
    ],
    "weaknesses": [...],
    "opportunities": [...],
    "threats": [...]
}
```

**3. Multi-Channel Data Aggregation**:
```python
# Researcher prompt structure
"""
For each competitor, gather data from:
1. Official website → feature lists, pricing
2. G2/Capterra reviews → user sentiment, ratings
3. Tech blogs → architecture insights
4. LinkedIn/Twitter → company updates

Save to: files/research_notes/{competitor_name}_{dimension}.md
"""
```

#### Error Handling Strategy

```python
# Graceful degradation
async def execute(self, prompt, tracker=None, transcript=None):
    researchers = await self._dispatch_researchers(competitors)

    # Wait for all, but don't fail if some timeout
    results = await asyncio.gather(*researchers, return_exceptions=True)

    successful = [r for r in results if not isinstance(r, Exception)]
    if len(successful) < 2:
        # Require minimum 2 successful for meaningful analysis
        raise InsufficientDataError("Need at least 2 competitor datasets")

    # Continue with available data
    await self._dispatch_analyst(successful)
```

#### Testing Approach

```python
# tests/test_competitive_intelligence.py

@pytest.mark.integration
async def test_full_workflow():
    """End-to-end workflow test."""
    session = init("research", config="examples/production/01_competitive_intelligence/config.yaml")

    query = "Analyze AWS vs Azure vs GCP for enterprise customers"
    results = await session.query(query)

    # Verify outputs
    assert (Path("files/reports") / "competitive_analysis.pdf").exists()
    assert len(list(Path("files/research_notes").glob("*.md"))) >= 6  # 3 competitors × 2 sources

@pytest.mark.unit
def test_swot_generation():
    """Test SWOT synthesis logic."""
    from examples.production.01_competitive_intelligence.utils import generate_swot

    research_data = {...}
    swot = generate_swot(research_data)

    assert all(k in swot for k in ["strengths", "weaknesses", "opportunities", "threats"])
    assert len(swot["strengths"]) > 0
```

#### Extension Points

1. **Custom Data Sources**: Add scrapers via `data_sources` config
2. **Analysis Dimensions**: Extend `dimensions` for industry-specific criteria
3. **Output Formats**: Implement custom reporters (e.g., PowerPoint, Notion)
4. **Automated Scheduling**: Add cron-based periodic analysis

---

### 13.3 PR Code Review Pipeline (Pipeline Pattern)

**Business Context**: Automated multi-stage code review for pull requests

#### Architecture Application

```
Stage 1: Architecture Review → Stage 2: Code Quality → Stage 3: Security Scan →
    Stage 4: Performance Test → Stage 5: Test Coverage
```

**Sequential Gating**:
```yaml
# config.yaml
stages:
  - name: architecture_review
    threshold: 7.0
    failure_strategy: stop    # Stop pipeline if score < 7.0

  - name: code_quality
    threshold: 6.0
    failure_strategy: warn    # Warn but continue

  - name: security_scan
    threshold: 8.0
    failure_strategy: stop    # Hard requirement

  - name: performance_test
    threshold: 5.0
    failure_strategy: continue  # Advisory only

  - name: test_coverage
    threshold: 70.0  # 70% coverage minimum
    failure_strategy: stop
```

#### Key Implementation Patterns

**1. Quality Thresholds with Configurable Failure Strategies**:
```python
@dataclass
class PipelineStage:
    name: str
    threshold: float
    failure_strategy: Literal["stop", "warn", "continue"]

    def evaluate(self, score: float) -> StageResult:
        passed = score >= self.threshold

        if not passed:
            if self.failure_strategy == "stop":
                raise PipelineStopped(f"{self.name} failed: {score} < {self.threshold}")
            elif self.failure_strategy == "warn":
                logger.warning(f"{self.name} below threshold: {score} < {self.threshold}")

        return StageResult(
            stage=self.name,
            score=score,
            passed=passed,
            action="continue" if passed or self.failure_strategy != "stop" else "stop"
        )
```

**2. Structured Review Report**:
```python
# Output: files/review_report.json
{
    "pr_id": "PR-123",
    "overall_status": "PASSED_WITH_WARNINGS",
    "stages": [
        {
            "stage": "architecture_review",
            "score": 8.5,
            "passed": true,
            "findings": [
                {"severity": "info", "message": "Good separation of concerns"}
            ]
        },
        {
            "stage": "code_quality",
            "score": 5.5,
            "passed": false,
            "findings": [
                {"severity": "warning", "message": "High complexity in PaymentProcessor.process()"}
            ],
            "action_taken": "warn"
        },
        // ...
    ],
    "recommendations": [...]
}
```

**3. Stage-Specific Tool Assignment**:
```python
STAGE_TOOLS = {
    "architecture_review": ["Read", "Glob", "Write"],          # Read code, write report
    "code_quality": ["Read", "Bash", "Write"],                 # Run linters
    "security_scan": ["Read", "Bash", "Grep", "Write"],        # Run bandit/semgrep
    "performance_test": ["Bash", "Read", "Write"],             # Run benchmarks
    "test_coverage": ["Bash", "Read", "Write"],                # Run pytest --cov
}
```

#### Error Handling Strategy

```python
async def execute_pipeline(self, stages: list[PipelineStage]):
    results = []

    for stage in stages:
        try:
            result = await self._run_stage(stage)
            results.append(result)

            # Check if should stop
            if not result.passed and stage.failure_strategy == "stop":
                logger.error(f"Pipeline stopped at {stage.name}")
                return PipelineReport(status="FAILED", stages=results)

        except ToolExecutionError as e:
            # Tool failure (e.g., linter crashed)
            if stage.failure_strategy == "stop":
                raise
            else:
                logger.warning(f"Stage {stage.name} tool error: {e}")
                results.append(StageResult(stage=stage.name, error=str(e)))

    return PipelineReport(status="PASSED", stages=results)
```

#### Testing Approach

```python
@pytest.fixture
def sample_pr():
    """Create test PR with known issues."""
    return {
        "files": ["auth.py", "payment.py"],
        "known_issues": {
            "code_quality": ["high_complexity"],
            "security": ["sql_injection_risk"]
        }
    }

@pytest.mark.integration
async def test_pipeline_stops_on_security_failure(sample_pr):
    """Test that security failures stop pipeline."""
    config = load_config("examples/production/02_pr_code_review/config.yaml")
    session = init("pipeline", config=config)

    result = await session.query(f"Review PR: {sample_pr}")

    # Should stop at security stage
    assert result.status == "FAILED"
    assert result.stopped_at == "security_scan"
    assert len(result.stages) <= 3  # Didn't reach stages 4-5
```

#### Extension Points

1. **Custom Linters**: Add new tools via `stage_tools` config
2. **Dynamic Thresholds**: Adjust based on PR size/criticality
3. **Integration Hooks**: Trigger CI/CD actions based on results
4. **Custom Stages**: Add domain-specific review stages

---

### 13.4 Marketing Content Optimizer (Critic-Actor Pattern)

**Business Context**: AI-assisted content creation with iterative quality improvement

#### Architecture Application

```
┌─────────────────────────────────────────┐
│  while quality < threshold:             │
│    Content = Actor.generate()           │
│    Scores = Critic.evaluate(content)    │
│    if scores.overall >= threshold:      │
│        break                             │
│    Content = Actor.improve(feedback)    │
└─────────────────────────────────────────┘
```

**Multi-Dimensional Weighted Scoring**:
```yaml
# config.yaml
evaluation_criteria:
  seo_optimization:
    weight: 0.25
    metrics:
      - keyword_density
      - meta_description
      - heading_structure

  engagement:
    weight: 0.30
    metrics:
      - hook_strength
      - readability_score
      - cta_clarity

  brand_consistency:
    weight: 0.25
    metrics:
      - tone_match
      - terminology_usage
      - style_guide_compliance

  accuracy:
    weight: 0.20
    metrics:
      - fact_verification
      - claim_support
      - source_credibility

quality_threshold: 8.0
max_iterations: 5
```

#### Key Implementation Patterns

**1. Weighted Multi-Dimensional Evaluation**:
```python
@dataclass
class ContentScores:
    seo_optimization: float
    engagement: float
    brand_consistency: float
    accuracy: float
    weights: dict[str, float] = field(default_factory=lambda: {
        "seo_optimization": 0.25,
        "engagement": 0.30,
        "brand_consistency": 0.25,
        "accuracy": 0.20
    })

    @property
    def overall_score(self) -> float:
        return (
            self.seo_optimization * self.weights["seo_optimization"] +
            self.engagement * self.weights["engagement"] +
            self.brand_consistency * self.weights["brand_consistency"] +
            self.accuracy * self.weights["accuracy"]
        )

    def get_improvement_priorities(self) -> list[str]:
        """Return dimensions sorted by improvement need."""
        scores = {
            "seo_optimization": self.seo_optimization,
            "engagement": self.engagement,
            "brand_consistency": self.brand_consistency,
            "accuracy": self.accuracy
        }
        # Weight impact = low_score × dimension_weight
        impact = {k: (10 - v) * self.weights[k] for k, v in scores.items()}
        return sorted(impact.keys(), key=lambda k: impact[k], reverse=True)
```

**2. Structured Feedback Loop**:
```python
# Critic output format
{
    "iteration": 3,
    "scores": {
        "seo_optimization": 7.5,
        "engagement": 8.2,
        "brand_consistency": 6.8,
        "accuracy": 9.0,
        "overall": 7.9
    },
    "feedback": {
        "seo_optimization": "Good keyword usage, but meta description too long (170 chars, max 155)",
        "brand_consistency": "Tone is too formal. Use more conversational language per brand guide.",
        "engagement": "Strong hook! CTA could be more specific."
    },
    "improvement_priorities": ["brand_consistency", "seo_optimization"],
    "continue_iteration": true  # overall < threshold (8.0)
}
```

**3. A/B Variant Generation**:
```python
# After reaching threshold, generate variants
async def generate_variants(self, final_content: str, n_variants: int = 3):
    """Generate A/B test variants of successful content."""
    variants = []

    for i in range(n_variants):
        variant_prompt = f"""
        Generate variant {i+1} of this content with different:
        - Headline approach (question vs statement vs benefit-driven)
        - Content structure (story vs data vs problem-solution)
        - CTA style (urgency vs value vs curiosity)

        Maintain same core message and quality level.
        """
        variant = await self.actor.generate(variant_prompt, base_content=final_content)
        variants.append(variant)

    return variants
```

#### Error Handling Strategy

```python
async def execute(self, prompt, tracker=None, transcript=None):
    iteration = 0
    max_iterations = self.config.max_iterations

    while iteration < max_iterations:
        # Generate content
        try:
            content = await self.actor.generate(prompt)
        except ContentGenerationError as e:
            logger.error(f"Actor failed at iteration {iteration}: {e}")
            if iteration == 0:
                raise  # Can't proceed without initial content
            else:
                # Use last successful iteration
                logger.warning("Using content from previous iteration")
                break

        # Evaluate
        scores = await self.critic.evaluate(content)

        if scores.overall_score >= self.config.quality_threshold:
            logger.info(f"Quality threshold met at iteration {iteration}")
            break

        # Prepare feedback for improvement
        feedback = self._format_feedback(scores)
        prompt = self._build_improvement_prompt(content, feedback)
        iteration += 1

    if iteration == max_iterations:
        logger.warning(f"Max iterations reached. Final score: {scores.overall_score}")

    return content, scores
```

#### Testing Approach

```python
@pytest.mark.unit
def test_weighted_scoring():
    """Test score calculation logic."""
    scores = ContentScores(
        seo_optimization=8.0,
        engagement=7.0,
        brand_consistency=9.0,
        accuracy=8.5
    )

    expected = 8.0*0.25 + 7.0*0.30 + 9.0*0.25 + 8.5*0.20
    assert abs(scores.overall_score - expected) < 0.01

    # Check priority logic
    priorities = scores.get_improvement_priorities()
    assert priorities[0] == "engagement"  # Lowest score with high weight

@pytest.mark.integration
async def test_iterative_improvement():
    """Test that quality improves across iterations."""
    session = init("critic_actor", config="examples/production/03_marketing_content/config.yaml")

    result = await session.query("Create blog post about AI productivity tools")

    # Verify improvement
    assert len(result.iteration_history) >= 2
    scores = [h.overall_score for h in result.iteration_history]
    assert scores[-1] >= scores[0]  # Final score >= initial score
```

#### Extension Points

1. **Custom Evaluation Metrics**: Add domain-specific scoring dimensions
2. **Brand Voice Training**: Fine-tune with brand-specific examples
3. **Multi-Language Support**: Extend for different languages
4. **Template Library**: Pre-built templates for different content types

---

### 13.5 IT Support Platform (Specialist Pool Pattern)

**Business Context**: Intelligent routing of IT support tickets to domain experts

#### Architecture Application

```
User Query → Router → Keyword Matching → Expert Selection → Expert(s) Execution
                                              ↓
                            [Network | Database | Security | Cloud]
```

**Keyword-Based Routing**:
```yaml
# config.yaml
specialists:
  network_expert:
    keywords:
      - vpn
      - firewall
      - dns
      - routing
      - bandwidth
    tools: [Bash, Read, Write]

  database_expert:
    keywords:
      - sql
      - query
      - index
      - transaction
      - backup
    tools: [Bash, Read, Write, Grep]

  security_expert:
    keywords:
      - authentication
      - permission
      - vulnerability
      - encryption
      - certificate
    tools: [Bash, Read, Write, Grep]

  cloud_expert:
    keywords:
      - aws
      - azure
      - kubernetes
      - docker
      - lambda
    tools: [Bash, Read, Write, WebSearch]

routing_strategy: multi_match  # single_best, multi_match, cascade
```

#### Key Implementation Patterns

**1. Multi-Dimensional Routing Algorithm**:
```python
@dataclass
class RoutingDecision:
    primary_expert: str
    secondary_experts: list[str]
    confidence: float
    keyword_matches: dict[str, list[str]]

class ExpertRouter:
    def route(self, query: str) -> RoutingDecision:
        """Route query to appropriate experts."""
        # Extract keywords
        query_keywords = self._extract_keywords(query.lower())

        # Score each expert
        scores = {}
        matches = {}

        for expert, config in self.specialists.items():
            matched_keywords = [kw for kw in config.keywords if kw in query_keywords]
            scores[expert] = len(matched_keywords)
            matches[expert] = matched_keywords

        # Sort by score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        if ranked[0][1] == 0:
            # No keyword matches, use fallback
            return RoutingDecision(
                primary_expert="general_support",
                secondary_experts=[],
                confidence=0.3,
                keyword_matches={}
            )

        # Check for multi-expert scenarios
        primary = ranked[0][0]
        secondary = [expert for expert, score in ranked[1:3] if score > 0]

        return RoutingDecision(
            primary_expert=primary,
            secondary_experts=secondary if len(secondary) > 0 else [],
            confidence=min(ranked[0][1] / 5.0, 1.0),  # Normalize to [0,1]
            keyword_matches=matches
        )
```

**2. Urgency Categorization with SLA**:
```python
@dataclass
class SupportTicket:
    query: str
    urgency: Literal["critical", "high", "medium", "low"]
    sla_hours: int  # Response time SLA

    @classmethod
    def categorize(cls, query: str) -> "SupportTicket":
        """Automatically categorize ticket urgency."""
        urgency_keywords = {
            "critical": ["down", "outage", "critical", "emergency", "production"],
            "high": ["error", "failed", "broken", "not working", "urgent"],
            "medium": ["slow", "issue", "problem", "help"],
            "low": ["question", "how to", "documentation", "feature request"]
        }

        query_lower = query.lower()
        for level, keywords in urgency_keywords.items():
            if any(kw in query_lower for kw in keywords):
                urgency = level
                break
        else:
            urgency = "low"

        sla_map = {"critical": 1, "high": 4, "medium": 24, "low": 72}

        return cls(
            query=query,
            urgency=urgency,
            sla_hours=sla_map[urgency]
        )
```

**3. Parallel Multi-Expert Consultation**:
```python
async def handle_multi_expert_query(self, ticket: SupportTicket, routing: RoutingDecision):
    """Handle queries requiring multiple experts."""
    # Dispatch primary and secondary experts in parallel
    tasks = [
        self._consult_expert(routing.primary_expert, ticket, role="primary")
    ]

    for expert in routing.secondary_experts:
        tasks.append(self._consult_expert(expert, ticket, role="secondary"))

    results = await asyncio.gather(*tasks)

    # Synthesize responses
    primary_response = results[0]
    secondary_responses = results[1:]

    return self._synthesize_response(primary_response, secondary_responses, routing)
```

#### Error Handling Strategy

```python
async def execute(self, prompt, tracker=None, transcript=None):
    # Categorize ticket
    ticket = SupportTicket.categorize(prompt)

    # Route to expert(s)
    routing = self.router.route(ticket.query)

    if routing.confidence < 0.5:
        logger.warning(f"Low routing confidence: {routing.confidence}")
        # Escalate to human or general support
        return await self._escalate_to_human(ticket, routing)

    try:
        if routing.secondary_experts:
            response = await self.handle_multi_expert_query(ticket, routing)
        else:
            response = await self._consult_expert(routing.primary_expert, ticket)
    except ExpertNotAvailableError as e:
        # Fallback to next best expert
        logger.warning(f"Primary expert unavailable: {e}")
        fallback = routing.secondary_experts[0] if routing.secondary_experts else "general_support"
        response = await self._consult_expert(fallback, ticket)

    return response
```

#### Testing Approach

```python
@pytest.mark.unit
def test_routing_logic():
    """Test expert routing algorithm."""
    router = ExpertRouter(load_config())

    # Test single-expert routing
    decision = router.route("VPN connection keeps dropping")
    assert decision.primary_expert == "network_expert"
    assert "vpn" in decision.keyword_matches["network_expert"]

    # Test multi-expert routing
    decision = router.route("Database query timeout in Kubernetes pod")
    assert decision.primary_expert == "database_expert"
    assert "cloud_expert" in decision.secondary_experts

@pytest.mark.unit
def test_urgency_categorization():
    """Test SLA assignment."""
    ticket1 = SupportTicket.categorize("Production database is down!")
    assert ticket1.urgency == "critical"
    assert ticket1.sla_hours == 1

    ticket2 = SupportTicket.categorize("How do I reset my password?")
    assert ticket2.urgency == "low"
    assert ticket2.sla_hours == 72
```

#### Extension Points

1. **Machine Learning Routing**: Replace keyword matching with ML classifier
2. **Expert Load Balancing**: Distribute tickets based on expert availability
3. **Escalation Paths**: Define multi-tier escalation workflows
4. **Knowledge Base Integration**: Auto-suggest KB articles before expert routing

---

### 13.6 Tech Decision Support (Debate Pattern)

**Business Context**: Structured decision-making for technology architecture choices

#### Architecture Application

```
Topic → Proponent (Pro Arguments) ↔ Opponent (Con Arguments) [3 rounds]
           ↓                             ↓
        Round 1: Opening Statements
        Round 2: Deep Analysis & Rebuttals
        Round 3: Final Arguments
           ↓
        Judge → Weighted Evaluation → Verdict + Recommendation
```

**Multi-Round Debate Structure**:
```yaml
# config.yaml
debate_config:
  rounds: 3
  round_structure:
    - name: opening
      time_limit_tokens: 1000
      focus: "Present main arguments"

    - name: analysis
      time_limit_tokens: 1500
      focus: "Deep dive into tradeoffs, rebut opponent"

    - name: closing
      time_limit_tokens: 800
      focus: "Summarize strongest points"

  evaluation_criteria:
    technical_feasibility:
      weight: 0.30
      description: "Can this be implemented with current resources?"

    cost_efficiency:
      weight: 0.25
      description: "TCO including development and operations"

    scalability:
      weight: 0.20
      description: "Ability to handle growth"

    team_expertise:
      weight: 0.15
      description: "Team's familiarity with technology"

    ecosystem_maturity:
      weight: 0.10
      description: "Tooling, community support, stability"
```

#### Key Implementation Patterns

**1. Structured Debate Rounds**:
```python
@dataclass
class DebateRound:
    round_number: int
    round_type: str  # opening, analysis, closing
    proponent_argument: str
    opponent_argument: str

    def serialize(self) -> dict:
        return {
            "round": self.round_number,
            "type": self.round_type,
            "pro": self.proponent_argument,
            "con": self.opponent_argument
        }

async def conduct_debate(self, topic: str) -> DebateTranscript:
    rounds = []
    context = {"topic": topic, "history": []}

    for i, round_config in enumerate(self.config.round_structure, 1):
        # Proponent speaks
        pro_prompt = self._build_round_prompt("proponent", round_config, context)
        pro_argument = await self.proponent.generate(pro_prompt)

        # Opponent responds (sees proponent's argument)
        context["last_pro_argument"] = pro_argument
        con_prompt = self._build_round_prompt("opponent", round_config, context)
        con_argument = await self.opponent.generate(con_prompt)

        # Record round
        round_data = DebateRound(i, round_config.name, pro_argument, con_argument)
        rounds.append(round_data)
        context["history"].append(round_data.serialize())

    return DebateTranscript(topic=topic, rounds=rounds)
```

**2. Weighted Multi-Criteria Evaluation**:
```python
@dataclass
class CriterionScore:
    criterion: str
    pro_score: float  # 0-10
    con_score: float  # 0-10
    weight: float
    justification: str

    @property
    def weighted_delta(self) -> float:
        """Positive favors pro, negative favors con."""
        return (self.pro_score - self.con_score) * self.weight

class DebateJudge:
    def evaluate(self, transcript: DebateTranscript) -> Verdict:
        """Evaluate debate across all criteria."""
        scores = []

        for criterion, config in self.evaluation_criteria.items():
            # Judge scores each side on this criterion
            score = self._score_criterion(
                criterion=criterion,
                pro_arguments=[r.proponent_argument for r in transcript.rounds],
                con_arguments=[r.opponent_argument for r in transcript.rounds],
                weight=config.weight
            )
            scores.append(score)

        # Calculate final verdict
        total_weighted_delta = sum(s.weighted_delta for s in scores)

        return Verdict(
            winner="proponent" if total_weighted_delta > 0 else "opponent",
            confidence=abs(total_weighted_delta) / sum(c.weight for c in self.evaluation_criteria.values()),
            criterion_scores=scores,
            summary=self._generate_summary(scores),
            recommendation=self._generate_recommendation(scores, total_weighted_delta)
        )
```

**3. Structured Decision Output**:
```json
// files/decision_report.json
{
  "decision_topic": "Microservices vs Monolith for new e-commerce platform",
  "debate_transcript": {
    "rounds": [
      {
        "round": 1,
        "type": "opening",
        "proponent": "Microservices offer...",
        "opponent": "Monolith provides..."
      },
      // ...
    ]
  },
  "evaluation": {
    "criteria_scores": [
      {
        "criterion": "technical_feasibility",
        "pro_score": 7.0,
        "con_score": 8.5,
        "weight": 0.30,
        "weighted_delta": -0.45,
        "justification": "Team has more experience with monoliths"
      },
      // ...
    ],
    "overall_winner": "opponent",
    "confidence": 0.72,
    "summary": "While microservices offer better scalability...",
    "recommendation": "Start with modular monolith, plan microservices migration for year 2"
  }
}
```

#### Error Handling Strategy

```python
async def conduct_debate(self, topic: str) -> DebateTranscript:
    rounds = []

    for i, round_config in enumerate(self.config.round_structure, 1):
        try:
            # Execute round
            round_data = await self._execute_round(i, round_config, rounds)
            rounds.append(round_data)
        except ArgumentGenerationError as e:
            if i == 1:
                # Can't proceed without opening round
                raise DebateFailedError(f"Failed at opening round: {e}")
            else:
                # Continue with partial debate
                logger.warning(f"Round {i} failed, proceeding to judgment with {len(rounds)} rounds")
                break

    if len(rounds) < 1:
        raise InsufficientDebateError("Need at least 1 complete round for judgment")

    return DebateTranscript(topic=topic, rounds=rounds)
```

#### Testing Approach

```python
@pytest.mark.integration
async def test_full_debate():
    """Test complete debate workflow."""
    session = init("debate", config="examples/production/05_tech_decision/config.yaml")

    result = await session.query("Should we adopt GraphQL or REST for our API?")

    # Verify structure
    assert len(result.rounds) == 3
    assert all(r.proponent_argument and r.opponent_argument for r in result.rounds)

    # Verify evaluation
    assert result.verdict.winner in ["proponent", "opponent"]
    assert 0 <= result.verdict.confidence <= 1
    assert len(result.verdict.criterion_scores) == 5

@pytest.mark.unit
def test_weighted_scoring():
    """Test multi-criteria scoring logic."""
    scores = [
        CriterionScore("tech", 8.0, 6.0, 0.30, "..."),  # +0.6
        CriterionScore("cost", 5.0, 7.0, 0.25, "..."),  # -0.5
        CriterionScore("scale", 9.0, 7.0, 0.20, "..."), # +0.4
    ]

    total = sum(s.weighted_delta for s in scores)
    assert total == 0.5  # Pro wins
```

#### Extension Points

1. **Multi-Option Debates**: Extend to 3+ alternatives
2. **Domain Expert Judges**: Specialized judges for different criteria
3. **Historical Decision Tracking**: Learn from past decisions
4. **Interactive Mode**: Allow human intervention between rounds

---

### 13.7 Code Debugger (Reflexion Pattern)

**Business Context**: AI-driven adaptive debugging for complex software issues

#### Architecture Application

```
┌─────────────────────────────────────────┐
│  while not solved and attempts < max:  │
│    Result = Executor.debug(strategy)   │
│    Analysis = Reflector.analyze(result)│
│    if Analysis.success: break          │
│    strategy = Adapter.improve(analysis)│
└─────────────────────────────────────────┘
```

**Strategy Library**:
```yaml
# config.yaml
debugging_strategies:
  - id: log_analysis
    name: "Log File Analysis"
    steps:
      - "Read error logs"
      - "Identify error patterns"
      - "Trace stack traces"
    success_indicators:
      - "Found root cause in logs"

  - id: code_inspection
    name: "Code Inspection"
    steps:
      - "Read relevant source files"
      - "Check recent changes (git diff)"
      - "Look for common anti-patterns"
    success_indicators:
      - "Identified problematic code"

  - id: runtime_debugging
    name: "Runtime Debugging"
    steps:
      - "Add debug print statements"
      - "Run with test inputs"
      - "Analyze execution flow"
    success_indicators:
      - "Pinpointed failure location"

  - id: dependency_check
    name: "Dependency Analysis"
    steps:
      - "Check library versions"
      - "Review recent updates"
      - "Test with different versions"
    success_indicators:
      - "Found version conflict"

max_debug_attempts: 5
reflection_depth: detailed  # quick, standard, detailed
```

#### Key Implementation Patterns

**1. Adaptive Strategy Selection**:
```python
@dataclass
class DebugAttempt:
    attempt_number: int
    strategy_used: str
    actions_taken: list[str]
    findings: str
    success: bool
    confidence: float
    time_taken: float

class ReflexiveDebugger:
    def __init__(self, strategies: list[DebugStrategy]):
        self.strategies = strategies
        self.attempt_history: list[DebugAttempt] = []

    async def debug(self, issue_description: str) -> DebugResult:
        """Reflexive debugging loop."""
        strategy_queue = self.strategies.copy()

        for attempt in range(self.max_attempts):
            # Select strategy
            if attempt == 0:
                strategy = strategy_queue[0]  # Start with first
            else:
                # Reflect on previous attempts
                reflection = await self._reflect_on_attempts()
                strategy = self._select_next_strategy(reflection, strategy_queue)

            # Execute strategy
            result = await self._execute_strategy(strategy, issue_description)

            # Record attempt
            attempt_data = DebugAttempt(
                attempt_number=attempt + 1,
                strategy_used=strategy.id,
                actions_taken=result.actions,
                findings=result.findings,
                success=result.success,
                confidence=result.confidence,
                time_taken=result.duration
            )
            self.attempt_history.append(attempt_data)

            if result.success:
                logger.info(f"Solved at attempt {attempt + 1} using {strategy.name}")
                break

            # Remove failed strategy from queue
            strategy_queue = [s for s in strategy_queue if s.id != strategy.id]
            if not strategy_queue:
                logger.error("All strategies exhausted")
                break

        return self._generate_debug_report()
```

**2. Structured Reflection**:
```python
@dataclass
class ReflectionAnalysis:
    """Analysis of debugging attempts."""
    patterns_observed: list[str]
    effective_actions: list[str]
    ineffective_actions: list[str]
    suggested_next_strategy: str
    confidence_trend: str  # improving, declining, stable
    hypothesis: str  # Current theory about root cause

async def _reflect_on_attempts(self) -> ReflectionAnalysis:
    """Analyze debugging history to inform next steps."""
    reflection_prompt = f"""
    Analyze these debugging attempts:

    {self._format_attempt_history()}

    Questions:
    1. What patterns emerge from the findings?
    2. Which actions yielded useful information?
    3. Which actions were dead ends?
    4. Based on evidence so far, what's the most likely root cause?
    5. What debugging strategy should we try next?
    """

    analysis = await self.reflector.analyze(reflection_prompt)
    return ReflectionAnalysis.parse(analysis)
```

**3. Success Pattern Learning**:
```python
class StrategyLearner:
    """Learn from successful debugging patterns."""

    def __init__(self):
        self.success_patterns: dict[str, list[DebugAttempt]] = {}

    def record_success(self, issue_type: str, attempt: DebugAttempt):
        """Record successful debugging approach."""
        if issue_type not in self.success_patterns:
            self.success_patterns[issue_type] = []
        self.success_patterns[issue_type].append(attempt)

    def suggest_strategy(self, issue_type: str) -> str | None:
        """Suggest strategy based on past successes."""
        if issue_type in self.success_patterns:
            # Find most successful strategy for this issue type
            successes = self.success_patterns[issue_type]
            strategy_counts = {}
            for attempt in successes:
                strategy_counts[attempt.strategy_used] = strategy_counts.get(attempt.strategy_used, 0) + 1

            # Return most frequently successful
            return max(strategy_counts.items(), key=lambda x: x[1])[0]
        return None
```

#### Error Handling Strategy

```python
async def debug(self, issue_description: str) -> DebugResult:
    try:
        # Execute reflexive loop
        for attempt in range(self.max_attempts):
            try:
                result = await self._execute_strategy(strategy, issue_description)
                self.attempt_history.append(result)

                if result.success:
                    return DebugResult(status="SOLVED", attempts=self.attempt_history)

            except StrategyExecutionError as e:
                # Strategy failed to execute
                logger.warning(f"Strategy {strategy.id} failed: {e}")
                self.attempt_history.append(DebugAttempt(
                    strategy_used=strategy.id,
                    success=False,
                    error=str(e)
                ))
                continue  # Try next strategy

        # All attempts exhausted
        return DebugResult(
            status="UNSOLVED",
            attempts=self.attempt_history,
            recommendation="Consider manual intervention or additional context"
        )

    except Exception as e:
        logger.error(f"Debugging session failed: {e}")
        return DebugResult(status="FAILED", error=str(e))
```

#### Testing Approach

```python
@pytest.mark.integration
async def test_reflexive_improvement():
    """Test that debugger adapts strategy based on reflection."""
    session = init("reflexion", config="examples/production/06_code_debugger/config.yaml")

    # Issue that requires strategy adaptation
    result = await session.query("App crashes on startup with no logs")

    # Verify reflexive behavior
    assert len(result.attempts) > 1  # Tried multiple strategies

    # Check that strategies changed based on reflection
    strategies_used = [a.strategy_used for a in result.attempts]
    assert len(set(strategies_used)) > 1  # Used different strategies

    # Verify learning
    assert result.reflection_analyses  # Performed reflections
    assert any("hypothesis" in r.dict() for r in result.reflection_analyses)

@pytest.mark.unit
def test_strategy_learning():
    """Test learning from successful patterns."""
    learner = StrategyLearner()

    # Record successes
    learner.record_success("null_pointer", DebugAttempt(strategy_used="code_inspection", success=True))
    learner.record_success("null_pointer", DebugAttempt(strategy_used="code_inspection", success=True))
    learner.record_success("null_pointer", DebugAttempt(strategy_used="runtime_debugging", success=True))

    # Should suggest most successful
    suggestion = learner.suggest_strategy("null_pointer")
    assert suggestion == "code_inspection"
```

#### Extension Points

1. **Custom Debugging Tools**: Add domain-specific debugging strategies
2. **Issue Classification**: Auto-categorize issues for better strategy selection
3. **Collaborative Debugging**: Multi-agent collaboration on complex issues
4. **Knowledge Base Integration**: Learn from past debugging sessions

---

### 13.8 Codebase Analysis (MapReduce Pattern)

**Business Context**: Large-scale technical debt and code quality analysis

#### Architecture Application

```
Codebase (500+ files)
    ↓
Intelligent Chunker (by_module, by_file_type, by_size, by_git_history)
    ↓
[Mapper 1: Module A] [Mapper 2: Module B] ... [Mapper N: Module N]
    ↓                      ↓                          ↓
  Issues JSON          Issues JSON                 Issues JSON
                           ↓
                    Reducer (Aggregate + Deduplicate + Prioritize)
                           ↓
              Comprehensive Analysis Report
```

**Intelligent Chunking Strategies**:
```yaml
# config.yaml
chunking_strategy: by_module  # by_module, by_file_type, by_size, by_git_history

strategies:
  by_module:
    description: "Group files by Python module/package"
    max_files_per_chunk: 50
    preserve_structure: true

  by_file_type:
    description: "Group by file extension"
    groups:
      python: ["*.py"]
      config: ["*.yaml", "*.json", "*.toml"]
      docs: ["*.md", "*.rst"]

  by_size:
    description: "Balance chunk sizes"
    target_chunk_size_kb: 500

  by_git_history:
    description: "Group frequently changed files together"
    use_git_blame: true
    activity_threshold: 10  # commits in last 90 days

analysis_tools:
  - pylint          # Code quality
  - bandit          # Security
  - radon           # Complexity metrics
  - mypy            # Type checking

max_parallel_mappers: 10
output_format: json
```

#### Key Implementation Patterns

**1. Intelligent Chunking**:
```python
from abc import ABC, abstractmethod
from pathlib import Path

class ChunkingStrategy(ABC):
    @abstractmethod
    def chunk(self, files: list[Path]) -> list[list[Path]]:
        """Split files into chunks for parallel processing."""
        pass

class ModuleChunker(ChunkingStrategy):
    def __init__(self, max_files_per_chunk: int = 50):
        self.max_files_per_chunk = max_files_per_chunk

    def chunk(self, files: list[Path]) -> list[list[Path]]:
        """Group files by Python module."""
        # Group by top-level module
        modules: dict[str, list[Path]] = {}

        for file in files:
            if file.suffix == ".py":
                # Extract module: src/foo/bar.py → foo
                parts = file.parts
                src_index = parts.index("src") if "src" in parts else 0
                module = parts[src_index + 1] if len(parts) > src_index + 1 else "root"

                if module not in modules:
                    modules[module] = []
                modules[module].append(file)

        # Split large modules
        chunks = []
        for module_files in modules.values():
            for i in range(0, len(module_files), self.max_files_per_chunk):
                chunks.append(module_files[i:i+self.max_files_per_chunk])

        return chunks

class SizeBalancedChunker(ChunkingStrategy):
    def __init__(self, target_chunk_size_kb: int = 500):
        self.target_size_bytes = target_chunk_size_kb * 1024

    def chunk(self, files: list[Path]) -> list[list[Path]]:
        """Create size-balanced chunks."""
        chunks = []
        current_chunk = []
        current_size = 0

        for file in sorted(files, key=lambda f: f.stat().st_size):
            file_size = file.stat().st_size

            if current_size + file_size > self.target_size_bytes and current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_size = 0

            current_chunk.append(file)
            current_size += file_size

        if current_chunk:
            chunks.append(current_chunk)

        return chunks
```

**2. Parallel Map with Progress Tracking**:
```python
@dataclass
class MapProgress:
    total_chunks: int
    completed_chunks: int = 0
    failed_chunks: int = 0
    current_mappers: list[str] = field(default_factory=list)

    @property
    def progress_pct(self) -> float:
        return (self.completed_chunks / self.total_chunks) * 100 if self.total_chunks > 0 else 0

async def parallel_map(self, chunks: list[list[Path]]) -> list[AnalysisResult]:
    """Execute mappers in parallel with progress tracking."""
    progress = MapProgress(total_chunks=len(chunks))

    # Create semaphore to limit parallelism
    semaphore = asyncio.Semaphore(self.max_parallel_mappers)

    async def map_with_progress(chunk_id: int, chunk: list[Path]):
        async with semaphore:
            mapper_id = f"mapper-{chunk_id}"
            progress.current_mappers.append(mapper_id)

            try:
                result = await self._run_mapper(chunk_id, chunk)
                progress.completed_chunks += 1
                logger.info(f"Progress: {progress.progress_pct:.1f}% ({progress.completed_chunks}/{progress.total_chunks})")
                return result

            except Exception as e:
                progress.failed_chunks += 1
                logger.error(f"Mapper {chunk_id} failed: {e}")
                return AnalysisResult(chunk_id=chunk_id, error=str(e))

            finally:
                progress.current_mappers.remove(mapper_id)

    # Execute all mappers
    tasks = [map_with_progress(i, chunk) for i, chunk in enumerate(chunks)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    return [r for r in results if isinstance(r, AnalysisResult)]
```

**3. Intelligent Reduction with Deduplication**:
```python
@dataclass
class CodeIssue:
    type: str  # security, quality, complexity, typing
    severity: str  # critical, high, medium, low
    file_path: str
    line_number: int
    message: str
    tool_source: str  # pylint, bandit, radon, mypy

    def fingerprint(self) -> str:
        """Generate fingerprint for deduplication."""
        return hashlib.md5(
            f"{self.file_path}:{self.line_number}:{self.type}:{self.message}".encode()
        ).hexdigest()

class IntelligentReducer:
    def reduce(self, mapper_results: list[AnalysisResult]) -> AnalysisReport:
        """Aggregate, deduplicate, and prioritize issues."""
        all_issues: dict[str, CodeIssue] = {}  # fingerprint → issue

        # Collect and deduplicate
        for result in mapper_results:
            for issue in result.issues:
                fingerprint = issue.fingerprint()
                if fingerprint not in all_issues:
                    all_issues[fingerprint] = issue

        issues = list(all_issues.values())

        # Prioritize
        priority_scores = {
            "critical": 100,
            "high": 50,
            "medium": 20,
            "low": 5
        }

        issues.sort(
            key=lambda i: (priority_scores.get(i.severity, 0), i.file_path),
            reverse=True
        )

        # Categorize
        by_type = self._group_by(issues, key=lambda i: i.type)
        by_severity = self._group_by(issues, key=lambda i: i.severity)
        by_file = self._group_by(issues, key=lambda i: i.file_path)

        # Generate statistics
        stats = AnalysisStatistics(
            total_files_analyzed=sum(len(r.files_analyzed) for r in mapper_results),
            total_issues=len(issues),
            by_severity={k: len(v) for k, v in by_severity.items()},
            by_type={k: len(v) for k, v in by_type.items()},
            top_problematic_files=self._get_top_problematic(by_file, n=10)
        )

        return AnalysisReport(
            timestamp=datetime.now(),
            issues=issues,
            statistics=stats,
            recommendations=self._generate_recommendations(issues, stats)
        )
```

**4. Structured Output Report**:
```json
// files/analysis_report.json
{
  "timestamp": "2024-12-25T10:30:00Z",
  "summary": {
    "total_files_analyzed": 523,
    "total_issues": 1247,
    "by_severity": {
      "critical": 12,
      "high": 87,
      "medium": 456,
      "low": 692
    },
    "by_type": {
      "security": 34,
      "quality": 567,
      "complexity": 234,
      "typing": 412
    }
  },
  "top_issues": [
    {
      "severity": "critical",
      "type": "security",
      "file": "src/auth/login.py",
      "line": 45,
      "message": "SQL injection vulnerability",
      "tool": "bandit"
    },
    // ...
  ],
  "top_problematic_files": [
    {
      "file": "src/core/processor.py",
      "issue_count": 47,
      "highest_severity": "high"
    },
    // ...
  ],
  "recommendations": [
    "Address 12 critical security issues immediately",
    "Refactor src/core/processor.py (47 issues)",
    "Add type hints to 89 functions missing annotations"
  ]
}
```

#### Error Handling Strategy

```python
async def execute(self, prompt, tracker=None, transcript=None):
    # Discover files
    try:
        files = await self._discover_codebase_files()
        if not files:
            raise EmptyCodebaseError("No files found to analyze")
    except Exception as e:
        raise CodebaseDiscoveryError(f"Failed to discover files: {e}")

    # Chunk files
    try:
        chunks = self.chunker.chunk(files)
        logger.info(f"Split {len(files)} files into {len(chunks)} chunks")
    except Exception as e:
        logger.error(f"Chunking failed: {e}")
        # Fallback: single chunk
        chunks = [files]

    # Map phase
    mapper_results = await self.parallel_map(chunks)

    # Check for failures
    failed = [r for r in mapper_results if r.error]
    if len(failed) > len(chunks) * 0.5:
        raise TooManyFailuresError(f"{len(failed)} of {len(chunks)} mappers failed")

    # Continue with successful results
    successful = [r for r in mapper_results if not r.error]

    # Reduce phase
    try:
        report = self.reducer.reduce(successful)
    except Exception as e:
        raise ReductionError(f"Failed to aggregate results: {e}")

    return report
```

#### Testing Approach

```python
@pytest.mark.integration
async def test_end_to_end_analysis():
    """Test complete MapReduce workflow."""
    session = init("mapreduce", config="examples/production/07_codebase_analysis/config.yaml")

    result = await session.query("Analyze ./test_codebase")

    # Verify report structure
    assert result.summary.total_files_analyzed > 0
    assert result.summary.total_issues >= 0
    assert all(k in result.summary.by_severity for k in ["critical", "high", "medium", "low"])

    # Verify deduplication
    fingerprints = [issue.fingerprint() for issue in result.issues]
    assert len(fingerprints) == len(set(fingerprints))  # No duplicates

@pytest.mark.unit
def test_chunking_strategies():
    """Test different chunking strategies."""
    files = list(Path("test_codebase").rglob("*.py"))

    # Test module chunking
    module_chunker = ModuleChunker(max_files_per_chunk=10)
    module_chunks = module_chunker.chunk(files)
    assert all(len(chunk) <= 10 for chunk in module_chunks)

    # Test size-balanced chunking
    size_chunker = SizeBalancedChunker(target_chunk_size_kb=100)
    size_chunks = size_chunker.chunk(files)
    # Verify size balance
    chunk_sizes = [sum(f.stat().st_size for f in chunk) for chunk in size_chunks]
    assert max(chunk_sizes) - min(chunk_sizes) < 200 * 1024  # Within 200KB variance
```

#### Extension Points

1. **Custom Analysis Tools**: Add domain-specific linters/analyzers
2. **Incremental Analysis**: Only analyze changed files (git diff integration)
3. **Trend Tracking**: Compare with historical reports, track improvements
4. **Auto-Fix Suggestions**: Generate patches for common issues

---

### 13.9 Common Production Patterns

All production examples share these implementation patterns:

#### Configuration-Driven Design

```python
# Standard config.yaml structure
from pydantic import BaseModel, Field

class ProductionConfig(BaseModel):
    """Base configuration for production examples."""

    # Architecture-specific settings
    architecture_config: dict = Field(...)

    # Model configuration
    lead_model: str = "haiku"
    subagent_model: str = "haiku"

    # Output configuration
    output_dir: str = "files"
    log_dir: str = "logs"

    # Feature flags
    enable_logging: bool = True
    enable_metrics: bool = True

    class Config:
        extra = "allow"  # Allow architecture-specific fields
```

#### Structured JSON Results

```python
# All examples output structured JSON for programmatic consumption
@dataclass
class ExecutionResult:
    """Standard result format."""
    status: Literal["success", "partial", "failed"]
    timestamp: str
    session_id: str
    outputs: dict[str, Path]  # output_type → file_path
    metrics: dict[str, Any]
    errors: list[str]

    def to_json(self, path: Path):
        """Save as JSON."""
        with open(path, 'w') as f:
            json.dump(asdict(self), f, indent=2, default=str)
```

#### Comprehensive Error Handling

```python
# Standard error handling pattern
async def execute(self, prompt, tracker=None, transcript=None):
    try:
        # Main execution logic
        result = await self._execute_workflow(prompt)
        return ExecutionResult(status="success", ...)

    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        return ExecutionResult(status="failed", errors=[str(e)])

    except ToolExecutionError as e:
        logger.error(f"Tool execution failed: {e}")
        # Attempt graceful degradation
        return self._handle_tool_failure(e)

    except Exception as e:
        logger.exception("Unexpected error")
        return ExecutionResult(status="failed", errors=[f"Unexpected: {str(e)}"])
```

#### Dual-Format Logging

```python
# JSONL for programmatic analysis + Human-readable for debugging
class ProductionLogger:
    def __init__(self, session_dir: Path):
        self.jsonl_log = open(session_dir / "events.jsonl", 'w')
        self.human_log = open(session_dir / "session.log", 'w')

    def log_event(self, event_type: str, data: dict):
        # Machine-readable
        entry = {"timestamp": datetime.now().isoformat(), "event": event_type, **data}
        self.jsonl_log.write(json.dumps(entry) + '\n')
        self.jsonl_log.flush()

        # Human-readable
        self.human_log.write(f"[{entry['timestamp']}] {event_type}: {data}\n")
        self.human_log.flush()
```

#### Multi-Tier Testing

```python
# tests/test_example.py

# Unit tests - fast, isolated
@pytest.mark.unit
def test_config_validation():
    config = ExampleConfig(...)
    assert config.validate()

# Integration tests - test component interaction
@pytest.mark.integration
async def test_workflow_stages():
    session = init("example")
    result = await session.execute_stage("stage1")
    assert result.success

# E2E tests - full workflow
@pytest.mark.e2e
async def test_full_example():
    session = init("example")
    result = await session.query("Full test query")
    assert result.status == "success"
    assert result.outputs["report"].exists()
```

---

### 13.10 Extending Production Examples

#### Adding Custom Business Logic

```python
# examples/production/XX_custom_example/custom_logic.py

from claude_agent_framework import BaseArchitecture, register_architecture

@register_architecture("custom_example")
class CustomExampleArchitecture(BaseArchitecture):
    """Custom architecture extending framework patterns."""

    def __init__(self, config: CustomConfig):
        super().__init__()
        self.config = config

        # Add custom components
        self.custom_processor = CustomProcessor(config)
        self.custom_validator = CustomValidator(config.validation_rules)

    async def execute(self, prompt, tracker=None, transcript=None):
        # Pre-process with custom logic
        processed_prompt = self.custom_processor.prepare(prompt)

        # Execute base architecture workflow
        result = await super().execute(processed_prompt, tracker, transcript)

        # Post-process with validation
        validated_result = self.custom_validator.validate(result)

        return validated_result
```

#### Composing Multiple Patterns

```python
# Combine Research + Critic-Actor for comprehensive analysis

async def hybrid_workflow(query: str):
    """Research phase followed by iterative refinement."""

    # Phase 1: Research (parallel data gathering)
    research_session = init("research")
    research_data = await research_session.query(query)

    # Phase 2: Critic-Actor (refine analysis)
    critic_session = init("critic_actor", context=research_data)
    refined_output = await critic_session.query("Refine the research findings")

    return refined_output
```

---

## Summary

1. **Multiple Patterns**: 7 distinct orchestration patterns for different problem domains
2. **Pattern Selection**: Choose based on task characteristics (parallel vs sequential, iterative vs one-shot)
3. **Separation of Concerns**: Lead Agent orchestrates, Subagents execute specialized tasks
4. **Tool Constraints**: Principle of least privilege, precise tool control per agent
5. **Observability**: Hook mechanism + JSONL audit logs for full traceability
6. **Cost Optimization**: Subagents use Haiku model for cost efficiency
7. **Prompt Engineering**: Structured templates with clear role boundaries
8. **Error Handling**: Graceful degradation, ensure resource cleanup

### Pattern Quick Reference

| Pattern | When to Use |
|---------|-------------|
| **Research** | Need to gather data from multiple sources in parallel |
| **Pipeline** | Sequential stages with clear handoffs |
| **Critic-Actor** | Iterative quality improvement through feedback |
| **Specialist Pool** | Routing queries to domain experts |
| **Debate** | Balanced analysis of pros and cons |
| **Reflexion** | Complex problems requiring self-reflection |
| **MapReduce** | Large-scale parallel processing with aggregation |

### Applicable Scenarios

- Multi-step research tasks
- Data collection and analysis pipelines
- Document generation automation
- Complex workflow orchestration
- Decision support systems
- Large-scale content analysis

---

*Document generated: 2024-12-25*
*Based on: Claude Agent Framework v0.3.0*
