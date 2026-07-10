"""LangChain tools for the Revenue Leakage Agent."""

from __future__ import annotations

import json

from langchain_core.tools import tool

from revenue_leakage_agent.fx import convert_amount
from revenue_leakage_agent.investigate import find_orphan_invoices, investigate_plan
from revenue_leakage_agent.loaders import get_plan, load_credit_memos, load_invoices
from revenue_leakage_agent.models import ActionDraft
from revenue_leakage_agent.sandbox import apply_action, create_draft, rollback_action


@tool
def load_plan(plan_id: str) -> str:
    """Read billing plan details by plan_id."""
    plan = get_plan(plan_id)
    if plan is None:
        return json.dumps({"error": f"Plan {plan_id} not found"})
    return plan.model_dump_json()


@tool
def query_invoices(
    plan_id: str = "",
    invoice_id: str = "",
    customer_name: str = "",
    date_from: str = "",
    date_to: str = "",
) -> str:
    """Filter invoices by plan_id, invoice_id, customer_name, and optional date range."""
    results = load_invoices()
    if plan_id:
        results = [inv for inv in results if inv.plan_id == plan_id]
    if invoice_id:
        results = [inv for inv in results if inv.invoice_id == invoice_id]
    if customer_name:
        results = [inv for inv in results if customer_name.lower() in inv.customer_name.lower()]
    if date_from:
        results = [inv for inv in results if inv.issue_date >= date_from]
    if date_to:
        results = [inv for inv in results if inv.issue_date <= date_to]
    return json.dumps([inv.model_dump() for inv in results])


@tool
def query_credit_memos(plan_id: str = "", invoice_id: str = "") -> str:
    """Filter credit memos by plan_id and/or invoice_id."""
    results = load_credit_memos()
    if plan_id:
        results = [memo for memo in results if memo.plan_id == plan_id]
    if invoice_id:
        results = [memo for memo in results if memo.invoice_id == invoice_id]
    return json.dumps([memo.model_dump() for memo in results])


@tool
def fx_convert(amount: float, from_ccy: str, to_ccy: str, on_date: str) -> str:
    """Convert amount between currencies using exchange_rates.json for on_date."""
    if from_ccy == to_ccy:
        return json.dumps({"converted_amount": amount, "rate": 1.0})
    converted = convert_amount(amount, from_ccy, to_ccy, on_date)
    if converted is None:
        return json.dumps({"error": f"No rate for {from_ccy}->{to_ccy} on {on_date}"})
    rate = converted / amount if amount else 1.0
    return json.dumps({"converted_amount": converted, "rate": rate})


@tool
def investigate_plan_tool(plan_id: str) -> str:
    """Run deterministic revenue leakage investigation for a billing plan."""
    result = investigate_plan(plan_id)
    return result.model_dump_json()


@tool
def find_orphan_invoices_tool() -> str:
    """Find invoices with no plan_id reference."""
    findings = find_orphan_invoices()
    return json.dumps([f.model_dump() for f in findings])


@tool
def propose_make_good_invoice(plan_id: str, amount: float, reason: str) -> str:
    """Draft a make-good invoice to recover missed or underbilled revenue. Does not write yet."""
    plan = get_plan(plan_id)
    draft = create_draft(
        "make_good_invoice",
        {
            "plan_id": plan_id,
            "amount": amount,
            "currency": plan.currency if plan else "USD",
            "customer_name": plan.customer_name if plan else "",
        },
        reason,
    )
    return draft.model_dump_json()


@tool
def propose_credit_memo(invoice_id: str, amount: float, reason: str) -> str:
    """Draft a credit memo for overbilling. Does not write yet."""
    inv = next((i for i in load_invoices() if i.invoice_id == invoice_id), None)
    draft = create_draft(
        "credit_memo",
        {
            "invoice_id": invoice_id,
            "plan_id": inv.plan_id if inv else "",
            "amount": amount,
            "currency": inv.currency if inv else "USD",
        },
        reason,
    )
    return draft.model_dump_json()


@tool
def propose_plan_amendment(plan_id: str, change_set_json: str) -> str:
    """Draft a billing plan amendment. change_set_json is a JSON object with plan fields."""
    changes = json.loads(change_set_json)
    plan = get_plan(plan_id)
    if plan is None:
        return json.dumps({"error": f"Plan {plan_id} not found"})
    updated = plan.model_dump()
    updated.update(changes)
    draft = create_draft("plan_amendment", {"plan": updated}, f"Amend plan {plan_id}")
    return draft.model_dump_json()


@tool
def apply(action_draft_json: str) -> str:
    """Apply a proposed action to the sandbox. Use only after user confirmation."""
    draft = ActionDraft.model_validate_json(action_draft_json)
    result = apply_action(draft)
    return json.dumps(result)


@tool
def rollback(action_id: str) -> str:
    """Undo a previously applied sandbox action."""
    result = rollback_action(action_id)
    return json.dumps(result)


ALL_TOOLS = [
    load_plan,
    query_invoices,
    query_credit_memos,
    fx_convert,
    investigate_plan_tool,
    find_orphan_invoices_tool,
    propose_make_good_invoice,
    propose_credit_memo,
    propose_plan_amendment,
    apply,
    rollback,
]
