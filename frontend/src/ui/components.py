from __future__ import annotations

from html import escape
from urllib.parse import urlparse

import streamlit as st

from src.utils.formatters import format_score, status_label


def _extract_domain(url: str) -> str:
    try:
        return (urlparse(url).netloc or "source externe").replace("www.", "")
    except Exception:  # noqa: BLE001
        return "source externe"


def render_header(index_ready: bool, llm_ready: bool, backend_url: str) -> None:
    label, css_class = status_label(index_ready=index_ready, llm_ready=llm_ready)
    st.markdown(
        (
            '<div class="main-shell">'
            '<div class="brand-title">Workways FAQ Assistant</div>'
            '<div class="brand-sub">Pose une question en langage naturel. La reponse est construite uniquement a partir des FAQ les plus pertinentes.</div>'
            f'<div class="status-chip {css_class}">{escape(label)} | API: {escape(backend_url)}</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


def render_toolbar(message_count: int) -> None:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            (
                '<div class="metric-tile">'
                '<div class="metric-label">Messages session</div>'
                f'<div class="metric-value">{message_count}</div>'
                '</div>'
            ),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            (
                '<div class="metric-tile">'
                '<div class="metric-label">Retrieval</div>'
                '<div class="metric-value">Top 3 FAQ</div>'
                '</div>'
            ),
            unsafe_allow_html=True,
        )


def render_chat_bubble(role: str, content: str) -> None:
    css = "chat-user" if role == "user" else "chat-assistant"
    st.markdown(
        f'<div class="chat-bubble {css}">{escape(content)}</div>',
        unsafe_allow_html=True,
    )


def render_sources(sources: list[dict]) -> None:
    if not sources:
        return

    cards = []
    for source in sorted(sources, key=lambda s: s.get("rank", 999))[:3]:
        question = escape(str(source.get("question", "-")))
        url = escape(str(source.get("url", "#")))
        rank = int(source.get("rank", 0))
        score = format_score(float(source.get("score", 0.0)))
        domain = escape(_extract_domain(str(source.get("url", ""))))
        cards.append(
            (
                '<div class="source-card">'
                f'<div class="source-meta">FAQ #{rank} | score {score}</div>'
                f'<div class="source-q">{question}</div>'
                f'<div class="source-domain">Source: {domain}</div>'
                f'<a class="source-link" href="{url}" target="_blank">Ouvrir la source</a>'
                '</div>'
            )
        )

    st.markdown('<div class="sources-title">FAQ utilisees pour la reponse</div>', unsafe_allow_html=True)
    st.markdown('<div class="sources-wrap">' + "".join(cards) + "</div>", unsafe_allow_html=True)


def render_footer() -> None:
    st.markdown(
        '<div class="footer-note">Si les FAQ ne couvrent pas la question, la reponse peut etre: "Je ne sais pas."</div>',
        unsafe_allow_html=True,
    )
