"""
MapReduce architecture implementation.

A parallel map with aggregation pattern for large-scale processing.
Split task into chunks, map in parallel, reduce to final result.
"""

from claude_agent_framework.architectures.mapreduce.config import MapReduceConfig
from claude_agent_framework.architectures.mapreduce.orchestrator import (
    MapReduceArchitecture,
)
from claude_agent_framework.architectures.mapreduce.splitter import TaskSplitter

__all__ = [
    "MapReduceArchitecture",
    "MapReduceConfig",
    "TaskSplitter",
]
