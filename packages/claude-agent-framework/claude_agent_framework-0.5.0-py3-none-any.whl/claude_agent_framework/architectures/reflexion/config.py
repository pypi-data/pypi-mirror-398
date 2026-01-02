"""
Reflexion architecture configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ReflexionConfig:
    """
    Configuration for the Reflexion architecture.

    Attributes:
        max_attempts: Maximum number of attempts
        executor_model: Model for executor
        reflector_model: Model for reflector (typically stronger)
        enable_memory: Whether to retain attempt history
        success_criteria: Criteria for success detection
    """

    max_attempts: int = 5
    executor_model: str = "haiku"
    reflector_model: str = "sonnet"  # Reflector uses stronger model
    enable_memory: bool = True

    # Success detection keywords
    success_indicators: list[str] = field(default_factory=list)
    failure_indicators: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Set default indicators."""
        if not self.success_indicators:
            self.success_indicators = [
                "成功",
                "通过",
                "完成",
                "正确",
                "PASSED",
                "SUCCESS",
            ]
        if not self.failure_indicators:
            self.failure_indicators = [
                "失败",
                "错误",
                "异常",
                "Error",
                "FAILED",
                "Exception",
            ]

    def get_model_overrides(self) -> dict[str, str]:
        """Get model overrides for AgentModelConfig."""
        return {
            "executor": self.executor_model,
            "reflector": self.reflector_model,
        }
