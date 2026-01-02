"""
转录和日志管理模块

提供会话日志记录、双格式输出（控制台+文件）等功能。
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import TextIO

logger = logging.getLogger(__name__)


def setup_session(base_dir: Path | str = "logs") -> tuple[Path, Path, Path]:
    """
    创建会话目录和日志文件

    Args:
        base_dir: 日志基础目录，默认为 "logs"

    Returns:
        (session_dir, transcript_file, tool_log_file) 三元组
    """
    base_dir = Path(base_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = base_dir / f"session_{timestamp}"
    session_dir.mkdir(parents=True, exist_ok=True)

    transcript_file = session_dir / "transcript.txt"
    tool_log_file = session_dir / "tool_calls.jsonl"

    logger.info(f"Session directory created: {session_dir}")
    return session_dir, transcript_file, tool_log_file


class TranscriptWriter:
    """
    双格式转录写入器

    同时输出到控制台和文件，支持详细日志仅写入文件。
    """

    def __init__(self, file_path: Path | str):
        """
        初始化转录写入器

        Args:
            file_path: 转录文件路径
        """
        self.file_path = Path(file_path)
        self._file: TextIO = open(self.file_path, "w", encoding="utf-8")

        # 写入会话头
        self._write_header()

    def _write_header(self) -> None:
        """写入会话头信息"""
        header = f"""{"=" * 60}
研究智能体会话转录
开始时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{"=" * 60}

"""
        self._file.write(header)
        self._file.flush()

    def write(self, text: str, end: str = "") -> None:
        """
        同时输出到控制台和文件

        Args:
            text: 要写入的文本
            end: 结束字符，默认为空
        """
        print(text, end=end, flush=True)
        self._file.write(text + end)
        self._file.flush()

    def write_to_file_only(self, text: str) -> None:
        """
        仅写入文件（用于详细日志）

        Args:
            text: 要写入的文本
        """
        self._file.write(text)
        self._file.flush()

    def write_to_console_only(self, text: str, end: str = "") -> None:
        """
        仅输出到控制台

        Args:
            text: 要输出的文本
            end: 结束字符
        """
        print(text, end=end, flush=True)

    def section(self, title: str) -> None:
        """
        写入分节标题

        Args:
            title: 节标题
        """
        section_text = f"\n{'─' * 40}\n{title}\n{'─' * 40}\n"
        self.write(section_text)

    def user_input(self, text: str) -> None:
        """
        记录用户输入

        Args:
            text: 用户输入内容
        """
        self.write(f"\n[USER] {text}\n")

    def agent_output(self, agent_id: str, text: str) -> None:
        """
        记录智能体输出

        Args:
            agent_id: 智能体 ID
            text: 输出内容
        """
        self.write(f"[{agent_id}] {text}")

    def tool_call(self, agent_id: str, tool_name: str, summary: str) -> None:
        """
        记录工具调用（仅文件）

        Args:
            agent_id: 智能体 ID
            tool_name: 工具名称
            summary: 调用摘要
        """
        self.write_to_file_only(f"\n[{agent_id}] TOOL {tool_name}: {summary}\n")

    def subagent_spawn(self, subagent_id: str, description: str) -> None:
        """
        记录子智能体派发

        Args:
            subagent_id: 子智能体 ID
            description: 任务描述
        """
        self.write(f"\n[SPAWN] {subagent_id}: {description}\n")

    def result(self, text: str) -> None:
        """
        记录结果

        Args:
            text: 结果内容
        """
        self.write(f"\n[RESULT] {text}\n")

    def error(self, text: str) -> None:
        """
        记录错误

        Args:
            text: 错误信息
        """
        self.write(f"\n[ERROR] {text}\n")

    def close(self) -> None:
        """关闭转录文件"""
        # 写入会话尾
        footer = f"""

{"=" * 60}
会话结束: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{"=" * 60}
"""
        self._file.write(footer)
        self._file.close()
        logger.info(f"Transcript saved to: {self.file_path}")


class QuietTranscriptWriter(TranscriptWriter):
    """
    静默转录写入器

    仅写入文件，不输出到控制台。适用于后台运行场景。
    """

    def write(self, text: str, end: str = "") -> None:
        """仅写入文件"""
        self._file.write(text + end)
        self._file.flush()

    def write_to_console_only(self, text: str, end: str = "") -> None:
        """静默模式下不输出到控制台"""
        pass
