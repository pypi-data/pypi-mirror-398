"""
Research architecture configuration.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ResearchConfig:
    """
    Configuration for the Research architecture.

    Attributes:
        max_researchers: Maximum number of parallel researcher agents
        enable_data_analysis: Whether to include data analysis stage
        enable_report_generation: Whether to generate PDF report
        research_depth: Depth of research (shallow/medium/deep)
        lead_model: Model for lead agent
        researcher_model: Model for researcher agents
        analyst_model: Model for data analyst
        writer_model: Model for report writer
    """

    max_researchers: int = 4
    enable_data_analysis: bool = True
    enable_report_generation: bool = True
    research_depth: str = "medium"  # shallow, medium, deep

    # Model configuration
    lead_model: str = "haiku"
    researcher_model: str = "haiku"
    analyst_model: str = "haiku"
    writer_model: str = "haiku"

    # Output directories (relative to files_dir)
    research_notes_dir: str = "research_notes"
    data_dir: str = "data"
    charts_dir: str = "charts"
    reports_dir: str = "reports"

    def get_model_overrides(self) -> dict[str, str]:
        """Get model overrides for AgentModelConfig."""
        return {
            "researcher": self.researcher_model,
            "data-analyst": self.analyst_model,
            "report-writer": self.writer_model,
        }

    @property
    def search_count_by_depth(self) -> int:
        """Get recommended search count based on depth."""
        depth_map = {
            "shallow": 3,
            "medium": 7,
            "deep": 15,
        }
        return depth_map.get(self.research_depth, 7)
