"""Request models for persisted conversations."""

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    title: str = Field(default="New chat", min_length=1, max_length=120)


class ConversationRename(BaseModel):
    title: str = Field(min_length=1, max_length=120)


class ChatQuery(BaseModel):
    conversation_id: str = Field(min_length=1, max_length=64)
    query: str = Field(min_length=1, max_length=20000)
