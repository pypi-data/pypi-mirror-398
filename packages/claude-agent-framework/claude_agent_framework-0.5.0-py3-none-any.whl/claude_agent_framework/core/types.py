"""
Centralized type definitions for Claude Agent Framework.

This module provides all public type aliases and enums used throughout the framework.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

__all__ = [
    "ModelType",
    "ModelTypeStr",
    "ArchitectureType",
    "RoleType",
    "RoleTypeStr",
    "RoleCardinality",
]


# Architecture types
ArchitectureType = Literal[
    "research",
    "pipeline",
    "critic_actor",
    "specialist_pool",
    "debate",
    "reflexion",
    "mapreduce",
]


# Model type as Enum (canonical, for Pydantic)
class ModelType(str, Enum):
    """Supported Claude model types."""

    HAIKU = "haiku"
    SONNET = "sonnet"
    OPUS = "opus"


# Model type as Literal (for init() backward compat)
ModelTypeStr = Literal["haiku", "sonnet", "opus"]


# Role types for role-based architecture
class RoleType(str, Enum):
    """
    Standard role types for multi-agent architectures.

    Each role type represents a semantic function that agents can fulfill
    within an architecture's workflow.
    """

    # Coordination roles
    COORDINATOR = "coordinator"  # Orchestrates overall workflow

    # Execution roles
    WORKER = "worker"  # Parallel task execution
    PROCESSOR = "processor"  # Data processing/analysis
    SYNTHESIZER = "synthesizer"  # Result aggregation/synthesis

    # Evaluation roles
    CRITIC = "critic"  # Evaluates/critiques output
    JUDGE = "judge"  # Makes final decisions

    # Specialized roles
    SPECIALIST = "specialist"  # Domain-specific expert
    ADVOCATE = "advocate"  # Argues a position

    # Processing roles (MapReduce pattern)
    MAPPER = "mapper"  # Parallel mapping
    REDUCER = "reducer"  # Result reduction

    # Reflection roles
    EXECUTOR = "executor"  # Executes actions
    REFLECTOR = "reflector"  # Reflects on results

    # Pipeline roles
    STAGE_EXECUTOR = "stage_executor"  # Sequential stage execution


RoleTypeStr = Literal[
    "coordinator",
    "worker",
    "processor",
    "synthesizer",
    "critic",
    "judge",
    "specialist",
    "advocate",
    "mapper",
    "reducer",
    "executor",
    "reflector",
    "stage_executor",
]


class RoleCardinality(str, Enum):
    """
    Cardinality constraints for role instantiation.

    Defines how many agent instances can fill a particular role.
    """

    EXACTLY_ONE = "exactly_one"  # Must have exactly 1 instance
    ONE_OR_MORE = "one_or_more"  # Must have at least 1, can have many
    ZERO_OR_MORE = "zero_or_more"  # Optional, can have many
    ZERO_OR_ONE = "zero_or_one"  # Optional, at most 1
