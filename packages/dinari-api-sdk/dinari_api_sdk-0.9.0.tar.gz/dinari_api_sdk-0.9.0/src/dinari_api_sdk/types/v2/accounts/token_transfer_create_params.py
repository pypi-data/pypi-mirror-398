# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["TokenTransferCreateParams"]


class TokenTransferCreateParams(TypedDict, total=False):
    quantity: Required[float]
    """Quantity of the token to transfer."""

    recipient_account_id: Required[str]
    """ID of the recipient account to which the tokens will be transferred."""

    token_address: Required[str]
    """Address of the token to transfer."""
