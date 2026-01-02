"""
Debate architecture configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DebateConfig:
    """
    Configuration for the Debate architecture.

    Attributes:
        debate_rounds: Number of debate rounds
        proponent_model: Model for proponent
        opponent_model: Model for opponent
        judge_model: Model for judge (typically stronger)
        require_evidence: Whether to require evidence for claims
        voting_mechanism: How judge makes decision
    """

    debate_rounds: int = 2
    proponent_model: str = "haiku"
    opponent_model: str = "haiku"
    judge_model: str = "sonnet"  # Judge uses stronger model
    require_evidence: bool = True
    voting_mechanism: str = "weighted"  # simple, weighted, consensus

    # Evaluation criteria for judge
    judge_criteria: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Set default judge criteria."""
        if not self.judge_criteria:
            self.judge_criteria = [
                "argument_strength",
                "evidence_quality",
                "logical_consistency",
                "counterargument_handling",
                "practical_feasibility",
            ]

    def get_model_overrides(self) -> dict[str, str]:
        """Get model overrides for AgentModelConfig."""
        return {
            "proponent": self.proponent_model,
            "opponent": self.opponent_model,
            "judge": self.judge_model,
        }
