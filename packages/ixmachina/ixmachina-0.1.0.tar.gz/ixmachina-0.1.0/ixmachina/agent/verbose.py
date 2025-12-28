"""
Verbose logging utilities for Agent.
"""

from typing import List, Dict, Any, Optional
import json


def print_iteration(iteration: int, max_iterations: int) -> None:
    """
    Print iteration information.
    
    Args:
        iteration: Current iteration number.
        max_iterations: Maximum number of iterations.
    """
    print(f"\n[Agent] Iteration {iteration}/{max_iterations}")


def print_conversation_context(conversation_history: List[Dict[str, Any]], num_messages: int = 3) -> None:
    """
    Print recent conversation context.
    
    Args:
        conversation_history: Full conversation history.
        num_messages: Number of recent messages to show.
    """
    print(f"[Agent] Recent conversation context:")
    recent_messages = conversation_history[-num_messages:] if len(conversation_history) > num_messages else conversation_history
    for msg in recent_messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if role == "user":
            print(f"  User: {content}")
        elif role == "assistant":
            if content:
                print(f"  Assistant: {content[:200]}{'...' if len(content) > 200 else ''}")
            elif "tool_calls" in msg:
                print(f"  Assistant: [calling tools]")
        elif role == "tool":
            print(f"  Tool: {content[:200]}{'...' if len(content) > 200 else ''}")


def print_llm_response(response: Any) -> None:
    """
    Print LLM response information.
    
    Args:
        response: The LLM response (can be string or dict with tool_calls).
    """
    if isinstance(response, dict) and "tool_calls" in response:
        print(f"[Agent] LLM decided to call tools")
    elif isinstance(response, str):
        print(f"[Agent] LLM response: {response[:300]}{'...' if len(response) > 300 else ''}")


def print_tool_calls(tool_calls: List[Dict[str, Any]]) -> None:
    """
    Print tool call information.
    
    Args:
        tool_calls: List of tool call dictionaries.
    """
    print(f"[Agent] LLM decided to call {len(tool_calls)} tool(s):")
    for tool_call in tool_calls:
        func_name = tool_call["function"]["name"]
        func_args = tool_call["function"]["arguments"]
        # Try to parse and pretty-print the arguments
        try:
            args_dict = json.loads(func_args)
            args_str = ", ".join([f"{k}={v}" for k, v in args_dict.items()])
            print(f"  → {func_name}({args_str})")
        except:
            print(f"  → {func_name}({func_args})")


def print_tool_result(tool_name: str, result: Any) -> None:
    """
    Print tool execution result.
    
    Args:
        tool_name: Name of the tool that was executed.
        result: The result from the tool execution.
    """
    string_result = str(result)
    if isinstance(result, str) and result.startswith("Error executing tool"):
        print(f"[Agent] Tool '{tool_name}' failed: {result}")
    else:
        result_preview = string_result[:150] + "..." if len(string_result) > 150 else string_result
        print(f"[Agent] Tool '{tool_name}' returned: {result_preview}")

