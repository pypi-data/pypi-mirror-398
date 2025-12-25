# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import TypeAlias

from .withdrawal import Withdrawal

__all__ = ["WithdrawalListResponse"]

WithdrawalListResponse: TypeAlias = List[Withdrawal]
