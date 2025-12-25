# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import date

from ...._models import BaseModel

__all__ = ["BaselineKYCCheckData"]


class BaselineKYCCheckData(BaseModel):
    """KYC data for an `Entity` in the BASELINE jurisdiction."""

    address_country_code: str
    """Country of residence. ISO 3166-1 alpha 2 country code."""

    country_code: str
    """Country of citizenship or home country of the organization.

    ISO 3166-1 alpha 2 country code.
    """

    last_name: str
    """Last name of the person."""

    address_city: Optional[str] = None
    """City of address. Not all international addresses use this attribute."""

    address_postal_code: Optional[str] = None
    """Postal code of residence address.

    Not all international addresses use this attribute.
    """

    address_street_1: Optional[str] = None
    """Street address of address."""

    address_street_2: Optional[str] = None
    """Extension of address, usually apartment or suite number."""

    address_subdivision: Optional[str] = None
    """State or subdivision of address.

    In the US, this should be the unabbreviated name of the state. Not all
    international addresses use this attribute.
    """

    birth_date: Optional[date] = None
    """Birth date of the individual. In ISO 8601 format, YYYY-MM-DD."""

    email: Optional[str] = None
    """Email address."""

    first_name: Optional[str] = None
    """First name of the person."""

    middle_name: Optional[str] = None
    """Middle name of the user"""

    tax_id_number: Optional[str] = None
    """ID number of the official tax document of the country the entity belongs to."""
