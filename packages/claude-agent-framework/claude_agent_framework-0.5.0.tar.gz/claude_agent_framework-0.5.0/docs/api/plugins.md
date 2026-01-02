# Plugins API Reference

**Version**: 1.0.0
**Last Updated**: 2025-12-26

This document provides complete API reference for Claude Agent Framework's plugin system.

---

## Table of Contents

1. [BasePlugin](#baseplugin)
2. [PluginContext](#plugincontext)
3. [PluginManager](#pluginmanager)
4. [Built-in Plugins](#built-in-plugins)

---

## BasePlugin

Abstract base class for all plugins.

### Class Definition

```python
class BasePlugin(ABC):
    name: str = "base_plugin"
    version: str = "0.1.0"
    description: str = ""
```

**Class Attributes**:

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | `"base_plugin"` | Plugin identifier (must be unique) |
| `version` | `str` | `"0.1.0"` | Semantic version |
| `description` | `str` | `""` | Short description of plugin functionality |

**Lifecycle Order**:

1. `on_session_start` - Session initializes
2. `on_before_execute` - Before main execution
3. `on_agent_spawn` - Subagent is spawned
4. `on_tool_call` - Tool is invoked
5. `on_tool_result` - Tool returns result
6. `on_agent_complete` - Subagent finishes
7. `on_after_execute` - After main execution
8. `on_session_end` - Session terminates
9. `on_error` - Error occurs (can happen anytime)

---

### Lifecycle Hooks

All hooks are **optional** and **async**. Override only the ones you need.

#### `on_session_start()`

Called when session starts.

```python
async def on_session_start(self, context: PluginContext) -> None
```

**Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `context` | `PluginContext` | Session information and shared state |

**Use Cases**:
- Initialize plugin state
- Set up resources (databases, connections)
- Register session in monitoring system

**Example**:

```python
async def on_session_start(self, context: PluginContext) -> None:
    self._session_id = context.session_id
    self._start_time = time.time()
    context.shared_state["my_plugin_initialized"] = True
    logger.info(f"Session {context.session_id} started")
```

---

#### `on_session_end()`

Called when session ends.

```python
async def on_session_end(self, context: PluginContext) -> None
```

**Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `context` | `PluginContext` | Session information and shared state |

**Use Cases**:
- Clean up resources
- Finalize metrics/logs
- Generate reports

**Example**:

```python
async def on_session_end(self, context: PluginContext) -> None:
    duration = time.time() - self._start_time
    logger.info(f"Session completed in {duration:.2f}s")
    await self._save_metrics()
```

---

#### `on_before_execute()`

Called before execution starts.

```python
async def on_before_execute(
    self,
    prompt: str,
    context: PluginContext
) -> str
```

**Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `prompt` | `str` | User's input prompt |
| `context` | `PluginContext` | Session information |

**Returns**: `str` - Modified prompt (or original if no modification needed)

**Use Cases**:
- Preprocess user prompts
- Add context/instructions
- Validate inputs

**Example**:

```python
async def on_before_execute(self, prompt: str, context: PluginContext) -> str:
    # Add metadata to prompt
    enhanced = f"{prompt}\n\n[Session ID: {context.session_id}]"
    return enhanced
```

---

#### `on_after_execute()`

Called after execution completes.

```python
async def on_after_execute(
    self,
    result: Any,
    context: PluginContext
) -> Any
```

**Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `result` | `Any` | Execution result |
| `context` | `PluginContext` | Session information |

**Returns**: `Any` - Modified result (or original if no modification needed)

**Use Cases**:
- Post-process results
- Add metadata
- Format output

**Example**:

```python
async def on_after_execute(self, result: Any, context: PluginContext) -> Any:
    # Wrap result with metadata
    return {
        "result": result,
        "session_id": context.session_id,
        "timestamp": time.time()
    }
```

---

#### `on_agent_spawn()`

Called when a subagent is spawned.

```python
async def on_agent_spawn(
    self,
    agent_type: str,
    agent_prompt: str,
    context: PluginContext
) -> str
```

**Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_type` | `str` | Type/name of the agent being spawned |
| `agent_prompt` | `str` | Prompt for the agent |
| `context` | `PluginContext` | Session information |

**Returns**: `str` - Modified agent prompt (or original if no modification needed)

**Use Cases**:
- Track agent creation
- Modify agent prompts
- Enforce agent limits

**Example**:

```python
async def on_agent_spawn(
    self, agent_type: str, agent_prompt: str, context: PluginContext
) -> str:
    self._agent_count += 1
    logger.debug(f"Spawning agent #{self._agent_count}: {agent_type}")

    # Check budget
    if self._agent_count > self.max_agents:
        raise ValueError(f"Exceeded max agents ({self.max_agents})")

    return agent_prompt
```

---

#### `on_agent_complete()`

Called when a subagent completes.

```python
async def on_agent_complete(
    self,
    agent_type: str,
    result: Any,
    context: PluginContext
) -> None
```

**Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_type` | `str` | Type/name of the completed agent |
| `result` | `Any` | Agent's result |
| `context` | `PluginContext` | Session information |

**Use Cases**:
- Collect agent results
- Validate outputs
- Update statistics

**Example**:

```python
async def on_agent_complete(
    self, agent_type: str, result: Any, context: PluginContext
) -> None:
    self._agent_results[agent_type] = result
    logger.debug(f"Agent {agent_type} completed")
```

---

#### `on_tool_call()`

Called when a tool is invoked.

```python
async def on_tool_call(
    self,
    tool_name: str,
    tool_input: dict[str, Any],
    context: PluginContext
) -> None
```

**Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `tool_name` | `str` | Name of the tool being called |
| `tool_input` | `dict[str, Any]` | Input parameters to the tool |
| `context` | `PluginContext` | Session information |

**Use Cases**:
- Track tool usage
- Validate tool inputs
- Enforce tool policies

**Example**:

```python
async def on_tool_call(
    self, tool_name: str, tool_input: dict[str, Any], context: PluginContext
) -> None:
    self._tool_calls[tool_name] = self._tool_calls.get(tool_name, 0) + 1
    logger.debug(f"Tool call: {tool_name} ({self._tool_calls[tool_name]} times)")
```

---

#### `on_tool_result()`

Called after a tool returns a result.

```python
async def on_tool_result(
    self,
    tool_name: str,
    result: Any,
    context: PluginContext
) -> None
```

**Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `tool_name` | `str` | Name of the tool that was called |
| `result` | `Any` | Tool's result |
| `context` | `PluginContext` | Session information |

**Use Cases**:
- Track tool results
- Analyze tool performance
- Cache results

**Example**:

```python
async def on_tool_result(
    self, tool_name: str, result: Any, context: PluginContext
) -> None:
    logger.debug(f"Tool {tool_name} returned {len(str(result))} chars")
```

---

#### `on_error()`

Called when an error occurs.

```python
async def on_error(
    self,
    error: Exception,
    context: PluginContext
) -> bool
```

**Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `error` | `Exception` | The exception that occurred |
| `context` | `PluginContext` | Session information |

**Returns**: `bool` - `True` to continue execution, `False` to abort

**Use Cases**:
- Error logging
- Retry logic
- Graceful degradation

**Example**:

```python
async def on_error(self, error: Exception, context: PluginContext) -> bool:
    self._error_count += 1
    logger.error(f"Error #{self._error_count}: {type(error).__name__}: {error}")

    # Retry on network errors
    if isinstance(error, (ConnectionError, TimeoutError)):
        if self._error_count < self.max_retries:
            await asyncio.sleep(self.retry_delay)
            return True  # Continue (retry)

    return False  # Abort on other errors
```

---

## PluginContext

Context object passed to all plugin hooks.

### Class Definition

```python
@dataclass
class PluginContext:
    architecture_name: str
    session_id: str
    metadata: dict[str, Any] = field(default_factory=dict)
    shared_state: dict[str, Any] = field(default_factory=dict)
```

**Attributes**:

| Attribute | Type | Description |
|-----------|------|-------------|
| `architecture_name` | `str` | Name of the current architecture |
| `session_id` | `str` | Unique session identifier |
| `metadata` | `dict[str, Any]` | Additional metadata (read-only) |
| `shared_state` | `dict[str, Any]` | Mutable shared state across plugins |

**Usage**:

```python
# Access session information
print(f"Architecture: {context.architecture_name}")
print(f"Session ID: {context.session_id}")

# Use shared state for cross-plugin communication
context.shared_state["my_data"] = {"count": 42}

# Read data from other plugins
other_data = context.shared_state.get("other_plugin_data", {})
```

---

## PluginManager

Manages plugin lifecycle and coordination.

### Class Definition

```python
class PluginManager:
    def __init__(self) -> None
```

---

### Methods

#### `register()`

Register a plugin.

```python
def register(self, plugin: BasePlugin) -> None
```

**Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `plugin` | `BasePlugin` | Plugin instance to register |

**Raises**:
- `ValueError` - If a plugin with the same name is already registered

**Example**:

```python
from claude_agent_framework.plugins.base import PluginManager
from my_plugin import MyPlugin

manager = PluginManager()
manager.register(MyPlugin())
```

---

#### `unregister()`

Unregister a plugin instance.

```python
def unregister(self, plugin: BasePlugin) -> bool
```

**Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `plugin` | `BasePlugin` | Plugin instance to unregister |

**Returns**: `bool` - `True` if plugin was found and removed

---

#### `unregister_by_name()`

Unregister a plugin by name.

```python
def unregister_by_name(self, name: str) -> bool
```

**Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Name of the plugin to unregister |

**Returns**: `bool` - `True` if plugin was found and removed

**Example**:

```python
manager.unregister_by_name("my_plugin")
```

---

#### `get_plugin()`

Get a plugin by name.

```python
def get_plugin(self, name: str) -> BasePlugin | None
```

**Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Name of the plugin to retrieve |

**Returns**: `BasePlugin | None` - Plugin instance if found, `None` otherwise

**Example**:

```python
metrics = manager.get_plugin("metrics_collector")
if metrics:
    print(metrics.get_metrics())
```

---

#### `list_plugins()`

Get list of all registered plugins.

```python
def list_plugins(self) -> list[BasePlugin]
```

**Returns**: `list[BasePlugin]` - List of plugin instances

**Example**:

```python
plugins = manager.list_plugins()
for plugin in plugins:
    print(f"{plugin.name} v{plugin.version}")
```

---

### Trigger Methods

Methods to trigger plugin hooks (used internally by framework):

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

**Note**: Plugins are applied in order, each receiving the result of the previous.

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

**Returns**: `bool` - `True` if execution should continue, `False` if it should abort

---

## Built-in Plugins

The framework provides three production-ready plugins:

### MetricsCollectorPlugin

Comprehensive metrics collection plugin.

**Source**: `claude_agent_framework.plugins.builtin.MetricsCollectorPlugin`

**Collected Metrics**:
- Session duration (ms)
- Agent spawn/complete counts
- Tool call statistics
- Token usage (when manually recorded)
- Error counts

**Usage**:

```python
from claude_agent_framework import init
from claude_agent_framework.plugins.builtin import MetricsCollectorPlugin

session = init("research")
metrics = MetricsCollectorPlugin()
session.architecture.add_plugin(metrics)

await session.query("Analyze AI trends")

# Get metrics
stats = metrics.get_metrics()
print(f"Duration: {stats.duration_ms}ms")
print(f"Agents: {stats.agent_count}")
print(f"Tools: {stats.tool_call_count}")
```

**Methods**:

```python
def get_metrics(self) -> Metrics
def reset(self) -> None
```

---

### CostTrackerPlugin

Token cost tracking and budget enforcement.

**Source**: `claude_agent_framework.plugins.builtin.CostTrackerPlugin`

**Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input_price_per_mtok` | `float` | `3.0` | Input token price per million |
| `output_price_per_mtok` | `float` | `15.0` | Output token price per million |
| `budget_limit_usd` | `float \| None` | `None` | Budget limit in USD |
| `warn_at_percent` | `float` | `0.8` | Warn when budget reaches this % |

**Usage**:

```python
from claude_agent_framework.plugins.builtin import CostTrackerPlugin

cost = CostTrackerPlugin(
    input_price_per_mtok=3.0,
    output_price_per_mtok=15.0,
    budget_limit_usd=10.0,
    warn_at_percent=0.8
)
session.architecture.add_plugin(cost)

await session.query("Analyze trends")

# Manual token recording
cost.record_tokens(input_tokens=50000, output_tokens=25000)

# Get cost summary
summary = cost.get_cost_summary()
print(f"Total cost: ${summary['total_cost_usd']:.4f}")
print(f"Budget remaining: ${summary['budget_remaining_usd']:.2f}")
```

**Methods**:

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

Automatic retry logic for failed operations.

**Source**: `claude_agent_framework.plugins.builtin.RetryHandlerPlugin`

**Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `strategy` | `RetryStrategy \| None` | `None` | Retry strategy (defaults to ExponentialBackoff) |
| `retryable_errors` | `set[type[Exception]] \| None` | `None` | Error types to retry |
| `non_retryable_errors` | `set[type[Exception]] \| None` | `{KeyboardInterrupt, SystemExit}` | Error types NOT to retry |
| `retry_condition` | `Callable \| None` | `None` | Custom retry condition function |

**Retry Strategies**:

```python
# Exponential backoff
from claude_agent_framework.plugins.builtin import ExponentialBackoff

strategy = ExponentialBackoff(
    max_retries=3,
    initial_delay=1.0,
    max_delay=60.0,
    multiplier=2.0
)

# Fixed delay
from claude_agent_framework.plugins.builtin import FixedDelay

strategy = FixedDelay(
    max_retries=5,
    delay=2.0
)
```

**Usage**:

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

await session.query("Analyze trends")

# Get retry statistics
stats = retry.get_retry_stats()
print(f"Total retries: {stats['total_retries']}")
print(f"Total failures: {stats['total_failures']}")
```

**Methods**:

```python
def get_retry_stats(self) -> dict[str, Any]
def reset(self) -> None
```

---

## Complete Example

Creating a custom plugin:

```python
import logging
from claude_agent_framework.plugins.base import BasePlugin, PluginContext

logger = logging.getLogger(__name__)


class LoggingPlugin(BasePlugin):
    """Simple plugin that logs all lifecycle events."""

    name = "simple_logger"
    version = "1.0.0"
    description = "Logs all plugin lifecycle events"

    def __init__(self, log_level: str = "INFO"):
        self.log_level = getattr(logging, log_level.upper())
        logging.basicConfig(level=self.log_level)

    async def on_session_start(self, context: PluginContext) -> None:
        logger.info(f"🚀 Session started: {context.session_id}")
        logger.info(f"   Architecture: {context.architecture_name}")

    async def on_agent_spawn(
        self, agent_type: str, agent_prompt: str, context: PluginContext
    ) -> str:
        logger.info(f"🤖 Agent spawned: {agent_type}")
        return agent_prompt

    async def on_tool_call(
        self, tool_name: str, tool_input: dict, context: PluginContext
    ) -> None:
        logger.info(f"🔧 Tool called: {tool_name}")

    async def on_error(self, error: Exception, context: PluginContext) -> bool:
        logger.error(f"❌ Error: {type(error).__name__}: {error}")
        return False

    async def on_session_end(self, context: PluginContext) -> None:
        logger.info(f"✅ Session ended: {context.session_id}")


# Usage
from claude_agent_framework import init

session = init("research")
session.architecture.add_plugin(LoggingPlugin())

await session.query("Analyze AI trends")
```

---

## Further Reading

- [Core API Reference](core.md) - Framework core API
- [Plugin Development Guide](../guides/customization/CUSTOM_PLUGINS.md) - Detailed plugin guide
- [Best Practices](../BEST_PRACTICES.md) - Usage guidelines

---

**Questions?** Open an issue on [GitHub](https://github.com/anthropics/claude-agent-framework).
