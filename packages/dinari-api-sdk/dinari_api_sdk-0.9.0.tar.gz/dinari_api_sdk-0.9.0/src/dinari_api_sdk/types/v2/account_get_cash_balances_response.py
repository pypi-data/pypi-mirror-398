# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import TypeAlias

from .chain import Chain
from ..._models import BaseModel

__all__ = ["AccountGetCashBalancesResponse", "AccountGetCashBalancesResponseItem"]


class AccountGetCashBalancesResponseItem(BaseModel):
    """Balance of a payment token in an `Account`."""

    amount: float
    """Total amount of the payment token in the `Account`."""

    chain_id: Chain
    """CAIP-2 chain ID of the payment token."""

    symbol: str
    """Symbol of the payment token."""

    token_address: str
    """Address of the payment token."""


AccountGetCashBalancesResponse: TypeAlias = List[AccountGetCashBalancesResponseItem]
