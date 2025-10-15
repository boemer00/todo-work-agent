"""
Monitoring and observability for the LangGraph agent.

This package provides LangSmith integration for:
- Automatic tracing of LLM calls and tool executions
- Custom metadata tracking
- Agent evaluation and quality metrics
"""

from .langsmith_config import setup_langsmith, add_metadata
from .evaluators import (
    evaluate_tool_selection,
    evaluate_response_quality,
    evaluate_task_completion
)

__all__ = [
    "setup_langsmith",
    "add_metadata",
    "evaluate_tool_selection",
    "evaluate_response_quality",
    "evaluate_task_completion",
]
