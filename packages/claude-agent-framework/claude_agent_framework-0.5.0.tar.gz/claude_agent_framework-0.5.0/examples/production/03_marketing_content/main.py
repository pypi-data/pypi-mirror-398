#!/usr/bin/env python3
"""营销内容优化 - 使用 Critic-Actor 架构的示例"""

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

ARCHITECTURE = "critic_actor"
OUTPUT_DIR = Path(__file__).parent / "outputs"

# ============================================================================
# 业务定制函数 (定制点 2-4)
# ============================================================================


def build_agent_instances(config: dict) -> list[AgentInstanceConfig]:
    """定制点 2: 定义智能体实例"""
    models = config.get("models", {})
    return [
        AgentInstanceConfig(
            name="content_creator",
            role="actor",
            model=models.get("actor", "sonnet"),
        ),
        AgentInstanceConfig(
            name="brand_reviewer",
            role="critic",
            model=models.get("critic", "sonnet"),
        ),
    ]


def build_prompt(config: dict) -> str:
    """定制点 3: 构建任务提示词"""
    content_config = config["content"]
    brand_config = config["brand"]
    evaluation_config = config["evaluation"]
    iteration_config = config["iteration"]

    # 评估标准
    criteria_sections = []
    for category, details in evaluation_config.items():
        if category in ["seo", "engagement", "brand_consistency", "accuracy"]:
            weight = details["weight"]
            criteria = details["criteria"]
            criteria_list = "\n".join(f"  - {c}" for c in criteria)
            criteria_sections.append(
                f"**{category.replace('_', ' ').title()}** (Weight: {weight}%):\n{criteria_list}"
            )

    # 品牌指南
    brand_text = f"""
**Brand Voice**: {brand_config["voice"]}
**Tone Attributes**: {", ".join(brand_config["tone"])}
**Company Values**: {", ".join(brand_config["values"])}
**Prohibited Phrases**: {", ".join(brand_config.get("prohibited_phrases", []))}
"""

    # 目标长度和关键词
    target_length = content_config.get("target_length", {})
    length_text = ""
    if target_length:
        min_words = target_length.get("min_words", "")
        max_words = target_length.get("max_words", "")
        if min_words and max_words:
            length_text = f"\n**Target Length**: {min_words}-{max_words} words"

    keywords = content_config.get("keywords", [])
    keywords_text = f"\n**SEO Keywords**: {', '.join(keywords)}" if keywords else ""

    return f"""Optimize marketing content using iterative Critic-Actor pattern.

## Content Brief

**Content Type**: {content_config["type"]}
{length_text}
{keywords_text}

**Brief**:
{content_config["brief"]}

## Brand Guidelines
{brand_text}

## Evaluation Criteria
{chr(10).join(criteria_sections)}

## Iteration Settings
- Max iterations: {iteration_config["max_iterations"]}
- Quality threshold: {iteration_config["quality_threshold"]}
- Minimum improvement: {iteration_config.get("min_improvement", 5)}%

Deliver optimized content meeting the quality threshold.
"""


def build_result(config: dict, contents: list[str], session) -> dict:
    """定制点 4: 构建输出结果"""
    content_config = config["content"]
    iteration_config = config["iteration"]

    # 解析结果
    final_content, iterations, final_score = parse_optimization_results(contents)

    return {
        "title": "Marketing Content Optimization Report",
        "summary": generate_summary(iterations, final_score, content_config),
        "content_type": content_config["type"],
        "final_content": final_content,
        "final_score": final_score,
        "iterations": iterations,
        "metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "architecture": ARCHITECTURE,
            "num_iterations": len(iterations),
            "quality_threshold": iteration_config["quality_threshold"],
        },
    }


# ============================================================================
# 业务辅助函数
# ============================================================================


def parse_optimization_results(results: list[str]) -> tuple[str, list[dict], float]:
    """解析优化结果"""
    full_text = "\n".join(results)
    iterations = []
    iteration_blocks = full_text.split("=== ITERATION")

    for block in iteration_blocks[1:]:
        if not block.strip():
            continue
        lines = block.split("\n")
        iteration_num = int(lines[0].strip().split()[0]) if lines[0].strip() else len(iterations) + 1

        content_start = block.find("**Content**:")
        content_end = block.find("**Critic Evaluation**:")
        content = block[content_start + 12:content_end].strip() if content_start != -1 and content_end != -1 else ""

        overall_score = 0.0
        score_match = block.find("**Overall Score**:")
        if score_match != -1:
            try:
                score_line = block[score_match:].split("\n")[0]
                overall_score = float(score_line.split(":")[1].split("/")[0].strip())
            except (IndexError, ValueError):
                pass

        iterations.append({"iteration": iteration_num, "content": content, "overall_score": overall_score})

    final_content = ""
    final_marker = full_text.find("=== FINAL CONTENT ===")
    if final_marker != -1:
        final_content = full_text[final_marker + 21:].strip()
    elif iterations:
        final_content = iterations[-1]["content"]

    final_score = iterations[-1]["overall_score"] if iterations else 0.0
    return final_content, iterations, final_score


def generate_summary(iterations: list[dict], final_score: float, content_config: dict) -> str:
    """生成摘要"""
    if not iterations:
        return "No iterations completed"
    initial_score = iterations[0]["overall_score"]
    improvement = final_score - initial_score
    return f"Optimized {content_config['type']} through {len(iterations)} iteration(s). Initial: {initial_score}/100, Final: {final_score}/100, Improvement: +{improvement:.1f}"


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
