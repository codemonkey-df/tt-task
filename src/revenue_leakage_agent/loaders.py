"""JSON data loaders."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from revenue_leakage_agent.models import (
    BillingPlan,
    CreditMemo,
    ExchangeRate,
    Invoice,
)
from revenue_leakage_agent import paths

T = TypeVar("T", bound=BaseModel)


def _load_json(path: Path) -> list[dict[str, Any]]:
    """Load a JSON array from disk."""
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def _load_models(path: Path, model: type[T]) -> list[T]:
    """Load and validate a list of Pydantic models."""
    return [model.model_validate(row) for row in _load_json(path)]


def load_billing_plans() -> list[BillingPlan]:
    """Load billing plans from data/ and sandbox/."""
    plans = {p.plan_id: p for p in _load_models(paths.BILLING_PLANS_FILE, BillingPlan)}
    for plan in _load_models(paths.SANDBOX_BILLING_PLANS_FILE, BillingPlan):
        plans[plan.plan_id] = plan
    return list(plans.values())


def load_invoices() -> list[Invoice]:
    """Load invoices from data/ and sandbox/."""
    return _load_models(paths.INVOICES_FILE, Invoice) + _load_models(
        paths.SANDBOX_INVOICES_FILE, Invoice
    )


def load_credit_memos() -> list[CreditMemo]:
    """Load credit memos from data/ and sandbox/."""
    return _load_models(paths.CREDIT_MEMOS_FILE, CreditMemo) + _load_models(
        paths.SANDBOX_CREDIT_MEMOS_FILE, CreditMemo
    )


def load_exchange_rates() -> list[ExchangeRate]:
    """Load exchange rates from data/."""
    return _load_models(paths.EXCHANGE_RATES_FILE, ExchangeRate)


def load_audit_log() -> list[dict[str, Any]]:
    """Load sandbox audit log entries."""
    return _load_json(paths.SANDBOX_AUDIT_LOG_FILE)


def save_json(path: Path, data: list[dict[str, Any]] | dict[str, Any]) -> None:
    """Write JSON data to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_plan(plan_id: str) -> BillingPlan | None:
    """Return a billing plan by ID."""
    for plan in load_billing_plans():
        if plan.plan_id == plan_id:
            return plan
    return None
