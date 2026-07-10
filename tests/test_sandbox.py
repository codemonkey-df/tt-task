"""Tests for sandbox apply operations."""

from revenue_leakage_agent.loaders import _load_json
from revenue_leakage_agent.sandbox import apply_action, create_draft


def test_apply_make_good_appends_invoice(tmp_path, monkeypatch) -> None:
    """F4: apply should append invoice to sandbox."""
    from revenue_leakage_agent import paths, sandbox

    inv_file = tmp_path / "invoices.json"
    audit_file = tmp_path / "audit_log.json"
    monkeypatch.setattr(paths, "SANDBOX_INVOICES_FILE", inv_file)
    monkeypatch.setattr(paths, "SANDBOX_AUDIT_LOG_FILE", audit_file)
    monkeypatch.setattr(paths, "SANDBOX_CREDIT_MEMOS_FILE", tmp_path / "credit_memos.json")
    monkeypatch.setattr(paths, "SANDBOX_BILLING_PLANS_FILE", tmp_path / "billing_plans.json")
    monkeypatch.setattr(sandbox, "load_audit_log", lambda: [])

    draft = create_draft(
        "make_good_invoice",
        {"plan_id": "C-1001", "amount": 8000, "currency": "USD"},
        "Missing September billing",
    )
    result = apply_action(draft)
    assert result["status"] == "applied"
    sandbox = _load_json(inv_file)
    assert len(sandbox) == 1
    assert sandbox[0]["amount_invoiced"] == 8000


def test_apply_action_is_idempotent(tmp_path, monkeypatch) -> None:
    """Re-applying the same action_id must not create duplicate sandbox writes."""
    from revenue_leakage_agent import paths, sandbox

    inv_file = tmp_path / "invoices.json"
    audit_file = tmp_path / "audit_log.json"
    monkeypatch.setattr(paths, "SANDBOX_INVOICES_FILE", inv_file)
    monkeypatch.setattr(paths, "SANDBOX_AUDIT_LOG_FILE", audit_file)
    monkeypatch.setattr(paths, "SANDBOX_CREDIT_MEMOS_FILE", tmp_path / "credit_memos.json")
    monkeypatch.setattr(paths, "SANDBOX_BILLING_PLANS_FILE", tmp_path / "billing_plans.json")

    draft = create_draft(
        "make_good_invoice",
        {"plan_id": "C-1001", "amount": 8000, "currency": "USD"},
        "Missing September billing",
    )
    first = apply_action(draft)
    second = apply_action(draft)
    assert first["status"] == "applied"
    assert second["status"] == "already_applied"
    assert len(_load_json(inv_file)) == 1
