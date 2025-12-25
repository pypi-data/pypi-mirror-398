# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from ....._models import BaseModel

__all__ = ["ExternalGetNonceResponse"]


class ExternalGetNonceResponse(BaseModel):
    """Connection message to sign to prove ownership of the `Wallet`."""

    message: str
    """Message to be signed by the `Wallet`"""

    nonce: str
    """Single-use identifier"""
