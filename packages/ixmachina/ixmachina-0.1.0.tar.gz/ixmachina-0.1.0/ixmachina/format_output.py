"""
Output formatting utilities for LLM responses.
"""

import json
from typing import Any, Optional, Union, Type


def format_output(
    llm: Any,
    output_string: str,
    output_format: Optional[Union[Type, str]] = None,
    infer_format: bool = False,
) -> Any:
    """
    Convert LLM output string to the desired format.

    First attempts to parse using json or type casting. If that fails,
    uses the LLM to help convert the output.

    Args:
        llm: An LLM instance (from ixmachina.llm.LLM).
        output_string: The string output from the LLM query.
        output_format: The desired output format. Can be:
            - A type: int, float, str, dict, list
            - A string: "int", "float", "str", "dict", "list", "json"
            - None: Will attempt to infer if infer_format is True
        infer_format: If True and output_format is None, attempts to infer
            the output format from the string.

    Returns:
        The converted output in the desired format.

    Raises:
        ValueError: If the format cannot be determined or conversion fails.
    """
    # Normalize output_format
    if output_format is None:
        if infer_format:
            output_format = _infer_format(output_string=output_string, llm=llm)
        else:
            raise ValueError(
                "Either output_format must be provided or infer_format must be True"
            )

    # Special handling for "json" format - can be dict or list
    if isinstance(output_format, str) and output_format.lower() == "json":
        return _parse_json_flexible(llm=llm, output_string=output_string)

    # Normalize format to type
    target_type = _normalize_format(output_format=output_format)

    # Try direct parsing/casting first
    try:
        return _try_direct_conversion(output_string=output_string, target_type=target_type)
    except (ValueError, json.JSONDecodeError, TypeError):
        # If direct conversion fails, use LLM to help
        return _convert_with_llm(
            llm=llm,
            output_string=output_string,
            target_type=target_type,
        )


def _normalize_format(output_format: Union[Type, str]) -> Type:
    """
    Normalize output format string to a type.

    Args:
        output_format: Format as type or string.

    Returns:
        The normalized type.
    """
    if isinstance(output_format, type):
        return output_format

    format_map = {
        "int": int,
        "float": float,
        "str": str,
        "dict": dict,
        "list": list,
        # Note: "json" is handled separately as it can be dict or list
    }

    format_lower = output_format.lower() if isinstance(output_format, str) else str(output_format)
    if format_lower in format_map:
        return format_map[format_lower]

    raise ValueError(f"Unsupported output format: {output_format}")


def _try_direct_conversion(output_string: str, target_type: Type) -> Any:
    """
    Attempt direct conversion using json or type casting.

    Args:
        output_string: The string to convert.
        target_type: The target type.

    Returns:
        The converted value.

    Raises:
        ValueError: If conversion fails.
    """
    output_string = output_string.strip()

    # Try JSON parsing for dict/list
    if target_type in (dict, list):
        try:
            parsed = json.loads(output_string)
            if isinstance(parsed, target_type):
                return parsed
            # If JSON parsed but wrong type, try to convert
            if target_type == dict and isinstance(parsed, list):
                raise ValueError("JSON is a list, not a dict")
            if target_type == list and isinstance(parsed, dict):
                raise ValueError("JSON is a dict, not a list")
            return parsed
        except json.JSONDecodeError:
            # Try extracting JSON from markdown code blocks
            if "```json" in output_string or "```" in output_string:
                # Extract content between code blocks
                start = output_string.find("```")
                if start != -1:
                    start = output_string.find("\n", start) + 1
                    end = output_string.rfind("```")
                    if end != -1:
                        json_content = output_string[start:end].strip()
                        parsed = json.loads(json_content)
                        if isinstance(parsed, target_type):
                            return parsed
                        raise ValueError(f"Extracted JSON is not {target_type.__name__}")

    # Try type casting for primitive types
    if target_type == int:
        # Remove common non-numeric characters
        cleaned = output_string.replace(",", "").strip()
        return int(cleaned)
    elif target_type == float:
        cleaned = output_string.replace(",", "").strip()
        return float(cleaned)
    elif target_type == str:
        return output_string

    raise ValueError(f"Direct conversion to {target_type.__name__} failed")


def _convert_with_llm(
    llm: Any,
    output_string: str,
    target_type: Type,
) -> Any:
    """
    Use LLM to help convert the output string to the desired format.

    Args:
        llm: An LLM instance.
        output_string: The string to convert.
        target_type: The target type.

    Returns:
        The converted value.
    """
    type_name = target_type.__name__

    if target_type == dict:
        prompt = f"""Convert the following text into a valid JSON dictionary/object.
        The JSON can contain nested dictionaries and lists. Return ONLY the JSON object, nothing else. 
        No explanations, no markdown, just the JSON.

        Text to convert:
        {output_string}

        Return the JSON object:"""

    elif target_type == list:
        prompt = f"""Convert the following text into a valid JSON array/list.
        The JSON can contain nested dictionaries and lists. Return ONLY the JSON array, nothing else. 
        No explanations, no markdown, just the JSON.

        Text to convert:
        {output_string}

        Return the JSON array:"""

    elif target_type == int:
        prompt = f"""Extract the integer number from the following text.
        Return ONLY the integer number, nothing else. No explanations, no text, just the number.

        Text to extract from:
        {output_string}

        Return the integer:"""

    elif target_type == float:
        prompt = f"""Extract the floating point number from the following text.
        Return ONLY the number, nothing else. No explanations, no text, just the number.

        Text to extract from:
        {output_string}

        Return the number:"""

    else:
        # For str or other types, just return as is
        return output_string

    # Query the LLM
    response = llm.query(user_prompt=prompt)

    # Try to parse the response
    try:
        return _try_direct_conversion(output_string=response, target_type=target_type)
    except (ValueError, json.JSONDecodeError, TypeError) as e:
        raise ValueError(
            f"LLM-assisted conversion to {type_name} failed. "
            f"LLM response: {response}. Error: {str(e)}"
        )


def _parse_json_flexible(llm: Any, output_string: str) -> Any:
    """
    Parse JSON that can be either a dict or a list.

    Args:
        llm: An LLM instance.
        output_string: The string to parse.

    Returns:
        The parsed JSON (dict or list).
    """
    # Try direct JSON parsing first
    try:
        parsed = json.loads(output_string.strip())
        if isinstance(parsed, (dict, list)):
            return parsed
    except json.JSONDecodeError:
        # Try extracting from markdown code blocks
        if "```json" in output_string or "```" in output_string:
            start = output_string.find("```")
            if start != -1:
                start = output_string.find("\n", start) + 1
                end = output_string.rfind("```")
                if end != -1:
                    json_content = output_string[start:end].strip()
                    try:
                        parsed = json.loads(json_content)
                        if isinstance(parsed, (dict, list)):
                            return parsed
                    except json.JSONDecodeError:
                        pass

    # If direct parsing fails, use LLM to help
    prompt = f"""Convert the following text into valid JSON.
    The JSON can be either a dictionary/object or an array/list, whichever is most appropriate.
    The JSON can contain nested dictionaries and lists. Return ONLY the JSON, nothing else. 
    No explanations, no markdown, just the JSON.

    Text to convert:
    {output_string}

    Return the JSON:"""

    response = llm.query(user_prompt=prompt)

    # Try to parse the LLM response
    try:
        parsed = json.loads(response.strip())
        if isinstance(parsed, (dict, list)):
            return parsed
        raise ValueError(f"LLM returned JSON but it's not a dict or list: {type(parsed)}")
    except json.JSONDecodeError as e:
        raise ValueError(
            f"LLM-assisted JSON parsing failed. "
            f"LLM response: {response}. Error: {str(e)}"
        )


def _infer_format(output_string: str, llm: Any) -> Type:
    """
    Infer the output format from the string using LLM.

    Args:
        output_string: The string to analyze.
        llm: An LLM instance.

    Returns:
        The inferred type.
    """
    prompt = f"""Analyze the following text and determine what type of data structure it represents.
    Respond with ONLY one word: "dict", "list", "int", "float", or "str".

    Text to analyze:
    {output_string}

    Respond with the type:"""

    response = llm.query(user_prompt=prompt)
    response_clean = response.strip().lower()

    # Map response to type
    type_map = {
        "dict": dict,
        "dictionary": dict,
        "json": dict,
        "object": dict,
        "list": list,
        "array": list,
        "int": int,
        "integer": int,
        "float": float,
        "number": float,
        "str": str,
        "string": str,
        "text": str,
    }

    for key, value in type_map.items():
        if key in response_clean:
            return value

    # Default to string if can't determine
    return str

