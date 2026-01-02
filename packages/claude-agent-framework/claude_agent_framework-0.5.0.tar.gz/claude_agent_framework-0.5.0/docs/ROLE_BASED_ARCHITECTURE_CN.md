# 角色类型系统架构

## 概述

角色类型系统是 Claude Agent Framework 的核心设计模式，它将**架构定义的角色类型（抽象）**与**业务配置的具体代理（具体）**分离，实现一个架构支持多种业务场景。

### 设计目标

```
传统模式：架构定义具体 agent 名称 → 业务模板必须匹配名称
角色模式：架构定义角色类型 → 业务配置实例化具体 agent
```

### 核心优势

| 优势 | 说明 |
|------|------|
| **业务复用** | 同一架构可支持多种业务场景 |
| **职责明确** | 角色定义约束，实例配置细节 |
| **验证机制** | 自动验证代理配置是否满足角色约束 |
| **提示组合** | 多层提示优先级，灵活定制 |

---

## 核心概念

### 1. RoleType（角色类型枚举）

定义代理的语义角色类型：

```python
from claude_agent_framework.core.types import RoleType

class RoleType(str, Enum):
    COORDINATOR = "coordinator"   # 协调者
    WORKER = "worker"             # 工作者
    PROCESSOR = "processor"       # 处理者
    SYNTHESIZER = "synthesizer"   # 综合者
    CRITIC = "critic"             # 批评者
    JUDGE = "judge"               # 裁判
    SPECIALIST = "specialist"     # 专家
    ADVOCATE = "advocate"         # 倡导者
    MAPPER = "mapper"             # 映射者
    REDUCER = "reducer"           # 归约者
    EXECUTOR = "executor"         # 执行者
    REFLECTOR = "reflector"       # 反思者
```

### 2. RoleCardinality（角色基数）

定义角色的数量约束：

```python
from claude_agent_framework.core.types import RoleCardinality

class RoleCardinality(str, Enum):
    EXACTLY_ONE = "exactly_one"   # 必须恰好 1 个
    ONE_OR_MORE = "one_or_more"   # 至少 1 个（1-N）
    ZERO_OR_MORE = "zero_or_more" # 任意数量（0-N）
    ZERO_OR_ONE = "zero_or_one"   # 可选（0-1）
```

### 3. RoleDefinition（角色定义）

架构级别的角色约束定义：

```python
from claude_agent_framework.core.roles import RoleDefinition

@dataclass
class RoleDefinition:
    role_type: RoleType           # 角色类型
    description: str = ""         # 角色描述
    required_tools: list[str]     # 必需工具
    optional_tools: list[str]     # 可选工具
    cardinality: RoleCardinality  # 数量约束
    default_model: str = "haiku"  # 默认模型
    prompt_file: str = ""         # 基础提示文件
```

### 4. AgentInstanceConfig（代理实例配置）

业务级别的具体代理配置：

```python
from claude_agent_framework.core.roles import AgentInstanceConfig

@dataclass
class AgentInstanceConfig:
    name: str                     # 代理名称
    role: str                     # 角色 ID
    description: str = ""         # 代理描述
    tools: list[str] = []         # 额外工具
    prompt: str = ""              # 直接提示内容
    prompt_file: str = ""         # 提示文件路径
    model: str = ""               # 模型覆盖
    metadata: dict[str, Any] = {} # 元数据
```

### 5. RoleRegistry（角色注册表）

验证代理配置是否满足角色约束：

```python
from claude_agent_framework.core.roles import RoleRegistry

registry = RoleRegistry()

# 注册角色定义
registry.register("worker", worker_role_def)
registry.register("processor", processor_role_def)

# 验证代理实例
errors = registry.validate_agents(agent_instances)
if errors:
    raise ValueError(f"配置错误: {errors}")
```

---

## 使用示例

### Python API 使用

```python
from claude_agent_framework import create_session
from claude_agent_framework.core.roles import AgentInstanceConfig

# 定义代理实例
agents = [
    AgentInstanceConfig(
        name="market-researcher",
        role="worker",
        description="市场数据收集专家",
        prompt_file="prompts/market_researcher.txt",
    ),
    AgentInstanceConfig(
        name="tech-researcher",
        role="worker",
        description="技术趋势分析专家",
        prompt_file="prompts/tech_researcher.txt",
    ),
    AgentInstanceConfig(
        name="data-analyst",
        role="processor",
        model="sonnet",
        description="数据分析师",
    ),
    AgentInstanceConfig(
        name="report-writer",
        role="synthesizer",
        description="报告撰写专家",
    ),
]

# 创建会话
session = create_session(
    "research",
    agent_instances=agents,
    business_template="competitive_intelligence",  # 可选：业务模板
)

# 执行
async for msg in session.run("分析 AI 市场趋势"):
    print(msg)
```

### YAML 配置格式

```yaml
# config.yaml
architecture: research

agents:
  - name: market-researcher
    role: worker
    description: 市场数据收集专家
    prompt_file: prompts/market_researcher.txt

  - name: tech-researcher
    role: worker
    description: 技术趋势分析专家
    prompt_file: prompts/tech_researcher.txt

  - name: data-analyst
    role: processor
    model: sonnet
    description: 数据分析师

  - name: report-writer
    role: synthesizer
    description: 报告撰写专家

prompts:
  business_template: competitive_intelligence

settings:
  research_depth: deep
```

---

## 架构角色映射

每个架构定义了特定的角色类型：

| 架构 | 角色定义 | 说明 |
|------|---------|------|
| **research** | worker (1+), processor (0-1), synthesizer (1) | 主从协调模式 |
| **pipeline** | stage_executor (1+) | 顺序流水线 |
| **critic_actor** | actor (1), critic (1) | 生成-评估循环 |
| **specialist_pool** | specialist (1+) | 专家路由池 |
| **debate** | advocate (2+), judge (1) | 辩论决策 |
| **reflexion** | executor (1), reflector (1) | 执行-反思循环 |
| **mapreduce** | mapper (1+), reducer (1) | 并行映射-归约 |

### Research 架构角色定义示例

```python
def get_role_definitions(self) -> dict[str, RoleDefinition]:
    return {
        "worker": RoleDefinition(
            role_type=RoleType.WORKER,
            description="通过网络搜索收集研究数据，保存到 files/research_notes/",
            required_tools=["WebSearch"],
            optional_tools=["Write", "Skill", "Read"],
            cardinality=RoleCardinality.ONE_OR_MORE,
            default_model="haiku",
            prompt_file="worker.txt",
        ),
        "processor": RoleDefinition(
            role_type=RoleType.PROCESSOR,
            description="分析研究数据并生成可视化，保存到 files/charts/",
            required_tools=["Read", "Write"],
            optional_tools=["Glob", "Bash", "Skill"],
            cardinality=RoleCardinality.ZERO_OR_ONE,
            default_model="haiku",
            prompt_file="processor.txt",
        ),
        "synthesizer": RoleDefinition(
            role_type=RoleType.SYNTHESIZER,
            description="生成最终报告，保存到 files/reports/",
            required_tools=["Write"],
            optional_tools=["Skill", "Read", "Glob", "Bash"],
            cardinality=RoleCardinality.EXACTLY_ONE,
            default_model="haiku",
            prompt_file="synthesizer.txt",
        ),
    }
```

---

## 提示优先级

系统支持多层提示组合，按优先级从高到低：

1. **AgentInstanceConfig.prompt** - 直接指定的提示内容（最高）
2. **prompt_overrides[agent_name]** - Session 级别覆盖
3. **custom_prompts_dir/<agent_name>.txt** - 自定义提示目录
4. **business_templates/<template>/<agent_name>.txt** - 业务模板
5. **RoleDefinition.prompt_file** - 角色基础提示（最低）

### 提示组合示例

```python
session = create_session(
    "research",
    agent_instances=agents,
    business_template="competitive_intelligence",  # 层级 4
    custom_prompts_dir="./my_prompts",              # 层级 3
    prompt_overrides={                              # 层级 2
        "market-researcher": "专注于中国市场数据...",
    },
    template_vars={                                  # 变量替换
        "company_name": "Acme Corp",
        "industry": "人工智能",
    },
)
```

---

## 验证机制

### 自动验证

RoleRegistry 自动验证代理配置：

```python
# 验证规则
errors = registry.validate_agents(agents)

# 可能的错误类型：
# - "Missing required role 'synthesizer' (cardinality: exactly_one)"
# - "Role 'processor' allows at most 1 agent, but got 2"
# - "Unknown role 'invalid_role' for agent 'my-agent'"
```

### 验证规则

| 基数 | 验证规则 |
|------|---------|
| EXACTLY_ONE | 必须恰好 1 个代理 |
| ONE_OR_MORE | 至少 1 个代理 |
| ZERO_OR_MORE | 无数量限制 |
| ZERO_OR_ONE | 最多 1 个代理 |

---

## 与 business_templates 和 skills 的兼容

### business_templates 支持

业务模板继续完全支持，作为提示优先级层级 4：

```
business_templates/
└── competitive_intelligence/
    ├── lead.txt              # 主代理提示
    ├── market-researcher.txt # 特定代理提示
    └── tech-researcher.txt
```

### skills 支持

Skills 通过 Claude Agent SDK 原生支持：

1. **配置方式**: `setting_sources=["project", "user"]`
2. **启用方式**: 在 `optional_tools` 中包含 `"Skill"`
3. **加载位置**: `.claude/skills/*/SKILL.md`

```python
# 角色定义中包含 Skill 工具
"worker": RoleDefinition(
    role_type=RoleType.WORKER,
    required_tools=["WebSearch"],
    optional_tools=["Write", "Skill", "Read"],  # Skill 工具
    ...
)
```

---

## 自定义架构

### 实现新架构

```python
from claude_agent_framework.core import register_architecture, BaseArchitecture
from claude_agent_framework.core.roles import RoleDefinition
from claude_agent_framework.core.types import RoleType, RoleCardinality

@register_architecture("my_custom")
class MyCustomArchitecture(BaseArchitecture):
    name = "my_custom"
    description = "自定义架构"

    def get_role_definitions(self) -> dict[str, RoleDefinition]:
        return {
            "executor": RoleDefinition(
                role_type=RoleType.EXECUTOR,
                description="执行任务",
                required_tools=["Bash", "Write"],
                optional_tools=["Read", "Glob"],
                cardinality=RoleCardinality.ONE_OR_MORE,
                default_model="haiku",
                prompt_file="executor.txt",
            ),
            "reviewer": RoleDefinition(
                role_type=RoleType.CRITIC,
                description="审查结果",
                required_tools=["Read"],
                optional_tools=["Write"],
                cardinality=RoleCardinality.EXACTLY_ONE,
                default_model="sonnet",
                prompt_file="reviewer.txt",
            ),
        }

    async def execute(self, prompt, tracker=None, transcript=None):
        # 实现执行逻辑
        ...
```

---

## API 参考

### create_session 参数

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

| 参数 | 类型 | 说明 |
|------|------|------|
| architecture | str | 架构名称 |
| model | str | 默认模型 |
| agent_instances | list[AgentInstanceConfig] | 代理实例配置 |
| business_template | str | 业务模板名称 |
| custom_prompts_dir | Path | 自定义提示目录 |
| prompt_overrides | dict | 代理提示覆盖 |
| template_vars | dict | 模板变量 |

---

## 最佳实践

### 1. 角色定义原则

- **最小化必需工具**: 只包含角色必须的工具
- **合理的基数**: 根据业务需求选择合适的基数
- **清晰的描述**: 描述应说明角色职责和输出位置

### 2. 代理配置原则

- **语义化命名**: 代理名称应反映其业务功能
- **提示分层**: 利用提示优先级实现复用
- **模型匹配**: 根据任务复杂度选择模型

### 3. 提示组织

```
my_project/
├── prompts/                    # 自定义提示
│   ├── market-researcher.txt
│   └── tech-researcher.txt
├── business_templates/         # 业务模板
│   └── competitive_intel/
│       ├── lead.txt
│       └── ...
└── config.yaml                 # 配置文件
```

---

## 相关文档

- [README.md](../README.md) - 项目概述
- [BEST_PRACTICES_CN.md](./BEST_PRACTICES_CN.md) - 最佳实践
- [核心 API 文档](./api/core_cn.md) - API 参考
- [架构选择指南](./guides/architecture_selection/GUIDE_CN.md) - 选择合适的架构
