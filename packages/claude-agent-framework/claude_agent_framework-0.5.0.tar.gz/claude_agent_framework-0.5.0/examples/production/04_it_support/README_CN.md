# IT 技术支持平台示例

一个基于 Claude Agent Framework **专家池(Specialist Pool)** 架构的生产级智能IT技术支持问题路由与解决系统。

## 概述

本示例展示如何构建企业级IT技术支持平台,具备以下能力:

- 基于关键词和SLA策略自动分类问题紧急程度
- 智能路由问题到合适的专家代理(网络、数据库、安全、云计算等)
- 利用并行专家协作处理复杂的跨领域问题
- 提供带置信度和行动计划的综合解决方案
- 追踪指标包括解决时间、专家利用率和SLA合规性

## 架构: 专家池(Specialist Pool)

专家池架构非常适合需要领域专家路由的场景:

```
用户问题
    ↓
紧急程度分类 (紧急/高/中/低)
    ↓
基于关键词的路由
    ↓
┌─────────────┬─────────────┬─────────────┬─────────────┐
│  网络专家   │  数据库专家 │  安全专家   │  云计算专家 │ (并行)
│             │             │             │             │
└─────────────┴─────────────┴─────────────┴─────────────┘
    ↓
综合解决方案 + 建议
```

**关键特性**:
- 基于关键词匹配的专家路由
- 基于优先级的专家选择
- 并行专家协作
- 无匹配时回退到通用专家
- 感知SLA的紧急程度分类

## 使用场景: 企业IT技术支持

### 真实场景

**问题**: IT技术支持团队每天需要处理数百个不同类型的问题 - 从网络故障到数据库性能、安全事件到云基础设施问题。人工路由速度慢且经常将问题误路由到错误的专家。

**解决方案**: 本系统自动完成:
1. 分类紧急程度(紧急: 1小时SLA, 高: 4小时, 中: 24小时, 低: 72小时)
2. 基于问题关键词路由到1-3个相关专家
3. 收集并行的专家分析
4. 综合成带置信度的可执行解决方案

### 可用专家

| 专家 | 关键词 | 优先级 | 专业领域 |
|-----|--------|--------|----------|
| **网络专家** | network, vpn, firewall, dns, ip address, routing | 1 | 连接性、VPN、防火墙 |
| **数据库专家** | database, sql, query, table, index, deadlock | 1 | SQL、性能、数据完整性 |
| **安全专家** | security, breach, vulnerability, authentication | 1 | 安全事件、访问控制 |
| **云计算专家** | cloud, aws, kubernetes, docker, scaling | 2 | 云基础设施、容器 |
| **应用专家** | application, error, crash, bug, timeout | 2 | 应用代码、运行时问题 |
| **DevOps专家** | deployment, cicd, jenkins, pipeline, build | 3 | CI/CD、构建系统 |
| **通用IT专家** | (回退专家) | 5 | 通用技术支持 |

## 安装

```bash
# 安装 Claude Agent Framework
pip install claude-agent-framework

# 或从源码安装
cd claude-agent-framework
pip install -e .
```

## 配置

`config.yaml` 文件定义专家、路由规则和紧急程度分类:

```yaml
architecture: specialist_pool

specialists:
  - name: "network_specialist"
    description: "网络基础设施专家"
    keywords: ["network", "vpn", "firewall", "dns"]
    priority: 1  # 数值越小优先级越高

  - name: "database_specialist"
    keywords: ["database", "sql", "query"]
    priority: 1

routing:
  strategy: "keyword_match"
  min_keyword_matches: 1      # 选择专家所需的最少关键词匹配数
  allow_multiple: true         # 允许每个问题分配多个专家
  max_specialists: 3           # 最大并发专家数
  use_fallback: true           # 无匹配时使用通用专家

categorization:
  urgency_levels:
    - name: "critical"
      sla_hours: 1
      keywords: ["down", "outage", "breach", "critical"]
    - name: "high"
      sla_hours: 4
      keywords: ["urgent", "production"]
    - name: "medium"
      sla_hours: 24
      keywords: ["bug", "issue"]
    - name: "low"
      sla_hours: 72
      keywords: ["request", "question"]

models:
  lead: "sonnet"              # 主代理模型
  specialists: "haiku"         # 专家代理模型(成本效益高)
```

## 使用方法

### 基本用法

```python
import asyncio
from pathlib import Path
from main import run_it_support
from common import load_yaml_config

async def main():
    # 加载配置
    config = load_yaml_config(Path(__file__).parent / "config.yaml")

    # 定义IT问题
    issue_title = "远程用户VPN连接失败"
    issue_description = """
    多名远程员工报告无法连接公司VPN。
    错误: "连接30秒后超时"
    受影响用户: ~20人
    开始时间: 2小时前
    """

    # 运行IT技术支持解决
    result = await run_it_support(config, issue_title, issue_description)

    # 访问结果
    print(f"紧急程度: {result['metadata']['urgency']}")
    print(f"SLA: {result['metadata']['sla_hours']} 小时")
    print(f"专家: {result['routing']['specialist_names']}")
    print(f"\n综合解决方案:\n{result['consolidated_solution']}")

    # 保存结果
    from common import ResultSaver
    saver = ResultSaver(config["output"]["directory"])
    output_path = saver.save(result, format="json")
    print(f"\n已保存到: {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 命令行使用

```bash
# 使用默认配置运行
python main.py

# 指定自定义配置
python main.py --config custom_config.yaml

# 更改输出格式
python main.py --output-format markdown  # 选项: json, markdown, pdf
```

## 示例输出

### 输入

```
标题: 数据库查询运行极其缓慢
描述: 客户仪表板加载需要30+秒。
      多名用户报告超时错误。
      生产数据库受影响。
```

### 路由决策

```
紧急程度: HIGH (4小时SLA)
匹配关键词: database, queries, slow, production
选中的专家:
  - database_specialist (3个关键词匹配, 优先级1)
  - application_specialist (1个关键词匹配, 优先级2)
```

### 综合解决方案

```markdown
### database_specialist

**分析**: 由于缺少索引和低效查询导致数据库性能下降。

**根本原因**:
- customer_orders.created_at 列缺少索引
- 在1000万+行表上进行全表扫描
- 仪表板端点查询未优化

**解决步骤**:
1. 创建复合索引: `CREATE INDEX idx_orders_created_user ON customer_orders(created_at, user_id)`
2. 使用 EXPLAIN ANALYZE 优化查询
3. 实现查询结果缓存(Redis, 5分钟TTL)
4. 添加数据库查询性能监控

**预防措施**:
- 实现自动化索引推荐
- 在CI/CD中添加查询性能预算
- 在代码审查中定期进行EXPLAIN分析

**置信度**: 高

---

### 综合解决方案

**主要根本原因**: 缺少数据库索引导致全表扫描

**推荐行动计划**:
1. **立即** (< 1小时): 在customer_orders表上创建缺失索引
2. **短期** (< 4小时): 实现查询结果缓存
3. **长期** (< 1周): 添加自动化性能监控

**预期解决时间**: 2-4小时

**风险评估**: 低风险 - 索引创建是在线操作

**后续行动**:
- 监控查询性能48小时
- 审查其他慢查询以发现类似问题
- 更新数据库维护手册
```

## 定制化

### 添加自定义专家

添加到 `config.yaml`:

```yaml
specialists:
  - name: "mobile_app_specialist"
    description: "iOS和Android移动应用专家"
    keywords: ["mobile", "ios", "android", "app crash", "push notification"]
    priority: 2
    tools: ["WebSearch", "Read"]  # 可选: 自定义工具集
```

### 自定义路由逻辑

修改 `main.py`:

```python
def _route_to_specialists(title, description, specialists_config, routing_config):
    """使用机器学习评分的自定义路由"""
    # 您的自定义逻辑
    # 示例: 使用嵌入进行语义匹配
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')

    issue_embedding = model.encode(f"{title} {description}")

    specialist_scores = []
    for specialist in specialists_config:
        specialist_text = " ".join(specialist["keywords"])
        specialist_embedding = model.encode(specialist_text)
        similarity = cosine_similarity(issue_embedding, specialist_embedding)
        specialist_scores.append((specialist, similarity))

    # 返回top-k专家
    specialist_scores.sort(key=lambda x: x[1], reverse=True)
    return [s[0] for s in specialist_scores[:routing_config["max_specialists"]]]
```

### 自定义紧急程度规则

```yaml
categorization:
  urgency_levels:
    - name: "p0_incident"
      sla_hours: 0.5           # 30分钟
      keywords: ["p0", "sev0", "complete outage"]
      auto_escalate: true
      notify: ["on-call-engineer", "engineering-manager"]

    - name: "critical"
      sla_hours: 1
      keywords: ["down", "breach", "data loss"]
      auto_escalate: true
```

## 高级功能

### 1. 多专家协调

对于复杂的跨领域问题:

```python
routing_config = {
    "strategy": "keyword_match",
    "allow_multiple": True,     # 启用多专家
    "max_specialists": 5,       # 允许最多5个专家
    "require_consensus": True,  # 要求解决方案达成一致
    "consensus_threshold": 0.75 # 需要75%的一致性
}
```

### 2. 历史学习

追踪专家绩效:

```python
result = await run_it_support(config, issue_title, issue_description)

# 追踪专家有效性
specialist_metrics = {
    "specialist": "database_specialist",
    "issue_id": result["metadata"]["issue_id"],
    "confidence": "High",
    "resolution_time": result["metadata"]["actual_resolution_hours"],
    "sla_met": result["metadata"]["sla_met"]
}

# 存储以优化未来路由
tracker.record_specialist_performance(specialist_metrics)
```

### 3. 升级规则

```python
def _should_escalate(result):
    """判断问题是否需要升级"""
    if result["metadata"]["urgency"] == "critical":
        if not result["metadata"].get("sla_met", True):
            return True, "紧急问题SLA违约"

    if all(r["confidence"] == "Low" for r in result["specialist_responses"]):
        return True, "所有专家置信度都很低"

    return False, None

should_escalate, reason = _should_escalate(result)
if should_escalate:
    await escalate_to_senior_engineer(result, reason)
```

## 测试

```bash
# 运行所有测试
pytest tests/ -v

# 仅运行单元测试
pytest tests/test_main.py -v

# 运行集成测试
pytest tests/test_integration.py -v

# 运行覆盖率测试
pytest tests/ --cov=. --cov-report=html
```

## 性能特征

| 指标 | 数值 |
|-----|------|
| 平均路由时间 | < 1秒 |
| 专家咨询(并行) | 10-30秒 |
| 总解决时间 | 15-45秒 |
| 每个问题成本(Haiku专家) | $0.01-0.05 |
| 每个问题成本(Sonnet专家) | $0.10-0.30 |
| 支持的并发问题数 | 100+ |

## 最佳实践

### 1. 专家设计

- **专注的专业知识**: 每个专家应有清晰、不重叠的领域
- **关键词选择**: 每个专家使用10-20个特定关键词
- **优先级调优**: 根据专家可用性和专业深度设置优先级
- **模型选择**: 常规问题使用Haiku,复杂分析使用Sonnet

### 2. 路由优化

- **关键词覆盖**: 确保至少80%的常见问题匹配到专家
- **回退专家**: 始终有优先级为5的通用专家
- **最大专家数**: 限制为3以避免噪音并降低成本
- **最小匹配数**: 设置为1以获得广泛覆盖,2+以获得精确度

### 3. 紧急程度校准

- **关键词调优**: 审查历史问题以优化紧急程度关键词
- **SLA监控**: 追踪实际与预期解决时间
- **误报审查**: 检查错误标记为紧急的问题
- **升级路径**: 为SLA违约定义清晰的升级规则

### 4. 成本管理

```python
# 使用分层模型选择
models:
  lead: "sonnet"              # 主代理需要推理能力
  specialists: "haiku"         # 专家执行专注任务
  fallback: "haiku"           # 回退处理常规问题

# 为类似问题启用缓存
caching:
  enabled: true
  ttl_hours: 24
  similarity_threshold: 0.85   # 与之前问题85%相似时缓存命中
```

## 故障排除

### 问题: 未选择专家

**症状**: 所有问题都路由到回退专家

**解决方案**:
1. 检查关键词覆盖: `python analyze_keywords.py --issues issues.jsonl`
2. 将 `min_keyword_matches` 降低到1
3. 为专家添加更多关键词
4. 审查问题描述中的意外术语

### 问题: 选择了错误的专家

**症状**: 网络问题路由到数据库专家

**解决方案**:
1. 添加否定关键词: `exclude_keywords: ["network", "vpn"]` 到数据库专家
2. 将 `min_keyword_matches` 增加到2以提高精确度
3. 审查专家之间的关键词重叠
4. 使用优先级偏好更具体的专家

### 问题: 响应时间慢

**症状**: 每个问题 > 60秒

**解决方案**:
1. 将 `max_specialists` 减少到2
2. 为专家使用Haiku模型
3. 为常见问题实现结果缓存
4. 在配置中设置专家超时

## 许可证

MIT许可证 - 详见主仓库

## 相关示例

- [竞品情报分析](../01_competitive_intelligence/) - Research架构
- [PR代码审查](../02_pr_code_review/) - Pipeline架构
- [营销内容优化](../03_marketing_content/) - Critic-Actor架构

## 支持

问题和疑问:
- GitHub Issues: https://github.com/anthropics/claude-agent-framework/issues
- 文档: https://github.com/anthropics/claude-agent-framework/docs
