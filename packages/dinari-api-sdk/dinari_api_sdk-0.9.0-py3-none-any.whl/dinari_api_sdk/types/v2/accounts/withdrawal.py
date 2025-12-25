# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from datetime import datetime

from ..chain import Chain
from ...._models import BaseModel
from .brokerage_order_status import BrokerageOrderStatus

__all__ = ["Withdrawal"]


class Withdrawal(BaseModel):
    """
    Information for a withdrawal of payment tokens from an `Account` backed by a Dinari-managed `Wallet`.
    """

    id: str
    """ID of the `Withdrawal`."""

    account_id: str
    """ID of the `Account` from which the `Withdrawal` is made."""

    chain_id: Chain
    """CAIP-2 chain ID of the blockchain where the `Withdrawal` is made."""

    payment_token_address: str
    """Address of USDC payment token that the `Withdrawal` will be received in."""

    payment_token_amount: float
    """Amount of USDC payment tokens to be withdrawn."""

    recipient_account_id: str
    """ID of the `Account` that will receive payment tokens from the `Withdrawal`.

    This `Account` must be connected to a non-managed `Wallet` and belong to the
    same `Entity`.
    """

    status: BrokerageOrderStatus
    """Status of the `Withdrawal`."""

    transaction_dt: datetime
    """Datetime at which the `Withdrawal` was transacted. ISO 8601 timestamp."""

    transaction_hash: str
    """Hash of the transaction for the `Withdrawal`."""

    withdrawal_request_id: str
    """ID of the `WithdrawalRequest` associated with this `Withdrawal`."""
