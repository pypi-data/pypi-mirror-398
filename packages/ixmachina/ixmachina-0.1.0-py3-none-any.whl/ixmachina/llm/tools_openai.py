"""
OpenAI tool conversion utilities.
"""

import inspect
from typing import Callable, Dict, Any, List


def function_to_openai_tool(func: Callable) -> Dict[str, Any]:
    """
    Convert a Python function to OpenAI tool format.

    Args:
        func: The function to convert.

    Returns:
        OpenAI tool format dictionary.
    """
    sig = inspect.signature(func)
    doc = inspect.getdoc(func) or ""
    
    properties = {}
    required = []
    
    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue
        param_type = "string"
        if param.annotation != inspect.Parameter.empty:
            if param.annotation == int:
                param_type = "integer"
            elif param.annotation == float:
                param_type = "number"
            elif param.annotation == bool:
                param_type = "boolean"
            elif param.annotation == dict:
                param_type = "object"
            elif param.annotation == list:
                param_type = "array"
        
        properties[param_name] = {
            "type": param_type,
            "description": "",
        }
        if param.default == inspect.Parameter.empty:
            required.append(param_name)
    
    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": doc.split("\n\n")[0] if doc else "",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


def convert_tools_to_openai(tools: List[Callable]) -> List[Dict[str, Any]]:
    """
    Convert a list of Python functions to OpenAI tool format.

    Args:
        tools: List of callable functions.

    Returns:
        List of OpenAI tool format dictionaries.
    """
    return [function_to_openai_tool(tool) for tool in tools]


def get_tool_schemas_for_openai(tools: List[Callable]) -> Dict[str, Dict[str, Any]]:
    """
    Get tool schemas for type conversion in OpenAI format.

    Args:
        tools: List of callable functions.

    Returns:
        Dictionary mapping tool names to their schemas.
    """
    schemas = {}
    for tool in tools:
        schemas[tool.__name__] = function_to_openai_tool(tool)
    return schemas

