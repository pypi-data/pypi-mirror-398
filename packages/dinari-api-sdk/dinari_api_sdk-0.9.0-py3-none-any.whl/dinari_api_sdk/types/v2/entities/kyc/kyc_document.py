# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from ....._models import BaseModel
from .kyc_document_type import KYCDocumentType

__all__ = ["KYCDocument"]


class KYCDocument(BaseModel):
    """A document associated with KYC for an `Entity`."""

    id: str
    """ID of the document."""

    document_type: KYCDocumentType
    """Type of document."""

    filename: str
    """Filename of document."""

    url: str
    """Temporary URL to access the document. Expires in 1 hour."""
