# F5 — LLM Layer

## Goal
LiteLLM wrapper for Ollama minimax-m3:cloud on localhost:11434.

## Env
- LITELLM_MODEL=ollama/minimax-m3:cloud
- OLLAMA_API_BASE=http://localhost:11434

## Acceptance criteria
- [ ] get_llm().invoke("hello") works with Ollama running

## Dependencies
F0

## Out of scope
Graph, UI
