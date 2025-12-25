# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from datetime import datetime

from ...._models import BaseModel

__all__ = ["KYCCreateManagedCheckResponse"]


class KYCCreateManagedCheckResponse(BaseModel):
    """URL for a managed KYC flow for an `Entity`."""

    embed_url: str
    """URL of a managed KYC flow interface for the `Entity`."""

    expiration_dt: datetime
    """Datetime at which the KYC request will expired. ISO 8601 timestamp."""
