# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, TypedDict

__all__ = ["OrderRequestCreateMarketBuyParams"]


class OrderRequestCreateMarketBuyParams(TypedDict, total=False):
    payment_amount: Required[float]
    """
    Amount of currency (USD for US equities and ETFs) to pay for the order. Must be
    a positive number with a precision of up to 2 decimal places.
    """

    stock_id: Required[str]
    """ID of `Stock`."""

    client_order_id: Optional[str]
    """Customer-supplied ID to map this order to an order in their own systems.

    Must be unique within the entity.
    """

    recipient_account_id: Optional[str]
    """ID of `Account` to receive the `Order`."""
