# Role-Based Architecture System

## Overview

The Role-Based Architecture System is a core design pattern in Claude Agent Framework that separates **architecture-defined role types (abstract)** from **business-configured agent instances (concrete)**, enabling a single architecture to support multiple business scenarios.

### Design Goal

```
Traditional: Architecture defines specific agent names → Business templates must match names
Role-Based:  Architecture defines role types → Business config instantiates specific agents
```

### Key Benefits

| Benefit | Description |
|---------|-------------|
| **Business Reuse** | Same architecture supports multiple business scenarios |
| **Clear Separation** | Role definitions set constraints, instance configs set details |
| **Validation** | Automatic validation that agent configs satisfy role constraints |
| **Prompt Composition** | Multi-layer prompt priority for flexible customization |

---

## Core Concepts

### 1. RoleType (Role Type Enum)

Defines the semantic role type of an agent:

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

### 2. RoleCardinality (Role Cardinality)

Defines quantity constraints for roles:

```python
from claude_agent_framework.core.types import RoleCardinality

class RoleCardinality(str, Enum):
    EXACTLY_ONE = "exactly_one"   # Must have exactly 1
    ONE_OR_MORE = "one_or_more"   # At least 1 (1-N)
    ZERO_OR_MORE = "zero_or_more" # Any number (0-N)
    ZERO_OR_ONE = "zero_or_one"   # Optional (0-1)
```

### 3. RoleDefinition (Role Definition)

Architecture-level role constraint definition:

```python
from claude_agent_framework.core.roles import RoleDefinition

@dataclass
class RoleDefinition:
    role_type: RoleType           # Role type
    description: str = ""         # Role description
    required_tools: list[str]     # Required tools
    optional_tools: list[str]     # Optional tools
    cardinality: RoleCardinality  # Quantity constraint
    default_model: str = "haiku"  # Default model
    prompt_file: str = ""         # Base prompt file
```

### 4. AgentInstanceConfig (Agent Instance Configuration)

Business-level concrete agent configuration:

```python
from claude_agent_framework.core.roles import AgentInstanceConfig

@dataclass
class AgentInstanceConfig:
    name: str                     # Agent name
    role: str                     # Role ID
    description: str = ""         # Agent description
    tools: list[str] = []         # Additional tools
    prompt: str = ""              # Direct prompt content
    prompt_file: str = ""         # Prompt file path
    model: str = ""               # Model override
    metadata: dict[str, Any] = {} # Metadata
```

### 5. RoleRegistry (Role Registry)

Validates agent configurations against role constraints:

```python
from claude_agent_framework.core.roles import RoleRegistry

registry = RoleRegistry()

# Register role definitions
registry.register("worker", worker_role_def)
registry.register("processor", processor_role_def)

# Validate agent instances
errors = registry.validate_agents(agent_instances)
if errors:
    raise ValueError(f"Configuration errors: {errors}")
```

---

## Usage Examples

### Python API Usage

```python
from claude_agent_framework import create_session
from claude_agent_framework.core.roles import AgentInstanceConfig

# Define agent instances
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
        description="Data analyst",
    ),
    AgentInstanceConfig(
        name="report-writer",
        role="synthesizer",
        description="Report writing specialist",
    ),
]

# Create session
session = create_session(
    "research",
    agent_instances=agents,
    business_template="competitive_intelligence",  # Optional: business template
)

# Execute
async for msg in session.run("Analyze AI market trends"):
    print(msg)
```

### YAML Configuration Format

```yaml
# config.yaml
architecture: research

agents:
  - name: market-researcher
    role: worker
    description: Market data collection specialist
    prompt_file: prompts/market_researcher.txt

  - name: tech-researcher
    role: worker
    description: Technology trends analyst
    prompt_file: prompts/tech_researcher.txt

  - name: data-analyst
    role: processor
    model: sonnet
    description: Data analyst

  - name: report-writer
    role: synthesizer
    description: Report writing specialist

prompts:
  business_template: competitive_intelligence

settings:
  research_depth: deep
```

---

## Architecture Role Mappings

Each architecture defines specific role types:

| Architecture | Role Definitions | Pattern |
|--------------|-----------------|---------|
| **research** | worker (1+), processor (0-1), synthesizer (1) | Master-worker coordination |
| **pipeline** | stage_executor (1+) | Sequential pipeline |
| **critic_actor** | actor (1), critic (1) | Generate-evaluate loop |
| **specialist_pool** | specialist (1+) | Expert routing pool |
| **debate** | advocate (2+), judge (1) | Debate deliberation |
| **reflexion** | executor (1), reflector (1) | Execute-reflect cycle |
| **mapreduce** | mapper (1+), reducer (1) | Parallel map-reduce |

### Research Architecture Role Definition Example

```python
def get_role_definitions(self) -> dict[str, RoleDefinition]:
    return {
        "worker": RoleDefinition(
            role_type=RoleType.WORKER,
            description="Gather research data via web search, save to files/research_notes/",
            required_tools=["WebSearch"],
            optional_tools=["Write", "Skill", "Read"],
            cardinality=RoleCardinality.ONE_OR_MORE,
            default_model="haiku",
            prompt_file="worker.txt",
        ),
        "processor": RoleDefinition(
            role_type=RoleType.PROCESSOR,
            description="Analyze research data and generate visualizations, save to files/charts/",
            required_tools=["Read", "Write"],
            optional_tools=["Glob", "Bash", "Skill"],
            cardinality=RoleCardinality.ZERO_OR_ONE,
            default_model="haiku",
            prompt_file="processor.txt",
        ),
        "synthesizer": RoleDefinition(
            role_type=RoleType.SYNTHESIZER,
            description="Generate final reports, save to files/reports/",
            required_tools=["Write"],
            optional_tools=["Skill", "Read", "Glob", "Bash"],
            cardinality=RoleCardinality.EXACTLY_ONE,
            default_model="haiku",
            prompt_file="synthesizer.txt",
        ),
    }
```

---

## Prompt Priority

The system supports multi-layer prompt composition, from highest to lowest priority:

1. **AgentInstanceConfig.prompt** - Directly specified prompt content (highest)
2. **prompt_overrides[agent_name]** - Session-level override
3. **custom_prompts_dir/<agent_name>.txt** - Custom prompts directory
4. **business_templates/<template>/<agent_name>.txt** - Business template
5. **RoleDefinition.prompt_file** - Role base prompt (lowest)

### Prompt Composition Example

```python
session = create_session(
    "research",
    agent_instances=agents,
    business_template="competitive_intelligence",  # Layer 4
    custom_prompts_dir="./my_prompts",              # Layer 3
    prompt_overrides={                              # Layer 2
        "market-researcher": "Focus on China market data...",
    },
    template_vars={                                  # Variable substitution
        "company_name": "Acme Corp",
        "industry": "Artificial Intelligence",
    },
)
```

---

## Validation Mechanism

### Automatic Validation

RoleRegistry automatically validates agent configurations:

```python
# Validation rules
errors = registry.validate_agents(agents)

# Possible error types:
# - "Missing required role 'synthesizer' (cardinality: exactly_one)"
# - "Role 'processor' allows at most 1 agent, but got 2"
# - "Unknown role 'invalid_role' for agent 'my-agent'"
```

### Validation Rules

| Cardinality | Validation Rule |
|-------------|----------------|
| EXACTLY_ONE | Must have exactly 1 agent |
| ONE_OR_MORE | Must have at least 1 agent |
| ZERO_OR_MORE | No quantity limit |
| ZERO_OR_ONE | At most 1 agent |

---

## Compatibility with business_templates and skills

### business_templates Support

Business templates remain fully supported as prompt priority layer 4:

```
business_templates/
└── competitive_intelligence/
    ├── lead.txt              # Lead agent prompt
    ├── market-researcher.txt # Specific agent prompt
    └── tech-researcher.txt
```

### skills Support

Skills are natively supported via Claude Agent SDK:

1. **Configuration**: `setting_sources=["project", "user"]`
2. **Enabling**: Include `"Skill"` in `optional_tools`
3. **Loading location**: `.claude/skills/*/SKILL.md`

```python
# Role definition includes Skill tool
"worker": RoleDefinition(
    role_type=RoleType.WORKER,
    required_tools=["WebSearch"],
    optional_tools=["Write", "Skill", "Read"],  # Skill tool
    ...
)
```

---

## Custom Architectures

### Implementing a New Architecture

```python
from claude_agent_framework.core import register_architecture, BaseArchitecture
from claude_agent_framework.core.roles import RoleDefinition
from claude_agent_framework.core.types import RoleType, RoleCardinality

@register_architecture("my_custom")
class MyCustomArchitecture(BaseArchitecture):
    name = "my_custom"
    description = "Custom architecture"

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
                optional_tools=["Write"],
                cardinality=RoleCardinality.EXACTLY_ONE,
                default_model="sonnet",
                prompt_file="reviewer.txt",
            ),
        }

    async def execute(self, prompt, tracker=None, transcript=None):
        # Implement execution logic
        ...
```

---

## API Reference

### create_session Parameters

```python
def create_session(
    architecture: str = "research",
    *,
    model: str = "haiku",
    agent_instances: list[AgentInstanceConfig] | None = None,
    business_template: str | None = None,
    prompts_dir: Path | str | None = None,
    custom_prompts_dir: Path | str | None = None,
    prompt_overrides: dict[str, str] | None = None,
    template_vars: dict[str, Any] | None = None,
    files_dir: Path | str | None = None,
    log_dir: Path | str | None = None,
    plugins: list[BasePlugin] | None = None,
    **arch_kwargs: Any,
) -> AgentSession:
```

| Parameter | Type | Description |
|-----------|------|-------------|
| architecture | str | Architecture name |
| model | str | Default model |
| agent_instances | list[AgentInstanceConfig] | Agent instance configurations |
| business_template | str | Business template name |
| custom_prompts_dir | Path | Custom prompts directory |
| prompt_overrides | dict | Agent prompt overrides |
| template_vars | dict | Template variables |

---

## Best Practices

### 1. Role Definition Principles

- **Minimize required tools**: Include only essential tools for the role
- **Appropriate cardinality**: Choose cardinality based on business needs
- **Clear descriptions**: Describe role responsibilities and output locations

### 2. Agent Configuration Principles

- **Semantic naming**: Agent names should reflect business function
- **Layered prompts**: Leverage prompt priority for reuse
- **Model matching**: Select model based on task complexity

### 3. Prompt Organization

```
my_project/
├── prompts/                    # Custom prompts
│   ├── market-researcher.txt
│   └── tech-researcher.txt
├── business_templates/         # Business templates
│   └── competitive_intel/
│       ├── lead.txt
│       └── ...
└── config.yaml                 # Configuration file
```

---

## Related Documentation

- [README.md](../README.md) - Project overview
- [BEST_PRACTICES.md](./BEST_PRACTICES.md) - Best practices
- [Core API Documentation](./api/core.md) - API reference
- [Architecture Selection Guide](./guides/architecture_selection/GUIDE.md) - Choosing the right architecture
