"""Pydantic domain models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class BillingPlan(BaseModel):
    """Billing plan (contract) record."""

    plan_id: str
    customer_name: str
    total_value: float
    currency: str
    cadence: Literal["Monthly", "Quarterly", "Annual"]
    start_date: str
    entitlements: list[str] = Field(default_factory=list)
    notes: str | None = None
    amends: str | None = None

    def expected_per_period(self) -> float:
        """Return expected amount per billing period."""
        divisors = {"Monthly": 12, "Quarterly": 4, "Annual": 1}
        return self.total_value / divisors[self.cadence]


class Invoice(BaseModel):
    """Invoice record."""

    invoice_id: str
    plan_id: str
    customer_name: str
    issue_date: str
    due_date: str
    amount_invoiced: float
    currency: str
    status: str
    description: str


class CreditMemo(BaseModel):
    """Credit memo record."""

    memo_id: str
    plan_id: str
    invoice_id: str
    amount: float
    currency: str
    issue_date: str
    reason: str


class ExchangeRate(BaseModel):
    """FX rate for a specific date."""

    date: str
    from_currency: str
    to_currency: str
    rate: float


class ActionDraft(BaseModel):
    """Pending corrective action awaiting approval."""

    action_id: str
    action_type: Literal["make_good_invoice", "credit_memo", "plan_amendment"]
    payload: dict[str, Any]
    reason: str


class Finding(BaseModel):
    """Single leakage finding from investigation."""

    signal_type: str
    description: str
    expected_amount: float
    actual_amount: float
    variance: float
    evidence: list[str] = Field(default_factory=list)


class InvestigationResult(BaseModel):
    """Result of deterministic plan investigation."""

    plan_id: str
    customer_name: str
    currency: str
    expected_per_period: float
    findings: list[Finding] = Field(default_factory=list)
    total_variance: float = 0.0
