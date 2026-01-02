# Claude Agent Framework - 最佳实践指南

> 使用 Claude Agent Framework 构建多智能体系统的完整开发指南

## 目录

1. [设计理念](#1-设计理念)
2. [架构模式](#2-架构模式)
3. [核心组件](#3-核心组件)
4. [多智能体编排](#4-多智能体编排)
5. [Hook 机制](#5-hook-机制)
6. [工具分配](#6-工具分配)
7. [提示词工程](#7-提示词工程)
8. [状态管理](#8-状态管理)
9. [错误处理](#9-错误处理)
10. [日志与审计](#10-日志与审计)
11. [配置管理](#11-配置管理)
12. [完整示例](#12-完整示例)

---

## 1. 设计理念

### 1.1 为什么需要多智能体？

复杂任务通常需要多种专业能力，单一 LLM 提示词无法有效处理。以研究任务为例：需要网络搜索、数据分析、报告撰写——每个环节需要不同的工具、提示词甚至模型。单体方案会导致：

- **提示词膨胀**：一个提示词试图做所有事情，变得难以维护
- **工具过载**：智能体在某些阶段访问了不该使用的工具
- **质量下降**：万金油式的提示词不如专业化提示词效果好
- **成本浪费**：简单子任务也使用昂贵模型

解决方案：**智能体专业化与编排** - 将复杂任务分解为由主智能体协调的专业化智能体。

### 1.2 框架概述

Claude Agent Framework 为多智能体系统提供 **7 种不同的编排模式**。虽然所有架构共享通用设计原则，但每种架构都实现了适合特定问题领域的独特工作流模式。

### 1.3 编排模式

每种架构实现不同的编排模式：

| 架构 | 模式 | 流程 | 最适用于 |
|------|------|------|----------|
| **Research** | 扇出/扇入 | 主智能体 → [工作者并行] → 聚合器 | 数据收集、深度研究 |
| **Pipeline** | 顺序链 | 阶段 A → B → C → D | 代码审查、内容创作 |
| **Critic-Actor** | 迭代优化 | 生成 ↔ 评估（循环） | 质量优化 |
| **Specialist Pool** | 动态路由 | 路由器 → 专家 → 综合 | 技术支持、问答 |
| **Debate** | 对抗辩论 | 正方 ↔ 反方（N轮）→ 裁判 | 决策支持 |
| **Reflexion** | 自我改进循环 | 执行 → 反思 → 改进 | 复杂问题求解 |
| **MapReduce** | 分治并行 | 分割 → [映射并行] → 归约 | 大规模分析 |

### 1.4 模式图示

**扇出/扇入（Research）**
```
主智能体 ─┬─→ 工作者 1 ─┐
          ├─→ 工作者 2 ─┼─→ 聚合器 → 输出
          └─→ 工作者 3 ─┘
```

**顺序链（Pipeline）**
```
阶段 A → 阶段 B → 阶段 C → 阶段 D → 输出
```

**迭代优化（Critic-Actor）**
```
┌─────────────────────────┐
│  Actor ──→ Critic       │
│    ↑         │          │
│    └─────────┘ (重复)   │
└─────────────────────────┘
```

**动态路由（Specialist Pool）**
```
查询 → 路由器 ─┬─→ 专家 A ─┐
              ├─→ 专家 B ─┼─→ 综合器
              └─→ 专家 C ─┘
```

**对抗辩论（Debate）**
```
议题 → 正方 ↔ 反方（N轮）→ 裁判 → 裁决
```

**自我改进循环（Reflexion）**
```
┌─────────────────────────────────┐
│  执行器 → 反思器 → 改进        │
│      ↑                │        │
│      └────────────────┘        │
└─────────────────────────────────┘
```

**分治并行（MapReduce）**
```
任务 → 分割器 ─┬─→ 映射器 1 ─┐
              ├─→ 映射器 2 ─┼─→ 归约器 → 结果
              └─→ 映射器 3 ─┘
```

### 1.5 通用设计原则

尽管编排模式不同，所有架构共享这些核心原则：

| 原则 | 描述 | 实现方式 |
|------|------|----------|
| **职责分离** | 每个智能体只做一件事 | 主智能体编排，子智能体执行特定任务 |
| **工具约束** | 限制可用工具集 | 每个智能体精确控制 `allowed_tools` |
| **松耦合** | 智能体通过文件系统交换数据 | 标准目录结构 + Glob/Read/Write |
| **可观测性** | 全链路追踪能力 | Hook 机制 + JSONL 日志 |
| **成本优化** | 明智选择模型 | 子智能体使用 Haiku 以降低成本 |
| **可扩展性** | 易于添加新模式 | 基于注册表的架构系统 |
| **类型安全** | 全程强类型 | Pydantic 模型、类型提示 |

### 1.6 选择合适的模式

| 场景 | 推荐模式 | 原因 |
|------|----------|------|
| 从多个来源收集信息 | **Research**（扇出/扇入） | 并行数据收集，然后综合 |
| 有明确交接的逐步处理 | **Pipeline**（顺序链） | 清晰的阶段边界，渐进式优化 |
| 通过反馈进行质量改进 | **Critic-Actor**（迭代） | 生成-评估循环直到达到阈值 |
| 将查询路由到领域专家 | **Specialist Pool**（动态） | 将查询类型匹配到专家能力 |
| 分析决策的利弊 | **Debate**（对抗） | 结构化论证，平衡分析 |
| 需要反思的复杂问题 | **Reflexion**（自我改进） | 从尝试中学习，优化策略 |
| 并行处理大型数据集 | **MapReduce**（分治） | 并行处理，高效聚合 |

---

## 2. 架构模式

### 2.1 模式选择指南

| 模式 | 最适用于 | 关键特征 |
|------|----------|----------|
| **Research** | 数据收集、分析 | 并行工作者 → 综合 |
| **Pipeline** | 顺序工作流 | 阶段 A → 阶段 B → 阶段 C |
| **Critic-Actor** | 质量迭代 | 生成 ↔ 评估循环 |
| **Specialist Pool** | 专家路由 | 按领域动态分发 |
| **Debate** | 决策分析 | 正反辩论 + 裁判 |
| **Reflexion** | 复杂问题求解 | 执行 → 反思 → 改进 |
| **MapReduce** | 大规模处理 | 分割 → 并行映射 → 归约 |

### 2.2 模式内部结构

#### Research 模式

```
                    ┌──────────────┐
                    │   主智能体    │
                    │  （协调者）   │
                    └──────┬───────┘
                           │ 任务分解
            ┌──────────────┼──────────────┐
            ↓              ↓              ↓
      ┌──────────┐  ┌──────────┐  ┌──────────┐
      │ 研究员 1 │  │ 研究员 2 │  │ 研究员 3 │
      └────┬─────┘  └────┬─────┘  └────┬─────┘
           │             │             │
           └──────┬──────┴──────┬──────┘
                  ↓             ↓
           files/research_notes/*.md
                        ↓
                ┌──────────────┐
                │   数据分析师  │
                └──────┬───────┘
                       ↓
                files/charts/*.png
                       ↓
                ┌──────────────┐
                │   报告撰写者  │
                └──────┬───────┘
                       ↓
                files/reports/*.pdf
```

#### Pipeline 模式

```
┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐
│ 架构师 │ → │ 编码者 │ → │ 审查者 │ → │ 测试者 │
└────────┘   └────────┘   └────────┘   └────────┘
     │            │            │            │
     ↓            ↓            ↓            ↓
   设计         实现         反馈         测试
```

#### Critic-Actor 模式

```
┌─────────────────────────────────────────┐
│                                         │
│   ┌─────────┐         ┌─────────┐      │
│   │  Actor  │ ──────→ │  Critic │      │
│   └────┬────┘         └────┬────┘      │
│        ↑    内容           │           │
│        │                   │ 反馈      │
│        └───────────────────┘           │
│                                         │
│   while 质量 < 阈值                     │
└─────────────────────────────────────────┘
```

---

## 3. 核心组件

### 3.1 初始化

框架提供简化的入口点：

```python
from claude_agent_framework import init

# 最简用法 - 两行代码启动
session = init("research")
async for msg in session.run("分析 AI 市场趋势"):
    print(msg)
```

### 3.2 架构组件

每个架构包含：

```
architectures/<name>/
├── __init__.py          # 导出
├── config.py            # 架构特定配置
├── orchestrator.py      # 主架构类
└── prompts/             # 智能体提示词
    ├── lead_agent.txt
    ├── agent_a.txt
    └── agent_b.txt
```

### 3.3 BaseArchitecture 接口

```python
from claude_agent_framework.core import BaseArchitecture, register_architecture

@register_architecture("my_architecture")
class MyArchitecture(BaseArchitecture):
    """自定义架构实现。"""

    name = "my_architecture"
    description = "在架构列表中显示的描述"

    def get_agents(self) -> dict[str, AgentDefinitionConfig]:
        """定义子智能体及其配置。"""
        return {
            "worker": AgentDefinitionConfig(
                name="worker",
                description="执行特定任务",
                tools=["Read", "Write"],
                prompt_file="worker.txt",
            ),
        }

    async def execute(
        self,
        prompt: str,
        tracker: SubagentTracker | None = None,
        transcript: TranscriptWriter | None = None,
    ) -> AsyncIterator[Any]:
        """执行架构工作流。"""
        # 实现
        ...
```

### 3.4 AgentSession

管理完整的会话生命周期：

```python
session = init("research")

try:
    async for msg in session.run("查询"):
        print(msg)
finally:
    await session.teardown()  # 清理

# 或使用上下文管理器
async with init("research") as session:
    results = await session.query("查询")
```

---

## 4. 多智能体编排

### 4.1 并行派发

主智能体同时派发多个子智能体：

```python
# 在主智能体提示词中：
"""
# 规则
1. 你只能使用 Task 工具派发子智能体
2. 绝不自己执行研究、分析或写作
3. 将请求分解为 2-4 个独立的子主题
4. 并行派发研究员（不是顺序）
5. 等待所有研究完成后再派发分析师
"""
```

### 4.2 文件系统协调

智能体通过标准目录结构通信：

```python
FILE_STRUCTURE = {
    "files/research_notes/": "研究员输出 → 分析师输入",
    "files/data/":           "分析师输出 → 报告者输入",
    "files/charts/":         "分析师图表 → 报告者引用",
    "files/reports/":        "报告者最终输出",
}
```

### 4.3 主智能体模板

```text
# 角色定义
你是研究协调员，负责任务分解和子智能体编排。

# 核心规则
1. 你只能使用 Task 工具派发子智能体
2. 绝不自己执行研究、分析或写作
3. 将研究请求分解为 2-4 个独立的子主题
4. 并行派发研究员（不是顺序）
5. 等待所有研究完成后再派发分析师
6. 最后派发报告者生成输出

# 工作流程
1. 分析用户请求 → 识别子主题
2. 并行派发研究员 → 收集信息
3. 派发分析师 → 处理数据
4. 派发报告者 → 生成报告
5. 向用户报告完成状态

# 可用子智能体
- researcher: 网络搜索和信息收集
- data-analyst: 数据处理和可视化
- report-writer: 最终报告生成
```

---

## 5. Hook 机制

### 5.1 Hook 类型

| Hook 类型 | 触发时机 | 用途 |
|-----------|----------|------|
| `PreToolUse` | 工具执行前 | 输入验证、权限检查、日志记录 |
| `PostToolUse` | 工具执行后 | 结果捕获、错误处理、指标收集 |
| `Notification` | 通知事件 | 状态更新、进度报告 |

### 5.2 Hook 配置

```python
from claude_agent_sdk import HookMatcher

hooks = {
    'PreToolUse': [
        HookMatcher(
            matcher=None,  # None = 匹配所有工具
            hooks=[tracker.pre_tool_use_hook]
        )
    ],
    'PostToolUse': [
        HookMatcher(
            matcher=None,
            hooks=[tracker.post_tool_use_hook]
        )
    ]
}
```

### 5.3 SubagentTracker 实现

```python
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime

@dataclass
class ToolCallRecord:
    """单个工具调用记录。"""
    timestamp: str
    tool_name: str
    tool_input: dict[str, Any]
    tool_use_id: str
    subagent_type: str
    parent_tool_use_id: str | None = None
    tool_output: Any = None
    error: str | None = None

class SubagentTracker:
    """追踪子智能体生成和工具调用。"""

    def __init__(self, log_file_path: str):
        self.sessions: dict[str, SubagentSession] = {}
        self.tool_call_records: dict[str, ToolCallRecord] = {}
        self._current_parent_id: str | None = None
        self.subagent_counters: dict[str, int] = {}
        self._log_file = open(log_file_path, 'w')

    async def pre_tool_use_hook(
        self,
        hook_input: dict[str, Any],
        tool_use_id: str,
        context: Any
    ) -> dict[str, Any]:
        """工具执行前 Hook。"""
        tool_name = hook_input['tool_name']
        tool_input = hook_input['tool_input']

        # 确定所属智能体
        subagent_type = "LEAD"
        if self._current_parent_id and self._current_parent_id in self.sessions:
            subagent_type = self.sessions[self._current_parent_id].subagent_id

        # 创建记录
        record = ToolCallRecord(
            timestamp=datetime.now().isoformat(),
            tool_name=tool_name,
            tool_input=tool_input,
            tool_use_id=tool_use_id,
            subagent_type=subagent_type,
            parent_tool_use_id=self._current_parent_id
        )
        self.tool_call_records[tool_use_id] = record

        return {'continue_': True}
```

---

## 6. 工具分配

### 6.1 内置工具

| 工具 | 用途 | 典型使用场景 |
|------|------|--------------|
| `Task` | 派发子智能体 | 主智能体编排 |
| `WebSearch` | 网络搜索 | 信息收集 |
| `Read` | 读取文件 | 加载数据 |
| `Write` | 写入文件 | 保存结果 |
| `Glob` | 文件模式匹配 | 发现文件 |
| `Grep` | 内容搜索 | 查找信息 |
| `Bash` | 执行命令 | 运行脚本 |
| `Edit` | 编辑文件 | 修改内容 |
| `Skill` | 调用技能 | 复杂操作 |

### 6.2 按角色分配工具

```python
TOOL_ASSIGNMENTS = {
    "lead":       ["Task"],                              # 仅编排
    "researcher": ["WebSearch", "Write"],                # 搜索和保存
    "analyst":    ["Glob", "Read", "Bash", "Write"],     # 分析和执行
    "reporter":   ["Glob", "Read", "Write", "Skill"],    # 生成报告
}
```

### 6.3 最小权限原则

```python
# 错误：工具过多
bad_agent = AgentDefinitionConfig(
    tools=["WebSearch", "Read", "Write", "Bash", "Edit", "Glob", "Grep"],
    ...
)

# 正确：精确控制
good_agent = AgentDefinitionConfig(
    tools=["WebSearch", "Write"],  # 只需要的工具
    ...
)
```

---

## 7. 提示词工程

### 7.1 提示词结构模板

```text
# 角色定义
你是 [角色名称]，负责 [核心职责]。

# 能力边界
- 你可以：[具体能力列表]
- 你不可以：[限制列表]

# 工作流程
1. [步骤 1]
2. [步骤 2]
3. [步骤 3]

# 输出规范
- 格式：[期望格式]
- 位置：[输出路径]
- 命名：[命名约定]

# 质量标准
- [标准 1]
- [标准 2]

# 示例
[具体示例]
```

### 7.2 研究员提示词示例

```text
# 角色定义
你是专业研究员，负责通过网络搜索收集定量数据和关键信息。

# 核心任务
1. 执行 5-10 次有针对性的搜索
2. 优先收集定量数据（市场规模、增长率、排名）
3. 将研究发现保存为 Markdown 文件

# 搜索策略
- 使用具体、有针对性的查询
- 寻找权威来源（行业报告、官方数据）
- 收集多个数据点进行交叉验证

# 输出规范
- 路径：files/research_notes/{topic_name}.md
- 格式：带结构化标题的 Markdown
- 内容：10-15+ 条具体统计数据

# 数据优先级
1. 市场规模和份额
2. 增长率和预测
3. 主要参与者排名
4. 技术参数对比
5. 投资和融资数据
```

### 7.3 提示词加载

```python
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "prompts"

def load_prompt(filename: str) -> str:
    """从提示词目录加载提示词。"""
    prompt_path = PROMPTS_DIR / filename
    if not prompt_path.exists():
        raise FileNotFoundError(f"未找到提示词文件：{prompt_path}")
    return prompt_path.read_text(encoding="utf-8").strip()
```

### 7.4 业务模板系统

框架提供了**分层提示词系统**，将架构层提示词与业务相关提示词分离：

```
┌─────────────────────────────────────────────────────────┐
│  应用层 (examples/production/)                          │
│  - 选择业务模板或完全自定义                              │
│  - 最终决定业务提示词                                   │
└─────────────────────────────────────────────────────────┘
                          ↓ 选择/覆盖
┌─────────────────────────────────────────────────────────┐
│  业务模板层 (business_templates/)                       │
│  - 独立于架构                                           │
│  - 按业务类型组织                                       │
│  - 预置常用场景模板                                     │
└─────────────────────────────────────────────────────────┘
                          ↓ 组合
┌─────────────────────────────────────────────────────────┐
│  架构层 (architectures/)                                │
│  - 核心 agent 角色、能力、约束                          │
│  - 不包含业务逻辑                                       │
└─────────────────────────────────────────────────────────┘
```

**最终提示词 = 核心提示词 + 业务提示词**

#### 可用业务模板

| 模板 | 适用架构 | 用途 |
|------|----------|------|
| `competitive_intelligence` | research | 竞品分析 |
| `market_research` | research | 市场研究 |
| `pr_code_review` | pipeline | PR 代码审查 |
| `marketing_content` | critic_actor | 营销内容 |
| `it_support` | specialist_pool | IT 支持 |
| `tech_decision` | debate | 技术决策 |
| `code_debugger` | reflexion | 代码调试 |
| `codebase_analysis` | mapreduce | 代码库分析 |

#### 使用业务模板

```python
from claude_agent_framework import create_session

# 方式 1：使用预置业务模板
session = create_session(
    "research",
    business_template="competitive_intelligence"
)

# 方式 2：使用模板 + 模板变量替换
session = create_session(
    "research",
    business_template="competitive_intelligence",
    template_vars={
        "company_name": "特斯拉",
        "industry": "电动汽车"
    }
)

# 方式 3：覆盖特定 agent 提示词
session = create_session(
    "research",
    business_template="competitive_intelligence",
    prompt_overrides={
        "researcher": "专注于电动汽车电池技术..."
    }
)

# 方式 4：完全自定义提示词目录
session = create_session(
    "research",
    prompts_dir="./my_custom_prompts"
)
```

#### YAML 配置

```yaml
# config.yaml
architecture: research
business_template: competitive_intelligence

prompts:
  template_vars:
    company_name: "特斯拉"
    industry: "电动汽车"
  agents:
    researcher:
      business_prompt: |
        专注于电池技术和电动汽车市场份额。
```

#### 模板变量

业务模板提示词可以包含 `${variable}` 占位符：

```text
# 业务背景：竞品分析

你正在为 ${company_name} 在 ${industry} 行业进行竞品分析。

# 研究重点
...
```

#### 提示词优先级解析

组合最终提示词时，系统按以下优先级顺序处理：

1. `prompt_overrides["agent_name"]` - 代码参数覆盖（最高优先级）
2. YAML `config.prompts.agents.xxx.business_prompt` - YAML 内联
3. `custom_prompts_dir/<agent>.txt` - 应用自定义目录
4. `business_templates/<template>/<agent>.txt` - 业务模板
5. 空（仅使用架构核心提示词）- 默认

### 7.5 角色类型系统

框架支持**角色类型架构**，将抽象的角色定义与具体的智能体实例分离，实现灵活的多业务配置。

#### 核心概念

| 概念 | 描述 |
|------|------|
| **RoleType** | 语义角色类型枚举（WORKER、PROCESSOR、SYNTHESIZER 等） |
| **RoleCardinality** | 数量约束（EXACTLY_ONE、ONE_OR_MORE、ZERO_OR_MORE、ZERO_OR_ONE） |
| **RoleDefinition** | 架构级角色规范，包含工具和约束定义 |
| **AgentInstanceConfig** | 业务级具体智能体配置 |
| **RoleRegistry** | 验证智能体实例是否满足角色约束 |

#### 角色类型

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

#### 智能体实例配置

```python
from claude_agent_framework import create_session
from claude_agent_framework.core.roles import AgentInstanceConfig

# 为特定业务需求定义智能体实例
agents = [
    AgentInstanceConfig(
        name="market-researcher",
        role="worker",
        description="市场数据收集专员",
        prompt_file="prompts/market_researcher.txt",
    ),
    AgentInstanceConfig(
        name="tech-researcher",
        role="worker",
        description="技术趋势分析师",
        prompt_file="prompts/tech_researcher.txt",
    ),
    AgentInstanceConfig(
        name="data-analyst",
        role="processor",
        model="sonnet",
        description="数据分析专家",
    ),
    AgentInstanceConfig(
        name="report-writer",
        role="synthesizer",
        description="报告生成专员",
    ),
]

# 使用角色配置创建会话
session = create_session(
    "research",
    agent_instances=agents,
    business_template="competitive_intelligence",
)
```

#### 架构角色映射

每个架构定义了特定的角色及其数量约束：

| 架构 | 角色定义 | 模式 |
|------|---------|------|
| **research** | worker (1+), processor (0-1), synthesizer (1) | 主从协调 |
| **pipeline** | stage_executor (1+) | 顺序阶段 |
| **critic_actor** | actor (1), critic (1) | 生成-评估 |
| **specialist_pool** | specialist (1+) | 专家路由 |
| **debate** | advocate (2+), judge (1) | 辩论协商 |
| **reflexion** | executor (1), reflector (1) | 执行-反思 |
| **mapreduce** | mapper (1+), reducer (1) | 并行映射-归约 |

#### 角色架构下的提示词优先级

使用角色类型架构时，提示词组合按以下优先级：

1. **AgentInstanceConfig.prompt** - 直接指定的提示词内容（最高）
2. **prompt_overrides[agent_name]** - 会话级覆盖
3. **custom_prompts_dir/<agent_name>.txt** - 自定义提示词目录
4. **business_templates/<template>/<agent_name>.txt** - 业务模板
5. **RoleDefinition.prompt_file** - 角色基础提示词（最低）

详细文档请参阅 [角色类型系统指南](ROLE_BASED_ARCHITECTURE_CN.md)。

---

## 8. 状态管理

### 8.1 会话状态

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class AgentSession:
    """智能体会话状态。"""
    session_id: str
    started_at: str
    user_query: str
    subagents_spawned: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    current_phase: str = "init"  # init, researching, analyzing, reporting, done
    errors: List[str] = field(default_factory=list)
```

### 8.2 阶段追踪

```python
class PhaseTracker:
    """工作流阶段追踪器。"""

    PHASES = ["init", "researching", "analyzing", "reporting", "done"]

    def __init__(self):
        self.current_phase = "init"
        self.phase_history = []

    def advance_phase(self, new_phase: str):
        """推进到新阶段。"""
        if new_phase not in self.PHASES:
            raise ValueError(f"未知阶段：{new_phase}")

        self.phase_history.append({
            "from": self.current_phase,
            "to": new_phase,
            "timestamp": datetime.now().isoformat()
        })
        self.current_phase = new_phase

    def is_complete(self) -> bool:
        return self.current_phase == "done"
```

---

## 9. 错误处理

### 9.1 优雅降级

```python
async def post_tool_use_hook(self, hook_input, tool_use_id, context):
    """错误处理示例。"""
    tool_response = hook_input.get('tool_response')

    # 检测错误
    error = None
    if isinstance(tool_response, dict):
        error = tool_response.get('error')

    if error:
        # 记录错误但不中断执行
        logger.warning(f"工具错误：{error}")
        self.errors.append({
            "tool_use_id": tool_use_id,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })

    # 继续执行
    return {'continue_': True}
```

### 9.2 资源清理

```python
async def main():
    tracker = None
    transcript = None

    try:
        # 初始化资源
        transcript = TranscriptWriter(log_path)
        tracker = SubagentTracker(tool_log_path)

        # 执行主逻辑
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt=user_input)
            async for msg in client.receive_response():
                process_message(msg, tracker, transcript)

    except Exception as e:
        logger.error(f"会话失败：{e}")
        raise

    finally:
        # 确保资源清理
        if transcript:
            transcript.close()
        if tracker:
            tracker.close()
```

### 9.3 错误分类

```python
class AgentError(Exception):
    """基础智能体错误。"""
    pass

class ConfigurationError(AgentError):
    """配置错误。"""
    pass

class ToolExecutionError(AgentError):
    """工具执行错误。"""
    def __init__(self, tool_name: str, message: str):
        self.tool_name = tool_name
        super().__init__(f"工具 '{tool_name}' 失败：{message}")

class SubagentError(AgentError):
    """子智能体错误。"""
    def __init__(self, subagent_id: str, message: str):
        self.subagent_id = subagent_id
        super().__init__(f"子智能体 '{subagent_id}' 失败：{message}")
```

---

## 10. 日志与审计

### 10.1 双格式日志

```python
class TranscriptWriter:
    """双格式日志写入器。"""

    def __init__(self, file_path: Path):
        self.file = open(file_path, 'w', encoding='utf-8')

    def write(self, text: str, end: str = ""):
        """同时输出到控制台和文件。"""
        print(text, end=end, flush=True)
        self.file.write(text + end)
        self.file.flush()

    def write_to_file_only(self, text: str):
        """仅写入文件（详细日志）。"""
        self.file.write(text)
        self.file.flush()

    def close(self):
        self.file.close()
```

### 10.2 JSONL 结构化日志

```python
import json
from datetime import datetime

class ToolCallLogger:
    """工具调用 JSONL 日志器。"""

    def __init__(self, file_path: Path):
        self.file = open(file_path, 'w')

    def log_tool_start(self, agent_id: str, tool_name: str,
                       tool_input: dict, tool_use_id: str):
        entry = {
            "event": "tool_call_start",
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "tool_name": tool_name,
            "tool_use_id": tool_use_id,
            "input_summary": self._summarize_input(tool_input)
        }
        self._write(entry)

    def log_tool_complete(self, tool_use_id: str, success: bool,
                         output_size: int = 0, error: str = None):
        entry = {
            "event": "tool_call_complete",
            "timestamp": datetime.now().isoformat(),
            "tool_use_id": tool_use_id,
            "success": success,
            "output_size": output_size,
            "error": error
        }
        self._write(entry)

    def _write(self, entry: dict):
        self.file.write(json.dumps(entry, ensure_ascii=False) + '\n')
        self.file.flush()

    def close(self):
        self.file.close()
```

### 10.3 会话目录管理

```python
from pathlib import Path
from datetime import datetime

def setup_session() -> tuple[Path, Path, Path]:
    """创建会话目录和日志文件。"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = Path("logs") / f"session_{timestamp}"
    session_dir.mkdir(parents=True, exist_ok=True)

    transcript_file = session_dir / "transcript.txt"
    tool_log_file = session_dir / "tool_calls.jsonl"

    return session_dir, transcript_file, tool_log_file
```

---

## 11. 配置管理

### 11.1 架构配置

```python
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class ResearchConfig:
    """Research 架构配置。"""

    # 模型配置
    lead_model: str = "haiku"
    researcher_model: str = "haiku"
    analyst_model: str = "haiku"
    reporter_model: str = "haiku"

    # 研究深度
    research_depth: str = "standard"  # shallow, standard, deep
    max_researchers: int = 4

    # 输出目录
    research_notes_dir: str = "research_notes"
    data_dir: str = "data"
    charts_dir: str = "charts"
    reports_dir: str = "reports"

    def get_model_overrides(self) -> dict[str, str]:
        """获取智能体模型覆盖。"""
        return {
            "researcher": self.researcher_model,
            "data-analyst": self.analyst_model,
            "report-writer": self.reporter_model,
        }
```

### 11.2 环境配置

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API 配置
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # 模型配置
    LEAD_MODEL = os.getenv("LEAD_MODEL", "haiku")
    SUBAGENT_MODEL = os.getenv("SUBAGENT_MODEL", "haiku")

    # 路径配置
    PROJECT_ROOT = Path(__file__).parent.parent
    FILES_DIR = PROJECT_ROOT / "files"
    LOGS_DIR = PROJECT_ROOT / "logs"
    PROMPTS_DIR = PROJECT_ROOT / "prompts"

    # 功能开关
    ENABLE_LOGGING = os.getenv("ENABLE_LOGGING", "true").lower() == "true"
    BYPASS_PERMISSIONS = os.getenv("BYPASS_PERMISSIONS", "true").lower() == "true"

    @classmethod
    def validate(cls):
        """验证必需配置。"""
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError("需要设置 ANTHROPIC_API_KEY 环境变量")
```

---

## 12. 完整示例

### 12.1 基础用法

```python
from claude_agent_framework import init
import asyncio

async def research_example():
    """基础研究示例。"""
    session = init("research")

    async for msg in session.run("分析 2024 年 AI 市场趋势"):
        print(msg)

asyncio.run(research_example())
```

### 12.2 自定义架构

```python
from claude_agent_framework import register_architecture, BaseArchitecture, init
from claude_agent_framework.core.base import AgentDefinitionConfig

@register_architecture("qa_expert")
class QAExpertArchitecture(BaseArchitecture):
    """自定义问答专家架构。"""

    name = "qa_expert"
    description = "带领域专家路由的问答系统"

    def get_agents(self) -> dict[str, AgentDefinitionConfig]:
        return {
            "code_expert": AgentDefinitionConfig(
                name="code_expert",
                description="编程和软件开发专家",
                tools=["Read", "Write", "Glob", "Grep"],
                prompt_file="code_expert.txt",
            ),
            "data_expert": AgentDefinitionConfig(
                name="data_expert",
                description="数据分析和统计专家",
                tools=["Read", "Write", "Bash"],
                prompt_file="data_expert.txt",
            ),
        }

    async def execute(self, prompt, tracker=None, transcript=None):
        """执行问答工作流。"""
        # 构建 SDK 配置
        options = ClaudeAgentOptions(
            permission_mode="bypassPermissions",
            setting_sources=["project"],
            system_prompt=self.get_lead_prompt(),
            allowed_tools=["Task"],
            agents=self.to_sdk_agents(),
            hooks=self._build_hooks(tracker),
            model=self.model_config.default,
        )

        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt=prompt)

            async for msg in client.receive_response():
                yield msg

# 使用自定义架构
async def main():
    session = init("qa_expert")
    async for msg in session.run("如何优化数据库查询？"):
        print(msg)
```

### 12.3 编程控制

```python
from claude_agent_framework import init
from pathlib import Path

async def programmatic_example():
    """完全编程控制。"""

    # 使用自定义选项初始化
    session = init(
        "research",
        model="sonnet",
        verbose=True,
        log_dir=Path("./custom_logs"),
    )

    # 访问内部组件
    print(f"架构：{session.architecture.name}")
    print(f"会话目录：{session.session_dir}")

    # 运行查询
    query = "分析云计算市场趋势"

    try:
        async for msg in session.run(query):
            print(msg)
    finally:
        await session.teardown()
        print(f"会话已保存到：{session.session_dir}")
```

---

## 13. 生产级示例深度分析

框架包含 7 个生产就绪示例（`examples/production/`），展示了每种架构模式的真实业务应用。本节提供这些实现模式、设计决策和扩展策略的深度技术分析。

### 13.1 示例概览

| 示例 | 架构 | 业务领域 | 关键技术模式 |
|------|------|---------|-------------|
| **01_competitive_intelligence** | Research | 市场研究 | 并行调度、SWOT 综合、多渠道数据聚合 |
| **02_pr_code_review** | Pipeline | 软件工程 | 顺序门控、可配置阈值、结构化报告 |
| **03_marketing_content** | Critic-Actor | 内容营销 | 加权评分、迭代优化、A/B 变体生成 |
| **04_it_support** | Specialist Pool | IT 运维 | 关键词路由、紧急程度分类、专家编排 |
| **05_tech_decision** | Debate | 技术战略 | 多轮辩论、加权标准、结构化裁决 |
| **06_code_debugger** | Reflexion | 软件调试 | 策略库、基于反思的适应、根因分析 |
| **07_codebase_analysis** | MapReduce | 代码质量 | 智能分块、并行分析、问题聚合 |

### 13.2 竞争情报系统（Research 模式）

**业务背景**：SaaS 公司的自动化竞争情报收集

#### 架构应用

```
主协调器
    ├─→ [研究员 1: AWS]     ─┐
    ├─→ [研究员 2: Azure]    ├─→ 数据分析师 → SWOT 生成器
    └─→ [研究员 3: GCP]     ─┘                      ↓
                                                   报告撰写者
                                                         ↓
                                              竞争分析报告.pdf
```

**并行调度策略**：
```python
# config.yaml
analysis_dimensions:
  - features        # 产品能力
  - pricing         # 定价模式
  - market          # 市场地位
  - technology      # 技术栈

competitors:
  - AWS
  - Azure
  - Google Cloud

max_parallel_researchers: 3  # 同时启动 3 个研究员
```

#### 关键实现模式

**1. 配置驱动的研究范围**：
```python
@dataclass
class CompetitorAnalysisConfig:
    competitors: list[str]
    dimensions: list[str]
    data_sources: list[str] = field(default_factory=lambda: [
        "official_website",
        "tech_blogs",
        "review_sites",
        "social_media"
    ])
    output_format: str = "pdf"  # pdf, markdown, html

    def validate(self):
        """确保配置有效。"""
        if len(self.competitors) < 2:
            raise ValueError("至少需要 2 个竞争对手进行分析")
        if not self.dimensions:
            raise ValueError("必须指定分析维度")
```

**2. 结构化 SWOT 分析**：
```python
# 分析师生成结构化 JSON 格式的 SWOT
swot_schema = {
    "strengths": [
        {"category": "features", "items": [...], "evidence": [...]},
        {"category": "pricing", "items": [...], "evidence": [...]}
    ],
    "weaknesses": [...],
    "opportunities": [...],
    "threats": [...]
}
```

**3. 多渠道数据聚合**：
```python
# 研究员提示词结构
"""
对于每个竞争对手，从以下渠道收集数据：
1. 官方网站 → 功能列表、定价
2. G2/Capterra 评价 → 用户情感、评分
3. 技术博客 → 架构洞察
4. LinkedIn/Twitter → 公司动态

保存到：files/research_notes/{竞争对手名称}_{维度}.md
"""
```

#### 错误处理策略

```python
# 优雅降级
async def execute(self, prompt, tracker=None, transcript=None):
    researchers = await self._dispatch_researchers(competitors)

    # 等待所有，但不会因部分超时失败
    results = await asyncio.gather(*researchers, return_exceptions=True)

    successful = [r for r in results if not isinstance(r, Exception)]
    if len(successful) < 2:
        # 要求至少 2 个成功才能进行有意义的分析
        raise InsufficientDataError("至少需要 2 个竞争对手数据集")

    # 使用可用数据继续
    await self._dispatch_analyst(successful)
```

#### 测试方法

```python
# tests/test_competitive_intelligence.py

@pytest.mark.integration
async def test_full_workflow():
    """端到端工作流测试。"""
    session = init("research", config="examples/production/01_competitive_intelligence/config.yaml")

    query = "分析 AWS vs Azure vs GCP 对企业客户的优势"
    results = await session.query(query)

    # 验证输出
    assert (Path("files/reports") / "competitive_analysis.pdf").exists()
    assert len(list(Path("files/research_notes").glob("*.md"))) >= 6  # 3 个竞争对手 × 2 个来源

@pytest.mark.unit
def test_swot_generation():
    """测试 SWOT 合成逻辑。"""
    from examples.production.01_competitive_intelligence.utils import generate_swot

    research_data = {...}
    swot = generate_swot(research_data)

    assert all(k in swot for k in ["strengths", "weaknesses", "opportunities", "threats"])
    assert len(swot["strengths"]) > 0
```

#### 扩展点

1. **自定义数据源**：通过 `data_sources` 配置添加爬虫
2. **分析维度**：为特定行业扩展 `dimensions`
3. **输出格式**：实现自定义报告器（如 PowerPoint、Notion）
4. **自动调度**：添加基于 cron 的定期分析

---

### 13.3 PR 代码审查流水线（Pipeline 模式）

**业务背景**：Pull Request 的自动化多阶段代码审查

#### 架构应用

```
阶段 1：架构审查 → 阶段 2：代码质量 → 阶段 3：安全扫描 →
    阶段 4：性能测试 → 阶段 5：测试覆盖率
```

**顺序门控**：
```yaml
# config.yaml
stages:
  - name: architecture_review
    threshold: 7.0
    failure_strategy: stop    # 分数 < 7.0 时停止流水线

  - name: code_quality
    threshold: 6.0
    failure_strategy: warn    # 警告但继续

  - name: security_scan
    threshold: 8.0
    failure_strategy: stop    # 硬性要求

  - name: performance_test
    threshold: 5.0
    failure_strategy: continue  # 仅供参考

  - name: test_coverage
    threshold: 70.0  # 最低 70% 覆盖率
    failure_strategy: stop
```

#### 关键实现模式

**1. 可配置失败策略的质量阈值**：
```python
@dataclass
class PipelineStage:
    name: str
    threshold: float
    failure_strategy: Literal["stop", "warn", "continue"]

    def evaluate(self, score: float) -> StageResult:
        passed = score >= self.threshold

        if not passed:
            if self.failure_strategy == "stop":
                raise PipelineStopped(f"{self.name} 失败：{score} < {self.threshold}")
            elif self.failure_strategy == "warn":
                logger.warning(f"{self.name} 低于阈值：{score} < {self.threshold}")

        return StageResult(
            stage=self.name,
            score=score,
            passed=passed,
            action="continue" if passed or self.failure_strategy != "stop" else "stop"
        )
```

**2. 结构化审查报告**：
```python
# 输出：files/review_report.json
{
    "pr_id": "PR-123",
    "overall_status": "PASSED_WITH_WARNINGS",
    "stages": [
        {
            "stage": "architecture_review",
            "score": 8.5,
            "passed": true,
            "findings": [
                {"severity": "info", "message": "良好的关注点分离"}
            ]
        },
        {
            "stage": "code_quality",
            "score": 5.5,
            "passed": false,
            "findings": [
                {"severity": "warning", "message": "PaymentProcessor.process() 复杂度过高"}
            ],
            "action_taken": "warn"
        },
        // ...
    ],
    "recommendations": [...]
}
```

**3. 阶段特定的工具分配**：
```python
STAGE_TOOLS = {
    "architecture_review": ["Read", "Glob", "Write"],          # 读代码、写报告
    "code_quality": ["Read", "Bash", "Write"],                 # 运行 linter
    "security_scan": ["Read", "Bash", "Grep", "Write"],        # 运行 bandit/semgrep
    "performance_test": ["Bash", "Read", "Write"],             # 运行基准测试
    "test_coverage": ["Bash", "Read", "Write"],                # 运行 pytest --cov
}
```

#### 错误处理策略

```python
async def execute_pipeline(self, stages: list[PipelineStage]):
    results = []

    for stage in stages:
        try:
            result = await self._run_stage(stage)
            results.append(result)

            # 检查是否应该停止
            if not result.passed and stage.failure_strategy == "stop":
                logger.error(f"流水线在 {stage.name} 停止")
                return PipelineReport(status="FAILED", stages=results)

        except ToolExecutionError as e:
            # 工具失败（如 linter 崩溃）
            if stage.failure_strategy == "stop":
                raise
            else:
                logger.warning(f"阶段 {stage.name} 工具错误：{e}")
                results.append(StageResult(stage=stage.name, error=str(e)))

    return PipelineReport(status="PASSED", stages=results)
```

#### 测试方法

```python
@pytest.fixture
def sample_pr():
    """创建带已知问题的测试 PR。"""
    return {
        "files": ["auth.py", "payment.py"],
        "known_issues": {
            "code_quality": ["high_complexity"],
            "security": ["sql_injection_risk"]
        }
    }

@pytest.mark.integration
async def test_pipeline_stops_on_security_failure(sample_pr):
    """测试安全失败会停止流水线。"""
    config = load_config("examples/production/02_pr_code_review/config.yaml")
    session = init("pipeline", config=config)

    result = await session.query(f"审查 PR：{sample_pr}")

    # 应该在安全阶段停止
    assert result.status == "FAILED"
    assert result.stopped_at == "security_scan"
    assert len(result.stages) <= 3  # 没有到达阶段 4-5
```

#### 扩展点

1. **自定义 Linter**：通过 `stage_tools` 配置添加新工具
2. **动态阈值**：根据 PR 大小/重要性调整
3. **集成钩子**：基于结果触发 CI/CD 操作
4. **自定义阶段**：添加特定领域的审查阶段

---

### 13.4 营销内容优化器（Critic-Actor 模式）

**业务背景**：AI 辅助的内容创作与迭代质量改进

#### 架构应用

```
┌─────────────────────────────────────────┐
│  while quality < threshold:             │
│    Content = Actor.generate()           │
│    Scores = Critic.evaluate(content)    │
│    if scores.overall >= threshold:      │
│        break                             │
│    Content = Actor.improve(feedback)    │
└─────────────────────────────────────────┘
```

**多维加权评分**：
```yaml
# config.yaml
evaluation_criteria:
  seo_optimization:
    weight: 0.25
    metrics:
      - keyword_density
      - meta_description
      - heading_structure

  engagement:
    weight: 0.30
    metrics:
      - hook_strength
      - readability_score
      - cta_clarity

  brand_consistency:
    weight: 0.25
    metrics:
      - tone_match
      - terminology_usage
      - style_guide_compliance

  accuracy:
    weight: 0.20
    metrics:
      - fact_verification
      - claim_support
      - source_credibility

quality_threshold: 8.0
max_iterations: 5
```

#### 关键实现模式

**1. 加权多维评估**：
```python
@dataclass
class ContentScores:
    seo_optimization: float
    engagement: float
    brand_consistency: float
    accuracy: float
    weights: dict[str, float] = field(default_factory=lambda: {
        "seo_optimization": 0.25,
        "engagement": 0.30,
        "brand_consistency": 0.25,
        "accuracy": 0.20
    })

    @property
    def overall_score(self) -> float:
        return (
            self.seo_optimization * self.weights["seo_optimization"] +
            self.engagement * self.weights["engagement"] +
            self.brand_consistency * self.weights["brand_consistency"] +
            self.accuracy * self.weights["accuracy"]
        )

    def get_improvement_priorities(self) -> list[str]:
        """返回按改进需求排序的维度。"""
        scores = {
            "seo_optimization": self.seo_optimization,
            "engagement": self.engagement,
            "brand_consistency": self.brand_consistency,
            "accuracy": self.accuracy
        }
        # 权重影响 = 低分 × 维度权重
        impact = {k: (10 - v) * self.weights[k] for k, v in scores.items()}
        return sorted(impact.keys(), key=lambda k: impact[k], reverse=True)
```

**2. 结构化反馈循环**：
```python
# Critic 输出格式
{
    "iteration": 3,
    "scores": {
        "seo_optimization": 7.5,
        "engagement": 8.2,
        "brand_consistency": 6.8,
        "accuracy": 9.0,
        "overall": 7.9
    },
    "feedback": {
        "seo_optimization": "关键词使用良好，但元描述过长（170 字符，最大 155）",
        "brand_consistency": "语气过于正式。按品牌指南使用更口语化的语言。",
        "engagement": "强有力的开场！CTA 可以更具体。"
    },
    "improvement_priorities": ["brand_consistency", "seo_optimization"],
    "continue_iteration": true  # overall < threshold (8.0)
}
```

**3. A/B 变体生成**：
```python
# 达到阈值后，生成变体
async def generate_variants(self, final_content: str, n_variants: int = 3):
    """生成成功内容的 A/B 测试变体。"""
    variants = []

    for i in range(n_variants):
        variant_prompt = f"""
        生成此内容的变体 {i+1}，使用不同的：
        - 标题方法（问题 vs 陈述 vs 收益驱动）
        - 内容结构（故事 vs 数据 vs 问题-解决方案）
        - CTA 风格（紧迫性 vs 价值 vs 好奇心）

        保持相同的核心信息和质量水平。
        """
        variant = await self.actor.generate(variant_prompt, base_content=final_content)
        variants.append(variant)

    return variants
```

#### 错误处理策略

```python
async def execute(self, prompt, tracker=None, transcript=None):
    iteration = 0
    max_iterations = self.config.max_iterations

    while iteration < max_iterations:
        # 生成内容
        try:
            content = await self.actor.generate(prompt)
        except ContentGenerationError as e:
            logger.error(f"Actor 在迭代 {iteration} 失败：{e}")
            if iteration == 0:
                raise  # 没有初始内容无法继续
            else:
                # 使用上次成功的迭代
                logger.warning("使用上一次迭代的内容")
                break

        # 评估
        scores = await self.critic.evaluate(content)

        if scores.overall_score >= self.config.quality_threshold:
            logger.info(f"在迭代 {iteration} 达到质量阈值")
            break

        # 准备改进反馈
        feedback = self._format_feedback(scores)
        prompt = self._build_improvement_prompt(content, feedback)
        iteration += 1

    if iteration == max_iterations:
        logger.warning(f"达到最大迭代次数。最终分数：{scores.overall_score}")

    return content, scores
```

#### 测试方法

```python
@pytest.mark.unit
def test_weighted_scoring():
    """测试分数计算逻辑。"""
    scores = ContentScores(
        seo_optimization=8.0,
        engagement=7.0,
        brand_consistency=9.0,
        accuracy=8.5
    )

    expected = 8.0*0.25 + 7.0*0.30 + 9.0*0.25 + 8.5*0.20
    assert abs(scores.overall_score - expected) < 0.01

    # 检查优先级逻辑
    priorities = scores.get_improvement_priorities()
    assert priorities[0] == "engagement"  # 高权重维度中最低分

@pytest.mark.integration
async def test_iterative_improvement():
    """测试质量在迭代中改进。"""
    session = init("critic_actor", config="examples/production/03_marketing_content/config.yaml")

    result = await session.query("创建关于 AI 生产力工具的博客文章")

    # 验证改进
    assert len(result.iteration_history) >= 2
    scores = [h.overall_score for h in result.iteration_history]
    assert scores[-1] >= scores[0]  # 最终分数 >= 初始分数
```

#### 扩展点

1. **自定义评估指标**：添加特定领域的评分维度
2. **品牌声音训练**：使用品牌特定示例微调
3. **多语言支持**：扩展到不同语言
4. **模板库**：为不同内容类型预构建模板

---

### 13.5 IT 支持平台（Specialist Pool 模式）

**业务背景**：IT 支持工单到领域专家的智能路由

#### 架构应用

```
用户查询 → 路由器 → 关键词匹配 → 专家选择 → 专家执行
                                              ↓
                            [网络 | 数据库 | 安全 | 云]
```

**基于关键词的路由**：
```yaml
# config.yaml
specialists:
  network_expert:
    keywords:
      - vpn
      - firewall
      - dns
      - routing
      - bandwidth
    tools: [Bash, Read, Write]

  database_expert:
    keywords:
      - sql
      - query
      - index
      - transaction
      - backup
    tools: [Bash, Read, Write, Grep]

  security_expert:
    keywords:
      - authentication
      - permission
      - vulnerability
      - encryption
      - certificate
    tools: [Bash, Read, Write, Grep]

  cloud_expert:
    keywords:
      - aws
      - azure
      - kubernetes
      - docker
      - lambda
    tools: [Bash, Read, Write, WebSearch]

routing_strategy: multi_match  # single_best, multi_match, cascade
```

#### 关键实现模式

**1. 多维路由算法**：
```python
@dataclass
class RoutingDecision:
    primary_expert: str
    secondary_experts: list[str]
    confidence: float
    keyword_matches: dict[str, list[str]]

class ExpertRouter:
    def route(self, query: str) -> RoutingDecision:
        """将查询路由到合适的专家。"""
        # 提取关键词
        query_keywords = self._extract_keywords(query.lower())

        # 为每个专家评分
        scores = {}
        matches = {}

        for expert, config in self.specialists.items():
            matched_keywords = [kw for kw in config.keywords if kw in query_keywords]
            scores[expert] = len(matched_keywords)
            matches[expert] = matched_keywords

        # 按分数排序
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        if ranked[0][1] == 0:
            # 无关键词匹配，使用后备
            return RoutingDecision(
                primary_expert="general_support",
                secondary_experts=[],
                confidence=0.3,
                keyword_matches={}
            )

        # 检查多专家场景
        primary = ranked[0][0]
        secondary = [expert for expert, score in ranked[1:3] if score > 0]

        return RoutingDecision(
            primary_expert=primary,
            secondary_experts=secondary if len(secondary) > 0 else [],
            confidence=min(ranked[0][1] / 5.0, 1.0),  # 归一化到 [0,1]
            keyword_matches=matches
        )
```

**2. 带 SLA 的紧急程度分类**：
```python
@dataclass
class SupportTicket:
    query: str
    urgency: Literal["critical", "high", "medium", "low"]
    sla_hours: int  # 响应时间 SLA

    @classmethod
    def categorize(cls, query: str) -> "SupportTicket":
        """自动分类工单紧急程度。"""
        urgency_keywords = {
            "critical": ["宕机", "故障", "紧急", "生产"],
            "high": ["错误", "失败", "损坏", "不工作"],
            "medium": ["缓慢", "问题", "帮助"],
            "low": ["问题", "如何", "文档", "功能请求"]
        }

        query_lower = query.lower()
        for level, keywords in urgency_keywords.items():
            if any(kw in query_lower for kw in keywords):
                urgency = level
                break
        else:
            urgency = "low"

        sla_map = {"critical": 1, "high": 4, "medium": 24, "low": 72}

        return cls(
            query=query,
            urgency=urgency,
            sla_hours=sla_map[urgency]
        )
```

**3. 并行多专家咨询**：
```python
async def handle_multi_expert_query(self, ticket: SupportTicket, routing: RoutingDecision):
    """处理需要多个专家的查询。"""
    # 并行调度主要和次要专家
    tasks = [
        self._consult_expert(routing.primary_expert, ticket, role="primary")
    ]

    for expert in routing.secondary_experts:
        tasks.append(self._consult_expert(expert, ticket, role="secondary"))

    results = await asyncio.gather(*tasks)

    # 综合响应
    primary_response = results[0]
    secondary_responses = results[1:]

    return self._synthesize_response(primary_response, secondary_responses, routing)
```

#### 错误处理策略

```python
async def execute(self, prompt, tracker=None, transcript=None):
    # 分类工单
    ticket = SupportTicket.categorize(prompt)

    # 路由到专家
    routing = self.router.route(ticket.query)

    if routing.confidence < 0.5:
        logger.warning(f"路由置信度低：{routing.confidence}")
        # 升级到人工或通用支持
        return await self._escalate_to_human(ticket, routing)

    try:
        if routing.secondary_experts:
            response = await self.handle_multi_expert_query(ticket, routing)
        else:
            response = await self._consult_expert(routing.primary_expert, ticket)
    except ExpertNotAvailableError as e:
        # 后备到次优专家
        logger.warning(f"主要专家不可用：{e}")
        fallback = routing.secondary_experts[0] if routing.secondary_experts else "general_support"
        response = await self._consult_expert(fallback, ticket)

    return response
```

#### 测试方法

```python
@pytest.mark.unit
def test_routing_logic():
    """测试专家路由算法。"""
    router = ExpertRouter(load_config())

    # 测试单专家路由
    decision = router.route("VPN 连接不断断开")
    assert decision.primary_expert == "network_expert"
    assert "vpn" in decision.keyword_matches["network_expert"]

    # 测试多专家路由
    decision = router.route("Kubernetes Pod 中的数据库查询超时")
    assert decision.primary_expert == "database_expert"
    assert "cloud_expert" in decision.secondary_experts

@pytest.mark.unit
def test_urgency_categorization():
    """测试 SLA 分配。"""
    ticket1 = SupportTicket.categorize("生产数据库宕机！")
    assert ticket1.urgency == "critical"
    assert ticket1.sla_hours == 1

    ticket2 = SupportTicket.categorize("如何重置密码？")
    assert ticket2.urgency == "low"
    assert ticket2.sla_hours == 72
```

#### 扩展点

1. **机器学习路由**：用 ML 分类器替换关键词匹配
2. **专家负载均衡**：根据专家可用性分配工单
3. **升级路径**：定义多级升级工作流
4. **知识库集成**：在专家路由前自动建议知识库文章

---

### 13.6 技术决策支持（Debate 模式）

**业务背景**：技术架构选择的结构化决策制定

#### 架构应用

```
议题 → 正方（支持论据）↔ 反方（反对论据）[3 轮]
           ↓                             ↓
        第 1 轮：开场陈述
        第 2 轮：深度分析与反驳
        第 3 轮：最终论点
           ↓
        裁判 → 加权评估 → 裁决 + 建议
```

**多轮辩论结构**：
```yaml
# config.yaml
debate_config:
  rounds: 3
  round_structure:
    - name: opening
      time_limit_tokens: 1000
      focus: "提出主要论点"

    - name: analysis
      time_limit_tokens: 1500
      focus: "深入权衡分析，反驳对手"

    - name: closing
      time_limit_tokens: 800
      focus: "总结最强论点"

  evaluation_criteria:
    technical_feasibility:
      weight: 0.30
      description: "能否用现有资源实现？"

    cost_efficiency:
      weight: 0.25
      description: "包括开发和运营的总拥有成本"

    scalability:
      weight: 0.20
      description: "处理增长的能力"

    team_expertise:
      weight: 0.15
      description: "团队对技术的熟悉程度"

    ecosystem_maturity:
      weight: 0.10
      description: "工具、社区支持、稳定性"
```

#### 关键实现模式

**1. 结构化辩论回合**：
```python
@dataclass
class DebateRound:
    round_number: int
    round_type: str  # opening, analysis, closing
    proponent_argument: str
    opponent_argument: str

    def serialize(self) -> dict:
        return {
            "round": self.round_number,
            "type": self.round_type,
            "pro": self.proponent_argument,
            "con": self.opponent_argument
        }

async def conduct_debate(self, topic: str) -> DebateTranscript:
    rounds = []
    context = {"topic": topic, "history": []}

    for i, round_config in enumerate(self.config.round_structure, 1):
        # 正方发言
        pro_prompt = self._build_round_prompt("proponent", round_config, context)
        pro_argument = await self.proponent.generate(pro_prompt)

        # 反方响应（看到正方论点）
        context["last_pro_argument"] = pro_argument
        con_prompt = self._build_round_prompt("opponent", round_config, context)
        con_argument = await self.opponent.generate(con_prompt)

        # 记录回合
        round_data = DebateRound(i, round_config.name, pro_argument, con_argument)
        rounds.append(round_data)
        context["history"].append(round_data.serialize())

    return DebateTranscript(topic=topic, rounds=rounds)
```

**2. 加权多标准评估**：
```python
@dataclass
class CriterionScore:
    criterion: str
    pro_score: float  # 0-10
    con_score: float  # 0-10
    weight: float
    justification: str

    @property
    def weighted_delta(self) -> float:
        """正值倾向正方，负值倾向反方。"""
        return (self.pro_score - self.con_score) * self.weight

class DebateJudge:
    def evaluate(self, transcript: DebateTranscript) -> Verdict:
        """跨所有标准评估辩论。"""
        scores = []

        for criterion, config in self.evaluation_criteria.items():
            # 裁判在此标准上为双方评分
            score = self._score_criterion(
                criterion=criterion,
                pro_arguments=[r.proponent_argument for r in transcript.rounds],
                con_arguments=[r.opponent_argument for r in transcript.rounds],
                weight=config.weight
            )
            scores.append(score)

        # 计算最终裁决
        total_weighted_delta = sum(s.weighted_delta for s in scores)

        return Verdict(
            winner="proponent" if total_weighted_delta > 0 else "opponent",
            confidence=abs(total_weighted_delta) / sum(c.weight for c in self.evaluation_criteria.values()),
            criterion_scores=scores,
            summary=self._generate_summary(scores),
            recommendation=self._generate_recommendation(scores, total_weighted_delta)
        )
```

**3. 结构化决策输出**：
```json
// files/decision_report.json
{
  "decision_topic": "新电商平台：微服务 vs 单体架构",
  "debate_transcript": {
    "rounds": [
      {
        "round": 1,
        "type": "opening",
        "proponent": "微服务提供...",
        "opponent": "单体架构提供..."
      },
      // ...
    ]
  },
  "evaluation": {
    "criteria_scores": [
      {
        "criterion": "technical_feasibility",
        "pro_score": 7.0,
        "con_score": 8.5,
        "weight": 0.30,
        "weighted_delta": -0.45,
        "justification": "团队对单体架构更有经验"
      },
      // ...
    ],
    "overall_winner": "opponent",
    "confidence": 0.72,
    "summary": "虽然微服务提供更好的可扩展性...",
    "recommendation": "从模块化单体开始，第二年计划微服务迁移"
  }
}
```

#### 错误处理策略

```python
async def conduct_debate(self, topic: str) -> DebateTranscript:
    rounds = []

    for i, round_config in enumerate(self.config.round_structure, 1):
        try:
            # 执行回合
            round_data = await self._execute_round(i, round_config, rounds)
            rounds.append(round_data)
        except ArgumentGenerationError as e:
            if i == 1:
                # 没有开场回合无法继续
                raise DebateFailedError(f"开场回合失败：{e}")
            else:
                # 使用部分辩论继续
                logger.warning(f"第 {i} 轮失败，用 {len(rounds)} 轮进行裁决")
                break

    if len(rounds) < 1:
        raise InsufficientDebateError("裁决至少需要 1 个完整回合")

    return DebateTranscript(topic=topic, rounds=rounds)
```

#### 测试方法

```python
@pytest.mark.integration
async def test_full_debate():
    """测试完整辩论工作流。"""
    session = init("debate", config="examples/production/05_tech_decision/config.yaml")

    result = await session.query("我们的 API 应该采用 GraphQL 还是 REST？")

    # 验证结构
    assert len(result.rounds) == 3
    assert all(r.proponent_argument and r.opponent_argument for r in result.rounds)

    # 验证评估
    assert result.verdict.winner in ["proponent", "opponent"]
    assert 0 <= result.verdict.confidence <= 1
    assert len(result.verdict.criterion_scores) == 5

@pytest.mark.unit
def test_weighted_scoring():
    """测试多标准评分逻辑。"""
    scores = [
        CriterionScore("tech", 8.0, 6.0, 0.30, "..."),  # +0.6
        CriterionScore("cost", 5.0, 7.0, 0.25, "..."),  # -0.5
        CriterionScore("scale", 9.0, 7.0, 0.20, "..."), # +0.4
    ]

    total = sum(s.weighted_delta for s in scores)
    assert total == 0.5  # 正方获胜
```

#### 扩展点

1. **多选项辩论**：扩展到 3+ 个备选方案
2. **领域专家裁判**：为不同标准设置专业裁判
3. **历史决策跟踪**：从过去决策中学习
4. **交互模式**：允许回合间人工干预

---

### 13.7 代码调试器（Reflexion 模式）

**业务背景**：复杂软件问题的 AI 驱动自适应调试

#### 架构应用

```
┌─────────────────────────────────────────┐
│  while not solved and attempts < max:  │
│    Result = Executor.debug(strategy)   │
│    Analysis = Reflector.analyze(result)│
│    if Analysis.success: break          │
│    strategy = Adapter.improve(analysis)│
└─────────────────────────────────────────┘
```

**策略库**：
```yaml
# config.yaml
debugging_strategies:
  - id: log_analysis
    name: "日志文件分析"
    steps:
      - "读取错误日志"
      - "识别错误模式"
      - "追踪堆栈跟踪"
    success_indicators:
      - "在日志中找到根本原因"

  - id: code_inspection
    name: "代码检查"
    steps:
      - "读取相关源文件"
      - "检查最近更改（git diff）"
      - "查找常见反模式"
    success_indicators:
      - "识别问题代码"

  - id: runtime_debugging
    name: "运行时调试"
    steps:
      - "添加调试打印语句"
      - "使用测试输入运行"
      - "分析执行流程"
    success_indicators:
      - "精确定位失败位置"

  - id: dependency_check
    name: "依赖分析"
    steps:
      - "检查库版本"
      - "审查最近更新"
      - "使用不同版本测试"
    success_indicators:
      - "找到版本冲突"

max_debug_attempts: 5
reflection_depth: detailed  # quick, standard, detailed
```

#### 关键实现模式

**1. 自适应策略选择**：
```python
@dataclass
class DebugAttempt:
    attempt_number: int
    strategy_used: str
    actions_taken: list[str]
    findings: str
    success: bool
    confidence: float
    time_taken: float

class ReflexiveDebugger:
    def __init__(self, strategies: list[DebugStrategy]):
        self.strategies = strategies
        self.attempt_history: list[DebugAttempt] = []

    async def debug(self, issue_description: str) -> DebugResult:
        """反思式调试循环。"""
        strategy_queue = self.strategies.copy()

        for attempt in range(self.max_attempts):
            # 选择策略
            if attempt == 0:
                strategy = strategy_queue[0]  # 从第一个开始
            else:
                # 反思之前的尝试
                reflection = await self._reflect_on_attempts()
                strategy = self._select_next_strategy(reflection, strategy_queue)

            # 执行策略
            result = await self._execute_strategy(strategy, issue_description)

            # 记录尝试
            attempt_data = DebugAttempt(
                attempt_number=attempt + 1,
                strategy_used=strategy.id,
                actions_taken=result.actions,
                findings=result.findings,
                success=result.success,
                confidence=result.confidence,
                time_taken=result.duration
            )
            self.attempt_history.append(attempt_data)

            if result.success:
                logger.info(f"在尝试 {attempt + 1} 使用 {strategy.name} 解决")
                break

            # 从队列中移除失败的策略
            strategy_queue = [s for s in strategy_queue if s.id != strategy.id]
            if not strategy_queue:
                logger.error("所有策略已耗尽")
                break

        return self._generate_debug_report()
```

**2. 结构化反思**：
```python
@dataclass
class ReflectionAnalysis:
    """调试尝试分析。"""
    patterns_observed: list[str]
    effective_actions: list[str]
    ineffective_actions: list[str]
    suggested_next_strategy: str
    confidence_trend: str  # improving, declining, stable
    hypothesis: str  # 关于根本原因的当前理论

async def _reflect_on_attempts(self) -> ReflectionAnalysis:
    """分析调试历史以指导下一步。"""
    reflection_prompt = f"""
    分析这些调试尝试：

    {self._format_attempt_history()}

    问题：
    1. 从发现中出现了什么模式？
    2. 哪些操作产生了有用的信息？
    3. 哪些操作是死胡同？
    4. 基于到目前为止的证据，最可能的根本原因是什么？
    5. 我们接下来应该尝试什么调试策略？
    """

    analysis = await self.reflector.analyze(reflection_prompt)
    return ReflectionAnalysis.parse(analysis)
```

**3. 成功模式学习**：
```python
class StrategyLearner:
    """从成功的调试模式中学习。"""

    def __init__(self):
        self.success_patterns: dict[str, list[DebugAttempt]] = {}

    def record_success(self, issue_type: str, attempt: DebugAttempt):
        """记录成功的调试方法。"""
        if issue_type not in self.success_patterns:
            self.success_patterns[issue_type] = []
        self.success_patterns[issue_type].append(attempt)

    def suggest_strategy(self, issue_type: str) -> str | None:
        """基于过去成功建议策略。"""
        if issue_type in self.success_patterns:
            # 找到此问题类型最成功的策略
            successes = self.success_patterns[issue_type]
            strategy_counts = {}
            for attempt in successes:
                strategy_counts[attempt.strategy_used] = strategy_counts.get(attempt.strategy_used, 0) + 1

            # 返回最常成功的
            return max(strategy_counts.items(), key=lambda x: x[1])[0]
        return None
```

#### 错误处理策略

```python
async def debug(self, issue_description: str) -> DebugResult:
    try:
        # 执行反思循环
        for attempt in range(self.max_attempts):
            try:
                result = await self._execute_strategy(strategy, issue_description)
                self.attempt_history.append(result)

                if result.success:
                    return DebugResult(status="SOLVED", attempts=self.attempt_history)

            except StrategyExecutionError as e:
                # 策略执行失败
                logger.warning(f"策略 {strategy.id} 失败：{e}")
                self.attempt_history.append(DebugAttempt(
                    strategy_used=strategy.id,
                    success=False,
                    error=str(e)
                ))
                continue  # 尝试下一个策略

        # 所有尝试已耗尽
        return DebugResult(
            status="UNSOLVED",
            attempts=self.attempt_history,
            recommendation="考虑人工干预或额外上下文"
        )

    except Exception as e:
        logger.error(f"调试会话失败：{e}")
        return DebugResult(status="FAILED", error=str(e))
```

#### 测试方法

```python
@pytest.mark.integration
async def test_reflexive_improvement():
    """测试调试器基于反思调整策略。"""
    session = init("reflexion", config="examples/production/06_code_debugger/config.yaml")

    # 需要策略适应的问题
    result = await session.query("应用启动时崩溃，无日志")

    # 验证反思行为
    assert len(result.attempts) > 1  # 尝试了多个策略

    # 检查基于反思改变了策略
    strategies_used = [a.strategy_used for a in result.attempts]
    assert len(set(strategies_used)) > 1  # 使用了不同策略

    # 验证学习
    assert result.reflection_analyses  # 执行了反思
    assert any("hypothesis" in r.dict() for r in result.reflection_analyses)

@pytest.mark.unit
def test_strategy_learning():
    """测试从成功模式中学习。"""
    learner = StrategyLearner()

    # 记录成功
    learner.record_success("null_pointer", DebugAttempt(strategy_used="code_inspection", success=True))
    learner.record_success("null_pointer", DebugAttempt(strategy_used="code_inspection", success=True))
    learner.record_success("null_pointer", DebugAttempt(strategy_used="runtime_debugging", success=True))

    # 应该建议最成功的
    suggestion = learner.suggest_strategy("null_pointer")
    assert suggestion == "code_inspection"
```

#### 扩展点

1. **自定义调试工具**：添加特定领域的调试策略
2. **问题分类**：自动分类问题以更好地选择策略
3. **协作调试**：多智能体在复杂问题上协作
4. **知识库集成**：从过去的调试会话中学习

---

### 13.8 代码库分析（MapReduce 模式）

**业务背景**：大规模技术债务和代码质量分析

#### 架构应用

```
代码库（500+ 文件）
    ↓
智能分块器（by_module, by_file_type, by_size, by_git_history）
    ↓
[映射器 1：模块 A] [映射器 2：模块 B] ... [映射器 N：模块 N]
    ↓                      ↓                          ↓
  问题 JSON            问题 JSON                  问题 JSON
                           ↓
                    归约器（聚合 + 去重 + 优先级）
                           ↓
              综合分析报告
```

**智能分块策略**：
```yaml
# config.yaml
chunking_strategy: by_module  # by_module, by_file_type, by_size, by_git_history

strategies:
  by_module:
    description: "按 Python 模块/包分组文件"
    max_files_per_chunk: 50
    preserve_structure: true

  by_file_type:
    description: "按文件扩展名分组"
    groups:
      python: ["*.py"]
      config: ["*.yaml", "*.json", "*.toml"]
      docs: ["*.md", "*.rst"]

  by_size:
    description: "平衡块大小"
    target_chunk_size_kb: 500

  by_git_history:
    description: "将频繁更改的文件分组在一起"
    use_git_blame: true
    activity_threshold: 10  # 最近 90 天的提交次数

analysis_tools:
  - pylint          # 代码质量
  - bandit          # 安全
  - radon           # 复杂度指标
  - mypy            # 类型检查

max_parallel_mappers: 10
output_format: json
```

#### 关键实现模式

**1. 智能分块**：
```python
from abc import ABC, abstractmethod
from pathlib import Path

class ChunkingStrategy(ABC):
    @abstractmethod
    def chunk(self, files: list[Path]) -> list[list[Path]]:
        """将文件分割成块以进行并行处理。"""
        pass

class ModuleChunker(ChunkingStrategy):
    def __init__(self, max_files_per_chunk: int = 50):
        self.max_files_per_chunk = max_files_per_chunk

    def chunk(self, files: list[Path]) -> list[list[Path]]:
        """按 Python 模块分组文件。"""
        # 按顶级模块分组
        modules: dict[str, list[Path]] = {}

        for file in files:
            if file.suffix == ".py":
                # 提取模块：src/foo/bar.py → foo
                parts = file.parts
                src_index = parts.index("src") if "src" in parts else 0
                module = parts[src_index + 1] if len(parts) > src_index + 1 else "root"

                if module not in modules:
                    modules[module] = []
                modules[module].append(file)

        # 分割大模块
        chunks = []
        for module_files in modules.values():
            for i in range(0, len(module_files), self.max_files_per_chunk):
                chunks.append(module_files[i:i+self.max_files_per_chunk])

        return chunks

class SizeBalancedChunker(ChunkingStrategy):
    def __init__(self, target_chunk_size_kb: int = 500):
        self.target_size_bytes = target_chunk_size_kb * 1024

    def chunk(self, files: list[Path]) -> list[list[Path]]:
        """创建大小平衡的块。"""
        chunks = []
        current_chunk = []
        current_size = 0

        for file in sorted(files, key=lambda f: f.stat().st_size):
            file_size = file.stat().st_size

            if current_size + file_size > self.target_size_bytes and current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_size = 0

            current_chunk.append(file)
            current_size += file_size

        if current_chunk:
            chunks.append(current_chunk)

        return chunks
```

**2. 带进度跟踪的并行 Map**：
```python
@dataclass
class MapProgress:
    total_chunks: int
    completed_chunks: int = 0
    failed_chunks: int = 0
    current_mappers: list[str] = field(default_factory=list)

    @property
    def progress_pct(self) -> float:
        return (self.completed_chunks / self.total_chunks) * 100 if self.total_chunks > 0 else 0

async def parallel_map(self, chunks: list[list[Path]]) -> list[AnalysisResult]:
    """带进度跟踪的并行执行映射器。"""
    progress = MapProgress(total_chunks=len(chunks))

    # 创建信号量限制并行度
    semaphore = asyncio.Semaphore(self.max_parallel_mappers)

    async def map_with_progress(chunk_id: int, chunk: list[Path]):
        async with semaphore:
            mapper_id = f"mapper-{chunk_id}"
            progress.current_mappers.append(mapper_id)

            try:
                result = await self._run_mapper(chunk_id, chunk)
                progress.completed_chunks += 1
                logger.info(f"进度：{progress.progress_pct:.1f}% ({progress.completed_chunks}/{progress.total_chunks})")
                return result

            except Exception as e:
                progress.failed_chunks += 1
                logger.error(f"映射器 {chunk_id} 失败：{e}")
                return AnalysisResult(chunk_id=chunk_id, error=str(e))

            finally:
                progress.current_mappers.remove(mapper_id)

    # 执行所有映射器
    tasks = [map_with_progress(i, chunk) for i, chunk in enumerate(chunks)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    return [r for r in results if isinstance(r, AnalysisResult)]
```

**3. 带去重的智能归约**：
```python
@dataclass
class CodeIssue:
    type: str  # security, quality, complexity, typing
    severity: str  # critical, high, medium, low
    file_path: str
    line_number: int
    message: str
    tool_source: str  # pylint, bandit, radon, mypy

    def fingerprint(self) -> str:
        """生成用于去重的指纹。"""
        return hashlib.md5(
            f"{self.file_path}:{self.line_number}:{self.type}:{self.message}".encode()
        ).hexdigest()

class IntelligentReducer:
    def reduce(self, mapper_results: list[AnalysisResult]) -> AnalysisReport:
        """聚合、去重和优先级排序问题。"""
        all_issues: dict[str, CodeIssue] = {}  # 指纹 → 问题

        # 收集和去重
        for result in mapper_results:
            for issue in result.issues:
                fingerprint = issue.fingerprint()
                if fingerprint not in all_issues:
                    all_issues[fingerprint] = issue

        issues = list(all_issues.values())

        # 优先级排序
        priority_scores = {
            "critical": 100,
            "high": 50,
            "medium": 20,
            "low": 5
        }

        issues.sort(
            key=lambda i: (priority_scores.get(i.severity, 0), i.file_path),
            reverse=True
        )

        # 分类
        by_type = self._group_by(issues, key=lambda i: i.type)
        by_severity = self._group_by(issues, key=lambda i: i.severity)
        by_file = self._group_by(issues, key=lambda i: i.file_path)

        # 生成统计
        stats = AnalysisStatistics(
            total_files_analyzed=sum(len(r.files_analyzed) for r in mapper_results),
            total_issues=len(issues),
            by_severity={k: len(v) for k, v in by_severity.items()},
            by_type={k: len(v) for k, v in by_type.items()},
            top_problematic_files=self._get_top_problematic(by_file, n=10)
        )

        return AnalysisReport(
            timestamp=datetime.now(),
            issues=issues,
            statistics=stats,
            recommendations=self._generate_recommendations(issues, stats)
        )
```

**4. 结构化输出报告**：
```json
// files/analysis_report.json
{
  "timestamp": "2024-12-25T10:30:00Z",
  "summary": {
    "total_files_analyzed": 523,
    "total_issues": 1247,
    "by_severity": {
      "critical": 12,
      "high": 87,
      "medium": 456,
      "low": 692
    },
    "by_type": {
      "security": 34,
      "quality": 567,
      "complexity": 234,
      "typing": 412
    }
  },
  "top_issues": [
    {
      "severity": "critical",
      "type": "security",
      "file": "src/auth/login.py",
      "line": 45,
      "message": "SQL 注入漏洞",
      "tool": "bandit"
    },
    // ...
  ],
  "top_problematic_files": [
    {
      "file": "src/core/processor.py",
      "issue_count": 47,
      "highest_severity": "high"
    },
    // ...
  ],
  "recommendations": [
    "立即处理 12 个关键安全问题",
    "重构 src/core/processor.py（47 个问题）",
    "为缺少注释的 89 个函数添加类型提示"
  ]
}
```

#### 错误处理策略

```python
async def execute(self, prompt, tracker=None, transcript=None):
    # 发现文件
    try:
        files = await self._discover_codebase_files()
        if not files:
            raise EmptyCodebaseError("未找到要分析的文件")
    except Exception as e:
        raise CodebaseDiscoveryError(f"发现文件失败：{e}")

    # 分块文件
    try:
        chunks = self.chunker.chunk(files)
        logger.info(f"将 {len(files)} 个文件分割成 {len(chunks)} 个块")
    except Exception as e:
        logger.error(f"分块失败：{e}")
        # 后备：单个块
        chunks = [files]

    # Map 阶段
    mapper_results = await self.parallel_map(chunks)

    # 检查失败
    failed = [r for r in mapper_results if r.error]
    if len(failed) > len(chunks) * 0.5:
        raise TooManyFailuresError(f"{len(failed)} 个映射器中有 {len(chunks)} 个失败")

    # 使用成功结果继续
    successful = [r for r in mapper_results if not r.error]

    # Reduce 阶段
    try:
        report = self.reducer.reduce(successful)
    except Exception as e:
        raise ReductionError(f"聚合结果失败：{e}")

    return report
```

#### 测试方法

```python
@pytest.mark.integration
async def test_end_to_end_analysis():
    """测试完整的 MapReduce 工作流。"""
    session = init("mapreduce", config="examples/production/07_codebase_analysis/config.yaml")

    result = await session.query("分析 ./test_codebase")

    # 验证报告结构
    assert result.summary.total_files_analyzed > 0
    assert result.summary.total_issues >= 0
    assert all(k in result.summary.by_severity for k in ["critical", "high", "medium", "low"])

    # 验证去重
    fingerprints = [issue.fingerprint() for issue in result.issues]
    assert len(fingerprints) == len(set(fingerprints))  # 无重复

@pytest.mark.unit
def test_chunking_strategies():
    """测试不同的分块策略。"""
    files = list(Path("test_codebase").rglob("*.py"))

    # 测试模块分块
    module_chunker = ModuleChunker(max_files_per_chunk=10)
    module_chunks = module_chunker.chunk(files)
    assert all(len(chunk) <= 10 for chunk in module_chunks)

    # 测试大小平衡分块
    size_chunker = SizeBalancedChunker(target_chunk_size_kb=100)
    size_chunks = size_chunker.chunk(files)
    # 验证大小平衡
    chunk_sizes = [sum(f.stat().st_size for f in chunk) for chunk in size_chunks]
    assert max(chunk_sizes) - min(chunk_sizes) < 200 * 1024  # 200KB 方差内
```

#### 扩展点

1. **自定义分析工具**：添加特定领域的 linter/分析器
2. **增量分析**：仅分析更改的文件（git diff 集成）
3. **趋势跟踪**：与历史报告比较，跟踪改进
4. **自动修复建议**：为常见问题生成补丁

---

### 13.9 通用生产模式

所有生产示例共享这些实现模式：

#### 配置驱动设计

```python
# 标准 config.yaml 结构
from pydantic import BaseModel, Field

class ProductionConfig(BaseModel):
    """生产示例的基础配置。"""

    # 架构特定设置
    architecture_config: dict = Field(...)

    # 模型配置
    lead_model: str = "haiku"
    subagent_model: str = "haiku"

    # 输出配置
    output_dir: str = "files"
    log_dir: str = "logs"

    # 功能标志
    enable_logging: bool = True
    enable_metrics: bool = True

    class Config:
        extra = "allow"  # 允许架构特定字段
```

#### 结构化 JSON 结果

```python
# 所有示例都输出结构化 JSON 以供程序化使用
@dataclass
class ExecutionResult:
    """标准结果格式。"""
    status: Literal["success", "partial", "failed"]
    timestamp: str
    session_id: str
    outputs: dict[str, Path]  # 输出类型 → 文件路径
    metrics: dict[str, Any]
    errors: list[str]

    def to_json(self, path: Path):
        """保存为 JSON。"""
        with open(path, 'w') as f:
            json.dump(asdict(self), f, indent=2, default=str)
```

#### 全面的错误处理

```python
# 标准错误处理模式
async def execute(self, prompt, tracker=None, transcript=None):
    try:
        # 主执行逻辑
        result = await self._execute_workflow(prompt)
        return ExecutionResult(status="success", ...)

    except ConfigurationError as e:
        logger.error(f"配置错误：{e}")
        return ExecutionResult(status="failed", errors=[str(e)])

    except ToolExecutionError as e:
        logger.error(f"工具执行失败：{e}")
        # 尝试优雅降级
        return self._handle_tool_failure(e)

    except Exception as e:
        logger.exception("意外错误")
        return ExecutionResult(status="failed", errors=[f"意外：{str(e)}"])
```

#### 双格式日志

```python
# JSONL 用于程序化分析 + 人类可读用于调试
class ProductionLogger:
    def __init__(self, session_dir: Path):
        self.jsonl_log = open(session_dir / "events.jsonl", 'w')
        self.human_log = open(session_dir / "session.log", 'w')

    def log_event(self, event_type: str, data: dict):
        # 机器可读
        entry = {"timestamp": datetime.now().isoformat(), "event": event_type, **data}
        self.jsonl_log.write(json.dumps(entry) + '\n')
        self.jsonl_log.flush()

        # 人类可读
        self.human_log.write(f"[{entry['timestamp']}] {event_type}: {data}\n")
        self.human_log.flush()
```

#### 多层测试

```python
# tests/test_example.py

# 单元测试 - 快速、隔离
@pytest.mark.unit
def test_config_validation():
    config = ExampleConfig(...)
    assert config.validate()

# 集成测试 - 测试组件交互
@pytest.mark.integration
async def test_workflow_stages():
    session = init("example")
    result = await session.execute_stage("stage1")
    assert result.success

# E2E 测试 - 完整工作流
@pytest.mark.e2e
async def test_full_example():
    session = init("example")
    result = await session.query("完整测试查询")
    assert result.status == "success"
    assert result.outputs["report"].exists()
```

---

### 13.10 扩展生产示例

#### 添加自定义业务逻辑

```python
# examples/production/XX_custom_example/custom_logic.py

from claude_agent_framework import BaseArchitecture, register_architecture

@register_architecture("custom_example")
class CustomExampleArchitecture(BaseArchitecture):
    """扩展框架模式的自定义架构。"""

    def __init__(self, config: CustomConfig):
        super().__init__()
        self.config = config

        # 添加自定义组件
        self.custom_processor = CustomProcessor(config)
        self.custom_validator = CustomValidator(config.validation_rules)

    async def execute(self, prompt, tracker=None, transcript=None):
        # 使用自定义逻辑预处理
        processed_prompt = self.custom_processor.prepare(prompt)

        # 执行基础架构工作流
        result = await super().execute(processed_prompt, tracker, transcript)

        # 使用验证后处理
        validated_result = self.custom_validator.validate(result)

        return validated_result
```

#### 组合多种模式

```python
# 组合 Research + Critic-Actor 进行综合分析

async def hybrid_workflow(query: str):
    """研究阶段后跟迭代优化。"""

    # 阶段 1：研究（并行数据收集）
    research_session = init("research")
    research_data = await research_session.query(query)

    # 阶段 2：Critic-Actor（优化分析）
    critic_session = init("critic_actor", context=research_data)
    refined_output = await critic_session.query("优化研究发现")

    return refined_output
```

---

## 总结

### 核心要点

1. **多种模式**：7 种不同的编排模式适用于不同问题领域
2. **模式选择**：根据任务特征选择（并行 vs 顺序，迭代 vs 一次性）
3. **职责分离**：主智能体编排，子智能体执行专业化任务
4. **工具约束**：最小权限原则，每个智能体精确控制工具
5. **可观测性**：Hook 机制 + JSONL 审计日志实现全链路追踪
6. **成本优化**：子智能体使用 Haiku 模型以降低成本
7. **提示词工程**：结构化模板，清晰的角色边界
8. **错误处理**：优雅降级，确保资源清理

### 模式快速参考

| 模式 | 何时使用 |
|------|----------|
| **Research** | 需要从多个来源并行收集数据 |
| **Pipeline** | 有明确交接的顺序阶段 |
| **Critic-Actor** | 通过反馈进行迭代质量改进 |
| **Specialist Pool** | 将查询路由到领域专家 |
| **Debate** | 利弊平衡分析 |
| **Reflexion** | 需要自我反思的复杂问题 |
| **MapReduce** | 大规模并行处理与聚合 |

### 适用场景

- 多步骤研究任务
- 数据收集和分析流水线
- 文档生成自动化
- 复杂工作流编排
- 决策支持系统
- 大规模内容分析

---

*文档生成日期：2024-12-25*
*基于：Claude Agent Framework v0.3.0*
