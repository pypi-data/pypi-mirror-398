"""
Unit tests for plugin system.

Tests BasePlugin, PluginContext, and PluginManager functionality.
"""

import pytest

from claude_agent_framework.plugins.base import (
    BasePlugin,
    PluginContext,
    PluginManager,
)


class TestPluginContext:
    """Test PluginContext dataclass."""

    def test_plugin_context_initialization(self):
        """Test PluginContext can be initialized with required fields."""
        context = PluginContext(architecture_name="research", session_id="test-session-123")

        assert context.architecture_name == "research"
        assert context.session_id == "test-session-123"
        assert context.metadata == {}
        assert context.shared_state == {}

    def test_plugin_context_with_metadata(self):
        """Test PluginContext with metadata and shared_state."""
        context = PluginContext(
            architecture_name="pipeline",
            session_id="test-session-456",
            metadata={"user": "test_user"},
            shared_state={"counter": 0},
        )

        assert context.metadata == {"user": "test_user"}
        assert context.shared_state == {"counter": 0}

    def test_plugin_context_shared_state_is_mutable(self):
        """Test that shared_state can be modified."""
        context = PluginContext(architecture_name="research", session_id="test-session")

        context.shared_state["key"] = "value"
        assert context.shared_state["key"] == "value"


class CounterPlugin(BasePlugin):
    """Test plugin that counts hook invocations."""

    name = "counter_plugin"
    version = "1.0.0"

    def __init__(self):
        self.session_start_count = 0
        self.session_end_count = 0
        self.before_execute_count = 0
        self.after_execute_count = 0
        self.agent_spawn_count = 0
        self.agent_complete_count = 0
        self.tool_call_count = 0
        self.tool_result_count = 0
        self.error_count = 0

    async def on_session_start(self, context: PluginContext) -> None:
        self.session_start_count += 1

    async def on_session_end(self, context: PluginContext) -> None:
        self.session_end_count += 1

    async def on_before_execute(self, prompt: str, context: PluginContext) -> str:
        self.before_execute_count += 1
        return prompt

    async def on_after_execute(self, result, context: PluginContext):
        self.after_execute_count += 1
        return result

    async def on_agent_spawn(
        self, agent_type: str, agent_prompt: str, context: PluginContext
    ) -> str:
        self.agent_spawn_count += 1
        return agent_prompt

    async def on_agent_complete(self, agent_type: str, result, context: PluginContext) -> None:
        self.agent_complete_count += 1

    async def on_tool_call(self, tool_name: str, tool_input: dict, context: PluginContext) -> None:
        self.tool_call_count += 1

    async def on_tool_result(self, tool_name: str, result, context: PluginContext) -> None:
        self.tool_result_count += 1

    async def on_error(self, error: Exception, context: PluginContext) -> bool:
        self.error_count += 1
        return True


class PromptModifierPlugin(BasePlugin):
    """Test plugin that modifies prompts."""

    name = "prompt_modifier"
    version = "1.0.0"

    async def on_before_execute(self, prompt: str, context: PluginContext) -> str:
        return f"[MODIFIED] {prompt}"

    async def on_agent_spawn(
        self, agent_type: str, agent_prompt: str, context: PluginContext
    ) -> str:
        return f"[AGENT: {agent_type}] {agent_prompt}"


class ErrorHandlingPlugin(BasePlugin):
    """Test plugin that can abort on error."""

    name = "error_handler"
    version = "1.0.0"

    def __init__(self, should_continue: bool = True):
        self.should_continue = should_continue

    async def on_error(self, error: Exception, context: PluginContext) -> bool:
        return self.should_continue


class TestBasePlugin:
    """Test BasePlugin base class."""

    def test_base_plugin_has_metadata(self):
        """Test that BasePlugin has name, version, description."""
        plugin = CounterPlugin()

        assert plugin.name == "counter_plugin"
        assert plugin.version == "1.0.0"
        assert plugin.description == ""

    @pytest.mark.asyncio
    async def test_plugin_hooks_are_async(self):
        """Test that all plugin hooks can be called as async functions."""
        plugin = CounterPlugin()
        context = PluginContext(architecture_name="test", session_id="test-session")

        # Should not raise
        await plugin.on_session_start(context)
        await plugin.on_session_end(context)
        await plugin.on_before_execute("test", context)
        await plugin.on_after_execute("result", context)
        await plugin.on_agent_spawn("agent", "prompt", context)
        await plugin.on_agent_complete("agent", "result", context)
        await plugin.on_tool_call("tool", {}, context)
        await plugin.on_tool_result("tool", "result", context)
        await plugin.on_error(Exception("test"), context)


class TestPluginManager:
    """Test PluginManager functionality."""

    def test_plugin_manager_initialization(self):
        """Test PluginManager can be initialized."""
        manager = PluginManager()

        assert len(manager) == 0
        assert manager.list_plugins() == []

    def test_register_plugin(self):
        """Test registering a plugin."""
        manager = PluginManager()
        plugin = CounterPlugin()

        manager.register(plugin)

        assert len(manager) == 1
        assert plugin in manager.list_plugins()

    def test_register_duplicate_plugin_raises_error(self):
        """Test that registering duplicate plugin name raises error."""
        manager = PluginManager()
        plugin1 = CounterPlugin()
        plugin2 = CounterPlugin()

        manager.register(plugin1)

        with pytest.raises(ValueError, match="already registered"):
            manager.register(plugin2)

    def test_unregister_plugin(self):
        """Test unregistering a plugin."""
        manager = PluginManager()
        plugin = CounterPlugin()

        manager.register(plugin)
        assert len(manager) == 1

        result = manager.unregister(plugin)

        assert result is True
        assert len(manager) == 0

    def test_unregister_nonexistent_plugin(self):
        """Test unregistering a plugin that doesn't exist."""
        manager = PluginManager()
        plugin = CounterPlugin()

        result = manager.unregister(plugin)

        assert result is False

    def test_unregister_by_name(self):
        """Test unregistering a plugin by name."""
        manager = PluginManager()
        plugin = CounterPlugin()

        manager.register(plugin)
        result = manager.unregister_by_name("counter_plugin")

        assert result is True
        assert len(manager) == 0

    def test_get_plugin(self):
        """Test retrieving a plugin by name."""
        manager = PluginManager()
        plugin = CounterPlugin()

        manager.register(plugin)
        retrieved = manager.get_plugin("counter_plugin")

        assert retrieved is plugin

    def test_get_nonexistent_plugin(self):
        """Test retrieving a nonexistent plugin returns None."""
        manager = PluginManager()

        retrieved = manager.get_plugin("nonexistent")

        assert retrieved is None

    @pytest.mark.asyncio
    async def test_trigger_session_start(self):
        """Test triggering session_start hook."""
        manager = PluginManager()
        plugin = CounterPlugin()
        manager.register(plugin)

        context = PluginContext(architecture_name="test", session_id="test")
        await manager.trigger_session_start(context)

        assert plugin.session_start_count == 1

    @pytest.mark.asyncio
    async def test_trigger_session_end(self):
        """Test triggering session_end hook."""
        manager = PluginManager()
        plugin = CounterPlugin()
        manager.register(plugin)

        context = PluginContext(architecture_name="test", session_id="test")
        await manager.trigger_session_end(context)

        assert plugin.session_end_count == 1

    @pytest.mark.asyncio
    async def test_trigger_before_execute(self):
        """Test triggering before_execute hook."""
        manager = PluginManager()
        plugin = CounterPlugin()
        manager.register(plugin)

        context = PluginContext(architecture_name="test", session_id="test")
        result = await manager.trigger_before_execute("test prompt", context)

        assert plugin.before_execute_count == 1
        assert result == "test prompt"

    @pytest.mark.asyncio
    async def test_trigger_before_execute_modifies_prompt(self):
        """Test that before_execute can modify the prompt."""
        manager = PluginManager()
        plugin = PromptModifierPlugin()
        manager.register(plugin)

        context = PluginContext(architecture_name="test", session_id="test")
        result = await manager.trigger_before_execute("test prompt", context)

        assert result == "[MODIFIED] test prompt"

    @pytest.mark.asyncio
    async def test_trigger_before_execute_chains_plugins(self):
        """Test that multiple plugins chain their modifications."""
        manager = PluginManager()
        plugin1 = PromptModifierPlugin()
        plugin2 = CounterPlugin()
        manager.register(plugin1)
        manager.register(plugin2)

        context = PluginContext(architecture_name="test", session_id="test")
        result = await manager.trigger_before_execute("test", context)

        # First plugin modifies, second plugin passes through
        assert result == "[MODIFIED] test"
        assert plugin2.before_execute_count == 1

    @pytest.mark.asyncio
    async def test_trigger_agent_spawn(self):
        """Test triggering agent_spawn hook."""
        manager = PluginManager()
        plugin = PromptModifierPlugin()
        manager.register(plugin)

        context = PluginContext(architecture_name="test", session_id="test")
        result = await manager.trigger_agent_spawn("researcher", "research prompt", context)

        assert result == "[AGENT: researcher] research prompt"

    @pytest.mark.asyncio
    async def test_trigger_agent_complete(self):
        """Test triggering agent_complete hook."""
        manager = PluginManager()
        plugin = CounterPlugin()
        manager.register(plugin)

        context = PluginContext(architecture_name="test", session_id="test")
        await manager.trigger_agent_complete("researcher", "result", context)

        assert plugin.agent_complete_count == 1

    @pytest.mark.asyncio
    async def test_trigger_tool_call(self):
        """Test triggering tool_call hook."""
        manager = PluginManager()
        plugin = CounterPlugin()
        manager.register(plugin)

        context = PluginContext(architecture_name="test", session_id="test")
        await manager.trigger_tool_call("WebSearch", {"query": "test"}, context)

        assert plugin.tool_call_count == 1

    @pytest.mark.asyncio
    async def test_trigger_tool_result(self):
        """Test triggering tool_result hook."""
        manager = PluginManager()
        plugin = CounterPlugin()
        manager.register(plugin)

        context = PluginContext(architecture_name="test", session_id="test")
        await manager.trigger_tool_result("WebSearch", "result", context)

        assert plugin.tool_result_count == 1

    @pytest.mark.asyncio
    async def test_trigger_error_continues(self):
        """Test that error hook returns True to continue."""
        manager = PluginManager()
        plugin = ErrorHandlingPlugin(should_continue=True)
        manager.register(plugin)

        context = PluginContext(architecture_name="test", session_id="test")
        should_continue = await manager.trigger_error(Exception("test error"), context)

        assert should_continue is True

    @pytest.mark.asyncio
    async def test_trigger_error_aborts(self):
        """Test that error hook can return False to abort."""
        manager = PluginManager()
        plugin = ErrorHandlingPlugin(should_continue=False)
        manager.register(plugin)

        context = PluginContext(architecture_name="test", session_id="test")
        should_continue = await manager.trigger_error(Exception("test error"), context)

        assert should_continue is False

    @pytest.mark.asyncio
    async def test_multiple_plugins_all_triggered(self):
        """Test that all registered plugins receive hooks."""
        manager = PluginManager()
        plugin1 = CounterPlugin()
        plugin2 = PromptModifierPlugin()  # Use different plugin type
        manager.register(plugin1)
        manager.register(plugin2)

        context = PluginContext(architecture_name="test", session_id="test")
        await manager.trigger_session_start(context)

        assert plugin1.session_start_count == 1
        # plugin2 doesn't track session_start, so we just verify no error

    def test_plugin_manager_repr(self):
        """Test PluginManager string representation."""
        manager = PluginManager()
        plugin1 = CounterPlugin()
        plugin2 = PromptModifierPlugin()

        manager.register(plugin1)
        manager.register(plugin2)

        repr_str = repr(manager)

        assert "PluginManager" in repr_str
        assert "counter_plugin" in repr_str
        assert "prompt_modifier" in repr_str
