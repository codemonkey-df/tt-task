"""Sandbox write operations and audit log."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from revenue_leakage_agent import paths
from revenue_leakage_agent.loaders import get_plan, load_audit_log, save_json
from revenue_leakage_agent.models import ActionDraft, CreditMemo, Invoice


def _now_iso() -> str:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def _load_sandbox_list(path: Path) -> list[dict[str, Any]]:
    """Load sandbox JSON list."""
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def create_draft(
    action_type: str,
    payload: dict[str, Any],
    reason: str,
) -> ActionDraft:
    """Create a new action draft."""
    return ActionDraft(
        action_id=f"ACT-{uuid.uuid4().hex[:8].upper()}",
        action_type=action_type,  # type: ignore[arg-type]
        payload=payload,
        reason=reason,
    )


def apply_action(draft: ActionDraft) -> dict[str, Any]:
    """Apply an action draft to the sandbox."""
    audit = load_audit_log()
    existing = next((entry for entry in audit if entry.get("action_id") == draft.action_id), None)
    if existing is not None:
        return {
            "status": "already_applied",
            "action_id": draft.action_id,
            "result": existing.get("result", {}),
        }

    result: dict[str, Any]

    if draft.action_type == "make_good_invoice":
        plan = get_plan(draft.payload["plan_id"])
        invoice = Invoice(
            invoice_id=f"INV-MG-{uuid.uuid4().hex[:6].upper()}",
            plan_id=draft.payload["plan_id"],
            customer_name=plan.customer_name if plan else draft.payload.get("customer_name", ""),
            issue_date=draft.payload.get("issue_date", "2025-09-05"),
            due_date=draft.payload.get("due_date", "2025-09-20"),
            amount_invoiced=float(draft.payload["amount"]),
            currency=draft.payload.get("currency", plan.currency if plan else "USD"),
            status="unpaid",
            description=f"Make-good: {draft.reason}",
        )
        sandbox_raw = _load_sandbox_list(paths.SANDBOX_INVOICES_FILE)
        sandbox_raw.append(invoice.model_dump())
        save_json(paths.SANDBOX_INVOICES_FILE, sandbox_raw)
        result = {"status": "applied", "invoice_id": invoice.invoice_id}

    elif draft.action_type == "credit_memo":
        memo = CreditMemo(
            memo_id=f"M-MG-{uuid.uuid4().hex[:6].upper()}",
            plan_id=draft.payload.get("plan_id", ""),
            invoice_id=draft.payload["invoice_id"],
            amount=float(draft.payload["amount"]),
            currency=draft.payload.get("currency", "USD"),
            issue_date=_now_iso()[:10],
            reason=draft.reason,
        )
        sandbox_raw = _load_sandbox_list(paths.SANDBOX_CREDIT_MEMOS_FILE)
        sandbox_raw.append(memo.model_dump())
        save_json(paths.SANDBOX_CREDIT_MEMOS_FILE, sandbox_raw)
        result = {"status": "applied", "memo_id": memo.memo_id}

    elif draft.action_type == "plan_amendment":
        plan_data = draft.payload["plan"]
        sandbox_raw = _load_sandbox_list(paths.SANDBOX_BILLING_PLANS_FILE)
        sandbox_raw.append(plan_data)
        save_json(paths.SANDBOX_BILLING_PLANS_FILE, sandbox_raw)
        result = {"status": "applied", "plan_id": plan_data.get("plan_id")}

    else:
        raise ValueError(f"Unknown action type: {draft.action_type}")

    audit.append(
        {
            "action_id": draft.action_id,
            "action_type": draft.action_type,
            "payload": draft.payload,
            "reason": draft.reason,
            "timestamp": _now_iso(),
            "result": result,
        }
    )
    save_json(paths.SANDBOX_AUDIT_LOG_FILE, audit)
    return result


def rollback_action(action_id: str) -> dict[str, Any]:
    """Rollback a sandbox action by reversing its write."""
    audit = load_audit_log()
    entry = next((e for e in audit if e.get("action_id") == action_id), None)
    if entry is None:
        return {"status": "error", "message": f"Action {action_id} not found"}

    action_type = entry.get("action_type")
    result = entry.get("result", {})

    if action_type == "make_good_invoice":
        inv_id = result.get("invoice_id")
        sandbox_raw = _load_sandbox_list(paths.SANDBOX_INVOICES_FILE)
        save_json(
            paths.SANDBOX_INVOICES_FILE,
            [r for r in sandbox_raw if r.get("invoice_id") != inv_id],
        )
    elif action_type == "credit_memo":
        memo_id = result.get("memo_id")
        sandbox_raw = _load_sandbox_list(paths.SANDBOX_CREDIT_MEMOS_FILE)
        save_json(
            paths.SANDBOX_CREDIT_MEMOS_FILE,
            [r for r in sandbox_raw if r.get("memo_id") != memo_id],
        )
    elif action_type == "plan_amendment":
        plan_id = result.get("plan_id")
        sandbox_raw = _load_sandbox_list(paths.SANDBOX_BILLING_PLANS_FILE)
        save_json(
            paths.SANDBOX_BILLING_PLANS_FILE,
            [r for r in sandbox_raw if r.get("plan_id") != plan_id],
        )

    audit = [e for e in audit if e.get("action_id") != action_id]
    save_json(paths.SANDBOX_AUDIT_LOG_FILE, audit)
    return {"status": "rolled_back", "action_id": action_id}
