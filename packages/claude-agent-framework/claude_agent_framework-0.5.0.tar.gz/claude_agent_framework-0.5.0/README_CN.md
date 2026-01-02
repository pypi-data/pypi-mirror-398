# Claude Agent Framework

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

基于 [Claude Agent SDK](https://github.com/anthropics/claude-code-sdk-python) 的生产级多智能体编排框架。设计、组合、部署复杂的 AI 工作流，使用预置架构模式。

[English Documentation](README.md)

## 概述

Claude Agent Framework 解决了复杂任务需要多种专业能力的根本挑战——研究、分析、代码生成、决策——这些无法通过单一 LLM 提示词有效处理。框架将这些任务分解为协调的工作流，由**主智能体编排专业子智能体**，每个子智能体具有专注的提示词、受限的工具访问和适当的模型选择。

基于 Claude Agent SDK 构建，提供：

- **7 种经过验证的模式** — Research、Pipeline、Critic-Actor、Specialist Pool、Debate、Reflexion、MapReduce
- **角色类型架构** — 将角色定义与智能体实例分离，实现灵活配置
- **两层提示词系统** — 框架提示词 + 业务提示词，实现工作流复用
- **生产级插件系统** — 生命周期钩子用于指标、成本追踪、重试处理
- **完整可观测性** — 结构化 JSONL 日志、会话追踪、调试工具
- **简洁 API** — 从概念到运行系统只需几分钟

```python
from claude_agent_framework import create_session

session = create_session("research")
async for msg in session.run("分析 AI 编程助手的竞争格局"):
    print(msg)
```

---

## 为什么需要多智能体？

复杂任务需要多种专业能力。一个研究任务需要网络搜索、数据分析和报告撰写——每个环节需要不同的工具、提示词和模型。单一 LLM 提示词无法有效处理这种场景。

**单体方案的问题：**
- 提示词膨胀：一个提示词试图做所有事情，变得难以维护
- 工具过载：智能体在某些阶段访问了不该使用的工具
- 质量下降：万金油式的提示词不如专业化提示词效果好
- 成本浪费：简单子任务也使用昂贵模型

**解决方案：智能体专业化与编排**

```
用户请求
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│                         主智能体 (Lead Agent)                    │
│  • 接收请求，分解为子任务                                          │
│  • 只能使用 Task 工具派发子智能体                                  │
│  • 不直接执行研究/分析/写作任务                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │ Task 工具调用（并行）
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Worker 1   │  │  Worker 2   │  │  Processor  │  ...         │
│  │  (haiku)    │  │  (haiku)    │  │  (sonnet)   │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         └────────────────┼────────────────┘                      │
│                          ▼                                       │
│                   files/ (文件系统)                               │
│                   通过文件松耦合                                   │
└─────────────────────────────────────────────────────────────────┘
```

**核心原则：**

| 原则 | 实现方式 |
|------|----------|
| 职责分离 | 主智能体编排，子智能体执行 |
| 工具约束 | 每个智能体只获得所需工具 |
| 松耦合 | 基于文件系统的数据交换 |
| 成本优化 | 根据任务复杂度匹配模型能力 |

---

## 快速开始

```bash
pip install claude-agent-framework
export ANTHROPIC_API_KEY="your-api-key"
```

```python
from claude_agent_framework import create_session
import asyncio

async def main():
    session = create_session("research")
    async for msg in session.run("分析 AI 编程助手的竞争格局"):
        print(msg)

asyncio.run(main())
```

---

## 架构模式

框架提供 7 种预置架构模式：

| 架构 | 模式 | 适用场景 |
|------|------|----------|
| **research** | 主从并行 | 多源数据采集、市场研究、文献综述 |
| **pipeline** | 顺序阶段 | 代码审查、内容工作流、多步审批 |
| **critic_actor** | 生成-评审循环 | 质量改进、迭代优化 |
| **specialist_pool** | 专家路由 | 技术支持、问答系统、诊断系统 |
| **debate** | 正反辩论 | 决策支持、风险评估、供应商评估 |
| **reflexion** | 执行-反思-改进 | 调试、根因分析、优化问题 |
| **mapreduce** | 并行映射+归约 | 大规模分析（500+文件）、批处理 |

每个架构定义了具有特定约束的**角色**：

```python
# Research 架构角色
worker      → RoleCardinality.ONE_OR_MORE   # 并行数据收集者
processor   → RoleCardinality.ZERO_OR_ONE   # 可选数据处理者
synthesizer → RoleCardinality.EXACTLY_ONE   # 必需结果综合者
```

---

## 构建业务应用

构建业务应用包含 5 个步骤：

### 步骤 1：选择架构

将你的工作流模式匹配到架构：
- 并行数据采集 → **Research**
- 顺序阶段处理 → **Pipeline**
- 迭代质量改进 → **Critic-Actor**
- 专家路由分发 → **Specialist Pool**
- 决策分析 → **Debate**
- 试错探索 → **Reflexion**
- 大规模处理 → **MapReduce**

### 步骤 2：定义智能体实例

将业务角色映射到架构角色：

```python
from claude_agent_framework.core.roles import AgentInstanceConfig

agents = [
    AgentInstanceConfig(
        name="market-researcher",      # 业务名称
        role="worker",                 # 架构角色
        description="市场数据收集",
        prompt_file="researcher.txt",
    ),
    AgentInstanceConfig(
        name="report-writer",
        role="synthesizer",
    ),
]
```

### 步骤 3：编写业务提示词

创建 `prompts/` 目录，包含业务特定上下文：

```
prompts/lead_agent.txt
```

```markdown
# 竞争情报协调者

你正在为 ${company_name} 协调分析工作。

## 团队与技能
- **研究员**: 使用 `competitive-research` 技能获取方法论
- **报告撰写者**: 使用 `report-generation` 技能进行格式化

## 交付物
- 研究笔记 → files/research_notes/
- 最终报告 → files/reports/
```

框架将你的业务提示词与通用框架提示词合并：

```
最终提示词 = 框架提示词（通用角色规则）
           + 业务提示词（领域上下文）
           + 模板变量（${company_name} → "Acme Corp"）
```

### 步骤 4：创建技能（可选）

技能提供方法论指导，智能体根据上下文自动调用：

```
.claude/skills/competitive-research/SKILL.md
```

```markdown
---
name: competitive-research
description: 竞争情报方法论
---

# 研究重点
- 产品与服务分析
- 市场定位
- 财务指标

# 数据收集优先级
1. 市场数据（规模、份额、增长）
2. 财务数据（营收、估值）
3. 技术指标

# 输出规范
保存至: files/research_notes/{competitor}.md
```

### 步骤 5：配置并运行

```python
from pathlib import Path
from claude_agent_framework import create_session
from claude_agent_framework.core.roles import AgentInstanceConfig

agents = [
    AgentInstanceConfig(name="market-researcher", role="worker"),
    AgentInstanceConfig(name="tech-researcher", role="worker"),
    AgentInstanceConfig(name="report-writer", role="synthesizer"),
]

session = create_session(
    "research",
    agent_instances=agents,
    prompts_dir=Path("prompts"),
    template_vars={
        "company_name": "Acme Corp",
        "industry": "Technology",
    },
)

async for msg in session.run("分析竞争对手 X、Y、Z"):
    print(msg)
```

---

## 完整示例结构

```
my_competitive_intel/
├── main.py                           # 入口点
├── config.yaml                       # 配置
├── prompts/                          # 业务提示词
│   ├── lead_agent.txt                # 协调策略
│   ├── researcher.txt                # 研究方法论
│   └── report_writer.txt             # 报告格式
└── .claude/skills/                   # 方法论指导
    ├── competitive-research/SKILL.md
    └── report-generation/SKILL.md
```

参见 [`examples/production/`](examples/production/) 获取 7 个完整的生产级示例。

---

## 两层提示词架构

提示词由两层组合而成：

| 层级 | 位置 | 作用 |
|------|------|------|
| **框架层** | `architectures/*/prompts/` | 通用角色能力、工作流规则、派发指南 |
| **业务层** | 你的 `prompts/` 目录 | 领域上下文、技能引用、交付物、成功标准 |

**框架提示词**（通用、可复用）：
```markdown
# 角色：研究协调者

## 核心规则
1. 你只能使用 Task 工具派发子智能体
2. 绝不自己执行研究、分析或写作任务

## 工作流阶段
1. 规划阶段 - 识别可并行的子主题
2. 研究阶段 - 并行派发 worker
3. 处理阶段 - 派发 processor（如已配置）
4. 综合阶段 - 派发 synthesizer 生成最终输出
```

**业务提示词**（领域特定）：
```markdown
# 竞争情报协调者

你正在为 ${company_name}（${industry} 领域）协调分析工作。

## 团队与技能
- **研究员**: 使用 `competitive-research` 技能
- **报告撰写者**: 使用 `report-generation` 技能

## 交付物
- 每个竞争对手的 SWOT 分析
- 功能对比矩阵
- 战略建议
```

---

## 角色配置

框架将**角色定义**（架构级）与**智能体实例**（业务级）分离：

```python
# 架构定义角色约束
class ResearchArchitecture(BaseArchitecture):
    def get_role_definitions(self) -> dict[str, RoleDefinition]:
        return {
            "worker": RoleDefinition(
                role_type=RoleType.WORKER,
                required_tools=["WebSearch"],
                cardinality=RoleCardinality.ONE_OR_MORE,  # 1-N 个 worker
                default_model="haiku",
            ),
            "synthesizer": RoleDefinition(
                role_type=RoleType.SYNTHESIZER,
                required_tools=["Write"],
                cardinality=RoleCardinality.EXACTLY_ONE,  # 恰好 1 个
                default_model="sonnet",
            ),
        }

# 业务配置具体智能体
agents = [
    AgentInstanceConfig(name="market-researcher", role="worker"),
    AgentInstanceConfig(name="tech-researcher", role="worker"),
    AgentInstanceConfig(name="report-writer", role="synthesizer", model="opus"),
]
```

---

## 自定义架构

```python
from claude_agent_framework import register_architecture, BaseArchitecture
from claude_agent_framework.core.roles import RoleDefinition
from claude_agent_framework.core.types import RoleType, RoleCardinality

@register_architecture("my_workflow")
class MyWorkflow(BaseArchitecture):
    name = "my_workflow"
    description = "我的自定义工作流"

    def get_role_definitions(self) -> dict[str, RoleDefinition]:
        return {
            "executor": RoleDefinition(
                role_type=RoleType.EXECUTOR,
                description="执行任务",
                required_tools=["Read", "Write", "Bash"],
                cardinality=RoleCardinality.ONE_OR_MORE,
            ),
            "reviewer": RoleDefinition(
                role_type=RoleType.CRITIC,
                description="审查结果",
                required_tools=["Read"],
                cardinality=RoleCardinality.EXACTLY_ONE,
            ),
        }

    async def execute(self, prompt, tracker=None, transcript=None):
        # 你的编排逻辑
        ...
```

---

## 插件系统

```python
from claude_agent_framework import create_session
from claude_agent_framework.plugins.builtin import (
    MetricsCollectorPlugin,
    CostTrackerPlugin,
)

session = create_session("research")

# 添加指标追踪
metrics = MetricsCollectorPlugin()
session.architecture.add_plugin(metrics)

# 添加成本追踪（带预算限制）
cost = CostTrackerPlugin(budget_usd=5.0)
session.architecture.add_plugin(cost)

async for msg in session.run("分析市场"):
    print(msg)

# 获取结果
print(f"成本: ${metrics.get_metrics().estimated_cost_usd:.4f}")
```

---

## 会话生命周期

```python
# 方式 1：手动管理
session = create_session("research")
try:
    async for msg in session.run(prompt):
        process(msg)
finally:
    await session.teardown()

# 方式 2：上下文管理器
async with create_session("research") as session:
    results = await session.query(prompt)
```

---

## 输出

每次会话生成：

```
logs/session_YYYYMMDD_HHMMSS/
├── transcript.txt      # 人类可读对话日志
└── tool_calls.jsonl    # 结构化工具调用记录

files/
└── <architecture>/     # 架构特定输出
```

---

## 安装

```bash
# 基础安装
pip install claude-agent-framework

# 支持 PDF 生成
pip install "claude-agent-framework[pdf]"

# 支持图表生成
pip install "claude-agent-framework[charts]"

# 完整安装
pip install "claude-agent-framework[all]"
```

---

## 文档

| 文档 | 描述 |
|------|------|
| [最佳实践](docs/BEST_PRACTICES_CN.md) | 模式选择和实现技巧 |
| [角色类型架构](docs/ROLE_BASED_ARCHITECTURE_CN.md) | 角色类型、约束和智能体实例化 |
| [提示词编写指南](docs/PROMPT_WRITING_GUIDE.md) | 两层提示词架构 |
| [核心 API 参考](docs/api/core_cn.md) | `create_session()`、`AgentSession`、`BaseArchitecture` |
| [插件 API 参考](docs/api/plugins_cn.md) | 插件系统和生命周期钩子 |
| [架构选择指南](docs/guides/architecture_selection/GUIDE_CN.md) | 选择合适的架构 |

---

## 生产级示例

[`examples/production/`](examples/production/) 中的全部 7 个示例均已完成并可投入生产：

| 示例 | 架构 | 业务场景 |
|------|------|----------|
| [01_competitive_intelligence](examples/production/01_competitive_intelligence/) | Research | SaaS 竞品分析 |
| [02_pr_code_review](examples/production/02_pr_code_review/) | Pipeline | 自动化 PR 审查 |
| [03_marketing_content](examples/production/03_marketing_content/) | Critic-Actor | 营销文案优化 |
| [04_it_support](examples/production/04_it_support/) | Specialist Pool | IT 支持路由 |
| [05_tech_decision](examples/production/05_tech_decision/) | Debate | 技术决策支持 |
| [06_code_debugger](examples/production/06_code_debugger/) | Reflexion | 自适应调试 |
| [07_codebase_analysis](examples/production/07_codebase_analysis/) | MapReduce | 大规模代码库分析 |

### 通用生产模式

所有生产示例遵循以下验证过的模式：

| 模式 | 实现方式 |
|------|----------|
| **配置驱动** | YAML 配置文件带验证、环境特定设置、无硬编码值 |
| **结构化结果** | 一致的 JSON 模式、编程访问、多格式输出（JSON/Markdown/PDF） |
| **健壮错误处理** | I/O 边界 try/catch、优雅降级、详细错误上下文 |
| **完整日志记录** | JSONL 工具追踪、人类可读转录、基于会话的组织 |
| **生产级测试** | 单元测试 + 集成测试、模拟外部依赖、100% 通过要求 |

### 各架构使用场景

| 架构 | 适用场景 | 示例 |
|------|----------|------|
| **Research** | 从多个独立数据源并行采集数据 | 市场研究、竞品分析、文献综述 |
| **Pipeline** | 具有质量门的清晰顺序阶段 | 代码审查、内容工作流、多步审批 |
| **Critic-Actor** | 输出需要针对定义标准迭代改进 | 内容优化、代码重构、设计迭代 |
| **Specialist Pool** | 请求需要路由到领域专家 | 技术支持、问答系统、诊断系统 |
| **Debate** | 决策需要平衡的正反分析 | 技术选型、架构决策、供应商评估 |
| **Reflexion** | 问题需要试错并从中学习 | 调试、根因分析、优化问题 |
| **MapReduce** | 大数据集（500+ 文件）需要并行处理 | 代码库分析、批处理、大规模审计 |

---

## 环境要求

- Python 3.10+
- `ANTHROPIC_API_KEY` 环境变量

## 许可证

MIT License - 详见 [LICENSE](LICENSE)
