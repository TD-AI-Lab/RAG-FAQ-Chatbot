from __future__ import annotations

import logging

import streamlit as st

from src.core.config import Settings, get_settings
from src.core.errors import BackendConnectionError, BackendResponseError, InputValidationError
from src.core.logging import configure_logging
from src.core.state import append_message, clear_history, init_session_state, next_request_id
from src.services.backend_client import BackendClient
from src.ui.components import render_chat_bubble, render_footer, render_header, render_sources, render_toolbar
from src.ui.theme import apply_theme
from src.utils.validators import validate_question

logger = logging.getLogger(__name__)


def _build_client(settings: Settings) -> BackendClient:
    return BackendClient(
        base_url=settings.backend_base_url,
        timeout_seconds=settings.request_timeout_seconds,
        chat_path=settings.backend_chat_path,
        health_path=settings.backend_health_path,
    )


@st.cache_data(ttl=10, show_spinner=False)
def _fetch_health(base_url: str, timeout_seconds: int, health_path: str, chat_path: str):
    client = BackendClient(
        base_url=base_url,
        timeout_seconds=timeout_seconds,
        chat_path=chat_path,
        health_path=health_path,
    )
    return client.health()


def _render_history() -> None:
    for msg in st.session_state.messages[-20:]:
        with st.chat_message("user" if msg["role"] == "user" else "assistant"):
            render_chat_bubble(msg["role"], msg["content"])
            if msg["role"] == "assistant":
                render_sources(msg.get("sources", []))


def _handle_prompt(prompt: str, settings: Settings) -> None:
    try:
        question = validate_question(prompt, settings.max_question_length)
    except InputValidationError as exc:
        st.error(str(exc))
        return

    req_id = next_request_id()
    logger.info("Submitting question %s", req_id)
    append_message("user", question)

    client = _build_client(settings)
    with st.chat_message("assistant"):
        with st.spinner("Recherche des FAQ les plus pertinentes..."):
            try:
                result = client.chat(question)
            except BackendConnectionError as exc:
                logger.error("%s connection error: %s", req_id, exc)
                error_msg = "Backend inaccessible. Verifie que l'API FastAPI tourne sur localhost:8000."
                append_message("assistant", error_msg, [])
                st.error(error_msg)
                return
            except BackendResponseError as exc:
                logger.warning("%s backend response error: %s", req_id, exc)
                append_message("assistant", str(exc), [])
                st.warning(str(exc))
                return

    sources = [source.model_dump() for source in sorted(result.sources, key=lambda s: s.rank)[:3]]
    append_message("assistant", result.answer, sources)
    st.rerun()


def run_app() -> None:
    configure_logging()
    st.set_page_config(
        page_title="Workways FAQ Assistant",
        page_icon="\U0001F4AC",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    apply_theme()
    init_session_state()

    settings = get_settings()

    backend_error = False
    try:
        health = _fetch_health(
            base_url=settings.backend_base_url,
            timeout_seconds=settings.request_timeout_seconds,
            health_path=settings.backend_health_path,
            chat_path=settings.backend_chat_path,
        )
        index_ready = health.index_ready
        llm_ready = health.llm_ready
    except Exception:  # noqa: BLE001
        index_ready = False
        llm_ready = False
        backend_error = True

    render_header(index_ready=index_ready, llm_ready=llm_ready, backend_url=settings.backend_base_url)
    render_toolbar(message_count=len(st.session_state.messages))

    if backend_error:
        st.error("Impossible de joindre le backend. Lance l'API puis rafraichis la page.")

    action_col, _ = st.columns([1, 5])
    with action_col:
        if st.button("Effacer l'historique", use_container_width=True):
            clear_history()
            st.rerun()

    _render_history()

    prompt = st.chat_input("Ex: Comment contacter le support Workways ?")
    if prompt:
        _handle_prompt(prompt, settings)

    if settings.show_debug:
        with st.expander("Debug", expanded=False):
            st.json(
                {
                    "backend": settings.backend_base_url,
                    "chat_path": settings.backend_chat_path,
                    "health_path": settings.backend_health_path,
                    "messages": len(st.session_state.messages),
                }
            )

    render_footer()
