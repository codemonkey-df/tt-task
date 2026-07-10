"""LiteLLM / Ollama LLM configuration."""

from __future__ import annotations

import os

from langchain_litellm import ChatLiteLLM


def get_llm() -> ChatLiteLLM:
    """Return configured ChatLiteLLM pointing at local Ollama."""
    return ChatLiteLLM(
        model=os.getenv("LITELLM_MODEL", "ollama/minimax-m3:cloud"),
        api_base=os.getenv("OLLAMA_API_BASE", "http://localhost:11434"),
        temperature=0,
    )
