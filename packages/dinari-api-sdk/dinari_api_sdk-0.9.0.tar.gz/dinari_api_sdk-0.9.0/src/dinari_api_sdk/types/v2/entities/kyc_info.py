# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Union, Optional
from datetime import datetime
from typing_extensions import Literal, Annotated, TypeAlias

from ...._utils import PropertyInfo
from ...._models import BaseModel
from .kyc_status import KYCStatus
from .us_kyc_check_data import UsKYCCheckData
from .baseline_kyc_check_data import BaselineKYCCheckData

__all__ = ["KYCInfo", "BaselineKYC", "UsKYC"]


class BaselineKYC(BaseModel):
    """KYC information for an `Entity` in the baseline jurisdiction."""

    id: str
    """ID of the KYC check."""

    status: KYCStatus
    """KYC check status."""

    checked_dt: Optional[datetime] = None
    """Datetime when the KYC was last checked. ISO 8601 timestamp."""

    data: Optional[BaselineKYCCheckData] = None
    """KYC data for an `Entity` in the BASELINE jurisdiction."""

    jurisdiction: Optional[Literal["BASELINE"]] = None
    """Jurisdiction of the KYC check."""


class UsKYC(BaseModel):
    """KYC information for an `Entity` in the US jurisdiction."""

    id: str
    """ID of the KYC check."""

    status: KYCStatus
    """KYC check status."""

    checked_dt: Optional[datetime] = None
    """Datetime when the KYC was last checked. ISO 8601 timestamp."""

    data: Optional[UsKYCCheckData] = None
    """KYC data for an `Entity` in the US jurisdiction."""

    jurisdiction: Optional[Literal["US"]] = None
    """Jurisdiction of the KYC check."""


KYCInfo: TypeAlias = Annotated[Union[BaselineKYC, UsKYC], PropertyInfo(discriminator="jurisdiction")]
