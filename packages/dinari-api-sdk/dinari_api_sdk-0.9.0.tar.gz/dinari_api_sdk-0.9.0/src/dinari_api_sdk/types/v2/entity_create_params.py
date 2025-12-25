# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, TypedDict

__all__ = ["EntityCreateParams"]


class EntityCreateParams(TypedDict, total=False):
    name: Required[str]
    """Name of the `Entity`."""

    reference_id: Optional[str]
    """Case sensitive unique reference ID for the `Entity`.

    We recommend setting this to the unique ID of the `Entity` in your system.
    """
