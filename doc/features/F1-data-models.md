# F1 — Data Models

## Goal
Pydantic models and JSON loaders for challenge data.

## API
- `load_billing_plans() -> list[BillingPlan]`
- `load_invoices() -> list[Invoice]`
- `load_credit_memos() -> list[CreditMemo]`
- `load_exchange_rates() -> list[ExchangeRate]`

## Acceptance criteria
- [ ] 4 billing plans loaded
- [ ] 13 invoices loaded
- [ ] Models validate challenge JSON

## Dependencies
F0

## Out of scope
Tools, agent
