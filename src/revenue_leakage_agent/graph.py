"""LangGraph ReAct agent with MemorySaver."""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from revenue_leakage_agent.llm import get_llm
from revenue_leakage_agent.prompts import SYSTEM_PROMPT
from revenue_leakage_agent.tool_call_parser import parse_text_tool_calls
from revenue_leakage_agent.tools import ALL_TOOLS


def build_graph() -> Any:
    """Build and compile the Revenue Leakage Agent graph."""
    llm = get_llm()
    checkpointer = MemorySaver()
    return create_react_agent(
        llm,
        ALL_TOOLS,
        prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
        post_model_hook=parse_text_tool_calls,
    )
