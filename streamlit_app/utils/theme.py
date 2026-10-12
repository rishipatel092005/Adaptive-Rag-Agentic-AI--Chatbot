"""Shared navy-blue design system for the Streamlit interface."""

import streamlit as st


def apply_theme(theme: str = "Dark") -> None:
    dark = theme == "Dark"
    background = "#07111f" if dark else "#f3f7fc"
    surface = "#0c1a2c" if dark else "#ffffff"
    surface_raised = "#10223a" if dark else "#f9fbff"
    sidebar = "#081524" if dark else "#eaf1fa"
    foreground = "#edf5ff" if dark else "#13243a"
    muted = "#9aabc1" if dark else "#63758e"
    border = "rgba(151, 184, 222, .15)" if dark else "rgba(45, 84, 132, .15)"
    accent = "#6ab9ff"
    shadow = "0 18px 55px rgba(0, 0, 0, .26)" if dark else "0 18px 55px rgba(25, 67, 118, .10)"
    st.markdown(
        f"""
        <style>
        :root {{
          color-scheme: {"dark" if dark else "light"};
          --app-bg: {background};
          --app-surface: {surface};
          --app-raised: {surface_raised};
          --app-sidebar: {sidebar};
          --app-fg: {foreground};
          --app-muted: {muted};
          --app-border: {border};
          --app-accent: {accent};
        }}
        html, body, [data-testid="stAppViewContainer"] {{
          background: {background};
          color: {foreground};
          font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }}
        [data-testid="stAppViewContainer"] {{
          background:
            radial-gradient(ellipse at 72% 3%, rgba(36, 112, 191, .14), transparent 38%),
            radial-gradient(ellipse at 25% 66%, rgba(37, 83, 155, .09), transparent 42%),
            {background};
        }}
        [data-testid="stHeader"] {{ background: transparent; }}
        [data-testid="stToolbar"] {{ right: 1rem; }}
        [data-testid="stSidebar"] {{
          background: linear-gradient(180deg, {sidebar}, {surface});
          border-right: 1px solid {border};
          box-shadow: 8px 0 32px rgba(0, 0, 0, .10);
        }}
        [data-testid="stSidebar"] > div:first-child {{ padding-top: 1.1rem; }}
        [data-testid="stSidebarNav"] {{ display: none; }}
        .block-container {{
          max-width: 1120px;
          padding: 1.55rem clamp(1rem, 4vw, 3.2rem) 8rem;
        }}
        h1, h2, h3, h4, p, label, li, span {{ color: {foreground}; }}
        h1, h2, h3 {{ letter-spacing: -.035em; }}
        h1 {{ font-size: clamp(2rem, 3.35vw, 2.85rem) !important; line-height: 1.1 !important; }}
        h2 {{ font-size: clamp(1.45rem, 2.5vw, 2rem) !important; }}
        [data-testid="stCaptionContainer"] p {{ color: {muted}; }}
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{ color: {muted}; }}
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong {{ color: {foreground}; }}
        [data-testid="stVerticalBlockBorderWrapper"] {{
          background: linear-gradient(145deg, {surface_raised}, {surface});
          border: 1px solid {border};
          border-radius: 20px;
          box-shadow: {shadow};
        }}
        [data-testid="stChatMessage"] {{
          border: 1px solid {border};
          border-radius: 20px;
          padding: 1.15rem 1.3rem;
          margin: .9rem 0;
          background: linear-gradient(145deg, {surface_raised}, {surface});
          box-shadow: 0 8px 24px rgba(0, 0, 0, .08);
        }}
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {{
          line-height: 1.72;
          font-size: 1rem;
        }}
        [data-testid="stChatMessage"] pre {{
          border: 1px solid {border};
          border-radius: 14px;
          background: #071321;
        }}
        [data-testid="stChatMessage"] table {{
          border-collapse: collapse;
          border-radius: 12px;
          overflow: hidden;
        }}
        [data-testid="stChatMessage"] th {{ background: {surface_raised}; }}
        [data-testid="stChatMessage"] td, [data-testid="stChatMessage"] th {{
          border-color: {border};
          padding: .65rem .8rem;
        }}
        .stButton > button {{
          min-height: 2.65rem;
          border: 1px solid {border};
          border-radius: 13px;
          background: {surface_raised};
          color: {foreground};
          font-weight: 550;
          transition: background .16s ease, border-color .16s ease, transform .16s ease, box-shadow .16s ease;
        }}
        .stButton > button:hover {{
          border-color: rgba(106, 185, 255, .68);
          background: rgba(60, 137, 210, .15);
          color: {foreground};
          transform: translateY(-1px);
          box-shadow: 0 8px 24px rgba(40, 127, 214, .12);
        }}
        .stButton > button:focus-visible, input:focus-visible, textarea:focus-visible {{
          outline: 2px solid {accent} !important;
          outline-offset: 2px;
        }}
        .stButton > button[kind="primary"], [data-testid^="stBaseButton-primary"] {{
          color: #061528;
          border: 1px solid rgba(157, 216, 255, .55);
          border-radius: 13px !important;
          background: linear-gradient(120deg, #71c6ff, #5c9cff);
          box-shadow: 0 8px 24px rgba(57, 151, 234, .23);
        }}
        .stButton > button[kind="primary"]:hover, [data-testid^="stBaseButton-primary"]:hover {{
          color: #061528;
          background: linear-gradient(120deg, #92d4ff, #75adff);
        }}
        [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
        [data-testid="stChatInput"] textarea, [data-baseweb="select"] > div {{
          color: {foreground};
          background: {surface};
          border: 1px solid {border};
          border-radius: 13px;
        }}
        input[type="radio"], input[type="checkbox"] {{ accent-color: {accent}; }}
        [data-testid="stChatInput"] {{
          background: transparent;
          border-color: transparent;
        }}
        [data-testid="stChatInput"] > div {{
          background: {surface_raised};
          border: 1px solid rgba(106, 185, 255, .24);
          border-radius: 22px;
          box-shadow: {shadow};
        }}
        [data-testid="stFileUploader"] section {{
          border: 1px dashed rgba(106, 185, 255, .38);
          border-radius: 14px;
          background: rgba(54, 125, 190, .07);
        }}
        [data-testid="stExpander"] {{
          border: 1px solid {border};
          border-radius: 14px;
          background: rgba(12, 26, 44, .34);
        }}
        [data-testid="stAlert"] {{ border-radius: 14px; }}
        .brand-lockup {{
          display: flex;
          align-items: center;
          gap: .8rem;
          padding: .65rem .25rem 1.2rem;
        }}
        .brand-glyph {{
          display: grid;
          width: 2.55rem;
          height: 2.55rem;
          place-items: center;
          border: 1px solid rgba(119, 198, 255, .42);
          border-radius: 13px;
          color: #b4e2ff;
          background: linear-gradient(145deg, rgba(71, 157, 231, .34), rgba(48, 87, 181, .25));
          box-shadow: 0 0 24px rgba(68, 158, 237, .19);
          font-size: 1.2rem;
          font-weight: 800;
        }}
        .brand-name {{ color: {foreground}; font-weight: 750; letter-spacing: -.02em; }}
        .brand-subtitle {{ color: {muted}; font-size: .72rem; margin-top: .08rem; }}
        .section-label {{
          color: {muted};
          font-size: .67rem;
          font-weight: 750;
          letter-spacing: .13em;
          margin: 1.25rem .2rem .45rem;
        }}
        .hero-eyebrow {{
          color: #8dceff;
          font-size: .74rem;
          font-weight: 750;
          letter-spacing: .15em;
          text-transform: uppercase;
        }}
        .hero-copy {{
          max-width: 720px;
          margin: .5rem auto 0;
          color: {muted};
          font-size: clamp(1rem, 1.7vw, 1.16rem);
          line-height: 1.7;
        }}
        .hero-panel {{
          position: relative;
          overflow: hidden;
          padding: clamp(1.8rem, 5vw, 3.7rem);
          border: 1px solid rgba(114, 180, 237, .22);
          border-radius: 28px;
          background:
            radial-gradient(ellipse at 88% 2%, rgba(56, 154, 236, .2), transparent 38%),
            linear-gradient(145deg, rgba(17, 42, 70, .94), rgba(9, 24, 42, .94));
          box-shadow: 0 28px 80px rgba(0, 0, 0, .2);
          text-align: center;
        }}
        .hero-panel h1 {{ max-width: 700px; margin: .65rem auto .75rem; }}
        .status-pill {{
          display: inline-flex;
          align-items: center;
          gap: .45rem;
          padding: .4rem .72rem;
          border: 1px solid rgba(103, 204, 177, .23);
          border-radius: 999px;
          color: #9de2cd;
          background: rgba(31, 130, 104, .1);
          font-size: .74rem;
          font-weight: 650;
        }}
        .soft-divider {{ height: 1px; background: {border}; margin: .75rem 0 1rem; }}
        .chat-heading {{
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 1rem;
          padding: .35rem 0 1rem;
          border-bottom: 1px solid {border};
          margin-bottom: 1rem;
        }}
        .chat-heading-title {{ color: {foreground}; font-size: 1.05rem; font-weight: 680; }}
        .chat-heading-subtitle {{ color: {muted}; font-size: .78rem; margin-top: .12rem; }}
        @media (max-width: 800px) {{
          .block-container {{ padding: 1rem .9rem 7rem; }}
          [data-testid="stSidebar"] {{ box-shadow: 5px 0 24px rgba(0, 0, 0, .18); }}
          [data-testid="stChatMessage"] {{ padding: .9rem 1rem; }}
        }}
        @media (max-width: 560px) {{
          .block-container {{ padding-inline: .7rem; }}
          .hero-panel {{ border-radius: 20px; padding: 1.6rem 1.05rem; }}
          .chat-heading {{ align-items: flex-start; }}
        }}
        @media (prefers-reduced-motion: reduce) {{
          *, *::before, *::after {{ scroll-behavior: auto !important; transition-duration: .01ms !important; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
