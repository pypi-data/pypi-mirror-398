# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["OrderRequestListParams"]


class OrderRequestListParams(TypedDict, total=False):
    client_order_id: Optional[str]
    """
    Customer-supplied ID to map this `OrderRequest` to an order in their own
    systems.
    """

    order_id: Optional[str]
    """Order ID for the `OrderRequest`"""

    order_request_id: Optional[str]
    """Order Request ID for the `OrderRequest`"""

    page: int

    page_size: int
