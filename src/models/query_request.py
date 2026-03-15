"""
Query request model.
"""

from pydantic import BaseModel


class QueryRequest(BaseModel):
    """Request model for RAG queries."""

    query: str
    session_id: str