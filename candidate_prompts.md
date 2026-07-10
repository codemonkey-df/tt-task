# Candidate AI Tool Usage Log

**Instructions for Candidates:**
Please document all prompts you use with AI tools during this challenge. This helps us understand your problem-solving approach and AI tool utilization skills.

---

## Reflection on AI Tool Effectiveness

Cursor (Claude) was used to plan and build the Revenue Leakage Agent. The workflow was: receive challenge data → read official documentation → choose tech stack → spec-driven implementation → tests. The AI helped structure the work into small features (F0–F8) with `doc/` specs before code, which kept the 1.5h scope manageable and aligned with the challenge requirements.

---

## AI Tool Usage Log

### Prompt 1
**Tool Used:** Cursor (Claude)
**Context:** Received challenge data and explored how to implement the agent
**Prompt:**
```
We got data from technical-case — investigate how to implement
an Agent Detective for Revenue Leakage. Read the documentation provided (readme.md and
data files) and propose an approach.
```

**Result:** Reviewed `readme.md` and JSON data (`billing_plans`, `invoices`, `credit_memos`, `exchange_rates`). Identified requirements: conversational stateful agent, investigate anomalies, propose/apply fixes to sandbox, Streamlit chat UI, 8 tools from spec.
**Follow-up:** Read full technical-case documentation.

---

### Prompt 2
**Tool Used:** Cursor (Claude)
**Context:** Read official challenge documentation in detail
**Prompt:**
```
Read technical-case — review readme.md and data/. Understand
objectives, tools, UI requirements, and embedded leakage cases (C-1001 missing September,
C-1010 underbilling, etc.).
```

**Result:** Mapped challenge objectives to implementation: investigate + propose + apply with human approval, maintain conversation context, document prompts in `candidate_prompts.md`.
**Follow-up:** Choose tech stack.

---

### Prompt 3
**Tool Used:** Cursor (Claude)
**Context:** Select stack for prototype
**Prompt:**
```
Choose tech stack for Revenue Leakage Agent: Python 3.13 (uv), LangGraph ReAct agent,
LiteLLM → Ollama minimax-m3:cloud on localhost, Streamlit chat UI, Pydantic models,
MemorySaver for conversation memory.
```

**Result:** Stack confirmed: `uv init --python=3.13`, LangGraph + ToolNode, LiteLLM/Ollama, Streamlit with `thread_id`, deterministic `investigate_plan` tool for reliable leakage detection.
**Follow-up:** Decide on development approach.

---

### Prompt 4
**Tool Used:** Cursor (Claude)
**Context:** Adopt spec-driven development
**Prompt:**
```
Follow specification-driven development: split the task into smaller features (F0–F8),
write specs in doc/ folder before implementation, then implement each feature and verify
acceptance criteria.
```

**Result:** Feature map: F0 scaffold + docs → F1 models → F2 read tools → F3 investigate → F4 sandbox → F5 LLM → F6 graph → F7 Streamlit → F8 integration. Each feature has `doc/features/Fx-*.md` with goal, API, acceptance criteria.
**Follow-up:** Implement all features per plan.

---

### Prompt 5
**Tool Used:** Cursor (Claude)
**Context:** Implement full solution following specs and challenge tasks
**Prompt:**
```
Implement Revenue Leakage Agent per spec-driven plan: all readme tools, sandbox
propose/apply/rollback, LangGraph agent with MemorySaver, Streamlit UI with approve flow.
Use uv init --python=3.13. Copy challenge data into project.
```

**Result:** Built `sandobx/revenue_leakage_agent/` — models, loaders, tools, investigate, sandbox, llm, graph, app.py, doc/ specs. All 4 data files copied from `technical-case/data/`.
**Follow-up:** Write tests.

---

### Prompt 6
**Tool Used:** Cursor (Claude)
**Context:** Add tests for deterministic investigation and sandbox
**Prompt:**
```
Write tests: C-1001 missing September, C-1010 underbilling, fx_convert, sandbox apply
make-good invoice. Run pytest and fix until passing.
```

**Result:** `tests/test_investigate.py` and `tests/test_sandbox.py` — 7 tests passing. Verified loaders (4 plans, 13 invoices), investigation findings, and sandbox writes.
**Follow-up:** None.

---

**Note:** Prompts document the Revenue Leakage Agent challenge only — from data review through spec-driven implementation and testing.
