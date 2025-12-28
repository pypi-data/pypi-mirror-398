"""
Provider-agnostic tool conversion utilities.
"""

from typing import List, Dict, Any, Callable, Optional


def prepare_tools_for_provider(
    tools: List[Callable],
    provider: str,
) -> Dict[str, Any]:
    """
    Prepare tools for a specific provider.

    Converts Python functions to provider-specific tool format and returns
    both the tools and schemas needed for type conversion.

    Args:
        tools: List of callable functions.
        provider: Provider name (e.g., "openai", "anthropic").

    Returns:
        Dictionary with:
            - "tools": List of tools in provider format
            - "schemas": Dictionary mapping tool names to schemas for type conversion
    """
    if provider == "openai":
        from .tools_openai import convert_tools_to_openai, get_tool_schemas_for_openai
        return {
            "tools": convert_tools_to_openai(tools),
            "schemas": get_tool_schemas_for_openai(tools),
        }
    else:
        # Future: add other providers
        return {
            "tools": [],
            "schemas": {},
        }

