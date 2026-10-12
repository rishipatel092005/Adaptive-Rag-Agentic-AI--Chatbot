"""Responsive, persistent AI document-assistant workspace."""

from datetime import datetime, timezone

import streamlit as st

from utils.api_client import (
    ApiError,
    create_conversation,
    delete_conversation,
    get_current_user,
    list_conversations,
    list_documents,
    load_conversation,
    logout as revoke_session,
    rename_conversation,
    send_query,
    upload_document,
)
from utils.theme import apply_theme

st.set_page_config(page_title="Adaptive RAG", page_icon="✦", layout="wide")


def logout() -> None:
    token = st.session_state.get("access_token")
    if token:
        try:
            revoke_session(token)
        except ApiError as exc:
            st.session_state["logout_warning"] = (
                f"Signed out on this device, but the API could not revoke the token: {exc}"
            )
    for key in (
        "access_token",
        "username",
        "selected_conversation_id",
        "pending_query",
        "retry_query",
    ):
        st.session_state.pop(key, None)
    st.switch_page("home.py")


def require_session() -> bool:
    token = st.session_state.get("access_token")
    if not token:
        st.switch_page("home.py")
        return False
    try:
        profile = get_current_user(token)
        st.session_state["username"] = profile["username"]
        return True
    except ApiError as exc:
        if exc.status_code == 401:
            logout()
            return False
        st.error(str(exc))
        st.stop()
    return True


def relative_date(value: str) -> str:
    try:
        created = datetime.fromisoformat(value.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - created
    except (ValueError, TypeError):
        return "Recent"
    if delta.days <= 0:
        return "Today"
    if delta.days == 1:
        return "Yesterday"
    if delta.days < 7:
        return f"{delta.days} days ago"
    return created.astimezone().strftime("%b %d")


def show_delete_dialog() -> None:
    @st.dialog("Delete this conversation?")
    def confirm():
        st.write("This permanently deletes this conversation and its saved messages.")
        left, right = st.columns(2)
        with left:
            if st.button("Keep conversation", use_container_width=True):
                st.session_state.pop("delete_conversation_id", None)
                st.rerun()
        with right:
            if st.button("Delete conversation", type="primary", use_container_width=True):
                try:
                    delete_conversation(
                        st.session_state["access_token"],
                        st.session_state["delete_conversation_id"],
                    )
                    st.session_state["selected_conversation_id"] = None
                    st.session_state.pop("delete_conversation_id", None)
                    st.rerun()
                except ApiError as exc:
                    st.error(str(exc))

    confirm()


def ensure_conversation() -> str:
    conversation_id = st.session_state.get("selected_conversation_id")
    if not conversation_id:
        record = create_conversation(st.session_state["access_token"])
        conversation_id = record["id"]
        st.session_state["selected_conversation_id"] = conversation_id
    return conversation_id


def submit_query(query: str) -> None:
    query = query.strip()
    if not query:
        return
    try:
        conversation_id = ensure_conversation()
        with st.spinner("Thinking through your question…"):
            send_query(st.session_state["access_token"], conversation_id, query)
        st.session_state.pop("retry_query", None)
        st.session_state.pop("query_error", None)
        st.rerun()
    except ApiError as exc:
        st.session_state["retry_query"] = query
        st.session_state["query_error"] = str(exc)
        st.rerun()


def upload_files(files) -> bool:
    if not files:
        return True
    for file in files:
        try:
            with st.spinner(f"Indexing {file.name}…"):
                upload_document(
                    st.session_state["access_token"],
                    file,
                    f"User-provided reference document: {file.name}",
                )
            st.toast(f"{file.name} is ready to use.")
        except ApiError as exc:
            st.error(f"Could not upload {file.name}: {exc}")
            return False
    return True


if not require_session():
    st.stop()

apply_theme(st.session_state.get("theme", "Dark"))
token = st.session_state["access_token"]

search_filter = st.session_state.get("conversation_search", "")
try:
    conversations = list_conversations(token, search_filter)
except ApiError as exc:
    conversations = []
    st.session_state["conversation_storage_error"] = str(exc)
else:
    st.session_state.pop("conversation_storage_error", None)

selected_id = st.session_state.get("selected_conversation_id")
selected = next((item for item in conversations if item["id"] == selected_id), None)
conversation = None
if selected:
    try:
        conversation = load_conversation(token, selected_id)
    except ApiError as exc:
        st.error(str(exc))

section = st.session_state.get("workspace_section", "Home")

with st.sidebar:
    st.markdown(
        """
        <div class="brand-lockup">
          <div class="brand-glyph">✦</div>
          <div><div class="brand-name">Adaptive RAG</div>
          <div class="brand-subtitle">AGENTIC KNOWLEDGE WORKSPACE</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("＋  New Chat", type="primary", use_container_width=True):
        try:
            record = create_conversation(token)
            st.session_state["selected_conversation_id"] = record["id"]
            st.session_state["workspace_section"] = "Chat"
            st.session_state.pop("retry_query", None)
            st.rerun()
        except ApiError as exc:
            st.error(str(exc))

    st.markdown('<div class="section-label">WORKSPACE</div>', unsafe_allow_html=True)
    for label, icon in (
        ("Home", "⌂"),
        ("Chat History", "▤"),
        ("Documents", "▧"),
        ("Settings", "⚙"),
    ):
        active = (
            section == label
            or (label == "Chat History" and section == "Chat")
        )
        if st.button(
            f"{icon}   {label}",
            key=f"nav_{label}",
            type="primary" if active else "secondary",
            use_container_width=True,
        ):
            st.session_state["workspace_section"] = label
            if label == "Home":
                st.session_state["selected_conversation_id"] = None
            st.rerun()

    st.markdown('<div class="section-label">RECENT CONVERSATIONS</div>', unsafe_allow_html=True)
    st.text_input(
        "Search conversations",
        placeholder="⌕  Search chats",
        label_visibility="collapsed",
        key="conversation_search",
    )
    for item in conversations[:12]:
        is_selected = item["id"] == selected_id
        title = item["title"][:27] + ("…" if len(item["title"]) > 27 else "")
        chat_col, menu_col = st.columns([5, 1], vertical_alignment="center")
        with chat_col:
            if st.button(
                f"{'●' if is_selected else '○'}  {title}",
                key=f"open_{item['id']}",
                use_container_width=True,
                help=item["title"],
            ):
                st.session_state["selected_conversation_id"] = item["id"]
                st.session_state["workspace_section"] = "Chat"
                st.session_state.pop("retry_query", None)
                st.rerun()
            st.caption(relative_date(item["updated_at"]))
        with menu_col:
            with st.popover("⋯", help=f"Actions for {item['title']}", use_container_width=True):
                if st.button("Rename", key=f"rename_{item['id']}", use_container_width=True):
                    st.session_state["rename_conversation_id"] = item["id"]
                    st.session_state["rename_conversation_title"] = item["title"]
                if st.button("Delete", key=f"delete_{item['id']}", use_container_width=True):
                    st.session_state["delete_conversation_id"] = item["id"]
                    st.rerun()
        if st.session_state.get("rename_conversation_id") == item["id"]:
            with st.form(f"rename_form_{item['id']}"):
                title_input = st.text_input(
                    "Chat name",
                    value=st.session_state.get("rename_conversation_title", item["title"]),
                    max_chars=120,
                )
                save, cancel = st.columns(2)
                with save:
                    save_title = st.form_submit_button("Save")
                with cancel:
                    cancel_rename = st.form_submit_button("Cancel")
            if save_title:
                try:
                    rename_conversation(token, item["id"], title_input)
                    st.session_state.pop("rename_conversation_id", None)
                    st.rerun()
                except ApiError as exc:
                    st.error(str(exc))
            if cancel_rename:
                st.session_state.pop("rename_conversation_id", None)
                st.rerun()

    if not conversations:
        st.caption("Your recent chats will appear here.")

    st.divider()
    profile_col, setting_col = st.columns([4, 1], vertical_alignment="center")
    with profile_col:
        st.markdown(
            f"**◉  {st.session_state['username']}**  \n"
            "<small>Anonymous guest session</small>",
            unsafe_allow_html=True,
        )
    with setting_col:
        with st.popover("⚙", help="Profile and settings", use_container_width=True):
            st.selectbox("Appearance", ["Dark", "Light"], key="theme")
            if st.button("Log out", use_container_width=True):
                logout()

if st.session_state.get("delete_conversation_id"):
    show_delete_dialog()

try:
    uploaded_documents = list_documents(token)
except ApiError as exc:
    uploaded_documents = []
    if section == "Documents":
        st.error(str(exc))

if section == "Settings":
    st.markdown(
        """
        <div class="hero-eyebrow">PREFERENCES</div>
        <h1 style="margin:.55rem 0">Settings</h1>
        <p class="hero-copy" style="margin:0">Make your knowledge workspace feel like yours.</p>
        """,
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        st.subheader("Appearance")
        st.selectbox("Color theme", ["Dark", "Light"], key="theme")
        st.caption("Theme preference is kept for this active Streamlit session.")
    with st.container(border=True):
        st.subheader("Account")
        st.write("You are using an anonymous guest session.")
        st.caption("Your session is not linked to an account.")
        if st.button("End guest session", type="secondary"):
            logout()

elif section == "Documents":
    st.markdown(
        """
        <div class="hero-eyebrow">YOUR KNOWLEDGE LIBRARY</div>
        <h1 style="margin:.55rem 0">Documents</h1>
        <p class="hero-copy" style="margin:0">Add trusted source material and ask questions grounded in your files.</p>
        """,
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        st.subheader("Add a document")
        file = st.file_uploader(
            "Choose a PDF, DOCX, or TXT file",
            type=["pdf", "docx", "txt"],
            key="library_upload",
        )
        description = st.text_input(
            "What should the assistant know about this file?",
            max_chars=300,
            key="library_description",
        )
        if st.button("Upload and index", type="primary", disabled=file is None):
            if not description.strip():
                st.error("Add a short description before uploading.")
            else:
                try:
                    with st.spinner(f"Processing {file.name}…"):
                        uploaded = upload_document(token, file, description.strip())
                    st.success(f"{uploaded['filename']} is ready.")
                    st.rerun()
                except ApiError as exc:
                    st.error(str(exc))
    st.subheader("Your documents")
    if uploaded_documents:
        for document in uploaded_documents:
            with st.container(border=True):
                doc_left, doc_right = st.columns([5, 1], vertical_alignment="center")
                with doc_left:
                    st.markdown(f"**▧  {document['filename']}**")
                    st.caption(document.get("description", "Ready to use in your workspace"))
                with doc_right:
                    st.markdown(f"`{document['status']}`")
    else:
        with st.container(border=True):
            st.caption("Your document library is empty. Upload a PDF, DOCX, or TXT to get started.")

elif section == "Chat History":
    st.markdown(
        """
        <div class="hero-eyebrow">YOUR CONVERSATIONS</div>
        <h1 style="margin:.55rem 0">Chat history</h1>
        <p class="hero-copy" style="margin:0">Pick up a thought, question, or research thread from where you left it.</p>
        """,
        unsafe_allow_html=True,
    )
    if conversations:
        for item in conversations:
            with st.container(border=True):
                item_col, date_col = st.columns([5, 1], vertical_alignment="center")
                with item_col:
                    st.markdown(f"**{item['title']}**")
                    st.caption(f"Updated {relative_date(item['updated_at'])}")
                with date_col:
                    if st.button("Open  →", key=f"history_open_{item['id']}"):
                        st.session_state["selected_conversation_id"] = item["id"]
                        st.session_state["workspace_section"] = "Chat"
                        st.rerun()
    else:
        st.info("No conversations yet. Start a new chat to begin.")

elif section == "Home" or (section == "Chat" and not conversation):
    if st.session_state.get("conversation_storage_error"):
        st.warning(
            "Anonymous workspace is open. Saving chats and documents needs MongoDB; "
            "configure MONGODB_URL in the project .env or start MongoDB to enable persistence."
        )
    if section == "Chat":
        st.markdown(
            '<div class="chat-heading"><div><div class="chat-heading-title">New conversation</div>'
            '<div class="chat-heading-subtitle">Private workspace · Ready when you are</div></div>'
            '<div class="status-pill">● Ready</div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="hero-panel">
              <div class="hero-eyebrow">YOUR PRIVATE AI WORKSPACE</div>
              <h1>Your knowledge. One conversation away.</h1>
              <p class="hero-copy">
                Bring your documents, research, and questions together. Get clear answers
                grounded in the information that matters to you.
              </p>
              <div style="margin-top:1.25rem"><span class="status-pill">✧ Anonymous session · Ready</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
        st.markdown('<div class="section-label">A GOOD PLACE TO START</div>', unsafe_allow_html=True)
        suggestions = [
            ("▤", "Understand a document", "Pull out the main ideas, claims, and evidence.", "Summarize the key ideas and evidence in my documents."),
            ("⌕", "Explore a question", "Research a topic and get a clear, useful overview.", "Research the key perspectives on a topic I am exploring."),
            ("✧", "Find the signal", "Turn dense material into a concise summary.", "Create a concise summary of the most important takeaways."),
            ("⌘", "Connect the dots", "Explore relationships across ideas and sources.", "What relationships connect the key ideas in my documents?"),
        ]
        suggestion_cols = st.columns(2)
        for index, (icon, title, subtitle, prompt_text) in enumerate(suggestions):
            with suggestion_cols[index % 2]:
                with st.container(border=True):
                    st.markdown(f"### {icon}  {title}")
                    st.caption(subtitle)
                    if st.button("Explore  →", key=f"suggestion_{index}", use_container_width=True):
                        st.session_state["selected_conversation_id"] = None
                        st.session_state["workspace_section"] = "Chat"
                        st.session_state["pending_query"] = prompt_text
                        st.rerun()

    if uploaded_documents:
        st.markdown('<div class="section-label">READY TO USE</div>', unsafe_allow_html=True)
        st.caption("  ·  ".join(document["filename"] for document in uploaded_documents[:4]))

    st.caption("Select a prompt or start a conversation below. The assistant answers with the configured LangGraph workflow.")

elif section == "Chat":
    title = conversation.get("title", "Conversation")
    updated = relative_date(conversation.get("updated_at", ""))
    st.markdown(
        f"""
        <div class="chat-heading">
          <div><div class="chat-heading-title">{title}</div>
          <div class="chat-heading-subtitle">Updated {updated} · Conversation history is saved to your account</div></div>
          <div class="status-pill">● Workspace ready</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    chat_messages = conversation.get("messages", [])
    if not chat_messages:
        st.markdown(
            """
            <div style="text-align:center;padding:4rem 1rem 2rem">
              <div class="brand-glyph" style="margin:auto">✦</div>
              <h2 style="margin-top:1.2rem">What would you like to explore?</h2>
              <p class="hero-copy">Ask naturally, or attach a PDF, DOCX, or TXT to add it to your personal library.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    if st.session_state.get("conversation_storage_error"):
        st.warning(
            "Chat history is temporarily unavailable because MongoDB is not reachable. "
            "Your guest workspace is open, but messages cannot be saved until MongoDB is configured."
        )
        prompt_suggestions = [
            "Summarize the key ideas in my documents",
            "Explain a complex topic step by step",
        ]
        prompt_cols = st.columns(2)
        for col, text in zip(prompt_cols, prompt_suggestions):
            with col:
                if st.button(text, key=f"chat_suggest_{text}", use_container_width=True):
                    st.session_state["pending_query"] = text
                    st.rerun()
    else:
        for message in chat_messages:
            role = "user" if message.get("type") in ("human", "user") else "assistant"
            with st.chat_message(role):
                st.markdown(message.get("content", ""))
                if role == "assistant":
                    route = message.get("route")
                    if route:
                        st.caption(f"Retrieved via · {route}")
                    for citation in message.get("citations", []):
                        label = citation.get("source", "Source")
                        page = citation.get("page")
                        display_page = page + 1 if isinstance(page, int) else page
                        st.caption(
                            f"Source · {label}"
                            + (f" · page {display_page}" if display_page is not None else "")
                        )

if st.session_state.get("query_error"):
    st.error(st.session_state["query_error"])
    if st.button("Retry response", type="primary"):
        submit_query(st.session_state.get("retry_query", ""))

composer = st.chat_input(
    "Message Adaptive RAG…",
    accept_file=True,
    file_type=["pdf", "docx", "txt"],
    max_upload_size=50,
)
pending_query = st.session_state.pop("pending_query", None)
if composer:
    files = getattr(composer, "files", [])
    text = getattr(composer, "text", "") if hasattr(composer, "text") else str(composer)
    if upload_files(files) and text.strip():
        submit_query(text)
    elif files:
        st.success("Document added to your library. Ask a question about it when you’re ready.")
elif pending_query:
    submit_query(pending_query)
