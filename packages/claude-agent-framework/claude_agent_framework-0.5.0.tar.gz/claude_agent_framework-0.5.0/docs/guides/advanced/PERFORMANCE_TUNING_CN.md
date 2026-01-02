# 性能优化指南

**版本**: 1.0.0
**最后更新**: 2025-12-26

本指南涵盖 Claude Agent Framework 应用程序的性能优化策略,包括模型选择、并行化、缓存和成本优化。

---

## 目录

1. [性能基础](#性能基础)
2. [模型选择策略](#模型选择策略)
3. [并行化优化](#并行化优化)
4. [性能导向的提示工程](#性能导向的提示工程)
5. [缓存策略](#缓存策略)
6. [Token优化](#token优化)
7. [架构特定调优](#架构特定调优)
8. [监控与分析](#监控与分析)
9. [性能基准测试](#性能基准测试)

---

## 性能基础

### 关键性能指标

| 指标 | 定义 | 目标值 |
|--------|------------|--------|
| **延迟** | 从请求到首次响应的时间 | haiku < 5s, sonnet < 15s |
| **吞吐量** | 每分钟处理的查询数 | 取决于使用场景 |
| **Token效率** | 每消耗token产生的输出质量 | 最大化价值/成本比 |
| **单次查询成本** | 包括所有代理的总成本 | 在保持质量的同时最小化 |
| **成功率** | 成功完成的查询百分比 | > 95% |

### 性能权衡

```
质量 ←→ 速度 ←→ 成本
   ↑         ↑         ↑
  Opus    Haiku    预算
```

**关键洞察**: 为每个代理选择**满足质量要求的最低模型层级**。

---

## 模型选择策略

### 模型层级特征

| 模型 | 速度 | 成本 | 使用场景 |
|-------|-------|------|-----------|
| **Haiku** | 🚀 快速 (1-3s) | 💰 便宜 ($0.25/MTok输入, $1.25/MTok输出) | 数据收集、格式化、简单分析 |
| **Sonnet** | ⚡ 中等 (3-8s) | 💵 适中 ($3/MTok输入, $15/MTok输出) | 复杂推理、综合、编排 |
| **Opus** | 🐌 慢速 (8-20s) | 💸 昂贵 ($15/MTok输入, $75/MTok输出) | 关键决策、复杂创意工作 |

### 选择决策树

```
任务是否关键？(法律、医疗、金融)
├─ 是 → Opus
└─ 否 → 是否需要复杂推理？
    ├─ 是 → Sonnet
    └─ 否 → 是否需要基本数据处理？
        ├─ 是 → Haiku
        └─ 否 → 考虑是否需要AI
```

### 代理级模型分配

**模式**: 快速代理用于数据收集,智能代理用于综合

```python
from claude_agent_framework import init

session = init("research")

# 为特定代理覆盖默认模型
session.architecture.config.agent_configs = {
    "lead": {"model": "sonnet"},        # 复杂编排
    "researcher_1": {"model": "haiku"},  # 简单数据收集
    "researcher_2": {"model": "haiku"},  # 简单数据收集
    "synthesizer": {"model": "sonnet"},  # 复杂综合
}

result = await session.query("分析市场趋势")
```

**成本节省**: 使用 haiku 而非 sonnet 用于2个研究员:
- 之前: 2 × $3/MTok = $6/MTok
- 之后: 2 × $0.25/MTok = $0.50/MTok
- **节省**: 数据收集代理成本降低91%

---

## 并行化优化

### 理解架构中的并行性

| 架构 | 并行代理数 | 最大加速比 | 最适用于 |
|--------------|----------------|-------------|----------|
| Research | 4-8 并发 | 5-7x | 独立研究任务 |
| MapReduce | 10-50 并发 | 10-40x | 大规模数据处理 |
| Specialist Pool | 2-4 并发 | 2-3x | 多领域查询 |
| Pipeline | 顺序执行 | 1x (无并行) | 阶段依赖任务 |

### 最佳并发级别

**Research 架构**:

```python
from claude_agent_framework.architectures.research import ResearchConfig

# 默认: 4 个并行研究员
config = ResearchConfig(
    max_parallel_agents=8  # 增加以获得更多并行性
)

session = init("research", config=config)
```

**性能 vs. 并发度**:

| 并行代理数 | 延迟降低 | 成本影响 |
|----------------|-------------------|-------------|
| 2 | 快40% | 总成本相同 |
| 4 (默认) | 快60% | 总成本相同 |
| 8 | 快70% | 总成本相同 |
| 16 | 快75% | API限流风险 |

**推荐**:
- **Research/MapReduce**: 6-8 个并行代理达到最佳平衡
- **Specialist Pool**: 2-4 个专家(受领域数量限制)
- **Pipeline/Debate**: 设计上顺序执行,优化各个阶段

### 管理API速率限制

Claude API 限制 (截至2025年):
- **并发请求**: 每个API密钥20个
- **每分钟Token数**: 40万(因层级而异)

**策略**:
```python
from claude_agent_framework.plugins.builtin import ThrottlePlugin

# 限制并发API调用
throttle = ThrottlePlugin(
    max_concurrent=15,  # 留出余量
    tokens_per_minute=350000  # 保守限制
)
session.architecture.add_plugin(throttle)
```

---

## 性能导向的提示工程

### 简洁提示 = 更快响应

**不好的做法** (冗长):
```python
prompt = """
我希望您能够进行全面而深入的分析,
仔细研究人工智能市场的当前状态,确保涵盖
所有主要参与者、新兴趋势、定价模型...
(500字的指令)
"""
```

**好的做法** (简洁):
```python
prompt = """
分析AI市场:
1. 主要参与者和市场份额
2. 新兴趋势 (2024-2025)
3. 定价模型对比
4. 竞争格局
"""
```

**影响**:
- 输入token: 500 → 50 (减少90%)
- 处理时间: 8s → 3s (快62%)
- 成本: $1.50 → $0.15 (节省90%)

### 结构化输出格式

**策略**: 请求结构化格式以减少冗长

```python
# 不要使用: "写一份详细报告..."
prompt = """
以以下格式提供分析:
- 关键发现: [一句话]
- 证据: [要点列表]
- 建议: [一句话]
"""
```

**好处**:
- 更短的输出(更少token)
- 更容易解析
- 更快生成

### 避免冗余指令

**不好的做法**:
```python
# 向每个代理重复指令
for agent in agents:
    agent_prompt = f"{base_instructions}\n\n{task}\n\n{base_instructions}"
```

**好的做法**:
```python
# 指令放在主提示中,任务仅给代理
lead_prompt = f"{base_instructions}\n\n委派这些任务: {tasks}"
```

---

## 缓存策略

### 基于文件的缓存

代理通过文件通信 - 缓存可重用数据:

```python
import hashlib
import json
from pathlib import Path

class CacheManager:
    def __init__(self, cache_dir: Path = Path("cache")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)

    def get_cache_key(self, prompt: str) -> str:
        return hashlib.md5(prompt.encode()).hexdigest()

    def get(self, prompt: str):
        cache_file = self.cache_dir / f"{self.get_cache_key(prompt)}.json"
        if cache_file.exists():
            return json.loads(cache_file.read_text())
        return None

    def set(self, prompt: str, result: dict):
        cache_file = self.cache_dir / f"{self.get_cache_key(prompt)}.json"
        cache_file.write_text(json.dumps(result))

# 使用
cache = CacheManager()

prompt = "分析特斯拉股票表现"
cached = cache.get(prompt)
if cached:
    print("使用缓存结果")
    result = cached
else:
    result = await session.query(prompt)
    cache.set(prompt, result)
```

**何时使用**:
- 重复查询(日报)
- 参考数据(公司信息、定义)
- 昂贵的计算

### 基于时间的缓存失效

```python
import time

class TimedCache(CacheManager):
    def get(self, prompt: str, max_age_hours: int = 24):
        cache_file = self.cache_dir / f"{self.get_cache_key(prompt)}.json"
        if cache_file.exists():
            age = time.time() - cache_file.stat().st_mtime
            if age < max_age_hours * 3600:
                return json.loads(cache_file.read_text())
        return None

# 市场数据缓存1小时,参考数据缓存7天
market_data = cache.get("市场趋势", max_age_hours=1)
company_info = cache.get("公司简介", max_age_hours=168)
```

---

## Token优化

### 最小化工具输出冗长

**问题**: 工具结果可能非常大(WebSearch返回10k+字符)

**解决方案**: 在子代理提示中进行摘要

```python
researcher_prompt = """
搜索关于 {topic} 的信息。

重要: 写一个简洁的摘要(最多500字)。
只关注关键事实。不要包括:
- 完整文章文本
- 冗余信息
- 填充词
"""
```

**影响**:
- 默认: 10k tokens → 2k tokens (减少80%)
- 主代理综合更快
- 更低成本

### 高效的主代理提示

**策略**: 主代理不需要看到完整的子代理记录

```python
# 不好: 将完整记录传递给主代理
lead_context = f"研究员输出:\n{full_transcript}"

# 好: 仅传递摘要
lead_context = f"研究员发现:\n{extract_summary(transcript)}"
```

**框架支持**: 框架通过基于文件的通信自动处理

### Token跟踪

使用 `CostTrackerPlugin` 监控token使用:

```python
from claude_agent_framework.plugins.builtin import CostTrackerPlugin

cost_plugin = CostTrackerPlugin(
    input_price_per_mtok=3.0,
    output_price_per_mtok=15.0
)
session.architecture.add_plugin(cost_plugin)

# 执行后
summary = cost_plugin.get_cost_summary()
print(f"总token数: {summary['total_tokens']}")
print(f"总成本: ${summary['total_cost_usd']:.4f}")

# 识别昂贵的代理
for agent, cost in summary['agent_costs'].items():
    if cost > 1.0:  # 每个代理$1+
        print(f"⚠️ 昂贵的代理: {agent} - ${cost:.2f}")
```

---

## 架构特定调优

### Research 架构

**瓶颈**: 综合阶段(主代理等待所有研究员)

**优化**:
```python
# 1. 研究员使用haiku,综合使用sonnet
config = ResearchConfig(
    lead_model="sonnet",
    subagent_model="haiku"
)

# 2. 限制研究范围
prompt = """
研究 {topic}。限制为:
- 每个研究员最多3个来源
- 最多500字摘要
- 专注于 [特定方面]
"""

# 3. 增加并行度
config.max_parallel_agents = 8
```

**预期改进**:
- 延迟: -40% (并行 + 更快模型)
- 成本: -70% (数据收集使用haiku)

### Pipeline 架构

**瓶颈**: 顺序阶段,最慢阶段决定总时间

**优化**:
```python
# 1. 独立优化每个阶段
stages = {
    "design_review": {"model": "sonnet"},    # 复杂
    "syntax_check": {"model": "haiku"},      # 简单
    "security_scan": {"model": "haiku"},     # 模式匹配
    "performance_test": {"model": "haiku"},  # 数据分析
    "final_review": {"model": "sonnet"}      # 复杂
}

# 2. 减少阶段交接开销
# 保持中间输出简洁
```

**预期改进**:
- 延迟: -50% (更快的简单阶段)
- 成本: -60% (5个阶段中3个使用haiku)

### MapReduce 架构

**瓶颈**: Map阶段并行度受块数限制

**优化**:
```python
from claude_agent_framework.architectures.mapreduce import MapReduceConfig

# 1. 最佳块大小
config = MapReduceConfig(
    chunk_size=50,  # 每个mapper 50个文件
    max_parallel_mappers=10  # 10个并发mapper
)

# 2. mapper使用haiku, reducer使用sonnet
config.mapper_model = "haiku"
config.reducer_model = "sonnet"

# 3. 减少mapper输出冗长
mapper_prompt = """
分析文件并仅输出:
- 问题数量: X
- 严重性: [高/中/低]
- 受影响文件: [列表]
"""
```

**预期改进**:
- 延迟: -60% (并行 + 快速mapper)
- 成本: -80% (大部分工作使用haiku)

---

## 监控与分析

### 使用 MetricsCollectorPlugin

```python
from claude_agent_framework.plugins.builtin import MetricsCollectorPlugin

metrics = MetricsCollectorPlugin()
session.architecture.add_plugin(metrics)

result = await session.query(prompt)

# 分析性能
m = metrics.get_metrics()
print(f"总持续时间: {m.duration_ms}ms")
print(f"代理生成数: {m.agent_count}")
print(f"工具调用数: {m.tool_call_count}")

# 识别瓶颈
for agent, duration in m.agent_durations.items():
    print(f"{agent}: {duration}ms")
```

### 性能分析

跟踪时间花费位置:

```python
import time

class PerformanceProfiler:
    def __init__(self):
        self.timings = {}

    def time_section(self, name):
        return self._Timer(name, self)

    class _Timer:
        def __init__(self, name, profiler):
            self.name = name
            self.profiler = profiler

        def __enter__(self):
            self.start = time.time()

        def __exit__(self, *args):
            duration = time.time() - self.start
            self.profiler.timings[self.name] = duration

# 使用
profiler = PerformanceProfiler()

with profiler.time_section("agent_spawn"):
    # ... 生成代理 ...

with profiler.time_section("synthesis"):
    # ... 综合结果 ...

# 分析
for section, duration in sorted(profiler.timings.items(), key=lambda x: -x[1]):
    print(f"{section}: {duration:.2f}s")
```

### A/B 测试配置

比较不同配置的性能:

```python
configs = [
    {"name": "基线", "lead_model": "sonnet", "sub_model": "sonnet"},
    {"name": "优化", "lead_model": "sonnet", "sub_model": "haiku"},
    {"name": "预算", "lead_model": "haiku", "sub_model": "haiku"},
]

results = []
for config in configs:
    session = init("research", config=config)
    metrics = MetricsCollectorPlugin()
    session.architecture.add_plugin(metrics)

    start = time.time()
    result = await session.query(prompt)
    duration = time.time() - start

    results.append({
        "config": config["name"],
        "duration": duration,
        "cost": metrics.get_metrics().estimated_cost_usd,
        "quality": evaluate_quality(result)  # 自定义指标
    })

# 找到最优
best = max(results, key=lambda r: r["quality"] / r["cost"])
print(f"最佳配置: {best['config']}")
```

---

## 性能基准测试

### 基线性能 (Research 架构)

**设置**:
- 任务: "分析AI市场趋势:参与者、定价、竞争"
- 4个并行研究员
- 所有模型: Sonnet

**结果**:

| 指标 | 值 |
|--------|-------|
| 总延迟 | 45 秒 |
| 总Token数 | 15万 (7.5万输入, 7.5万输出) |
| 总成本 | $1.35 |
| 代理数 | 5 (1主 + 4研究员) |
| 工具调用 | 12 (WebSearch, Write) |

### 优化后性能

**应用的优化**:
1. 研究员使用Haiku → 仅主代理使用Sonnet
2. 简洁提示 (输入token -40%)
3. 结构化输出格式 (输出token -30%)
4. 增加并行度 (4 → 6 代理)

**结果**:

| 指标 | 值 | 改进 |
|--------|-------|-------------|
| 总延迟 | 18 秒 | **-60%** |
| 总Token数 | 6.3万 (3.5万输入, 2.8万输出) | **-58%** |
| 总成本 | $0.32 | **-76%** |
| 代理数 | 7 (1主 + 6研究员) | +2代理 |
| 工具调用 | 15 | +3调用 |

**质量评估**: 输出质量无可衡量差异

### 成本-延迟权衡矩阵

| 配置 | 延迟 | 成本 | 质量 | 使用场景 |
|---------------|---------|------|---------|----------|
| **全Opus** | 90s | $5.25 | 9.5/10 | 关键决策 |
| **全Sonnet** | 45s | $1.35 | 9.0/10 | 标准研究 |
| **混合 (Sonnet主 + Haiku子)** | 18s | $0.32 | 8.8/10 | **推荐** |
| **全Haiku** | 12s | $0.08 | 7.5/10 | 简单数据收集 |

---

## 性能检查清单

部署前验证:

### 模型选择
- [ ] 主代理使用适合编排复杂度的模型
- [ ] 子代理使用最低可行模型(尽可能使用haiku)
- [ ] 关键路径使用更高层级模型

### 并行化
- [ ] 并行架构使用6-8个并发代理
- [ ] 考虑API速率限制(每个密钥 < 15并发)
- [ ] MapReduce的工作负载适当分块

### 提示
- [ ] 提示简洁(简单任务 < 200字)
- [ ] 指定结构化输出格式
- [ ] 代理间无冗余指令

### 缓存
- [ ] 重复查询使用适当TTL缓存
- [ ] 参考数据长期缓存(天/周)
- [ ] 定义缓存失效策略

### 监控
- [ ] 启用MetricsCollectorPlugin
- [ ] 按代理跟踪token使用
- [ ] 识别并优化瓶颈

### 测试
- [ ] 对比基线进行性能基准测试
- [ ] A/B测试多个配置
- [ ] 优化后验证质量

---

## 高级技术

### 推测执行

对于延迟关键应用:

```python
# 推测性启动多个代理,使用最快的结果
async def speculative_query(prompt, count=3):
    tasks = [session.query(prompt) for _ in range(count)]
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    # 取消待处理
    for task in pending:
        task.cancel()

    return done.pop().result()

# 使用3倍资源获得2-3倍更低延迟
result = await speculative_query("需要紧急分析")
```

**权衡**: 更高成本换取更低延迟

### 自适应模型选择

根据复杂度动态选择模型:

```python
def estimate_complexity(prompt: str) -> str:
    """从提示估计任务复杂度。"""
    keywords_complex = ["分析", "综合", "评估", "比较"]
    keywords_simple = ["列出", "查找", "提取", "摘要"]

    if any(kw in prompt for kw in keywords_complex):
        return "sonnet"
    elif any(kw in prompt for kw in keywords_simple):
        return "haiku"
    return "sonnet"  # 默认

# 应用
model = estimate_complexity(user_prompt)
config = ResearchConfig(lead_model=model)
session = init("research", config=config)
```

### 流式响应

对于面向用户的应用,流式传输部分结果:

```python
async for message in session.run(prompt):
    print(message, end="", flush=True)  # 流式传输给用户
```

**好处**: 用户看到进度,降低感知延迟

---

## 进一步阅读

- [架构选择指南](../architecture_selection/GUIDE_CN.md) - 选择最佳架构
- [成本优化指南](COST_OPTIMIZATION_CN.md) - 最小化开支
- [API参考](../../api/core_cn.md) - 配置选项
- [最佳实践](../../BEST_PRACTICES_CN.md) - 通用指南

---

**有问题?** 在 [GitHub](https://github.com/anthropics/claude-agent-framework) 上提出issue。
