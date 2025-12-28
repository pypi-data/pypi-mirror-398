"""
ixmachina - A package to simplify and wrap connections to LLMs with RAG, memory, and MCP support.
"""

from .llm import LLM, EnvVar
from .format_output import format_output
from .agent import Agent

__version__ = "0.1.0"

__all__ = ["LLM", "format_output", "EnvVar", "Agent"]

