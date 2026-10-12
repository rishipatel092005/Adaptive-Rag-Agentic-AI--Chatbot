"""Create an anonymous workspace session and open the assistant."""

import streamlit as st

from utils.api_client import ApiError, create_guest_session
from utils.theme import apply_theme

st.set_page_config(page_title="Adaptive RAG", page_icon="✦", layout="wide")
apply_theme(st.session_state.get("theme", "Dark"))

if not st.session_state.get("access_token"):
    try:
        with st.spinner("Opening your private guest workspace…"):
            guest = create_guest_session()
        st.session_state["access_token"] = guest["access_token"]
        st.session_state["username"] = guest["username"]
        st.session_state["is_guest"] = True
        st.session_state["selected_conversation_id"] = None
    except ApiError as exc:
        st.markdown(
            """
            <div class="hero-panel">
              <div class="hero-eyebrow">ADAPTIVE RAG</div>
              <h1>Your knowledge. One conversation away.</h1>
              <p class="hero-copy">The assistant API is currently unavailable.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.error(str(exc))
        st.stop()

st.switch_page("pages/chat.py")
