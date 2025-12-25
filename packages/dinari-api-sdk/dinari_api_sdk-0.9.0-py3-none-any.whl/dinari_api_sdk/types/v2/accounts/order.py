# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from ..chain import Chain
from .order_tif import OrderTif
from ...._models import BaseModel
from .order_side import OrderSide
from .order_type import OrderType
from .brokerage_order_status import BrokerageOrderStatus

__all__ = ["Order"]


class Order(BaseModel):
    id: str
    """ID of the `Order`."""

    chain_id: Chain
    """
    CAIP-2 formatted chain ID of the blockchain that the `Order` transaction was run
    on.
    """

    created_dt: datetime
    """Datetime at which the `Order` was created. ISO 8601 timestamp."""

    order_contract_address: str
    """Smart contract address that `Order` was created from."""

    order_side: OrderSide
    """Indicates whether `Order` is a buy or sell."""

    order_tif: OrderTif
    """Time in force. Indicates how long `Order` is valid for."""

    order_transaction_hash: str
    """Transaction hash for the `Order` creation."""

    order_type: OrderType
    """Type of `Order`."""

    payment_token: str
    """The payment token (stablecoin) address."""

    status: BrokerageOrderStatus
    """Status of the `Order`."""

    stock_id: str
    """The `Stock` ID associated with the `Order`"""

    asset_token: Optional[str] = None
    """The dShare asset token address."""

    asset_token_quantity: Optional[float] = None
    """Total amount of assets involved."""

    cancel_transaction_hash: Optional[str] = None
    """Transaction hash for cancellation of `Order`, if the `Order` was cancelled."""

    client_order_id: Optional[str] = None
    """
    Customer-supplied unique identifier to map this `Order` to an order in the
    customer's systems.
    """

    fee: Optional[float] = None
    """Fee amount associated with `Order`."""

    limit_price: Optional[float] = None
    """
    For limit `Orders`, the price per asset, specified in the `Stock`'s native
    currency (USD for US equities and ETFs).
    """

    order_request_id: Optional[str] = None
    """Order Request ID for the `Order`"""

    payment_token_quantity: Optional[float] = None
    """Total amount of payment involved."""
