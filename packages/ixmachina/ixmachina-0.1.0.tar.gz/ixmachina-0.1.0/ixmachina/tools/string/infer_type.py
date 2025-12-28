"""
Tools for inferring the best type a string can be converted to.
"""

import json
from typing import Dict, Any, Optional, Union


def infer_string_type(
    text: str,
    llm: Optional[Any] = None,
    max_length: int = 2000,
) -> Dict[str, Any]:
    """
    Infer the best type a string can be converted to (dict, list, int, float, bool, str).

    First tries JSON parsing, then falls back to LLM if provided and JSON fails.

    Args:
        text: The string to analyze.
        llm: Optional LLM instance to use for inference if JSON parsing fails.
            Can be passed via special objects as "use:llm".
        max_length: Maximum length of text to send to LLM. If text is longer, it will be
            truncated and a note will be added to the prompt. Default is 2000.

    Returns:
        Dictionary with:
            - type: The inferred type name (e.g., "dict", "list", "int", "float", "bool", "str")
            - value: The converted value (if conversion successful)
            - success: Boolean indicating if type inference was successful
            - method: How the type was inferred ("json", "llm", or "fallback")
            - error: Error message if inference failed (None if successful)
    """
    # Try JSON parsing first (fastest and most reliable)
    try:
        parsed = json.loads(text.strip())
        python_type = type(parsed).__name__
        
        # Map JSON types to Python type names
        type_mapping = {
            "dict": "dict",
            "list": "list",
            "int": "int",
            "float": "float",
            "bool": "bool",
            "str": "str",
        }
        
        inferred_type = type_mapping.get(python_type, "str")
        
        return {
            "type": inferred_type,
            "value": parsed,
            "success": True,
            "method": "json",
            "error": None,
        }
    except (json.JSONDecodeError, ValueError):
        # JSON parsing failed, try LLM if provided
        if llm is not None:
            return _infer_type_with_llm(text=text, llm=llm, max_length=max_length)
        else:
            # No LLM provided, try basic type inference
            return _infer_type_basic(text=text)


def _infer_type_basic(text: str) -> Dict[str, Any]:
    """
    Basic type inference without LLM (tries common patterns).

    Args:
        text: The string to analyze.

    Returns:
        Dictionary with type inference result.
    """
    text = text.strip()
    
    # Try int
    try:
        if text.isdigit() or (text.startswith("-") and text[1:].isdigit()):
            return {
                "type": "int",
                "value": int(text),
                "success": True,
                "method": "fallback",
                "error": None,
            }
    except ValueError:
        pass
    
    # Try float
    try:
        float_val = float(text)
        # Only return float if it's not actually an int
        if "." in text or "e" in text.lower() or "E" in text:
            return {
                "type": "float",
                "value": float_val,
                "success": True,
                "method": "fallback",
                "error": None,
            }
    except ValueError:
        pass
    
    # Try bool
    text_lower = text.lower()
    if text_lower in ("true", "false"):
        return {
            "type": "bool",
            "value": text_lower == "true",
            "success": True,
            "method": "fallback",
            "error": None,
        }
    
    # Default to string
    return {
        "type": "str",
        "value": text,
        "success": True,
        "method": "fallback",
        "error": None,
    }


def _infer_type_with_llm(text: str, llm: Any, max_length: int = 2000) -> Dict[str, Any]:
    """
    Use LLM to infer the type of a string.

    Args:
        text: The string to analyze.
        llm: LLM instance to use for inference.
        max_length: Maximum length of text to send to LLM.

    Returns:
        Dictionary with type inference result.
    """
    try:
        original_length = len(text)
        truncated_text = text[:max_length]
        was_truncated = original_length > max_length
        
        truncation_note = ""
        if was_truncated:
            truncation_note = f"\n\nNote: The string was truncated at {max_length} characters (original length: {original_length})."
        
        prompt = f"""Analyze this string and determine what type it represents. 
The string should be converted to one of: dict, list, int, float, bool, or str.

String to analyze:
{truncated_text}{truncation_note}

Respond with ONLY a valid JSON object in this exact format:
{{
    "type": "dict|list|int|float|bool|str",
    "value": <the converted value>
}}

For example, if the string is '{{"key": "value"}}', respond:
{{"type": "dict", "value": {{"key": "value"}}}}

If the string is '[1, 2, 3]', respond:
{{"type": "list", "value": [1, 2, 3]}}

If the string is '42', respond:
{{"type": "int", "value": 42}}

Return ONLY the JSON, nothing else."""

        llm_response = llm.query(user_prompt=prompt)
        
        # Extract content if it's a dict
        if isinstance(llm_response, dict):
            response_text = llm_response.get("content", str(llm_response))
        else:
            response_text = str(llm_response)
        
        # Try to parse the LLM's JSON response
        # Sometimes LLM wraps it in markdown code blocks
        response_text = response_text.strip()
        if response_text.startswith("```"):
            # Extract JSON from code block
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text
        
        parsed_response = json.loads(response_text)
        
        inferred_type = parsed_response.get("type", "str")
        converted_value = parsed_response.get("value", text)
        
        return {
            "type": inferred_type,
            "value": converted_value,
            "success": True,
            "method": "llm",
            "error": None,
        }
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        # LLM inference failed, fall back to basic inference
        return _infer_type_basic(text=text)
    except Exception as e:
        return {
            "type": "str",
            "value": text,
            "success": False,
            "method": "llm",
            "error": f"Error using LLM for type inference: {str(e)}",
        }

