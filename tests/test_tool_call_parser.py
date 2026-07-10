"""Tests for text-based tool call parsing."""

from langchain_core.messages import AIMessage

from revenue_leakage_agent.tool_call_parser import (
    extract_tool_calls_from_text,
    normalize_ai_message,
    parse_text_tool_calls,
    strip_thinking_tags,
)


def test_strip_thinking_tags() -> None:
    text = (
        "<mm:think>Reasoning here.</mm:think>"
        '{"name": "investigate_plan_tool", "arguments":{"plan_id": "C-1001"}}'
    )
    assert strip_thinking_tags(text) == (
        '{"name": "investigate_plan_tool", "arguments":{"plan_id": "C-1001"}}'
    )


def test_extract_single_tool_call() -> None:
    text = '{"name": "investigate_plan_tool", "arguments":{"plan_id": "C-1001"}}'
    cleaned, calls = extract_tool_calls_from_text(text)
    assert cleaned == ""
    assert len(calls) == 1
    assert calls[0]["name"] == "investigate_plan_tool"
    assert calls[0]["args"] == {"plan_id": "C-1001"}


def test_extract_multiple_tool_calls_with_thinking() -> None:
    text = (
        "<mm:think>Load plan and invoices.</mm:think>"
        '{"name": "load_plan", "arguments":{"plan_id": "C-1001"}} '
        '{"name": "query_invoices", "arguments":{"plan_id": "C-1001"}}'
    )
    cleaned, calls = extract_tool_calls_from_text(text)
    assert cleaned == ""
    assert [call["name"] for call in calls] == ["load_plan", "query_invoices"]


def test_normalize_ai_message_preserves_existing_tool_calls() -> None:
    message = AIMessage(
        content="<mm:think>ok</mm:think>",
        tool_calls=[
            {
                "name": "investigate_plan_tool",
                "args": {"plan_id": "C-1001"},
                "id": "call-1",
                "type": "tool_call",
            }
        ],
    )
    normalized = normalize_ai_message(message)
    assert normalized.content == ""
    assert normalized.tool_calls[0]["name"] == "investigate_plan_tool"


def test_parse_text_tool_calls_updates_state() -> None:
    bad_message = AIMessage(
        content='{"name": "investigate_plan_tool", "arguments":{"plan_id": "C-1001"}}',
        id="ai-1",
    )
    update = parse_text_tool_calls({"messages": [bad_message]})
    assert "messages" in update
    fixed = update["messages"][0]
    assert fixed.tool_calls
    assert fixed.tool_calls[0]["name"] == "investigate_plan_tool"


def test_extract_openai_style_tool_calls_array() -> None:
    text = (
        "Let me retry the FX conversion.Tool Calls: [ "
        '{ "id": "parsed-fx-retry", "type": "function", "function": { '
        '"name": "fx_convert", "arguments": { '
        '"amount": 25000, "from_ccy": "EUR", "to_ccy": "USD", "on_date": "2025-09-12" } } }, '
        '{ "id": "parsed-orphan-invoices", "type": "function", "function": { '
        '"name": "query_invoices", "arguments": { "invoice_id": "I-9202" } } } ]'
    )
    cleaned, calls = extract_tool_calls_from_text(text)
    assert cleaned == "Let me retry the FX conversion."
    assert [call["name"] for call in calls] == ["fx_convert", "query_invoices"]
    assert calls[0]["args"]["on_date"] == "2025-09-12"
    assert calls[1]["args"]["invoice_id"] == "I-9202"


def test_looks_like_text_tool_calls_detects_openai_array() -> None:
    from revenue_leakage_agent.tool_call_parser import looks_like_text_tool_calls

    text = 'Tool Calls: [ { "type": "function", "function": { "name": "fx_convert" } } ]'
    assert looks_like_text_tool_calls(text)

