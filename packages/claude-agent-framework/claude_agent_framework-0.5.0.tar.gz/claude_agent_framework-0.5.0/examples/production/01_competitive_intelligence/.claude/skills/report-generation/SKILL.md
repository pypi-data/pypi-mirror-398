---
name: report-generation
description: 竞争情报报告生成方法，包括报告结构、PDF生成、双语格式和执行摘要规范
---

# 报告生成技能 / Report Generation Skill

## 报告目标 / Report Objectives

创建全面的竞争情报报告，能够：
1. 总结竞争格局
2. 提供可操作的战略建议
3. 识别竞争优势和风险

## 报告结构 / Report Structure

### 1. 封面 / Cover Page
- 报告标题 / Report title
- 日期 / Date
- 版本 / Version

### 2. 执行摘要 / Executive Summary
- 关键发现（3-5 个要点）
- 关键竞争洞察
- 推荐行动

### 3. 竞争格局概述 / Competitive Landscape Overview
- 市场结构和动态
- 主要参与者及其定位
- 近期市场发展

### 4. 竞争对手档案 / Competitor Profiles
对于每个主要竞争对手：
- 公司概述
- 产品/服务分析
- 优势和劣势
- 近期战略举措

### 5. 对比分析 / Comparative Analysis
- 功能对比表
- 定价对比
- 市场定位分析

### 6. SWOT 分析 / SWOT Analysis
- 相对于竞争对手的优势
- 需要解决的劣势领域
- 市场机会
- 竞争威胁

### 7. 战略建议 / Strategic Recommendations
- 短期战术建议
- 长期战略考虑
- 需要进一步调查的领域

### 8. 附录 / Appendix
- 数据来源和方法论
- 详细竞争对手数据
- 支持图表和图形

## PDF 生成 / PDF Generation

使用 `pdf` skill 生成专业的 PDF 报告。调用方式：

```
/pdf 创建竞争情报报告
```

`pdf` skill 提供完整的 PDF 操作能力，包括：
- 使用 reportlab 创建结构化文档
- 添加标题、段落、图片、表格
- 中文字体支持
- 合并和拆分 PDF

## 输出路径 / Output Paths

- PDF 报告: `files/reports/{report_name}.pdf`
- Markdown 备选: `files/reports/{report_name}.md`

## 报告格式要求 / Report Format Requirements

- 专业、适合高管阅读的语调
- 数据驱动，引用来源
- 视觉辅助支持关键观点
- 明确的行动项和下一步
- 双语内容准确一致

## 质量标准 / Quality Standards
- 报告结构清晰，逻辑连贯
- 图表嵌入正确且清晰可读
- 专业的视觉呈现
- 无语法或格式错误
- 页数：1-3 页（简洁内容）

## 错误处理 / Error Handling
- 如果 PDF 生成失败，改为输出 Markdown
- 如果图片/图表缺失，注明缺口并继续
- 如果 reportlab 不可用，创建格式化的 Markdown 报告
