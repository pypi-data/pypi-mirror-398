"""
Helper utility functions for Claude Agent Framework.

Provides convenience functions for common use cases.
"""

from claude_agent_framework.core.types import ArchitectureType, ModelTypeStr


async def quick_query(
    prompt: str,
    architecture: ArchitectureType = "research",
    model: ModelTypeStr = "haiku",
) -> list:
    """
    Execute a single query and return all messages.

    Convenience function for quick, one-off queries. For multiple queries
    or streaming output, use create_session() instead.

    Args:
        prompt: The query to execute
        architecture: Architecture to use
        model: Model to use

    Returns:
        List of all response messages

    Example:
        >>> import asyncio
        >>> from claude_agent_framework import quick_query
        >>>
        >>> results = asyncio.run(quick_query("Analyze Python trends"))
        >>> print(results[-1])  # Print final message
    """
    from claude_agent_framework.session import create_session

    session = create_session(architecture, model=model)
    try:
        return await session.query(prompt)
    finally:
        await session.teardown()
