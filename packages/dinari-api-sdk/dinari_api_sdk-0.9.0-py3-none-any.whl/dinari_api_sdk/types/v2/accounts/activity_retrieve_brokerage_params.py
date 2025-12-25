# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["ActivityRetrieveBrokerageParams"]


class ActivityRetrieveBrokerageParams(TypedDict, total=False):
    page_size: Optional[int]
    """The maximum number of entries to return in the response. Defaults to 100."""

    page_token: Optional[str]
    """Pagination token.

    Set to the `id` field of the last Activity returned in the previous page to get
    the next page of results.
    """
