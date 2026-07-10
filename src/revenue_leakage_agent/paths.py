"""Project path helpers."""

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PACKAGE_ROOT / "data"
SANDBOX_DIR = PACKAGE_ROOT / "sandbox"

BILLING_PLANS_FILE = DATA_DIR / "billing_plans.json"
INVOICES_FILE = DATA_DIR / "invoices.json"
CREDIT_MEMOS_FILE = DATA_DIR / "credit_memos.json"
EXCHANGE_RATES_FILE = DATA_DIR / "exchange_rates.json"

SANDBOX_INVOICES_FILE = SANDBOX_DIR / "invoices.json"
SANDBOX_CREDIT_MEMOS_FILE = SANDBOX_DIR / "credit_memos.json"
SANDBOX_BILLING_PLANS_FILE = SANDBOX_DIR / "billing_plans.json"
SANDBOX_AUDIT_LOG_FILE = SANDBOX_DIR / "audit_log.json"
