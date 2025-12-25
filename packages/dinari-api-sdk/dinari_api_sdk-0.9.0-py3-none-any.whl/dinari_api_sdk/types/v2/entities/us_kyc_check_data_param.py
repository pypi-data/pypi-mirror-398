# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Union, Optional
from datetime import date, datetime
from typing_extensions import Literal, Required, Annotated, TypedDict

from ...._types import SequenceNotStr
from ...._utils import PropertyInfo

__all__ = [
    "UsKYCCheckDataParam",
    "AlpacaCustomerAgreement",
    "AmlCheck",
    "DataCitation",
    "Employment",
    "FinancialProfile",
    "Identity",
    "KYCMetadata",
    "NonProfessionalTraderAttestation",
    "RiskDisclosure",
    "TrustedContact",
    "UsImmigrationInfo",
]


class AlpacaCustomerAgreement(TypedDict, total=False):
    """
    Information to affirm that the individual has read, agreed to, and signed Alpaca's customer
                agreement, found here: https://files.alpaca.markets/disclosures/library/AcctAppMarginAndCustAgmt.pdf
    """

    ip_address: Required[str]
    """The IP address from where the individual signed the agreement."""

    signed_at: Required[Annotated[Union[str, datetime], PropertyInfo(format="iso8601")]]
    """The timestamp the agreement was signed."""


class AmlCheck(TypedDict, total=False):
    """AML check information for this individual.

    If any of the checks have a match, provide details about the matches or hits found. The individual will be marked as high risk and be subject to manual review.
    """

    check_created_at: Required[Annotated[Union[str, datetime], PropertyInfo(format="iso8601")]]
    """Datetime that this AML check was created."""

    is_adverse_media_match: Required[bool]
    """Whether there was a match in the adverse media check."""

    is_monitored_lists_match: Required[bool]
    """Whether there was a match in the monitored lists check."""

    is_politically_exposed_person_match: Required[bool]
    """Whether there was a match in the politically exposed person (PEP) check."""

    is_sanctions_match: Required[bool]
    """Whether there was a match in the sanctions check."""

    records: Required[SequenceNotStr[str]]
    """
    If any of the checks have a match, provide details about the matches or hits
    found.
    """

    ref_id: Required[str]
    """Your unique identifier for the AML check."""


class DataCitation(TypedDict, total=False):
    """Data source citations for a KYC check."""

    address_sources: Required[SequenceNotStr[str]]
    """List of sources for address verification"""

    date_of_birth_sources: Required[SequenceNotStr[str]]
    """List of sources for date of birth verification"""

    tax_id_sources: Required[SequenceNotStr[str]]
    """List of sources for tax ID verification"""


class Employment(TypedDict, total=False):
    """Employment information for the individual"""

    employment_status: Required[Literal["UNEMPLOYED", "EMPLOYED", "STUDENT", "RETIRED"]]
    """One of the following: employed, unemployed, retired, or student."""

    employer_address: Optional[str]
    """The employer's address if the user is employed."""

    employer_name: Optional[str]
    """The name of the employer if the user is employed."""

    employment_position: Optional[str]
    """The user's position if they are employed."""


class FinancialProfile(TypedDict, total=False):
    """
    Financial profile information for the individual
                <br/><br/>
                Examples of liquid net worth ranges:
                <br/> - $0 - $20,000
                <br/> - $20,000 - $50,000
                <br/> - $50,000 - $100,000
                <br/> - $100,000 - $500,000
                <br/> - $500,000 - $1,000,000
    """

    funding_sources: Required[
        List[Literal["EMPLOYMENT_INCOME", "INVESTMENTS", "INHERITANCE", "BUSINESS_INCOME", "SAVINGS", "FAMILY"]]
    ]
    """
    One or more of the following: employment_income, investments, inheritance,
    business_income, savings, family.
    """

    liquid_net_worth_max: Required[int]
    """The upper bound of the user's liquid net worth (USD)."""

    liquid_net_worth_min: Required[int]
    """The lower bound of the user's liquid net worth (USD).

    Can be 0 if max is <=$20,000, but otherwise must be within an order of magnitude
    of the max value.
    """


class Identity(TypedDict, total=False):
    """Identity information for the individual"""

    city: Required[str]
    """City of the applicant."""

    country_of_citizenship: Required[str]
    """Nationality of the applicant."""

    country_of_tax_residence: Required[Literal["US"]]
    """Country of residency of the applicant. Must be 'US'."""

    date_of_birth: Required[Annotated[Union[str, date], PropertyInfo(format="iso8601")]]
    """Date of birth of the applicant."""

    email_address: Required[str]
    """Email address of the applicant."""

    family_name: Required[str]
    """The last name (surname) of the user."""

    given_name: Required[str]
    """The first/given name of the user."""

    phone_number: Required[str]
    """Phone number should include the country code, format: “+15555555555”"""

    postal_code: Required[str]
    """Postal code of the applicant."""

    street_address: Required[str]
    """Street address of the applicant."""

    tax_id: Required[str]
    """
    Social Security Number (SSN) or Tax Identification Number (TIN) of the
    applicant.
    """

    middle_name: Optional[str]
    """The middle name of the user."""

    state: Optional[str]
    """State of the applicant.

    Required if the applicant resides in the US as a 2-letter abbreviation.
    """

    unit: Optional[str]
    """The specific apartment number if applicable"""


class KYCMetadata(TypedDict, total=False):
    """Metadata about the KYC check."""

    check_completed_at: Required[Annotated[Union[str, datetime], PropertyInfo(format="iso8601")]]
    """Completion datetime of KYC check."""

    check_initiated_at: Required[Annotated[Union[str, datetime], PropertyInfo(format="iso8601")]]
    """Start datetime of KYC check."""

    ip_address: Required[str]
    """IP address of applicant at time of KYC check."""

    ref_id: Required[str]
    """Your unique identifier for the KYC check."""


class NonProfessionalTraderAttestation(TypedDict, total=False):
    """
    The non-professional trader property is a self-attestation for US customers that can affect the metered realtime data fees. This field must be updated when if there is a change in the user's attestation. This field may also be modified by Dinari compliance team. For more information, please see the US Customers Integration Guide.
    """

    attestation_dt: Required[Annotated[Union[str, datetime], PropertyInfo(format="iso8601")]]
    """Datetime when the attestation was made."""

    is_non_professional_trader: Required[bool]
    """Whether the individual attests to being a non-professional trader."""


class RiskDisclosure(TypedDict, total=False):
    """
    Risk information about the individual
                <br/><br/>
                Fields denote if the account owner falls under each category defined by FINRA rules. If any of the answers
                is true (yes), additional verifications may be required before US account approval.
    """

    immediate_family_exposed: Required[bool]
    """
    If the individual's immediate family member (sibling, husband/wife, child,
    parent) is either politically exposed or holds a control position.
    """

    is_affiliated_exchange_or_finra: Required[bool]
    """Whether the individual is affiliated with any exchanges or FINRA."""

    is_control_person: Required[bool]
    """
    Whether the individual holds a controlling position in a publicly traded
    company, is a member of the board of directors, or has policy making abilities
    in a publicly traded company.
    """

    is_politically_exposed: Required[bool]
    """Whether the individual is politically exposed."""


class TrustedContact(TypedDict, total=False):
    """Information for a trusted contact person for the individual.

    More information:
                <br/>
                - <a href="https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-trusted-contact" target="_blank" rel="noopener noreferrer">Investor.gov - Trusted Contact</a>
                <br/>
                - <a href="https://www.finra.org/investors/insights/trusted-contact" target="_blank" rel="noopener noreferrer">FINRA - Trusted Contact</a>
    """

    family_name: Required[str]
    """The family name of the trusted contact"""

    given_name: Required[str]
    """The given name of the trusted contact"""

    email_address: Optional[str]
    """The email address of the trusted contact.

    At least one of email_address or phone_number is required.
    """

    phone_number: Optional[str]
    """The phone number of the trusted contact.

    At least one of email_address or phone_number is required.
    """


class UsImmigrationInfo(TypedDict, total=False):
    """US immigration information for this individual.

    Required if the individual is not a US citizen.
    """

    country_of_birth: Required[str]
    """Country where the individual was born."""

    is_permanent_resident: Required[bool]
    """Whether the individual is a US permanent resident (green card holder)."""

    departure_from_us_date: Annotated[Union[str, date, None], PropertyInfo(format="iso8601")]
    """Date the individual is scheduled to leave the US. Required for B1 and B2 visas."""

    visa_expiration_date: Annotated[Union[str, date, None], PropertyInfo(format="iso8601")]
    """Expiration date of the visa. Required if visa_type is provided."""

    visa_type: Literal["B1", "B2", "DACA", "E1", "E2", "E3", "F1", "G4", "H1B", "J1", "L1", "Other", "O1", "TN1"]
    """Type of visa the individual holds. Required if not a permanent resident."""


class UsKYCCheckDataParam(TypedDict, total=False):
    """KYC data for an `Entity` in the US jurisdiction."""

    alpaca_customer_agreement: Required[AlpacaCustomerAgreement]
    """
    Information to affirm that the individual has read, agreed to, and signed
    Alpaca's customer agreement, found here:
    https://files.alpaca.markets/disclosures/library/AcctAppMarginAndCustAgmt.pdf
    """

    aml_check: Required[AmlCheck]
    """AML check information for this individual.

    If any of the checks have a match, provide details about the matches or hits
    found. The individual will be marked as high risk and be subject to manual
    review.
    """

    data_citation: Required[DataCitation]
    """Data source citations for a KYC check."""

    employment: Required[Employment]
    """Employment information for the individual"""

    financial_profile: Required[FinancialProfile]
    """
    Financial profile information for the individual <br/><br/> Examples of liquid
    net worth ranges: <br/> - $0 - $20,000 <br/> - $20,000 - $50,000 <br/> -
    $50,000 - $100,000 <br/> - $100,000 - $500,000 <br/> - $500,000 - $1,000,000
    """

    identity: Required[Identity]
    """Identity information for the individual"""

    kyc_metadata: Required[KYCMetadata]
    """Metadata about the KYC check."""

    non_professional_trader_attestation: Required[NonProfessionalTraderAttestation]
    """
    The non-professional trader property is a self-attestation for US customers that
    can affect the metered realtime data fees. This field must be updated when if
    there is a change in the user's attestation. This field may also be modified by
    Dinari compliance team. For more information, please see the US Customers
    Integration Guide.
    """

    risk_disclosure: Required[RiskDisclosure]
    """
    Risk information about the individual <br/><br/> Fields denote if the account
    owner falls under each category defined by FINRA rules. If any of the answers is
    true (yes), additional verifications may be required before US account approval.
    """

    trusted_contact: Required[TrustedContact]
    """Information for a trusted contact person for the individual.

    More information: <br/> -
    <a href="https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-trusted-contact" target="_blank" rel="noopener noreferrer">Investor.gov -
    Trusted Contact</a> <br/> -
    <a href="https://www.finra.org/investors/insights/trusted-contact" target="_blank" rel="noopener noreferrer">FINRA -
    Trusted Contact</a>
    """

    us_immigration_info: Optional[UsImmigrationInfo]
    """US immigration information for this individual.

    Required if the individual is not a US citizen.
    """
