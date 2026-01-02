# 技术决策支持系统示例

一个基于 Claude Agent Framework **辩论(Debate)** 架构的生产级技术决策支持系统。为评估技术选型、架构变更、自建vs购买决策和供应商选择提供结构化讨论。

## 概述

本示例展示如何构建企业级技术决策平台,具备以下能力:

- 通过正反方进行结构化辩论
- 跨多个加权标准评估决策
- 提供基于证据的建议和全面论证
- 生成详细的分阶段实施路线图
- 识别风险和缓解策略
- 为利益相关者生成执行摘要

## 架构: 辩论(Debate)

辩论架构非常适合需要平衡评估的技术决策:

```
决策问题 + 上下文
    ↓
┌─────────────┬─────────────┬─────────────┐
│  正方        │  反方        │  主持人      │
│  (支持者)    │  (批评者)    │  (引导者)    │
└─────────────┴─────────────┴─────────────┘
    ↓
第1轮: 开场陈述 (正方 vs 反方)
    ↓
第2轮: 深度分析 (基于证据)
    ↓
第3轮: 反驳 (反驳论点)
    ↓
┌─────────────────────────┐
│  专家评审团              │
│  加权评估                │
│  最终建议                │
└─────────────────────────┘
```

**关键特性**:
- 结构化多轮讨论
- 正反方观点确保平衡分析
- 基于证据的论证和事实核查
- 加权标准评分(技术、成本、风险、业务)
- 专家评审团判断和反对意见

## 使用场景: 技术选型

### 真实场景

**问题**: 工程团队每天面临关键的技术决策 - 选择数据库、框架、云服务商、决定自建还是购买。这些决策有长期影响,但往往仓促或基于不完整分析做出。

**解决方案**: 本系统提供:
1. 结构化辩论格式确保探索所有角度
2. 跨技术、成本、风险和业务标准的加权评估
3. 基于数据和行业研究的证据论证
4. 带实施路线图和风险缓解的最终建议

### 常见决策类型

| 决策类型 | 示例 | 关键标准 |
|---------|------|---------|
| **技术选型** | React vs Vue, PostgreSQL vs MongoDB | 技术契合度、学习曲线、生态系统 |
| **架构变更** | 单体到微服务 | 可扩展性、复杂度、迁移成本 |
| **自建vs购买** | 自建认证 vs Auth0 | 开发时间、定制化、总拥有成本 |
| **供应商选择** | AWS vs Azure vs GCP | 功能、定价、锁定风险 |

## 安装

```bash
# 安装 Claude Agent Framework
pip install claude-agent-framework

# 或从源码安装
cd claude-agent-framework
pip install -e .
```

## 配置

`config.yaml` 文件定义辩论结构、参与者和评估标准:

```yaml
architecture: debate

# 辩论参与者
participants:
  proponent:
    name: "solution_advocate"
    role: "为提议的解决方案提供最有力的论证"
    focus_areas:
      - "技术优势和能力"
      - "业务对齐和投资回报率"
      - "实施可行性"

  opponent:
    name: "critical_analyst"
    role: "识别弱点并提出替代方案"
    focus_areas:
      - "技术限制和缺点"
      - "实施风险和挑战"
      - "替代方案比较"

  judge:
    name: "expert_panel"
    expertise:
      - "软件架构"
      - "技术战略"
      - "风险管理"

# 辩论结构
debate_config:
  rounds: 3
  round_structure:
    - round: 1
      name: "开场陈述"
      focus: "展示主要立场"
    - round: 2
      name: "深度分析"
      focus: "基于证据的评估"
    - round: 3
      name: "反驳"
      focus: "反驳论点和加强立场"

# 加权评估标准
evaluation_criteria:
  technical_fit:
    weight: 30
    sub_criteria:
      - "满足功能需求"
      - "可扩展性和性能"
      - "安全特性"

  implementation_feasibility:
    weight: 25
    sub_criteria:
      - "团队技能可用性"
      - "学习曲线"
      - "迁移复杂度"

  cost_efficiency:
    weight: 25
    sub_criteria:
      - "初始成本"
      - "运营成本"
      - "三年总拥有成本"

  risk_management:
    weight: 20
    sub_criteria:
      - "供应商锁定风险"
      - "支持和社区"
      - "迁移/退出策略"

# 模型配置
models:
  lead: "sonnet"       # 主持人
  proponent: "sonnet"  # 强论证能力
  opponent: "sonnet"   # 批判性分析
  judge: "opus"        # 最佳判断力
```

## 使用方法

### 基本用法

```python
import asyncio
from pathlib import Path
from main import run_tech_decision
from common import load_yaml_config

async def main():
    # 加载配置
    config = load_yaml_config(Path(__file__).parent / "config.yaml")

    # 定义决策问题
    decision_question = "我们是否应该从REST API迁移到GraphQL?"

    # 提供决策上下文
    context = {
        "options": [
            "完全迁移到GraphQL",
            "混合方式(GraphQL + REST)",
            "增强REST并改进文档",
        ],
        "requirements": [
            "减少移动应用API调用次数",
            "改善开发者体验",
            "支持实时更新",
        ],
        "constraints": {
            "budget": "$75,000",
            "timeline": "6个月",
            "team_size": "5名后端工程师",
            "tech_stack": "Node.js, PostgreSQL, React Native",
        },
        "current_situation": """
        REST API有150+个端点。移动应用每个屏幕需要20+次API调用。
        团队有REST经验但没有GraphQL知识。
        客户抱怨移动应用性能慢。
        """,
    }

    # 运行决策流程
    result = await run_tech_decision(config, decision_question, context)

    # 访问结果
    print(f"决策: {result['decision']['question']}")
    print(f"建议: {result['recommendation']['recommended_option']}")
    print(f"理由: {result['recommendation']['justification'][:200]}...")

    # 保存结果
    from common import ResultSaver
    saver = ResultSaver(config["output"]["directory"])
    output_path = saver.save(result, format="json")
    print(f"完整决策报告已保存到: {output_path}")

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
问题: 我们应该采用Kubernetes进行容器编排吗?

上下文:
- 选项: Kubernetes, Docker Swarm, AWS ECS
- 需求: 自动扩展, 高可用性, 多区域
- 约束: $100k预算, 6个月时间线
- 当前: 手动扩展的EC2实例
```

### 辩论摘录

```markdown
### 第1轮: 开场陈述

**[正方 - solution_advocate]**

Kubernetes是行业标准的容器编排平台,拥有无与伦比的生态系统支持。它提供:

- 基于CPU/内存指标或自定义指标的自动扩展
- 自动容器重启和健康检查的自愈能力
- 避免供应商锁定的多云可移植性
- 丰富的生态系统: Helm, Istio, Prometheus集成
- 80%+的财富500强公司使用Kubernetes

学习曲线的投资在运营效率和团队市场竞争力上会得到回报。

**[反方 - critical_analyst]**

虽然Kubernetes提供强大的能力,但该提议忽略了关键挑战:

- 陡峭的学习曲线: 团队熟练需要3-6个月
- 运营复杂性: 需要专门的DevOps资源
- 当前规模过度设计: 现有工作负载可在更简单的方案上运行
- 预算担忧: 培训、工具和咨询轻松超过$100k
- AWS ECS以少量复杂度提供80%的好处

"人人都在用"的论证是从众谬误。应基于实际需求选择,而非炒作。

### 第2轮: 深度分析

**[正方]**

**技术契合度 (30%): 95/100**
- 原生支持所有需求: 自动扩展(HPA)、多区域(联邦)、高可用性(副本集)
- 声明式配置和GitOps支持
- 在大规模下久经考验(Google每周运行20亿容器)

**实施可行性 (25%): 70/100**
- 托管Kubernetes(EKS, GKE, AKS)减少运营负担
- 团队可以从托管控制平面开始,逐步增加复杂度
- 强大的招聘池: K8s技能高度可用

**成本 (25%): 65/100**
- 较高的初始投资: $40k培训, $20k咨询, $15k工具
- 长期节省: 通过bin packing减少40%基础设施成本
- 3年TCO与替代方案相当

**风险 (20%): 75/100**
- 成熟技术(CNCF毕业项目)
- 多云策略消除供应商锁定
- 大型社区和企业支持选项

**[反方]**

**对评分的现实检验:**

**技术契合度**: 95分被高估。缺少背景是当前工作负载是20个实例上的10个服务。K8s是为数百个服务设计的。更合适的评分: 75。

**实施**: 70分很慷慨。托管K8s仍需深入理解pods、services、ingress、RBAC、网络策略。真正熟练: 9-12个月。评分: 50。

**成本**: 低估了运营开销。需要专职SRE($150k/年)、监控工具($10k/年)、培训进修。3年TCO实际更高。评分: 55。

**替代提案**: AWS ECS with Fargate
- 技术契合度: 85/100 - 满足所有需求,AWS原生集成
- 实施: 90/100 - 团队已熟悉Docker, 2周上手
- 成本: 80/100 - 无控制平面成本,按容器付费
- 风险: 70/100 - AWS锁定担忧,但当前架构已依赖AWS

### 评估记分卡

**技术契合度 (30%)**
- Kubernetes: 85/100 - 优秀但对当前规模过于强大
- Docker Swarm: 70/100 - 更简单但生态系统有限
- AWS ECS: 82/100 - AWS原生,满足需求

**实施可行性 (25%)**
- Kubernetes: 60/100 - 陡峭曲线,时间线激进
- Docker Swarm: 85/100 - 更易学习,更快部署
- AWS ECS: 88/100 - 最小学习量,团队有AWS经验

**成本效益 (25%)**
- Kubernetes: 65/100 - 高初始成本,长期节省
- Docker Swarm: 90/100 - 最低成本选项
- AWS ECS: 80/100 - 中等成本,无控制平面费用

**风险管理 (20%)**
- Kubernetes: 80/100 - 成熟、可移植、强大社区
- Docker Swarm: 60/100 - 社区衰退,未来不确定
- AWS ECS: 72/100 - 供应商锁定,但支持强大

**总体加权评分**
- Kubernetes: 72.5/100
- Docker Swarm: 76.3/100
- AWS ECS: 81.0/100

### 最终建议

**[评审团决策]**

**推荐选项**: AWS ECS with Fargate(过渡性), 计划在18-24个月内迁移到Kubernetes

**理由**:

加权评估(ECS: 81.0, Kubernetes: 72.5)结合上下文分析,得出分阶段方法:

**阶段1 (现在 - 18个月): 采用AWS ECS**
- 即时价值: 最小摩擦下获得容器化好处
- 团队用熟悉的AWS工具学习容器编排概念
- 满足时间线和预算约束
- 风险缓解: 维持生产稳定性

**阶段2 (18-24个月): Kubernetes迁移**
- 到那时: 团队有容器编排经验
- 到那时: 应用架构演进到需要K8s复杂度
- 到那时: 更大的团队和预算用于适当的K8s投资

**此方法的关键优势**:
1. 务实: 解决即时需求而不过度工程化
2. 教育性: 团队在生产中增量构建编排专业知识
3. 财务性: 保持在预算内,推迟主要K8s投资
4. 战略性: 在业务需要时为多云未来定位
5. 低风险: 经验证的技术和现有团队专业知识

**已确认的风险**:
1. 18个月后ECS到K8s迁移成本 - 缓解: 使用K8s兼容模式(12因子应用),容器化已是80%的工作
2. ECS阶段的AWS供应商锁定 - 缓解: 避免ECS特定功能,使用开放标准(Docker, CloudFormation → Terraform)
3. 团队可能抵制最终K8s转型 - 缓解: 从第6个月开始在专业发展计划中包含K8s学习

**实施路线图**:

阶段1 (立即 - 0-30天):
- 使用Fargate启动类型创建ECS集群
- 容器化第一个低风险服务(内部仪表板)
- 建立容器部署的CI/CD管道
- 建立监控和日志(CloudWatch + Datadog)

阶段2 (短期 - 1-3个月):
- 将5个核心服务迁移到ECS
- 实施自动扩展策略
- 建立多区域部署(us-east-1, us-west-2)
- 团队容器最佳实践培训

阶段3 (长期 - 3-18个月):
- 迁移剩余服务
- 优化容器大小和成本
- 评估服务网格(AWS App Mesh)
- 第12个月: 开始K8s评估以准备18个月转型

**成功指标**:
- 迁移期间零生产事故
- 维持99.9%正常运行时间
- 部署时间从30分钟减少到5分钟
- 通过更好的资源利用减少20%基础设施成本
- 团队满意度评分: 编排体验8/10

**反对意见**:

少数派观点主张立即采用Kubernetes,认为ECS到K8s迁移会造成重复工作。然而,考虑到团队当前的专业水平和时间线约束,失败K8s实施的风险超过效率论证。如果时间线延长到12个月,应重新审视此立场。
```

## 定制化

### 添加自定义决策模板

扩展 `config.yaml`:

```yaml
decision_templates:
  ml_framework_selection:
    description: "选择ML/AI框架"
    required_info:
      - "用例(NLP、计算机视觉等)"
      - "团队ML专业知识"
      - "部署环境"
      - "性能要求"
      - "模型复杂度"

  database_selection:
    description: "RDBMS vs NoSQL vs NewSQL"
    required_info:
      - "数据模型特征"
      - "事务要求(ACID?)"
      - "规模预测(每秒读写次数)"
      - "查询模式"
      - "一致性要求"
```

### 自定义评估标准

```yaml
evaluation_criteria:
  # 用于开源库选择
  community_health:
    weight: 15
    sub_criteria:
      - "GitHub星标和fork数"
      - "最近提交活动"
      - "问题解决时间"
      - "贡献者数量"
      - "文档质量"

  license_compliance:
    weight: 10
    sub_criteria:
      - "许可证类型(MIT, Apache, GPL)"
      - "商业使用限制"
      - "专利授权"
      - "归属要求"
```

### 高级辩论选项

```yaml
advanced:
  enable_fact_checking: true       # 用WebSearch验证声明
  require_evidence: true            # 论证必须引用来源
  allow_expert_consultation: true  # 为特定问题生成领域专家
  structured_scoring: true          # 使用详细评分规则
  generate_alternatives: true       # AI建议额外选项
  sensitivity_analysis: true        # 测试决策对假设变化的稳健性
```

## 测试

```bash
# 运行所有测试
pytest examples/production/05_tech_decision/tests/ -v

# 仅运行单元测试
pytest examples/production/05_tech_decision/tests/test_main.py -v

# 运行集成测试
pytest examples/production/05_tech_decision/tests/test_integration.py -v

# 运行覆盖率测试
pytest examples/production/05_tech_decision/tests/ --cov=. --cov-report=html
```

## 性能特征

| 指标 | 数值 |
|-----|------|
| 平均辩论时间 | 45-90秒 |
| 辩论轮数 | 2-4(可配置) |
| 每次决策成本(Sonnet辩论, Opus评审) | $0.50-1.50 |
| 每次决策成本(Haiku辩论, Sonnet评审) | $0.10-0.30 |
| 支持的决策类型 | 4个模板 + 自定义 |

## 最佳实践

### 1. 决策框架

**好的决策问题**:
> "我们是否应该将面向客户平台的单体Rails应用迁移到微服务架构?"

具体、有范围、可执行。

**不好的决策问题**:
> "我们应该使用微服务吗?"

太模糊,缺少上下文。

### 2. 上下文完整性

提供全面的上下文:
- **当前情况**: 推动此决策的问题是什么?
- **选项**: 2-4个具体替代方案(不是10个)
- **需求**: 具体、可衡量的需求
- **约束**: 预算、时间线、团队规模、现有技术栈
- **利益相关者**: 谁受此决策影响?

### 3. 标准加权

将权重与业务优先级对齐:

```yaml
# 用于早期创业公司(速度优于完美)
evaluation_criteria:
  time_to_market: {weight: 40}
  cost: {weight: 30}
  technical_fit: {weight: 20}
  risk: {weight: 10}

# 用于受监管企业(风险缓解关键)
evaluation_criteria:
  compliance_and_security: {weight: 35}
  risk_management: {weight: 30}
  technical_fit: {weight: 20}
  cost: {weight: 15}
```

### 4. 模型选择策略

```yaml
# 关注预算(最小化成本)
models:
  lead: "haiku"
  proponent: "haiku"
  opponent: "haiku"
  judge: "sonnet"

# 平衡(质量 + 成本)
models:
  lead: "sonnet"
  proponent: "sonnet"
  opponent: "sonnet"
  judge: "opus"

# 高风险决策(最高质量)
models:
  lead: "opus"
  proponent: "opus"
  opponent: "opus"
  judge: "opus"
```

### 5. 迭代优化

对于复杂决策,使用优化标准运行多次辩论:

1. **第1轮**: 使用广泛标准进行初始辩论 → 识别前2-3个选项
2. **第2轮**: 使用详细标准对决赛选项进行重点辩论 → 做出最终决策
3. **第3轮**(可选): 使用敏感性分析验证决策(改变假设)

## 故障排除

### 问题: 辩论过于肤浅

**症状**: 建议缺乏深度,理由感觉通用

**解决方案**:
1. 将辩论轮数增加到4-5轮
2. 要求证据: `require_evidence: true`
3. 启用事实核查: `enable_fact_checking: true`
4. 使用Sonnet/Opus模型而非Haiku
5. 提供更详细的上下文和具体需求

### 问题: 辩论偏向现状

**症状**: 总是推荐"保持当前解决方案"或增量变更

**解决方案**:
1. 明确要求反方"挑战现状偏见"
2. 添加评估标准: "创新和竞争优势"
3. 要求正方为最雄心勃勃的选项辩护
4. 提供显示行业方向的市场趋势数据

### 问题: 建议不明确

**症状**: 评审提出"视情况而定"或列出所有选项都可行

**解决方案**:
1. 收紧约束(预算、时间线)以强制优先排序
2. 要求单一建议(默认不是"混合")
3. 为评审使用Opus模型(更好的决策能力)
4. 增加标准中的权重差异(更清晰的优先级)

## 许可证

MIT许可证 - 详见主仓库

## 相关示例

- [竞品情报分析](../01_competitive_intelligence/) - Research架构
- [PR代码审查](../02_pr_code_review/) - Pipeline架构
- [营销内容优化](../03_marketing_content/) - Critic-Actor架构
- [IT技术支持平台](../04_it_support/) - Specialist Pool架构

## 支持

问题和疑问:
- GitHub Issues: https://github.com/anthropics/claude-agent-framework/issues
- 文档: https://github.com/anthropics/claude-agent-framework/docs
