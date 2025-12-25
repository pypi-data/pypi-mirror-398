# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import TypeAlias

from .withdrawal_request import WithdrawalRequest

__all__ = ["WithdrawalRequestListResponse"]

WithdrawalRequestListResponse: TypeAlias = List[WithdrawalRequest]
