# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from ..chain import Chain
from ...._models import BaseModel

__all__ = ["TokenTransfer"]


class TokenTransfer(BaseModel):
    """Information about a token transfer between accounts."""

    id: str
    """ID of the token transfer."""

    chain_id: Chain
    """CAIP-2 chain ID of the blockchain that the transfer is made on."""

    created_dt: datetime
    """Datetime at which the transfer was created. ISO 8601 timestamp."""

    quantity: float
    """Quantity of the token being transferred."""

    recipient_account_id: str
    """ID of the account to which the tokens are transferred."""

    sender_account_id: str
    """ID of the account from which the tokens are transferred."""

    status: Literal["PENDING", "IN_PROGRESS", "COMPLETE", "FAILED"]
    """Status of the token transfer."""

    token_address: str
    """Address of the token being transferred."""

    updated_dt: datetime
    """Datetime at which the transfer was last updated. ISO 8601 timestamp."""

    transaction_hash: Optional[str] = None
    """Transaction hash of the transfer on the blockchain, if applicable.

    This is only present if the transfer has been executed on-chain.
    """
