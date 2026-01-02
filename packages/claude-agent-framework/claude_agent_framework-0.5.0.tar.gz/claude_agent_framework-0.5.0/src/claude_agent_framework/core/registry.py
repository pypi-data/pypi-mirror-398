"""
Architecture registry for dynamic architecture discovery and loading.

Provides:
- @register_architecture decorator for registering new architectures
- get_architecture() for retrieving registered architectures
- list_architectures() for discovering available architectures
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from claude_agent_framework.core.base import BaseArchitecture

# Global registry mapping architecture names to their classes
_ARCHITECTURES: dict[str, type[BaseArchitecture]] = {}


def register_architecture(name: str) -> Callable[[type], type]:
    """
    Decorator to register an architecture class.

    Usage:
        @register_architecture("pipeline")
        class PipelineArchitecture(BaseArchitecture):
            ...

    Args:
        name: Unique name for the architecture

    Returns:
        Decorator function
    """

    def decorator(cls: type) -> type:
        if name in _ARCHITECTURES:
            raise ValueError(
                f"Architecture '{name}' is already registered by {_ARCHITECTURES[name].__name__}"
            )
        _ARCHITECTURES[name] = cls
        # Also set the class attribute
        cls.name = name
        return cls

    return decorator


def get_architecture(name: str) -> type[BaseArchitecture]:
    """
    Get an architecture class by name.

    Args:
        name: Name of the architecture

    Returns:
        Architecture class

    Raises:
        KeyError: If architecture is not registered
    """
    if name not in _ARCHITECTURES:
        available = ", ".join(sorted(_ARCHITECTURES.keys()))
        raise KeyError(
            f"Architecture '{name}' not found. Available: {available or '(none registered)'}"
        )
    return _ARCHITECTURES[name]


def list_architectures() -> list[str]:
    """
    List all registered architecture names.

    Returns:
        Sorted list of architecture names
    """
    return sorted(_ARCHITECTURES.keys())


def get_architecture_info() -> dict[str, dict[str, str]]:
    """
    Get detailed information about all registered architectures.

    Returns:
        Dict mapping name to {name, description, class}
    """
    return {
        name: {
            "name": name,
            "description": cls.description,
            "class": f"{cls.__module__}.{cls.__name__}",
        }
        for name, cls in sorted(_ARCHITECTURES.items())
    }


def unregister_architecture(name: str) -> bool:
    """
    Unregister an architecture (mainly for testing).

    Args:
        name: Name of architecture to unregister

    Returns:
        True if was registered, False otherwise
    """
    if name in _ARCHITECTURES:
        del _ARCHITECTURES[name]
        return True
    return False


def clear_registry() -> None:
    """Clear all registered architectures (for testing)."""
    _ARCHITECTURES.clear()


def load_builtin_architectures() -> None:
    """
    Load all built-in architectures.

    This imports all architecture modules to trigger registration.
    Should be called once at framework startup.
    """
    # Import architecture modules to trigger registration
    # Each module should use @register_architecture decorator
    try:
        from claude_agent_framework.architectures import (  # noqa: F401
            critic_actor,
            debate,
            mapreduce,
            pipeline,
            reflexion,
            research,
            specialist_pool,
        )
    except ImportError:
        # Architectures not yet implemented
        pass
