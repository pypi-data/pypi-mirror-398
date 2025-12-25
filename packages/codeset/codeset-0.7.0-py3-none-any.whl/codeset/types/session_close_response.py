# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .._models import BaseModel

__all__ = ["SessionCloseResponse"]


class SessionCloseResponse(BaseModel):
    """Response model for session deletion."""

    duration_seconds: float
    """Duration of the session in seconds."""

    message: str
    """Success message confirming session deletion"""
