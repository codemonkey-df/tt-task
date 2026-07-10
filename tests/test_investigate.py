"""Tests for deterministic investigation."""

import json

from revenue_leakage_agent.investigate import find_orphan_invoices, investigate_plan
from revenue_leakage_agent.loaders import get_plan, load_billing_plans, load_invoices
from revenue_leakage_agent.tools import fx_convert, query_credit_memos


def test_load_billing_plans_count() -> None:
    """F1: Should load 4 billing plans from challenge data."""
    assert len(load_billing_plans()) >= 4


def test_load_invoices_count() -> None:
    """F1: Should load 13 invoices from challenge data."""
    assert len(load_invoices()) >= 13


def test_c1001_missing_september() -> None:
    """F3: C-1001 should have missing September invoice."""
    result = investigate_plan("C-1001")
    missing = [f for f in result.findings if f.signal_type == "missing_invoice"]
    assert any("2025-09" in f.description for f in missing)
    assert any(f.variance == 8000.0 for f in missing)


def test_c1007_underbilling() -> None:
    """F3: C-1007 quarterly invoice should be underbilled by $2,500."""
    result = investigate_plan("C-1007")
    mismatches = [f for f in result.findings if f.signal_type == "amount_mismatch"]
    assert len(mismatches) >= 1
    assert mismatches[0].variance == 2500.0


def test_c1007a1_fx_overbilling_corrected() -> None:
    """F3: C-1007-A1 FX overbilling should be offset by existing credit memo M-300."""
    result = investigate_plan("C-1007-A1")
    corrected = [f for f in result.findings if f.signal_type == "fx_overbilling_corrected"]
    assert len(corrected) == 1
    assert corrected[0].variance == 0.0
    assert any("M-300" in item for item in corrected[0].evidence)


def test_c1010_underbilling() -> None:
    """F3: C-1010 annual invoice should be underbilled by $20,000."""
    result = investigate_plan("C-1010")
    under = [f for f in result.findings if f.signal_type == "underbilling"]
    assert len(under) >= 1
    assert under[0].variance == 20000.0


def test_find_orphan_invoices() -> None:
    """F3: Orphan invoice I-9202 should be detected."""
    findings = find_orphan_invoices()
    assert any(f.evidence[0] == "invoice_id=I-9202" for f in findings)


def test_load_plan_c1001_fields() -> None:
    """F2: C-1001 plan metadata."""
    plan = get_plan("C-1001")
    assert plan is not None
    assert plan.customer_name == "ACME Corp"
    assert plan.currency == "USD"
    assert plan.cadence == "Monthly"


def test_fx_convert() -> None:
    """F2: EUR to USD conversion on 2025-09-12."""
    result = json.loads(
        fx_convert.invoke(
            {
                "amount": 25000,
                "from_ccy": "EUR",
                "to_ccy": "USD",
                "on_date": "2025-09-12",
            }
        )
    )
    assert result["converted_amount"] == 27000.0


def test_query_credit_memos_for_plan() -> None:
    """F2: query_credit_memos should return M-300 for C-1007-A1."""
    result = json.loads(query_credit_memos.invoke({"plan_id": "C-1007-A1"}))
    assert len(result) == 1
    assert result[0]["memo_id"] == "M-300"
