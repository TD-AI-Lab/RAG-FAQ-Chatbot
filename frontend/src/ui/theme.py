from __future__ import annotations

import streamlit as st


THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

:root {
  --bg: #f3f6f4;
  --surface: #ffffff;
  --surface-soft: #f8faf9;
  --text: #0f1d19;
  --text-muted: #344741;
  --line: #bfd0c8;
  --brand: #0a8a69;
  --brand-2: #d46f24;
  --ok-bg: #e4f6ee;
  --ok-text: #0c6e53;
  --warn-bg: #fff2df;
  --warn-text: #8a4e0b;
  --bad-bg: #fde9e8;
  --bad-text: #8f271f;
}

.stApp {
  background:
    radial-gradient(900px 320px at -10% -25%, #d8ece4 0%, transparent 58%),
    linear-gradient(180deg, #f8fbf9 0%, #eef3f0 100%);
  color: var(--text) !important;
}

html, body {
  font-family: "IBM Plex Sans", sans-serif;
  color: var(--text) !important;
}

h1, h2, h3, h4 {
  font-family: "Space Grotesk", sans-serif;
  letter-spacing: -0.01em;
}

.block-container {
  max-width: 1120px;
  padding-top: 1.3rem;
  padding-bottom: 2.2rem;
}

.main-shell {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 1.05rem 1.15rem;
  box-shadow: 0 12px 30px rgba(12, 25, 20, 0.08);
}

.brand-title {
  font-size: 1.72rem;
  line-height: 1.15;
  font-weight: 700;
  margin-bottom: .35rem;
}

.brand-sub {
  color: var(--text-muted);
  font-size: 0.98rem;
  line-height: 1.45;
  margin-bottom: .7rem;
}

.status-chip {
  display: inline-flex;
  align-items: center;
  gap: .45rem;
  border-radius: 999px;
  padding: .36rem .78rem;
  font-size: .88rem;
  font-weight: 600;
  border: 1px solid transparent;
}

.status-ok { background: var(--ok-bg); color: var(--ok-text); border-color: #bce4d3; }
.status-warn { background: var(--warn-bg); color: var(--warn-text); border-color: #f3cf9c; }
.status-bad { background: var(--bad-bg); color: var(--bad-text); border-color: #ebb7b2; }

.toolbar {
  margin: .72rem 0 1.05rem 0;
  border: 1px solid var(--line);
  background: var(--surface-soft);
  border-radius: 14px;
  padding: .68rem .72rem;
}

.metric-tile {
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fff;
  padding: .66rem .72rem;
}

.metric-label {
  font-size: .83rem;
  color: var(--text-muted);
}

.metric-value {
  font-size: 1rem;
  font-weight: 700;
  margin-top: .08rem;
}

.chat-bubble {
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: .86rem .95rem;
  margin-bottom: .45rem;
  font-size: 0.99rem;
  line-height: 1.5;
  color: var(--text) !important;
}

.chat-bubble * {
  color: var(--text) !important;
  opacity: 1 !important;
}

.chat-user {
  background: #eaf7f2;
  border-left: 5px solid var(--brand);
}

.chat-assistant {
  background: var(--surface);
  border-left: 5px solid var(--brand-2);
}

.sources-title {
  margin-top: .28rem;
  margin-bottom: .45rem;
  font-size: .89rem;
  font-weight: 700;
  color: #20352e;
}

.sources-wrap {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: .78rem;
  margin-top: .35rem;
}

.source-card {
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--surface);
  padding: .78rem;
}

.source-meta {
  font-size: .85rem;
  font-weight: 600;
  color: #29433b;
  margin-bottom: .24rem;
}

.source-q {
  font-size: .95rem;
  font-weight: 600;
  line-height: 1.35;
  margin-bottom: .5rem;
  color: var(--text) !important;
}

.source-domain {
  font-size: .83rem;
  color: var(--text-muted);
  margin-bottom: .4rem;
}

a.source-link {
  color: #0a6f53;
  text-decoration: none;
  font-weight: 700;
  font-size: .9rem;
}

a.source-link:hover {
  text-decoration: underline;
}

.footer-note {
  margin-top: .9rem;
  font-size: .9rem;
  color: var(--text-muted) !important;
}

[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] div {
  color: var(--text) !important;
  opacity: 1 !important;
}

[data-testid="stChatInput"] textarea,
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
  background: #fff !important;
  color: var(--text) !important;
  border-radius: 12px !important;
  border: 1px solid var(--line) !important;
  font-size: .98rem !important;
  -webkit-text-fill-color: var(--text) !important;
}

[data-testid="stChatInput"] textarea:focus,
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
  border-color: #0c8f6c !important;
  box-shadow: 0 0 0 2px rgba(12, 143, 108, 0.2) !important;
}

.stButton > button {
  border: 1px solid #2f4a41 !important;
  background: #10251f !important;
  color: #f8fffc !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
}

.stButton > button:hover {
  background: #16352c !important;
}

.stButton > button:focus-visible {
  outline: 3px solid rgba(10, 138, 105, 0.35) !important;
  outline-offset: 2px !important;
}

[data-testid="stAlert"] {
  border-radius: 12px;
}

@media (max-width: 900px) {
  .brand-title { font-size: 1.42rem; }
  .brand-sub { font-size: .93rem; }
  .chat-bubble { font-size: .96rem; }
  .sources-wrap { grid-template-columns: 1fr; }
}
</style>
"""


def apply_theme() -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)
