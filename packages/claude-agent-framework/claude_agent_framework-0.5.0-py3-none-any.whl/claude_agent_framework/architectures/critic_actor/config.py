"""
Critic-Actor architecture configuration.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CriticActorConfig:
    """
    Configuration for the Critic-Actor architecture.

    Attributes:
        max_iterations: Maximum number of improvement iterations
        quality_threshold: Quality score threshold for acceptance (0.0-1.0)
        actor_model: Model for actor (content generator)
        critic_model: Model for critic (evaluator, typically stronger)
        enable_memory: Whether to retain iteration history
    """

    max_iterations: int = 5
    quality_threshold: float = 0.8
    actor_model: str = "haiku"
    critic_model: str = "sonnet"  # Critic uses stronger model
    enable_memory: bool = True

    # Evaluation criteria weights
    criteria_weights: dict[str, float] | None = None

    def __post_init__(self) -> None:
        """Set default criteria weights."""
        if self.criteria_weights is None:
            self.criteria_weights = {
                "correctness": 0.3,
                "completeness": 0.25,
                "clarity": 0.2,
                "efficiency": 0.15,
                "style": 0.1,
            }

    def get_model_overrides(self) -> dict[str, str]:
        """Get model overrides for AgentModelConfig."""
        return {
            "actor": self.actor_model,
            "critic": self.critic_model,
        }
