# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from datetime import date
from typing_extensions import TypeAlias

from ..._models import BaseModel

__all__ = ["AccountGetDividendPaymentsResponse", "AccountGetDividendPaymentsResponseItem"]


class AccountGetDividendPaymentsResponseItem(BaseModel):
    """Represents a dividend payment event for an `Account`."""

    amount: float
    """Amount of the dividend paid."""

    currency: str
    """Currency in which the dividend was paid. (e.g. USD)"""

    payment_date: date
    """Date the dividend was distributed to the account. ISO 8601 format, YYYY-MM-DD."""

    stock_id: str
    """ID of the `Stock` for which the dividend was paid."""


AccountGetDividendPaymentsResponse: TypeAlias = List[AccountGetDividendPaymentsResponseItem]
