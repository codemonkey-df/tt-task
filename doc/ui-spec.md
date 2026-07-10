# UI Specification

## Framework

Streamlit chat (`app.py`)

## Layout

- Title + Ollama status indicator
- `st.chat_message` history loop
- `st.chat_input` for user messages
- `st.expander("Tool trace")` for tool calls in last response
- Approve / Reject buttons when pending_action in session

## Session state

| Key | Type | Purpose |
|-----|------|---------|
| thread_id | str (uuid) | MemorySaver thread |
| graph_app | CompiledGraph | LangGraph app |
| pending_action | dict \| None | Awaiting approval |
| messages_display | list | UI chat history |

## Approve flow

1. Agent calls propose_* → stores draft in response
2. UI detects pending proposal → shows Approve/Reject
3. Approve → sends "Yes, apply it" or calls apply tool directly
4. Reject → clears pending_action
