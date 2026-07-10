"""Normalize LLM output when models emit tool calls as plain text."""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

from langchain_core.messages import AIMessage

_THINKING_PATTERN = re.compile(r"<mm:think>.*?</mm:think>", re.DOTALL | re.IGNORECASE)
_TOOL_CALLS_MARKER = re.compile(r"tool\s*calls?\s*:\s*\[", re.IGNORECASE)


def strip_thinking_tags(text: str) -> str:
    """Remove model-specific thinking blocks from visible content."""
    return _THINKING_PATTERN.sub("", text).strip()


def _normalize_tool_call_entry(obj: dict[str, Any]) -> dict[str, Any] | None:
    """Normalize one tool-call object from various model text formats."""
    if "name" in obj:
        raw_args = obj.get("arguments", obj.get("args", {}))
        name = str(obj["name"])
    elif isinstance(obj.get("function"), dict):
        func = obj["function"]
        if "name" not in func:
            return None
        name = str(func["name"])
        raw_args = func.get("arguments", func.get("args", {}))
    else:
        return None

    args = raw_args if isinstance(raw_args, dict) else {}
    call_id = obj.get("id")
    return {
        "name": name,
        "args": args,
        "id": str(call_id) if call_id else f"parsed-{uuid.uuid4().hex[:12]}",
        "type": "tool_call",
    }


def _try_parse_json_object(text: str, start: int) -> tuple[dict[str, Any], int] | None:
    """Parse one JSON object starting at ``start``."""
    try:
        obj, end = json.JSONDecoder().raw_decode(text, start)
    except json.JSONDecodeError:
        return None
    if isinstance(obj, dict):
        return obj, end
    return None


def _extract_tool_calls_array(text: str) -> tuple[list[dict[str, Any]], list[tuple[int, int]]]:
    """Parse ``Tool Calls: [ {...}, ... ]`` arrays emitted as plain text."""
    tool_calls: list[dict[str, Any]] = []
    spans: list[tuple[int, int]] = []

    for match in _TOOL_CALLS_MARKER.finditer(text):
        bracket = text.find("[", match.end() - 1)
        if bracket == -1:
            continue
        try:
            arr, end = json.JSONDecoder().raw_decode(text, bracket)
        except json.JSONDecodeError:
            continue
        if not isinstance(arr, list):
            continue

        parsed_any = False
        for item in arr:
            if not isinstance(item, dict):
                continue
            normalized = _normalize_tool_call_entry(item)
            if normalized is None:
                continue
            tool_calls.append(normalized)
            parsed_any = True

        if parsed_any:
            spans.append((match.start(), end))

    return tool_calls, spans


def _extract_inline_tool_calls(text: str) -> tuple[list[dict[str, Any]], list[tuple[int, int]]]:
    """Parse inline ``{"name": ...}`` or OpenAI-style function blobs."""
    tool_calls: list[dict[str, Any]] = []
    spans: list[tuple[int, int]] = []
    search_start = 0
    needles = ('{"name"', '{"id"', '{"type"')

    while search_start < len(text):
        candidates = [text.find(needle, search_start) for needle in needles]
        candidates = [idx for idx in candidates if idx != -1]
        if not candidates:
            break

        idx = min(candidates)
        parsed = _try_parse_json_object(text, idx)
        if parsed is None:
            search_start = idx + 1
            continue

        obj, end = parsed
        normalized = _normalize_tool_call_entry(obj)
        if normalized is None:
            search_start = idx + 1
            continue

        tool_calls.append(normalized)
        spans.append((idx, end))
        search_start = end

    return tool_calls, spans


def _remove_spans(text: str, spans: list[tuple[int, int]]) -> str:
    """Remove parsed JSON spans from text."""
    if not spans:
        return text

    merged = sorted(spans)
    chunks: list[str] = []
    cursor = 0
    for start, end in merged:
        if start < cursor:
            continue
        chunks.append(text[cursor:start])
        cursor = end
    chunks.append(text[cursor:])
    return "".join(chunks).strip()


def extract_tool_calls_from_text(text: str) -> tuple[str, list[dict[str, Any]]]:
    """Parse tool-call JSON blobs from model text output."""
    cleaned = strip_thinking_tags(text)
    array_calls, array_spans = _extract_tool_calls_array(cleaned)
    inline_calls, inline_spans = _extract_inline_tool_calls(cleaned)

    if array_calls:
        tool_calls = array_calls
        spans = array_spans
    else:
        tool_calls = inline_calls
        spans = inline_spans

    cleaned = _remove_spans(cleaned, spans)
    return cleaned, tool_calls


def looks_like_text_tool_calls(text: str) -> bool:
    """Return True when assistant text still contains unparsed tool-call JSON."""
    if not text:
        return False
    lowered = text.lower()
    if "tool calls:" in lowered and "[" in text:
        return True
    if '{"name"' in text and ("arguments" in text or '"args"' in text):
        return True
    if '"function"' in text and '"name"' in text and '"arguments"' in text:
        return True
    return False


def normalize_ai_message(message: AIMessage) -> AIMessage:
    """Convert text-based tool calls into structured ``tool_calls`` on an AIMessage."""
    content = message.content
    if isinstance(content, list):
        return message

    text = str(content or "")
    if message.tool_calls:
        stripped = strip_thinking_tags(text)
        if stripped == text:
            return message
        return AIMessage(
            content=stripped,
            tool_calls=message.tool_calls,
            id=message.id,
            response_metadata=message.response_metadata,
        )

    cleaned, parsed_calls = extract_tool_calls_from_text(text)
    if not parsed_calls:
        stripped = strip_thinking_tags(text)
        if stripped == text:
            return message
        return AIMessage(
            content=stripped,
            id=message.id,
            response_metadata=message.response_metadata,
        )

    return AIMessage(
        content=cleaned,
        tool_calls=parsed_calls,
        id=message.id,
        response_metadata=message.response_metadata,
    )


def parse_text_tool_calls(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph post-model hook: fix AIMessages that contain text tool JSON."""
    messages = state.get("messages", [])
    last_ai = next((m for m in reversed(messages) if isinstance(m, AIMessage)), None)
    if last_ai is None:
        return {}

    normalized = normalize_ai_message(last_ai)
    if normalized is last_ai:
        return {}

    return {"messages": [normalized]}
