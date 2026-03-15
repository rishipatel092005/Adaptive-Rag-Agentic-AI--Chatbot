"""
In-memory chat history storage.
"""

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory


class ChatInMemoryHistory:
    """In-memory chat history storage."""

    store = {}

    @classmethod
    def get_session_history(
        cls,
        session_id: str,
        config: dict = None
    ) -> BaseChatMessageHistory:
        """
        Get or create chat history for a session.

        Args:
            session_id: Unique session identifier.
            config: Optional configuration dictionary.

        Returns:
            ChatMessageHistory instance for the session.
        """
        if session_id not in cls.store:
            cls.store[session_id] = ChatMessageHistory()
        return cls.store[session_id]

    @classmethod
    def clear_history(cls, session_id: str):
        """
        Clear chat history for a session.

        Args:
            session_id: Unique session identifier.
        """
        if session_id in cls.store:
            del cls.store[session_id]
