# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import TypeAlias

from .order_request import OrderRequest

__all__ = ["OrderRequestListResponse"]

OrderRequestListResponse: TypeAlias = List[OrderRequest]
