#!/usr/bin/env python3
"""IT 技术支持 - 使用 Specialist Pool 架构的示例"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

import yaml

from claude_agent_framework import create_session
from claude_agent_framework.core.roles import AgentInstanceConfig

# ============================================================================
# 业务配置 (定制点 1)
# ============================================================================

ARCHITECTURE = "specialist_pool"
OUTPUT_DIR = Path(__file__).parent / "outputs"

# ============================================================================
# 业务定制函数 (定制点 2-4)
# ============================================================================


def build_agent_instances(config: dict) -> list[AgentInstanceConfig]:
    """定制点 2: 定义智能体实例"""
    models = config.get("models", {})
    issue_data = config.get("_issue_data", {})
    selected_specialists = issue_data.get("specialists", [])

    return [
        AgentInstanceConfig(
            name=specialist["name"],
            role="specialist",
            model=models.get("specialists", "haiku"),
            prompt_file=str(Path(__file__).parent / "prompts" / "specialist.txt"),
        )
        for specialist in selected_specialists
    ]


def build_prompt(config: dict) -> str:
    """定制点 3: 构建任务提示词"""
    issue_data = config.get("_issue_data", {})
    response_template = config.get("response_template", {})

    title = issue_data.get("title", "")
    description = issue_data.get("description", "")
    urgency = issue_data.get("urgency", "medium")
    sla_hours = issue_data.get("sla_hours", 24)
    specialists = issue_data.get("specialists", [])

    specialist_list = "\n".join(f"- **{s['name']}**: {s['description']}" for s in specialists)

    requirements = []
    if response_template.get("include_diagnosis", True):
        requirements.append("Root cause diagnosis")
    if response_template.get("include_steps", True):
        requirements.append("Step-by-step resolution steps")
    if response_template.get("include_prevention", True):
        requirements.append("Prevention recommendations")

    return f"""Resolve an IT support issue.

## Issue Details

**Title**: {title}

**Description**:
{description}

**Urgency**: {urgency.upper()} (SLA: {sla_hours} hours)

## Available Specialists
{specialist_list}

## Required Response Components
{chr(10).join(f"- {req}" for req in requirements)}

Provide specialist analysis and a consolidated solution with actionable steps.
"""


def build_result(config: dict, contents: list[str], session) -> dict:
    """定制点 4: 构建输出结果"""
    issue_data = config.get("_issue_data", {})
    routing_config = config.get("routing", {})
    specialists = issue_data.get("specialists", [])

    # 解析专家响应
    specialist_responses = parse_specialist_responses(contents, specialists)
    consolidated = extract_consolidated_solution(contents)

    return {
        "title": f"IT Support Resolution: {issue_data.get('title', '')}",
        "summary": f"Issue resolved with {issue_data.get('urgency', 'medium')} urgency. Consulted {len(specialists)} specialist(s).",
        "issue": {
            "title": issue_data.get("title", ""),
            "description": issue_data.get("description", ""),
            "urgency": issue_data.get("urgency", "medium"),
            "sla_hours": issue_data.get("sla_hours", 24),
        },
        "routing": {
            "specialists": [s["name"] for s in specialists],
            "strategy": routing_config.get("strategy", "keyword_match"),
        },
        "specialist_responses": specialist_responses,
        "consolidated_solution": consolidated,
        "metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "architecture": ARCHITECTURE,
            "num_specialists": len(specialists),
        },
    }


# ============================================================================
# 业务辅助函数
# ============================================================================


def categorize_urgency(title: str, description: str, config: dict) -> tuple[str, int]:
    """分类紧急程度"""
    text = f"{title} {description}".lower()
    urgency_levels = config.get("categorization", {}).get("urgency_levels", [])

    for level in urgency_levels:
        if any(kw.lower() in text for kw in level.get("keywords", [])):
            return level["name"], level["sla_hours"]
    return "medium", 24


def route_to_specialists(title: str, description: str, config: dict) -> list[dict]:
    """路由到专家"""
    text = f"{title} {description}".lower()
    specialists_config = config.get("specialists", [])
    routing = config.get("routing", {})
    min_matches = routing.get("min_keyword_matches", 1)
    max_specialists = routing.get("max_specialists", 3)

    scored = []
    for spec in specialists_config:
        if spec.get("priority", 5) >= 5:
            continue
        matches = sum(1 for kw in spec.get("keywords", []) if kw.lower() in text)
        if matches >= min_matches:
            scored.append({"specialist": spec, "matches": matches, "priority": spec.get("priority", 5)})

    scored.sort(key=lambda x: (-x["matches"], x["priority"]))
    selected = [item["specialist"] for item in scored[:max_specialists]]

    if not selected and specialists_config:
        # Fallback
        fallback = max(specialists_config, key=lambda s: s.get("priority", 0))
        selected = [fallback]

    return selected


def parse_specialist_responses(results: list[str], specialists: list[dict]) -> list[dict]:
    """解析专家响应"""
    full_text = "\n".join(results)
    responses = []

    for spec in specialists:
        name = spec["name"]
        for marker in [f"### {name}", f"**{name}**"]:
            start = full_text.find(marker)
            if start != -1:
                end = len(full_text)
                for other in specialists:
                    if other["name"] != name:
                        pos = full_text.find(f"### {other['name']}", start + 1)
                        if pos != -1 and pos < end:
                            end = pos
                consol_pos = full_text.find("### Consolidated", start + 1)
                if consol_pos != -1 and consol_pos < end:
                    end = consol_pos

                responses.append({"specialist": name, "response": full_text[start:end].strip()})
                break

    return responses


def extract_consolidated_solution(results: list[str]) -> str:
    """提取综合解决方案"""
    full_text = "\n".join(results)
    marker = "### Consolidated Solution"
    start = full_text.find(marker)
    return full_text[start:].strip() if start != -1 else "See individual specialist responses."


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
    # 业务特定: 从示例问题获取输入
    example_issues = config.get("example_issues", [])
    if example_issues:
        issue = example_issues[0]
        title, description = issue["title"], issue["description"]
    else:
        title, description = "General IT Issue", "Please provide issue details in config."

    # 路由和分类
    urgency, sla_hours = categorize_urgency(title, description, config)
    specialists = route_to_specialists(title, description, config)

    config["_issue_data"] = {
        "title": title,
        "description": description,
        "urgency": urgency,
        "sla_hours": sla_hours,
        "specialists": specialists,
    }

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
