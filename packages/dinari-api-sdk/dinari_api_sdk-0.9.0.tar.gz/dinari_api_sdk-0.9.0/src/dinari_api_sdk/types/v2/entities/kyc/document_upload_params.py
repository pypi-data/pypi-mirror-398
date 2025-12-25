# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

from ....._types import FileTypes
from .kyc_document_type import KYCDocumentType

__all__ = ["DocumentUploadParams"]


class DocumentUploadParams(TypedDict, total=False):
    entity_id: Required[str]

    document_type: Required[KYCDocumentType]
    """Type of `KYCDocument` to be uploaded."""

    file: Required[FileTypes]
    """File to be uploaded.

    Must be a valid image or PDF file (jpg, jpeg, png, pdf) less than 10MB in size.
    """
