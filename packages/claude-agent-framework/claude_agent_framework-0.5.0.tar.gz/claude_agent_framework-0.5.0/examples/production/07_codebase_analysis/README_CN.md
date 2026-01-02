# 代码库分析 - MapReduce 架构示例

本示例演示使用 **MapReduce 架构**进行大规模静态代码分析和技术债务检测。它可以并行分析整个代码库（数百个文件），识别质量问题、安全漏洞并提供可执行的改进建议。

## 架构概述

MapReduce 架构将大型代码库划分为可管理的块，并行分析它们（map 阶段），然后聚合结果（reduce 阶段）:

```
                    ┌─────────────────┐
                    │   协调器        │
                    │   (编排)        │
                    └────────┬────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
         ┌──────▼──────┐ ┌──▼────────┐ ┌▼──────────┐
         │  映射器 1   │ │ 映射器 2  │ │ 映射器 N  │
         │ (分析       │ │ (分析     │ │ (分析     │
         │  块 1)      │ │  块 2)    │ │  块 N)    │
         └──────┬──────┘ └──┬────────┘ └┬──────────┘
                │            │            │
                └────────────┼────────────┘
                             │
                    ┌────────▼────────┐
                    │    归约器      │
                    │  (聚合和       │
                    │   排序)        │
                    └─────────────────┘
```

## 实际应用场景

### 1. 企业代码库审计

**场景**: 软件公司需要在重大重构之前评估 500+ Python 文件的技术债务。

**配置重点**:
- 启用所有分析类型（质量、安全、性能、可维护性、测试）
- 使用 `by_module` 分块策略尊重项目组织结构
- 设置高置信度阈值（0.8）以关注关键问题
- 生成包含可视化的综合报告

**预期结果**:
- 在 10 个并行块中分析 250+ 文件
- 识别约 50 个关键安全漏洞
- 发现约 120 个高优先级技术债务项目
- 每个模块的健康评分用于针对性重构
- 估计需要 80 小时解决关键问题

### 2. 开源项目安全审查

**场景**: 安全团队需要在采用流行开源库之前进行审计。

**配置重点**:
- 仅启用安全和测试分析类型
- 使用 `bandit` 和 `safety` 工具进行自动扫描
- 过滤掉测试文件和构建产物
- 生成安全重点报告

**预期结果**:
- 检测到 SQL 注入漏洞
- 发现并标记硬编码的密钥
- 识别依赖项漏洞
- 关键路径的测试覆盖率缺口
- 安全评分和修复优先级

### 3. 发布前质量门控

**场景**: DevOps 团队在每次主要发布前实施自动化质量检查。

**配置重点**:
- 增量分析（仅自上次发布以来更改的文件）
- 基线比较以跟踪质量趋势
- 启用自动修复建议
- 将结果导出到 CI/CD 仪表板（JSON 格式）

**预期结果**:
- 自上次发布以来新增 15 个问题
- 解决了 22 个问题
- 总体质量评分：82/100（从 78/100 提升）
- 4 个需要立即关注的阻塞问题
- 为 12 个问题提供自动修复建议

## 配置说明

完整的 `config.yaml` 结构:

```yaml
architecture: mapreduce

analysis:
  max_parallel_mappers: 10       # 并行分析任务数（推荐 10）
  chunk_size: 50                 # 每个块的文件数（根据总数自动调整）
  aggregation_strategy: weighted # weighted、average 或 max
  min_confidence: 0.7            # 报告的置信度阈值（0.0-1.0）
  enable_caching: true           # 缓存结果用于增量分析
  output_format: structured      # structured、markdown 或 json

mapreduce_config:
  mapper:
    name: code_analyzer
    role: 分析代码块以查找质量问题、技术债务和模式
    tools:
      - Read         # 读取源文件
      - Bash         # 运行静态分析工具
      - Grep         # 搜索模式
    analysis_depth: comprehensive  # quick、standard 或 comprehensive

  reducer:
    name: results_aggregator
    role: 聚合并排序所有块的分析结果
    capabilities:
      - Deduplication   # 删除重复发现
      - Prioritization  # 按严重性和影响排序
      - Categorization  # 按类型和位置分组
      - Trend analysis  # 识别代码库中的模式

  coordinator:
    name: analysis_coordinator
    role: 编排分析工作流并确保完整性
    responsibilities:
      - 基于文件关系的智能分块
      - 跨映射器的负载均衡
      - 进度跟踪
      - 质量保证

# 分块策略（通过 options.chunking_strategy 选择）
chunking_strategies:
  by_module:          # 按模块/包结构分组（默认）
    description: 按模块/包结构分组文件
    when_to_use: 组织良好、模块清晰的代码库
    benefits:
      - 尊重代码组织结构
      - 更好的分析上下文
      - 更易理解的结果

  by_file_type:       # 按语言/扩展名分组
    description: 按扩展名/语言分组文件
    when_to_use: 多语言代码库
    benefits:
      - 语言特定的分析
      - 并行语言处理
      - 专业工具使用

  by_size:            # 按文件大小平衡块
    description: 按总文件大小平衡块
    when_to_use: 文件大小差异很大
    benefits:
      - 均匀的工作负载分配
      - 可预测的执行时间
      - 更好的资源利用

  by_git_history:     # 关注频繁更改的文件
    description: 按更改频率分组文件
    when_to_use: 关注频繁更改的代码
    benefits:
      - 优先处理高风险区域
      - 发现热点
      - 针对性的重构工作

# 分析类型（根据需要启用/禁用）
analysis_types:
  code_quality:
    enabled: true
    priority: 1
    checks:
      - complexity          # 圈复杂度
      - duplication         # 代码重复
      - naming_conventions  # 变量/函数命名
      - code_smells         # 常见反模式
      - documentation       # 缺失的文档字符串/注释
    tools:
      - pylint
      - radon
      - flake8
    thresholds:
      max_complexity: 10
      max_duplication: 5
      min_documentation: 0.7

  security:
    enabled: true
    priority: 1
    checks:
      - sql_injection       # SQL 注入漏洞
      - xss                 # 跨站脚本
      - hardcoded_secrets   # 代码中的密码、API 密钥
      - unsafe_functions    # 危险函数使用
      - dependency_vulnerabilities
    tools:
      - bandit
      - safety
    severity_levels:
      - critical
      - high
      - medium
      - low

  performance:
    enabled: true
    priority: 2
    checks:
      - n_plus_one_queries  # 数据库查询模式
      - inefficient_loops   # 嵌套循环、不必要的迭代
      - memory_leaks        # 潜在的内存问题
      - blocking_operations # 异步代码中的阻塞 I/O

  maintainability:
    enabled: true
    priority: 2
    checks:
      - technical_debt      # TODO、FIXME、HACK
      - deprecated_usage    # 使用已弃用的 API
      - dead_code           # 无法访问的代码
      - long_methods        # 超出长度限制的方法
      - god_classes         # 责任过多的类
    thresholds:
      max_method_lines: 50
      max_class_lines: 300
      max_parameters: 5

  testing:
    enabled: true
    priority: 3
    checks:
      - test_coverage       # 代码覆盖率百分比
      - missing_tests       # 未测试的关键路径
      - test_quality        # 断言计数、测试隔离
      - flaky_tests         # 结果不一致的测试
    target_coverage: 0.8

# 高级设置
advanced:
  incremental_analysis: true    # 仅分析更改的文件
  git_integration: true         # 使用 git 历史作为上下文
  baseline_comparison: true     # 与以前的运行进行比较
  auto_fix_suggestions: true    # 建议自动修复
  confidence_scoring: true      # 为每个发现评分

  performance:
    timeout_per_chunk: 300      # 每个块 5 分钟
    max_memory_per_mapper: 1024 # 1GB 内存限制
    retry_on_failure: 3         # 重试失败的块

  filters:
    exclude_paths:
      - "*/tests/*"             # 排除测试文件
      - "*/migrations/*"        # 排除迁移文件
      - "*/build/*"            # 排除构建产物
      - "*/node_modules/*"     # 排除依赖项

    include_extensions:
      - .py
      - .js
      - .ts
      - .java
      - .go
      - .rb

    min_file_size: 10          # 字节
    max_file_size: 1000000     # 1MB

models:
  coordinator: sonnet          # 复杂编排（推荐: sonnet）
  mapper: haiku                # 快速并行分析（推荐: haiku）
  reducer: sonnet              # 复杂聚合逻辑（推荐: sonnet）
```

## 输出结构

分析返回一个综合结果字典:

```python
{
    "analysis_id": "abc123...",
    "title": "代码库分析: my-project",
    "summary": "执行摘要，健康评分 75/100...",

    "codebase": {
        "path": "/path/to/codebase",
        "files_analyzed": 250,
        "lines_of_code": 35000,
        "languages": ["Python", "JavaScript"]
    },

    "execution": {
        "chunks_analyzed": [
            {
                "chunk_id": 1,
                "file_count": 50,
                "files": ["file1.py", "file2.py", ...]
            },
            ...
        ],
        "parallel_mappers": 5,
        "chunking_strategy": "by_module"
    },

    "issues": {
        "total": 87,
        "by_severity": {
            "critical": 5,
            "high": 18,
            "medium": 42,
            "low": 22
        },
        "critical": [
            {
                "severity": "critical",
                "type": "security",
                "file": "auth/models.py",
                "line": 45,
                "description": "SQL 注入漏洞",
                "confidence": "High",
                "fix_effort": "Medium"
            },
            ...
        ],
        "high": [...],
        "medium": [...],
        "low": [...],
        "all_issues": [...]
    },

    "metrics": {
        "total_files": 250,
        "total_lines": 35000,
        "average_complexity": 6.8,
        "test_coverage": 72.5,
        "quality_score": 78,
        "security_score": 68,
        "maintainability_score": 82
    },

    "module_health": [
        {
            "name": "auth_module",
            "score": 65,
            "status": "needs_attention"  # healthy, needs_attention, critical
        },
        ...
    ],

    "trends": {
        "new_issues": 12,
        "resolved_issues": 18,
        "net_change": -6
    },

    "recommendations": [
        {
            "action": "修复 auth/models.py 中的 SQL 注入",
            "reason": "关键安全风险",
            "effort": "Medium",
            "impact": "High",
            "priority": "High"
        },
        ...
    ],

    "scores": {
        "overall": 75,
        "quality": 78,
        "security": 68,
        "maintainability": 82,
        "test_coverage": 72.5
    },

    "metadata": {
        "timestamp": "2025-12-25T10:30:00Z",
        "analysis_config": {
            "types_enabled": ["code_quality", "security", "performance"],
            "parallel_mappers": 10,
            "chunk_size": 50
        },
        "models": {
            "coordinator": "sonnet",
            "mapper": "haiku",
            "reducer": "sonnet"
        }
    }
}
```

## 自定义示例

### 1. 仅安全分析

```python
from claude_agent_framework import init
from main import run_codebase_analysis
import yaml

with open("config.yaml") as f:
    config = yaml.safe_load(f)

# 除安全外禁用所有
config["analysis_types"] = {
    "security": {
        "enabled": True,
        "priority": 1,
        "checks": ["sql_injection", "xss", "hardcoded_secrets"]
    }
}

result = await run_codebase_analysis(config, "/path/to/codebase")
print(f"安全评分: {result['scores']['security']}/100")
print(f"关键漏洞: {len(result['issues']['critical'])}")
```

### 2. 快速质量检查（快速模式）

```python
# 使用快速模型和最少检查
config["mapreduce_config"]["mapper"]["analysis_depth"] = "quick"
config["models"] = {"coordinator": "haiku", "mapper": "haiku", "reducer": "haiku"}
config["analysis"]["chunk_size"] = 100  # 更大的块

result = await run_codebase_analysis(config, "/path/to/codebase")
```

### 3. 增量分析与基线对比

```python
# 仅分析自上次运行以来更改的文件
config["advanced"]["incremental_analysis"] = True
config["advanced"]["baseline_comparison"] = True
config["advanced"]["git_integration"] = True

result = await run_codebase_analysis(config, "/path/to/codebase")

# 与基线比较
trends = result["trends"]
print(f"新增问题: +{trends['new_issues']}")
print(f"已解决: -{trends['resolved_issues']}")
print(f"净变化: {trends['net_change']}")
```

### 4. 自定义分块策略

```python
# 使用 git 历史记录优先处理频繁更改的文件
options = {"chunking_strategy": "by_git_history"}
result = await run_codebase_analysis(config, "/path/to/codebase", options)
```

### 5. 导出到 CI/CD 流水线

```python
import json

result = await run_codebase_analysis(config, "/path/to/codebase")

# 为 CI/CD 导出
with open("analysis_report.json", "w") as f:
    json.dump(result, f, indent=2)

# 如果发现关键问题则失败构建
critical_count = len(result["issues"]["critical"])
if critical_count > 0:
    print(f"❌ 构建失败: 发现 {critical_count} 个关键问题")
    exit(1)
else:
    print(f"✅ 构建通过: 质量评分 {result['scores']['overall']}/100")
```

## 最佳实践

### 1. 选择适当的块大小

- **小型代码库（< 50 文件）**: chunk_size = 10-20
- **中型代码库（50-200 文件）**: chunk_size = 30-50
- **大型代码库（200-500 文件）**: chunk_size = 50-100
- **超大型代码库（> 500 文件）**: chunk_size = 100-200

### 2. 并行映射器优化

- **本地开发**: max_parallel_mappers = 3-5（避免 API 速率限制）
- **CI/CD 流水线**: max_parallel_mappers = 8-12（更快执行）
- **生产审计**: max_parallel_mappers = 10-15（平衡速度与成本）

### 3. 分析类型选择

**日常检查**: 仅启用 `code_quality` 和 `security`（优先级 1）
**发布门控**: 启用 `code_quality`、`security`、`testing`（优先级 1-3）
**全面审计**: 启用所有分析类型
**安全审查**: 仅启用 `security` 及所有检查

### 4. 模型选择策略

- **协调器**: 始终使用 `sonnet`（复杂编排逻辑）
- **映射器**: 使用 `haiku` 提高速度，`sonnet` 提高准确性
- **归约器**: 使用 `sonnet` 进行复杂聚合，如果是简单去重则使用 `haiku`

### 5. 置信度阈值调整

- **高置信度（0.8-1.0）**: 用于关键生产审计（更少误报）
- **中等置信度（0.6-0.8）**: 用于常规代码审查（平衡）
- **低置信度（0.4-0.6）**: 用于探索性分析（更多发现，一些误报）

### 6. 增量分析

启用 `incremental_analysis` 用于:
- 每日/每小时 CI 检查
- 提交前钩子
- 持续监控

禁用用于:
- 初始审计
- 重大重构验证
- 季度综合审查

## 性能指标

基于 500 文件 Python 代码库的测试:

| 配置 | 文件数 | 块数 | 并行数 | 时间 | 成本 |
|------|--------|------|--------|------|------|
| 快速（Haiku）| 500 | 5 | 5 | ~3 分钟 | ~$0.50 |
| 标准（混合）| 500 | 10 | 10 | ~5 分钟 | ~$1.20 |
| 全面（Sonnet）| 500 | 10 | 10 | ~8 分钟 | ~$2.50 |

**可扩展性估计**:
- 100 文件: 1-2 分钟
- 500 文件: 3-8 分钟
- 1000 文件: 6-15 分钟
- 5000 文件: 25-60 分钟

## 故障排除

### 问题: 结果为空或缺失

**症状**: 分析完成但未返回问题或指标

**原因**:
1. `exclude_paths` 过滤器过于激进
2. `min_confidence` 阈值太高
3. 分析类型已禁用

**解决方案**:
```python
# 检查过滤器
config["advanced"]["filters"]["exclude_paths"] = []  # 暂时删除所有排除项

# 降低置信度阈值
config["analysis"]["min_confidence"] = 0.5

# 启用所有分析类型
for analysis_type in config["analysis_types"].values():
    analysis_type["enabled"] = True
```

### 问题: 超时错误

**症状**: `TimeoutError` 或块失败

**原因**:
1. 块大小过大
2. 复杂文件的超时时间太短
3. 过多的并行映射器使 API 过载

**解决方案**:
```python
# 减小块大小
config["analysis"]["chunk_size"] = 20  # 更小的块

# 增加超时时间
config["advanced"]["performance"]["timeout_per_chunk"] = 600  # 10 分钟

# 减少并行度
config["analysis"]["max_parallel_mappers"] = 3
```

### 问题: 高误报率

**症状**: 过多低优先级或不相关的问题

**原因**:
1. 置信度阈值太低
2. 分析深度过于全面
3. 工具产生噪音

**解决方案**:
```python
# 提高置信度阈值
config["analysis"]["min_confidence"] = 0.8

# 使用标准深度而不是全面
config["mapreduce_config"]["mapper"]["analysis_depth"] = "standard"

# 禁用噪音检查
config["analysis_types"]["code_quality"]["checks"] = ["complexity", "security"]  # 删除 "naming_conventions"
```

### 问题: 内存错误

**症状**: 分析期间出现内存不足错误

**原因**:
1. 过多的并行映射器
2. 块大小过大
3. 代码库中有非常大的文件

**解决方案**:
```python
# 减少并行度
config["analysis"]["max_parallel_mappers"] = 3

# 限制文件大小
config["advanced"]["filters"]["max_file_size"] = 500000  # 500KB

# 使用 "by_size" 分块以平衡负载
options = {"chunking_strategy": "by_size"}
```

## 完整示例

```python
import asyncio
import yaml
from main import run_codebase_analysis

async def analyze_codebase():
    # 加载配置
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    # 根据您的需求自定义
    config["analysis"]["max_parallel_mappers"] = 5
    config["analysis"]["min_confidence"] = 0.7

    # 启用特定分析类型
    config["analysis_types"]["security"]["enabled"] = True
    config["analysis_types"]["code_quality"]["enabled"] = True

    # 运行分析
    print("🔍 开始代码库分析...")
    result = await run_codebase_analysis(
        config,
        "/path/to/your/codebase",
        options={"chunking_strategy": "by_module"}
    )

    # 打印摘要
    print(f"\n{'='*60}")
    print(f"📊 分析完成: {result['title']}")
    print(f"{'='*60}")
    print(f"\n📁 代码库:")
    print(f"  - 分析的文件: {result['codebase']['files_analyzed']}")
    print(f"  - 代码行数: {result['codebase']['lines_of_code']:,}")

    print(f"\n🎯 总体评分: {result['scores']['overall']}/100")
    print(f"  - 质量: {result['scores']['quality']}/100")
    print(f"  - 安全: {result['scores']['security']}/100")
    print(f"  - 可维护性: {result['scores']['maintainability']}/100")

    print(f"\n⚠️  发现的问题: {result['issues']['total']}")
    print(f"  - 关键: {result['issues']['by_severity']['critical']}")
    print(f"  - 高: {result['issues']['by_severity']['high']}")
    print(f"  - 中: {result['issues']['by_severity']['medium']}")
    print(f"  - 低: {result['issues']['by_severity']['low']}")

    if result['issues']['critical']:
        print(f"\n🚨 关键问题（前 5 个）:")
        for issue in result['issues']['critical'][:5]:
            print(f"  - {issue['file']}:{issue['line']} - {issue['description']}")

    print(f"\n📈 模块健康状况:")
    for module in result['module_health'][:5]:
        status_icon = "✅" if module['status'] == "healthy" else "⚠️" if module['status'] == "needs_attention" else "❌"
        print(f"  {status_icon} {module['name']}: {module['score']}/100")

    if result['recommendations']:
        print(f"\n💡 主要建议:")
        for i, rec in enumerate(result['recommendations'][:5], 1):
            print(f"  {i}. {rec['action']}")
            print(f"     工作量: {rec['effort']} | 影响: {rec['impact']}")

    return result

if __name__ == "__main__":
    result = asyncio.run(analyze_codebase())
```

**示例输出**:

```
🔍 开始代码库分析...

============================================================
📊 分析完成: 代码库分析: my-project
============================================================

📁 代码库:
  - 分析的文件: 250
  - 代码行数: 35,000

🎯 总体评分: 75/100
  - 质量: 78/100
  - 安全: 68/100
  - 可维护性: 82/100

⚠️  发现的问题: 87
  - 关键: 5
  - 高: 18
  - 中: 42
  - 低: 22

🚨 关键问题（前 5 个）:
  - auth/models.py:45 - 原始查询中的 SQL 注入漏洞
  - api/endpoints.py:89 - 管理端点缺少身份验证检查
  - utils/crypto.py:23 - 硬编码的加密密钥
  - payment/process.py:156 - SQL 查询中的未验证用户输入
  - session/manager.py:78 - 不安全的会话令牌生成

📈 模块健康状况:
  ❌ auth_module: 65/100
  ⚠️  api_module: 78/100
  ✅ utils_module: 88/100
  ✅ core_module: 92/100
  ✅ tests_module: 95/100

💡 主要建议:
  1. 修复 auth/models.py 中的 SQL 注入漏洞
     工作量: Medium | 影响: High
  2. 为所有 API 端点添加身份验证检查
     工作量: Medium | 影响: High
  3. 删除硬编码凭据并使用环境变量
     工作量: Low | 影响: High
  4. 降低 auth/views.py 的圈复杂度（复杂度: 25）
     工作量: High | 影响: Medium
  5. 将测试覆盖率提高到目标 80%（当前 72.5%）
     工作量: High | 影响: Medium
```

## 架构优势

1. **可扩展性**: 并行分析数百个文件，处理任何大小的代码库
2. **全面性**: 检测质量、安全、性能和可维护性问题
3. **可操作性**: 提供具有工作量/影响估计的优先级建议
4. **灵活性**: 高度可定制的分块策略和分析类型
5. **高效性**: MapReduce 模式最小化冗余工作并优化资源使用
6. **增量性**: 支持基线比较和 CI/CD 的增量分析
7. **详细性**: 每个模块的健康评分支持有针对性的重构工作

## 下一步

1. **自定义配置**: 根据您的代码库和优先级调整 `config.yaml`
2. **运行初始审计**: 执行全面分析以建立基线
3. **集成 CI/CD**: 将自动检查添加到您的部署流水线
4. **设置质量门控**: 定义构建失败的阈值（例如，无关键问题）
5. **跟踪趋势**: 随时间监控质量评分以衡量进度
6. **优先修复**: 首先解决关键和高优先级问题
7. **迭代**: 定期重新运行分析以尽早发现新问题
