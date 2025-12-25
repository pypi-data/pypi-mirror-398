# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from datetime import datetime

from ...._models import BaseModel

__all__ = ["StockRetrieveCurrentQuoteResponse"]


class StockRetrieveCurrentQuoteResponse(BaseModel):
    ask_price: float
    """The ask price."""

    ask_size: float
    """The ask size."""

    bid_price: float
    """The bid price."""

    bid_size: float
    """The bid size."""

    stock_id: str
    """ID of the `Stock`"""

    timestamp: datetime
    """When the Stock Quote was generated."""
