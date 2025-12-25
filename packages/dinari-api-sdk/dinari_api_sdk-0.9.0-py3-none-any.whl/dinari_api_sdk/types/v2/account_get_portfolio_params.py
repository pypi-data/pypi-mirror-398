# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["AccountGetPortfolioParams"]


class AccountGetPortfolioParams(TypedDict, total=False):
    page: Optional[int]
    """The page number."""

    page_size: Optional[int]
    """The number of stocks to return per page, maximum number is 200."""
