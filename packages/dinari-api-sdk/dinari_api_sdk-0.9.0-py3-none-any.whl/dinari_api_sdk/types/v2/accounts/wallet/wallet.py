# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from ....._models import BaseModel
from .wallet_chain_id import WalletChainID

__all__ = ["Wallet"]


class Wallet(BaseModel):
    """Information about a blockchain `Wallet`."""

    address: str
    """Address of the `Wallet`."""

    chain_id: WalletChainID
    """CAIP-2 formatted chain ID of the blockchain the `Wallet` is on.

    eip155:0 is used for EOA wallets
    """

    is_aml_flagged: bool
    """Indicates whether the `Wallet` is flagged for AML violation."""

    is_managed_wallet: bool
    """Indicates whether the `Wallet` is a Dinari-managed wallet."""
