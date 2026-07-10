"""CLI entry point for smoke testing."""

from __future__ import annotations

import sys
import uuid

from langchain_core.messages import HumanMessage

from revenue_leakage_agent.graph import build_graph


def main() -> None:
    """Run a single-message smoke test against the agent."""
    message = (
        " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Check plan C-1001 for revenue leakage"
    )
    app = build_graph()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    result = app.invoke({"messages": [HumanMessage(content=message)]}, config=config)
    for msg in result["messages"]:
        msg.pretty_print()


if __name__ == "__main__":
    main()
