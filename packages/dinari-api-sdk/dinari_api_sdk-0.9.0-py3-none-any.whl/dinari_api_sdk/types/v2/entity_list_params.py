# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["EntityListParams"]


class EntityListParams(TypedDict, total=False):
    page: int

    page_size: int

    reference_id: Optional[str]
    """Case sensitive unique reference ID for the `Entity`."""
