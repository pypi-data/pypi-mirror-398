# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["SampleListResponse", "Sample"]


class Sample(BaseModel):
    """Information about a software engineering task sample."""

    base_commit: str
    """Base commit hash for the sample."""

    environment_setup_commit: str
    """Environment setup commit hash for the sample."""

    fail_to_fail: List[str]
    """List of test names that remained FAIL to FAIL."""

    fail_to_pass: List[str]
    """List of test names that changed from FAIL to PASS."""

    hints_text: str
    """Hints text for the sample (concatenated issue comments)."""

    instance_id: str
    """Instance identifier for the sample (e.g., 'psf\\__\\__requests-1234')."""

    language: str
    """Primary programming language of the sample."""

    non_code_patch: str
    """Non-code patch for the sample."""

    pass_to_pass: List[str]
    """List of test names that remained PASS to PASS."""

    patch: str
    """Code patch (diff) that fixes the bug for the sample."""

    problem_statement: str
    """Problem statement for the sample (issue title + body)."""

    repo: str
    """Repository full name for the sample (e.g., 'psf/requests')."""

    sample_id: str
    """Unique identifier for the sample (e.g., 'traccar-1')."""

    test_patch: str
    """Test patch (diff) for the sample."""

    verifier: Literal["test_suite", "static_analysis", "linter", "custom"]
    """The type of verifier used for this sample."""

    created_at: Optional[datetime] = None
    """Timestamp when the sample was created (UTC)."""

    dataset: Optional[str] = None
    """Dataset name for the sample."""

    description: Optional[str] = None
    """A brief description of the sample."""

    latest: Optional[bool] = None
    """Whether this is the latest version."""

    version: Optional[int] = None
    """Version number of the sample."""

    version_description: Optional[str] = None
    """Description of this version."""


class SampleListResponse(BaseModel):
    """Response for listing samples with pagination."""

    has_more: bool
    """Indicates if more pages of results are available."""

    page: int
    """Current page number (1-based)."""

    page_size: int
    """Number of samples per page."""

    samples: List[Sample]
    """List of samples for the current page."""

    total_count: int
    """Total number of samples available."""
