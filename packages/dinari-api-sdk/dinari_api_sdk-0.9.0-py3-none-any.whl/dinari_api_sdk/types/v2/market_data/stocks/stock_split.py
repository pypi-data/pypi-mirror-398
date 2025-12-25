# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from datetime import date
from typing_extensions import Literal

from ....._models import BaseModel

__all__ = ["StockSplit"]


class StockSplit(BaseModel):
    """
    Information about a stock split, including the `Stock` ID, the number of shares before and after the split, the record date, payable date, ex-date, and the status of the split.
    """

    id: str
    """ID of the `StockSplit`"""

    ex_date: date
    """Ex-date of the split in Eastern Time Zone.

    First day the stock trades at post-split prices. Typically is last date in the
    process, and the main important date for investors. In ISO 8601 format,
    YYYY-MM-DD.
    """

    payable_date: date
    """Payable date of the split in Eastern Time Zone.

    This is the date when company will send out the new shares. Mainly for record
    keeping by brokerages, who forward the shares to eventual owners. Typically is
    the second date in the process. In ISO 8601 format, YYYY-MM-DD.
    """

    record_date: date
    """
    Record date of the split in Eastern Time Zone, for company to determine where to
    send their new shares. Mainly for record keeping by brokerages, who forward the
    shares to eventual owners. Typically is the first date in the process. In ISO
    8601 format, YYYY-MM-DD.
    """

    split_from: float
    """The number of shares before the split. In a 10-for-1 split, this would be 1."""

    split_to: float
    """The number of shares after the split. In a 10-for-1 split, this would be 10."""

    status: Literal["PENDING", "IN_PROGRESS", "COMPLETE"]
    """The status of Dinari's processing of the `StockSplit`.

    `Stocks` for which this status is `IN_PROGRESS` will not be available for
    trading.
    """

    stock_id: str
    """ID of the `Stock` whose shares are being split."""
