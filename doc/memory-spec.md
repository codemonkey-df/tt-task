# Memory Specification

## Requirement

Challenge requires stateful conversation — follow-up questions without repeating context.

## Implementation

- LangGraph `MemorySaver` checkpointer (in-process, local)
- `thread_id` UUID in Streamlit `session_state`
- Each invoke passes only new `HumanMessage` + config thread_id

```python
config = {"configurable": {"thread_id": st.session_state.thread_id}}
app.invoke({"messages": [HumanMessage(content=user_input)]}, config=config)
```

## Within-turn vs across-turn

| Layer | Mechanism |
|-------|-----------|
| Within-turn tool loop | ReAct graph automatic |
| Across-turn history | MemorySaver + thread_id |

## Fallback

If checkpointing fails, accumulate messages in session_state manually.
