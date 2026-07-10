"""Tests for approval / pending-action UI helpers."""

from revenue_leakage_agent.ui_pending import (
    apply_succeeded_this_turn,
    extract_pending_from_tool_trace,
    is_approval_message,
    resolve_pending_action,
)


def test_is_approval_message() -> None:
    assert is_approval_message('Yes, apply this action: {"action_id": "ACT-123"}')
    assert not is_approval_message("Run a full audit")


def test_resolve_pending_action_suppresses_chain_after_apply() -> None:
    tool_trace = [
        {
            "tool": "apply",
            "result": '{"status": "applied", "invoice_id": "INV-MG-001"}',
        },
        {
            "tool": "propose_make_good_invoice",
            "result": (
                '{"action_id": "ACT-NEXT", "action_type": "make_good_invoice", '
                '"payload": {"plan_id": "C-1007", "amount": 2500.0}}'
            ),
        },
    ]
    user_input = 'Yes, apply this action: {"action_id": "ACT-123"}'
    assert resolve_pending_action(tool_trace, user_input) is None


def test_resolve_pending_action_keeps_investigation_proposal() -> None:
    tool_trace = [
        {
            "tool": "propose_make_good_invoice",
            "result": (
                '{"action_id": "ACT-123", "action_type": "make_good_invoice", '
                '"payload": {"plan_id": "C-1001", "amount": 8000.0}}'
            ),
        },
    ]
    assert resolve_pending_action(tool_trace, "Summarize findings") == {
        "action_id": "ACT-123",
        "action_type": "make_good_invoice",
        "payload": {"plan_id": "C-1001", "amount": 8000.0},
    }


def test_apply_succeeded_this_turn() -> None:
    assert apply_succeeded_this_turn([{"tool": "apply", "result": '{"status": "applied"}'}])
    assert not apply_succeeded_this_turn([{"tool": "apply", "result": '{"status": "error"}'}])


def test_extract_pending_from_tool_trace() -> None:
    trace = [
        {
            "tool": "propose_credit_memo",
            "result": '{"action_id": "ACT-X", "action_type": "credit_memo", "payload": {}}',
        }
    ]
    assert extract_pending_from_tool_trace(trace)["action_id"] == "ACT-X"
