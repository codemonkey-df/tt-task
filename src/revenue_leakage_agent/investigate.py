"""Deterministic revenue leakage investigation."""

from __future__ import annotations

from datetime import date

from revenue_leakage_agent.fx import convert_amount
from revenue_leakage_agent.loaders import get_plan, load_credit_memos, load_invoices
from revenue_leakage_agent.models import CreditMemo, Finding, InvestigationResult, Invoice


def _parse_date(value: str) -> date:
    """Parse ISO date string."""
    return date.fromisoformat(value)


def _month_key(d: date) -> str:
    """Return YYYY-MM key for a date."""
    return f"{d.year:04d}-{d.month:02d}"


def _expected_months(plan_start: date, through: date) -> list[str]:
    """Generate expected monthly billing months from plan start through date."""
    months: list[str] = []
    year, month = plan_start.year, plan_start.month
    end_key = _month_key(through)
    while f"{year:04d}-{month:02d}" <= end_key:
        months.append(f"{year:04d}-{month:02d}")
        month += 1
        if month > 12:
            month = 1
            year += 1
    return months


def _memo_total_in_plan_currency(memos: list[CreditMemo], plan_currency: str) -> float:
    """Sum credit memo amounts normalized to the plan currency."""
    total = 0.0
    for memo in memos:
        if memo.currency == plan_currency:
            total += memo.amount
            continue
        converted = convert_amount(memo.amount, memo.currency, plan_currency, memo.issue_date)
        if converted is not None:
            total += converted
    return total


def _check_fx_overbilling(
    inv: Invoice,
    plan_id: str,
    expected: float,
    plan_currency: str,
) -> Finding | None:
    """Detect FX overbilling and net residual after existing credit memos."""
    if inv.currency == plan_currency:
        return None

    converted = convert_amount(inv.amount_invoiced, inv.currency, plan_currency, inv.issue_date)
    if converted is None:
        return Finding(
            signal_type="currency_mismatch",
            description=(
                f"Invoice {inv.invoice_id} currency {inv.currency} "
                f"differs from plan currency {plan_currency}; no FX rate on {inv.issue_date}"
            ),
            expected_amount=expected,
            actual_amount=inv.amount_invoiced,
            variance=0.0,
            evidence=[f"invoice_id={inv.invoice_id}", f"currency={inv.currency}"],
        )

    gross_overbilling = converted - expected
    if gross_overbilling <= 0.01:
        return None

    memos = [
        memo
        for memo in load_credit_memos()
        if memo.invoice_id == inv.invoice_id or memo.plan_id == plan_id
    ]
    memo_total = _memo_total_in_plan_currency(memos, plan_currency)
    net_overbilling = gross_overbilling - memo_total
    memo_ids = [memo.memo_id for memo in memos]
    evidence = [
        f"invoice_id={inv.invoice_id}",
        f"converted_amount={converted:.2f}",
        f"gross_overbilling={gross_overbilling:.2f}",
        f"credit_memo_total={memo_total:.2f}",
    ]
    if memo_ids:
        evidence.append(f"credit_memo_ids={','.join(memo_ids)}")

    if net_overbilling > 0.01:
        return Finding(
            signal_type="fx_overbilling",
            description=(
                f"Invoice {inv.invoice_id} converts to {converted:.2f} {plan_currency} "
                f"vs expected {expected:.2f}; net overbilling {net_overbilling:.2f} "
                f"{plan_currency} after credit memos"
            ),
            expected_amount=expected,
            actual_amount=converted,
            variance=net_overbilling,
            evidence=evidence,
        )

    return Finding(
        signal_type="fx_overbilling_corrected",
        description=(
            f"Invoice {inv.invoice_id} gross FX overbilling {gross_overbilling:.2f} "
            f"{plan_currency} fully offset by existing credit memo(s)"
        ),
        expected_amount=expected,
        actual_amount=converted,
        variance=0.0,
        evidence=evidence,
    )


def investigate_plan(plan_id: str) -> InvestigationResult:
    """Run deterministic leakage checks for a billing plan."""
    plan = get_plan(plan_id)
    if plan is None:
        return InvestigationResult(
            plan_id=plan_id,
            customer_name="",
            currency="",
            expected_per_period=0.0,
            findings=[
                Finding(
                    signal_type="plan_not_found",
                    description=f"Plan {plan_id} not found",
                    expected_amount=0.0,
                    actual_amount=0.0,
                    variance=0.0,
                )
            ],
        )

    expected = plan.expected_per_period()
    invoices = [inv for inv in load_invoices() if inv.plan_id == plan_id]
    findings: list[Finding] = []

    if plan.cadence == "Monthly":
        plan_start = _parse_date(plan.start_date)
        invoice_dates = [_parse_date(inv.issue_date) for inv in invoices]
        through = max(invoice_dates) if invoice_dates else date(2025, 9, 30)
        if through < date(2025, 9, 1):
            through = date(2025, 9, 30)

        billed_months = {_month_key(_parse_date(inv.issue_date)) for inv in invoices}
        for month in _expected_months(plan_start, through):
            if month not in billed_months:
                findings.append(
                    Finding(
                        signal_type="missing_invoice",
                        description=f"Missing invoice for billing month {month}",
                        expected_amount=expected,
                        actual_amount=0.0,
                        variance=expected,
                        evidence=[f"plan_id={plan_id}", f"missing_month={month}"],
                    )
                )

    for inv in invoices:
        if inv.currency != plan.currency:
            fx_finding = _check_fx_overbilling(inv, plan_id, expected, plan.currency)
            if fx_finding is not None:
                findings.append(fx_finding)
            continue

        if abs(inv.amount_invoiced - expected) > 0.01 and plan.cadence != "Annual":
            findings.append(
                Finding(
                    signal_type="amount_mismatch",
                    description=(
                        f"Invoice {inv.invoice_id} amount {inv.amount_invoiced} "
                        f"differs from expected {expected:.2f}"
                    ),
                    expected_amount=expected,
                    actual_amount=inv.amount_invoiced,
                    variance=expected - inv.amount_invoiced,
                    evidence=[f"invoice_id={inv.invoice_id}", f"issue_date={inv.issue_date}"],
                )
            )

    if plan.cadence == "Annual" and invoices:
        inv = invoices[0]
        if inv.amount_invoiced < plan.total_value - 0.01:
            findings.append(
                Finding(
                    signal_type="underbilling",
                    description=(
                        f"Annual invoice {inv.invoice_id} billed {inv.amount_invoiced} "
                        f"vs plan total {plan.total_value}"
                    ),
                    expected_amount=plan.total_value,
                    actual_amount=inv.amount_invoiced,
                    variance=plan.total_value - inv.amount_invoiced,
                    evidence=[f"invoice_id={inv.invoice_id}"],
                )
            )

    total_variance = sum(abs(f.variance) for f in findings)
    return InvestigationResult(
        plan_id=plan.plan_id,
        customer_name=plan.customer_name,
        currency=plan.currency,
        expected_per_period=expected,
        findings=findings,
        total_variance=total_variance,
    )


def find_orphan_invoices() -> list[Finding]:
    """Find invoices with no plan reference."""
    findings: list[Finding] = []
    for inv in load_invoices():
        if not inv.plan_id.strip():
            findings.append(
                Finding(
                    signal_type="orphan_invoice",
                    description=f"Invoice {inv.invoice_id} has no plan_id",
                    expected_amount=0.0,
                    actual_amount=inv.amount_invoiced,
                    variance=inv.amount_invoiced,
                    evidence=[f"invoice_id={inv.invoice_id}", f"customer={inv.customer_name}"],
                )
            )
    return findings
