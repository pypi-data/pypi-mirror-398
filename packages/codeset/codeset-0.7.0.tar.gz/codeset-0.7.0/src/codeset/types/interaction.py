# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from .._models import BaseModel

__all__ = ["Interaction"]


class Interaction(BaseModel):
    interaction_id: str
    """Unique identifier for the interaction."""

    session_id: str
    """Session identifier for this interaction."""

    created_at: datetime
    """Timestamp when the interaction was created (UTC)."""

    exit_code: Optional[int] = None
    """Exit code of the executed command (if completed)."""

    stdout: Optional[str] = None
    """Standard output from the command (if completed)."""

    stderr: Optional[str] = None
    """Standard error from the command (if completed)."""

    execution_time_seconds: Optional[float] = None
    """Execution time in seconds (if completed)."""

    success: Optional[bool] = None
    """Whether the command execution was successful (if completed)."""

    message: Optional[str] = None
    """Message describing the interaction status."""
