# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from datetime import datetime

from ..._models import BaseModel
from .job_status import JobStatus

__all__ = ["VerifyStartResponse"]


class VerifyStartResponse(BaseModel):
    """Response for starting verification (async)."""

    job_id: str
    """Unique identifier for the verification job."""

    started_at: datetime
    """Timestamp when verification started (UTC)."""

    status: JobStatus
    """Initial status of the verification job."""
