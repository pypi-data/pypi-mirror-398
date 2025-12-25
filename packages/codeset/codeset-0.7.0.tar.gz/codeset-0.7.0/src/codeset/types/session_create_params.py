# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["SessionCreateParams"]


class SessionCreateParams(TypedDict, total=False):
    dataset: Required[str]
    """Dataset name for the sample."""

    sample_id: Required[str]
    """Identifier of the sample to use for this session."""

    ttl_minutes: int
    """Time to live for the session in minutes (default: 30)."""
