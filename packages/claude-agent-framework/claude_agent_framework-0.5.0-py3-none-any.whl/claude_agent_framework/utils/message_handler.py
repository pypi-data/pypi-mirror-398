"""
消息处理模块

处理 Claude SDK 返回的各类消息，提取上下文信息并更新追踪器。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from claude_agent_framework.utils.tracker import SubagentTracker
    from claude_agent_framework.utils.transcript import TranscriptWriter

logger = logging.getLogger(__name__)


def process_assistant_message(
    msg: Any,
    tracker: SubagentTracker,
    transcript: TranscriptWriter,
) -> None:
    """
    处理 AssistantMessage

    提取 parent_tool_use_id 更新追踪器上下文，
    处理文本块和工具调用块。

    Args:
        msg: AssistantMessage 对象
        tracker: 子智能体追踪器
        transcript: 转录写入器
    """
    # 获取父级工具调用 ID 并更新上下文
    parent_id = getattr(msg, "parent_tool_use_id", None)
    tracker.set_current_context(parent_id)

    # 获取当前智能体 ID
    agent_id = tracker.get_current_agent_id()

    # 处理消息内容块
    content = getattr(msg, "content", [])
    for block in content:
        block_type = type(block).__name__

        if block_type == "TextBlock":
            # 文本输出
            text = getattr(block, "text", "")
            if text:
                transcript.write(text)

        elif block_type == "ToolUseBlock":
            # 工具调用
            tool_name = getattr(block, "name", "unknown")
            tool_input = getattr(block, "input", {})
            tool_id = getattr(block, "id", "")

            # 记录到转录（详细信息仅写入文件）
            summary = _format_tool_call(tool_name, tool_input)
            transcript.tool_call(agent_id, tool_name, summary)

            # 检测子智能体派发
            if tool_name == "Task":
                subagent_type = tool_input.get("subagent_type", "unknown")
                description = tool_input.get("description", "")
                prompt = tool_input.get("prompt", "")

                subagent_id = tracker.register_subagent_spawn(
                    tool_use_id=tool_id,
                    subagent_type=subagent_type,
                    description=description,
                    prompt=prompt,
                )
                transcript.subagent_spawn(subagent_id, description)


def process_result_message(
    msg: Any,
    tracker: SubagentTracker,
    transcript: TranscriptWriter,
) -> None:
    """
    处理 ResultMessage

    记录最终结果。

    Args:
        msg: ResultMessage 对象
        tracker: 子智能体追踪器
        transcript: 转录写入器
    """
    result = getattr(msg, "result", None)
    if result:
        transcript.result(str(result))


def process_error_message(
    msg: Any,
    tracker: SubagentTracker,
    transcript: TranscriptWriter,
) -> None:
    """
    处理错误消息

    Args:
        msg: 错误消息对象
        tracker: 子智能体追踪器
        transcript: 转录写入器
    """
    error = getattr(msg, "error", None) or getattr(msg, "message", None) or str(msg)
    transcript.error(str(error))
    logger.error(f"Error message received: {error}")


def process_message(
    msg: Any,
    tracker: SubagentTracker,
    transcript: TranscriptWriter,
) -> None:
    """
    统一消息处理入口

    根据消息类型分发到对应的处理函数。

    Args:
        msg: SDK 消息对象
        tracker: 子智能体追踪器
        transcript: 转录写入器
    """
    msg_type = type(msg).__name__

    if msg_type == "AssistantMessage":
        process_assistant_message(msg, tracker, transcript)
    elif msg_type == "ResultMessage":
        process_result_message(msg, tracker, transcript)
    elif msg_type in ("ErrorMessage", "Error"):
        process_error_message(msg, tracker, transcript)
    else:
        # 未知消息类型，记录到文件
        logger.debug(f"Unknown message type: {msg_type}")
        transcript.write_to_file_only(f"\n[DEBUG] Unknown message: {msg_type}\n")


def _format_tool_call(tool_name: str, tool_input: dict[str, Any]) -> str:
    """
    格式化工具调用摘要

    Args:
        tool_name: 工具名称
        tool_input: 工具输入

    Returns:
        格式化的摘要字符串
    """
    if tool_name == "Task":
        subagent = tool_input.get("subagent_type", "unknown")
        desc = tool_input.get("description", "")[:50]
        return f"spawn {subagent}: {desc}..."

    if tool_name == "WebSearch":
        query = tool_input.get("query", "")[:50]
        return f"'{query}...'"

    if tool_name in ("Read", "Write"):
        path = tool_input.get("file_path", tool_input.get("path", ""))
        return path

    if tool_name == "Glob":
        pattern = tool_input.get("pattern", "")
        return f"pattern='{pattern}'"

    if tool_name == "Grep":
        pattern = tool_input.get("pattern", "")
        return f"search='{pattern}'"

    if tool_name == "Bash":
        cmd = tool_input.get("command", "")[:60]
        return f"$ {cmd}..."

    if tool_name == "Skill":
        skill = tool_input.get("skill", "")
        return f"invoke {skill}"

    # 默认
    return str(tool_input)[:80]
