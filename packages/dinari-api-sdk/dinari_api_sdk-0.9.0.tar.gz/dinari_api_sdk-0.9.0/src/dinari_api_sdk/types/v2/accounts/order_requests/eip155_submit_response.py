# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from ..order_tif import OrderTif
from ....._models import BaseModel
from ..order_side import OrderSide
from ..order_type import OrderType
from ..order_request_status import OrderRequestStatus

__all__ = ["Eip155SubmitResponse"]


class Eip155SubmitResponse(BaseModel):
    """A request to create an `Order`.

    An `EIP155OrderRequest` is created when a user places an order through the Dinari API.
    The `EIP155OrderRequest` is then fulfilled by creating an `Order` on-chain.

    The `EIP155OrderRequest` is a record of the user's intent to place an order, while the `Order` is the actual transaction that occurs on the blockchain.
    """

    id: str
    """ID of `EIP155OrderRequest`.

    This is the primary identifier for the `/order_requests` routes.
    """

    account_id: str
    """ID of `Account` placing the `EIP155OrderRequest`."""

    created_dt: datetime
    """Datetime at which the `EIP155OrderRequest` was created. ISO 8601 timestamp."""

    order_side: OrderSide
    """Indicates whether `Order` is a buy or sell."""

    order_tif: OrderTif
    """Indicates how long `Order` is valid for."""

    order_type: OrderType
    """Type of `Order`."""

    status: OrderRequestStatus
    """Status of `EIP155OrderRequest`. Possible values:

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

    order_id: Optional[str] = None
    """ID of `Order` created from the `EIP155OrderRequest`.

    This is the primary identifier for the `/orders` routes.
    """

    recipient_account_id: Optional[str] = None
    """ID of recipient `Account`."""
