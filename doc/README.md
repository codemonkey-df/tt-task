# Revenue Leakage Agent — Specification Index

Spec-driven implementation. **No feature code without its spec.**

## Core specs

| Document | Purpose |
|----------|---------|
| [architecture.md](architecture.md) | System design and data flow |
| [data-model.md](data-model.md) | Pydantic schemas |
| [tools-spec.md](tools-spec.md) | All agent tools |
| [agent-spec.md](agent-spec.md) | LangGraph ReAct agent |
| [memory-spec.md](memory-spec.md) | MemorySaver + thread_id |
| [ui-spec.md](ui-spec.md) | Streamlit chat UI |
| [demo-script.md](demo-script.md) | Evaluation demo |
| [ground-truth.md](ground-truth.md) | Embedded data leaks |

## Feature specs (implement in order)

| Feature | Spec |
|---------|------|
| F0 | [features/F0-scaffold.md](features/F0-scaffold.md) |
| F1 | [features/F1-data-models.md](features/F1-data-models.md) |
| F2 | [features/F2-read-tools.md](features/F2-read-tools.md) |
| F3 | [features/F3-investigate.md](features/F3-investigate.md) |
| F4 | [features/F4-sandbox.md](features/F4-sandbox.md) |
| F5 | [features/F5-llm.md](features/F5-llm.md) |
| F6 | [features/F6-agent-graph.md](features/F6-agent-graph.md) |
| F7 | [features/F7-streamlit-ui.md](features/F7-streamlit-ui.md) |
| F8 | [features/F8-integration.md](features/F8-integration.md) |

## Extensions

| Document | Purpose |
|----------|---------|
| [extensions/RAG_EXTENSION.md](extensions/RAG_EXTENSION.md) | Deferred RAG path |
