"""
智能体追踪器模块

提供子智能体会话追踪、工具调用记录和 Hook 实现。
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from claude_agent_framework.utils.transcript import TranscriptWriter

logger = logging.getLogger(__name__)


@dataclass
class ToolCallRecord:
    """单次工具调用记录"""

    timestamp: str
    tool_name: str
    tool_input: dict[str, Any]
    tool_use_id: str
    subagent_type: str
    parent_tool_use_id: str | None = None
    tool_output: Any | None = None
    error: str | None = None


@dataclass
class SubagentSession:
    """子智能体会话追踪"""

    subagent_type: str
    parent_tool_use_id: str
    spawned_at: str
    description: str
    subagent_id: str  # 如 "RESEARCHER-1"
    prompt_summary: str = ""
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    completed_at: str | None = None
    status: str = "running"  # running, completed, failed


class SubagentTracker:
    """
    子智能体追踪器

    负责：
    - 追踪子智能体派发和生命周期
    - 记录所有工具调用
    - 关联工具调用与其父级上下文
    - 输出结构化 JSONL 日志
    """

    def __init__(
        self,
        tool_log_path: Path | str,
        transcript_writer: TranscriptWriter | None = None,
    ):
        """
        初始化追踪器

        Args:
            tool_log_path: JSONL 日志文件路径
            transcript_writer: 可选的转录写入器
        """
        self.tool_log_path = Path(tool_log_path)
        self.transcript_writer = transcript_writer

        # 状态存储
        self.sessions: dict[str, SubagentSession] = {}  # parent_tool_use_id -> session
        self.tool_call_records: dict[str, ToolCallRecord] = {}  # tool_use_id -> record
        self._current_parent_id: str | None = None
        self.subagent_counters: dict[str, int] = {}

        # 打开日志文件
        self._log_file = open(self.tool_log_path, "w", encoding="utf-8")

        # 写入会话开始事件
        self._log_event("session_start", {"timestamp": datetime.now().isoformat()})

    def set_current_context(self, parent_tool_use_id: str | None) -> None:
        """
        设置当前执行上下文

        当收到 AssistantMessage 时，提取其 parent_tool_use_id 并调用此方法。
        后续的工具调用将被关联到这个上下文。

        Args:
            parent_tool_use_id: 父级工具调用 ID，None 表示主智能体上下文
        """
        self._current_parent_id = parent_tool_use_id

    def get_current_agent_id(self) -> str:
        """获取当前活跃的智能体 ID"""
        if self._current_parent_id and self._current_parent_id in self.sessions:
            return self.sessions[self._current_parent_id].subagent_id
        return "LEAD"

    def register_subagent_spawn(
        self,
        tool_use_id: str,
        subagent_type: str,
        description: str,
        prompt: str,
    ) -> str:
        """
        注册子智能体派发

        当检测到 Task 工具调用时调用此方法。

        Args:
            tool_use_id: Task 工具调用的 ID
            subagent_type: 子智能体类型（如 "researcher"）
            description: 任务描述
            prompt: 子智能体提示词

        Returns:
            生成的子智能体 ID（如 "RESEARCHER-1"）
        """
        # 生成唯一 ID
        self.subagent_counters.setdefault(subagent_type, 0)
        self.subagent_counters[subagent_type] += 1
        subagent_id = f"{subagent_type.upper()}-{self.subagent_counters[subagent_type]}"

        # 创建会话
        session = SubagentSession(
            subagent_type=subagent_type,
            parent_tool_use_id=tool_use_id,
            spawned_at=datetime.now().isoformat(),
            description=description,
            subagent_id=subagent_id,
            prompt_summary=prompt[:200] + "..." if len(prompt) > 200 else prompt,
        )
        self.sessions[tool_use_id] = session

        # 记录事件
        self._log_event(
            "subagent_spawn",
            {
                "subagent_id": subagent_id,
                "subagent_type": subagent_type,
                "parent_tool_use_id": tool_use_id,
                "description": description,
            },
        )

        logger.info(f"Spawned subagent: {subagent_id}")
        return subagent_id

    def mark_subagent_complete(self, parent_tool_use_id: str, status: str = "completed") -> None:
        """
        标记子智能体完成

        Args:
            parent_tool_use_id: 子智能体的父级工具调用 ID
            status: 完成状态 ("completed" 或 "failed")
        """
        if parent_tool_use_id in self.sessions:
            session = self.sessions[parent_tool_use_id]
            session.completed_at = datetime.now().isoformat()
            session.status = status

            self._log_event(
                "subagent_complete",
                {
                    "subagent_id": session.subagent_id,
                    "status": status,
                    "tool_call_count": len(session.tool_calls),
                },
            )

    async def pre_tool_use_hook(
        self,
        hook_input: dict[str, Any],
        tool_use_id: str,
        context: Any,
    ) -> dict[str, Any]:
        """
        工具执行前 Hook

        捕获工具调用输入，创建记录并关联到当前上下文。

        Args:
            hook_input: Hook 输入数据，包含 tool_name 和 tool_input
            tool_use_id: 工具调用 ID
            context: 上下文对象

        Returns:
            包含 continue_=True 的字典，允许继续执行
        """
        tool_name = hook_input.get("tool_name", "unknown")
        tool_input = hook_input.get("tool_input", {})

        # 确定所属智能体
        agent_id = self.get_current_agent_id()

        # 创建记录
        record = ToolCallRecord(
            timestamp=datetime.now().isoformat(),
            tool_name=tool_name,
            tool_input=tool_input,
            tool_use_id=tool_use_id,
            subagent_type=agent_id,
            parent_tool_use_id=self._current_parent_id,
        )
        self.tool_call_records[tool_use_id] = record

        # 如果属于某个子智能体会话，添加到其工具调用列表
        if self._current_parent_id and self._current_parent_id in self.sessions:
            self.sessions[self._current_parent_id].tool_calls.append(record)

        # 写入日志
        self._log_event(
            "tool_call_start",
            {
                "agent_id": agent_id,
                "tool_name": tool_name,
                "tool_use_id": tool_use_id,
                "input_summary": self._format_tool_input(tool_input),
            },
        )

        # 写入转录（如果有）
        if self.transcript_writer:
            self.transcript_writer.write_to_file_only(
                f"\n[{agent_id}] {tool_name}: {self._format_tool_input(tool_input)}\n"
            )

        logger.debug(f"[{agent_id}] Starting tool: {tool_name}")
        return {"continue_": True}

    async def post_tool_use_hook(
        self,
        hook_input: dict[str, Any],
        tool_use_id: str,
        context: Any,
    ) -> dict[str, Any]:
        """
        工具执行后 Hook

        捕获工具执行结果或错误。

        Args:
            hook_input: Hook 输入数据，包含 tool_response
            tool_use_id: 工具调用 ID
            context: 上下文对象

        Returns:
            包含 continue_=True 的字典，允许继续执行
        """
        tool_response = hook_input.get("tool_response")
        record = self.tool_call_records.get(tool_use_id)

        if record:
            # 检查错误
            error = None
            if isinstance(tool_response, dict):
                error = tool_response.get("error")

            record.tool_output = tool_response
            record.error = error

            # 计算输出大小
            output_size = 0
            if tool_response:
                try:
                    output_size = len(str(tool_response))
                except Exception:
                    pass

            # 写入日志
            self._log_event(
                "tool_call_complete",
                {
                    "tool_use_id": tool_use_id,
                    "tool_name": record.tool_name,
                    "agent_id": record.subagent_type,
                    "success": error is None,
                    "output_size": output_size,
                    "error": error,
                },
            )

            if error:
                logger.warning(f"[{record.subagent_type}] Tool {record.tool_name} error: {error}")

        return {"continue_": True}

    def _format_tool_input(self, tool_input: dict[str, Any], max_length: int = 100) -> str:
        """格式化工具输入为可读摘要"""
        if not tool_input:
            return "(no input)"

        # 常见字段的特殊处理
        if "query" in tool_input:
            query = str(tool_input["query"])
            return f"query='{query[:max_length]}{'...' if len(query) > max_length else ''}'"

        if "file_path" in tool_input:
            path = Path(tool_input["file_path"]).name
            if "content" in tool_input:
                content_len = len(str(tool_input["content"]))
                return f"file='{path}' ({content_len} chars)"
            return f"file='{path}'"

        if "path" in tool_input:
            return f"path='{tool_input['path']}'"

        if "pattern" in tool_input:
            return f"pattern='{tool_input['pattern']}'"

        if "command" in tool_input:
            cmd = str(tool_input["command"])
            return f"cmd='{cmd[:max_length]}{'...' if len(cmd) > max_length else ''}'"

        if "subagent_type" in tool_input:
            return f"subagent={tool_input['subagent_type']}"

        # 默认：JSON 摘要
        try:
            summary = json.dumps(tool_input, ensure_ascii=False)
            if len(summary) > max_length:
                return summary[: max_length - 3] + "..."
            return summary
        except Exception:
            return str(tool_input)[:max_length]

    def _log_event(self, event_type: str, data: dict[str, Any]) -> None:
        """写入 JSONL 日志"""
        entry = {
            "event": event_type,
            "timestamp": datetime.now().isoformat(),
            **data,
        }
        self._log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self._log_file.flush()

    def get_session_summary(self) -> dict[str, Any]:
        """获取会话摘要"""
        return {
            "total_subagents": len(self.sessions),
            "total_tool_calls": len(self.tool_call_records),
            "subagent_summary": {
                session.subagent_id: {
                    "type": session.subagent_type,
                    "status": session.status,
                    "tool_calls": len(session.tool_calls),
                }
                for session in self.sessions.values()
            },
        }

    def close(self) -> None:
        """关闭追踪器，清理资源"""
        # 写入会话结束事件
        self._log_event("session_end", self.get_session_summary())

        # 关闭日志文件
        self._log_file.close()
        logger.info(f"Tracker closed. Log saved to: {self.tool_log_path}")
