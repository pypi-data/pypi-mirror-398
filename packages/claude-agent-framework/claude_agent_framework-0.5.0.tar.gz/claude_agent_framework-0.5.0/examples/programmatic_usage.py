#!/usr/bin/env python3
"""
Example: Programmatic Usage

Demonstrates advanced programmatic usage of framework components.
"""

import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def programmatic_example():
    """Programmatic usage with full control over components."""
    from claude_agent_framework import create_session

    # Initialize session
    session = create_session(
        "research",
        model="haiku",
        verbose=True,
        log_dir=Path("./custom_logs"),
    )

    # Access internal components if needed
    logger.info(f"Architecture: {session.architecture.name}")
    logger.info(f"Session directory: {session.session_dir}")

    # Run query
    query = "Briefly research cloud computing market size"
    logger.info(f"Executing query: {query}")

    try:
        async for msg in session.run(query):
            print(msg)
    finally:
        await session.teardown()
        logger.info(f"Session saved to: {session.session_dir}")


async def quick_query_example():
    """Quick one-off query without session management."""
    from claude_agent_framework import quick_query

    # Quick query returns all messages
    results = await quick_query(
        "What is the current state of quantum computing?",
        architecture="research",
    )

    print("Results:")
    for msg in results:
        print(msg)


async def context_manager_example():
    """Using session as context manager for automatic cleanup."""
    from claude_agent_framework import create_session

    async with create_session("research") as session:
        async for msg in session.run("Analyze Python web frameworks"):
            print(msg)
    # Session is automatically cleaned up here


async def multiple_queries_example():
    """Run multiple queries in a single session."""
    from claude_agent_framework import create_session

    session = create_session("research")

    queries = [
        "What are the top 3 Python web frameworks?",
        "Compare their performance characteristics",
        "Which is best for beginners?",
    ]

    for query in queries:
        print(f"\n{'=' * 40}")
        print(f"Query: {query}")
        print("=" * 40)

        async for msg in session.run(query):
            print(msg)

    await session.teardown()


if __name__ == "__main__":
    import os

    print("Programmatic Usage Examples")
    print("=" * 40)
    print("1. Full programmatic control")
    print("2. Quick query")
    print("3. Context manager")
    print("4. Multiple queries")
    print("=" * 40)

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set. Please set it to run examples.")
        exit(1)

    choice = input("Select example (1/2/3/4): ").strip()

    if choice == "1":
        asyncio.run(programmatic_example())
    elif choice == "2":
        asyncio.run(quick_query_example())
    elif choice == "3":
        asyncio.run(context_manager_example())
    elif choice == "4":
        asyncio.run(multiple_queries_example())
    else:
        print("Running quick query example")
        asyncio.run(quick_query_example())
