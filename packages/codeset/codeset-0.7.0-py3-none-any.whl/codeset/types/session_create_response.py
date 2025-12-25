# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from datetime import datetime

from .._models import BaseModel
from .session_status import SessionStatus

__all__ = ["SessionCreateResponse"]


class SessionCreateResponse(BaseModel):
    """Response for creating a session."""

    expires_at: datetime
    """Timestamp when the session will expire (UTC)."""

    session_id: str
    """Unique identifier for the created session."""

    status: SessionStatus
    """Initial status of the session."""
