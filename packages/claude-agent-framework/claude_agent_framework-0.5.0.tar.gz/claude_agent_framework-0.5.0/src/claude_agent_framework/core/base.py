"""
Base architecture abstraction.

Provides abstract base class that all architecture implementations must inherit.
Supports role-based agent configuration for flexible business customization.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from claude_agent_framework.plugins.base import BasePlugin
    from claude_agent_framework.utils import SubagentTracker, TranscriptWriter

from claude_agent_framework.core.roles import (
    AgentInstanceConfig,
    RoleDefinition,
    RoleRegistry,
)


@dataclass
class AgentDefinitionConfig:
    """
    Configuration for a single agent within an architecture.

    Supports two-layer prompt composition:
    - Role prompt: Framework-level generic role capabilities (from role_prompt_file)
    - Instance prompt: Business-level specific context (from prompt_file)

    Final prompt = role_prompt + "\\n\\n# Business Context\\n\\n" + instance_prompt

    Attributes:
        name: Agent identifier (used as subagent_type)
        description: When to use this agent
        tools: List of allowed tools
        prompt: Inline prompt content (highest priority)
        prompt_file: Business instance prompt file (relative to custom_prompts_dir)
        role_prompt_file: Framework role prompt file (relative to arch_prompts_dir)
        model: Model to use (haiku/sonnet/opus)
    """

    name: str
    description: str
    tools: list[str] = field(default_factory=list)
    prompt: str = ""
    prompt_file: str = ""
    role_prompt_file: str = ""
    model: str = "haiku"

    def load_prompt(self, prompts_dir: Path) -> str:
        """Load prompt content from file if prompt_file is set.

        Note: This method is for backward compatibility. For two-layer composition,
        use load_merged_prompt() instead.
        """
        if self.prompt:
            return self.prompt
        if self.prompt_file:
            prompt_path = prompts_dir / self.prompt_file
            if prompt_path.exists():
                return prompt_path.read_text(encoding="utf-8").strip()
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        return ""

    def load_merged_prompt(
        self,
        arch_prompts_dir: Path,
        custom_prompts_dir: Path | None = None,
    ) -> str:
        """Load and merge role prompt with instance prompt.

        Two-layer composition:
        1. Role prompt: Generic role capabilities from framework (arch_prompts_dir)
        2. Instance prompt: Business-specific context (custom_prompts_dir)

        Args:
            arch_prompts_dir: Framework architecture prompts directory
            custom_prompts_dir: Business custom prompts directory (optional)

        Returns:
            Merged prompt string with clear section separation
        """
        # If inline prompt is set, use it directly (highest priority)
        if self.prompt:
            return self.prompt

        # Load role prompt (framework layer)
        role_prompt = ""
        if self.role_prompt_file:
            role_path = arch_prompts_dir / self.role_prompt_file
            if role_path.exists():
                role_prompt = role_path.read_text(encoding="utf-8").strip()

        # Load instance prompt (business layer)
        instance_prompt = ""
        if self.prompt_file and custom_prompts_dir:
            instance_path = custom_prompts_dir / self.prompt_file
            if instance_path.exists():
                instance_prompt = instance_path.read_text(encoding="utf-8").strip()

        # Merge prompts with clear separation
        if role_prompt and instance_prompt:
            return f"{role_prompt}\n\n# Business Context\n\n{instance_prompt}"
        elif role_prompt:
            return role_prompt
        elif instance_prompt:
            return instance_prompt
        else:
            return ""


@dataclass
class AgentModelConfig:
    """
    Model configuration for architecture agents.

    Allows specifying default model and per-agent overrides.

    Attributes:
        default: Default model for all agents
        overrides: Per-agent model overrides {agent_name: model}
    """

    default: str = "haiku"
    overrides: dict[str, str] = field(default_factory=dict)

    def get_model(self, agent_name: str) -> str:
        """Get model for specific agent, falling back to default."""
        return self.overrides.get(agent_name, self.default)


@runtime_checkable
class ArchitecturePlugin(Protocol):
    """
    Protocol for architecture plugins.

    Plugins can hook into architecture lifecycle events.
    """

    def on_before_execute(self, prompt: str) -> str:
        """Called before execution, can modify prompt."""
        ...

    def on_after_stage(self, stage: str, result: Any) -> Any:
        """Called after each stage completes."""
        ...

    def on_error(self, error: Exception) -> bool:
        """Called on error, returns whether to continue."""
        ...


class BaseArchitecture(ABC):
    """
    Abstract base class for role-based architecture implementations.

    All architectures must inherit from this class and implement:
    - execute(): Main execution logic returning async message stream
    - get_role_definitions(): Returns role definitions for the architecture

    The role-based system separates:
    - Role definitions: What roles the architecture supports (abstract)
    - Agent instances: How business configs fill those roles (concrete)

    Workflow:
    1. Architecture defines roles via get_role_definitions()
    2. Business calls configure_agents() with AgentInstanceConfig list
    3. Architecture validates against role constraints
    4. get_agents() returns configured agent definitions
    """

    # Class attributes - override in subclasses
    name: str = "base"
    description: str = "Base architecture (abstract)"

    def __init__(
        self,
        model_config: AgentModelConfig | None = None,
        prompts_dir: Path | None = None,
        files_dir: Path | None = None,
        # Role-based configuration
        agent_instances: list[AgentInstanceConfig] | None = None,
        # Prompt customization (business_templates and skills support)
        business_template: str | None = None,
        custom_prompts_dir: Path | str | None = None,
        prompt_overrides: dict[str, str] | None = None,
        template_vars: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize architecture.

        Args:
            model_config: Model configuration for agents
            prompts_dir: Directory containing prompt files
            files_dir: Working directory for file operations
            agent_instances: List of agent instance configurations (role-based)
            business_template: Name of business template for prompts
            custom_prompts_dir: Application-level custom prompts directory
            prompt_overrides: Dict of agent_name -> override prompt content
            template_vars: Dict of template variables for ${var} substitution
        """
        self.model_config = model_config or AgentModelConfig()
        self._prompts_dir = prompts_dir
        self._files_dir = files_dir
        self._plugins: list[ArchitecturePlugin] = []  # Legacy plugin support
        self._result: Any = None

        # Prompt customization (business_templates support)
        self._business_template = business_template
        self._custom_prompts_dir = Path(custom_prompts_dir) if custom_prompts_dir else None
        self._prompt_overrides = prompt_overrides or {}
        self._template_vars = template_vars or {}

        # Role-based agent management
        self._role_registry = RoleRegistry()
        self._agent_instances: list[AgentInstanceConfig] = []
        self._configured_agents: dict[str, AgentDefinitionConfig] = {}

        # Register roles from subclass implementation
        self._register_roles()

        # Configure agents if provided
        if agent_instances:
            self.configure_agents(agent_instances)

        # New plugin system
        from claude_agent_framework.plugins.base import PluginManager

        self._plugin_manager = PluginManager()

        # Dynamic agent registry (for runtime additions)
        from claude_agent_framework.dynamic.agent_registry import DynamicAgentRegistry

        self._dynamic_agents = DynamicAgentRegistry()

    def _register_roles(self) -> None:
        """Register role definitions from subclass. Called during __init__."""
        for role_id, role_def in self.get_role_definitions().items():
            self._role_registry.register(role_id, role_def)

    @abstractmethod
    def get_role_definitions(self) -> dict[str, RoleDefinition]:
        """
        Get role definitions for this architecture.

        Each role defines:
        - role_type: Semantic type (worker, processor, etc.)
        - cardinality: How many agents can fill this role
        - required_tools: Tools any agent in this role must have
        - default_model: Suggested model tier

        Returns:
            Dict mapping role_id to RoleDefinition

        Example:
            >>> def get_role_definitions(self):
            ...     return {
            ...         "worker": RoleDefinition(
            ...             role_type=RoleType.WORKER,
            ...             cardinality=RoleCardinality.ONE_OR_MORE,
            ...             required_tools=["WebSearch"],
            ...         ),
            ...     }
        """
        pass

    def configure_agents(self, agents: list[AgentInstanceConfig]) -> None:
        """
        Configure agents from business configuration.

        Validates agent instances against role definitions and
        builds the internal agent configuration.

        Args:
            agents: List of agent instance configurations

        Raises:
            ValueError: If configuration doesn't match role requirements

        Example:
            >>> architecture.configure_agents([
            ...     AgentInstanceConfig(name="market-researcher", role="worker", ...),
            ...     AgentInstanceConfig(name="tech-researcher", role="worker", ...),
            ... ])
        """
        # Validate against role definitions
        errors = self._role_registry.validate_agents(agents)
        if errors:
            error_msg = "\n".join(f"  - {e}" for e in errors)
            raise ValueError(f"Agent configuration errors:\n{error_msg}")

        self._agent_instances = agents
        self._build_configured_agents()

    def _build_configured_agents(self) -> None:
        """Build AgentDefinitionConfig from validated agent instances."""
        self._configured_agents = {}

        for instance in self._agent_instances:
            role_def = self._role_registry.get(instance.role)
            if role_def:
                agent_def = instance.to_agent_definition(role_def, self.prompts_dir)
                self._configured_agents[instance.name] = agent_def

    def get_agents(self) -> dict[str, AgentDefinitionConfig]:
        """
        Get configured agent definitions.

        Returns:
            Dict mapping agent name to AgentDefinitionConfig

        Raises:
            ValueError: If agents not configured via configure_agents()
        """
        if not self._configured_agents:
            raise ValueError(
                "Agents not configured. Call configure_agents() with agent instances first."
            )
        return self._configured_agents

    # Role query methods
    def list_roles(self) -> list[str]:
        """
        List all role IDs defined by this architecture.

        Returns:
            List of role identifiers
        """
        return self._role_registry.list_roles()

    def get_role(self, role_id: str) -> RoleDefinition | None:
        """
        Get role definition by ID.

        Args:
            role_id: The role identifier

        Returns:
            RoleDefinition if found, None otherwise
        """
        return self._role_registry.get(role_id)

    def get_agents_by_role(self, role_id: str) -> list[str]:
        """
        Get agent names that fill a specific role.

        Args:
            role_id: The role identifier

        Returns:
            List of agent names filling this role
        """
        return [inst.name for inst in self._agent_instances if inst.role == role_id]

    def get_required_roles(self) -> list[str]:
        """
        Get all roles that require at least one agent.

        Returns:
            List of required role identifiers
        """
        return self._role_registry.get_required_roles()

    def get_optional_roles(self) -> list[str]:
        """
        Get all optional roles.

        Returns:
            List of optional role identifiers
        """
        return self._role_registry.get_optional_roles()

    @property
    def prompts_dir(self) -> Path:
        """Get prompts directory for this architecture."""
        if self._prompts_dir:
            return self._prompts_dir
        # Default: architectures/<name>/prompts/
        from claude_agent_framework.config import FRAMEWORK_ROOT

        return FRAMEWORK_ROOT / "architectures" / self.name / "prompts"

    @property
    def files_dir(self) -> Path:
        """Get files directory for this architecture."""
        if self._files_dir:
            return self._files_dir
        from claude_agent_framework.config import FILES_DIR

        return FILES_DIR / self.name

    @property
    def template_vars(self) -> dict[str, Any]:
        """Get template variables dict."""
        return self._template_vars

    @property
    def role_registry(self) -> RoleRegistry:
        """Get the role registry."""
        return self._role_registry

    @property
    def agent_instances(self) -> list[AgentInstanceConfig]:
        """Get the configured agent instances."""
        return self._agent_instances

    @abstractmethod
    async def execute(
        self,
        prompt: str,
        tracker: SubagentTracker | None = None,
        transcript: TranscriptWriter | None = None,
    ) -> AsyncIterator[Any]:
        """
        Execute the architecture's main logic.

        Args:
            prompt: User input prompt
            tracker: Optional subagent tracker for hook tracking
            transcript: Optional transcript writer for logging

        Yields:
            Messages from Claude SDK response stream
        """
        pass

    def get_lead_prompt(self) -> str:
        """
        Get the lead agent's system prompt.

        Override in subclasses to customize.
        """
        prompt_path = self.prompts_dir / "lead_agent.txt"
        if prompt_path.exists():
            prompt = prompt_path.read_text(encoding="utf-8").strip()
            # Apply template variable substitution
            if self._template_vars:
                from string import Template

                template = Template(prompt)
                prompt = template.safe_substitute(self._template_vars)
            return prompt
        return self._default_lead_prompt()

    def _default_lead_prompt(self) -> str:
        """Default lead agent prompt - override in subclasses."""
        return f"You are a {self.name} architecture coordinator."

    def get_hooks(self) -> dict[str, list]:
        """
        Get hook configuration for the architecture.

        Returns default hooks that can be overridden by subclasses.
        """
        return {}

    def _build_hooks(self, tracker: "SubagentTracker | None") -> dict[str, list]:
        """
        Build hook configuration for SDK client.

        Combines tracker hooks with custom hooks from get_hooks().
        This is a common implementation shared by all architectures.

        Args:
            tracker: Optional subagent tracker for tool call monitoring

        Returns:
            Dict of hook type to list of HookMatchers
        """
        from claude_agent_sdk import HookMatcher

        hooks: dict[str, list] = {}

        if tracker:
            hooks["PreToolUse"] = [
                HookMatcher(matcher=None, hooks=[tracker.pre_tool_use_hook])
            ]
            hooks["PostToolUse"] = [
                HookMatcher(matcher=None, hooks=[tracker.post_tool_use_hook])
            ]

        # Merge with custom hooks from get_hooks()
        custom_hooks = self.get_hooks()
        for hook_type, matchers in custom_hooks.items():
            if hook_type not in hooks:
                hooks[hook_type] = []
            hooks[hook_type].extend(matchers)

        return hooks

    def _customize_prompt(self, prompt: str) -> str:
        """
        Customize the user prompt before execution.

        Override in subclasses to wrap or modify the prompt.
        Default implementation returns prompt unchanged.

        Args:
            prompt: Original user prompt

        Returns:
            Modified prompt

        Examples:
            - Debate: wraps as "Debate Topic: {prompt}"
            - Reflexion: wraps as "Task: {prompt}"
            - Specialist-Pool: adds routing analysis
        """
        return prompt

    def _get_allowed_tools(self) -> list[str]:
        """
        Get allowed tools for the lead agent.

        Override in subclasses to customize.
        Default returns ["Task"] for standard orchestration.

        Returns:
            List of allowed tool names

        Examples:
            - MapReduce: returns ["Task", "Glob"]
        """
        return ["Task"]

    def _get_setting_sources(self) -> list[str]:
        """
        Get setting sources for SDK options.

        Override in subclasses to customize.
        Default returns ["project"].

        Returns:
            List of setting source names

        Examples:
            - Research: returns ["project", "user"]
        """
        return ["project"]

    async def setup(self) -> None:
        """
        Setup resources before execution.

        Override to perform initialization tasks.
        """
        # Ensure directories exist
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self.files_dir.mkdir(parents=True, exist_ok=True)

    async def teardown(self) -> None:
        """
        Cleanup resources after execution.

        Override to perform cleanup tasks.
        """
        pass

    def add_plugin(self, plugin: ArchitecturePlugin | BasePlugin) -> None:
        """
        Add a plugin to the architecture.

        Supports both legacy ArchitecturePlugin (Protocol) and new BasePlugin.

        Args:
            plugin: Plugin instance (legacy or new style)
        """
        from claude_agent_framework.plugins.base import BasePlugin

        if isinstance(plugin, BasePlugin):
            # New style plugin
            self._plugin_manager.register(plugin)
        elif isinstance(plugin, ArchitecturePlugin):
            # Legacy style plugin
            self._plugins.append(plugin)
        else:
            raise TypeError(f"Plugin must be BasePlugin or ArchitecturePlugin, got {type(plugin)}")

    def remove_plugin(self, plugin: ArchitecturePlugin | BasePlugin) -> None:
        """
        Remove a plugin from the architecture.

        Args:
            plugin: Plugin instance to remove
        """
        from claude_agent_framework.plugins.base import BasePlugin

        if isinstance(plugin, BasePlugin):
            self._plugin_manager.unregister(plugin)
        elif plugin in self._plugins:
            self._plugins.remove(plugin)

    @property
    def plugin_manager(self):
        """
        Get the plugin manager instance.

        Returns:
            PluginManager instance for advanced plugin management
        """
        return self._plugin_manager

    @property
    def dynamic_agents(self):
        """
        Get the dynamic agent registry.

        Returns:
            DynamicAgentRegistry instance for runtime agent management
        """
        return self._dynamic_agents

    def add_agent(
        self,
        name: str,
        description: str,
        tools: list[str],
        prompt: str,
        model: str = "haiku",
    ) -> None:
        """
        Add an agent dynamically at runtime.

        This allows adding new agents without modifying the architecture class.
        Dynamic agents are merged with configured agents from configure_agents().

        Args:
            name: Unique agent name (used as subagent_type)
            description: Description of when to use this agent
            tools: List of allowed tool names
            prompt: Agent system prompt
            model: Model to use (default: haiku)

        Raises:
            AgentConfigError: If configuration is invalid
            ValueError: If agent name already exists
        """
        self._dynamic_agents.register(
            name=name,
            description=description,
            tools=tools,
            prompt=prompt,
            model=model,
        )

    def remove_agent(self, name: str) -> None:
        """
        Remove a dynamically registered agent.

        Args:
            name: Agent name to remove

        Raises:
            KeyError: If agent not found in dynamic registry
        """
        self._dynamic_agents.unregister(name)

    def list_dynamic_agents(self) -> list[str]:
        """
        List all dynamically registered agent names.

        Returns:
            List of dynamic agent names
        """
        return self._dynamic_agents.list_agents()

    def _apply_before_execute(self, prompt: str) -> str:
        """Apply all plugin before_execute hooks."""
        for plugin in self._plugins:
            prompt = plugin.on_before_execute(prompt)
        return prompt

    def _apply_after_stage(self, stage: str, result: Any) -> Any:
        """Apply all plugin after_stage hooks."""
        for plugin in self._plugins:
            result = plugin.on_after_stage(stage, result)
        return result

    def _apply_on_error(self, error: Exception) -> bool:
        """Apply all plugin on_error hooks. Returns True if should continue."""
        for plugin in self._plugins:
            if not plugin.on_error(error):
                return False
        return True

    def get_result(self) -> Any:
        """Get the final result after execution."""
        return self._result

    def to_sdk_agents(self) -> dict[str, Any]:
        """
        Convert agent configs to Claude SDK AgentDefinition format.

        Two-layer prompt composition:
        1. Role prompt (framework layer): From RoleDefinition.prompt_file
           - Generic role capabilities, workflow framework, quality standards
        2. Instance prompt (business layer): From AgentInstanceConfig.prompt_file
           - Business context, Skills references, specific outputs

        Final prompt = role_prompt + "\\n\\n# Business Context\\n\\n" + instance_prompt

        Fallback to PromptComposer if no instance prompt_file is specified.
        Template variable substitution is applied to the final prompt.

        Returns:
            Dict suitable for ClaudeAgentOptions.agents parameter
        """
        from string import Template

        from claude_agent_sdk import AgentDefinition

        from claude_agent_framework.core.prompt import PromptComposer

        # Get configured agents
        agents = self.get_agents()
        result = {}

        # Create PromptComposer as fallback for agents without explicit prompt_file
        composer = PromptComposer(
            architecture_prompts_dir=self.prompts_dir,
            business_template=self._business_template,
            custom_prompts_dir=self._custom_prompts_dir,
            prompt_overrides=self._prompt_overrides,
            template_vars=self._template_vars,
        )

        for name, config in agents.items():
            # Use two-layer prompt composition
            # This merges role_prompt_file (framework) + prompt_file (business)
            merged_prompt = config.load_merged_prompt(
                arch_prompts_dir=self.prompts_dir,
                custom_prompts_dir=self._custom_prompts_dir,
            )

            if merged_prompt:
                prompt = merged_prompt
            else:
                # Fallback to PromptComposer for backward compatibility
                # (handles business_template and prompt_overrides)
                prompt = composer.compose(name)

            # Apply template variable substitution
            if self._template_vars and prompt:
                prompt = Template(prompt).safe_substitute(self._template_vars)

            result[name] = AgentDefinition(
                description=config.description,
                tools=config.tools,
                prompt=prompt,
                model=self.model_config.get_model(name),
            )

        # Merge dynamic agents (they override configured ones with same name)
        dynamic_agents = self._dynamic_agents.get_all()
        result.update(dynamic_agents)

        return result

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name!r})>"
