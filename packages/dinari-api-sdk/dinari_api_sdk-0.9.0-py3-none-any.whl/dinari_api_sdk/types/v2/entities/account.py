# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from ...._models import BaseModel
from .jurisdiction import Jurisdiction

__all__ = ["Account"]


class Account(BaseModel):
    """Information about an `Account` owned by an `Entity`."""

    id: str
    """Unique ID for the `Account`."""

    created_dt: datetime
    """Datetime when the `Account` was created. ISO 8601 timestamp."""

    entity_id: str
    """ID for the `Entity` that owns the `Account`."""

    is_active: bool
    """Indicates whether the `Account` is active."""

    jurisdiction: Jurisdiction
    """Jurisdiction of the `Account`."""

    brokerage_account_id: Optional[str] = None
    """ID of the brokerage account associated with the `Account`."""
