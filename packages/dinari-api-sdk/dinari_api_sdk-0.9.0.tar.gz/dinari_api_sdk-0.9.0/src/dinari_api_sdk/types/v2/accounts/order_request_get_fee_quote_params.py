# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, TypedDict

from ..chain import Chain
from .order_side import OrderSide
from .order_type import OrderType

__all__ = ["OrderRequestGetFeeQuoteParams"]


class OrderRequestGetFeeQuoteParams(TypedDict, total=False):
    order_side: Required[OrderSide]
    """Indicates whether `Order Request` is a buy or sell."""

    order_type: Required[OrderType]
    """Type of `Order Request`."""

    stock_id: Required[str]
    """The Stock ID associated with the Order Request"""

    asset_token_quantity: Optional[float]
    """Amount of dShare asset tokens involved.

    Required for limit `Order Requests` and market sell `Order Requests`. Must be a
    positive number with a precision of up to 4 decimal places for limit
    `Order Requests` or up to 6 decimal places for market sell `Order Requests`.
    """

    chain_id: Optional[Chain]
    """CAIP-2 chain ID of the blockchain where the `Order Request` will be placed.

    If not provided, the default chain ID (eip155:42161) will be used.
    """

    limit_price: Optional[float]
    """Price per asset in the asset's native currency.

    USD for US equities and ETFs. Required for limit `Order Requests`.
    """

    payment_token_address: Optional[str]
    """Address of the payment token to be used for an order.

    If not provided, the default payment token (USD+) will be used.
    """

    payment_token_quantity: Optional[float]
    """Amount of payment tokens involved. Required for market buy `Order Requests`."""
