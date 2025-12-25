# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from ..._models import BaseModel

__all__ = ["MarketDataRetrieveMarketHoursResponse"]


class MarketDataRetrieveMarketHoursResponse(BaseModel):
    is_market_open: bool
    """Whether or not the market is open"""

    next_session_close_dt: datetime
    """Datetime at which the next session closes. ISO 8601 timestamp."""

    next_session_open_dt: datetime
    """Datetime at which the next session opens. ISO 8601 timestamp."""

    current_session_after_hours_close_time_dt: Optional[datetime] = None
    """Time at which the current session after-hours end."""

    current_session_close_dt: Optional[datetime] = None
    """Datetime at which the current session closes.

    `null` if the market is currently closed. ISO 8601 timestamp.
    """

    current_session_open_dt: Optional[datetime] = None
    """Datetime at which the current session opened.

    `null` if the market is currently closed. ISO 8601 timestamp.
    """

    current_session_overnight_open_time_dt: Optional[datetime] = None
    """Time at which the current session overnight starts."""

    current_session_pre_market_open_time_dt: Optional[datetime] = None
    """Time at which the current session pre-market hours start."""

    next_session_after_hours_close_time_dt: Optional[datetime] = None
    """Time at which the next session after-hours end."""

    next_session_overnight_open_time_dt: Optional[datetime] = None
    """Time at which the next session overnight starts."""

    next_session_pre_market_open_time_dt: Optional[datetime] = None
    """Time at which the next session pre-market hours start."""
