# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal, TypeAlias

__all__ = ["BrokerageOrderStatus"]

BrokerageOrderStatus: TypeAlias = Literal[
    "PENDING_SUBMIT",
    "PENDING_CANCEL",
    "PENDING_ESCROW",
    "PENDING_FILL",
    "ESCROWED",
    "SUBMITTED",
    "CANCELLED",
    "FILLED",
    "REJECTED",
    "REQUIRING_CONTACT",
    "ERROR",
]
