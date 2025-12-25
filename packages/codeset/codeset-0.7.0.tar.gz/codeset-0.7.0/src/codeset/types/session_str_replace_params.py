# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["SessionStrReplaceParams"]


class SessionStrReplaceParams(TypedDict, total=False):
    file_path: Required[str]
    """Path to the file where replacement should be performed."""

    str_to_insert: Required[str]
    """String to insert as replacement."""

    str_to_replace: Required[str]
    """String to be replaced."""
