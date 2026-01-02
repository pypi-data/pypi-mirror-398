#!/usr/bin/env python3
"""
Example: Basic Usage

Demonstrates how to use Claude Agent Framework with the simplified init() API.
"""

import asyncio

from claude_agent_framework import create_session


async def basic_example():
    """Basic usage with the simplified init() API."""
    # Initialize session with default settings
    # API key validation, directory creation, and logging are handled automatically
    session = create_session("research")

    # Run interactive session
    async for msg in session.run("Analyze AI market trends in 2024"):
        print(msg)


async def single_query_example():
    """Single query example."""
    session = create_session("research")

    # Execute single query
    async for msg in session.run("Research applications of AI in healthcare"):
        print(msg)


async def with_options_example():
    """Example with custom options."""
    # Initialize with options
    session = create_session(
        "research",
        model="sonnet",  # Use a more powerful model
        verbose=True,  # Enable debug logging
    )

    # Run session
    async for msg in session.run("Analyze quantum computing market"):
        print(msg)


async def different_architectures_example():
    """Example using different architectures."""
    # Pipeline architecture for code development
    pipeline_session = create_session("pipeline")
    async for msg in pipeline_session.run("Create a simple REST API"):
        print(msg)

    # Debate architecture for decision support
    debate_session = create_session("debate")
    async for msg in debate_session.run("Should we use microservices or monolith?"):
        print(msg)


if __name__ == "__main__":
    print("Claude Agent Framework Examples")
    print("=" * 40)
    print("1. Basic interactive session")
    print("2. Single query")
    print("3. With custom options")
    print("4. Different architectures")
    print("=" * 40)

    choice = input("Select example (1/2/3/4): ").strip()

    if choice == "1":
        asyncio.run(basic_example())
    elif choice == "2":
        asyncio.run(single_query_example())
    elif choice == "3":
        asyncio.run(with_options_example())
    elif choice == "4":
        asyncio.run(different_architectures_example())
    else:
        print("Running default example")
        asyncio.run(basic_example())
