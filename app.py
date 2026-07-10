"""Streamlit chat UI for the Revenue Leakage Agent."""

from __future__ import annotations

import json
import uuid
from typing import Any

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from revenue_leakage_agent.graph import build_graph
from revenue_leakage_agent.llm import get_llm
from revenue_leakage_agent.tool_call_parser import looks_like_text_tool_calls, strip_thinking_tags
from revenue_leakage_agent.ui_pending import is_approval_message, resolve_pending_action


def _init_session() -> None:
    """Initialize Streamlit session state."""
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())
    if "graph_app" not in st.session_state:
        st.session_state.graph_app = build_graph()
    if "chat_history" not in st.session_state:
        st.session_state.chat_history: list[dict[str, Any]] = []
    if "pending_action" not in st.session_state:
        st.session_state.pending_action = None


def _extract_assistant_response(messages: list) -> str:
    """Pick the final natural-language assistant reply from graph messages."""
    for msg in reversed(messages):
        if not isinstance(msg, AIMessage) or not msg.content or msg.tool_calls:
            continue
        text = strip_thinking_tags(str(msg.content))
        if text and not looks_like_text_tool_calls(text):
            return text
    return "No response generated."


def _format_tool_result(content: Any) -> str:
    """Pretty-print tool output for the UI."""
    if not content:
        return ""
    text = str(content)
    try:
        parsed = json.loads(text)
        return json.dumps(parsed, indent=2)
    except (json.JSONDecodeError, TypeError):
        return text


def _format_tool_args(args: dict[str, Any]) -> str:
    """Format tool arguments for display."""
    if not args:
        return ""
    return json.dumps(args, indent=2)


def _build_tool_trace(messages: list) -> list[dict[str, Any]]:
    """Build structured tool trace from graph messages."""
    trace: list[dict[str, Any]] = []
    pending_by_id: dict[str, dict[str, Any]] = {}

    for msg in messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tool_call in msg.tool_calls:
                step = {
                    "tool": tool_call["name"],
                    "args": tool_call.get("args", {}),
                    "result": None,
                    "tool_call_id": tool_call.get("id"),
                }
                trace.append(step)
                if step["tool_call_id"]:
                    pending_by_id[step["tool_call_id"]] = step
        elif isinstance(msg, ToolMessage):
            step = pending_by_id.get(msg.tool_call_id)
            if step is None:
                step = {
                    "tool": msg.name or "unknown",
                    "args": {},
                    "result": None,
                    "tool_call_id": msg.tool_call_id,
                }
                trace.append(step)
            step["result"] = _format_tool_result(msg.content)
            step["tool"] = msg.name or step["tool"]

    return trace


def _render_tool_trace_ui(tool_trace: list[dict[str, Any]]) -> None:
    """Render persisted tool activity under an assistant message."""
    if not tool_trace:
        return

    label = f"Tool activity ({len(tool_trace)} call{'s' if len(tool_trace) != 1 else ''})"
    with st.expander(label, expanded=True):
        for index, step in enumerate(tool_trace, start=1):
            st.markdown(f"**{index}. `{step['tool']}`**")
            if step.get("args"):
                st.caption("Arguments")
                st.code(_format_tool_args(step["args"]), language="json")
            if step.get("result"):
                st.caption("Result")
                st.code(step["result"], language="json")
            if index < len(tool_trace):
                st.divider()


def _record_tool_call(
    tool_trace: list[dict[str, Any]],
    pending_by_id: dict[str, dict[str, Any]],
    tool_call: dict[str, Any],
) -> dict[str, Any]:
    """Append a tool call step and index it by tool_call_id."""
    step = {
        "tool": tool_call["name"],
        "args": tool_call.get("args", {}),
        "result": None,
        "tool_call_id": tool_call.get("id"),
    }
    tool_trace.append(step)
    if step["tool_call_id"]:
        pending_by_id[step["tool_call_id"]] = step
    return step


def _record_tool_result(
    tool_trace: list[dict[str, Any]],
    pending_by_id: dict[str, dict[str, Any]],
    message: ToolMessage,
) -> dict[str, Any] | None:
    """Attach a tool result to its matching call step."""
    step = pending_by_id.get(message.tool_call_id)
    if step is None:
        step = {
            "tool": message.name or "unknown",
            "args": {},
            "result": None,
            "tool_call_id": message.tool_call_id,
        }
        tool_trace.append(step)
    step["result"] = _format_tool_result(message.content)
    step["tool"] = message.name or step["tool"]
    return step


def _process_stream_update(
    update: dict[str, Any],
    tool_trace: list[dict[str, Any]],
    pending_by_id: dict[str, dict[str, Any]],
    status: Any,
) -> None:
    """Handle one LangGraph stream update and emit live tool observability."""
    for node_name, node_update in update.items():
        if not node_update or node_name == "post_model_hook":
            continue

        messages = node_update.get("messages", [])
        if node_name == "agent":
            for msg in messages:
                if isinstance(msg, AIMessage) and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        _record_tool_call(tool_trace, pending_by_id, tool_call)
                        status.write(
                            f"**Calling** `{tool_call['name']}`\n\n"
                            f"```json\n{_format_tool_args(tool_call.get('args', {}))}\n```"
                        )
                    status.update(
                        label=f"Running {len(msg.tool_calls)} tool(s)...",
                        state="running",
                    )
        elif node_name == "tools":
            for msg in messages:
                if not isinstance(msg, ToolMessage):
                    continue
                step = _record_tool_result(tool_trace, pending_by_id, msg)
                if step is None:
                    continue
                preview = step["result"][:400]
                if len(step["result"]) > 400:
                    preview += "\n..."
                status.write(f"**Completed** `{step['tool']}`\n\n```json\n{preview}\n```")
                status.update(label=f"Completed `{step['tool']}`", state="running")


def main() -> None:
    """Run Streamlit chat application."""
    st.set_page_config(page_title="Revenue Leakage Agent", page_icon="🔍")
    st.title("Revenue Leakage Agent")
    st.caption("Investigate billing anomalies · Propose fixes · Apply to sandbox")

    _init_session()

    try:
        get_llm().invoke("ping")
        st.success("Ollama connected", icon="✅")
    except Exception as exc:
        st.warning(f"Ollama not reachable: {exc}. Start with: ollama serve", icon="⚠️")

    for entry in st.session_state.chat_history:
        with st.chat_message(entry["role"]):
            st.markdown(entry["content"])
            if entry["role"] == "assistant" and entry.get("tool_trace"):
                _render_tool_trace_ui(entry["tool_trace"])

    if st.session_state.pending_action:
        pending = st.session_state.pending_action
        st.info(
            f"Pending proposal **{pending.get('action_id', '')}** "
            f"({pending.get('action_type', '').replace('_', ' ')})"
        )
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Approve", type="primary"):
                draft_json = json.dumps(pending)
                _run_agent(f"Yes, apply this action: {draft_json}")
                st.rerun()
        with col2:
            if st.button("Reject"):
                st.session_state.pending_action = None
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": "Proposal rejected.", "tool_trace": []}
                )
                st.rerun()
        with col3:
            if st.button("Skip for now"):
                st.session_state.pending_action = None
                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": (
                            f"Left **{pending.get('action_id', '')}** as a draft. "
                            "Say **continue** when you want the next proposal."
                        ),
                        "tool_trace": [],
                    }
                )
                st.rerun()

    if prompt := st.chat_input("Ask about billing plans, invoices, or leakage..."):
        _run_agent(prompt)


def _run_agent(user_input: str) -> None:
    """Send user message to agent, stream tool activity, and update UI."""
    if is_approval_message(user_input):
        st.session_state.pending_action = None

    st.session_state.chat_history.append({"role": "user", "content": user_input})
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    tool_trace: list[dict[str, Any]] = []
    pending_by_id: dict[str, dict[str, Any]] = {}
    final_state: dict[str, Any] | None = None

    with st.status("Agent running...", expanded=True) as status:
        for mode, chunk in st.session_state.graph_app.stream(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
            stream_mode=["updates", "values"],
        ):
            if mode == "updates" and chunk:
                _process_stream_update(chunk, tool_trace, pending_by_id, status)
            elif mode == "values":
                final_state = chunk

        if tool_trace:
            status.update(
                label=f"Finished — {len(tool_trace)} tool call(s)",
                state="complete",
            )
        else:
            status.update(label="Finished", state="complete")

    messages = final_state["messages"] if final_state else []
    if not tool_trace and messages:
        tool_trace = _build_tool_trace(messages)

    response = _extract_assistant_response(messages)
    st.session_state.chat_history.append(
        {
            "role": "assistant",
            "content": response,
            "tool_trace": tool_trace,
        }
    )

    pending = resolve_pending_action(tool_trace, user_input)
    st.session_state.pending_action = pending

    st.rerun()


if __name__ == "__main__":
    main()
