# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

__all__ = ["StockRetrieveHistoricalPricesParams"]


class StockRetrieveHistoricalPricesParams(TypedDict, total=False):
    timespan: Required[Literal["DAY", "WEEK", "MONTH", "YEAR"]]
    """The timespan of the historical prices to query."""
