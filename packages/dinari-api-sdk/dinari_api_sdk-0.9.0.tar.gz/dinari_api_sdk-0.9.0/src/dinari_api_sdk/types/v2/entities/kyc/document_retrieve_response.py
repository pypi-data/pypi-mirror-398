# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import TypeAlias

from .kyc_document import KYCDocument

__all__ = ["DocumentRetrieveResponse"]

DocumentRetrieveResponse: TypeAlias = List[KYCDocument]
