"""
Anthropic query implementation.
"""

from typing import List, Dict, Optional, Any


def query_anthropic(
    client: Any,
    model_name: str,
    messages: List[Dict[str, str]],
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    **kwargs: Any,
) -> str:
    """
    Query Anthropic with messages.

    Args:
        client: The Anthropic client instance.
        model_name: The model name to use.
        messages: List of message dictionaries with 'role' and 'content' keys.
        max_tokens: Maximum number of tokens to generate.
        temperature: Sampling temperature (0.0 to 1.0).
        **kwargs: Additional Anthropic-specific parameters.

    Returns:
        The clean string output from Anthropic.
    """
    # Separate system messages from conversation messages
    system_prompt = None
    conversation_messages = []
    system_prompts = []

    for message in messages:
        if message.get("role") == "system":
            system_prompts.append(message.get("content"))
        else:
            conversation_messages.append(message)
    
    # Combine multiple system messages if present
    if len(system_prompts) > 1:
        system_prompt = "\n\n".join(system_prompts)
    elif len(system_prompts) == 1:
        system_prompt = system_prompts[0]

    message_params = {
        "model": model_name,
        "messages": conversation_messages,
    }

    if system_prompt:
        message_params["system"] = system_prompt

    if max_tokens is not None:
        message_params["max_tokens"] = max_tokens

    if temperature is not None:
        message_params["temperature"] = temperature

    message_params.update(kwargs)

    response = client.messages.create(**message_params)
    
    # Extract usage information
    usage = None
    if hasattr(response, "usage") and response.usage:
        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
        }
    
    if not response.content:
        raise ValueError("Empty response from Anthropic API")
    
    content = response.content[0].text
    if usage:
        return {"content": content, "usage": usage}
    return content
