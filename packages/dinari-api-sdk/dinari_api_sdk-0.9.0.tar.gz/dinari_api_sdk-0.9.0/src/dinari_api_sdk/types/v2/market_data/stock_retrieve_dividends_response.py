# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import date
from typing_extensions import TypeAlias

from ...._models import BaseModel

__all__ = ["StockRetrieveDividendsResponse", "StockRetrieveDividendsResponseItem"]


class StockRetrieveDividendsResponseItem(BaseModel):
    """Information about a dividend announcement for a `Stock`."""

    cash_amount: Optional[float] = None
    """Cash amount of the dividend per share owned."""

    currency: Optional[str] = None
    """Currency in which the dividend is paid."""

    dividend_type: Optional[str] = None
    """Type of dividend.

    Dividends that have been paid and/or are expected to be paid on consistent
    schedules are denoted as `CD`. Special Cash dividends that have been paid that
    are infrequent or unusual, and/or can not be expected to occur in the future are
    denoted as `SC`.
    """

    ex_dividend_date: Optional[date] = None
    """
    Date on or after which a `Stock` is traded without the right to receive the next
    dividend payment. If you purchase a `Stock` on or after the ex-dividend date,
    you will not receive the upcoming dividend. In ISO 8601 format, YYYY-MM-DD.
    """

    pay_date: Optional[date] = None
    """Date on which the dividend is paid out. In ISO 8601 format, YYYY-MM-DD."""

    record_date: Optional[date] = None
    """Date that the shares must be held to receive the dividend; set by the company.

    In ISO 8601 format, YYYY-MM-DD.
    """

    ticker: Optional[str] = None
    """Ticker symbol of the `Stock`."""


StockRetrieveDividendsResponse: TypeAlias = List[StockRetrieveDividendsResponseItem]
