"""
MapReduce architecture configuration.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MapReduceConfig:
    """
    Configuration for the MapReduce architecture.

    Attributes:
        max_mappers: Maximum number of parallel mappers
        chunk_size: Number of items per mapper
        mapper_model: Model for mapper agents
        reducer_model: Model for reducer (typically stronger)
        split_strategy: How to split tasks (files, topic, content)
        aggregation_method: How to aggregate results
    """

    max_mappers: int = 10
    chunk_size: int = 5
    mapper_model: str = "haiku"
    reducer_model: str = "sonnet"  # Reducer uses stronger model
    split_strategy: str = "files"  # files, topic, content
    aggregation_method: str = "merge"  # merge, summarize, vote

    def get_model_overrides(self) -> dict[str, str]:
        """Get model overrides for AgentModelConfig."""
        return {
            "mapper": self.mapper_model,
            "reducer": self.reducer_model,
        }
