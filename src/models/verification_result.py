"""
Verification result model.
"""

from pydantic import BaseModel, Field


class VerificationResult(BaseModel):
    """Model for verifying answer faithfulness."""

    faithful: bool = Field(
        description="True if answer is supported by the context."
    )
    explanation: str = Field(
        description="Brief reasoning."
    )
