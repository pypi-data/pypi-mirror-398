# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal, TypeAlias

__all__ = ["OrderRequestStatus"]

OrderRequestStatus: TypeAlias = Literal[
    "QUOTED", "PENDING", "PENDING_BRIDGE", "SUBMITTED", "ERROR", "CANCELLED", "EXPIRED"
]
