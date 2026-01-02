#!/usr/bin/env python3
"""代码调试器 - 使用 Reflexion 架构的示例"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml

from claude_agent_framework import create_session
from claude_agent_framework.core.roles import AgentInstanceConfig

# ============================================================================
# 业务配置 (定制点 1)
# ============================================================================

ARCHITECTURE = "reflexion"
OUTPUT_DIR = Path(__file__).parent / "outputs"

# ============================================================================
# 业务定制函数 (定制点 2-4)
# ============================================================================


def build_agent_instances(config: dict) -> list[AgentInstanceConfig]:
    """定制点 2: 定义智能体实例"""
    models = config.get("models", {})
    return [
        AgentInstanceConfig(
            name="debug_executor",
            role="executor",
            model=models.get("executor", "sonnet"),
        ),
        AgentInstanceConfig(
            name="debug_analyst",
            role="reflector",
            model=models.get("reflector", "sonnet"),
        ),
    ]


def build_prompt(config: dict) -> str:
    """定制点 3: 构建任务提示词"""
    bug_data = config.get("_bug_data", {})
    bug_description = bug_data.get("description", "")
    context = bug_data.get("context", {})
    debugging_config = config.get("debugging", {})
    strategies = config.get("strategies", {})
    root_cause_framework = config.get("root_cause_analysis", {})
    advanced = config.get("advanced", {})

    # 提取上下文
    error_message = context.get("error_message", "")
    file_path = context.get("file_path", "")
    reproduction_steps = context.get("reproduction_steps", [])
    expected_behavior = context.get("expected_behavior", "")
    actual_behavior = context.get("actual_behavior", "")
    code_snippet = context.get("code_snippet", "")

    # 构建策略描述
    strategies_desc = []
    for strategy_name, strategy_config in strategies.items():
        desc = strategy_config.get("description", "")
        priority = strategy_config.get("priority", 0)
        strategies_desc.append(f"- **{strategy_name}** (Priority {priority}): {desc}")
    strategies_text = "\n".join(strategies_desc)

    # 构建根因分类
    categories = root_cause_framework.get("categories", [])
    categories_desc = []
    for category in categories:
        name = category.get("name", "")
        indicators = category.get("indicators", [])
        categories_desc.append(f"- **{name}**: {', '.join(indicators)}")
    categories_text = "\n".join(categories_desc)

    # 构建高级选项
    advanced_options = []
    if advanced.get("enable_static_analysis"):
        advanced_options.append("- Static analysis enabled")
    if advanced.get("enable_llm_debugging"):
        advanced_options.append("- LLM debugging enabled")
    if advanced.get("verbose_logging"):
        advanced_options.append("- Verbose logging enabled")
    advanced_text = "\n".join(advanced_options) if advanced_options else "None"

    return f"""# Code Debugging Task

## Bug Description

{bug_description}

## Bug Context

**Error Message**:
```
{error_message if error_message else "No error message provided"}
```

**File Path**: {file_path if file_path else "Not specified"}

**Code Snippet**:
```python
{code_snippet if code_snippet else "No code snippet provided"}
```

**Expected Behavior**: {expected_behavior if expected_behavior else "Not specified"}

**Actual Behavior**: {actual_behavior if actual_behavior else "Not specified"}

**Reproduction Steps**:
{chr(10).join(f"{i + 1}. {step}" for i, step in enumerate(reproduction_steps)) if reproduction_steps else "Not provided"}

## Debugging Configuration

Maximum iterations: {debugging_config.get("max_iterations", 5)}
Success threshold: {debugging_config.get("success_threshold", 0.9)}

## Available Debugging Strategies

{strategies_text}

## Root Cause Categories

{categories_text}

## Advanced Options

{advanced_text}

Debug this issue using the reflexion loop to systematically find and fix the root cause.
"""


def build_result(config: dict, contents: list[str], session) -> dict:
    """定制点 4: 构建输出结果"""
    bug_data = config.get("_bug_data", {})
    bug_description = bug_data.get("description", "")
    context = bug_data.get("context", {})
    debugging_config = config.get("debugging", {})
    bug_categories = config.get("bug_categories", {})
    strategies = config.get("strategies", {})
    models = config.get("models", {})

    # 解析调试结果
    debugging_timeline = parse_debugging_timeline(contents)
    root_cause = extract_root_cause(contents)
    proposed_fix = extract_proposed_fix(contents)
    failed_attempts = extract_failed_attempts(contents)
    learnings = extract_learnings(contents)
    prevention_recommendations = extract_prevention_recommendations(contents)

    return {
        "debug_session_id": str(uuid.uuid4()),
        "title": f"Debug Session: {bug_description[:100]}",
        "summary": generate_summary(bug_description, root_cause, debugging_timeline),
        "bug": {
            "description": bug_description,
            "error_message": context.get("error_message", ""),
            "file_path": context.get("file_path", ""),
            "category": categorize_bug(bug_description, context, bug_categories),
            "context": context,
        },
        "debugging_timeline": debugging_timeline,
        "root_cause": root_cause,
        "proposed_fix": proposed_fix,
        "failed_attempts": failed_attempts,
        "learnings": learnings,
        "prevention_recommendations": prevention_recommendations,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "architecture": ARCHITECTURE,
            "iterations": len(debugging_timeline),
            "max_iterations": debugging_config.get("max_iterations", 5),
            "success": confidence_to_score(root_cause.get("confidence", "Unknown"))
            >= debugging_config.get("success_threshold", 0.9),
            "config": {
                "strategies_used": list(strategies.keys()),
                "models": models,
            },
        },
    }


# ============================================================================
# 业务辅助函数
# ============================================================================


def confidence_to_score(confidence: str) -> float:
    """将置信度字符串转换为数值分数"""
    confidence_map = {
        "high": 1.0,
        "medium": 0.6,
        "low": 0.3,
        "unknown": 0.0,
    }
    return confidence_map.get(confidence.lower(), 0.0)


def categorize_bug(bug_description: str, context: dict, bug_categories: dict) -> str:
    """根据描述和上下文分类 bug"""
    error_message = context.get("error_message", "").lower()
    description_lower = bug_description.lower()

    for category, cfg in bug_categories.items():
        patterns = cfg.get("patterns", [])
        for pattern in patterns:
            if pattern.lower() in error_message or pattern.lower() in description_lower:
                return category

    return "unknown"


def parse_debugging_timeline(results: list[str]) -> list[dict]:
    """解析调试时间线"""
    full_text = "\n".join(results)
    timeline = []
    iterations = []
    current_iteration = None

    for line in full_text.split("\n"):
        if line.startswith("### Iteration"):
            if current_iteration:
                iterations.append(current_iteration)
            current_iteration = {"iteration": line, "content": []}
        elif current_iteration is not None:
            current_iteration["content"].append(line)

    if current_iteration:
        iterations.append(current_iteration)

    for idx, iteration_data in enumerate(iterations):
        iteration_text = "\n".join(iteration_data["content"])
        executor_text = ""
        reflector_text = ""
        improver_text = ""

        if "**[Executor]**" in iteration_text:
            parts = iteration_text.split("**[Executor]**")
            if len(parts) > 1:
                executor_part = parts[1].split("**[Reflector]**")[0]
                executor_text = executor_part.strip()

        if "**[Reflector]**" in iteration_text:
            parts = iteration_text.split("**[Reflector]**")
            if len(parts) > 1:
                reflector_part = parts[1].split("**[Improver]**")[0]
                reflector_text = reflector_part.strip()

        if "**[Improver]**" in iteration_text:
            parts = iteration_text.split("**[Improver]**")
            if len(parts) > 1:
                improver_text = parts[1].strip()

        timeline.append({
            "iteration": idx + 1,
            "executor": executor_text,
            "reflector": reflector_text,
            "improver": improver_text,
        })

    return timeline


def extract_root_cause(results: list[str]) -> dict:
    """提取根因"""
    full_text = "\n".join(results)
    root_cause = {
        "category": "Unknown",
        "description": "",
        "confidence": "Unknown",
        "evidence": [],
    }

    if "**Root Cause Identified**" in full_text:
        cause_start = full_text.index("**Root Cause Identified**")
        cause_section = full_text[cause_start : cause_start + 1500]

        if "Category:" in cause_section:
            category_line = cause_section.split("Category:")[1].split("\n")[0]
            root_cause["category"] = category_line.strip()

        if "Description:" in cause_section:
            desc_start = cause_section.index("Description:")
            desc_end = cause_section.find("Why it causes", desc_start)
            if desc_end == -1:
                desc_end = cause_section.find("Confidence:", desc_start)
            if desc_end == -1:
                desc_end = len(cause_section)
            description = cause_section[desc_start:desc_end]
            root_cause["description"] = description.replace("Description:", "").strip()

        if "Confidence:" in cause_section:
            conf_line = cause_section.split("Confidence:")[1].split("\n")[0]
            root_cause["confidence"] = conf_line.strip()

        if "Evidence:" in cause_section:
            evidence_start = cause_section.index("Evidence:")
            evidence_section = cause_section[evidence_start : evidence_start + 500]
            lines = evidence_section.split("\n")
            for line in lines:
                if line.strip().startswith(("1.", "2.", "3.", "4.", "5.")):
                    evidence_text = line.strip()[3:].strip()
                    root_cause["evidence"].append(evidence_text)

    return root_cause


def extract_proposed_fix(results: list[str]) -> dict:
    """提取建议修复"""
    full_text = "\n".join(results)
    proposed_fix = {
        "file_path": None,
        "before_code": None,
        "after_code": None,
        "explanation": "",
        "alternatives": [],
    }

    if "**Proposed Fix**" in full_text:
        fix_start = full_text.index("**Proposed Fix**")
        fix_section = full_text[fix_start : fix_start + 2000]

        if "# File:" in fix_section:
            file_line = fix_section.split("# File:")[1].split("\n")[0]
            proposed_fix["file_path"] = file_line.strip()

        if "# Before" in fix_section and "# After" in fix_section:
            before_start = fix_section.find("# Before")
            after_marker = fix_section.find("# After", before_start)
            if after_marker != -1:
                before_section = fix_section[before_start:after_marker]
                lines = before_section.split("\n")[1:]
                code_lines = []
                for line in lines:
                    if not line.strip() or line.strip().startswith("# After"):
                        break
                    code_lines.append(line)
                proposed_fix["before_code"] = "\n".join(code_lines).strip()

            after_start = fix_section.find("# After")
            expl_marker = fix_section.find("# Explanation:", after_start)
            if expl_marker == -1:
                expl_marker = fix_section.find("```", after_start + 10)
            if expl_marker != -1:
                after_section = fix_section[after_start:expl_marker]
                lines = after_section.split("\n")[1:]
                code_lines = []
                for line in lines:
                    if line.strip().startswith("# Explanation") or line.strip() == "```":
                        break
                    code_lines.append(line)
                proposed_fix["after_code"] = "\n".join(code_lines).strip()

        if "# Explanation:" in fix_section:
            expl_start = fix_section.index("# Explanation:")
            expl_end = fix_section.find("Alternative approaches", expl_start)
            if expl_end == -1:
                expl_end = fix_section.find("**Fix Validation**", expl_start)
            if expl_end == -1:
                expl_end = len(fix_section)
            explanation = fix_section[expl_start:expl_end]
            proposed_fix["explanation"] = explanation.replace("# Explanation:", "").strip()

    return proposed_fix


def extract_failed_attempts(results: list[str]) -> list[dict]:
    """提取失败尝试"""
    full_text = "\n".join(results)
    failed_attempts = []

    if "**Failed Attempts Summary**" in full_text:
        summary_start = full_text.index("**Failed Attempts Summary**")
        summary_section = full_text[summary_start : summary_start + 1000]

        lines = summary_section.split("\n")
        for line in lines:
            if line.strip().startswith("Iteration"):
                parts = line.split(":")
                if len(parts) >= 2:
                    iteration_part = parts[0].strip()
                    detail_part = ":".join(parts[1:])

                    if " - Failed because " in detail_part:
                        tried_part, reason_part = detail_part.split(" - Failed because ")
                        failed_attempts.append({
                            "iteration": iteration_part,
                            "strategy": tried_part.replace("Tried", "").strip(),
                            "reason": reason_part.strip(),
                        })

    return failed_attempts


def extract_learnings(results: list[str]) -> list[str]:
    """提取关键学习"""
    full_text = "\n".join(results)
    learnings = []

    if "Key learnings:" in full_text:
        learnings_start = full_text.index("Key learnings:")
        learnings_section = full_text[learnings_start : learnings_start + 500]

        lines = learnings_section.split("\n")
        for line in lines:
            if line.strip().startswith(("1.", "2.", "3.", "4.", "5.")):
                learning_text = line.strip()[3:].strip()
                learnings.append(learning_text)

    return learnings if learnings else ["No explicit learnings documented"]


def extract_prevention_recommendations(results: list[str]) -> list[str]:
    """提取预防建议"""
    full_text = "\n".join(results)
    recommendations = []

    if "**Prevention Recommendations**" in full_text:
        prev_start = full_text.index("**Prevention Recommendations**")
        prev_section = full_text[prev_start : prev_start + 800]

        lines = prev_section.split("\n")
        for line in lines:
            if line.strip().startswith(("1.", "2.", "3.", "4.", "5.")):
                rec_text = line.strip()[3:].strip()
                recommendations.append(rec_text)

    return recommendations if recommendations else ["No prevention recommendations provided"]


def generate_summary(bug_description: str, root_cause: dict, debugging_timeline: list[dict]) -> str:
    """生成执行摘要"""
    iterations = len(debugging_timeline)
    category = root_cause.get("category", "Unknown")
    confidence = root_cause.get("confidence", "Low")

    return f"Debugged: {bug_description[:100]}. Root cause: {category}. Confidence: {confidence}. Iterations: {iterations}."


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

        # 业务特定: 设置 bug 数据
        bug_description = "AttributeError: 'NoneType' object has no attribute 'get'"
        context = {
            "error_message": """
Traceback (most recent call last):
  File "app.py", line 45, in process_user_data
    user_email = user.get('email')
AttributeError: 'NoneType' object has no attribute 'get'
            """,
            "file_path": "app.py",
            "code_snippet": """
def process_user_data(user_id):
    user = fetch_user(user_id)
    user_email = user.get('email')  # Line 45 - Error occurs here
    send_notification(user_email)
    return user
            """,
            "reproduction_steps": [
                "Call process_user_data(999) with non-existent user ID",
                "fetch_user returns None for invalid ID",
                "Attempt to call .get() on None raises AttributeError",
            ],
            "expected_behavior": "Should handle missing user gracefully",
            "actual_behavior": "Crashes with AttributeError",
        }

        config["_bug_data"] = {
            "description": bug_description,
            "context": context,
        }

        print(f"Debugging: {bug_description}\n")

        result = await run_task(config)

        output_path = save_result(result, f"{ARCHITECTURE}_result")

        print(f"Debug Session ID: {result['debug_session_id']}")
        print(f"Root Cause: {result['root_cause']['category']}")
        print(f"Confidence: {result['root_cause']['confidence']}")
        print(f"Iterations: {result['metadata']['iterations']}")
        print(f"\n✅ Complete! Output: {output_path}")
        print(f"📊 Summary: {result.get('summary', 'N/A')}")

    except Exception as e:
        print(f"❌ Error: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
