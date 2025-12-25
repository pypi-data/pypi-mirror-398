# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .._models import BaseModel

__all__ = ["HealthCheckResponse"]


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""

    service: str
    """Name of the service"""

    status: str
    """Health status of the service"""

    timestamp: str
    """Timestamp when the health check was performed (ISO format)"""

    version: str
    """Version of the service"""
