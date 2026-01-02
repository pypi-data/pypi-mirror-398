# 架构选择指南

**版本**: 1.0.0
**最后更新**: 2025-12-26

本指南帮助您为任务选择合适的架构模式。Claude Agent Framework 提供 7 种预构建架构，每种都针对不同的问题领域进行了优化。

---

## 快速选择流程图

```
开始：你的任务是什么？
    │
    ├─ 需要全面研究/数据收集？
    │  └─> Research（扇出/扇入）
    │
    ├─ 有顺序依赖的阶段？
    │  └─> Pipeline（顺序链）
    │
    ├─ 需要迭代质量改进？
    │  └─> Critic-Actor（生成-评估循环）
    │
    ├─ 需要领域专家路由？
    │  └─> Specialist Pool（动态路由）
    │
    ├─ 需要多视角平衡分析？
    │  └─> Debate（对抗性辩论）
    │
    ├─ 需要自适应问题解决与学习？
    │  └─> Reflexion（自我改进）
    │
    └─ 并行处理大规模数据？
       └─> MapReduce（分治）
```

---

## 架构对比矩阵

| 架构 | 并行度 | 迭代 | 最适合 | 示例用例 |
|------|--------|------|--------|----------|
| **Research** | 高 | 否 | 数据收集、分析 | 市场研究、竞品分析、文献综述 |
| **Pipeline** | 无 | 否 | 顺序工作流 | 代码审查、内容创作、多阶段处理 |
| **Critic-Actor** | 无 | 是 | 质量改进 | 内容优化、错误修复、设计改进 |
| **Specialist Pool** | 中 | 否 | 领域专业知识 | 技术支持、问答、多领域任务 |
| **Debate** | 无 | 结构化 | 决策制定 | 架构决策、风险评估、方案分析 |
| **Reflexion** | 无 | 是 | 复杂问题 | 调试、优化、自适应规划 |
| **MapReduce** | 高 | 否 | 大规模处理 | 日志分析、代码库审计、数据聚合 |

---

## 角色类型配置

每个架构支持**角色类型配置**，允许您在遵循角色约束的前提下自定义智能体实例。

### 架构角色映射

| 架构 | 角色 | 数量约束 | 描述 |
|------|------|----------|------|
| **research** | worker | 1+ | 数据收集工作者 |
| | processor | 0-1 | 可选的数据处理者 |
| | synthesizer | 1 | 结果综合者 |
| **pipeline** | stage_executor | 1+ | 顺序阶段执行者 |
| **critic_actor** | actor | 1 | 内容生成者 |
| | critic | 1 | 质量评估者 |
| **specialist_pool** | specialist | 1+ | 领域专家 |
| **debate** | advocate | 2+ | 立场倡导者 |
| | judge | 1 | 决策者 |
| **reflexion** | executor | 1 | 任务执行者 |
| | reflector | 1 | 自我反思者 |
| **mapreduce** | mapper | 1+ | 并行映射者 |
| | reducer | 1 | 结果归约者 |

### 配置示例

```python
from claude_agent_framework import create_session
from claude_agent_framework.core.roles import AgentInstanceConfig

# 使用自定义智能体的 Research 架构
agents = [
    AgentInstanceConfig(
        name="market-researcher",
        role="worker",
        description="市场数据收集",
        prompt_file="prompts/market.txt",
    ),
    AgentInstanceConfig(
        name="tech-researcher",
        role="worker",
        description="技术趋势分析",
    ),
    AgentInstanceConfig(
        name="analyst",
        role="processor",
        model="sonnet",
    ),
    AgentInstanceConfig(
        name="writer",
        role="synthesizer",
    ),
]

session = create_session("research", agent_instances=agents)
```

详细角色配置请参阅 [角色类型系统指南](../../ROLE_BASED_ARCHITECTURE_CN.md)。

---

## 详细架构概况

### 1. Research（扇出/扇入）

**模式**：主编排器生成多个并行工作者，然后聚合结果。

**适用场景**：
- ✅ 任务可以分解为独立的子任务
- ✅ 需要从多个角度全面覆盖
- ✅ 结果可以综合成统一输出
- ✅ 时间宝贵（并行执行）

**不适用场景**：
- ❌ 子任务有依赖关系
- ❌ 需要严格的操作顺序
- ❌ 解决方案是单一线性路径

**关键特性**：
- **并行度**：高（典型5-10个并发工作者）
- **协调**：主节点聚合结果
- **通信**：单向（工作者 → 主节点）
- **可扩展性**：对IO密集型任务极佳

**示例**：
```python
from claude_agent_framework import init

session = init("research")
result = await session.query(
    "分析AI智能体市场：主要参与者、趋势、"
    "定价模型和竞争格局"
)
# 生成: market_analyst, competitor_researcher,
#      pricing_analyst, trend_forecaster
```

**生产示例**：[竞品情报系统](../../examples/production/01_competitive_intelligence/)

---

### 2. Pipeline（顺序链）

**模式**：任务按顺序流经各阶段，每个阶段转换输出。

**适用场景**：
- ✅ 有清晰的顺序阶段和依赖关系
- ✅ 每个阶段需要前一阶段的输出
- ✅ 阶段间有质量门
- ✅ 需要逐阶段验证

**不适用场景**：
- ❌ 阶段是独立的
- ❌ 需要并行探索
- ❌ 需要大量迭代

**关键特性**：
- **并行度**：无（设计上顺序执行）
- **协调**：输出 → 输入链接
- **通信**：线性流
- **可扩展性**：受限于最长阶段

**示例**：
```python
session = init("pipeline")
result = await session.query(
    "审查PR #123：检查架构、代码质量、"
    "安全性和性能"
)
# 阶段: architecture_reviewer → quality_checker →
#      security_scanner → performance_analyzer
```

**生产示例**：[PR代码审查流水线](../../examples/production/02_pr_code_review/)

---

### 3. Critic-Actor（生成-评估循环）

**模式**：Actor生成输出，Critic评估并提供反馈，重复直到达到质量阈值。

**适用场景**：
- ✅ 质量比速度更重要
- ✅ 存在明确的评估标准
- ✅ 迭代改进可提升输出
- ✅ 需要达到质量阈值

**不适用场景**：
- ❌ 初稿已足够
- ❌ 没有明确的质量指标
- ❌ 时间敏感任务

**关键特性**：
- **并行度**：无（顺序迭代）
- **协调**：反馈循环
- **通信**：双向（Actor ↔ Critic）
- **可扩展性**：受限于迭代次数

**示例**：
```python
session = init("critic_actor")
result = await session.query(
    "为我们的新AI产品发布创建营销邮件。"
    "目标：企业CTO。语调：专业但创新。"
)
# 循环: Actor生成 → Critic评分（SEO、清晰度、语调）
#      → Actor改进 → 重复直到分数 ≥ 阈值
```

**生产示例**：[营销内容优化器](../../examples/production/03_marketing_content/)

---

### 4. Specialist Pool（动态路由）

**模式**：主智能体分析查询，路由到适当的专家，编排响应。

**适用场景**：
- ✅ 多领域问题空间
- ✅ 特定领域需要专家知识
- ✅ 可以预先确定查询领域
- ✅ 专家具有非重叠的专业知识

**不适用场景**：
- ❌ 单领域问题
- ❌ 所有任务需要相同专业知识
- ❌ 路由逻辑复杂

**关键特性**：
- **并行度**：中（可能并行查询专家）
- **协调**：基于关键词的路由
- **通信**：中心辐射
- **可扩展性**：良好（按需添加专家）

**示例**：
```python
session = init("specialist_pool")
result = await session.query(
    "用户报告：'升级到v2.5后无法连接数据库。"
    "错误：SSL握手失败，端口5432'"
)
# 路由到: database_expert（主要）, network_specialist（次要）
```

**生产示例**：[IT支持平台](../../examples/production/04_it_support/)

---

### 5. Debate（对抗性辩论）

**模式**：支持者和反对者从不同观点争论，评委评估并决定。

**适用场景**：
- ✅ 需要平衡分析
- ✅ 重要决策有权衡
- ✅ 需要风险评估
- ✅ 存在多个有效观点

**不适用场景**：
- ❌ 明确的决策
- ❌ 单一正确答案
- ❌ 时间关键的选择

**关键特性**：
- **并行度**：无（结构化辩论轮次）
- **协调**：多轮论证
- **通信**：支持者 ↔ 反对者 → 评委
- **可扩展性**：受限于辩论轮次

**示例**：
```python
session = init("debate")
result = await session.query(
    "我们应该从单体架构迁移到微服务吗？"
    "背景：50人团队，5年代码库，"
    "性能问题日益严重"
)
# 辩论: 支持者（收益）vs 反对者（风险）→
#      评委（建议及风险评估）
```

**生产示例**：[技术决策支持](../../examples/production/05_tech_decision/)

---

### 6. Reflexion（自我改进）

**模式**：执行策略，反思结果，调整方法，用改进的策略重试。

**适用场景**：
- ✅ 需要学习的复杂问题
- ✅ 初始方法可能失败
- ✅ 反馈提供更好的策略
- ✅ 需要自适应问题解决

**不适用场景**：
- ❌ 问题有确定性解决方案
- ❌ 无法从失败中学习
- ❌ 不能承受试错

**关键特性**：
- **并行度**：无（顺序学习）
- **协调**：反思-适应循环
- **通信**：执行者 → 反思者 → 执行者
- **可扩展性**：受限于反思深度

**示例**：
```python
session = init("reflexion")
result = await session.query(
    "调试为什么test_auth_flow间歇性失败。"
    "堆栈跟踪：[已提供]。代码库：/path/to/repo"
)
# 循环: 尝试调试策略 → 反思结果 →
#      调整策略 → 重试 → 最终找到根本原因
```

**生产示例**：[代码调试器](../../examples/production/06_code_debugger/)

---

### 7. MapReduce（分治）

**模式**：将数据分成块，并行处理（Map），聚合结果（Reduce）。

**适用场景**：
- ✅ 大数据集（数百项）
- ✅ 极易并行处理
- ✅ 结果可以聚合
- ✅ 每项处理是独立的

**不适用场景**：
- ❌ 小数据集（<50项）
- ❌ 项之间有依赖关系
- ❌ 无法有意义地聚合

**关键特性**：
- **并行度**：非常高（10-50+并行映射器）
- **协调**：分片 + 聚合
- **通信**：映射器 → 归约器
- **可扩展性**：数据处理极佳

**示例**：
```python
session = init("mapreduce")
result = await session.query(
    "分析/path/to/large-repo代码库的技术债务："
    "代码异味、安全问题、性能问题、测试覆盖率"
)
# Map: 将500个文件拆分 → 10个并行分析器
# Reduce: 聚合 + 去重 + 优先级排序问题
```

**生产示例**：[代码库分析](../../examples/production/07_codebase_analysis/)

---

## 决策框架

### 步骤1：识别任务特征

问自己：

1. **并行化潜力？**
   - 高 → Research 或 MapReduce
   - 中 → Specialist Pool
   - 无 → Pipeline、Critic-Actor、Debate、Reflexion

2. **迭代需求？**
   - 是，专注质量 → Critic-Actor
   - 是，专注学习 → Reflexion
   - 结构化（辩论）→ Debate
   - 否 → Research、Pipeline、Specialist Pool、MapReduce

3. **数据规模？**
   - 大（100s-1000s）→ MapReduce
   - 中（10s）→ Research
   - 小 → 其他任何

4. **领域专业知识？**
   - 多领域 → Specialist Pool
   - 单领域 → 其他架构

### 步骤2：匹配模式

| 任务特征 | 推荐架构 |
|---------|----------|
| 并行 + 聚合 | Research |
| 顺序 + 阶段 | Pipeline |
| 迭代 + 质量 | Critic-Actor |
| 多领域 + 路由 | Specialist Pool |
| 平衡 + 决策 | Debate |
| 迭代 + 学习 | Reflexion |
| 大规模 + 并行 | MapReduce |

### 步骤3：验证选择

检查这些标准：

- ✅ **效率**：模式是否避免不必要的工作？
- ✅ **清晰度**：工作流程是否易于理解？
- ✅ **可扩展性**：能否处理任务复杂度的增长？
- ✅ **成本**：Token使用是否合理？

---

## 常见模式组合

您可以通过将一个架构的输出作为另一个架构的输入来组合模式：

### 模式1：Research → Critic-Actor

```python
# 阶段1：收集数据
research_session = init("research")
raw_data = await research_session.query("研究主题X")

# 阶段2：精炼成精美输出
critic_session = init("critic_actor")
polished = await critic_session.query(
    f"从以下内容创建执行摘要：{raw_data}"
)
```

**用例**：市场研究 → 精美报告

### 模式2：MapReduce → Pipeline

```python
# 阶段1：分析所有文件
mapreduce_session = init("mapreduce")
issues = await mapreduce_session.query("在/repo中找到所有bug")

# 阶段2：优先级排序并创建工单
pipeline_session = init("pipeline")
tickets = await pipeline_session.query(
    f"对这些问题进行分类并创建JIRA工单：{issues}"
)
```

**用例**：代码库审计 → 问题跟踪

### 模式3：Specialist Pool → Debate

```python
# 阶段1：获取专家意见
pool_session = init("specialist_pool")
opinions = await pool_session.query("评估云提供商")

# 阶段2：辩论利弊
debate_session = init("debate")
decision = await debate_session.query(
    f"从以下选项中决定最佳方案：{opinions}"
)
```

**用例**：技术评估 → 决策制定

---

## 要避免的反模式

### ❌ 对顺序任务使用Research

**问题**：强制人为并行化，而实际不存在。

**示例**："步骤1：读取文件，步骤2：处理，步骤3：写入输出"

**解决方案**：改用Pipeline。

### ❌ 对独立任务使用Pipeline

**问题**：串行化本可并行的工作。

**示例**："分析代码质量、安全性和性能"

**解决方案**：改用Research。

### ❌ 使用Critic-Actor但没有明确标准

**问题**：如果Critic标准模糊，循环永远不会收敛。

**示例**："让这段代码更好"（没有定义"更好"）

**解决方案**：定义具体指标或使用简单Pipeline。

### ❌ 对小数据集使用MapReduce

**问题**：分片开销超过收益。

**示例**："分析10个文件"

**解决方案**：改用Research或简单Pipeline。

### ❌ 对确定性问题使用Reflexion

**问题**：在有已知解决方案的问题上浪费迭代。

**示例**："按字母顺序排序此列表"

**解决方案**：使用直接代码执行，而非智能体架构。

---

## 性能考虑

### Token使用

各架构的近似Token成本（相对规模）：

```
MapReduce（大数据）:  ████████████ (12x)
Research（10个工作者）:████████     (8x)
Reflexion（5次迭代）: ██████       (6x)
Debate（3轮）:        █████        (5x)
Critic-Actor（4次迭代）:████       (4x)
Specialist Pool:      ███          (3x)
Pipeline（4阶段）:    ███          (3x)
直接查询:             █            (1x基准)
```

### 执行时间

各架构的近似时间（对于IO密集型任务）：

```
Pipeline（顺序）:       ████████████ (最慢)
Debate（多轮）:        ██████████
Reflexion（迭代）:     ██████████
Critic-Actor（迭代）:  ████████
Specialist Pool:       ████
Research（并行）:      ███
MapReduce（并行）:     ███          (大数据最快)
```

**注意**：实际性能取决于：
- 任务复杂度
- 网络延迟
- 模型选择（haiku/sonnet/opus）
- 迭代/工作者数量

---

## 按架构的模型选择

| 架构 | 推荐主智能体模型 | 推荐子智能体模型 |
|------|------------------|------------------|
| Research | Sonnet（编排）| Haiku（数据收集）|
| Pipeline | Haiku（简单路由）| Sonnet（分析阶段）|
| Critic-Actor | Sonnet（评估）| Sonnet（生成）|
| Specialist Pool | Haiku（路由）| Sonnet（专业知识）|
| Debate | Sonnet（主持）| Sonnet（论证）|
| Reflexion | Sonnet（反思）| Sonnet（执行）|
| MapReduce | Haiku（简单归约）| Haiku（映射任务）|

**模型层级**：
- **Haiku**：快速、便宜，适合简单任务
- **Sonnet**：平衡，推荐用于大多数任务
- **Opus**：强大、昂贵，用于复杂推理

---

## 延伸阅读

- [生产示例](../../examples/production/) - 真实世界实现
- [最佳实践](../../BEST_PRACTICES_CN.md) - 深入技术模式
- [自定义架构指南](../customization/CUSTOM_ARCHITECTURE_CN.md) - 构建自己的架构
- [性能调优](../advanced/PERFORMANCE_TUNING_CN.md) - 优化技术

---

## 快速参考

```python
# 导入
from claude_agent_framework import init

# 初始化任何架构
session = init("research")         # 或 "pipeline", "critic_actor" 等

# 运行查询
result = await session.query("您的任务在这里")

# 访问结果
print(result)
```

**需要帮助选择？** 考虑：
1. 任务可以并行运行吗？ → Research/MapReduce
2. 任务必须顺序执行吗？ → Pipeline
3. 需要质量迭代吗？ → Critic-Actor/Reflexion
4. 需要领域专家吗？ → Specialist Pool
5. 需要平衡分析吗？ → Debate

---

**有疑问？** 请参阅[示例](../../examples/production/)或[最佳实践](../../BEST_PRACTICES_CN.md)。
