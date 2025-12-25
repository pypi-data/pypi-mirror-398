# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

from ...._types import SequenceNotStr

__all__ = ["OrderFulfillmentQueryParams"]


class OrderFulfillmentQueryParams(TypedDict, total=False):
    order_ids: SequenceNotStr[str]
    """List of `Order` IDs to query `OrderFulfillments` for."""

    page: int

    page_size: int
