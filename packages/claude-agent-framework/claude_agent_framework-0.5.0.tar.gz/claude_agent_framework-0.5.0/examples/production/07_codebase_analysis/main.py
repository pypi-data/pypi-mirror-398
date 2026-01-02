#!/usr/bin/env python3
"""代码库分析 - 使用 MapReduce 架构的示例"""

import asyncio
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml

from claude_agent_framework import create_session
from claude_agent_framework.core.roles import AgentInstanceConfig

# ============================================================================
# 业务配置 (定制点 1)
# ============================================================================

ARCHITECTURE = "mapreduce"
OUTPUT_DIR = Path(__file__).parent / "outputs"

# ============================================================================
# 业务定制函数 (定制点 2-4)
# ============================================================================


def build_agent_instances(config: dict) -> list[AgentInstanceConfig]:
    """定制点 2: 定义智能体实例"""
    models = config.get("models", {})
    mapreduce_config = config.get("mapreduce_config", {})
    return [
        AgentInstanceConfig(
            name=mapreduce_config.get("mapper", {}).get("name", "code_analyzer"),
            role="mapper",
            model=models.get("mapper", "haiku"),
            prompt_file=str(Path(__file__).parent / "prompts" / "code_analyzer.txt"),
        ),
        AgentInstanceConfig(
            name=mapreduce_config.get("reducer", {}).get("name", "report_aggregator"),
            role="reducer",
            model=models.get("reducer", "sonnet"),
            prompt_file=str(Path(__file__).parent / "prompts" / "report_aggregator.txt"),
        ),
    ]


def build_prompt(config: dict) -> str:
    """定制点 3: 构建任务提示词"""
    analysis_data = config.get("_analysis_data", {})
    codebase_path = analysis_data.get("codebase_path", ".")
    options = analysis_data.get("options", {})
    analysis_config = config.get("analysis", {})
    analysis_types = config.get("analysis_types", {})
    chunking_strategies = config.get("chunking_strategies", {})
    aggregation_rules = config.get("aggregation_rules", {})
    advanced = config.get("advanced", {})

    # 提取启用的分析类型
    enabled_analyses = []
    for analysis_type, type_config in analysis_types.items():
        if type_config.get("enabled", True):
            priority = type_config.get("priority", 2)
            checks = type_config.get("checks", [])
            enabled_analyses.append(
                f"- **{analysis_type.replace('_', ' ').title()}** (Priority {priority}): {', '.join(checks)}"
            )
    analyses_text = "\n".join(enabled_analyses)

    # 提取分块策略
    chunking_strategy = options.get("chunking_strategy", "by_module")
    strategy_info = chunking_strategies.get(chunking_strategy, {})

    # 提取过滤器
    exclude_paths = advanced.get("filters", {}).get("exclude_paths", [])
    include_extensions = advanced.get("filters", {}).get("include_extensions", [])

    # 构建去重和优先级信息
    dedup_config = aggregation_rules.get("deduplication", {})
    priority_criteria = aggregation_rules.get("prioritization", {}).get("criteria", {})

    return f"""# Codebase Analysis Task

## Analysis Target

**Codebase Path**: {codebase_path}

**Analysis Scope**:
- Include extensions: {", ".join(include_extensions) if include_extensions else "All"}
- Exclude paths: {", ".join(exclude_paths) if exclude_paths else "None"}
- Minimum confidence: {analysis_config.get("min_confidence", 0.7)}

## Analysis Configuration

Maximum parallel mappers: {analysis_config.get("max_parallel_mappers", 10)}
Target chunk size: {analysis_config.get("chunk_size", 50)} files per chunk
Aggregation strategy: {analysis_config.get("aggregation_strategy", "weighted")}

## Chunking Strategy

**Selected Strategy**: {chunking_strategy}
{strategy_info.get("description", "")}

**Benefits**:
{chr(10).join(f"- {b}" for b in strategy_info.get("benefits", [])) if strategy_info.get("benefits") else "- Efficient code analysis"}

## Analysis Types

{analyses_text}

## Aggregation Rules

**Deduplication**:
- Similarity threshold: {dedup_config.get("similarity_threshold", 0.85)}
- Merge strategy: {dedup_config.get("merge_strategy", "highest_severity")}

**Prioritization Criteria**:
{chr(10).join(f"- {k}: {v * 100}%" for k, v in priority_criteria.items()) if priority_criteria else "- Default prioritization"}

Analyze the codebase using MapReduce pattern to efficiently identify issues and generate recommendations.
"""


def build_result(config: dict, contents: list[str], session) -> dict:
    """定制点 4: 构建输出结果"""
    analysis_data = config.get("_analysis_data", {})
    codebase_path = analysis_data.get("codebase_path", ".")
    options = analysis_data.get("options", {})
    analysis_config = config.get("analysis", {})
    analysis_types = config.get("analysis_types", {})
    models = config.get("models", {})

    # 解析分析结果
    chunks_analyzed = extract_chunks_analyzed(contents)
    issues_found = extract_issues(contents)
    metrics = extract_metrics(contents)
    module_health = extract_module_health(contents)
    trends = extract_trends(contents)
    recommendations = extract_recommendations(contents)

    # 计算总分
    overall_score = calculate_overall_score(metrics, module_health)
    issue_summary = summarize_issues(issues_found)

    return {
        "analysis_id": str(uuid.uuid4()),
        "title": f"Codebase Analysis: {Path(codebase_path).name}",
        "summary": generate_summary(issue_summary, overall_score, chunks_analyzed),
        "codebase": {
            "path": codebase_path,
            "files_analyzed": metrics.get("total_files", 0),
            "lines_of_code": metrics.get("total_lines", 0),
            "languages": metrics.get("languages", []),
        },
        "execution": {
            "chunks_analyzed": chunks_analyzed,
            "parallel_mappers": len(chunks_analyzed),
            "chunking_strategy": options.get("chunking_strategy", "by_module"),
        },
        "issues": {
            "total": len(issues_found),
            "by_severity": issue_summary,
            "critical": [i for i in issues_found if i.get("severity") == "critical"],
            "high": [i for i in issues_found if i.get("severity") == "high"],
            "medium": [i for i in issues_found if i.get("severity") == "medium"],
            "low": [i for i in issues_found if i.get("severity") == "low"],
            "all_issues": issues_found,
        },
        "metrics": metrics,
        "module_health": module_health,
        "trends": trends,
        "recommendations": recommendations,
        "scores": {
            "overall": overall_score,
            "quality": metrics.get("quality_score", 0),
            "security": metrics.get("security_score", 0),
            "maintainability": metrics.get("maintainability_score", 0),
            "test_coverage": metrics.get("test_coverage", 0),
        },
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "architecture": ARCHITECTURE,
            "analysis_config": {
                "types_enabled": [t for t, cfg in analysis_types.items() if cfg.get("enabled")],
                "parallel_mappers": analysis_config.get("max_parallel_mappers", 10),
                "chunk_size": analysis_config.get("chunk_size", 50),
            },
            "models": models,
        },
    }


# ============================================================================
# 业务辅助函数
# ============================================================================


def extract_chunks_analyzed(results: list[str]) -> list[dict]:
    """提取分块分析信息"""
    chunks = []
    full_text = "\n".join(results)

    chunk_pattern = r"\*\*Chunk (\d+) Analysis\*\*.*?Files: \[([^\]]+)\]"
    matches = re.finditer(chunk_pattern, full_text, re.DOTALL)

    for match in matches:
        chunk_num = int(match.group(1))
        files_str = match.group(2)
        files = [f.strip().strip("'\"") for f in files_str.split(",")]

        chunks.append({
            "chunk_id": chunk_num,
            "files": files,
            "file_count": len(files),
        })

    if not chunks:
        chunks.append({
            "chunk_id": 1,
            "files": ["[Analyzed files]"],
            "file_count": 0,
        })

    return chunks


def extract_issues(results: list[str]) -> list[dict]:
    """提取所有问题"""
    issues = []
    full_text = "\n".join(results)

    # 格式 1: - [Severity] [Type] in [file]:[line] - [Description]
    issue_pattern1 = (
        r"-\s*\[(critical|high|medium|low)\]\s*\[(\w+)\]\s*in\s+([^:]+):(\d+)\s*-\s*(.+?)(?:\n|$)"
    )
    matches = re.finditer(issue_pattern1, full_text, re.IGNORECASE | re.MULTILINE)

    for match in matches:
        severity = match.group(1).lower()
        issue_type = match.group(2)
        file_path = match.group(3).strip()
        line_number = int(match.group(4))
        description = match.group(5).strip()

        issues.append({
            "severity": severity,
            "type": issue_type,
            "file": file_path,
            "line": line_number,
            "description": description,
            "confidence": "Medium",
            "fix_effort": "Medium",
        })

    # 格式 2: 顶部问题列表
    top_issue_pattern = r"\d+\.\s*(.+?)\s+in\s+([^:]+):(\d+)"
    matches = re.finditer(top_issue_pattern, full_text, re.MULTILINE)

    seen = set()
    for match in matches:
        description = match.group(1).strip()
        file_path = match.group(2).strip()
        line_number = int(match.group(3))

        key = (description, file_path, line_number)
        if key in seen:
            continue
        seen.add(key)

        severity = "medium"
        if "critical" in description.lower() or "security" in description.lower():
            severity = "critical"
        elif "high" in description.lower() or "performance" in description.lower():
            severity = "high"

        issues.append({
            "severity": severity,
            "type": "code_quality",
            "file": file_path,
            "line": line_number,
            "description": description,
            "confidence": "High",
            "fix_effort": "Medium",
        })

    return issues


def extract_metrics(results: list[str]) -> dict:
    """提取代码指标"""
    full_text = "\n".join(results)

    metrics = {
        "total_files": 0,
        "total_lines": 0,
        "average_complexity": 0,
        "max_complexity": 0,
        "test_coverage": 0,
        "quality_score": 0,
        "security_score": 0,
        "maintainability_score": 0,
        "languages": [],
    }

    patterns = {
        "total_files": r"Total files analyzed:\s*(\d+)",
        "total_lines": r"Total lines of code:\s*(\d+)",
        "average_complexity": r"Average complexity:\s*([\d.]+)",
        "test_coverage": r"Test coverage:\s*([\d.]+)%?",
        "quality_score": r"Quality score:\s*([\d.]+)",
        "security_score": r"Security score:\s*([\d.]+)",
        "maintainability_score": r"Maintainability score:\s*([\d.]+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            value = match.group(1)
            metrics[key] = float(value) if "." in value else int(value)

    return metrics


def extract_module_health(results: list[str]) -> list[dict]:
    """提取模块健康度"""
    modules = []
    full_text = "\n".join(results)

    if "**Module Health**" in full_text:
        module_section_start = full_text.index("**Module Health**")
        module_section = full_text[module_section_start : module_section_start + 2000]

        module_pattern = r"-\s*([^:]+):\s*(\d+)/100"
        matches = re.finditer(module_pattern, module_section)

        for match in matches:
            module_name = match.group(1).strip()
            score = int(match.group(2))

            modules.append({
                "name": module_name,
                "score": score,
                "status": (
                    "healthy"
                    if score >= 80
                    else "needs_attention"
                    if score >= 60
                    else "critical"
                ),
            })

    return modules


def extract_trends(results: list[str]) -> dict:
    """提取趋势信息"""
    full_text = "\n".join(results)

    trends = {
        "new_issues": 0,
        "resolved_issues": 0,
        "net_change": 0,
    }

    patterns = {
        "new_issues": r"New issues introduced:\s*(\d+)",
        "resolved_issues": r"Issues resolved:\s*(\d+)",
        "net_change": r"Net change:\s*([+-]?\d+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            value = match.group(1)
            trends[key] = int(value.replace("+", "").replace("-", ""))
            if "-" in value:
                trends[key] = -trends[key]

    return trends


def extract_recommendations(results: list[str]) -> list[dict]:
    """提取优先建议"""
    recommendations = []
    full_text = "\n".join(results)

    if "**Top Recommendations**" in full_text or "**Recommendations**" in full_text:
        rec_pattern = (
            r"\d+\.\s*(?:\[Priority \d+\]\s*)?(.+?)(?:\n\s+Reason:|Effort:|Impact:|\d+\.|$)"
        )
        matches = re.finditer(rec_pattern, full_text, re.DOTALL)

        for match in matches:
            action = match.group(1).strip()
            if action and len(action) > 10:
                recommendations.append({
                    "action": action,
                    "priority": "high",
                    "effort": "medium",
                    "impact": "high",
                })

    return recommendations[:10]


def calculate_overall_score(metrics: dict, module_health: list[dict]) -> int:
    """计算总体健康分数"""
    quality = metrics.get("quality_score", 70)
    security = metrics.get("security_score", 70)
    maintainability = metrics.get("maintainability_score", 70)
    coverage = metrics.get("test_coverage", 0)

    module_avg = 70
    if module_health:
        module_avg = sum(m["score"] for m in module_health) / len(module_health)

    overall = (
        quality * 0.25 + security * 0.3 + maintainability * 0.2 + coverage * 0.15 + module_avg * 0.1
    )

    return int(overall)


def summarize_issues(issues: list[dict]) -> dict:
    """按严重性汇总问题"""
    summary = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    for issue in issues:
        severity = issue.get("severity", "medium").lower()
        if severity in summary:
            summary[severity] += 1

    return summary


def generate_summary(issue_summary: dict, overall_score: int, chunks: list) -> str:
    """生成执行摘要"""
    total_issues = sum(issue_summary.values())
    critical = issue_summary.get("critical", 0)
    high = issue_summary.get("high", 0)

    status = (
        "healthy"
        if overall_score >= 80
        else "needs attention"
        if overall_score >= 60
        else "critical"
    )

    summary = (
        f"Analyzed {len(chunks)} chunks with overall health score of {overall_score}/100 ({status}). "
        f"Found {total_issues} total issues: {critical} critical, {high} high priority. "
    )

    if critical > 0:
        summary += f"Immediate action required on {critical} critical security/quality issues."
    elif high > 0:
        summary += f"Should address {high} high-priority issues in next sprint."
    else:
        summary += "No critical issues found. Focus on continuous improvement."

    return summary


# ============================================================================
# 公共主线 (所有示例相同)
# ============================================================================


def load_config() -> dict:
    """加载 YAML 配置文件"""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_result(result: dict, filename: str) -> Path:
    """保存结果为 JSON 文件"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{filename}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    return output_path


def extract_content(msg) -> str | None:
    """从 SDK 消息中提取文本内容"""
    if hasattr(msg, "result"):
        return msg.result
    if hasattr(msg, "content"):
        texts = [b.text for b in msg.content if hasattr(b, "text")]
        return "\n".join(texts) if texts else None
    return None


async def run_task(config: dict) -> dict:
    """执行任务的标准流程"""
    prompt = build_prompt(config)
    agent_instances = build_agent_instances(config)
    models = config.get("models", {})

    session = create_session(
        ARCHITECTURE,
        model=models.get("lead", "sonnet"),
        agent_instances=agent_instances,
        prompts_dir=Path(__file__).parent / "prompts",
        template_vars=config.get("template_vars", {}),
        verbose=False,
    )

    contents = []
    try:
        async for msg in session.run(prompt):
            if content := extract_content(msg):
                contents.append(content)
    finally:
        await session.teardown()

    return build_result(config, contents, session)


async def main():
    """入口函数"""
    try:
        config = load_config()

        # 业务特定: 设置分析数据
        codebase_path = str(Path(__file__).parent.parent.parent)
        options = {
            "chunking_strategy": "by_module",
            "focus_areas": ["security", "code_quality"],
        }

        config["_analysis_data"] = {
            "codebase_path": codebase_path,
            "options": options,
        }

        print(f"Analyzing codebase: {codebase_path}\n")

        result = await run_task(config)

        output_path = save_result(result, f"{ARCHITECTURE}_result")

        print(f"Analysis ID: {result['analysis_id']}")
        print(f"Overall Score: {result['scores']['overall']}/100")
        print(f"Issues Found: {result['issues']['total']}")
        print(f"   - Critical: {len(result['issues']['critical'])}")
        print(f"   - High: {len(result['issues']['high'])}")
        print(f"   - Medium: {len(result['issues']['medium'])}")
        print(f"   - Low: {len(result['issues']['low'])}")
        print(f"\n✅ Complete! Output: {output_path}")
        print(f"📊 Summary: {result.get('summary', 'N/A')}")

    except Exception as e:
        print(f"❌ Error: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
