# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from .._models import BaseModel
from .error_info import ErrorInfo
from .container_info import ContainerInfo
from .session_status import SessionStatus

__all__ = ["Session"]


class Session(BaseModel):
    """Represents a session for multi-turn interactions."""

    dataset: str
    """Dataset name for the sample."""

    expires_at: datetime
    """Timestamp when the session will expire (UTC)."""

    requested_at: datetime
    """Timestamp when the session was requested (UTC)."""

    sample_id: str
    """Identifier of the sample being used for the session."""

    session_id: str
    """Unique identifier for the session."""

    status: SessionStatus
    """Current status of the session."""

    user_id: str
    """User ID who owns this session."""

    container_info: Optional[ContainerInfo] = None
    """Information about a container."""

    created_at: Optional[datetime] = None
    """Timestamp when the container became ready and billing started (UTC)."""

    duration_seconds: Optional[float] = None
    """Duration of the session in seconds."""

    error: Optional[ErrorInfo] = None
    """Details about an error that occurred during job processing."""
