# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from ....._models import BaseModel

__all__ = ["Eip155CreatePermitTransactionResponse"]


class Eip155CreatePermitTransactionResponse(BaseModel):
    abi: object
    """
    [JSON ABI](https://docs.soliditylang.org/en/v0.8.30/abi-spec.html#json) of the
    smart contract function encoded in the transaction. Provided for informational
    purposes.
    """

    args: object
    """Arguments to the smart contract function encoded in the transaction.

    Provided for informational purposes.
    """

    contract_address: str
    """Smart contract address that the transaction should call."""

    data: str
    """Hex-encoded function call."""

    value: str
    """Transaction value estimate in Wei."""
