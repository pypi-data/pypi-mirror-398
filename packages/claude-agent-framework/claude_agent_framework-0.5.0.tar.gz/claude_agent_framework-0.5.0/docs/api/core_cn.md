# 核心API参考

**版本**: 1.0.0
**最后更新**: 2025-12-26

本文档提供 Claude Agent Framework 核心组件的完整 API 参考。

---

## 目录

1. [初始化API](#初始化api)
2. [AgentSession](#agentsession)
3. [BaseArchitecture](#basearchitecture)
4. [角色类型系统](#角色类型系统)
5. [配置类](#配置类)
6. [工具函数](#工具函数)

---

## 初始化API

### `create_session()`

初始化框架的推荐入口点。

```python
def create_session(
    architecture: ArchitectureType = "research",
    *,
    model: ModelType = "haiku",
    agent_instances: list[AgentInstanceConfig] | None = None,
    prompts_dir: Path | str | None = None,
    template_vars: dict[str, Any] | None = None,
    verbose: bool = False,
    log_dir: Path | str | None = None,
    files_dir: Path | str | None = None,
) -> AgentSession
```

**参数**:

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `architecture` | `ArchitectureType` | `"research"` | 要使用的架构模式。选项: `"research"`, `"pipeline"`, `"critic_actor"`, `"specialist_pool"`, `"debate"`, `"reflexion"`, `"mapreduce"` |
| `model` | `ModelType` | `"haiku"` | 代理的默认模型。选项: `"haiku"`, `"sonnet"`, `"opus"` |
| `agent_instances` | `list[AgentInstanceConfig] \| None` | `None` | 基于角色的智能体实例配置 |
| `prompts_dir` | `Path \| str \| None` | `None` | 业务提示词的自定义目录 |
| `template_vars` | `dict[str, Any] \| None` | `None` | 提示词模板变量 |
| `verbose` | `bool` | `False` | 启用调试日志 |
| `log_dir` | `Path \| str \| None` | `None` | 日志的自定义目录(默认: `logs/`) |
| `files_dir` | `Path \| str \| None` | `None` | 输出文件的自定义目录(默认: `files/`) |

**返回值**: `AgentSession` - 可立即使用的会话对象

**异常**:
- `InitializationError` - 如果未设置 `ANTHROPIC_API_KEY` 或未知架构

**示例**:

```python
from claude_agent_framework import create_session

# 简单使用
session = create_session("research")

# 带选项
session = create_session(
    "pipeline",
    model="sonnet",
    verbose=True,
    log_dir="my_logs"
)

# 使用会话
async for msg in session.run("分析市场趋势"):
    print(msg)
```

---

### `quick_query()`

用于一次性查询的便捷函数。

```python
async def quick_query(
    prompt: str,
    architecture: ArchitectureType = "research",
    model: ModelType = "haiku",
) -> list
```

**参数**:

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `prompt` | `str` | (必需) | 要执行的查询 |
| `architecture` | `ArchitectureType` | `"research"` | 要使用的架构 |
| `model` | `ModelType` | `"haiku"` | 要使用的模型 |

**返回值**: `list` - 执行的所有响应消息

**示例**:

```python
import asyncio
from claude_agent_framework import quick_query

# 快速单次查询
results = asyncio.run(quick_query("分析Python趋势"))
print(results[-1])  # 打印最终消息
```

**注意**: 对于多个查询或流式输出,请改用 `create_session()`。

---

### `get_available_architectures()`

获取所有可用架构及其描述。

```python
def get_available_architectures() -> dict[str, str]
```

**返回值**: `dict[str, str]` - 架构名称到描述的映射

**示例**:

```python
from claude_agent_framework import get_available_architectures

architectures = get_available_architectures()
for name, desc in architectures.items():
    print(f"{name}: {desc}")

# 输出:
# research: 并行工作者深度研究
# pipeline: 顺序阶段处理
# ...
```

---

## AgentSession

包装架构执行的主要会话管理类。

### 类定义

```python
class AgentSession:
    def __init__(
        self,
        architecture: BaseArchitecture,
        config: FrameworkConfig | None = None,
    ) -> None
```

**参数**:

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `architecture` | `BaseArchitecture` | (必需) | 要使用的架构实例 |
| `config` | `FrameworkConfig \| None` | `None` | 框架配置(如果为None则使用默认) |

---

### 方法

#### `setup()`

初始化会话资源。

```python
async def setup(self) -> None
```

**描述**: 设置目录、日志记录并初始化架构。如果尚未调用,`run()` 会自动调用。

**异常**:
- `RuntimeError` - 如果未设置 `ANTHROPIC_API_KEY`

**示例**:

```python
session = create_session("research")
await session.setup()  # 可选 - run() 会自动调用
```

---

#### `teardown()`

清理会话资源。

```python
async def teardown(self) -> None
```

**描述**: 关闭记录写入器,清理架构资源。

**示例**:

```python
session = create_session("research")
try:
    async for msg in session.run(prompt):
        print(msg)
finally:
    await session.teardown()
```

---

#### `run()`

以流式输出运行会话。

```python
async def run(self, prompt: str) -> AsyncIterator[Any]
```

**参数**:

| 参数 | 类型 | 描述 |
|-----------|------|-------------|
| `prompt` | `str` | 用户输入提示 |

**生成**: 来自架构执行的消息(文本内容、工具调用等)

**示例**:

```python
session = create_session("research")

async for message in session.run("分析AI市场趋势"):
    # message 可以是:
    # - str: 文本内容
    # - dict: 工具调用/结果
    # - other: 架构特定数据
    print(message)
```

---

#### `query()`

运行并收集所有消息的便捷方法。

```python
async def query(self, prompt: str) -> list[Any]
```

**参数**:

| 参数 | 类型 | 描述 |
|-----------|------|-------------|
| `prompt` | `str` | 用户输入提示 |

**返回值**: `list[Any]` - 执行的所有消息

**示例**:

```python
session = create_session("research")

messages = await session.query("分析市场趋势")
print(f"收到 {len(messages)} 条消息")
print(messages[-1])  # 最终结果
```

---

### 上下文管理器支持

`AgentSession` 支持异步上下文管理器以自动清理:

```python
async with create_session("research") as session:
    result = await session.query("分析趋势")
    # 自动进行清理
```

---

### 属性

#### `architecture`

获取架构实例。

```python
@property
def architecture(self) -> BaseArchitecture
```

**示例**:

```python
session = create_session("research")
print(session.architecture.name)  # "research"
print(session.architecture.description)
```

---

#### `config`

获取框架配置。

```python
@property
def config(self) -> FrameworkConfig
```

**示例**:

```python
session = create_session("research")
print(session.config.logs_dir)  # 日志目录路径
```

---

#### `session_dir`

获取当前会话日志目录。

```python
@property
def session_dir(self) -> Path | None
```

**返回值**: 会话目录的 `Path`,如果未初始化则为 `None`

**示例**:

```python
session = create_session("research")
await session.setup()
print(f"会话日志: {session.session_dir}")
# 输出: 会话日志: logs/session-20251226-103045/
```

---

#### `tracker`

获取子代理跟踪器实例。

```python
@property
def tracker(self) -> SubagentTracker | None
```

**返回值**: 用于检查工具调用的 `SubagentTracker` 实例

---

#### `transcript`

获取记录写入器实例。

```python
@property
def transcript(self) -> TranscriptWriter | None
```

**返回值**: 用于日志记录的 `TranscriptWriter` 实例

---

## BaseArchitecture

所有架构必须继承的抽象基类。

### 类定义

```python
class BaseArchitecture(ABC):
    name: str = "base"
    description: str = "基础架构(抽象)"

    def __init__(
        self,
        model_config: AgentModelConfig | None = None,
        prompts_dir: Path | None = None,
        files_dir: Path | None = None,
    ) -> None
```

**类属性**:

| 属性 | 类型 | 描述 |
|-----------|------|-------------|
| `name` | `str` | 架构标识符(在子类中覆盖) |
| `description` | `str` | 人类可读描述(在子类中覆盖) |

**初始化参数**:

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `model_config` | `AgentModelConfig \| None` | `None` | 代理的模型配置 |
| `prompts_dir` | `Path \| None` | `None` | 包含提示文件的目录 |
| `files_dir` | `Path \| None` | `None` | 文件操作的工作目录 |

---

### 抽象方法

子类**必须**实现这些方法:

#### `execute()`

主执行逻辑。

```python
@abstractmethod
async def execute(
    self,
    prompt: str,
    tracker: SubagentTracker | None = None,
    transcript: TranscriptWriter | None = None,
) -> AsyncIterator[Any]
```

**参数**:

| 参数 | 类型 | 描述 |
|-----------|------|-------------|
| `prompt` | `str` | 用户输入 |
| `tracker` | `SubagentTracker \| None` | 工具调用跟踪器 |
| `transcript` | `TranscriptWriter \| None` | 记录写入器 |

**生成**: 向用户显示的消息

---

#### `get_role_definitions()`

返回此架构的角色定义。

```python
@abstractmethod
def get_role_definitions(self) -> dict[str, RoleDefinition]
```

**返回值**: `dict[str, RoleDefinition]` - 角色 ID 到角色定义的映射

**示例**:

```python
from claude_agent_framework.core.roles import RoleDefinition
from claude_agent_framework.core.types import RoleType, RoleCardinality

def get_role_definitions(self) -> dict[str, RoleDefinition]:
    return {
        "worker": RoleDefinition(
            role_type=RoleType.WORKER,
            description="对特定主题进行研究",
            required_tools=["WebSearch", "Read", "Write"],
            cardinality=RoleCardinality.ONE_OR_MORE,
            prompt_file="worker.txt",
            default_model="haiku"
        ),
        "synthesizer": RoleDefinition(
            role_type=RoleType.SYNTHESIZER,
            description="综合研究发现",
            required_tools=["Read", "Write"],
            cardinality=RoleCardinality.EXACTLY_ONE,
            prompt_file="synthesizer.txt",
            default_model="sonnet"
        )
    }
```

---

### 可选方法

子类**可以**覆盖这些方法:

#### `setup()`

执行前初始化。

```python
async def setup(self) -> None
```

**示例**:

```python
async def setup(self) -> None:
    # 初始化资源
    self.cache = {}
    await super().setup()
```

---

#### `teardown()`

执行后清理。

```python
async def teardown(self) -> None
```

**示例**:

```python
async def teardown(self) -> None:
    # 清理资源
    self.cache.clear()
    await super().teardown()
```

---

#### `get_hooks()`

自定义钩子配置。

```python
def get_hooks(self) -> dict[str, list]
```

**返回值**: `dict[str, list]` - Claude SDK 的钩子配置

**示例**:

```python
def get_hooks(self) -> dict[str, list]:
    return {
        "PreToolUse": [HookMatcher(...)],
        "PostToolUse": [HookMatcher(...)],
    }
```

---

### 插件支持

#### `add_plugin()`

向架构添加插件。

```python
def add_plugin(self, plugin: BasePlugin) -> None
```

**参数**:

| 参数 | 类型 | 描述 |
|-----------|------|-------------|
| `plugin` | `BasePlugin` | 要添加的插件实例 |

**示例**:

```python
from claude_agent_framework.plugins.builtin import MetricsCollectorPlugin

session = create_session("research")
metrics = MetricsCollectorPlugin()
session.architecture.add_plugin(metrics)

await session.query("分析趋势")
print(metrics.get_metrics())
```

---

#### `remove_plugin()`

按名称删除插件。

```python
def remove_plugin(self, plugin_name: str) -> None
```

**参数**:

| 参数 | 类型 | 描述 |
|-----------|------|-------------|
| `plugin_name` | `str` | 要删除的插件名称 |

---

### 属性

#### `prompts_dir`

获取此架构的提示目录。

```python
@property
def prompts_dir(self) -> Path
```

**返回值**: 提示目录的 `Path`(默认: `architectures/<name>/prompts/`)

---

#### `files_dir`

获取文件操作的工作目录。

```python
@property
def files_dir(self) -> Path
```

**返回值**: 文件目录的 `Path`(默认: `files/`)

---

## 角色类型系统

角色类型系统提供了角色定义（抽象）和智能体实例（具体）之间的清晰分离。

### `RoleType`

定义语义角色类型的枚举。

```python
from claude_agent_framework.core.types import RoleType

class RoleType(str, Enum):
    COORDINATOR = "coordinator"   # 任务编排者
    WORKER = "worker"             # 数据收集者
    PROCESSOR = "processor"       # 数据处理者
    SYNTHESIZER = "synthesizer"   # 结果综合者
    CRITIC = "critic"             # 质量评估者
    JUDGE = "judge"               # 决策制定者
    SPECIALIST = "specialist"     # 领域专家
    ADVOCATE = "advocate"         # 立场倡导者
    MAPPER = "mapper"             # 并行映射者
    REDUCER = "reducer"           # 结果归约者
    EXECUTOR = "executor"         # 任务执行者
    REFLECTOR = "reflector"       # 自我反思者
```

---

### `RoleCardinality`

定义角色数量约束的枚举。

```python
from claude_agent_framework.core.types import RoleCardinality

class RoleCardinality(str, Enum):
    EXACTLY_ONE = "exactly_one"   # 必须恰好 1 个
    ONE_OR_MORE = "one_or_more"   # 至少 1 个 (1-N)
    ZERO_OR_MORE = "zero_or_more" # 任意数量 (0-N)
    ZERO_OR_ONE = "zero_or_one"   # 可选 (0-1)
```

---

### `RoleDefinition`

架构级角色约束定义。

```python
from claude_agent_framework.core.roles import RoleDefinition

@dataclass
class RoleDefinition:
    role_type: RoleType
    description: str = ""
    required_tools: list[str] = field(default_factory=list)
    optional_tools: list[str] = field(default_factory=list)
    cardinality: RoleCardinality = RoleCardinality.EXACTLY_ONE
    default_model: str = "haiku"
    prompt_file: str = ""
```

**属性**:

| 属性 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `role_type` | `RoleType` | 必需 | 语义角色类型 |
| `description` | `str` | `""` | 角色描述 |
| `required_tools` | `list[str]` | `[]` | 角色必须拥有的工具 |
| `optional_tools` | `list[str]` | `[]` | 允许的附加工具 |
| `cardinality` | `RoleCardinality` | `EXACTLY_ONE` | 数量约束 |
| `default_model` | `str` | `"haiku"` | 此角色的默认模型 |
| `prompt_file` | `str` | `""` | 基础提示词文件路径 |

---

### `AgentInstanceConfig`

业务级具体智能体配置。

```python
from claude_agent_framework.core.roles import AgentInstanceConfig

@dataclass
class AgentInstanceConfig:
    name: str
    role: str
    description: str = ""
    tools: list[str] = field(default_factory=list)
    prompt: str = ""
    prompt_file: str = ""
    model: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
```

**属性**:

| 属性 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `name` | `str` | 必需 | 唯一的智能体名称 |
| `role` | `str` | 必需 | 角色 ID（必须匹配架构角色） |
| `description` | `str` | `""` | 智能体描述 |
| `tools` | `list[str]` | `[]` | 此智能体的附加工具 |
| `prompt` | `str` | `""` | 直接提示词内容（最高优先级） |
| `prompt_file` | `str` | `""` | 提示词文件路径 |
| `model` | `str` | `""` | 模型覆盖（为空时使用角色默认值） |
| `metadata` | `dict[str, Any]` | `{}` | 自定义元数据 |

**示例**:

```python
from claude_agent_framework.core.roles import AgentInstanceConfig

agent = AgentInstanceConfig(
    name="market-researcher",
    role="worker",
    description="市场数据收集专员",
    prompt_file="prompts/market_researcher.txt",
    model="sonnet",
)
```

---

### `RoleRegistry`

验证智能体配置是否满足角色约束。

```python
from claude_agent_framework.core.roles import RoleRegistry

class RoleRegistry:
    def register(self, role_id: str, role_def: RoleDefinition) -> None:
        """注册角色定义。"""

    def get(self, role_id: str) -> RoleDefinition | None:
        """根据 ID 获取角色定义。"""

    def validate_agents(
        self, agents: list[AgentInstanceConfig]
    ) -> list[str]:
        """验证智能体实例是否满足角色约束。
        返回错误消息列表（有效时为空）。"""
```

**示例**:

```python
from claude_agent_framework.core.roles import RoleRegistry, RoleDefinition, AgentInstanceConfig
from claude_agent_framework.core.types import RoleType, RoleCardinality

registry = RoleRegistry()

# 注册角色定义
registry.register("worker", RoleDefinition(
    role_type=RoleType.WORKER,
    cardinality=RoleCardinality.ONE_OR_MORE,
    required_tools=["WebSearch"],
))
registry.register("synthesizer", RoleDefinition(
    role_type=RoleType.SYNTHESIZER,
    cardinality=RoleCardinality.EXACTLY_ONE,
    required_tools=["Write"],
))

# 验证智能体实例
agents = [
    AgentInstanceConfig(name="researcher-1", role="worker"),
    AgentInstanceConfig(name="researcher-2", role="worker"),
    AgentInstanceConfig(name="writer", role="synthesizer"),
]

errors = registry.validate_agents(agents)
if errors:
    raise ValueError(f"配置错误: {errors}")
```

---

### 使用角色配置的 `create_session()`

`create_session()` 函数支持基于角色的智能体配置。

```python
def create_session(
    architecture: str = "research",
    *,
    model: str = "haiku",
    agent_instances: list[AgentInstanceConfig] | None = None,
    business_template: str | None = None,
    custom_prompts_dir: Path | str | None = None,
    prompt_overrides: dict[str, str] | None = None,
    template_vars: dict[str, Any] | None = None,
    # ... 其他参数
) -> AgentSession
```

**新参数**:

| 参数 | 类型 | 描述 |
|------|------|------|
| `agent_instances` | `list[AgentInstanceConfig] \| None` | 智能体实例配置列表 |

**示例**:

```python
from claude_agent_framework import create_session
from claude_agent_framework.core.roles import AgentInstanceConfig

agents = [
    AgentInstanceConfig(name="market-researcher", role="worker"),
    AgentInstanceConfig(name="tech-researcher", role="worker"),
    AgentInstanceConfig(name="analyst", role="processor", model="sonnet"),
    AgentInstanceConfig(name="writer", role="synthesizer"),
]

session = create_session(
    "research",
    agent_instances=agents,
    business_template="competitive_intelligence",
)

async for msg in session.run("分析 AI 市场趋势"):
    print(msg)
```

---

## 配置类

### `AgentModelConfig`

架构代理的模型配置。

```python
@dataclass
class AgentModelConfig:
    default: str = "haiku"
    overrides: dict[str, str] = field(default_factory=dict)
```

**属性**:

| 属性 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `default` | `str` | `"haiku"` | 所有代理的默认模型 |
| `overrides` | `dict[str, str]` | `{}` | 按代理的模型覆盖 |

**方法**:

```python
def get_model(self, agent_name: str) -> str:
    """获取特定代理的模型,如果没有则使用默认值。"""
```

**示例**:

```python
from claude_agent_framework.core.base import AgentModelConfig

config = AgentModelConfig(
    default="haiku",
    overrides={
        "lead": "sonnet",
        "synthesizer": "sonnet"
    }
)

print(config.get_model("researcher"))    # "haiku" (默认)
print(config.get_model("lead"))          # "sonnet" (覆盖)
```

---

### `AgentDefinitionConfig`

单个代理的配置。

```python
@dataclass
class AgentDefinitionConfig:
    name: str
    description: str
    tools: list[str] = field(default_factory=list)
    prompt: str = ""
    prompt_file: str = ""
    model: str = "haiku"
```

**属性**:

| 属性 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `name` | `str` | (必需) | 代理标识符(用作 subagent_type) |
| `description` | `str` | (必需) | 何时使用此代理 |
| `tools` | `list[str]` | `[]` | 允许的工具列表 |
| `prompt` | `str` | `""` | 内联提示内容 |
| `prompt_file` | `str` | `""` | 提示文件路径(相对于提示目录) |
| `model` | `str` | `"haiku"` | 要使用的模型 |

**方法**:

```python
def load_prompt(self, prompts_dir: Path) -> str:
    """如果设置了 prompt_file,从文件加载提示内容。"""
```

**示例**:

```python
from claude_agent_framework.core.base import AgentDefinitionConfig

agent = AgentDefinitionConfig(
    name="researcher",
    description="进行网络研究",
    tools=["WebSearch", "Read", "Write"],
    prompt_file="researcher.txt",
    model="haiku"
)

# 从文件加载提示
prompt_content = agent.load_prompt(Path("prompts"))
```

---

### `FrameworkConfig`

全局框架配置。

```python
@dataclass
class FrameworkConfig:
    lead_agent_model: str = "haiku"
    logs_dir: Path = Path("logs")
    files_dir: Path = Path("files")
    enable_tracking: bool = True
    enable_transcripts: bool = True
```

**属性**:

| 属性 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `lead_agent_model` | `str` | `"haiku"` | 主代理的默认模型 |
| `logs_dir` | `Path` | `Path("logs")` | 会话日志目录 |
| `files_dir` | `Path` | `Path("files")` | 输出的工作目录 |
| `enable_tracking` | `bool` | `True` | 启用工具调用跟踪 |
| `enable_transcripts` | `bool` | `True` | 启用记录日志 |

**方法**:

```python
def ensure_directories(self) -> None:
    """如果不存在,创建日志和文件目录。"""
```

**示例**:

```python
from claude_agent_framework.config import FrameworkConfig

config = FrameworkConfig(
    lead_agent_model="sonnet",
    logs_dir=Path("my_logs"),
    files_dir=Path("my_files")
)

config.ensure_directories()  # 创建目录
```

---

## 工具函数

### `validate_api_key()`

检查是否设置了 ANTHROPIC_API_KEY。

```python
def validate_api_key() -> bool
```

**返回值**: `bool` - 如果设置了API密钥则为True

**示例**:

```python
from claude_agent_framework.config import validate_api_key

if not validate_api_key():
    print("请设置 ANTHROPIC_API_KEY 环境变量")
```

---

### `get_architecture()`

按名称获取架构类。

```python
def get_architecture(name: str) -> type[BaseArchitecture]
```

**参数**:

| 参数 | 类型 | 描述 |
|-----------|------|---------|
| `name` | `str` | 架构名称 |

**返回值**: `type[BaseArchitecture]` - 架构类

**异常**:
- `KeyError` - 如果未找到架构

**示例**:

```python
from claude_agent_framework.core import get_architecture

ArchClass = get_architecture("research")
arch = ArchClass()
```

---

### `register_architecture()`

注册自定义架构的装饰器。

```python
def register_architecture(name: str) -> Callable
```

**参数**:

| 参数 | 类型 | 描述 |
|-----------|------|---------|
| `name` | `str` | 架构名称 |

**返回值**: 装饰器函数

**示例**:

```python
from claude_agent_framework.core import register_architecture, BaseArchitecture
from claude_agent_framework.core.roles import RoleDefinition
from claude_agent_framework.core.types import RoleType, RoleCardinality

@register_architecture("my_custom")
class MyCustomArchitecture(BaseArchitecture):
    name = "my_custom"
    description = "我的自定义架构"

    def get_role_definitions(self) -> dict[str, RoleDefinition]:
        return {
            "worker": RoleDefinition(
                role_type=RoleType.WORKER,
                description="执行研究任务",
                required_tools=["Read", "Write"],
                cardinality=RoleCardinality.ONE_OR_MORE,
            ),
        }

    async def execute(self, prompt, tracker=None, transcript=None):
        ...

# 现在可以与 create_session() 一起使用
session = create_session("my_custom")
```

---

## 类型别名

```python
ArchitectureType = Literal[
    "research",
    "pipeline",
    "critic_actor",
    "specialist_pool",
    "debate",
    "reflexion",
    "mapreduce"
]

ModelType = Literal["haiku", "sonnet", "opus"]
```

---

## 异常

### `InitializationError`

框架初始化失败时抛出。

**常见原因**:
- 未设置 `ANTHROPIC_API_KEY` 环境变量
- 未知架构名称
- 配置错误

**示例**:

```python
from claude_agent_framework import create_session, InitializationError

try:
    session = create_session("unknown_architecture")
except InitializationError as e:
    print(f"初始化失败: {e}")
```

---

## 进一步阅读

- [最佳实践](../BEST_PRACTICES_CN.md) - 使用指南
- [角色架构指南](../ROLE_BASED_ARCHITECTURE_CN.md) - 角色系统详解
- [架构选择指南](../guides/architecture_selection/GUIDE_CN.md) - 选择正确的架构

---

**有问题?** 在 [GitHub](https://github.com/anthropics/claude-agent-framework) 上提出issue。
