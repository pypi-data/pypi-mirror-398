# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

from .chain import Chain

__all__ = ["AccountMintSandboxTokensParams"]


class AccountMintSandboxTokensParams(TypedDict, total=False):
    chain_id: Optional[Chain]
    """CAIP-2 chain ID of blockchain in which to mint the sandbox payment tokens.

    If none specified, defaults to eip155:421614. If the `Account` is linked to a
    Dinari-managed `Wallet`, only eip155:42161 is allowed.
    """
