# 竞品情报分析系统

基于 Claude Agent Framework 的 Research 架构实现的自动化竞品情报收集与分析系统。

## 功能概述

这个示例展示了如何使用 Research 架构进行并行数据收集和综合分析，适用于：

- **SaaS 公司竞品分析** - 自动化收集和分析竞争对手的产品、定价、市场表现
- **市场调研** - 并行调研多个目标，快速获取行业洞察
- **产品规划** - 基于竞品分析做出数据驱动的产品决策

###核心功能

- ✅ **并行竞品调研** - 同时调研多个竞品（AWS、Azure、Google Cloud等）
- ✅ **多渠道数据收集** - 官网信息、市场报告、用户评论
- ✅ **多维度分析** - 功能对比、定价分析、市场占有率、技术栈等
- ✅ **结构化报告** - 生成 JSON/Markdown/PDF 格式的分析报告
- ✅ **SWOT分析** - 自动生成优势、劣势、机会、威胁分析

## 快速开始

### 1. 安装依赖

```bash
# 从项目根目录安装
cd /path/to/claude-agent-framework
pip install -e ".[all]"

# 或只安装基础依赖
pip install -e .
```

### 2. 配置 API Key

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

### 3. 配置分析参数

编辑 `config.yaml` 文件：

```yaml
competitors:
  - name: "AWS"
    website: "https://aws.amazon.com"
    focus_areas:
      - "Compute services"
      - "Storage solutions"
      - "Database offerings"

analysis_dimensions:
  - "Product Features"
  - "Pricing Model"
  - "Market Share"

output:
  directory: "outputs"
  format: "markdown"  # json, markdown, pdf
```

### 4. 运行分析

```bash
cd examples/production/01_competitive_intelligence
python main.py
```

## 输出示例

分析完成后，会生成以下输出：

```
outputs/competitive_intelligence_report_20250125_143022.md
```

**报告内容包括：**

```markdown
# Competitive Intelligence Analysis Report

## Summary
Analyzed 3 competitors across 6 dimensions

## Competitors
- AWS
- Microsoft Azure
- Google Cloud

## Analysis by Dimension

### Product Features
AWS: Leading in breadth of services...
Azure: Strong integration with Microsoft ecosystem...
Google Cloud: Advanced data analytics and ML...

### Pricing Model
AWS: Pay-as-you-go with volume discounts...
Azure: Hybrid benefit for Windows/SQL Server...
Google Cloud: Sustained use discounts...

### Market Share
AWS: 32% market leader...
Azure: 23% second position...
Google Cloud: 10% growing rapidly...

## SWOT Analysis

### AWS
**Strengths:** Market leader, extensive services
**Weaknesses:** Complex pricing, steep learning curve
**Opportunities:** Growing enterprise market
**Threats:** Intense competition from Azure/GCP

...

## Recommendations
1. Consider AWS for enterprise-scale deployments
2. Azure best for Microsoft-centric organizations
3. Google Cloud for data-intensive workloads
```

## 配置说明

### 竞品配置

```yaml
competitors:
  - name: "竞品名称"
    website: "官方网站 URL"
    focus_areas:
      - "关注领域1"
      - "关注领域2"
```

### 分析维度

可配置的分析维度包括：

- **Product Features** - 产品功能对比
- **Pricing Model** - 定价模式分析
- **Market Share** - 市场份额
- **Technology Stack** - 技术栈
- **Customer Reviews** - 客户评价
- **Recent Updates** - 最新动态

### 输出格式

支持三种输出格式：

1. **JSON** - 结构化数据，便于程序处理
2. **Markdown** - 人类可读，易于分享
3. **PDF** - 专业报告格式（需要安装 `pip install ".[pdf]"`）

## 架构说明

本示例使用 **Research** 架构，工作流程如下：

```
Lead Agent (Research Coordinator)
    ├─> Industry Researcher (调研行业趋势)
    ├─> Competitor Analyst 1 (深度分析竞品 A)
    ├─> Competitor Analyst 2 (深度分析竞品 B)
    ├─> Competitor Analyst 3 (深度分析竞品 C)
    └─> Report Generator (综合生成报告)
```

**优势：**

- **并行处理** - 多个分析任务同时进行，大幅提升效率
- **专业分工** - 每个子智能体专注于特定竞品或维度
- **自动聚合** - Lead Agent 自动整合所有分析结果

## 定制化

### 添加自定义竞品

在 `config.yaml` 中添加：

```yaml
competitors:
  - name: "Your Competitor"
    website: "https://example.com"
    focus_areas:
      - "Custom area 1"
      - "Custom area 2"
```

### 自定义分析维度

```yaml
analysis_dimensions:
  - "Security & Compliance"
  - "Developer Experience"
  - "Community Support"
```

### 调整模型配置

```yaml
models:
  lead: "opus"     # 使用更强大的模型作为主智能体
  agents: "haiku"  # 子智能体使用高性价比模型
```

## 测试

```bash
# 运行单元测试
pytest tests/test_main.py -v

# 运行集成测试
pytest tests/test_integration.py -v
```

## 常见问题

### Q: 如何减少 API 成本？

A: 调整模型配置，使用 `haiku` 作为子智能体模型：

```yaml
models:
  lead: "sonnet"
  agents: "haiku"
```

### Q: 分析时间太长怎么办？

A: 减少竞品数量或分析维度，或者使用更快的模型（haiku）。

### Q: 如何保存到 PDF？

A: 安装 PDF 依赖并配置输出格式：

```bash
pip install "claude-agent-framework[pdf]"
```

```yaml
output:
  format: "pdf"
```

### Q: 如何查看详细日志？

A: 配置日志级别为 DEBUG：

```yaml
logging:
  level: "DEBUG"
  file: "logs/analysis.log"
```

## 相关资源

- [Research 架构详细文档](../../docs/BEST_PRACTICES_CN.md#research-架构)
- [生产级示例设计文档](../../docs/PRODUCTION_EXAMPLES_DESIGN_CN.md)
- [Claude Agent Framework 文档](../../README_CN.md)

## License

MIT License
