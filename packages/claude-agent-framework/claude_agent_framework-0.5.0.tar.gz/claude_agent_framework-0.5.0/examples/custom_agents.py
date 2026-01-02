#!/usr/bin/env python3
"""
Example: Custom Architecture

Demonstrates how to define and register custom architectures.
"""

import asyncio
from typing import Any

from claude_agent_framework import create_session, register_architecture
from claude_agent_framework.core.base import BaseArchitecture


# Define a custom architecture
@register_architecture("custom_qa")
class CustomQAArchitecture(BaseArchitecture):
    """Custom Q&A architecture with expert routing."""

    name = "custom_qa"
    description = "Custom Q&A system with expert routing"

    def get_agents(self) -> dict[str, Any]:
        """Define available agents."""
        return {
            "expert": {
                "description": "Domain expert for answering questions",
                "tools": ["WebSearch", "Read"],
                "model": "haiku",
            },
            "summarizer": {
                "description": "Summarizes expert responses",
                "tools": ["Write"],
                "model": "haiku",
            },
        }

    async def execute(
        self,
        prompt: str,
        tracker: Any = None,
        transcript: Any = None,
    ):
        """Execute the custom Q&A workflow."""
        # This is a simplified example
        # In practice, you would implement the full workflow here
        yield f"Processing question: {prompt}"
        yield "Routing to appropriate expert..."
        yield "Expert analysis complete."
        yield "Generating summary..."


async def custom_architecture_example():
    """Use a custom registered architecture."""
    # The custom_qa architecture is now available
    session = create_session("custom_qa")

    async for msg in session.run("What are the best practices for Python async programming?"):
        print(msg)


async def list_architectures_example():
    """List all available architectures including custom ones."""
    from claude_agent_framework import get_available_architectures

    architectures = get_available_architectures()
    print("Available architectures:")
    for name, info in architectures.items():
        print(f"  - {name}: {info.get('description', 'No description')}")


if __name__ == "__main__":
    print("Custom Architecture Example")
    print("=" * 40)

    # List all architectures (including our custom one)
    asyncio.run(list_architectures_example())

    print("\nRunning custom Q&A architecture...")
    asyncio.run(custom_architecture_example())
