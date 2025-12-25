# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

from .jurisdiction import Jurisdiction

__all__ = ["AccountCreateParams"]


class AccountCreateParams(TypedDict, total=False):
    jurisdiction: Jurisdiction
    """Jurisdiction of the `Account`."""
