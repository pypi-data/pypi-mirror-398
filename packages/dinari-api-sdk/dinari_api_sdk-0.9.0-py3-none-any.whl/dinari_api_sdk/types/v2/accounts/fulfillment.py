# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from ..chain import Chain
from ...._models import BaseModel

__all__ = ["Fulfillment"]


class Fulfillment(BaseModel):
    """Information about a fulfillment of an `Order`.

    An order may be fulfilled in multiple transactions.
    """

    id: str
    """ID of the `OrderFulfillment`."""

    asset_token_filled: float
    """Amount of dShare asset token filled for `BUY` orders."""

    asset_token_spent: float
    """Amount of dShare asset token spent for `SELL` orders."""

    chain_id: Chain
    """Blockchain that the transaction was run on."""

    order_id: str
    """ID of the `Order` this `OrderFulfillment` is for."""

    payment_token_filled: float
    """Amount of payment token filled for `SELL` orders."""

    payment_token_spent: float
    """Amount of payment token spent for `BUY` orders."""

    transaction_dt: datetime
    """Time when transaction occurred."""

    transaction_hash: str
    """Transaction hash for this fulfillment."""

    payment_token_fee: Optional[float] = None
    """Fee amount, in payment tokens."""
