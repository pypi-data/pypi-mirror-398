# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import TypeAlias

from ...._models import BaseModel

__all__ = ["StockRetrieveHistoricalPricesResponse", "StockRetrieveHistoricalPricesResponseItem"]


class StockRetrieveHistoricalPricesResponseItem(BaseModel):
    """Datapoint of historical price data for a `Stock`."""

    close: float
    """Close price from the given time period."""

    high: float
    """Highest price from the given time period."""

    low: float
    """Lowest price from the given time period."""

    open: float
    """Open price from the given time period."""

    timestamp: int
    """The UNIX timestamp in seconds for the start of the aggregate window."""


StockRetrieveHistoricalPricesResponse: TypeAlias = List[StockRetrieveHistoricalPricesResponseItem]
