# PR 代码审查流水线示例

本示例展示如何使用 **Pipeline（流水线）** 架构实现自动化 Pull Request 代码审查系统，通过顺序执行多个分析阶段进行全面审查。

## 概述

PR 代码审查流水线按顺序执行一系列审查阶段:

1. **架构审查** - 分析设计模式、依赖关系、架构设计
2. **代码质量** - 检查代码风格、复杂度、可维护性
3. **安全扫描** - 扫描安全漏洞（SAST 静态分析）
4. **性能分析** - 分析性能影响和潜在瓶颈
5. **测试覆盖率** - 验证测试覆盖率和质量

每个阶段都建立在前一阶段的发现之上，提供全面的代码审查反馈。

## 功能特性

- ✅ 顺序流水线处理（5个可配置阶段）
- ✅ 支持 GitHub PR URL 或本地 git 仓库
- ✅ 可配置的分析阈值（复杂度、覆盖率等）
- ✅ 多种失败策略（遇到严重问题停止 vs. 继续全部）
- ✅ 结构化审查报告和整体状态
- ✅ 可操作的建议提取
- ✅ 多种输出格式（JSON、Markdown、PDF）
- ✅ 完善的错误处理和日志记录

## 快速开始

### 安装

```bash
cd examples/production/02_pr_code_review
pip install -e ".[all]"
```

### 基本使用

1. **审查本地 PR**（对比当前分支和 main）:

```bash
python main.py
```

2. **使用自定义配置审查**:

```bash
python main.py --config my_config.yaml
```

3. **审查 GitHub PR**:

编辑 `config.yaml` 设置:
```yaml
pr_source:
  pr_url: "https://github.com/owner/repo/pull/123"
```

### 命令行选项

```bash
python main.py [选项]

选项:
  --config PATH          配置文件路径（默认: config.yaml）
  --output-format STR    输出格式: json, markdown, pdf（默认: markdown）
  --output-file PATH     输出文件路径（默认: 自动生成）
  --log-level STR        日志级别: DEBUG, INFO, WARNING, ERROR
```

## 配置说明

### 基本配置 (`config.yaml`)

```yaml
# 架构类型
architecture: pipeline

# 审查阶段（按顺序执行）
stages:
  - name: "architecture_review"
    description: "分析设计模式、依赖关系和架构"
    required: true
    timeout: 300

  - name: "code_quality"
    description: "检查代码风格、复杂度和可维护性"
    required: true
    timeout: 180

  - name: "security_scan"
    description: "扫描安全漏洞（SAST）"
    required: true
    timeout: 240

  - name: "performance_analysis"
    description: "分析性能影响和瓶颈"
    required: false  # 可选阶段
    timeout: 180

  - name: "test_coverage"
    description: "验证测试覆盖率和质量"
    required: true
    timeout: 120

# PR 来源（二选一）
pr_source:
  # 选项 1: 本地 git 仓库
  local_path: "."
  base_branch: "main"

  # 选项 2: GitHub PR URL
  # pr_url: "https://github.com/owner/repo/pull/123"

# 分析阈值
analysis:
  max_complexity: 10           # 最大圈复杂度
  max_function_length: 50      # 每个函数最大行数
  min_coverage: 80             # 最小测试覆盖率百分比
  max_file_size: 500           # 每个文件最大行数

# 失败策略
failure_strategy: "stop_on_critical"  # 或 "continue_all"

# 模型配置
models:
  lead: "sonnet"   # 主协调器模型
  agents: "haiku"  # 阶段分析器模型

# 输出配置
output:
  directory: "outputs"
  format: "markdown"  # json, markdown 或 pdf

# 日志配置
logging:
  level: "INFO"
  file: "logs/pr_review.log"
```

### 配置选项说明

| 字段 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `architecture` | string | 必须是 "pipeline" | "pipeline" |
| `stages` | list | 要执行的审查阶段 | 见示例 |
| `pr_source.local_path` | string | 本地 git 仓库路径 | "." |
| `pr_source.base_branch` | string | 对比的基准分支 | "main" |
| `pr_source.pr_url` | string | GitHub PR URL（替代本地） | - |
| `analysis.max_complexity` | int | 最大圈复杂度 | 10 |
| `analysis.min_coverage` | int | 最小测试覆盖率（%） | 80 |
| `failure_strategy` | string | "stop_on_critical" 或 "continue_all" | "stop_on_critical" |
| `models.lead` | string | 主模型: haiku, sonnet, opus | "sonnet" |
| `output.format` | string | 输出格式: json, markdown, pdf | "markdown" |

## 输出示例

### Markdown 报告

```markdown
# Pull Request 代码审查报告

**整体状态**: ✅ 通过（有建议）

## 摘要
- 执行了 5 个阶段
- 4 个阶段通过
- 1 个阶段有警告
- 0 个阶段失败

## PR 信息
- **修改文件数**: 15
- **新增行数**: 450
- **删除行数**: 120
- **基准分支**: main

## 审查阶段

### 1. 架构审查 ✅ 通过
- 关注点分离清晰
- 设计模式使用恰当
- 依赖管理良好

### 2. 代码质量 ⚠️ 警告
- 3 个函数超过复杂度阈值（>10）
- 建议重构: `process_data()`, `validate_input()`
- 整体可维护性: 良好

### 3. 安全扫描 ✅ 通过
- 未检测到 SQL 注入漏洞
- 未发现 XSS 漏洞
- 输入验证完善

### 4. 性能分析 ✅ 通过
- 无明显性能瓶颈
- 数据库查询已优化
- 缓存策略恰当

### 5. 测试覆盖率 ✅ 通过
- 覆盖率: 85%（阈值: 80%）
- 关键路径已测试
- 边界情况已覆盖

## 建议

1. **高优先级**: 重构 `process_data()` 以降低复杂度（当前: 15, 最大: 10）
2. **中优先级**: 在 `api_client.py:45` 添加错误处理
3. **低优先级**: 考虑为新 API 端点添加集成测试

## 元数据
- **审查耗时**: 45.2 秒
- **时间戳**: 2024-01-15 14:30:00
- **审查者**: Claude 代码审查机器人
```

## 架构说明

本示例使用 **Pipeline（流水线）** 架构:

```
┌─────────────────────────────────────────────────────────────┐
│                     主协调器                                  │
│  (协调顺序阶段执行)                                           │
└────────────┬────────────────────────────────────────────────┘
             │
             ├─► 阶段 1: 架构审查
             │   └─► 输出: 设计模式、架构反馈
             │
             ├─► 阶段 2: 代码质量
             │   └─► 输出: 风格问题、复杂度警告
             │
             ├─► 阶段 3: 安全扫描
             │   └─► 输出: 漏洞发现
             │
             ├─► 阶段 4: 性能分析
             │   └─► 输出: 性能影响评估
             │
             └─► 阶段 5: 测试覆盖率
                 └─► 输出: 覆盖率指标、测试质量
```

### 流水线特性

- **顺序处理**: 各阶段按顺序执行
- **数据流**: 每个阶段可使用前一阶段的输出
- **失败处理**: 可在严重失败时停止或继续全部
- **阶段独立**: 每个阶段聚焦特定方面
- **结果聚合**: 最终报告合并所有阶段发现

## 定制化

### 添加自定义审查阶段

在 `config.yaml` 中添加新阶段:

```yaml
stages:
  # ... 现有阶段 ...

  - name: "documentation_check"
    description: "验证文档完整性和质量"
    required: false
    timeout: 60
```

### 自定义分析规则

在 `config.yaml` 中修改阈值:

```yaml
analysis:
  max_complexity: 15        # 更宽松
  min_coverage: 90          # 更严格
  max_file_size: 300        # 更严格

  # 添加自定义规则
  custom_rules:
    - "no-console-log"
    - "prefer-const"
    - "no-implicit-any"
```

### 集成到 CI/CD

GitHub Actions 工作流示例:

```yaml
name: PR 代码审查

on:
  pull_request:
    branches: [ main, develop ]

jobs:
  code-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: 设置 Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: 安装依赖
        run: |
          cd examples/production/02_pr_code_review
          pip install -e ".[all]"

      - name: 运行 PR 审查
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python main.py --output-format markdown --output-file review.md

      - name: 评论 PR
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const review = fs.readFileSync('review.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: review
            });
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

### 自定义提示词模板

为特定阶段类型创建自定义提示词:

```python
# prompts/security_scan.txt
你是一名安全专家，正在审查代码中的漏洞。

重点关注:
- SQL 注入漏洞
- XSS 跨站脚本漏洞
- 认证/授权问题
- 敏感数据暴露
- 加密弱点

对于每个发现，提供:
- 严重程度（严重/高/中/低）
- 位置（文件:行号）
- 描述
- 修复步骤
```

### 编程式使用

```python
from claude_agent_framework import init
from common import load_yaml_config, ResultSaver

# 加载配置
config = load_yaml_config("config.yaml")

# 运行审查
result = await run_pr_review(config)

# 处理结果
if result["overall_status"] == "APPROVED":
    print("✅ PR 已批准!")
elif result["overall_status"] == "APPROVED_WITH_COMMENTS":
    print("⚠️ PR 已批准（有建议）")
    for rec in result["recommendations"]:
        print(f"  - {rec}")
else:
    print("❌ 需要修改")
    sys.exit(1)
```

## 故障排除

### 常见问题

1. **未找到 git**
   ```
   错误: git 命令未找到
   解决方案: 安装 git 或使用 pr_url 替代 local_path
   ```

2. **未检测到更改**
   ```
   错误: 分支之间未发现更改
   解决方案: 确保你在特性分支上，而不是 main
   ```

3. **超时错误**
   ```
   错误: 阶段超时 300 秒
   解决方案: 在阶段配置中增加超时时间
   ```

### 调试模式

启用详细日志:

```bash
python main.py --log-level DEBUG
```

## 常见问题

**问: 可以用于 Bitbucket 或 GitLab 吗？**
答: 目前支持 GitHub URL 和本地 git 仓库。对于其他平台，请使用 local_path 模式。

**问: 如何自定义审查标准？**
答: 修改 config.yaml 中的 `analysis` 部分，或创建自定义阶段提示词。

**问: 可以跳过某些阶段吗？**
答: 可以，将可选阶段设置为 `required: false`，或从阶段列表中删除它们。

**问: 典型审查需要多长时间？**
答: 小型 PR（<500 行）30-60 秒，大型 PR（>2000 行）2-3 分钟。

**问: 这能替代人工代码审查吗？**
答: 不能，它旨在通过捕获常见问题和提供初步反馈来增强人工审查。

## 相关示例

- [01_competitive_intelligence](../01_competitive_intelligence/) - Research 架构
- [03_marketing_content](../03_marketing_content/) - Critic-Actor 架构
- [07_codebase_analysis](../07_codebase_analysis/) - MapReduce 架构

## 许可证

MIT License - 详见 [LICENSE](../../../LICENSE)
