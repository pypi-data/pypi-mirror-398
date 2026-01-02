---
name: PDF 工具集
description: PDF 创建、编辑、合并、拆分工具集
---

# PDF 操作工具集

本技能提供 PDF 文档操作的完整指南。

## 依赖库

```bash
pip install reportlab pypdf pdfplumber
```

## 1. 创建 PDF (reportlab)

### 基础文档

```python
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    Table, TableStyle, PageBreak
)
from reportlab.lib import colors

# 创建文档
doc = SimpleDocTemplate(
    "output.pdf",
    pagesize=A4,
    rightMargin=72,
    leftMargin=72,
    topMargin=72,
    bottomMargin=72
)

# 获取样式
styles = getSampleStyleSheet()

# 构建内容
story = []

# 添加标题
story.append(Paragraph("报告标题", styles['Heading1']))
story.append(Spacer(1, 12))

# 添加段落
story.append(Paragraph("这是正文内容。", styles['Normal']))
story.append(Spacer(1, 12))

# 生成 PDF
doc.build(story)
```

### 添加图片

```python
from reportlab.platypus import Image

# 添加图片（指定宽度，保持比例）
img = Image("chart.png", width=400)
story.append(img)
```

### 添加表格

```python
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

data = [
    ['标题1', '标题2', '标题3'],
    ['数据1', '数据2', '数据3'],
    ['数据4', '数据5', '数据6'],
]

table = Table(data)
table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTSIZE', (0, 0), (-1, 0), 14),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
]))

story.append(table)
```

### 自定义样式

```python
# 自定义段落样式
custom_style = ParagraphStyle(
    'CustomStyle',
    parent=styles['Normal'],
    fontSize=12,
    leading=16,
    spaceAfter=12,
    textColor=colors.darkblue,
)
```

## 2. 合并 PDF (pypdf)

```python
from pypdf import PdfMerger

merger = PdfMerger()

# 添加 PDF 文件
merger.append("file1.pdf")
merger.append("file2.pdf")
merger.append("file3.pdf")

# 写入合并后的文件
merger.write("merged.pdf")
merger.close()
```

## 3. 拆分 PDF

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("input.pdf")

# 提取特定页面
for i, page in enumerate(reader.pages):
    writer = PdfWriter()
    writer.add_page(page)
    with open(f"page_{i+1}.pdf", "wb") as output:
        writer.write(output)
```

## 4. 提取文本 (pdfplumber)

```python
import pdfplumber

with pdfplumber.open("input.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        print(text)
```

## 5. 提取表格

```python
import pdfplumber

with pdfplumber.open("input.pdf") as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            for row in table:
                print(row)
```

## 6. 完整报告示例

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
)
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime

def create_research_report(
    output_path: str,
    title: str,
    summary: str,
    findings: list,
    charts: list,
    data_table: list
):
    """创建研究报告 PDF"""

    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # 封面
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph(title, styles['Title']))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(
        f"生成日期: {datetime.now().strftime('%Y-%m-%d')}",
        styles['Normal']
    ))
    story.append(PageBreak())

    # 执行摘要
    story.append(Paragraph("执行摘要", styles['Heading1']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(summary, styles['Normal']))
    story.append(Spacer(1, 24))

    # 关键发现
    story.append(Paragraph("关键发现", styles['Heading1']))
    story.append(Spacer(1, 12))
    for i, finding in enumerate(findings, 1):
        story.append(Paragraph(f"{i}. {finding}", styles['Normal']))
        story.append(Spacer(1, 6))
    story.append(Spacer(1, 24))

    # 图表
    if charts:
        story.append(Paragraph("数据可视化", styles['Heading1']))
        story.append(Spacer(1, 12))
        for chart_path in charts:
            try:
                img = Image(chart_path, width=5*inch)
                story.append(img)
                story.append(Spacer(1, 12))
            except Exception as e:
                story.append(Paragraph(f"图表加载失败: {chart_path}", styles['Normal']))

    # 数据表格
    if data_table:
        story.append(Paragraph("详细数据", styles['Heading1']))
        story.append(Spacer(1, 12))
        table = Table(data_table)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#E7E6E6')]),
        ]))
        story.append(table)

    # 生成 PDF
    doc.build(story)
    return output_path

# 使用示例
create_research_report(
    output_path="files/reports/research_report.pdf",
    title="市场研究报告",
    summary="本报告分析了...",
    findings=["发现1", "发现2", "发现3"],
    charts=["files/charts/chart1.png", "files/charts/chart2.png"],
    data_table=[
        ["指标", "2023", "2024", "增长率"],
        ["市场规模", "100亿", "120亿", "20%"],
        ["用户数", "1000万", "1500万", "50%"],
    ]
)
```

## 注意事项

1. **中文支持**：reportlab 默认不支持中文，需要注册中文字体：
   ```python
   from reportlab.pdfbase import pdfmetrics
   from reportlab.pdfbase.ttfonts import TTFont
   pdfmetrics.registerFont(TTFont('SimHei', 'SimHei.ttf'))
   ```

2. **图片格式**：支持 PNG, JPG, GIF 格式

3. **内存优化**：处理大文件时使用流式处理
