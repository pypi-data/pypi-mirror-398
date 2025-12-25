# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .._models import BaseModel

__all__ = ["SessionStrReplaceResponse"]


class SessionStrReplaceResponse(BaseModel):
    """Response for string replacement operation."""

    message: str
    """Details about the string replacement operation."""

    success: bool
    """Whether the string replacement was successful."""
