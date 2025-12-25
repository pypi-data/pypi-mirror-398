# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["WithdrawalRequestCreateParams"]


class WithdrawalRequestCreateParams(TypedDict, total=False):
    payment_token_quantity: Required[float]
    """Amount of USD+ payment tokens to be withdrawn.

    Must be greater than 0 and have at most 6 decimal places.
    """

    recipient_account_id: Required[str]
    """ID of the `Account` that will receive payment tokens from the `Withdrawal`."""
