# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import TypeAlias

from .._models import BaseModel

__all__ = ["DatasetListResponse", "DatasetListResponseItem"]


class DatasetListResponseItem(BaseModel):
    """Information about a dataset."""

    name: str
    """Unique name of the dataset."""

    sample_count: int
    """Number of samples in the dataset."""

    created_at: Optional[datetime] = None
    """Timestamp when the dataset was first created (UTC)."""

    description: Optional[str] = None
    """A brief description of the dataset."""


DatasetListResponse: TypeAlias = List[DatasetListResponseItem]
