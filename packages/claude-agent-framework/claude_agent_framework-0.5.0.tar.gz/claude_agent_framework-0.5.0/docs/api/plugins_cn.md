# 插件API参考

**版本**: 1.0.0
**最后更新**: 2025-12-26

本文档提供 Claude Agent Framework 插件系统的完整 API 参考。

---

## 目录

1. [BasePlugin](#baseplugin)
2. [PluginContext](#plugincontext)
3. [PluginManager](#pluginmanager)
4. [内置插件](#内置插件)

---

## BasePlugin

所有插件的抽象基类。

### 类定义

```python
class BasePlugin(ABC):
    name: str = "base_plugin"
    version: str = "0.1.0"
    description: str = ""
```

**类属性**:

| 属性 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `name` | `str` | `"base_plugin"` | 插件标识符(必须唯一) |
| `version` | `str` | `"0.1.0"` | 语义化版本号 |
| `description` | `str` | `""` | 插件功能的简短描述 |

**生命周期顺序**:

1. `on_session_start` - 会话初始化
2. `on_before_execute` - 主执行之前
3. `on_agent_spawn` - 子代理生成
4. `on_tool_call` - 工具调用
5. `on_tool_result` - 工具返回结果
6. `on_agent_complete` - 子代理完成
7. `on_after_execute` - 主执行之后
8. `on_session_end` - 会话终止
9. `on_error` - 错误发生(可在任何时候发生)

---

### 生命周期钩子

所有钩子都是**可选的**和**异步的**。只覆盖你需要的。

#### `on_session_start()`

会话开始时调用。

```python
async def on_session_start(self, context: PluginContext) -> None
```

**参数**:

| 参数 | 类型 | 描述 |
|-----------|------|-------------|
| `context` | `PluginContext` | 会话信息和共享状态 |

**使用场景**:
- 初始化插件状态
- 设置资源(数据库、连接)
- 在监控系统中注册会话

**示例**:

```python
async def on_session_start(self, context: PluginContext) -> None:
    self._session_id = context.session_id
    self._start_time = time.time()
    context.shared_state["my_plugin_initialized"] = True
    logger.info(f"会话 {context.session_id} 已启动")
```

---

#### `on_session_end()`

会话结束时调用。

```python
async def on_session_end(self, context: PluginContext) -> None
```

**参数**:

| 参数 | 类型 | 描述 |
|-----------|------|-------------|
| `context` | `PluginContext` | 会话信息和共享状态 |

**使用场景**:
- 清理资源
- 完成指标/日志
- 生成报告

**示例**:

```python
async def on_session_end(self, context: PluginContext) -> None:
    duration = time.time() - self._start_time
    logger.info(f"会话在 {duration:.2f}s 内完成")
    await self._save_metrics()
```

---

#### `on_before_execute()`

执行开始前调用。

```python
async def on_before_execute(
    self,
    prompt: str,
    context: PluginContext
) -> str
```

**参数**:

| 参数 | 类型 | 描述 |
|-----------|------|-------------|
| `prompt` | `str` | 用户的输入提示 |
| `context` | `PluginContext` | 会话信息 |

**返回值**: `str` - 修改后的提示(如果不需要修改则返回原始提示)

**使用场景**:
- 预处理用户提示
- 添加上下文/指令
- 验证输入

**示例**:

```python
async def on_before_execute(self, prompt: str, context: PluginContext) -> str:
    # 向提示添加元数据
    enhanced = f"{prompt}\n\n[会话ID: {context.session_id}]"
    return enhanced
```

---

#### `on_after_execute()`

执行完成后调用。

```python
async def on_after_execute(
    self,
    result: Any,
    context: PluginContext
) -> Any
```

**参数**:

| 参数 | 类型 | 描述 |
|-----------|------|-------------|
| `result` | `Any` | 执行结果 |
| `context` | `PluginContext` | 会话信息 |

**返回值**: `Any` - 修改后的结果(如果不需要修改则返回原始结果)

**使用场景**:
- 后处理结果
- 添加元数据
- 格式化输出

**示例**:

```python
async def on_after_execute(self, result: Any, context: PluginContext) -> Any:
    # 用元数据包装结果
    return {
        "result": result,
        "session_id": context.session_id,
        "timestamp": time.time()
    }
```

---

#### `on_agent_spawn()`

子代理生成时调用。

```python
async def on_agent_spawn(
    self,
    agent_type: str,
    agent_prompt: str,
    context: PluginContext
) -> str
```

**参数**:

| 参数 | 类型 | 描述 |
|-----------|------|-------------|
| `agent_type` | `str` | 正在生成的代理的类型/名称 |
| `agent_prompt` | `str` | 代理的提示 |
| `context` | `PluginContext` | 会话信息 |

**返回值**: `str` - 修改后的代理提示(如果不需要修改则返回原始提示)

**使用场景**:
- 跟踪代理创建
- 修改代理提示
- 强制执行代理限制

**示例**:

```python
async def on_agent_spawn(
    self, agent_type: str, agent_prompt: str, context: PluginContext
) -> str:
    self._agent_count += 1
    logger.debug(f"正在生成代理 #{self._agent_count}: {agent_type}")

    # 检查预算
    if self._agent_count > self.max_agents:
        raise ValueError(f"超过最大代理数 ({self.max_agents})")

    return agent_prompt
```

---

#### `on_agent_complete()`

子代理完成时调用。

```python
async def on_agent_complete(
    self,
    agent_type: str,
    result: Any,
    context: PluginContext
) -> None
```

**参数**:

| 参数 | 类型 | 描述 |
|-----------|------|-------------|
| `agent_type` | `str` | 已完成代理的类型/名称 |
| `result` | `Any` | 代理的结果 |
| `context` | `PluginContext` | 会话信息 |

**使用场景**:
- 收集代理结果
- 验证输出
- 更新统计信息

**示例**:

```python
async def on_agent_complete(
    self, agent_type: str, result: Any, context: PluginContext
) -> None:
    self._agent_results[agent_type] = result
    logger.debug(f"代理 {agent_type} 已完成")
```

---

#### `on_tool_call()`

工具调用时调用。

```python
async def on_tool_call(
    self,
    tool_name: str,
    tool_input: dict[str, Any],
    context: PluginContext
) -> None
```

**参数**:

| 参数 | 类型 | 描述 |
|-----------|------|-------------|
| `tool_name` | `str` | 正在调用的工具名称 |
| `tool_input` | `dict[str, Any]` | 工具的输入参数 |
| `context` | `PluginContext` | 会话信息 |

**使用场景**:
- 跟踪工具使用情况
- 验证工具输入
- 强制执行工具策略

**示例**:

```python
async def on_tool_call(
    self, tool_name: str, tool_input: dict[str, Any], context: PluginContext
) -> None:
    self._tool_calls[tool_name] = self._tool_calls.get(tool_name, 0) + 1
    logger.debug(f"工具调用: {tool_name} ({self._tool_calls[tool_name]} 次)")
```

---

#### `on_tool_result()`

工具返回结果后调用。

```python
async def on_tool_result(
    self,
    tool_name: str,
    result: Any,
    context: PluginContext
) -> None
```

**参数**:

| 参数 | 类型 | 描述 |
|-----------|------|-------------|
| `tool_name` | `str` | 已调用的工具名称 |
| `result` | `Any` | 工具的结果 |
| `context` | `PluginContext` | 会话信息 |

**使用场景**:
- 跟踪工具结果
- 分析工具性能
- 缓存结果

**示例**:

```python
async def on_tool_result(
    self, tool_name: str, result: Any, context: PluginContext
) -> None:
    logger.debug(f"工具 {tool_name} 返回了 {len(str(result))} 个字符")
```

---

#### `on_error()`

发生错误时调用。

```python
async def on_error(
    self,
    error: Exception,
    context: PluginContext
) -> bool
```

**参数**:

| 参数 | 类型 | 描述 |
|-----------|------|-------------|
| `error` | `Exception` | 发生的异常 |
| `context` | `PluginContext` | 会话信息 |

**返回值**: `bool` - `True` 继续执行, `False` 中止

**使用场景**:
- 错误日志记录
- 重试逻辑
- 优雅降级

**示例**:

```python
async def on_error(self, error: Exception, context: PluginContext) -> bool:
    self._error_count += 1
    logger.error(f"错误 #{self._error_count}: {type(error).__name__}: {error}")

    # 网络错误时重试
    if isinstance(error, (ConnectionError, TimeoutError)):
        if self._error_count < self.max_retries:
            await asyncio.sleep(self.retry_delay)
            return True  # 继续(重试)

    return False  # 其他错误时中止
```

---

## PluginContext

传递给所有插件钩子的上下文对象。

### 类定义

```python
@dataclass
class PluginContext:
    architecture_name: str
    session_id: str
    metadata: dict[str, Any] = field(default_factory=dict)
    shared_state: dict[str, Any] = field(default_factory=dict)
```

**属性**:

| 属性 | 类型 | 描述 |
|-----------|------|-------------|
| `architecture_name` | `str` | 当前架构的名称 |
| `session_id` | `str` | 唯一会话标识符 |
| `metadata` | `dict[str, Any]` | 附加元数据(只读) |
| `shared_state` | `dict[str, Any]` | 插件间的可变共享状态 |

**用法**:

```python
# 访问会话信息
print(f"架构: {context.architecture_name}")
print(f"会话ID: {context.session_id}")

# 使用共享状态进行跨插件通信
context.shared_state["my_data"] = {"count": 42}

# 从其他插件读取数据
other_data = context.shared_state.get("other_plugin_data", {})
```

---

## PluginManager

管理插件生命周期和协调。

### 类定义

```python
class PluginManager:
    def __init__(self) -> None
```

---

### 方法

#### `register()`

注册插件。

```python
def register(self, plugin: BasePlugin) -> None
```

**参数**:

| 参数 | 类型 | 描述 |
|-----------|------|-------------|
| `plugin` | `BasePlugin` | 要注册的插件实例 |

**异常**:
- `ValueError` - 如果已注册同名插件

**示例**:

```python
from claude_agent_framework.plugins.base import PluginManager
from my_plugin import MyPlugin

manager = PluginManager()
manager.register(MyPlugin())
```

---

#### `unregister()`

取消注册插件实例。

```python
def unregister(self, plugin: BasePlugin) -> bool
```

**参数**:

| 参数 | 类型 | 描述 |
|-----------|------|-------------|
| `plugin` | `BasePlugin` | 要取消注册的插件实例 |

**返回值**: `bool` - 如果找到并移除了插件则为 `True`

---

#### `unregister_by_name()`

按名称取消注册插件。

```python
def unregister_by_name(self, name: str) -> bool
```

**参数**:

| 参数 | 类型 | 描述 |
|-----------|------|-------------|
| `name` | `str` | 要取消注册的插件名称 |

**返回值**: `bool` - 如果找到并移除了插件则为 `True`

**示例**:

```python
manager.unregister_by_name("my_plugin")
```

---

#### `get_plugin()`

按名称获取插件。

```python
def get_plugin(self, name: str) -> BasePlugin | None
```

**参数**:

| 参数 | 类型 | 描述 |
|-----------|------|-------------|
| `name` | `str` | 要检索的插件名称 |

**返回值**: `BasePlugin | None` - 如果找到则返回插件实例,否则为 `None`

**示例**:

```python
metrics = manager.get_plugin("metrics_collector")
if metrics:
    print(metrics.get_metrics())
```

---

#### `list_plugins()`

获取所有已注册插件的列表。

```python
def list_plugins(self) -> list[BasePlugin]
```

**返回值**: `list[BasePlugin]` - 插件实例列表

**示例**:

```python
plugins = manager.list_plugins()
for plugin in plugins:
    print(f"{plugin.name} v{plugin.version}")
```

---

### 触发方法

触发插件钩子的方法(框架内部使用):

#### `trigger_session_start()`

```python
async def trigger_session_start(self, context: PluginContext) -> None
```

#### `trigger_session_end()`

```python
async def trigger_session_end(self, context: PluginContext) -> None
```

#### `trigger_before_execute()`

```python
async def trigger_before_execute(
    self, prompt: str, context: PluginContext
) -> str
```

**注意**: 插件按顺序应用,每个接收前一个的结果。

#### `trigger_after_execute()`

```python
async def trigger_after_execute(
    self, result: Any, context: PluginContext
) -> Any
```

#### `trigger_agent_spawn()`

```python
async def trigger_agent_spawn(
    self, agent_type: str, agent_prompt: str, context: PluginContext
) -> str
```

#### `trigger_agent_complete()`

```python
async def trigger_agent_complete(
    self, agent_type: str, result: Any, context: PluginContext
) -> None
```

#### `trigger_tool_call()`

```python
async def trigger_tool_call(
    self, tool_name: str, tool_input: dict[str, Any], context: PluginContext
) -> None
```

#### `trigger_tool_result()`

```python
async def trigger_tool_result(
    self, tool_name: str, result: Any, context: PluginContext
) -> None
```

#### `trigger_error()`

```python
async def trigger_error(
    self, error: Exception, context: PluginContext
) -> bool
```

**返回值**: `bool` - 如果执行应该继续则为 `True`,如果应该中止则为 `False`

---

## 内置插件

框架提供三个生产就绪的插件:

### MetricsCollectorPlugin

全面的指标收集插件。

**来源**: `claude_agent_framework.plugins.builtin.MetricsCollectorPlugin`

**收集的指标**:
- 会话持续时间(ms)
- 代理生成/完成计数
- 工具调用统计
- Token使用情况(手动记录时)
- 错误计数

**用法**:

```python
from claude_agent_framework import init
from claude_agent_framework.plugins.builtin import MetricsCollectorPlugin

session = init("research")
metrics = MetricsCollectorPlugin()
session.architecture.add_plugin(metrics)

await session.query("分析AI趋势")

# 获取指标
stats = metrics.get_metrics()
print(f"持续时间: {stats.duration_ms}ms")
print(f"代理数: {stats.agent_count}")
print(f"工具调用: {stats.tool_call_count}")
```

**方法**:

```python
def get_metrics(self) -> Metrics
def reset(self) -> None
```

---

### CostTrackerPlugin

Token成本跟踪和预算强制执行。

**来源**: `claude_agent_framework.plugins.builtin.CostTrackerPlugin`

**参数**:

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `input_price_per_mtok` | `float` | `3.0` | 每百万输入token价格 |
| `output_price_per_mtok` | `float` | `15.0` | 每百万输出token价格 |
| `budget_limit_usd` | `float \| None` | `None` | 美元预算限制 |
| `warn_at_percent` | `float` | `0.8` | 预算达到此百分比时警告 |

**用法**:

```python
from claude_agent_framework.plugins.builtin import CostTrackerPlugin

cost = CostTrackerPlugin(
    input_price_per_mtok=3.0,
    output_price_per_mtok=15.0,
    budget_limit_usd=10.0,
    warn_at_percent=0.8
)
session.architecture.add_plugin(cost)

await session.query("分析趋势")

# 手动记录token
cost.record_tokens(input_tokens=50000, output_tokens=25000)

# 获取成本摘要
summary = cost.get_cost_summary()
print(f"总成本: ${summary['total_cost_usd']:.4f}")
print(f"剩余预算: ${summary['budget_remaining_usd']:.2f}")
```

**方法**:

```python
def record_tokens(
    self,
    input_tokens: int,
    output_tokens: int,
    agent_name: str = "unknown"
) -> None

def get_cost_summary(self) -> dict[str, Any]
def reset(self) -> None
```

---

### RetryHandlerPlugin

失败操作的自动重试逻辑。

**来源**: `claude_agent_framework.plugins.builtin.RetryHandlerPlugin`

**参数**:

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `strategy` | `RetryStrategy \| None` | `None` | 重试策略(默认为 ExponentialBackoff) |
| `retryable_errors` | `set[type[Exception]] \| None` | `None` | 要重试的错误类型 |
| `non_retryable_errors` | `set[type[Exception]] \| None` | `{KeyboardInterrupt, SystemExit}` | 不重试的错误类型 |
| `retry_condition` | `Callable \| None` | `None` | 自定义重试条件函数 |

**重试策略**:

```python
# 指数退避
from claude_agent_framework.plugins.builtin import ExponentialBackoff

strategy = ExponentialBackoff(
    max_retries=3,
    initial_delay=1.0,
    max_delay=60.0,
    multiplier=2.0
)

# 固定延迟
from claude_agent_framework.plugins.builtin import FixedDelay

strategy = FixedDelay(
    max_retries=5,
    delay=2.0
)
```

**用法**:

```python
from claude_agent_framework.plugins.builtin import (
    RetryHandlerPlugin,
    ExponentialBackoff
)

retry = RetryHandlerPlugin(
    strategy=ExponentialBackoff(max_retries=3),
    retryable_errors={ConnectionError, TimeoutError}
)
session.architecture.add_plugin(retry)

await session.query("分析趋势")

# 获取重试统计信息
stats = retry.get_retry_stats()
print(f"总重试次数: {stats['total_retries']}")
print(f"总失败次数: {stats['total_failures']}")
```

**方法**:

```python
def get_retry_stats(self) -> dict[str, Any]
def reset(self) -> None
```

---

## 完整示例

创建自定义插件:

```python
import logging
from claude_agent_framework.plugins.base import BasePlugin, PluginContext

logger = logging.getLogger(__name__)


class LoggingPlugin(BasePlugin):
    """记录所有生命周期事件的简单插件。"""

    name = "simple_logger"
    version = "1.0.0"
    description = "记录所有插件生命周期事件"

    def __init__(self, log_level: str = "INFO"):
        self.log_level = getattr(logging, log_level.upper())
        logging.basicConfig(level=self.log_level)

    async def on_session_start(self, context: PluginContext) -> None:
        logger.info(f"🚀 会话已启动: {context.session_id}")
        logger.info(f"   架构: {context.architecture_name}")

    async def on_agent_spawn(
        self, agent_type: str, agent_prompt: str, context: PluginContext
    ) -> str:
        logger.info(f"🤖 代理已生成: {agent_type}")
        return agent_prompt

    async def on_tool_call(
        self, tool_name: str, tool_input: dict, context: PluginContext
    ) -> None:
        logger.info(f"🔧 工具已调用: {tool_name}")

    async def on_error(self, error: Exception, context: PluginContext) -> bool:
        logger.error(f"❌ 错误: {type(error).__name__}: {error}")
        return False

    async def on_session_end(self, context: PluginContext) -> None:
        logger.info(f"✅ 会话已结束: {context.session_id}")


# 使用
from claude_agent_framework import init

session = init("research")
session.architecture.add_plugin(LoggingPlugin())

await session.query("分析AI趋势")
```

---

## 进一步阅读

- [核心API参考](core_cn.md) - 框架核心API
- [插件开发指南](../guides/customization/CUSTOM_PLUGINS_CN.md) - 详细插件指南
- [最佳实践](../BEST_PRACTICES_CN.md) - 使用指南

---

**有问题?** 在 [GitHub](https://github.com/anthropics/claude-agent-framework) 上提出issue。
