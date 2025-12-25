# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from .order import Order
from ...._models import BaseModel

__all__ = ["OrderBatchCancelResponse"]


class OrderBatchCancelResponse(BaseModel):
    cancel_queued_orders: List[Order]
    """Orders that were queued to cancel."""

    failed_to_cancel_orders: List[Order]
    """Orders that could not be queued to cancel."""
