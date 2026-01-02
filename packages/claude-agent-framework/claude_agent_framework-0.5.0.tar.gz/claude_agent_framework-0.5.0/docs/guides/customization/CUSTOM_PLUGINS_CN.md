# 插件开发指南

**版本**: 1.0.0
**最后更新**: 2025-12-26

本指南介绍如何为 Claude Agent Framework 创建自定义插件。插件允许你通过钩入代理执行生命周期来扩展框架功能。

---

## 目录

1. [插件系统概述](#插件系统概述)
2. [插件生命周期钩子](#插件生命周期钩子)
3. [创建第一个插件](#创建第一个插件)
4. [内置插件参考](#内置插件参考)
5. [高级插件模式](#高级插件模式)
6. [测试插件](#测试插件)
7. [最佳实践](#最佳实践)
8. [常见陷阱](#常见陷阱)

---

## 插件系统概述

### 什么是插件?

插件是一个实现 `BasePlugin` 接口的 Python 类,可以钩入代理执行生命周期的各个点来:

- **监控** 代理行为(日志、指标)
- **修改** 代理输入/输出(预处理、后处理)
- **控制** 执行流程(重试逻辑、错误处理)
- **收集** 数据(指标、成本、错误)

### 插件架构

```
┌─────────────────────────────────────┐
│      AgentSession                   │
│  ┌───────────────────────────────┐  │
│  │  BaseArchitecture             │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │  PluginManager          │  │  │
│  │  │  - Plugin 1             │  │  │
│  │  │  - Plugin 2             │  │  │
│  │  │  - Plugin 3             │  │  │
│  │  └─────────────────────────┘  │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
         │
         ├─> on_session_start()
         ├─> on_agent_spawn()
         ├─> on_tool_call()
         ├─> on_tool_result()
         ├─> on_agent_complete()
         ├─> on_error()
         └─> on_session_end()
```

### 核心组件

**BasePlugin**: 定义生命周期钩子的抽象基类

```python
from claude_agent_framework.plugins.base import BasePlugin, PluginContext

class BasePlugin(ABC):
    """所有插件的基类。"""

    name: str              # 插件标识符
    version: str           # 语义化版本号
    description: str       # 简短描述

    # 生命周期钩子(全部异步,全部可选)
    async def on_session_start(self, context: PluginContext) -> None: ...
    async def on_session_end(self, context: PluginContext) -> None: ...
    async def on_before_execute(self, prompt: str, context: PluginContext) -> str: ...
    async def on_after_execute(self, result: Any, context: PluginContext) -> Any: ...
    async def on_agent_spawn(self, agent_type: str, agent_prompt: str, context: PluginContext) -> str: ...
    async def on_agent_complete(self, agent_type: str, result: Any, context: PluginContext) -> Any: ...
    async def on_tool_call(self, tool_name: str, tool_input: dict, context: PluginContext) -> None: ...
    async def on_tool_result(self, tool_name: str, result: Any, context: PluginContext) -> None: ...
    async def on_error(self, error: Exception, context: PluginContext) -> bool: ...
```

**PluginContext**: 共享状态和元数据

```python
@dataclass
class PluginContext:
    architecture_name: str          # 当前架构
    session_id: str                 # 唯一会话ID
    metadata: dict[str, Any]        # 会话元数据
    shared_state: dict[str, Any]    # 跨插件状态
```

---

## 插件生命周期钩子

### 1. 会话钩子

#### `on_session_start(context: PluginContext)`

**调用时机**: 会话开始时调用一次,在任何代理生成之前。

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

#### `on_session_end(context: PluginContext)`

**调用时机**: 会话完成时调用一次,在所有代理完成后。

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

### 2. 执行钩子

#### `on_before_execute(prompt: str, context: PluginContext) -> str`

**调用时机**: 主查询执行前。

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

#### `on_after_execute(result: Any, context: PluginContext) -> Any`

**调用时机**: 主查询完成后。

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

### 3. 代理钩子

#### `on_agent_spawn(agent_type: str, agent_prompt: str, context: PluginContext) -> str`

**调用时机**: 子代理即将生成时。

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

    return agent_prompt  # 返回可能修改后的提示
```

#### `on_agent_complete(agent_type: str, result: Any, context: PluginContext) -> Any`

**调用时机**: 子代理完成时。

**使用场景**:
- 收集代理结果
- 验证输出
- 更新统计信息

**示例**:
```python
async def on_agent_complete(
    self, agent_type: str, result: Any, context: PluginContext
) -> Any:
    self._agent_results[agent_type] = result
    logger.debug(f"代理 {agent_type} 已完成")
    return result
```

---

### 4. 工具钩子

#### `on_tool_call(tool_name: str, tool_input: dict, context: PluginContext)`

**调用时机**: 工具调用前。

**使用场景**:
- 跟踪工具使用情况
- 验证工具输入
- 强制执行工具策略

**示例**:
```python
async def on_tool_call(
    self, tool_name: str, tool_input: dict, context: PluginContext
) -> None:
    self._tool_calls[tool_name] = self._tool_calls.get(tool_name, 0) + 1
    logger.debug(f"工具调用: {tool_name} ({self._tool_calls[tool_name]} 次)")
```

#### `on_tool_result(tool_name: str, result: Any, context: PluginContext)`

**调用时机**: 工具完成后。

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

### 5. 错误钩子

#### `on_error(error: Exception, context: PluginContext) -> bool`

**调用时机**: 执行过程中任何地方发生错误时。

**使用场景**:
- 错误日志记录
- 重试逻辑
- 优雅降级

**返回值**:
- `True`: 继续执行(错误已处理)
- `False`: 中止执行(错误致命)

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

## 创建第一个插件

### 示例: 简单日志插件

```python
# my_logging_plugin.py

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
        return False  # 不处理,让错误传播

    async def on_session_end(self, context: PluginContext) -> None:
        logger.info(f"✅ 会话已结束: {context.session_id}")
```

### 使用插件

```python
from claude_agent_framework import init
from my_logging_plugin import LoggingPlugin

# 创建会话
session = init("research")

# 添加插件
logger_plugin = LoggingPlugin(log_level="INFO")
session.architecture.add_plugin(logger_plugin)

# 运行查询(插件将记录事件)
result = await session.query("分析AI趋势")

# 输出:
# 🚀 会话已启动: abc-123
#    架构: research
# 🤖 代理已生成: market_analyst
# 🔧 工具已调用: WebSearch
# 🔧 工具已调用: Write
# ✅ 会话已结束: abc-123
```

---

## 内置插件参考

框架包含三个生产就绪的插件:

### 1. MetricsCollectorPlugin

**用途**: 全面的指标收集

```python
from claude_agent_framework.plugins.builtin import MetricsCollectorPlugin

metrics_plugin = MetricsCollectorPlugin()
session.architecture.add_plugin(metrics_plugin)

# ... 运行会话 ...

metrics = metrics_plugin.get_metrics()
print(f"持续时间: {metrics.duration_ms}ms")
print(f"代理数: {metrics.agent_count}")
print(f"工具调用: {metrics.tool_call_count}")
print(f"成本: ${metrics.estimated_cost_usd:.4f}")
```

**功能**:
- 会话持续时间跟踪
- 代理生成/完成跟踪
- 工具调用统计
- Token使用(手动记录)
- 内存采样
- 错误记录

---

### 2. CostTrackerPlugin

**用途**: Token成本跟踪和预算强制执行

```python
from claude_agent_framework.plugins.builtin import CostTrackerPlugin

cost_plugin = CostTrackerPlugin(
    input_price_per_mtok=3.0,   # Sonnet定价
    output_price_per_mtok=15.0,
    budget_limit_usd=10.0,      # $10预算
    warn_at_percent=0.8         # 在80%时警告
)
session.architecture.add_plugin(cost_plugin)

# ... 运行会话 ...

# 手动记录token(来自SDK使用)
cost_plugin.record_tokens(input_tokens=50000, output_tokens=25000)

summary = cost_plugin.get_cost_summary()
print(f"总成本: ${summary['total_cost_usd']:.4f}")
print(f"剩余预算: ${summary['budget_remaining_usd']:.2f}")
```

**功能**:
- 按代理成本跟踪
- 带警告的预算限制
- 实时成本监控
- 多模型定价支持

---

### 3. RetryHandlerPlugin

**用途**: 失败操作的自动重试逻辑

```python
from claude_agent_framework.plugins.builtin import (
    RetryHandlerPlugin,
    ExponentialBackoff,
    FixedDelay,
)

# 选项1: 指数退避
retry_plugin = RetryHandlerPlugin(
    strategy=ExponentialBackoff(
        max_retries=3,
        initial_delay=1.0,
        max_delay=60.0,
        multiplier=2.0
    ),
    retryable_errors={ConnectionError, TimeoutError}
)

# 选项2: 固定延迟
retry_plugin = RetryHandlerPlugin(
    strategy=FixedDelay(max_retries=5, delay=2.0),
    non_retryable_errors={KeyboardInterrupt, SystemExit}
)

session.architecture.add_plugin(retry_plugin)

# ... 错误将自动重试 ...

stats = retry_plugin.get_retry_stats()
print(f"总重试次数: {stats['total_retries']}")
print(f"总失败次数: {stats['total_failures']}")
```

**功能**:
- 可配置的重试策略
- 错误类型过滤
- 重试统计
- 自定义重试条件

---

## 高级插件模式

### 模式1: 插件链(多个插件)

插件按注册顺序执行。用于组合:

```python
# 添加多个插件
session.architecture.add_plugin(MetricsCollectorPlugin())
session.architecture.add_plugin(CostTrackerPlugin(budget_limit_usd=20.0))
session.architecture.add_plugin(RetryHandlerPlugin())
session.architecture.add_plugin(LoggingPlugin())

# 执行顺序:
# 1. MetricsCollectorPlugin钩子运行
# 2. CostTrackerPlugin钩子运行
# 3. RetryHandlerPlugin钩子运行
# 4. LoggingPlugin钩子运行
```

### 模式2: 跨插件通信

在 `PluginContext` 中使用 `shared_state`:

```python
class PluginA(BasePlugin):
    async def on_session_start(self, context: PluginContext) -> None:
        context.shared_state["plugin_a_data"] = {"key": "value"}

class PluginB(BasePlugin):
    async def on_agent_spawn(
        self, agent_type: str, agent_prompt: str, context: PluginContext
    ) -> str:
        # 从PluginA读取数据
        data = context.shared_state.get("plugin_a_data", {})
        logger.info(f"PluginA数据: {data}")
        return agent_prompt
```

### 模式3: 条件钩子执行

基于上下文跳过处理:

```python
class SelectivePlugin(BasePlugin):
    def __init__(self, enabled_architectures: set[str]):
        self.enabled_architectures = enabled_architectures

    async def on_agent_spawn(
        self, agent_type: str, agent_prompt: str, context: PluginContext
    ) -> str:
        # 仅处理特定架构
        if context.architecture_name not in self.enabled_architectures:
            return agent_prompt  # 跳过处理

        # ... 做某事 ...
        return modified_prompt

# 仅应用于research和mapreduce
plugin = SelectivePlugin(enabled_architectures={"research", "mapreduce"})
```

### 模式4: 资源管理

使用会话钩子进行设置/清理:

```python
class DatabasePlugin(BasePlugin):
    def __init__(self, db_url: str):
        self.db_url = db_url
        self._connection = None

    async def on_session_start(self, context: PluginContext) -> None:
        # 获取资源
        self._connection = await create_connection(self.db_url)
        logger.info("数据库已连接")

    async def on_session_end(self, context: PluginContext) -> None:
        # 释放资源
        if self._connection:
            await self._connection.close()
            logger.info("数据库已断开")

    async def on_agent_complete(
        self, agent_type: str, result: Any, context: PluginContext
    ) -> Any:
        # 使用连接
        await self._connection.execute("INSERT INTO results ...", result)
        return result
```

### 模式5: 动态配置

基于运行时条件调整行为:

```python
class AdaptivePlugin(BasePlugin):
    def __init__(self):
        self._agent_count = 0
        self._current_mode = "normal"

    async def on_agent_spawn(
        self, agent_type: str, agent_prompt: str, context: PluginContext
    ) -> str:
        self._agent_count += 1

        # 许多代理后切换到保守模式
        if self._agent_count > 10 and self._current_mode == "normal":
            self._current_mode = "conservative"
            logger.warning("切换到保守模式")
            # ... 调整行为 ...

        return agent_prompt
```

---

## 测试插件

### 单元测试

使用模拟上下文隔离测试插件:

```python
import pytest
from claude_agent_framework.plugins.base import PluginContext
from my_plugin import MyPlugin


@pytest.mark.asyncio
async def test_session_lifecycle():
    plugin = MyPlugin()
    context = PluginContext(
        session_id="test-123",
        architecture_name="research",
        metadata={},
        shared_state={}
    )

    # 测试会话启动
    await plugin.on_session_start(context)
    assert context.shared_state["my_plugin_initialized"] is True

    # 测试会话结束
    await plugin.on_session_end(context)
    assert plugin._session_ended is True


@pytest.mark.asyncio
async def test_agent_spawn():
    plugin = MyPlugin()
    context = PluginContext(session_id="test", architecture_name="research")

    prompt = "原始提示"
    modified = await plugin.on_agent_spawn("researcher", prompt, context)

    assert modified != prompt  # 验证修改
    assert "metadata" in modified  # 检查增强


@pytest.mark.asyncio
async def test_error_handling():
    plugin = MyPlugin(max_retries=3)
    context = PluginContext(session_id="test", architecture_name="research")

    error = ConnectionError("网络失败")
    should_continue = await plugin.on_error(error, context)

    assert should_continue is True  # 应该重试

    # 不可重试的错误
    fatal_error = KeyboardInterrupt()
    should_continue = await plugin.on_error(fatal_error, context)

    assert should_continue is False  # 应该中止
```

### 集成测试

使用真实会话测试插件:

```python
@pytest.mark.asyncio
async def test_plugin_integration():
    from claude_agent_framework import init
    from my_plugin import MyPlugin

    # 创建带插件的会话
    session = init("research")
    plugin = MyPlugin()
    session.architecture.add_plugin(plugin)

    # 运行查询
    result = await session.query("测试查询")

    # 验证插件效果
    assert plugin._session_started is True
    assert plugin._agent_count > 0
    assert plugin._session_ended is True
```

---

## 最佳实践

### 1. 保持钩子轻量级

**好的做法**:
```python
async def on_tool_call(self, tool_name: str, tool_input: dict, context: PluginContext) -> None:
    self._tool_count += 1  # 快速操作
```

**不好的做法**:
```python
async def on_tool_call(self, tool_name: str, tool_input: dict, context: PluginContext) -> None:
    # 不要: 在热路径中进行昂贵的I/O操作
    await self._make_api_call(tool_name)
    await self._write_to_database(tool_input)
```

### 2. 优雅地处理错误

**好的做法**:
```python
async def on_agent_complete(self, agent_type: str, result: Any, context: PluginContext) -> Any:
    try:
        await self._process_result(result)
    except Exception as e:
        logger.error(f"插件错误(非致命): {e}")
        # 不要让插件错误破坏会话
    return result
```

**不好的做法**:
```python
async def on_agent_complete(self, agent_type: str, result: Any, context: PluginContext) -> Any:
    # 不要: 未处理的错误可能导致会话崩溃
    await self._process_result(result)  # 可能抛出异常
    return result
```

### 3. 使用描述性名称和版本

**好的做法**:
```python
class AuditLogPlugin(BasePlugin):
    name = "audit_logger"
    version = "1.2.3"
    description = "记录所有代理操作以进行合规审计"
```

**不好的做法**:
```python
class MyPlugin(BasePlugin):
    name = "plugin"
    version = "1.0"
    description = "做一些事情"
```

### 4. 记录所需依赖

```python
class DatabasePlugin(BasePlugin):
    """
    用于在PostgreSQL中存储结果的插件。

    依赖:
        - asyncpg>=0.28.0

    用法:
        plugin = DatabasePlugin(db_url="postgresql://...")
        session.architecture.add_plugin(plugin)
    """
    ...
```

### 5. 提供配置验证

```python
class MyPlugin(BasePlugin):
    def __init__(self, max_retries: int, timeout: float):
        if max_retries < 1:
            raise ValueError("max_retries必须 >= 1")
        if timeout <= 0:
            raise ValueError("timeout必须为正数")

        self.max_retries = max_retries
        self.timeout = timeout
```

---

## 常见陷阱

### ❌ 陷阱1: 钩子中的阻塞I/O

```python
# 不好: 阻塞调用
async def on_session_end(self, context: PluginContext) -> None:
    time.sleep(5)  # 阻塞事件循环!
    self._save_data()

# 好: 异步I/O
async def on_session_end(self, context: PluginContext) -> None:
    await asyncio.sleep(5)
    await self._save_data_async()
```

### ❌ 陷阱2: 不安全地修改上下文元数据

```python
# 不好: 可能与其他插件冲突
async def on_session_start(self, context: PluginContext) -> None:
    context.metadata["data"] = "value"  # 可能覆盖!

# 好: 使用命名空间键
async def on_session_start(self, context: PluginContext) -> None:
    context.metadata[f"{self.name}_data"] = "value"
```

### ❌ 陷阱3: 不返回修改后的值

```python
# 不好: 修改丢失
async def on_before_execute(self, prompt: str, context: PluginContext) -> str:
    modified = prompt + "\n额外指令"
    # 缺少return!

# 好: 返回修改后的值
async def on_before_execute(self, prompt: str, context: PluginContext) -> str:
    modified = prompt + "\n额外指令"
    return modified
```

### ❌ 陷阱4: 跨会话的状态错误

```python
# 不好: 状态在会话间持续存在
class BadPlugin(BasePlugin):
    _counter = 0  # 类变量!

    async def on_agent_spawn(...):
        self._counter += 1  # 跨会话泄漏

# 好: 按会话重置状态
class GoodPlugin(BasePlugin):
    def __init__(self):
        self._counter = 0  # 实例变量

    async def on_session_start(self, context: PluginContext) -> None:
        self._counter = 0  # 每个会话重置
```

### ❌ 陷阱5: 忽略on_error的返回值

```python
# 不好: 总是返回True(掩盖错误)
async def on_error(self, error: Exception, context: PluginContext) -> bool:
    logger.error(f"错误: {error}")
    return True  # 总是继续!

# 好: 选择性错误处理
async def on_error(self, error: Exception, context: PluginContext) -> bool:
    if isinstance(error, RetryableError):
        return True  # 重试
    return False  # 致命错误时中止
```

---

## 发布你的插件

### 包结构

```
my-claude-plugin/
├── pyproject.toml
├── README.md
├── LICENSE
├── my_claude_plugin/
│   ├── __init__.py
│   ├── plugin.py
│   └── utils.py
└── tests/
    ├── __init__.py
    └── test_plugin.py
```

### pyproject.toml

```toml
[project]
name = "my-claude-plugin"
version = "1.0.0"
description = "我的出色的 Claude Agent Framework 插件"
authors = [{name = "你的名字", email = "your.email@example.com"}]
dependencies = [
    "claude-agent-framework>=0.4.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
]
```

### 在其他项目中使用

```bash
# 安装
pip install my-claude-plugin

# 使用
from claude_agent_framework import init
from my_claude_plugin import MyPlugin

session = init("research")
session.architecture.add_plugin(MyPlugin())
```

---

## 进一步阅读

- [BasePlugin API参考](../../api/plugins.md)
- [内置插件源代码](../../../src/claude_agent_framework/plugins/builtin/)
- [最佳实践](../../BEST_PRACTICES.md#plugin-development)
- [示例插件](../../../examples/plugins/)

---

**有问题?** 在 [GitHub](https://github.com/anthropics/claude-agent-framework) 上提出issue。
