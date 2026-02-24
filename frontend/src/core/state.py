from __future__ import annotations

import uuid

import streamlit as st


def init_session_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "request_counter" not in st.session_state:
        st.session_state.request_counter = 0


def next_request_id() -> str:
    st.session_state.request_counter += 1
    return f"req-{st.session_state.request_counter}-{uuid.uuid4().hex[:8]}"


def append_message(role: str, content: str, sources: list[dict] | None = None) -> None:
    st.session_state.messages.append(
        {
            "role": role,
            "content": content,
            "sources": sources or [],
        }
    )


def clear_history() -> None:
    st.session_state.messages = []