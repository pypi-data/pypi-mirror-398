"""
OpenAI query implementation.
"""

from typing import List, Dict, Optional, Any


def query_openai(
    client: Any,
    model_name: str,
    messages: List[Dict[str, str]],
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    **kwargs: Any,
) -> Any:
    """
    Query OpenAI with messages.

    Args:
        client: The OpenAI client instance.
        model_name: The model name to use.
        messages: List of message dictionaries with 'role' and 'content' keys.
        max_tokens: Maximum number of tokens to generate.
        temperature: Sampling temperature (0.0 to 2.0).
        tools: Optional list of tool definitions for function calling.
        **kwargs: Additional OpenAI-specific parameters.

    Returns:
        The clean string output from OpenAI, or a dict with function_call if tool was called.
    """
    request_params = {
        "model": model_name,
        "messages": messages,
    }

    if max_tokens is not None:
        request_params["max_tokens"] = max_tokens

    if temperature is not None:
        request_params["temperature"] = temperature

    if tools is not None:
        request_params["tools"] = tools
        request_params["tool_choice"] = "auto"

    request_params.update(kwargs)

    response = client.chat.completions.create(**request_params)
    
    if not response.choices:
        raise ValueError("Empty response from OpenAI API")
    
    message = response.choices[0].message
    
    # Extract usage information
    # Standardize to input_tokens/output_tokens for consistency across providers
    usage = None
    if hasattr(response, "usage") and response.usage:
        usage = {
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }

    # Check for tool_calls (newer API format)
    if hasattr(message, "tool_calls") and message.tool_calls and len(message.tool_calls) > 0:
        # Return tool calls with full information including IDs
        result = {
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": tool_call.type,
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,  # JSON string
                    }
                }
                for tool_call in message.tool_calls
            ]
        }
        if usage:
            result["usage"] = usage
        return result
    elif hasattr(message, "function_call") and message.function_call is not None:
        # Older API format with function_call (legacy support)
        result = {
            "tool_calls": [
                {
                    "id": f"call_{message.function_call.name}",
                    "type": "function",
                    "function": {
                        "name": message.function_call.name,
                        "arguments": message.function_call.arguments,
                    }
                }
            ]
        }
        if usage:
            result["usage"] = usage
        return result

    content = message.content or ""
    if usage:
        return {"content": content, "usage": usage}
    return content
