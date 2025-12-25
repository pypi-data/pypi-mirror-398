# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["SessionExecuteCommandParams"]


class SessionExecuteCommandParams(TypedDict, total=False):
    command: Required[str]
    """The bash command to execute."""

    command_timeout: int
    """Timeout for command execution in seconds (default: 300)."""
