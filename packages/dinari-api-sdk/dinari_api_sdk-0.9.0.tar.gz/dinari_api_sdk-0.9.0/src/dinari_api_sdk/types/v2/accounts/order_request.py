# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from .order_tif import OrderTif
from ...._models import BaseModel
from .order_side import OrderSide
from .order_type import OrderType
from .order_request_status import OrderRequestStatus

__all__ = ["OrderRequest"]


class OrderRequest(BaseModel):
    """A request to create an `Order`.

    An `OrderRequest` is created when a user places an order through the Dinari API.
    The `OrderRequest` is then fulfilled by creating an `Order` on-chain.

    The `OrderRequest` is a record of the user's intent to place an order, while the `Order` is the actual transaction that occurs on the blockchain.
    """

    id: str
    """ID of `OrderRequest`.

    This is the primary identifier for the `/order_requests` routes.
    """

    account_id: str
    """ID of `Account` placing the `OrderRequest`."""

    created_dt: datetime
    """Datetime at which the `OrderRequest` was created. ISO 8601 timestamp."""

    order_side: OrderSide
    """Indicates whether `Order` is a buy or sell."""

    order_tif: OrderTif
    """Indicates how long `Order` is valid for."""

    order_type: OrderType
    """Type of `Order`."""

    status: OrderRequestStatus
    """Status of `OrderRequest`. Possible values:

    - `QUOTED`: Order request created with fee quote provided, ready for processing
    - `PENDING`: Order request is being prepared for submission
    - `PENDING_BRIDGE`: Order is waiting for bridge transaction to complete
    - `SUBMITTED`: Order has been successfully submitted to the order book
    - `ERROR`: An error occurred during order processing
    - `CANCELLED`: Order request was cancelled
    - `EXPIRED`: Order request expired due to deadline passing
    """

    cancel_message: Optional[str] = None
    """Reason for the order cancellation if the order status is CANCELLED"""

    client_order_id: Optional[str] = None
    """
    Customer-supplied ID to map this `OrderRequest` to an order in their own
    systems.
    """

    order_id: Optional[str] = None
    """ID of `Order` created from the `OrderRequest`.

    This is the primary identifier for the `/orders` routes.
    """

    recipient_account_id: Optional[str] = None
    """ID of recipient `Account`."""
