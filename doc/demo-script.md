# Demo Script

## Prerequisites

```bash
ollama serve
ollama pull minimax-m3:cloud  # or ensure model available
cd sandobx/revenue_leakage_agent
uv sync
uv run streamlit run app.py
```

## Conversation steps

### 1. Investigate C-1001

**User:** Check plan C-1001 for revenue leakage issues.

**Expected:** Agent finds missing September 2025 invoice ($8,000 USD).

### 2. Memory test

**User:** What currency is that plan in?

**Expected:** USD — without user repeating plan ID.

### 3. Propose and apply make-good

**User:** Create a make-good invoice for the missing September billing.

**Expected:** Agent proposes $8,000 make-good. User approves. Sandbox invoice appended.

### 4. Investigate C-1010

**User:** What about plan C-1010?

**Expected:** $20,000 underbilling (invoice $100k vs plan $120k annual).
