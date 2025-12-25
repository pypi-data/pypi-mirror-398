# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import TypeAlias

from .stock_split import StockSplit

__all__ = ["SplitListForStockResponse"]

SplitListForStockResponse: TypeAlias = List[StockSplit]
