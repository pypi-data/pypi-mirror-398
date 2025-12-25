# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from .session import Session
from .._models import BaseModel

__all__ = ["SessionListResponse"]


class SessionListResponse(BaseModel):
    """Response for listing sessions."""

    has_more: bool
    """Indicates if more pages of results are available."""

    sessions: List[Session]

    total_count: int
    """Total number of sessions returned."""
