# Data Model

## BillingPlan

| Field | Type | Notes |
|-------|------|-------|
| plan_id | str | e.g. C-1001 |
| customer_name | str | |
| total_value | float | Contract total |
| currency | str | USD, EUR |
| cadence | str | Monthly, Quarterly, Annual |
| start_date | str | ISO date |
| entitlements | list[str] | optional |
| notes | str | optional |
| amends | str | optional, prior plan_id |

## Invoice

| Field | Type | Notes |
|-------|------|-------|
| invoice_id | str | |
| plan_id | str | may be empty (orphan) |
| customer_name | str | |
| issue_date | str | ISO date |
| due_date | str | |
| amount_invoiced | float | |
| currency | str | |
| status | str | paid, unpaid |
| description | str | |

## CreditMemo, ExchangeRate, ActionDraft

See `src/revenue_leakage_agent/models.py`.

## ActionDraft

| Field | Type |
|-------|------|
| action_id | str |
| action_type | make_good_invoice \| credit_memo \| plan_amendment |
| payload | dict |
| reason | str |
