# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

from .wallet_chain_id import WalletChainID

__all__ = ["ExternalGetNonceParams"]


class ExternalGetNonceParams(TypedDict, total=False):
    chain_id: Required[WalletChainID]
    """CAIP-2 formatted chain ID of the blockchain the `Wallet` is on.

    eip155:0 is used for EOA wallets
    """

    wallet_address: Required[str]
    """Address of the `Wallet` to connect."""
