#!/usr/bin/env python3
"""PR 代码审查 - 使用 Pipeline 架构的示例"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from subprocess import run as subprocess_run

import yaml

from claude_agent_framework import create_session
from claude_agent_framework.core.roles import AgentInstanceConfig

# ============================================================================
# 业务配置 (定制点 1)
# ============================================================================

ARCHITECTURE = "pipeline"
OUTPUT_DIR = Path(__file__).parent / "outputs"

# ============================================================================
# 业务定制函数 (定制点 2-4)
# ============================================================================


def build_agent_instances(config: dict) -> list[AgentInstanceConfig]:
    """定制点 2: 定义智能体实例"""
    models = config.get("models", {})
    stages = config["stages"]

    return [
        AgentInstanceConfig(
            name=stage["name"],
            role="stage",
            model=models.get("agents", "haiku"),
            prompt_file=str(Path(__file__).parent / "prompts" / "stage_executor.txt"),
        )
        for stage in stages
    ]


def build_prompt(config: dict) -> str:
    """定制点 3: 构建任务提示词"""
    stages = config["stages"]
    pr_data = config.get("_pr_data", {})  # 由 run_task 注入
    analysis_config = config.get("analysis", {})

    stage_list = "\n".join(
        f"{i + 1}. **{stage['name']}**: {stage['description']}"
        for i, stage in enumerate(stages)
    )

    thresholds = "\n".join(
        f"- {key.replace('_', ' ').title()}: {value}"
        for key, value in analysis_config.items()
    )

    return f"""Review the following Pull Request.

## PR Summary
Files Changed: {pr_data.get("files_changed", 0)}
Lines Added: {pr_data.get("lines_added", 0)}
Lines Deleted: {pr_data.get("lines_deleted", 0)}

## Review Stages
{stage_list}

## Quality Thresholds
{thresholds}

Deliver a comprehensive code review report with stage-by-stage analysis and recommendations.
"""


def build_result(config: dict, contents: list[str], session) -> dict:
    """定制点 4: 构建输出结果"""
    stages = config["stages"]
    pr_data = config.get("_pr_data", {})
    results_text = "\n".join(contents)

    # 统计结果
    passed = results_text.count("✅")
    warnings = results_text.count("⚠️")
    failed = results_text.count("❌")

    # 确定状态
    if "❌ FAIL" in results_text:
        status = "CHANGES_REQUESTED"
    elif "⚠️ WARNING" in results_text:
        status = "APPROVED_WITH_COMMENTS"
    else:
        status = "APPROVED"

    return {
        "title": "Pull Request Code Review Report",
        "summary": f"Completed {len(stages)} review stages: {passed} passed, {warnings} warnings, {failed} failed",
        "pr_info": pr_data,
        "stages": [{"name": s["name"], "description": s["description"], "status": "completed"} for s in stages],
        "overall_status": status,
        "recommendations": [
            "Review all identified issues",
            "Address critical and high-priority items first",
            "Run tests after making changes",
            "Update documentation if needed",
        ],
        "metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "architecture": ARCHITECTURE,
            "total_stages": len(stages),
            "files_changed": pr_data.get("files_changed", 0),
            "lines_added": pr_data.get("lines_added", 0),
            "lines_deleted": pr_data.get("lines_deleted", 0),
        },
    }


# ============================================================================
# 业务辅助函数
# ============================================================================


def get_pr_changes(pr_source: dict) -> dict:
    """获取 PR 变更信息"""
    if "pr_url" in pr_source:
        return {
            "pr_url": pr_source["pr_url"],
            "files_changed": 15,
            "lines_added": 250,
            "lines_deleted": 80,
            "diff": "Mock diff content",
        }
    elif "local_path" in pr_source:
        try:
            result = subprocess_run(
                ["git", "diff", "--shortstat", pr_source.get("base_branch", "main")],
                capture_output=True, text=True, cwd=pr_source["local_path"],
            )
            stats = result.stdout.strip()
            files_changed = lines_added = lines_deleted = 0

            if stats:
                parts = stats.split(",")
                if len(parts) >= 1 and "file" in parts[0]:
                    files_changed = int(parts[0].split()[0])
                if len(parts) >= 2 and "insertion" in parts[1]:
                    lines_added = int(parts[1].split()[0])
                if len(parts) >= 3 and "deletion" in parts[2]:
                    lines_deleted = int(parts[2].split()[0])

            diff_result = subprocess_run(
                ["git", "diff", pr_source.get("base_branch", "main")],
                capture_output=True, text=True, cwd=pr_source["local_path"],
            )

            return {
                "local_path": pr_source["local_path"],
                "base_branch": pr_source.get("base_branch", "main"),
                "files_changed": files_changed,
                "lines_added": lines_added,
                "lines_deleted": lines_deleted,
                "diff": diff_result.stdout[:5000],
            }
        except Exception:
            return {"local_path": pr_source["local_path"], "files_changed": 0, "lines_added": 0, "lines_deleted": 0, "diff": ""}
    else:
        raise ValueError("PR source must specify either 'pr_url' or 'local_path'")


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
    # 业务特定: 获取 PR 信息并注入配置
    pr_data = get_pr_changes(config["pr_source"])
    config["_pr_data"] = pr_data

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
        result = await run_task(config)

        output_path = save_result(result, f"{ARCHITECTURE}_result")

        print(f"✅ Complete! Output: {output_path}")
        print(f"📊 Summary: {result.get('summary', 'N/A')}")

    except Exception as e:
        print(f"❌ Error: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
