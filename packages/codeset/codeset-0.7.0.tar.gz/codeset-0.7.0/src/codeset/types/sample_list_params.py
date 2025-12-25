# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["SampleListParams"]


class SampleListParams(TypedDict, total=False):
    dataset: Optional[str]
    """Filter samples by dataset name"""

    page: Optional[int]
    """Page number (1-based). If not provided, returns all samples"""

    page_size: Optional[int]
    """Number of samples per page (max 100). If not provided, returns all samples"""

    search: Optional[str]
    """Search for samples by instance_id"""
