# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict

from ....._models import BaseModel

__all__ = ["Eip155CreatePermitResponse"]


class Eip155CreatePermitResponse(BaseModel):
    """Token permit to be signed by the smart contract submitter."""

    order_request_id: str
    """ID representing the EIP155 `OrderRequest`"""

    permit: Dict[str, None]
    """
    Token permit that is to be signed by smart contract submitter for authorizing
    token transfer for the `OrderRequest`
    """
