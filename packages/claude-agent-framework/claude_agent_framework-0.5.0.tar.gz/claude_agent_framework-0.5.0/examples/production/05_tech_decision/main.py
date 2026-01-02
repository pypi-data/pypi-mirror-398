#!/usr/bin/env python3
"""技术决策支持 - 使用 Debate 架构的示例"""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path

import yaml

from claude_agent_framework import create_session
from claude_agent_framework.core.roles import AgentInstanceConfig

# ============================================================================
# 业务配置 (定制点 1)
# ============================================================================

ARCHITECTURE = "debate"
OUTPUT_DIR = Path(__file__).parent / "outputs"

# ============================================================================
# 业务定制函数 (定制点 2-4)
# ============================================================================


def build_agent_instances(config: dict) -> list[AgentInstanceConfig]:
    """定制点 2: 定义智能体实例"""
    models = config.get("models", {})
    return [
        AgentInstanceConfig(
            name="solution_advocate",
            role="proponent",
            model=models.get("proponent", "sonnet"),
        ),
        AgentInstanceConfig(
            name="risk_analyst",
            role="opponent",
            model=models.get("opponent", "sonnet"),
        ),
        AgentInstanceConfig(
            name="tech_lead",
            role="judge",
            model=models.get("judge", "sonnet"),
        ),
    ]


def build_prompt(config: dict) -> str:
    """定制点 3: 构建任务提示词"""
    decision_data = config.get("_decision_data", {})
    decision_question = decision_data.get("question", "")
    context = decision_data.get("context", {})
    debate_config = config.get("debate_config", {})
    evaluation_criteria = config.get("evaluation_criteria", {})

    # 提取上下文
    options = context.get("options", [])
    requirements = context.get("requirements", [])
    constraints = context.get("constraints", {})
    current_situation = context.get("current_situation", "")

    # 构建评估标准描述
    criteria_desc = []
    for criterion, cfg in evaluation_criteria.items():
        weight = cfg.get("weight", 0)
        sub_criteria = cfg.get("sub_criteria", [])
        criteria_desc.append(
            f"- **{criterion.replace('_', ' ').title()}** ({weight}%): " + ", ".join(sub_criteria)
        )
    criteria_text = "\n".join(criteria_desc)

    rounds = debate_config.get("rounds", 3)

    return f"""# Tech Decision Debate

## Decision Question

{decision_question}

## Current Situation

{current_situation if current_situation else "Not specified"}

## Options Being Evaluated

{chr(10).join(f"- **Option {i + 1}**: {opt}" for i, opt in enumerate(options))}

## Requirements

{chr(10).join(f"- {req}" for req in requirements)}

## Constraints

Budget: {constraints.get("budget", "Not specified")}
Timeline: {constraints.get("timeline", "Not specified")}
Team Size: {constraints.get("team_size", "Not specified")}
Existing Tech Stack: {constraints.get("tech_stack", "Not specified")}

## Debate Configuration

Rounds: {rounds}
Format: {debate_config.get("format", "oxford_style")}

## Evaluation Criteria (Weighted)

{criteria_text}

Conduct a structured debate and provide a final recommendation with implementation roadmap.
"""


def build_result(config: dict, contents: list[str], session) -> dict:
    """定制点 4: 构建输出结果"""
    decision_data = config.get("_decision_data", {})
    decision_question = decision_data.get("question", "")
    context = decision_data.get("context", {})
    debate_config = config.get("debate_config", {})
    evaluation_criteria = config.get("evaluation_criteria", {})
    decision_config = config.get("decision", {})
    participants_config = config.get("participants", {})
    models = config.get("models", {})

    # 解析辩论结果
    debate_transcript = parse_debate_transcript(contents)
    evaluation_scores = extract_evaluation_scores(contents, evaluation_criteria)
    final_recommendation = extract_final_recommendation(contents)
    risk_assessment = extract_risk_assessment(contents)
    implementation_roadmap = extract_implementation_roadmap(contents)

    return {
        "decision_id": str(uuid.uuid4()),
        "title": f"Tech Decision: {decision_question}",
        "summary": generate_summary(decision_question, final_recommendation, evaluation_scores),
        "decision": {
            "question": decision_question,
            "context": context,
            "decision_type": decision_config.get("decision_type", "technology_selection"),
        },
        "debate": {
            "rounds": debate_config.get("rounds", 3),
            "transcript": debate_transcript,
            "format": debate_config.get("format", "oxford_style"),
        },
        "evaluation": {
            "criteria": evaluation_criteria,
            "scores": evaluation_scores,
            "overall_score": calculate_overall_score(evaluation_scores, evaluation_criteria),
        },
        "recommendation": final_recommendation,
        "risk_assessment": risk_assessment,
        "implementation_roadmap": implementation_roadmap,
        "metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "architecture": ARCHITECTURE,
            "config": {
                "rounds": debate_config.get("rounds"),
                "participants": list(participants_config.keys()),
                "models": models,
            },
        },
    }


# ============================================================================
# 业务辅助函数
# ============================================================================


def parse_debate_transcript(results: list[str]) -> list[dict]:
    """解析辩论记录"""
    full_text = "\n".join(results)
    transcript = []
    rounds = []
    current_round = None

    for line in full_text.split("\n"):
        if line.startswith("### Round"):
            if current_round:
                rounds.append(current_round)
            current_round = {"round": line, "content": []}
        elif current_round is not None:
            current_round["content"].append(line)

    if current_round:
        rounds.append(current_round)

    for round_data in rounds:
        round_text = "\n".join(round_data["content"])
        proponent_text = ""
        opponent_text = ""

        if "**[Proponent]**" in round_text:
            parts = round_text.split("**[Proponent]**")
            if len(parts) > 1:
                proponent_part = parts[1].split("**[Opponent]**")[0]
                proponent_text = proponent_part.strip()

        if "**[Opponent]**" in round_text:
            parts = round_text.split("**[Opponent]**")
            if len(parts) > 1:
                opponent_text = parts[1].strip()

        transcript.append({
            "round": round_data["round"],
            "proponent": proponent_text,
            "opponent": opponent_text,
        })

    return transcript


def extract_evaluation_scores(results: list[str], evaluation_criteria: dict) -> dict:
    """提取评估分数"""
    full_text = "\n".join(results)
    scores = {}

    if "### Evaluation Scorecard" in full_text:
        scorecard_start = full_text.index("### Evaluation Scorecard")
        scorecard_section = full_text[scorecard_start:]

        for criterion in evaluation_criteria.keys():
            criterion_title = criterion.replace("_", " ").title()
            if criterion_title in scorecard_section:
                scores[criterion] = {
                    "weight": evaluation_criteria[criterion].get("weight", 0),
                    "scores": {},
                }

    return scores if scores else {"note": "Scores not found in standard format"}


def extract_final_recommendation(results: list[str]) -> dict:
    """提取最终建议"""
    full_text = "\n".join(results)
    recommendation = {
        "recommended_option": "Not determined",
        "justification": "",
        "strengths": [],
        "risks": [],
    }

    if "### Final Recommendation" in full_text:
        rec_start = full_text.index("### Final Recommendation")
        rec_section = full_text[rec_start : rec_start + 2000]

        if "**Recommended Option**:" in rec_section:
            option_line = rec_section.split("**Recommended Option**:")[1].split("\n")[0]
            recommendation["recommended_option"] = option_line.strip()

        if "**Justification**:" in rec_section:
            just_start = rec_section.index("**Justification**:")
            just_end = rec_section.find("**Key Strengths**:", just_start)
            if just_end == -1:
                just_end = len(rec_section)
            justification = rec_section[just_start:just_end]
            recommendation["justification"] = justification.replace("**Justification**:", "").strip()

    return recommendation


def extract_risk_assessment(results: list[str]) -> list[dict]:
    """提取风险评估"""
    full_text = "\n".join(results)
    risks = []

    if "**Acknowledged Risks**:" in full_text:
        risks_start = full_text.index("**Acknowledged Risks**:")
        risks_section = full_text[risks_start : risks_start + 1000]

        lines = risks_section.split("\n")
        for line in lines:
            if line.strip().startswith(("1.", "2.", "3.", "4.", "5.")):
                risk_text = line.strip()[3:].strip()
                risks.append({"risk": risk_text, "severity": "Medium", "mitigation": ""})

    return risks if risks else [{"risk": "No risks explicitly identified", "severity": "N/A"}]


def extract_implementation_roadmap(results: list[str]) -> dict:
    """提取实施路线图"""
    full_text = "\n".join(results)
    roadmap = {"phases": [], "success_metrics": []}

    if "**Implementation Roadmap**:" in full_text:
        roadmap_start = full_text.index("**Implementation Roadmap**:")
        roadmap_section = full_text[roadmap_start : roadmap_start + 2000]

        for phase_name in ["Phase 1", "Phase 2", "Phase 3"]:
            if phase_name in roadmap_section:
                phase_start = roadmap_section.index(phase_name)
                phase_end = roadmap_section.find("Phase", phase_start + 1)
                if phase_end == -1:
                    phase_end = roadmap_section.find("**Success Metrics**:", phase_start)
                if phase_end == -1:
                    phase_end = len(roadmap_section)

                phase_text = roadmap_section[phase_start:phase_end]
                actions = [
                    line.strip()[2:].strip()
                    for line in phase_text.split("\n")
                    if line.strip().startswith("-")
                ]

                roadmap["phases"].append({"phase": phase_name, "actions": actions})

    return roadmap


def generate_summary(decision_question: str, final_recommendation: dict, evaluation_scores: dict) -> str:
    """生成执行摘要"""
    recommended = final_recommendation.get("recommended_option", "Not determined")
    justification = final_recommendation.get("justification", "")

    if justification:
        first_sentence = justification.split(".")[0] + "."
    else:
        first_sentence = "Decision evaluated through structured debate."

    return f"Evaluated: {decision_question}. Recommendation: {recommended}. {first_sentence}"


def calculate_overall_score(evaluation_scores: dict, evaluation_criteria: dict) -> float:
    """计算加权总分"""
    return 0.0


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

        # 业务特定: 设置决策数据
        decision_question = "Should we migrate from REST API to GraphQL?"
        context = {
            "options": [
                "Migrate entire API to GraphQL",
                "Hybrid approach (GraphQL for new, REST for existing)",
                "Stay with REST and enhance with better documentation",
            ],
            "requirements": [
                "Reduce number of API calls from mobile app",
                "Improve developer experience",
                "Maintain backward compatibility",
                "Support real-time updates",
            ],
            "constraints": {
                "budget": "$50,000",
                "timeline": "6 months",
                "team_size": "5 backend engineers",
                "tech_stack": "Node.js, PostgreSQL, React Native mobile app",
            },
            "current_situation": """
            Our REST API has 150+ endpoints. Mobile app makes 20+ API calls to render a single screen.
            Team experienced with REST but no GraphQL experience.
            Customers complain about slow mobile app performance.
            """,
        }

        config["_decision_data"] = {
            "question": decision_question,
            "context": context,
        }

        print(f"Evaluating decision: {decision_question}\n")

        result = await run_task(config)

        output_path = save_result(result, f"{ARCHITECTURE}_result")

        print(f"Decision ID: {result['decision_id']}")
        print(f"Recommendation: {result['recommendation']['recommended_option']}")
        print(f"\n✅ Complete! Output: {output_path}")
        print(f"📊 Summary: {result.get('summary', 'N/A')}")

    except Exception as e:
        print(f"❌ Error: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
