# Revenue Leakage Agent


![Extract Data](doc/logo.png)

A conversational AI agent that investigates billing anomalies between contracts (billing plans) and invoices, proposes corrective actions, and applies fixes to a sandbox environment — only after human approval.

Built for SaaS revenue operations teams who need to detect missed billing, FX overbilling, amount mismatches, and orphan invoices without manually cross-referencing spreadsheets.

---

## Purpose

Revenue leakage happens when customers are billed incorrectly — or not billed at all — relative to their contract terms. This agent automates the investigation workflow:

1. **Investigate** — Compare billing plans against invoices using deterministic rules (not LLM math).
2. **Explain** — Surface findings with evidence: invoice IDs, expected vs. actual amounts, and variance.
3. **Propose** — Draft corrective actions (make-good invoice, credit memo, or plan amendment).
4. **Apply** — Write changes to a sandbox only after the user explicitly approves.

The LLM orchestrates tool calls and explains results; all dollar amounts come from tool outputs. This keeps investigations auditable and prevents hallucinated figures.

### Embedded demo scenarios

The bundled `data/` files contain intentional leakage cases for evaluation:

| Plan / Invoice | Issue | Fix type | Impact |
|----------------|-------|----------|--------|
| C-1001 | Missing September 2025 invoice | make-good invoice | $8,000 USD |
| C-1010 | Invoice $100k vs plan $120k annual | make-good invoice | $20,000 USD |
| C-1007 | Invoice $20k vs expected $22.5k/qtr | make-good invoice | $2,500 USD |
| C-1007-A1 | EUR invoice vs USD plan; partial credit memo | credit memo | ~$2,000 USD |
| I-9202 | Orphan invoice (no `plan_id`) | manual review | $15,000 USD |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.13 |
| Package manager | [uv](https://docs.astral.sh/uv/) |
| Agent framework | [LangGraph](https://langchain-ai.github.io/langgraph/) (ReAct agent) |
| LLM integration | [LiteLLM](https://docs.litellm.ai/) via `langchain-litellm` |
| Local LLM runtime | [Ollama](https://ollama.com/) (default: `minimax-m3:cloud`) |
| Data validation | [Pydantic](https://docs.pydantic.dev/) v2 |
| Chat UI | [Streamlit](https://streamlit.io/) |
| Persistence | JSON files (`data/` read-only, `sandbox/` writable) |
| Dev tooling | pytest, ruff, mypy |

---

## Architecture

```
User → Streamlit UI → LangGraph (ReAct + MemorySaver) → LLM (Ollama via LiteLLM)
                              ↓
                         ToolNode → data/*.json (read) + sandbox/*.json (write)
```

**Design principles:**

- **Tools compute dollars** — The LLM selects tools and explains; it never invents amounts.
- **Deterministic investigation** — `investigate_plan` runs rule-based checks (missing invoices, FX overbilling, amount mismatches, underbilling).
- **Human-in-the-loop** — Propose actions first; apply only after explicit user confirmation.
- **Conversation memory** — `MemorySaver` checkpointing preserves context across turns via `thread_id`.
- **Sandbox isolation** — All writes go to `sandbox/` with a full audit log; source data in `data/` is never modified.

---

## Prerequisites

- **Python 3.13+**
- **[uv](https://docs.astral.sh/uv/)** installed
- **[Ollama](https://ollama.com/)** running locally

```bash
# Start Ollama and pull the default model
ollama serve
ollama pull minimax-m3:cloud
```

---

## Installation

```bash
cd revenue_leakage_agent
uv sync
```

For development dependencies (pytest, ruff, mypy):

```bash
uv sync --group dev
```

---

## Configuration

Environment variables (all optional):

| Variable | Default | Description |
|----------|---------|-------------|
| `LITELLM_MODEL` | `ollama/minimax-m3:cloud` | LiteLLM model identifier |
| `OLLAMA_API_BASE` | `http://localhost:11434` | Ollama API base URL |

Example:

```bash
export LITELLM_MODEL="ollama/llama3.2"
export OLLAMA_API_BASE="http://localhost:11434"
```

---

## Usage

### Streamlit chat UI (recommended)

```bash
uv run streamlit run app.py
```

Open the URL shown in the terminal (typically `http://localhost:8501`).

The UI provides:

- A chat interface for natural-language billing questions
- Live tool-call tracing (arguments and results)
- Approve / Reject buttons when the agent proposes a corrective action
- Ollama connectivity status on startup

**Example prompts:**

```
Check plan C-1001 for revenue leakage issues.
```

```
What currency is that plan in?
```

```
Create a make-good invoice for the missing September billing.
```

```
What about plan C-1010?
```

```
Find orphan invoices with no plan reference.
```

### CLI (smoke test)

Run a single message against the agent without the UI:

```bash
# Default prompt: "Check plan C-1001 for revenue leakage"
uv run revenue-leakage-agent

# Custom prompt
uv run revenue-leakage-agent Investigate plan C-1010 for underbilling
```

### Approval workflow

1. Ask the agent to investigate a plan or issue.
2. When leakage is found, ask it to propose a fix (e.g. "Create a make-good invoice for the missing month").
3. The agent calls a `propose_*` tool and returns an `ActionDraft` JSON.
4. In the Streamlit UI, click **Approve** to apply the action to the sandbox, or **Reject** to discard it.
5. Applied actions are recorded in `sandbox/audit_log.json` and can be rolled back via the `rollback` tool.

---

## Agent Tools

### Read tools

| Tool | Description |
|------|-------------|
| `load_plan` | Load billing plan details by `plan_id` |
| `query_invoices` | Filter invoices by plan, customer, date range |
| `query_credit_memos` | Filter credit memos by plan or invoice |
| `fx_convert` | Convert amounts using `data/exchange_rates.json` |
| `investigate_plan_tool` | Run deterministic leakage checks for a plan |
| `find_orphan_invoices_tool` | Find invoices with no `plan_id` |

### Propose tools (no writes)

| Tool | Description |
|------|-------------|
| `propose_make_good_invoice` | Draft a make-good invoice for missed/underbilling |
| `propose_credit_memo` | Draft a credit memo for overbilling |
| `propose_plan_amendment` | Draft a billing plan amendment |

### Sandbox tools

| Tool | Description |
|------|-------------|
| `apply` | Apply a proposed action to `sandbox/` (after user confirmation) |
| `rollback` | Undo a previously applied sandbox action |

See [doc/tools-spec.md](doc/tools-spec.md) for full tool signatures.

---

## Investigation Signals

The deterministic `investigate_plan` engine detects:

| Signal | Description |
|--------|-------------|
| `missing_invoice` | Expected monthly billing period has no invoice |
| `amount_mismatch` | Invoice amount differs from expected per-period amount |
| `underbilling` | Annual invoice total is below plan `total_value` |
| `fx_overbilling` | Foreign-currency invoice converts above expected (net of credit memos) |
| `fx_overbilling_corrected` | FX overbilling fully offset by existing credit memos |
| `currency_mismatch` | Invoice currency differs from plan with no FX rate available |
| `orphan_invoice` | Invoice has an empty `plan_id` |
| `plan_not_found` | Requested plan ID does not exist |

---

## Project Structure

```
revenue_leakage_agent/
├── app.py                          # Streamlit chat UI
├── data/                           # Read-only source billing data
│   ├── billing_plans.json
│   ├── invoices.json
│   ├── credit_memos.json
│   └── exchange_rates.json
├── sandbox/                        # Writable sandbox (created on first apply)
│   ├── invoices.json
│   ├── credit_memos.json
│   ├── billing_plans.json
│   └── audit_log.json
├── doc/                            # Spec-driven design documents
├── src/revenue_leakage_agent/
│   ├── cli.py                      # CLI entry point
│   ├── graph.py                    # LangGraph ReAct agent
│   ├── investigate.py              # Deterministic leakage checks
│   ├── tools.py                    # LangChain tool definitions
│   ├── sandbox.py                  # Sandbox write/rollback logic
│   ├── loaders.py                  # JSON data loaders
│   ├── models.py                   # Pydantic domain models
│   ├── fx.py                       # FX conversion helpers
│   ├── llm.py                      # LiteLLM / Ollama configuration
│   └── prompts.py                  # System prompt
└── tests/
```

---

## Development

### Run tests

```bash
uv run pytest
```

### Lint and format

```bash
uv run ruff check .
uv run ruff format .
```

### Type check

```bash
uv run mypy src/
```

### Pre-commit checklist

1. `uv run ruff check .`
2. `uv run ruff format .`
3. `uv run mypy src/`
4. `uv run pytest`

---

## Data Model

Core Pydantic models in `src/revenue_leakage_agent/models.py`:

- **BillingPlan** — Contract with `plan_id`, `total_value`, `currency`, `cadence` (Monthly / Quarterly / Annual), and `start_date`
- **Invoice** — Billed amount linked to a plan
- **CreditMemo** — Adjustment against an invoice or plan
- **ExchangeRate** — FX rate for a specific date and currency pair
- **Finding** — Single leakage signal with expected/actual amounts and evidence
- **InvestigationResult** — Aggregated findings for a plan
- **ActionDraft** — Proposed corrective action awaiting approval

Expected per-period billing is computed as `total_value / divisors[cadence]` where divisors are `{Monthly: 12, Quarterly: 4, Annual: 1}`.

---

## Available Demo Plans

| Plan ID | Customer | Cadence | Notes |
|---------|----------|---------|-------|
| C-1001 | ACME Corp | Monthly | $96k/year → $8k/month; missing Sep 2025 invoice |
| C-1007 | Globex Ltd | Quarterly | Superseded by C-1007-A1 |
| C-1007-A1 | Globex Ltd | Quarterly | Amendment from 2025-07-01; EUR/FX scenario |
| C-1010 | Initech | Annual | $120k plan; invoice billed at $100k |

---

## Documentation

This project follows a spec-driven development approach. Detailed design documents live in `doc/`:

| Document | Purpose |
|----------|---------|
| [doc/architecture.md](doc/architecture.md) | System design and data flow |
| [doc/tools-spec.md](doc/tools-spec.md) | Agent tool specifications |
| [doc/ground-truth.md](doc/ground-truth.md) | Embedded leakage scenarios |
| [doc/demo-script.md](doc/demo-script.md) | Step-by-step demo conversation |
| [doc/README.md](doc/README.md) | Full specification index |

---

## License

All rights reserved. No license granted without prior written permission
