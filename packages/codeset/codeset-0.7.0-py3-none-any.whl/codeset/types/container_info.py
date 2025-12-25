# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from datetime import datetime

from .._models import BaseModel

__all__ = ["ContainerInfo"]


class ContainerInfo(BaseModel):
    """Information about a container."""

    container_name: str
    """Name of the Cloud Run service."""

    created_at: datetime
    """Timestamp when the container was created (UTC)."""

    expires_at: datetime
    """Timestamp when the container will expire (UTC)."""

    location: str
    """Cloud Run region where the container is deployed (e.g., 'europe-west1')."""

    sample_id: str
    """Sample ID of the container."""

    service_url: str
    """URL of the Cloud Run service."""

    status: str
    """Status of the container."""
