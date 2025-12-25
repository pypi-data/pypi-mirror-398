# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from ..._models import BaseModel

__all__ = ["Entity"]


class Entity(BaseModel):
    """
    Information about an `Entity`, which can be either an individual or an organization.
    """

    id: str
    """Unique ID of the `Entity`."""

    entity_type: Literal["INDIVIDUAL", "ORGANIZATION"]
    """Type of `Entity`.

    `ORGANIZATION` for Dinari Partners and `INDIVIDUAL` for their individual
    customers.
    """

    is_kyc_complete: bool
    """Indicates if `Entity` completed KYC."""

    name: Optional[str] = None
    """Name of `Entity`."""

    nationality: Optional[str] = None
    """Nationality or home country of the `Entity`."""

    reference_id: Optional[str] = None
    """Case sensitive unique reference ID that you can set for the `Entity`.

    We recommend setting this to the unique ID of the `Entity` in your system.
    """
