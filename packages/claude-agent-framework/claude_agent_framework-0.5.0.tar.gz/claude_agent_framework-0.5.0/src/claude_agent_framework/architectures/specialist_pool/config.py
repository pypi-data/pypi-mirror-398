"""
Specialist Pool architecture configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from claude_agent_framework.core.base import AgentDefinitionConfig


@dataclass
class ExpertConfig:
    """
    Configuration for a single expert.

    Attributes:
        name: Expert identifier
        domain: Domain of expertise
        keywords: Keywords for routing
        agent: Agent configuration
        priority: Routing priority (higher = preferred)
    """

    name: str
    domain: str
    keywords: list[str]
    agent: AgentDefinitionConfig
    priority: int = 0


@dataclass
class SpecialistPoolConfig:
    """
    Configuration for the Specialist Pool architecture.

    Attributes:
        experts: List of available experts
        max_experts_per_query: Max experts to dispatch per query
        parallel_dispatch: Whether to dispatch experts in parallel
        aggregation_method: How to aggregate expert responses
        router_model: Model for the router agent
    """

    experts: list[ExpertConfig] = field(default_factory=list)
    max_experts_per_query: int = 3
    parallel_dispatch: bool = True
    aggregation_method: str = "summarize"  # summarize, concatenate, vote
    router_model: str = "haiku"

    def __post_init__(self) -> None:
        """Set default experts if none provided."""
        if not self.experts:
            self.experts = self._default_experts()

    def _default_experts(self) -> list[ExpertConfig]:
        """Default technical support experts."""
        return [
            ExpertConfig(
                name="code_expert",
                domain="代码开发",
                keywords=["代码", "编程", "函数", "类", "实现", "bug", "错误"],
                agent=AgentDefinitionConfig(
                    name="code_expert",
                    description="代码开发和调试专家",
                    tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
                    prompt_file="code_expert.txt",
                ),
                priority=1,
            ),
            ExpertConfig(
                name="data_expert",
                domain="数据分析",
                keywords=["数据", "分析", "统计", "可视化", "图表", "SQL", "pandas"],
                agent=AgentDefinitionConfig(
                    name="data_expert",
                    description="数据分析和可视化专家",
                    tools=["Read", "Write", "Bash", "Glob"],
                    prompt_file="data_expert.txt",
                ),
                priority=0,
            ),
            ExpertConfig(
                name="security_expert",
                domain="安全审计",
                keywords=["安全", "漏洞", "注入", "XSS", "认证", "授权", "加密"],
                agent=AgentDefinitionConfig(
                    name="security_expert",
                    description="安全审计和漏洞分析专家",
                    tools=["Read", "Glob", "Grep"],
                    prompt_file="security_expert.txt",
                ),
                priority=2,
            ),
            ExpertConfig(
                name="performance_expert",
                domain="性能优化",
                keywords=["性能", "优化", "慢", "内存", "CPU", "缓存", "并发"],
                agent=AgentDefinitionConfig(
                    name="performance_expert",
                    description="性能优化和诊断专家",
                    tools=["Read", "Bash", "Glob", "Grep"],
                    prompt_file="performance_expert.txt",
                ),
                priority=0,
            ),
        ]

    def get_expert(self, name: str) -> ExpertConfig | None:
        """Get expert by name."""
        for expert in self.experts:
            if expert.name == name:
                return expert
        return None

    def get_expert_names(self) -> list[str]:
        """Get list of expert names."""
        return [e.name for e in self.experts]
