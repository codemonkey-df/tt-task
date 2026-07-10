"""Pending-action resolution for the Streamlit approval UI."""

from __future__ import annotations

import json
from typing import Any

_PROPOSAL_ACTION_TYPES = frozenset({"make_good_invoice", "credit_memo", "plan_amendment"})


def is_approval_message(text: str) -> bool:
    """Return True when the user is confirming a sandbox apply."""
    lowered = text.lower()
    return (
        "apply this action" in lowered
        or lowered.strip().startswith("yes, apply")
        or (lowered.startswith("yes") and "act-" in lowered)
    )


def apply_succeeded_this_turn(tool_trace: list[dict[str, Any]]) -> bool:
    """Return True when apply ran successfully in the current agent turn."""
    for step in tool_trace:
        if step.get("tool") != "apply" or not step.get("result"):
            continue
        try:
            data = json.loads(step["result"])
        except (json.JSONDecodeError, TypeError):
            continue
        if data.get("status") == "applied":
            return True
    return False


def extract_pending_from_tool_trace(tool_trace: list[dict[str, Any]]) -> dict | None:
    """Return the latest proposal created during the current agent turn."""
    for step in reversed(tool_trace):
        tool_name = step.get("tool", "")
        if not tool_name.startswith("propose_") or not step.get("result"):
            continue
        try:
            data = json.loads(step["result"])
        except (json.JSONDecodeError, TypeError):
            continue
        if "action_id" in data and data.get("action_type") in _PROPOSAL_ACTION_TYPES:
            return data
    return None


def resolve_pending_action(
    tool_trace: list[dict[str, Any]],
    user_input: str,
) -> dict | None:
    """Resolve pending proposal for the UI without chaining after apply."""
    if apply_succeeded_this_turn(tool_trace) and is_approval_message(user_input):
        return None
    return extract_pending_from_tool_trace(tool_trace)
