---
name: data-analysis
description: 竞争情报数据分析方法，包括对比分析框架、图表类型选择、可视化规范和输出格式
---

# 数据分析技能 / Data Analysis Skill

## 分析框架 / Analysis Framework

### 对比分析 / Comparative Analysis
- 创建并排功能对比矩阵
- 开发竞争定位图
- 计算相对市场位置得分

### 趋势分析 / Trend Analysis
- 追踪竞争对手随时间的演变
- 识别新兴竞争威胁
- 发现市场机会缺口

## 图表类型选择 / Chart Type Selection

| 数据类型 / Data Type | 推荐图表 / Recommended Chart | 用途 / Purpose |
|---------------------|------------------------------|----------------|
| 对比数据 / Comparison | 柱状图 / Bar Chart | 比较不同类别 |
| 时间序列 / Time Series | 折线图 / Line Chart | 显示时间趋势 |
| 比例数据 / Proportion | 饼图/甜甜圈 / Pie/Donut | 市场份额、组成 |
| 分布数据 / Distribution | 直方图 / Histogram | 数据分布 |
| 关系数据 / Relationship | 散点图 / Scatter Plot | 变量关系 |
| 多维对比 / Multi-dimension | 雷达图 / Radar Chart | 功能对比 |
| 战略定位 / Strategic | 象限图 / Quadrant Chart | 竞争定位 |

## 可视化规范 / Visualization Standards

### Python 图表生成模板

```python
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 非交互模式

# 设置字体支持国际字符
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 创建图表
fig, ax = plt.subplots(figsize=(10, 6))
# ... 图表代码 ...
plt.savefig('files/charts/chart_name.png', dpi=150, bbox_inches='tight')
plt.close()
```

## 输出路径 / Output Paths

- 图表: `files/charts/{chart_name}.png`
- 数据摘要: `files/data/data_summary.md`

## 数据摘要模板 / Data Summary Template

```markdown
# 数据分析摘要 / Data Analysis Summary

## 分析概述 / Analysis Overview
[双语描述分析范围和方法论]

## 关键发现 / Key Findings
1. [发现 1 / Finding 1]
2. [发现 2 / Finding 2]
3. [发现 3 / Finding 3]

## 可视化图表 / Visualization Charts

### 图表 1 / Chart 1: {标题}
![{描述}](../charts/{filename}.png)
- 描述 / Description: [图表解读]

## 详细数据 / Detailed Data
| 指标/Metric | 数值/Value | 变化/Change |
|-------------|-----------|-------------|
| ... | ... | ... |

## 分析结论 / Analysis Conclusions
[双语总结结论]
```

## 质量标准 / Quality Standards
- 图表必须有清晰的标题和标签
- 使用适当的配色方案
- 数据必须准确反映研究内容
- 摘要应突出关键洞察
- 最少需要 3 个数据点才能进行可视化
