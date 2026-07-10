"""Pending-action resolution for the Streamlit approval UI."""

from __future__ import annotations

import json
from typing import Any

from revenue_leakage_agent.loaders import load_audit_log

_PROPOSAL_ACTION_TYPES = frozenset({"make_good_invoice", "credit_memo", "plan_amendment"})


def is_approval_message(text: str) -> bool:
    """Return True when the user is confirming a sandbox apply."""
    lowered = text.lower()
    return (
        "apply this action" in lowered
        or lowered.strip().startswith("yes, apply")
        or (lowered.startswith("yes") and "act-" in lowered)
    )


def load_applied_action_ids() -> set[str]:
    """Return action IDs already written to the sandbox audit log."""
    return {
        str(entry["action_id"])
        for entry in load_audit_log()
        if entry.get("action_id")
    }


def extract_action_id_from_message(text: str) -> str | None:
    """Extract action_id from an approval message JSON payload."""
    start = text.find("{")
    if start == -1:
        return None
    try:
        obj, _end = json.JSONDecoder().raw_decode(text, start)
    except json.JSONDecodeError:
        return None
    if isinstance(obj, dict) and obj.get("action_id"):
        return str(obj["action_id"])
    return None


def apply_succeeded_this_turn(tool_trace: list[dict[str, Any]]) -> bool:
    """Return True when apply ran successfully in the current agent turn."""
    for step in tool_trace:
        if step.get("tool") != "apply" or not step.get("result"):
            continue
        try:
            data = json.loads(step["result"])
        except (json.JSONDecodeError, TypeError):
            continue
        if data.get("status") in {"applied", "already_applied"}:
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
    applied_action_ids: set[str] | None = None,
) -> dict | None:
    """Resolve pending proposal for the UI without re-queueing stale drafts."""
    applied_action_ids = applied_action_ids or load_applied_action_ids()

    if is_approval_message(user_input):
        return None

    pending = extract_pending_from_tool_trace(tool_trace)
    if pending and pending.get("action_id") in applied_action_ids:
        return None
    return pending


def sanitize_pending_action(pending: dict | None) -> dict | None:
    """Drop pending proposals that were already applied to the sandbox."""
    if pending is None:
        return None
    if pending.get("action_id") in load_applied_action_ids():
        return None
    return pending
