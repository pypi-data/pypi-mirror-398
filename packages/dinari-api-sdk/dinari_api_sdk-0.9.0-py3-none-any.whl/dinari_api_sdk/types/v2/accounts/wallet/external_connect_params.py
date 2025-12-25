# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

from .wallet_chain_id import WalletChainID

__all__ = ["ExternalConnectParams"]


class ExternalConnectParams(TypedDict, total=False):
    chain_id: Required[WalletChainID]
    """CAIP-2 formatted chain ID of the blockchain the `Wallet` to link is on.

    eip155:0 is used for EOA wallets
    """

    nonce: Required[str]
    """Nonce contained within the connection message."""

    signature: Required[str]
    """Signature payload from signing the connection message with the `Wallet`."""

    wallet_address: Required[str]
    """Address of the `Wallet`."""
