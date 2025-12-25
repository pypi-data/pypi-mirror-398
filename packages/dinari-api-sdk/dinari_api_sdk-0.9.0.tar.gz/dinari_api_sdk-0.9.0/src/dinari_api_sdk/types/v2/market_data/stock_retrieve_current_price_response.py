# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from ...._models import BaseModel

__all__ = ["StockRetrieveCurrentPriceResponse"]


class StockRetrieveCurrentPriceResponse(BaseModel):
    price: float
    """The ask price."""

    stock_id: str
    """ID of the `Stock`"""

    timestamp: datetime
    """When the Stock Quote was generated."""

    change: Optional[float] = None
    """The change in price from the previous close."""

    change_percent: Optional[float] = None
    """The percentage change in price from the previous close."""

    close: Optional[float] = None
    """The close price from the given time period."""

    high: Optional[float] = None
    """The highest price from the given time period"""

    low: Optional[float] = None
    """The lowest price from the given time period."""

    market_cap: Optional[int] = None
    """
    The most recent close price of the ticker multiplied by weighted outstanding
    shares.
    """

    open: Optional[float] = None
    """The open price from the given time period."""

    previous_close: Optional[float] = None
    """The close price for the `Stock` from the previous trading session."""

    volume: Optional[float] = None
    """The trading volume from the given time period."""

    weighted_shares_outstanding: Optional[int] = None
    """The number of shares outstanding in the given time period."""
