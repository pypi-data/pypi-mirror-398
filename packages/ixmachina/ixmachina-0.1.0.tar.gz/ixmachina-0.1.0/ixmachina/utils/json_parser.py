"""
Utilities for parsing JSON and Python literal formats.
"""

import json
import ast
from typing import Any


def parse_json_or_python_literal(value: str) -> Any:
    """
    Parse a string that might be JSON or Python literal format.
    
    Handles both JSON (double quotes) and Python literals (single quotes).
    Falls back to original string if parsing fails.
    
    Args:
        value: String to parse (should look like JSON or Python literal).
        
    Returns:
        Parsed value (dict, list, int, float, bool) or original string if parsing fails.
    """
    if not isinstance(value, str) or not value.strip().startswith(("{", "[", "'", '"')):
        return value
    
    # Try JSON first (double quotes)
    try:
        parsed = json.loads(value)
        if isinstance(parsed, (dict, list, int, float, bool)):
            return parsed
    except (json.JSONDecodeError, ValueError):
        pass
    
    # If JSON fails, try Python literal (single quotes, etc.)
    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, (dict, list, int, float, bool)):
            return parsed
    except (ValueError, SyntaxError):
        pass
    
    # Return original string if all parsing fails
    return value

