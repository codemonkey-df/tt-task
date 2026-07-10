"""Foreign-exchange conversion helpers."""

from __future__ import annotations

from revenue_leakage_agent.loaders import load_exchange_rates


def convert_amount(amount: float, from_ccy: str, to_ccy: str, on_date: str) -> float | None:
    """Convert amount between currencies using exchange_rates.json.

    Args:
        amount: Amount in the source currency.
        from_ccy: Source currency code.
        to_ccy: Target currency code.
        on_date: ISO date string for the FX rate lookup.

    Returns:
        Converted amount, or None when no matching rate exists.
    """
    if from_ccy == to_ccy:
        return amount

    for rate in load_exchange_rates():
        if rate.date == on_date and rate.from_currency == from_ccy and rate.to_currency == to_ccy:
            return amount * rate.rate
    return None
