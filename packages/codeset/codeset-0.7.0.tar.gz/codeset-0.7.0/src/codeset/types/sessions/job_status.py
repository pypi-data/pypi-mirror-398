# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal, TypeAlias

__all__ = ["JobStatus"]

JobStatus: TypeAlias = Literal["pending", "starting", "running", "completed", "error", "cancelled"]
