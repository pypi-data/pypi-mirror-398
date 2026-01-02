# Plugin Development Guide

**Version**: 1.0.0
**Last Updated**: 2025-12-26

This guide explains how to create custom plugins for Claude Agent Framework. Plugins allow you to extend the framework's functionality by hooking into the agent execution lifecycle.

---

## Table of Contents

1. [Plugin System Overview](#plugin-system-overview)
2. [Plugin Lifecycle Hooks](#plugin-lifecycle-hooks)
3. [Creating Your First Plugin](#creating-your-first-plugin)
4. [Built-in Plugins Reference](#built-in-plugins-reference)
5. [Advanced Plugin Patterns](#advanced-plugin-patterns)
6. [Testing Plugins](#testing-plugins)
7. [Best Practices](#best-practices)
8. [Common Pitfalls](#common-pitfalls)

---

## Plugin System Overview

### What is a Plugin?

A plugin is a Python class that implements the `BasePlugin` interface and can hook into various points in the agent execution lifecycle to:

- **Monitor** agent behavior (logging, metrics)
- **Modify** agent inputs/outputs (preprocessing, post-processing)
- **Control** execution flow (retry logic, error handling)
- **Collect** data (metrics, costs, errors)

### Plugin Architecture

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

### Core Components

**BasePlugin**: Abstract base class defining lifecycle hooks

```python
from claude_agent_framework.plugins.base import BasePlugin, PluginContext

class BasePlugin(ABC):
    """Base class for all plugins."""

    name: str              # Plugin identifier
    version: str           # Semantic version
    description: str       # Short description

    # Lifecycle hooks (all async, all optional)
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

**PluginContext**: Shared state and metadata

```python
@dataclass
class PluginContext:
    architecture_name: str          # Current architecture
    session_id: str                 # Unique session ID
    metadata: dict[str, Any]        # Session metadata
    shared_state: dict[str, Any]    # Cross-plugin state
```

---

## Plugin Lifecycle Hooks

### 1. Session Hooks

#### `on_session_start(context: PluginContext)`

**Called**: Once when session begins, before any agents spawn.

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

#### `on_session_end(context: PluginContext)`

**Called**: Once when session completes, after all agents finish.

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

### 2. Execution Hooks

#### `on_before_execute(prompt: str, context: PluginContext) -> str`

**Called**: Before main query execution.

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

#### `on_after_execute(result: Any, context: PluginContext) -> Any`

**Called**: After main query completes.

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

### 3. Agent Hooks

#### `on_agent_spawn(agent_type: str, agent_prompt: str, context: PluginContext) -> str`

**Called**: When a subagent is about to be spawned.

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

    return agent_prompt  # Return potentially modified prompt
```

#### `on_agent_complete(agent_type: str, result: Any, context: PluginContext) -> Any`

**Called**: When a subagent completes.

**Use Cases**:
- Collect agent results
- Validate outputs
- Update statistics

**Example**:
```python
async def on_agent_complete(
    self, agent_type: str, result: Any, context: PluginContext
) -> Any:
    self._agent_results[agent_type] = result
    logger.debug(f"Agent {agent_type} completed")
    return result
```

---

### 4. Tool Hooks

#### `on_tool_call(tool_name: str, tool_input: dict, context: PluginContext)`

**Called**: Before a tool is invoked.

**Use Cases**:
- Track tool usage
- Validate tool inputs
- Enforce tool policies

**Example**:
```python
async def on_tool_call(
    self, tool_name: str, tool_input: dict, context: PluginContext
) -> None:
    self._tool_calls[tool_name] = self._tool_calls.get(tool_name, 0) + 1
    logger.debug(f"Tool call: {tool_name} ({self._tool_calls[tool_name]} times)")
```

#### `on_tool_result(tool_name: str, result: Any, context: PluginContext)`

**Called**: After a tool completes.

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

### 5. Error Hook

#### `on_error(error: Exception, context: PluginContext) -> bool`

**Called**: When an error occurs anywhere in execution.

**Use Cases**:
- Error logging
- Retry logic
- Graceful degradation

**Returns**:
- `True`: Continue execution (error handled)
- `False`: Abort execution (error fatal)

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

## Creating Your First Plugin

### Example: Simple Logging Plugin

```python
# my_logging_plugin.py

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
        return False  # Don't handle, let error propagate

    async def on_session_end(self, context: PluginContext) -> None:
        logger.info(f"✅ Session ended: {context.session_id}")
```

### Using the Plugin

```python
from claude_agent_framework import init
from my_logging_plugin import LoggingPlugin

# Create session
session = init("research")

# Add plugin
logger_plugin = LoggingPlugin(log_level="INFO")
session.architecture.add_plugin(logger_plugin)

# Run query (plugin will log events)
result = await session.query("Analyze AI trends")

# Output:
# 🚀 Session started: abc-123
#    Architecture: research
# 🤖 Agent spawned: market_analyst
# 🔧 Tool called: WebSearch
# 🔧 Tool called: Write
# ✅ Session ended: abc-123
```

---

## Built-in Plugins Reference

The framework includes three production-ready plugins:

### 1. MetricsCollectorPlugin

**Purpose**: Comprehensive metrics collection

```python
from claude_agent_framework.plugins.builtin import MetricsCollectorPlugin

metrics_plugin = MetricsCollectorPlugin()
session.architecture.add_plugin(metrics_plugin)

# ... run session ...

metrics = metrics_plugin.get_metrics()
print(f"Duration: {metrics.duration_ms}ms")
print(f"Agents: {metrics.agent_count}")
print(f"Tools: {metrics.tool_call_count}")
print(f"Cost: ${metrics.estimated_cost_usd:.4f}")
```

**Features**:
- Session duration tracking
- Agent spawn/complete tracking
- Tool call statistics
- Token usage (manual recording)
- Memory sampling
- Error logging

---

### 2. CostTrackerPlugin

**Purpose**: Token cost tracking and budget enforcement

```python
from claude_agent_framework.plugins.builtin import CostTrackerPlugin

cost_plugin = CostTrackerPlugin(
    input_price_per_mtok=3.0,   # Sonnet pricing
    output_price_per_mtok=15.0,
    budget_limit_usd=10.0,      # $10 budget
    warn_at_percent=0.8         # Warn at 80%
)
session.architecture.add_plugin(cost_plugin)

# ... run session ...

# Manual token recording (from SDK usage)
cost_plugin.record_tokens(input_tokens=50000, output_tokens=25000)

summary = cost_plugin.get_cost_summary()
print(f"Total cost: ${summary['total_cost_usd']:.4f}")
print(f"Budget remaining: ${summary['budget_remaining_usd']:.2f}")
```

**Features**:
- Per-agent cost tracking
- Budget limits with warnings
- Real-time cost monitoring
- Multi-model pricing support

---

### 3. RetryHandlerPlugin

**Purpose**: Automatic retry logic for failed operations

```python
from claude_agent_framework.plugins.builtin import (
    RetryHandlerPlugin,
    ExponentialBackoff,
    FixedDelay,
)

# Option 1: Exponential backoff
retry_plugin = RetryHandlerPlugin(
    strategy=ExponentialBackoff(
        max_retries=3,
        initial_delay=1.0,
        max_delay=60.0,
        multiplier=2.0
    ),
    retryable_errors={ConnectionError, TimeoutError}
)

# Option 2: Fixed delay
retry_plugin = RetryHandlerPlugin(
    strategy=FixedDelay(max_retries=5, delay=2.0),
    non_retryable_errors={KeyboardInterrupt, SystemExit}
)

session.architecture.add_plugin(retry_plugin)

# ... errors will auto-retry ...

stats = retry_plugin.get_retry_stats()
print(f"Total retries: {stats['total_retries']}")
print(f"Total failures: {stats['total_failures']}")
```

**Features**:
- Configurable retry strategies
- Error type filtering
- Retry statistics
- Custom retry conditions

---

## Advanced Plugin Patterns

### Pattern 1: Plugin Chain (Multiple Plugins)

Plugins execute in registration order. Use for composition:

```python
# Add multiple plugins
session.architecture.add_plugin(MetricsCollectorPlugin())
session.architecture.add_plugin(CostTrackerPlugin(budget_limit_usd=20.0))
session.architecture.add_plugin(RetryHandlerPlugin())
session.architecture.add_plugin(LoggingPlugin())

# Execution order:
# 1. MetricsCollectorPlugin hooks run
# 2. CostTrackerPlugin hooks run
# 3. RetryHandlerPlugin hooks run
# 4. LoggingPlugin hooks run
```

### Pattern 2: Cross-Plugin Communication

Use `shared_state` in `PluginContext`:

```python
class PluginA(BasePlugin):
    async def on_session_start(self, context: PluginContext) -> None:
        context.shared_state["plugin_a_data"] = {"key": "value"}

class PluginB(BasePlugin):
    async def on_agent_spawn(
        self, agent_type: str, agent_prompt: str, context: PluginContext
    ) -> str:
        # Read data from PluginA
        data = context.shared_state.get("plugin_a_data", {})
        logger.info(f"PluginA data: {data}")
        return agent_prompt
```

### Pattern 3: Conditional Hook Execution

Skip processing based on context:

```python
class SelectivePlugin(BasePlugin):
    def __init__(self, enabled_architectures: set[str]):
        self.enabled_architectures = enabled_architectures

    async def on_agent_spawn(
        self, agent_type: str, agent_prompt: str, context: PluginContext
    ) -> str:
        # Only process for certain architectures
        if context.architecture_name not in self.enabled_architectures:
            return agent_prompt  # Skip processing

        # ... do something ...
        return modified_prompt

# Only apply to research and mapreduce
plugin = SelectivePlugin(enabled_architectures={"research", "mapreduce"})
```

### Pattern 4: Resource Management

Use session hooks for setup/cleanup:

```python
class DatabasePlugin(BasePlugin):
    def __init__(self, db_url: str):
        self.db_url = db_url
        self._connection = None

    async def on_session_start(self, context: PluginContext) -> None:
        # Acquire resources
        self._connection = await create_connection(self.db_url)
        logger.info("Database connected")

    async def on_session_end(self, context: PluginContext) -> None:
        # Release resources
        if self._connection:
            await self._connection.close()
            logger.info("Database disconnected")

    async def on_agent_complete(
        self, agent_type: str, result: Any, context: PluginContext
    ) -> Any:
        # Use connection
        await self._connection.execute("INSERT INTO results ...", result)
        return result
```

### Pattern 5: Dynamic Configuration

Adjust behavior based on runtime conditions:

```python
class AdaptivePlugin(BasePlugin):
    def __init__(self):
        self._agent_count = 0
        self._current_mode = "normal"

    async def on_agent_spawn(
        self, agent_type: str, agent_prompt: str, context: PluginContext
    ) -> str:
        self._agent_count += 1

        # Switch to conservative mode after many agents
        if self._agent_count > 10 and self._current_mode == "normal":
            self._current_mode = "conservative"
            logger.warning("Switching to conservative mode")
            # ... adjust behavior ...

        return agent_prompt
```

---

## Testing Plugins

### Unit Testing

Test plugins in isolation using mock contexts:

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

    # Test session start
    await plugin.on_session_start(context)
    assert context.shared_state["my_plugin_initialized"] is True

    # Test session end
    await plugin.on_session_end(context)
    assert plugin._session_ended is True


@pytest.mark.asyncio
async def test_agent_spawn():
    plugin = MyPlugin()
    context = PluginContext(session_id="test", architecture_name="research")

    prompt = "Original prompt"
    modified = await plugin.on_agent_spawn("researcher", prompt, context)

    assert modified != prompt  # Verify modification
    assert "metadata" in modified  # Check enhancement


@pytest.mark.asyncio
async def test_error_handling():
    plugin = MyPlugin(max_retries=3)
    context = PluginContext(session_id="test", architecture_name="research")

    error = ConnectionError("Network failed")
    should_continue = await plugin.on_error(error, context)

    assert should_continue is True  # Should retry

    # Non-retryable error
    fatal_error = KeyboardInterrupt()
    should_continue = await plugin.on_error(fatal_error, context)

    assert should_continue is False  # Should abort
```

### Integration Testing

Test plugins with real sessions:

```python
@pytest.mark.asyncio
async def test_plugin_integration():
    from claude_agent_framework import init
    from my_plugin import MyPlugin

    # Create session with plugin
    session = init("research")
    plugin = MyPlugin()
    session.architecture.add_plugin(plugin)

    # Run query
    result = await session.query("Test query")

    # Verify plugin effects
    assert plugin._session_started is True
    assert plugin._agent_count > 0
    assert plugin._session_ended is True
```

---

## Best Practices

### 1. Keep Hooks Lightweight

**Good**:
```python
async def on_tool_call(self, tool_name: str, tool_input: dict, context: PluginContext) -> None:
    self._tool_count += 1  # Fast operation
```

**Bad**:
```python
async def on_tool_call(self, tool_name: str, tool_input: dict, context: PluginContext) -> None:
    # DON'T: Expensive I/O in hot path
    await self._make_api_call(tool_name)
    await self._write_to_database(tool_input)
```

### 2. Handle Errors Gracefully

**Good**:
```python
async def on_agent_complete(self, agent_type: str, result: Any, context: PluginContext) -> Any:
    try:
        await self._process_result(result)
    except Exception as e:
        logger.error(f"Plugin error (non-fatal): {e}")
        # Don't let plugin errors break the session
    return result
```

**Bad**:
```python
async def on_agent_complete(self, agent_type: str, result: Any, context: PluginContext) -> Any:
    # DON'T: Unhandled errors can crash the session
    await self._process_result(result)  # May raise
    return result
```

### 3. Use Descriptive Names and Versions

**Good**:
```python
class AuditLogPlugin(BasePlugin):
    name = "audit_logger"
    version = "1.2.3"
    description = "Logs all agent actions for compliance auditing"
```

**Bad**:
```python
class MyPlugin(BasePlugin):
    name = "plugin"
    version = "1.0"
    description = "Does stuff"
```

### 4. Document Required Dependencies

```python
class DatabasePlugin(BasePlugin):
    """
    Plugin for storing results in PostgreSQL.

    Dependencies:
        - asyncpg>=0.28.0

    Usage:
        plugin = DatabasePlugin(db_url="postgresql://...")
        session.architecture.add_plugin(plugin)
    """
    ...
```

### 5. Provide Configuration Validation

```python
class MyPlugin(BasePlugin):
    def __init__(self, max_retries: int, timeout: float):
        if max_retries < 1:
            raise ValueError("max_retries must be >= 1")
        if timeout <= 0:
            raise ValueError("timeout must be positive")

        self.max_retries = max_retries
        self.timeout = timeout
```

---

## Common Pitfalls

### ❌ Pitfall 1: Blocking I/O in Hooks

```python
# BAD: Blocking call
async def on_session_end(self, context: PluginContext) -> None:
    time.sleep(5)  # Blocks event loop!
    self._save_data()

# GOOD: Async I/O
async def on_session_end(self, context: PluginContext) -> None:
    await asyncio.sleep(5)
    await self._save_data_async()
```

### ❌ Pitfall 2: Modifying Context Metadata Unsafely

```python
# BAD: May conflict with other plugins
async def on_session_start(self, context: PluginContext) -> None:
    context.metadata["data"] = "value"  # Might overwrite!

# GOOD: Use namespaced keys
async def on_session_start(self, context: PluginContext) -> None:
    context.metadata[f"{self.name}_data"] = "value"
```

### ❌ Pitfall 3: Not Returning Modified Values

```python
# BAD: Modification lost
async def on_before_execute(self, prompt: str, context: PluginContext) -> str:
    modified = prompt + "\nExtra instruction"
    # Missing return!

# GOOD: Return modified value
async def on_before_execute(self, prompt: str, context: PluginContext) -> str:
    modified = prompt + "\nExtra instruction"
    return modified
```

### ❌ Pitfall 4: Stateful Bugs Across Sessions

```python
# BAD: State persists across sessions
class BadPlugin(BasePlugin):
    _counter = 0  # Class variable!

    async def on_agent_spawn(...):
        self._counter += 1  # Leaks across sessions

# GOOD: Reset state per session
class GoodPlugin(BasePlugin):
    def __init__(self):
        self._counter = 0  # Instance variable

    async def on_session_start(self, context: PluginContext) -> None:
        self._counter = 0  # Reset per session
```

### ❌ Pitfall 5: Ignoring Return Value of on_error

```python
# BAD: Always returns True (masks errors)
async def on_error(self, error: Exception, context: PluginContext) -> bool:
    logger.error(f"Error: {error}")
    return True  # Always continues!

# GOOD: Selective error handling
async def on_error(self, error: Exception, context: PluginContext) -> bool:
    if isinstance(error, RetryableError):
        return True  # Retry
    return False  # Abort on fatal errors
```

---

## Publishing Your Plugin

### Package Structure

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
description = "My awesome Claude Agent Framework plugin"
authors = [{name = "Your Name", email = "your.email@example.com"}]
dependencies = [
    "claude-agent-framework>=0.4.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
]
```

### Usage in Other Projects

```bash
# Install
pip install my-claude-plugin

# Use
from claude_agent_framework import init
from my_claude_plugin import MyPlugin

session = init("research")
session.architecture.add_plugin(MyPlugin())
```

---

## Further Reading

- [BasePlugin API Reference](../../api/plugins.md)
- [Built-in Plugins Source](../../../src/claude_agent_framework/plugins/builtin/)
- [Best Practices](../../BEST_PRACTICES.md#plugin-development)
- [Example Plugins](../../../examples/plugins/)

---

**Questions?** Open an issue on [GitHub](https://github.com/anthropics/claude-agent-framework).
