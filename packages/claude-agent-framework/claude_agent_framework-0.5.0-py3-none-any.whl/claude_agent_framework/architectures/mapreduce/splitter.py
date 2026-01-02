"""
Task splitting strategies for MapReduce architecture.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class SplitResult:
    """Result of task splitting."""

    chunks: list[list[str]]
    strategy: str
    total_items: int


class TaskSplitter:
    """
    Splits tasks into chunks for parallel processing.

    Supports multiple splitting strategies:
    - files: Split by file paths
    - topic: Split by topic/aspect
    - content: Split by content length
    """

    def __init__(self, chunk_size: int = 5) -> None:
        """Initialize splitter with chunk size."""
        self.chunk_size = chunk_size

    def split_by_files(self, file_list: list[str]) -> SplitResult:
        """
        Split file list into chunks.

        Args:
            file_list: List of file paths to process

        Returns:
            SplitResult with file chunks
        """
        chunks = [
            file_list[i : i + self.chunk_size] for i in range(0, len(file_list), self.chunk_size)
        ]
        return SplitResult(
            chunks=chunks,
            strategy="files",
            total_items=len(file_list),
        )

    def split_by_topic(self, topic: str, aspects: list[str]) -> SplitResult:
        """
        Split topic into aspects for parallel research.

        Args:
            topic: Main topic
            aspects: List of aspects to analyze

        Returns:
            SplitResult with topic chunks
        """
        # Each aspect becomes a chunk
        chunks = [[aspect] for aspect in aspects]
        return SplitResult(
            chunks=chunks,
            strategy="topic",
            total_items=len(aspects),
        )

    def split_by_content(self, content: str, max_tokens: int = 2000) -> SplitResult:
        """
        Split long content into chunks by estimated token count.

        Args:
            content: Content to split
            max_tokens: Maximum tokens per chunk

        Returns:
            SplitResult with content chunks
        """
        # Rough estimate: 4 chars per token
        max_chars = max_tokens * 4
        lines = content.split("\n")

        chunks = []
        current_chunk = []
        current_length = 0

        for line in lines:
            line_length = len(line)
            if current_length + line_length > max_chars and current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_length = 0

            current_chunk.append(line)
            current_length += line_length

        if current_chunk:
            chunks.append(current_chunk)

        return SplitResult(
            chunks=chunks,
            strategy="content",
            total_items=len(chunks),
        )

    def split_directory(self, directory: Path, pattern: str = "**/*") -> SplitResult:
        """
        Split files from a directory into chunks.

        Args:
            directory: Directory to scan
            pattern: Glob pattern for files

        Returns:
            SplitResult with file chunks
        """
        if not directory.exists():
            return SplitResult(chunks=[], strategy="files", total_items=0)

        files = [str(f) for f in directory.glob(pattern) if f.is_file()]
        return self.split_by_files(files)
