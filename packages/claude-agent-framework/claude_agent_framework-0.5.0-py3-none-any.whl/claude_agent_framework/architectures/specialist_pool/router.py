"""
Expert routing logic for Specialist Pool architecture.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from claude_agent_framework.architectures.specialist_pool.config import (
    ExpertConfig,
    SpecialistPoolConfig,
)


@dataclass
class RoutingResult:
    """Result of routing decision."""

    experts: list[str]
    confidence: float
    reasoning: str


class ExpertRouter:
    """
    Router that analyzes queries and selects appropriate experts.

    Supports keyword-based routing and can be extended for semantic routing.
    """

    def __init__(self, config: SpecialistPoolConfig) -> None:
        """Initialize router with configuration."""
        self.config = config
        self._build_keyword_index()

    def _build_keyword_index(self) -> None:
        """Build keyword to expert mapping."""
        self._keyword_index: dict[str, list[str]] = {}

        for expert in self.config.experts:
            for keyword in expert.keywords:
                keyword_lower = keyword.lower()
                if keyword_lower not in self._keyword_index:
                    self._keyword_index[keyword_lower] = []
                self._keyword_index[keyword_lower].append(expert.name)

    def route(self, query: str) -> RoutingResult:
        """
        Analyze query and determine which experts to dispatch.

        Args:
            query: User query to analyze

        Returns:
            RoutingResult with selected experts
        """
        query_lower = query.lower()

        # Score each expert based on keyword matches
        scores: dict[str, float] = {}
        matches: dict[str, list[str]] = {}

        for expert in self.config.experts:
            score = 0.0
            matched_keywords = []

            for keyword in expert.keywords:
                if keyword.lower() in query_lower:
                    score += 1.0
                    matched_keywords.append(keyword)
                    # Bonus for exact word match
                    if re.search(rf"\b{re.escape(keyword.lower())}\b", query_lower):
                        score += 0.5

            # Apply priority bonus
            score += expert.priority * 0.1

            if score > 0:
                scores[expert.name] = score
                matches[expert.name] = matched_keywords

        # Sort by score and select top experts
        sorted_experts = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        selected = sorted_experts[: self.config.max_experts_per_query]

        # Calculate confidence
        if selected:
            max_score = max(scores.values())
            confidence = min(max_score / 3.0, 1.0)  # Normalize to 0-1
        else:
            confidence = 0.0

        # Build reasoning
        if selected:
            reasoning_parts = []
            for name in selected:
                if name in matches:
                    reasoning_parts.append(f"{name}: 匹配关键词 {', '.join(matches[name])}")
            reasoning = "; ".join(reasoning_parts)
        else:
            reasoning = "未找到匹配的专家，将使用默认专家"
            # Fall back to first expert
            if self.config.experts:
                selected = [self.config.experts[0].name]
                confidence = 0.3

        return RoutingResult(
            experts=selected,
            confidence=confidence,
            reasoning=reasoning,
        )

    def get_expert_for_domain(self, domain: str) -> ExpertConfig | None:
        """Get expert by domain name."""
        for expert in self.config.experts:
            if expert.domain == domain:
                return expert
        return None

    def add_expert(self, expert: ExpertConfig) -> None:
        """Add a new expert to the pool."""
        self.config.experts.append(expert)
        # Rebuild index
        self._build_keyword_index()

    def remove_expert(self, name: str) -> bool:
        """Remove an expert from the pool."""
        for i, expert in enumerate(self.config.experts):
            if expert.name == name:
                del self.config.experts[i]
                self._build_keyword_index()
                return True
        return False
