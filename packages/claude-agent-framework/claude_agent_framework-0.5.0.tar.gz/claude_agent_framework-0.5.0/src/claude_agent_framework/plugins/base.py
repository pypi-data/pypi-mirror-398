"""
Base plugin infrastructure.

Provides abstract base class and plugin manager for the framework's plugin system.
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PluginContext:
    """
    Context passed to plugin hooks.

    Provides shared state and metadata across plugin invocations.

    Attributes:
        architecture_name: Name of the current architecture
        session_id: Unique session identifier
        metadata: Additional metadata (read-only)
        shared_state: Mutable shared state across plugins
    """

    architecture_name: str
    session_id: str
    metadata: dict[str, Any] = field(default_factory=dict)
    shared_state: dict[str, Any] = field(default_factory=dict)


class BasePlugin(ABC):
    """
    Base class for all plugins.

    Plugins can hook into various lifecycle events to extend framework functionality.
    All hook methods are optional - override only the ones you need.

    Lifecycle Events (in order):
        1. on_session_start - When session initializes
        2. on_before_execute - Before main execution starts
        3. on_agent_spawn - When a subagent is spawned
        4. on_tool_call - When a tool is invoked
        5. on_tool_result - After tool returns result
        6. on_agent_complete - When a subagent finishes
        7. on_after_execute - After main execution completes
        8. on_session_end - When session terminates
        9. on_error - When an error occurs (can happen anytime)

    Example:
        >>> class MyPlugin(BasePlugin):
        ...     name = "my_plugin"
        ...     version = "1.0.0"
        ...
        ...     async def on_session_start(self, context: PluginContext) -> None:
        ...         context.shared_state['start_time'] = time.time()
        ...
        ...     async def on_session_end(self, context: PluginContext) -> None:
        ...         duration = time.time() - context.shared_state['start_time']
        ...         print(f"Session duration: {duration}s")
    """

    # Plugin metadata
    name: str = "base_plugin"
    version: str = "0.1.0"
    description: str = ""

    # Session lifecycle hooks
    async def on_session_start(self, context: PluginContext) -> None:
        """
        Called when session starts.

        Use this to initialize plugin state or resources.

        Args:
            context: Plugin context with session information
        """
        pass

    async def on_session_end(self, context: PluginContext) -> None:
        """
        Called when session ends.

        Use this to cleanup resources or finalize outputs.

        Args:
            context: Plugin context with session information
        """
        pass

    # Execution lifecycle hooks
    async def on_before_execute(self, prompt: str, context: PluginContext) -> str:
        """
        Called before execution starts.

        Can modify the user prompt before it's processed.

        Args:
            prompt: The user's input prompt
            context: Plugin context

        Returns:
            Modified prompt (or original if no modification needed)
        """
        return prompt

    async def on_after_execute(self, result: Any, context: PluginContext) -> Any:
        """
        Called after execution completes.

        Can modify the execution result.

        Args:
            result: The execution result
            context: Plugin context

        Returns:
            Modified result (or original if no modification needed)
        """
        return result

    # Agent lifecycle hooks
    async def on_agent_spawn(
        self, agent_type: str, agent_prompt: str, context: PluginContext
    ) -> str:
        """
        Called when a subagent is spawned.

        Can modify the agent's prompt before execution.

        Args:
            agent_type: Type/name of the agent being spawned
            agent_prompt: The prompt for the agent
            context: Plugin context

        Returns:
            Modified agent prompt (or original if no modification needed)
        """
        return agent_prompt

    async def on_agent_complete(self, agent_type: str, result: Any, context: PluginContext) -> None:
        """
        Called when a subagent completes.

        Use this to track agent execution or collect metrics.

        Args:
            agent_type: Type/name of the completed agent
            result: The agent's result
            context: Plugin context
        """
        pass

    # Tool lifecycle hooks
    async def on_tool_call(
        self, tool_name: str, tool_input: dict[str, Any], context: PluginContext
    ) -> None:
        """
        Called when a tool is invoked.

        Use this to track tool usage or validate inputs.

        Args:
            tool_name: Name of the tool being called
            tool_input: Input parameters to the tool
            context: Plugin context
        """
        pass

    async def on_tool_result(self, tool_name: str, result: Any, context: PluginContext) -> None:
        """
        Called after a tool returns a result.

        Use this to track tool results or collect metrics.

        Args:
            tool_name: Name of the tool that was called
            result: The tool's result
            context: Plugin context
        """
        pass

    # Error handling
    async def on_error(self, error: Exception, context: PluginContext) -> bool:
        """
        Called when an error occurs.

        Plugins can handle or log errors. Return False to abort execution.

        Args:
            error: The exception that occurred
            context: Plugin context

        Returns:
            True to continue execution, False to abort
        """
        return True


class PluginManager:
    """
    Manages plugin lifecycle and coordination.

    The PluginManager maintains a list of registered plugins and triggers
    their hooks at appropriate times.

    Example:
        >>> manager = PluginManager()
        >>> manager.register(MyPlugin())
        >>> context = PluginContext(architecture_name="research", session_id="abc123")
        >>> await manager.trigger_session_start(context)
    """

    def __init__(self) -> None:
        """Initialize the plugin manager."""
        self._plugins: list[BasePlugin] = []
        self._context: PluginContext | None = None

    def register(self, plugin: BasePlugin) -> None:
        """
        Register a plugin.

        Args:
            plugin: Plugin instance to register

        Raises:
            ValueError: If a plugin with the same name is already registered
        """
        # Check for duplicate names
        existing = [p for p in self._plugins if p.name == plugin.name]
        if existing:
            raise ValueError(
                f"Plugin '{plugin.name}' is already registered. "
                f"Remove it first or use a different name."
            )

        self._plugins.append(plugin)

    def unregister(self, plugin: BasePlugin) -> bool:
        """
        Unregister a plugin.

        Args:
            plugin: Plugin instance to unregister

        Returns:
            True if plugin was found and removed, False otherwise
        """
        if plugin in self._plugins:
            self._plugins.remove(plugin)
            return True
        return False

    def unregister_by_name(self, name: str) -> bool:
        """
        Unregister a plugin by name.

        Args:
            name: Name of the plugin to unregister

        Returns:
            True if plugin was found and removed, False otherwise
        """
        for plugin in self._plugins:
            if plugin.name == name:
                self._plugins.remove(plugin)
                return True
        return False

    def get_plugin(self, name: str) -> BasePlugin | None:
        """
        Get a plugin by name.

        Args:
            name: Name of the plugin to retrieve

        Returns:
            Plugin instance if found, None otherwise
        """
        for plugin in self._plugins:
            if plugin.name == name:
                return plugin
        return None

    def list_plugins(self) -> list[BasePlugin]:
        """
        Get list of all registered plugins.

        Returns:
            List of plugin instances
        """
        return list(self._plugins)

    # Hook trigger methods
    async def trigger_session_start(self, context: PluginContext) -> None:
        """Trigger on_session_start hook on all plugins."""
        self._context = context
        for plugin in self._plugins:
            await plugin.on_session_start(context)

    async def trigger_session_end(self, context: PluginContext) -> None:
        """Trigger on_session_end hook on all plugins."""
        for plugin in self._plugins:
            await plugin.on_session_end(context)

    async def trigger_before_execute(self, prompt: str, context: PluginContext) -> str:
        """
        Trigger on_before_execute hook on all plugins.

        Plugins are applied in order, each receiving the result of the previous.
        """
        result = prompt
        for plugin in self._plugins:
            result = await plugin.on_before_execute(result, context)
        return result

    async def trigger_after_execute(self, result: Any, context: PluginContext) -> Any:
        """
        Trigger on_after_execute hook on all plugins.

        Plugins are applied in order, each receiving the result of the previous.
        """
        current_result = result
        for plugin in self._plugins:
            current_result = await plugin.on_after_execute(current_result, context)
        return current_result

    async def trigger_agent_spawn(
        self, agent_type: str, agent_prompt: str, context: PluginContext
    ) -> str:
        """
        Trigger on_agent_spawn hook on all plugins.

        Plugins are applied in order, each receiving the result of the previous.
        """
        result = agent_prompt
        for plugin in self._plugins:
            result = await plugin.on_agent_spawn(agent_type, result, context)
        return result

    async def trigger_agent_complete(
        self, agent_type: str, result: Any, context: PluginContext
    ) -> None:
        """Trigger on_agent_complete hook on all plugins."""
        for plugin in self._plugins:
            await plugin.on_agent_complete(agent_type, result, context)

    async def trigger_tool_call(
        self, tool_name: str, tool_input: dict[str, Any], context: PluginContext
    ) -> None:
        """Trigger on_tool_call hook on all plugins."""
        for plugin in self._plugins:
            await plugin.on_tool_call(tool_name, tool_input, context)

    async def trigger_tool_result(
        self, tool_name: str, result: Any, context: PluginContext
    ) -> None:
        """Trigger on_tool_result hook on all plugins."""
        for plugin in self._plugins:
            await plugin.on_tool_result(tool_name, result, context)

    async def trigger_error(self, error: Exception, context: PluginContext) -> bool:
        """
        Trigger on_error hook on all plugins.

        Returns:
            True if execution should continue, False if it should abort
        """
        for plugin in self._plugins:
            should_continue = await plugin.on_error(error, context)
            if not should_continue:
                return False
        return True

    def __len__(self) -> int:
        """Return number of registered plugins."""
        return len(self._plugins)

    def __repr__(self) -> str:
        """Return string representation."""
        plugin_names = [p.name for p in self._plugins]
        return f"<PluginManager plugins={plugin_names}>"
