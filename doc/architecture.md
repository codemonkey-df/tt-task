# Architecture

## Overview

Conversational Revenue Leakage Agent: LangGraph ReAct + tools + Streamlit chat.

```
User → Streamlit → LangGraph (MemorySaver) → LLM (Ollama/LiteLLM)
                              ↓
                         ToolNode → data/*.json (read) + sandbox/*.json (write)
```

## Design principles

1. **Spec before code** — each feature has a doc/features spec
2. **Tools compute dollars** — LLM selects tools and explains, never invents amounts
3. **Pydantic domain models** — validated data at tool boundaries
4. **MemorySaver** — across-turn conversation context via thread_id
5. **Human approve** — propose before apply to sandbox

## Stack

- Python 3.13, uv
- LangGraph ReAct agent
- LiteLLM → Ollama `minimax-m3:cloud` on localhost:11434
- Streamlit chat UI
- JSON data files (no parsing required)
