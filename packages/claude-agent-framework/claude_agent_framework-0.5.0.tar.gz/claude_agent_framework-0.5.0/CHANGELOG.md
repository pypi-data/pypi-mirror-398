# Changelog

All notable changes to Claude Agent Framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2025-12-26

### Added

#### Plugin System
- **Production Plugin System** with 9 lifecycle hooks for comprehensive workflow control
  - Session hooks: `on_session_start`, `on_session_end`
  - Execution hooks: `on_before_execute`, `on_after_execute`
  - Agent hooks: `on_agent_spawn`, `on_agent_complete`
  - Tool hooks: `on_tool_call`, `on_tool_result`
  - Error hook: `on_error`
- **Built-in Plugins**:
  - `MetricsCollectorPlugin` - Comprehensive performance and usage tracking
  - `CostTrackerPlugin` - Token usage and cost estimation with budget limits
  - `RetryHandlerPlugin` - Automatic retry on agent/tool failures
- Plugin API in `src/claude_agent_framework/plugins/`
  - `BasePlugin` abstract class for custom plugin development
  - `PluginManager` for plugin registration and lifecycle management
  - Hook execution with error isolation

#### Configuration System
- **Advanced Configuration** with Pydantic validation
  - Type-safe configuration schema with `FrameworkConfigSchema`
  - Multi-source configuration loading (YAML, environment variables, Python dict)
  - Configuration inheritance and override mechanisms
  - Environment-specific profiles (development, staging, production)
- **ConfigLoader** utility for flexible configuration management
  - `from_yaml()` - Load from YAML files
  - `from_env()` - Load from environment variables with prefix
  - `load_with_profile()` - Load environment-specific profiles
- Configuration validation with detailed error messages
- Located in `src/claude_agent_framework/config/`

#### Metrics & Performance Tracking
- **MetricsCollector** for comprehensive performance tracking
  - Execution duration (total and per-stage)
  - Token usage statistics (input/output/total)
  - Cost estimation based on Claude pricing
  - Agent spawn tracking (count, types, distribution)
  - Tool call statistics (count, types, error rates)
  - Memory profiling (peak and average usage)
- **Multi-format Export**:
  - JSON - Human-readable structured data
  - CSV - Spreadsheet-compatible format
  - Prometheus - Monitoring system integration
- `MetricsAggregator` for session comparison and trend analysis
- Located in `src/claude_agent_framework/metrics/`

#### Dynamic Agent Registry
- **Runtime Agent Registration** without code changes
  - `add_agent()` - Register new agents dynamically
  - `remove_agent()` - Remove agents at runtime
  - `list_dynamic_agents()` - Query registered agents
- **Dynamic Architecture Creation** for custom workflows
  - `create_dynamic_architecture()` - Build architectures programmatically
  - Runtime modification of agent configurations
- Agent validation and conflict detection
- Located in `src/claude_agent_framework/dynamic/`

#### Observability
- **EventLogger** for structured JSONL logging
  - Session lifecycle events
  - Agent spawn and completion events
  - Tool call and result events
  - Error and warning events
  - Query-able log files for debugging
- **SessionVisualizer** for interactive session analysis
  - Timeline visualization with D3.js
  - Tool call dependency graphs
  - Performance bottleneck identification
  - HTML dashboard generation
- **InteractiveDebugger** for real-time session inspection
  - Step-through session execution
  - Breakpoint support on hooks
  - Live variable inspection
  - Call stack visualization
- Located in `src/claude_agent_framework/observability/`

#### CLI Enhancements
- **Session Metrics Command**: `claude-agent metrics <session-id>`
  - Display duration, token usage, cost breakdown
  - Agent and tool call statistics
  - Performance summary
- **Interactive Dashboard Command**: `claude-agent view <session-id>`
  - Opens browser with session timeline
  - Tool call graphs and performance charts
  - Real-time session monitoring (for active sessions)
- **HTML Report Command**: `claude-agent report <session-id> --output <file>`
  - Generate comprehensive session reports
  - Include charts, tables, and execution logs
  - Shareable standalone HTML files

#### Documentation
- **Comprehensive Bilingual Documentation**:
  - Architecture Selection Guide (EN/CN): `docs/guides/architecture_selection/`
  - Custom Architecture Guide (EN/CN): `docs/guides/customization/CUSTOM_ARCHITECTURE.md`
  - Plugin Development Guide (EN/CN): `docs/guides/customization/CUSTOM_PLUGINS.md`
  - Performance Tuning Guide (EN/CN): `docs/guides/advanced/PERFORMANCE_TUNING.md`
  - Cost Optimization Guide (EN/CN): `docs/guides/advanced/COST_OPTIMIZATION.md`
- **API Reference Documentation**:
  - Core API (EN/CN): `docs/api/core.md`
  - Plugins API (EN/CN): `docs/api/plugins.md`
  - Architectures API (EN/CN): `docs/api/architectures.md`
- **Updated README** with v0.4.0 feature documentation
- **Enhanced BEST_PRACTICES** with plugin and performance guidance

#### Production Examples
- **7 Real-World Examples** demonstrating all architectures with v0.4.0 features:
  - `01_competitive_intelligence/` - Research architecture with web search integration
  - `02_pr_code_review/` - Pipeline architecture for code quality automation
  - `03_marketing_content/` - Critic-Actor for content optimization
  - `04_it_support/` - Specialist Pool for intelligent routing
  - `05_tech_decision/` - Debate architecture for technical decisions
  - `06_code_debugger/` - Reflexion for adaptive debugging
  - `07_codebase_analysis/` - MapReduce for large-scale analysis
- Each example includes:
  - Complete runnable code with error handling
  - Plugin usage demonstrations
  - Configuration examples
  - Comprehensive testing
  - Bilingual documentation (README.md/README_CN.md)

### Changed

- **Enhanced BaseArchitecture**:
  - Integrated `PluginManager` for lifecycle hooks
  - Support for dynamic agent registration
  - Improved error handling and logging
- **Improved AgentSession**:
  - Session-level metrics tracking
  - Enhanced observability with event logging
  - Better resource cleanup in teardown
- **Optimized Code Quality**:
  - Fixed 73 linting errors with ruff
  - Reformatted 50 files with ruff format
  - Added type hints across codebase
  - Documented 62 known type issues for future improvement

### Fixed

- Code style inconsistencies across modules
- Import ordering and unused imports
- F-string usage without placeholders
- Modern type hint adoption (collections.abc over typing)

### Dependencies

- **Added**:
  - `pydantic>=2.0.0` - Configuration validation (optional: [config])
  - `prometheus-client>=0.20.0` - Metrics export (optional: [metrics])
  - `matplotlib>=3.7.0` - Visualization (optional: [viz])
  - `jinja2>=3.1.0` - HTML template rendering (optional: [viz])
  - `types-PyYAML>=6.0.12` - Type stubs for YAML (dev)

### Testing

- **187 tests** with 100% pass rate
- **64% test coverage** overall
- **High coverage** (>85%) on all new v0.4.0 modules:
  - Metrics: 98-99%
  - Observability: 95-98%
  - Configuration: 87-93%
  - Dynamic agents: 92-97%

### Migration Guide

#### From v0.3.x to v0.4.0

**No Breaking Changes** - v0.4.0 is fully backward compatible with v0.3.x. All new features are opt-in.

**To Use New Features**:

1. **Install Optional Dependencies**:
```bash
# For all new features
pip install claude-agent-framework[all]

# Or selectively
pip install claude-agent-framework[config,metrics,viz]
```

2. **Add Plugins to Existing Code**:
```python
from claude_agent_framework import init
from claude_agent_framework.plugins.builtin import MetricsCollectorPlugin

session = init("research")
session.architecture.add_plugin(MetricsCollectorPlugin())
# Existing code continues to work
```

3. **Use New CLI Commands**:
```bash
# View metrics for any session
claude-agent metrics <session-id>
```

**No Code Changes Required** - Existing code continues to work without modification.

---

## [0.3.0] - 2025-12-20

### Added
- Initial public release
- 7 pre-built architecture patterns (Research, Pipeline, Critic-Actor, Specialist Pool, Debate, Reflexion, MapReduce)
- Simplified `init()` API for quick start
- Architecture registry system
- Basic CLI with `run` and `list` commands
- Session lifecycle management
- Subagent tracking and transcript logging
- Bilingual documentation (English/Chinese)
- Best practices guide
- Basic examples for each architecture

### Changed
- Migrated from standalone to Claude Agent SDK integration
- Simplified configuration management
- Improved async/await patterns

### Fixed
- Session cleanup issues
- Agent communication race conditions
- File path resolution on Windows

---

## [0.2.0] - 2025-12-10

### Added
- MapReduce architecture for large-scale processing
- Reflexion architecture for complex problem solving
- Basic metrics tracking (token usage)
- Session transcript logging

### Changed
- Refactored agent communication to use filesystem
- Improved error handling across architectures

---

## [0.1.0] - 2025-12-01

### Added
- Initial prototype release
- Research, Pipeline, Critic-Actor, Specialist Pool, Debate architectures
- Basic agent orchestration framework
- Example code for each architecture

---

[0.4.0]: https://github.com/yourusername/claude-agent-framework/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/yourusername/claude-agent-framework/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/yourusername/claude-agent-framework/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/yourusername/claude-agent-framework/releases/tag/v0.1.0
