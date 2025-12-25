# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal

from ..._models import BaseModel
from .job_status import JobStatus
from ..error_info import ErrorInfo
from ..container_info import ContainerInfo

__all__ = ["VerifyStatusResponse", "Result"]


class Result(BaseModel):
    """Result from a test suite verifier."""

    execution_duration_seconds: float
    """Total execution time for the verification step."""

    failed: int
    """Number of tests that failed."""

    is_success: bool
    """Overall success status of the verification."""

    passed: int
    """Number of tests that passed."""

    skipped: int
    """Number of tests that were skipped."""

    total: int
    """Total number of tests executed."""

    failures: Optional[List[object]] = None
    """A list of failed tests with their details."""

    passes: Optional[List[object]] = None
    """A list of passing tests with their details."""

    skips: Optional[List[object]] = None
    """A list of skipped/ignored tests with their details."""

    stderr: Optional[str] = None
    """Standard error from the verifier."""

    stdout: Optional[str] = None
    """Standard output from the verifier."""

    tool: Optional[Literal["test_suite"]] = None


class VerifyStatusResponse(BaseModel):
    """Represents a single verification job, the core resource of the API."""

    created_at: datetime
    """Timestamp when the job was created (UTC)."""

    job_id: str
    """Unique identifier for the job."""

    sample_id: str
    """Identifier of the sample being used for verification."""

    session_id: str
    """Session identifier for this job."""

    status: JobStatus
    """Current status of the job."""

    completed_at: Optional[datetime] = None
    """Timestamp when the job completed (UTC)."""

    container_info: Optional[ContainerInfo] = None
    """Information about a container."""

    error: Optional[ErrorInfo] = None
    """Details about an error that occurred during job processing."""

    result: Optional[Result] = None
    """Result from a test suite verifier."""

    started_at: Optional[datetime] = None
    """Timestamp when the job processing started (UTC)."""
