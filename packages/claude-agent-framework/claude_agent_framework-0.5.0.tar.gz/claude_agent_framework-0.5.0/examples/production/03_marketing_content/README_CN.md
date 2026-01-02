# 营销内容优化示例

本示例展示如何使用 **Critic-Actor（评论家-演员）** 架构通过多维度评估和反馈迭代创建和改进营销内容。

## 概述

营销内容优化系统使用生成-评估-改进循环:

1. **Actor（演员）** 基于简介和品牌指南生成初始内容
2. **Critic（评论家）** 跨多个维度（SEO、吸引力、品牌、准确性）评估内容
3. **Actor** 基于具体反馈改进内容
4. **重复** 直到达到质量阈值或耗尽最大迭代次数

此外，系统可以为同一信息生成不同角度的 A/B 测试变体。

## 功能特性

- ✅ 使用 Critic-Actor 模式迭代优化内容
- ✅ 多维度评估（SEO、吸引力、品牌一致性、技术准确性）
- ✅ 加权评分系统（自定义每个维度的重要性）
- ✅ 品牌声音和语调强制执行
- ✅ 禁用短语检测
- ✅ 质量阈值和改进跟踪
- ✅ 不同角度的 A/B 测试变体生成
- ✅ 多种内容类型（博客文章、邮件、广告文案、社交媒体、落地页）
- ✅ 多种输出格式（JSON、Markdown、PDF）
- ✅ 迭代历史跟踪

## 快速开始

### 安装

```bash
cd examples/production/03_marketing_content
pip install -e ".[all]"
```

### 基本使用

1. **使用默认配置优化营销内容**:

```bash
python main.py
```

2. **使用自定义配置**:

```bash
python main.py --config my_config.yaml
```

3. **生成 PDF 报告**:

```bash
python main.py --output-format pdf
```

### 命令行选项

```bash
python main.py [选项]

选项:
  --config PATH          配置文件（默认: config.yaml）
  --output-format STR    输出格式: json, markdown, pdf（默认: markdown）
  --output-file PATH     输出文件路径（默认: 自动生成）
  --log-level STR        日志级别: DEBUG, INFO, WARNING, ERROR
```

## 配置说明

### 基本配置 (`config.yaml`)

```yaml
# 架构类型
architecture: critic_actor

# 内容配置
content:
  # 内容类型
  type: "blog_post"  # blog_post, email, ad_copy, social_media, landing_page

  # 内容简介
  brief: |
    创建一篇博客文章，宣布我们新的 AI 驱动的代码审查工具。
    目标受众：软件工程团队和 DevOps 专业人员。
    关键要点：
    - 自动化代码质量检查
    - 安全漏洞检测
    - 与 GitHub 和 GitLab 集成
    - 减少 50% 的审查时间
    行动号召：注册免费试用

  # 关键词（SEO）
  keywords:
    - "AI 代码审查"
    - "自动化代码分析"
    - "代码质量"

  # 目标长度
  target_length:
    min_words: 800
    max_words: 1200

# 品牌指南
brand:
  voice: "专业但平易近人"

  tone:
    - "创新的"
    - "值得信赖的"
    - "技术但易懂的"

  prohibited_phrases:
    - "革命性的"
    - "改变游戏规则"

  values:
    - "技术卓越"
    - "开发者生产力"

# 评估标准（权重总和必须为 100）
evaluation:
  # SEO 优化
  seo:
    weight: 25
    criteria:
      - "关键词密度（1-2%）"
      - "元描述（150-160 字符）"
      - "标题结构（H1、H2、H3）"

  # 吸引力/可读性
  engagement:
    weight: 30
    criteria:
      - "开头质量（第一段）"
      - "可读性评分（Flesch-Kincaid 60-80）"
      - "行动号召清晰度"

  # 品牌一致性
  brand_consistency:
    weight: 25
    criteria:
      - "声音对齐"
      - "语调一致性"
      - "无禁用短语"

  # 技术准确性
  accuracy:
    weight: 20
    criteria:
      - "事实正确性"
      - "技术术语使用"

# 迭代配置
iteration:
  max_iterations: 3              # N 次迭代后停止
  quality_threshold: 85          # 分数 >= 阈值时停止
  min_improvement: 5             # 改进 < X% 时停止

# A/B 测试
ab_testing:
  enabled: true
  num_variants: 2

# 模型
models:
  lead: "sonnet"       # 主协调器
  actor: "sonnet"      # 内容创建者（需要创造力）
  critic: "haiku"      # 评估者（可以更快/更便宜）

# 输出
output:
  directory: "outputs"
  format: "markdown"
  include_evaluation: true
  include_history: true
```

### 配置选项说明

| 字段 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `content.type` | string | 内容类型（blog_post、email、ad_copy等） | "blog_post" |
| `content.brief` | string | 内容创建简介 | 必需 |
| `content.keywords` | list | SEO 关键词 | [] |
| `content.target_length` | object | 最小/最大字数 | - |
| `brand.voice` | string | 品牌声音描述 | 必需 |
| `brand.tone` | list | 语调属性 | [] |
| `brand.prohibited_phrases` | list | 要避免的短语 | [] |
| `evaluation.*.weight` | int | 维度权重（总和=100） | 必需 |
| `iteration.max_iterations` | int | 最大迭代次数 | 3 |
| `iteration.quality_threshold` | int | 目标分数（0-100） | 85 |
| `ab_testing.enabled` | bool | 生成 A/B 变体 | false |
| `ab_testing.num_variants` | int | 变体数量 | 2 |

## 输出示例

### Markdown 报告

```markdown
# 营销内容优化报告

**整体状态**: ✅ 达到目标质量

## 摘要
通过 3 次迭代优化了 blog_post
初始分数: 68/100
最终分数: 88/100
改进: +20.0 分

## 最终内容

[优化后的内容 - 准备发布]

## 迭代历史

### 迭代 1（分数: 68/100）

**评估**:
- SEO: 60/100 - 需要更多关键词集成
- 吸引力: 70/100 - 开头可以更强
- 品牌一致性: 75/100 - 声音略显正式
- 准确性: 80/100 - 技术细节良好

**改进措施**:
- 将关键词密度提高到 1.5%
- 用更强的开头重写第一段
- 调整语调使其更平易近人

### 迭代 2（分数: 82/100）

**评估**:
- SEO: 85/100 - 关键词集成更好
- 吸引力: 88/100 - 出色的开头和行动号召
- 品牌一致性: 82/100 - 声音对齐良好
- 准确性: 85/100 - 清晰、准确的声明

**改进措施**:
- 添加 H2/H3 子标题以改善结构
- 加强行动号召
- 添加支持性统计数据

### 迭代 3（分数: 88/100）

**评估**:
- SEO: 90/100 - 出色的关键词放置
- 吸引力: 92/100 - 高度吸引人
- 品牌一致性: 88/100 - 完美的声音匹配
- 准确性: 90/100 - 有据可查的声明

**最终结果**: 内容达到质量阈值（≥85）

## A/B 测试变体

### 变体 1: 功能导向
[强调产品功能的变体...]

### 变体 2: 利益导向
[强调用户收益的变体...]

## 元数据
- 时间戳: 2024-01-15 14:30:00
- 迭代次数: 3
- 目标内容类型: blog_post
- 质量阈值: 85/100
```

## 架构说明

本示例使用 **Critic-Actor（评论家-演员）** 架构:

```
┌─────────────────────────────────────────────────────────────┐
│                    主协调器                                   │
│  (管理生成-评估-改进循环)                                      │
└──────────┬──────────────────────────────────┬───────────────┘
           │                                  │
           ▼                                  ▼
    ┌──────────┐                      ┌──────────┐
    │  Actor   │◄─────反馈──────────│  Critic  │
    │  演员    │                      │  评论家  │
    │ 生成     │──────内容────────►│ 评估     │
    │ 内容     │                      │ 分数 &   │
    │          │                      │ 反馈     │
    └──────────┘                      └──────────┘
           │
           │ (重复直到阈值或最大迭代次数)
           ▼
    最终内容
```

### Critic-Actor 特性

- **迭代改进**: 内容通过多个循环改进
- **具体反馈**: 评论家提供可操作的建议
- **多维度**: 跨 SEO、吸引力、品牌、准确性评估
- **加权评分**: 自定义不同维度的重要性
- **收敛检测**: 当改进变得微小时停止

## 定制化

### 添加自定义评估维度

在 `config.yaml` 中添加新维度:

```yaml
evaluation:
  # ... 现有维度 ...

  accessibility:
    weight: 10  # 调整其他权重以保持总和=100
    criteria:
      - "图像的替代文本"
      - "适当的标题层次结构"
      - "WCAG 合规性"
```

### 自定义内容类型

为新内容类型创建模板:

```python
# prompts/product_description.txt
按照以下指南创建引人注目的产品描述:

**产品**: {product_name}
**关键特性**: {features}
**目标受众**: {audience}
**长度**: {min_words}-{max_words} 字

专注于利益而非特性，使用感官语言，并包括社会证明。
```

### 品牌声音示例

不同的品牌声音配置:

```yaml
# 专业/技术
brand:
  voice: "权威且专业"
  tone: ["技术性", "精确", "值得信赖"]

# 休闲/友好
brand:
  voice: "对话式且温暖"
  tone: ["友好", "易懂", "热情"]

# 奢华/高端
brand:
  voice: "精致且有抱负"
  tone: ["优雅", "独特", "精炼"]
```

## 测试

### 运行单元测试

```bash
pytest tests/test_main.py -v
```

### 运行集成测试

```bash
pytest tests/test_integration.py -v
```

### 运行所有测试

```bash
pytest tests/ -v --cov=. --cov-report=html
```

## 高级用法

### 编程式使用

```python
from claude_agent_framework import init
from common import load_yaml_config, ResultSaver

# 加载配置
config = load_yaml_config("config.yaml")

# 运行优化
result = await run_content_optimization(config)

# 访问结果
print(f"最终分数: {result['final_score']}/100")
print(f"迭代次数: {len(result['iterations'])}")

# 如需要生成 A/B 变体
if result['ab_variants']:
    for variant in result['ab_variants']:
        print(f"\n变体 {variant['variant']} ({variant['angle']}):")
        print(variant['content'])
```

### 自定义评估逻辑

用自定义评估扩展评论家:

```python
def custom_evaluation(content: str, brand: dict) -> dict:
    """自定义评估逻辑。"""
    scores = {}

    # 检查阅读水平
    from textstat import flesch_reading_ease
    readability = flesch_reading_ease(content)
    scores['readability'] = min(100, readability * 1.25)

    # 检查品牌声音合规性
    voice_keywords = brand.get('voice_keywords', [])
    matches = sum(1 for kw in voice_keywords if kw.lower() in content.lower())
    scores['brand_voice'] = min(100, (matches / len(voice_keywords)) * 100)

    return scores
```

## 故障排除

### 常见问题

1. **分数未改进**
   ```
   问题: 分数在迭代中保持不变
   解决方案: 降低 quality_threshold 或增加 max_iterations
   ```

2. **内容太短/太长**
   ```
   问题: 生成的内容不符合长度要求
   解决方案: 在内容简介中强调 target_length
   ```

3. **品牌声音不匹配**
   ```
   问题: 内容与品牌声音不匹配
   解决方案: 在品牌配置中提供更具体的声音示例
   ```

### 调试模式

启用详细日志:

```bash
python main.py --log-level DEBUG
```

## 常见问题

**问: 应该使用多少次迭代？**
答: 从 3 次开始。对于复杂内容或高质量标准，增加到 5 次。

**问: 可以用于英语以外语言的内容吗？**
答: 可以，只需用目标语言提供简介和品牌指南。

**问: 如何权衡评估维度？**
答: 调整每个维度的 `weight` 字段。权重总和必须为 100。

**问: 可以生成超过 2 个 A/B 变体吗？**
答: 可以，将 `ab_testing.num_variants` 设置为任意数字（推荐: 2-4）。

**问: 优化需要多长时间？**
答: 每次迭代通常 45-90 秒，取决于内容长度和模型。

## 相关示例

- [01_competitive_intelligence](../01_competitive_intelligence/) - Research 架构
- [02_pr_code_review](../02_pr_code_review/) - Pipeline 架构
- [05_tech_decision](../05_tech_decision/) - Debate 架构

## 许可证

MIT License - 详见 [LICENSE](../../../LICENSE)
