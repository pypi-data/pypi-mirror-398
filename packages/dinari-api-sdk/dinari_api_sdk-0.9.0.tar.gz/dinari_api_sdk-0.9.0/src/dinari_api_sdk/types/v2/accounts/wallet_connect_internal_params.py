# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, TypedDict

from .wallet.wallet_chain_id import WalletChainID

__all__ = ["WalletConnectInternalParams"]


class WalletConnectInternalParams(TypedDict, total=False):
    chain_id: Required[WalletChainID]
    """CAIP-2 formatted chain ID of the blockchain the `Wallet` to link is on.

    eip155:0 is used for EOA wallets
    """

    wallet_address: Required[str]
    """Address of the `Wallet`."""

    is_shared: Optional[bool]
    """Is the linked Wallet shared or not"""
