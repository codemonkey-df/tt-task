"""Tests for FX conversion helpers."""

from revenue_leakage_agent.fx import convert_amount


def test_convert_amount_same_currency() -> None:
    """Same currency should return the original amount."""
    assert convert_amount(100.0, "USD", "USD", "2025-09-12") == 100.0


def test_convert_amount_eur_to_usd() -> None:
    """EUR to USD conversion should use the seeded exchange rate."""
    assert convert_amount(25000.0, "EUR", "USD", "2025-09-12") == 27000.0


def test_convert_amount_missing_rate() -> None:
    """Unknown currency pair should return None."""
    assert convert_amount(100.0, "GBP", "USD", "2025-09-12") is None
