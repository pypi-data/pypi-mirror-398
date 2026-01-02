#!/usr/bin/env python3
"""竞争情报分析 - 使用 Research 架构的示例"""

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

ARCHITECTURE = "research"
OUTPUT_DIR = Path(__file__).parent / "outputs"

# ============================================================================
# 业务定制函数 (定制点 2-4)
# ============================================================================


def build_agent_instances(config: dict) -> list[AgentInstanceConfig]:
    """定制点 2: 定义智能体实例"""
    models = config.get("models", {})
    agent_model = models.get("agents", "haiku")
    competitors = config.get("competitors", [])

    agent_instances = []

    # Worker 角色: 每个 competitor 创建一个专属 researcher
    for competitor in competitors:
        name = competitor["name"].lower().replace(" ", "_")
        agent_instances.append(
            AgentInstanceConfig(
                name=f"researcher_{name}",
                role="worker",
                description=f"Research {competitor['name']} ({competitor['website']})",
                tools=["Write", "Read"],
                prompt_file="researcher.txt",
                model=agent_model,
                metadata={"competitor": competitor},
            )
        )

    # Processor 角色: 数据分析师（可选，0-1）
    if config.get("output", {}).get("include_charts", False):
        agent_instances.append(
            AgentInstanceConfig(
                name="data_analyst",
                role="processor",
                description="Analyze research data and generate visualizations",
                tools=["Glob", "Bash"],
                prompt_file="data_analyst.txt",
                model=agent_model,
            )
        )

    # Synthesizer 角色: 报告撰写者（必须恰好 1 个）
    agent_instances.append(
        AgentInstanceConfig(
            name="report_writer",
            role="synthesizer",
            description="Generate comprehensive competitive intelligence report",
            tools=["Read", "Glob"],
            prompt_file="report_writer.txt",
            model=agent_model,
        )
    )

    return agent_instances


def build_prompt(config: dict) -> str:
    """定制点 3: 构建任务提示词"""
    competitors = config["competitors"]
    dimensions = config["analysis_dimensions"]

    competitor_list = "\n".join(
        f"- {c['name']}: {c['website']}\n  Focus: {', '.join(c.get('focus_areas', ['General analysis']))}"
        for c in competitors
    )
    dimension_list = "\n".join(f"- {dim}" for dim in dimensions)

    return f"""Analyze the following competitors:

{competitor_list}

Analysis dimensions:
{dimension_list}

Deliver a comprehensive competitive intelligence report with comparative analysis and strategic recommendations.
"""


def build_result(config: dict, contents: list[str], session) -> dict:
    """定制点 4: 构建输出结果"""
    competitors = config["competitors"]
    dimensions = config["analysis_dimensions"]

    return {
        "title": "Competitive Intelligence Analysis Report",
        "summary": f"Analyzed {len(competitors)} competitors across {len(dimensions)} dimensions",
        "competitors": [c["name"] for c in competitors],
        "dimensions": dimensions,
        "content": "\n\n".join(contents) if contents else "No content generated",
        "metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "architecture": ARCHITECTURE,
            "total_competitors": len(competitors),
            "total_dimensions": len(dimensions),
        },
    }


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
        result = await run_task(config)

        output_path = save_result(result, f"{ARCHITECTURE}_result")

        print(f"✅ Complete! Output: {output_path}")
        print(f"📊 Summary: {result.get('summary', 'N/A')}")

    except Exception as e:
        print(f"❌ Error: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
