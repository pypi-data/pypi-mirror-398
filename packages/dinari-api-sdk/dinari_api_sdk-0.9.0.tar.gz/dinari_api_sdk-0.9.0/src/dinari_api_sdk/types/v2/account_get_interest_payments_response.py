# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from datetime import date
from typing_extensions import TypeAlias

from ..._models import BaseModel

__all__ = ["AccountGetInterestPaymentsResponse", "AccountGetInterestPaymentsResponseItem"]


class AccountGetInterestPaymentsResponseItem(BaseModel):
    """An object representing an interest payment from stablecoin holdings."""

    amount: float
    """Amount of interest paid."""

    currency: str
    """Currency in which the interest was paid (e.g. USD)."""

    payment_date: date
    """Date of interest payment in US Eastern time zone. ISO 8601 format, YYYY-MM-DD."""


AccountGetInterestPaymentsResponse: TypeAlias = List[AccountGetInterestPaymentsResponseItem]
