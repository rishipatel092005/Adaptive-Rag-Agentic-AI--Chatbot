"""
Route identifier model.
"""

from pydantic import BaseModel


class RouteIdentifier(BaseModel):
    """Model for routing queries to appropriate nodes."""

    route: str
