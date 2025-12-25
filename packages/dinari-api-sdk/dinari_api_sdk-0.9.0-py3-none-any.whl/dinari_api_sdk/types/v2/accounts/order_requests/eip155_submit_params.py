# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["Eip155SubmitParams"]


class Eip155SubmitParams(TypedDict, total=False):
    order_request_id: Required[str]
    """ID of the prepared proxied order to be submitted as a proxied order."""

    permit_signature: Required[str]
    """
    Signature of the permit typed data, allowing Dinari to spend the payment token
    or dShare asset token on behalf of the owner.
    """
