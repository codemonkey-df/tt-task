# Tools Specification

## Read tools

### load_plan(plan_id: str) -> str
Returns JSON billing plan or error message.

### query_invoices(plan_id?, customer_name?, date_from?, date_to?) -> str
Returns JSON list of matching invoices.

### query_credit_memos(plan_id?, invoice_id?) -> str
Returns JSON list of matching credit memos.

### fx_convert(amount, from_ccy, to_ccy, on_date) -> str
Returns converted amount using exchange_rates.json.

### investigate_plan(plan_id: str) -> str
Deterministic anomaly detection. Returns structured findings JSON.

## Write tools (propose — no sandbox write)

### propose_make_good_invoice(plan_id, amount, reason) -> str
Returns ActionDraft JSON.

### propose_credit_memo(invoice_id, amount, reason) -> str
Returns ActionDraft JSON.

### propose_plan_amendment(plan_id, change_set_json) -> str
Returns ActionDraft JSON.

## Sandbox tools

### apply(action_draft_json) -> str
Writes to sandbox/ after user confirmation. Appends audit_log.

### rollback(action_id) -> str
Reverts last sandbox action from audit log.
