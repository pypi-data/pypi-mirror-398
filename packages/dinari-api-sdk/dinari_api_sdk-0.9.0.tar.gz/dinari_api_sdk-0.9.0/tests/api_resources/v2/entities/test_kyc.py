# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from dinari_api_sdk import Dinari, AsyncDinari
from dinari_api_sdk._utils import parse_date, parse_datetime
from dinari_api_sdk.types.v2.entities import (
    KYCInfo,
    KYCCreateManagedCheckResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestKYC:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Dinari) -> None:
        kyc = client.v2.entities.kyc.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(KYCInfo, kyc, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Dinari) -> None:
        response = client.v2.entities.kyc.with_raw_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        kyc = response.parse()
        assert_matches_type(KYCInfo, kyc, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Dinari) -> None:
        with client.v2.entities.kyc.with_streaming_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            kyc = response.parse()
            assert_matches_type(KYCInfo, kyc, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Dinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `entity_id` but received ''"):
            client.v2.entities.kyc.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_managed_check(self, client: Dinari) -> None:
        kyc = client.v2.entities.kyc.create_managed_check(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(KYCCreateManagedCheckResponse, kyc, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create_managed_check(self, client: Dinari) -> None:
        response = client.v2.entities.kyc.with_raw_response.create_managed_check(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        kyc = response.parse()
        assert_matches_type(KYCCreateManagedCheckResponse, kyc, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create_managed_check(self, client: Dinari) -> None:
        with client.v2.entities.kyc.with_streaming_response.create_managed_check(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            kyc = response.parse()
            assert_matches_type(KYCCreateManagedCheckResponse, kyc, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_create_managed_check(self, client: Dinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `entity_id` but received ''"):
            client.v2.entities.kyc.with_raw_response.create_managed_check(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_submit_overload_1(self, client: Dinari) -> None:
        kyc = client.v2.entities.kyc.submit(
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            data={
                "address_country_code": "SG",
                "country_code": "SG",
                "last_name": "Doe",
            },
            provider_name="x",
        )
        assert_matches_type(KYCInfo, kyc, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_submit_with_all_params_overload_1(self, client: Dinari) -> None:
        kyc = client.v2.entities.kyc.submit(
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            data={
                "address_country_code": "SG",
                "country_code": "SG",
                "last_name": "Doe",
                "address_city": "San Francisco",
                "address_postal_code": "94111",
                "address_street_1": "123 Main St.",
                "address_street_2": "Apt. 123",
                "address_subdivision": "California",
                "birth_date": parse_date("2019-12-27"),
                "email": "johndoe@website.com",
                "first_name": "John",
                "middle_name": "x",
                "tax_id_number": "12-3456789",
            },
            provider_name="x",
            jurisdiction="BASELINE",
        )
        assert_matches_type(KYCInfo, kyc, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_submit_overload_1(self, client: Dinari) -> None:
        response = client.v2.entities.kyc.with_raw_response.submit(
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            data={
                "address_country_code": "SG",
                "country_code": "SG",
                "last_name": "Doe",
            },
            provider_name="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        kyc = response.parse()
        assert_matches_type(KYCInfo, kyc, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_submit_overload_1(self, client: Dinari) -> None:
        with client.v2.entities.kyc.with_streaming_response.submit(
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            data={
                "address_country_code": "SG",
                "country_code": "SG",
                "last_name": "Doe",
            },
            provider_name="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            kyc = response.parse()
            assert_matches_type(KYCInfo, kyc, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_submit_overload_1(self, client: Dinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `entity_id` but received ''"):
            client.v2.entities.kyc.with_raw_response.submit(
                entity_id="",
                data={
                    "address_country_code": "SG",
                    "country_code": "SG",
                    "last_name": "Doe",
                },
                provider_name="x",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_submit_overload_2(self, client: Dinari) -> None:
        kyc = client.v2.entities.kyc.submit(
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            data={
                "alpaca_customer_agreement": {
                    "ip_address": "192.0.2.1",
                    "signed_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                },
                "aml_check": {
                    "check_created_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "is_adverse_media_match": True,
                    "is_monitored_lists_match": True,
                    "is_politically_exposed_person_match": True,
                    "is_sanctions_match": True,
                    "records": [
                        "Name: John Doe, Alias: Jonathan Doe, Address: 123 Main St, Springfield, DOB: 01/01/1980, Type of Hit: PEP, Position: Mayor of Springfield, List: World-Check, URL: http://example.com/article",
                        "Name: John Doe, Address: 456 Elm St, Springfield, Type of Hit: Adverse Media, Summary: Involved in financial scandal, URL: http://example.com/article",
                    ],
                    "ref_id": "x",
                },
                "data_citation": {
                    "address_sources": ["utility bill"],
                    "date_of_birth_sources": ["birth certificate", "government database lookup"],
                    "tax_id_sources": ["tax return", "government database lookup"],
                },
                "employment": {"employment_status": "UNEMPLOYED"},
                "financial_profile": {
                    "funding_sources": ["EMPLOYMENT_INCOME"],
                    "liquid_net_worth_max": 0,
                    "liquid_net_worth_min": 0,
                },
                "identity": {
                    "city": "xx",
                    "country_of_citizenship": "xx",
                    "country_of_tax_residence": "US",
                    "date_of_birth": parse_date("2019-12-27"),
                    "email_address": "email_address",
                    "family_name": "xx",
                    "given_name": "x",
                    "phone_number": "+321669910225610",
                    "postal_code": "x",
                    "street_address": "xx",
                    "tax_id": "732-66-9102",
                },
                "kyc_metadata": {
                    "check_completed_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "check_initiated_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "ip_address": "192.0.2.1",
                    "ref_id": "x",
                },
                "non_professional_trader_attestation": {
                    "attestation_dt": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "is_non_professional_trader": True,
                },
                "risk_disclosure": {
                    "immediate_family_exposed": True,
                    "is_affiliated_exchange_or_finra": True,
                    "is_control_person": True,
                    "is_politically_exposed": True,
                },
                "trusted_contact": {
                    "family_name": "family_name",
                    "given_name": "given_name",
                },
            },
            provider_name="x",
        )
        assert_matches_type(KYCInfo, kyc, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_submit_with_all_params_overload_2(self, client: Dinari) -> None:
        kyc = client.v2.entities.kyc.submit(
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            data={
                "alpaca_customer_agreement": {
                    "ip_address": "192.0.2.1",
                    "signed_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                },
                "aml_check": {
                    "check_created_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "is_adverse_media_match": True,
                    "is_monitored_lists_match": True,
                    "is_politically_exposed_person_match": True,
                    "is_sanctions_match": True,
                    "records": [
                        "Name: John Doe, Alias: Jonathan Doe, Address: 123 Main St, Springfield, DOB: 01/01/1980, Type of Hit: PEP, Position: Mayor of Springfield, List: World-Check, URL: http://example.com/article",
                        "Name: John Doe, Address: 456 Elm St, Springfield, Type of Hit: Adverse Media, Summary: Involved in financial scandal, URL: http://example.com/article",
                    ],
                    "ref_id": "x",
                },
                "data_citation": {
                    "address_sources": ["utility bill"],
                    "date_of_birth_sources": ["birth certificate", "government database lookup"],
                    "tax_id_sources": ["tax return", "government database lookup"],
                },
                "employment": {
                    "employment_status": "UNEMPLOYED",
                    "employer_address": "x",
                    "employer_name": "x",
                    "employment_position": "x",
                },
                "financial_profile": {
                    "funding_sources": ["EMPLOYMENT_INCOME"],
                    "liquid_net_worth_max": 0,
                    "liquid_net_worth_min": 0,
                },
                "identity": {
                    "city": "xx",
                    "country_of_citizenship": "xx",
                    "country_of_tax_residence": "US",
                    "date_of_birth": parse_date("2019-12-27"),
                    "email_address": "email_address",
                    "family_name": "xx",
                    "given_name": "x",
                    "phone_number": "+321669910225610",
                    "postal_code": "x",
                    "street_address": "xx",
                    "tax_id": "732-66-9102",
                    "middle_name": "x",
                    "state": "x",
                    "unit": "x",
                },
                "kyc_metadata": {
                    "check_completed_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "check_initiated_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "ip_address": "192.0.2.1",
                    "ref_id": "x",
                },
                "non_professional_trader_attestation": {
                    "attestation_dt": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "is_non_professional_trader": True,
                },
                "risk_disclosure": {
                    "immediate_family_exposed": True,
                    "is_affiliated_exchange_or_finra": True,
                    "is_control_person": True,
                    "is_politically_exposed": True,
                },
                "trusted_contact": {
                    "family_name": "family_name",
                    "given_name": "given_name",
                    "email_address": "email_address",
                    "phone_number": "+321669910225610",
                },
                "us_immigration_info": {
                    "country_of_birth": "xx",
                    "is_permanent_resident": True,
                    "departure_from_us_date": parse_date("2019-12-27"),
                    "visa_expiration_date": parse_date("2019-12-27"),
                    "visa_type": "B1",
                },
            },
            provider_name="x",
            jurisdiction="US",
        )
        assert_matches_type(KYCInfo, kyc, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_submit_overload_2(self, client: Dinari) -> None:
        response = client.v2.entities.kyc.with_raw_response.submit(
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            data={
                "alpaca_customer_agreement": {
                    "ip_address": "192.0.2.1",
                    "signed_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                },
                "aml_check": {
                    "check_created_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "is_adverse_media_match": True,
                    "is_monitored_lists_match": True,
                    "is_politically_exposed_person_match": True,
                    "is_sanctions_match": True,
                    "records": [
                        "Name: John Doe, Alias: Jonathan Doe, Address: 123 Main St, Springfield, DOB: 01/01/1980, Type of Hit: PEP, Position: Mayor of Springfield, List: World-Check, URL: http://example.com/article",
                        "Name: John Doe, Address: 456 Elm St, Springfield, Type of Hit: Adverse Media, Summary: Involved in financial scandal, URL: http://example.com/article",
                    ],
                    "ref_id": "x",
                },
                "data_citation": {
                    "address_sources": ["utility bill"],
                    "date_of_birth_sources": ["birth certificate", "government database lookup"],
                    "tax_id_sources": ["tax return", "government database lookup"],
                },
                "employment": {"employment_status": "UNEMPLOYED"},
                "financial_profile": {
                    "funding_sources": ["EMPLOYMENT_INCOME"],
                    "liquid_net_worth_max": 0,
                    "liquid_net_worth_min": 0,
                },
                "identity": {
                    "city": "xx",
                    "country_of_citizenship": "xx",
                    "country_of_tax_residence": "US",
                    "date_of_birth": parse_date("2019-12-27"),
                    "email_address": "email_address",
                    "family_name": "xx",
                    "given_name": "x",
                    "phone_number": "+321669910225610",
                    "postal_code": "x",
                    "street_address": "xx",
                    "tax_id": "732-66-9102",
                },
                "kyc_metadata": {
                    "check_completed_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "check_initiated_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "ip_address": "192.0.2.1",
                    "ref_id": "x",
                },
                "non_professional_trader_attestation": {
                    "attestation_dt": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "is_non_professional_trader": True,
                },
                "risk_disclosure": {
                    "immediate_family_exposed": True,
                    "is_affiliated_exchange_or_finra": True,
                    "is_control_person": True,
                    "is_politically_exposed": True,
                },
                "trusted_contact": {
                    "family_name": "family_name",
                    "given_name": "given_name",
                },
            },
            provider_name="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        kyc = response.parse()
        assert_matches_type(KYCInfo, kyc, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_submit_overload_2(self, client: Dinari) -> None:
        with client.v2.entities.kyc.with_streaming_response.submit(
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            data={
                "alpaca_customer_agreement": {
                    "ip_address": "192.0.2.1",
                    "signed_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                },
                "aml_check": {
                    "check_created_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "is_adverse_media_match": True,
                    "is_monitored_lists_match": True,
                    "is_politically_exposed_person_match": True,
                    "is_sanctions_match": True,
                    "records": [
                        "Name: John Doe, Alias: Jonathan Doe, Address: 123 Main St, Springfield, DOB: 01/01/1980, Type of Hit: PEP, Position: Mayor of Springfield, List: World-Check, URL: http://example.com/article",
                        "Name: John Doe, Address: 456 Elm St, Springfield, Type of Hit: Adverse Media, Summary: Involved in financial scandal, URL: http://example.com/article",
                    ],
                    "ref_id": "x",
                },
                "data_citation": {
                    "address_sources": ["utility bill"],
                    "date_of_birth_sources": ["birth certificate", "government database lookup"],
                    "tax_id_sources": ["tax return", "government database lookup"],
                },
                "employment": {"employment_status": "UNEMPLOYED"},
                "financial_profile": {
                    "funding_sources": ["EMPLOYMENT_INCOME"],
                    "liquid_net_worth_max": 0,
                    "liquid_net_worth_min": 0,
                },
                "identity": {
                    "city": "xx",
                    "country_of_citizenship": "xx",
                    "country_of_tax_residence": "US",
                    "date_of_birth": parse_date("2019-12-27"),
                    "email_address": "email_address",
                    "family_name": "xx",
                    "given_name": "x",
                    "phone_number": "+321669910225610",
                    "postal_code": "x",
                    "street_address": "xx",
                    "tax_id": "732-66-9102",
                },
                "kyc_metadata": {
                    "check_completed_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "check_initiated_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "ip_address": "192.0.2.1",
                    "ref_id": "x",
                },
                "non_professional_trader_attestation": {
                    "attestation_dt": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "is_non_professional_trader": True,
                },
                "risk_disclosure": {
                    "immediate_family_exposed": True,
                    "is_affiliated_exchange_or_finra": True,
                    "is_control_person": True,
                    "is_politically_exposed": True,
                },
                "trusted_contact": {
                    "family_name": "family_name",
                    "given_name": "given_name",
                },
            },
            provider_name="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            kyc = response.parse()
            assert_matches_type(KYCInfo, kyc, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_submit_overload_2(self, client: Dinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `entity_id` but received ''"):
            client.v2.entities.kyc.with_raw_response.submit(
                entity_id="",
                data={
                    "alpaca_customer_agreement": {
                        "ip_address": "192.0.2.1",
                        "signed_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                    },
                    "aml_check": {
                        "check_created_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                        "is_adverse_media_match": True,
                        "is_monitored_lists_match": True,
                        "is_politically_exposed_person_match": True,
                        "is_sanctions_match": True,
                        "records": [
                            "Name: John Doe, Alias: Jonathan Doe, Address: 123 Main St, Springfield, DOB: 01/01/1980, Type of Hit: PEP, Position: Mayor of Springfield, List: World-Check, URL: http://example.com/article",
                            "Name: John Doe, Address: 456 Elm St, Springfield, Type of Hit: Adverse Media, Summary: Involved in financial scandal, URL: http://example.com/article",
                        ],
                        "ref_id": "x",
                    },
                    "data_citation": {
                        "address_sources": ["utility bill"],
                        "date_of_birth_sources": ["birth certificate", "government database lookup"],
                        "tax_id_sources": ["tax return", "government database lookup"],
                    },
                    "employment": {"employment_status": "UNEMPLOYED"},
                    "financial_profile": {
                        "funding_sources": ["EMPLOYMENT_INCOME"],
                        "liquid_net_worth_max": 0,
                        "liquid_net_worth_min": 0,
                    },
                    "identity": {
                        "city": "xx",
                        "country_of_citizenship": "xx",
                        "country_of_tax_residence": "US",
                        "date_of_birth": parse_date("2019-12-27"),
                        "email_address": "email_address",
                        "family_name": "xx",
                        "given_name": "x",
                        "phone_number": "+321669910225610",
                        "postal_code": "x",
                        "street_address": "xx",
                        "tax_id": "732-66-9102",
                    },
                    "kyc_metadata": {
                        "check_completed_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                        "check_initiated_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                        "ip_address": "192.0.2.1",
                        "ref_id": "x",
                    },
                    "non_professional_trader_attestation": {
                        "attestation_dt": parse_datetime("2019-12-27T18:11:19.117Z"),
                        "is_non_professional_trader": True,
                    },
                    "risk_disclosure": {
                        "immediate_family_exposed": True,
                        "is_affiliated_exchange_or_finra": True,
                        "is_control_person": True,
                        "is_politically_exposed": True,
                    },
                    "trusted_contact": {
                        "family_name": "family_name",
                        "given_name": "given_name",
                    },
                },
                provider_name="x",
            )


class TestAsyncKYC:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncDinari) -> None:
        kyc = await async_client.v2.entities.kyc.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(KYCInfo, kyc, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.entities.kyc.with_raw_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        kyc = await response.parse()
        assert_matches_type(KYCInfo, kyc, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.entities.kyc.with_streaming_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            kyc = await response.parse()
            assert_matches_type(KYCInfo, kyc, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncDinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `entity_id` but received ''"):
            await async_client.v2.entities.kyc.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_managed_check(self, async_client: AsyncDinari) -> None:
        kyc = await async_client.v2.entities.kyc.create_managed_check(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(KYCCreateManagedCheckResponse, kyc, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create_managed_check(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.entities.kyc.with_raw_response.create_managed_check(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        kyc = await response.parse()
        assert_matches_type(KYCCreateManagedCheckResponse, kyc, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create_managed_check(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.entities.kyc.with_streaming_response.create_managed_check(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            kyc = await response.parse()
            assert_matches_type(KYCCreateManagedCheckResponse, kyc, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_create_managed_check(self, async_client: AsyncDinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `entity_id` but received ''"):
            await async_client.v2.entities.kyc.with_raw_response.create_managed_check(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_submit_overload_1(self, async_client: AsyncDinari) -> None:
        kyc = await async_client.v2.entities.kyc.submit(
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            data={
                "address_country_code": "SG",
                "country_code": "SG",
                "last_name": "Doe",
            },
            provider_name="x",
        )
        assert_matches_type(KYCInfo, kyc, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_submit_with_all_params_overload_1(self, async_client: AsyncDinari) -> None:
        kyc = await async_client.v2.entities.kyc.submit(
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            data={
                "address_country_code": "SG",
                "country_code": "SG",
                "last_name": "Doe",
                "address_city": "San Francisco",
                "address_postal_code": "94111",
                "address_street_1": "123 Main St.",
                "address_street_2": "Apt. 123",
                "address_subdivision": "California",
                "birth_date": parse_date("2019-12-27"),
                "email": "johndoe@website.com",
                "first_name": "John",
                "middle_name": "x",
                "tax_id_number": "12-3456789",
            },
            provider_name="x",
            jurisdiction="BASELINE",
        )
        assert_matches_type(KYCInfo, kyc, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_submit_overload_1(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.entities.kyc.with_raw_response.submit(
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            data={
                "address_country_code": "SG",
                "country_code": "SG",
                "last_name": "Doe",
            },
            provider_name="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        kyc = await response.parse()
        assert_matches_type(KYCInfo, kyc, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_submit_overload_1(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.entities.kyc.with_streaming_response.submit(
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            data={
                "address_country_code": "SG",
                "country_code": "SG",
                "last_name": "Doe",
            },
            provider_name="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            kyc = await response.parse()
            assert_matches_type(KYCInfo, kyc, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_submit_overload_1(self, async_client: AsyncDinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `entity_id` but received ''"):
            await async_client.v2.entities.kyc.with_raw_response.submit(
                entity_id="",
                data={
                    "address_country_code": "SG",
                    "country_code": "SG",
                    "last_name": "Doe",
                },
                provider_name="x",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_submit_overload_2(self, async_client: AsyncDinari) -> None:
        kyc = await async_client.v2.entities.kyc.submit(
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            data={
                "alpaca_customer_agreement": {
                    "ip_address": "192.0.2.1",
                    "signed_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                },
                "aml_check": {
                    "check_created_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "is_adverse_media_match": True,
                    "is_monitored_lists_match": True,
                    "is_politically_exposed_person_match": True,
                    "is_sanctions_match": True,
                    "records": [
                        "Name: John Doe, Alias: Jonathan Doe, Address: 123 Main St, Springfield, DOB: 01/01/1980, Type of Hit: PEP, Position: Mayor of Springfield, List: World-Check, URL: http://example.com/article",
                        "Name: John Doe, Address: 456 Elm St, Springfield, Type of Hit: Adverse Media, Summary: Involved in financial scandal, URL: http://example.com/article",
                    ],
                    "ref_id": "x",
                },
                "data_citation": {
                    "address_sources": ["utility bill"],
                    "date_of_birth_sources": ["birth certificate", "government database lookup"],
                    "tax_id_sources": ["tax return", "government database lookup"],
                },
                "employment": {"employment_status": "UNEMPLOYED"},
                "financial_profile": {
                    "funding_sources": ["EMPLOYMENT_INCOME"],
                    "liquid_net_worth_max": 0,
                    "liquid_net_worth_min": 0,
                },
                "identity": {
                    "city": "xx",
                    "country_of_citizenship": "xx",
                    "country_of_tax_residence": "US",
                    "date_of_birth": parse_date("2019-12-27"),
                    "email_address": "email_address",
                    "family_name": "xx",
                    "given_name": "x",
                    "phone_number": "+321669910225610",
                    "postal_code": "x",
                    "street_address": "xx",
                    "tax_id": "732-66-9102",
                },
                "kyc_metadata": {
                    "check_completed_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "check_initiated_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "ip_address": "192.0.2.1",
                    "ref_id": "x",
                },
                "non_professional_trader_attestation": {
                    "attestation_dt": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "is_non_professional_trader": True,
                },
                "risk_disclosure": {
                    "immediate_family_exposed": True,
                    "is_affiliated_exchange_or_finra": True,
                    "is_control_person": True,
                    "is_politically_exposed": True,
                },
                "trusted_contact": {
                    "family_name": "family_name",
                    "given_name": "given_name",
                },
            },
            provider_name="x",
        )
        assert_matches_type(KYCInfo, kyc, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_submit_with_all_params_overload_2(self, async_client: AsyncDinari) -> None:
        kyc = await async_client.v2.entities.kyc.submit(
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            data={
                "alpaca_customer_agreement": {
                    "ip_address": "192.0.2.1",
                    "signed_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                },
                "aml_check": {
                    "check_created_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "is_adverse_media_match": True,
                    "is_monitored_lists_match": True,
                    "is_politically_exposed_person_match": True,
                    "is_sanctions_match": True,
                    "records": [
                        "Name: John Doe, Alias: Jonathan Doe, Address: 123 Main St, Springfield, DOB: 01/01/1980, Type of Hit: PEP, Position: Mayor of Springfield, List: World-Check, URL: http://example.com/article",
                        "Name: John Doe, Address: 456 Elm St, Springfield, Type of Hit: Adverse Media, Summary: Involved in financial scandal, URL: http://example.com/article",
                    ],
                    "ref_id": "x",
                },
                "data_citation": {
                    "address_sources": ["utility bill"],
                    "date_of_birth_sources": ["birth certificate", "government database lookup"],
                    "tax_id_sources": ["tax return", "government database lookup"],
                },
                "employment": {
                    "employment_status": "UNEMPLOYED",
                    "employer_address": "x",
                    "employer_name": "x",
                    "employment_position": "x",
                },
                "financial_profile": {
                    "funding_sources": ["EMPLOYMENT_INCOME"],
                    "liquid_net_worth_max": 0,
                    "liquid_net_worth_min": 0,
                },
                "identity": {
                    "city": "xx",
                    "country_of_citizenship": "xx",
                    "country_of_tax_residence": "US",
                    "date_of_birth": parse_date("2019-12-27"),
                    "email_address": "email_address",
                    "family_name": "xx",
                    "given_name": "x",
                    "phone_number": "+321669910225610",
                    "postal_code": "x",
                    "street_address": "xx",
                    "tax_id": "732-66-9102",
                    "middle_name": "x",
                    "state": "x",
                    "unit": "x",
                },
                "kyc_metadata": {
                    "check_completed_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "check_initiated_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "ip_address": "192.0.2.1",
                    "ref_id": "x",
                },
                "non_professional_trader_attestation": {
                    "attestation_dt": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "is_non_professional_trader": True,
                },
                "risk_disclosure": {
                    "immediate_family_exposed": True,
                    "is_affiliated_exchange_or_finra": True,
                    "is_control_person": True,
                    "is_politically_exposed": True,
                },
                "trusted_contact": {
                    "family_name": "family_name",
                    "given_name": "given_name",
                    "email_address": "email_address",
                    "phone_number": "+321669910225610",
                },
                "us_immigration_info": {
                    "country_of_birth": "xx",
                    "is_permanent_resident": True,
                    "departure_from_us_date": parse_date("2019-12-27"),
                    "visa_expiration_date": parse_date("2019-12-27"),
                    "visa_type": "B1",
                },
            },
            provider_name="x",
            jurisdiction="US",
        )
        assert_matches_type(KYCInfo, kyc, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_submit_overload_2(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.entities.kyc.with_raw_response.submit(
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            data={
                "alpaca_customer_agreement": {
                    "ip_address": "192.0.2.1",
                    "signed_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                },
                "aml_check": {
                    "check_created_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "is_adverse_media_match": True,
                    "is_monitored_lists_match": True,
                    "is_politically_exposed_person_match": True,
                    "is_sanctions_match": True,
                    "records": [
                        "Name: John Doe, Alias: Jonathan Doe, Address: 123 Main St, Springfield, DOB: 01/01/1980, Type of Hit: PEP, Position: Mayor of Springfield, List: World-Check, URL: http://example.com/article",
                        "Name: John Doe, Address: 456 Elm St, Springfield, Type of Hit: Adverse Media, Summary: Involved in financial scandal, URL: http://example.com/article",
                    ],
                    "ref_id": "x",
                },
                "data_citation": {
                    "address_sources": ["utility bill"],
                    "date_of_birth_sources": ["birth certificate", "government database lookup"],
                    "tax_id_sources": ["tax return", "government database lookup"],
                },
                "employment": {"employment_status": "UNEMPLOYED"},
                "financial_profile": {
                    "funding_sources": ["EMPLOYMENT_INCOME"],
                    "liquid_net_worth_max": 0,
                    "liquid_net_worth_min": 0,
                },
                "identity": {
                    "city": "xx",
                    "country_of_citizenship": "xx",
                    "country_of_tax_residence": "US",
                    "date_of_birth": parse_date("2019-12-27"),
                    "email_address": "email_address",
                    "family_name": "xx",
                    "given_name": "x",
                    "phone_number": "+321669910225610",
                    "postal_code": "x",
                    "street_address": "xx",
                    "tax_id": "732-66-9102",
                },
                "kyc_metadata": {
                    "check_completed_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "check_initiated_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "ip_address": "192.0.2.1",
                    "ref_id": "x",
                },
                "non_professional_trader_attestation": {
                    "attestation_dt": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "is_non_professional_trader": True,
                },
                "risk_disclosure": {
                    "immediate_family_exposed": True,
                    "is_affiliated_exchange_or_finra": True,
                    "is_control_person": True,
                    "is_politically_exposed": True,
                },
                "trusted_contact": {
                    "family_name": "family_name",
                    "given_name": "given_name",
                },
            },
            provider_name="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        kyc = await response.parse()
        assert_matches_type(KYCInfo, kyc, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_submit_overload_2(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.entities.kyc.with_streaming_response.submit(
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            data={
                "alpaca_customer_agreement": {
                    "ip_address": "192.0.2.1",
                    "signed_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                },
                "aml_check": {
                    "check_created_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "is_adverse_media_match": True,
                    "is_monitored_lists_match": True,
                    "is_politically_exposed_person_match": True,
                    "is_sanctions_match": True,
                    "records": [
                        "Name: John Doe, Alias: Jonathan Doe, Address: 123 Main St, Springfield, DOB: 01/01/1980, Type of Hit: PEP, Position: Mayor of Springfield, List: World-Check, URL: http://example.com/article",
                        "Name: John Doe, Address: 456 Elm St, Springfield, Type of Hit: Adverse Media, Summary: Involved in financial scandal, URL: http://example.com/article",
                    ],
                    "ref_id": "x",
                },
                "data_citation": {
                    "address_sources": ["utility bill"],
                    "date_of_birth_sources": ["birth certificate", "government database lookup"],
                    "tax_id_sources": ["tax return", "government database lookup"],
                },
                "employment": {"employment_status": "UNEMPLOYED"},
                "financial_profile": {
                    "funding_sources": ["EMPLOYMENT_INCOME"],
                    "liquid_net_worth_max": 0,
                    "liquid_net_worth_min": 0,
                },
                "identity": {
                    "city": "xx",
                    "country_of_citizenship": "xx",
                    "country_of_tax_residence": "US",
                    "date_of_birth": parse_date("2019-12-27"),
                    "email_address": "email_address",
                    "family_name": "xx",
                    "given_name": "x",
                    "phone_number": "+321669910225610",
                    "postal_code": "x",
                    "street_address": "xx",
                    "tax_id": "732-66-9102",
                },
                "kyc_metadata": {
                    "check_completed_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "check_initiated_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "ip_address": "192.0.2.1",
                    "ref_id": "x",
                },
                "non_professional_trader_attestation": {
                    "attestation_dt": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "is_non_professional_trader": True,
                },
                "risk_disclosure": {
                    "immediate_family_exposed": True,
                    "is_affiliated_exchange_or_finra": True,
                    "is_control_person": True,
                    "is_politically_exposed": True,
                },
                "trusted_contact": {
                    "family_name": "family_name",
                    "given_name": "given_name",
                },
            },
            provider_name="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            kyc = await response.parse()
            assert_matches_type(KYCInfo, kyc, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_submit_overload_2(self, async_client: AsyncDinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `entity_id` but received ''"):
            await async_client.v2.entities.kyc.with_raw_response.submit(
                entity_id="",
                data={
                    "alpaca_customer_agreement": {
                        "ip_address": "192.0.2.1",
                        "signed_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                    },
                    "aml_check": {
                        "check_created_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                        "is_adverse_media_match": True,
                        "is_monitored_lists_match": True,
                        "is_politically_exposed_person_match": True,
                        "is_sanctions_match": True,
                        "records": [
                            "Name: John Doe, Alias: Jonathan Doe, Address: 123 Main St, Springfield, DOB: 01/01/1980, Type of Hit: PEP, Position: Mayor of Springfield, List: World-Check, URL: http://example.com/article",
                            "Name: John Doe, Address: 456 Elm St, Springfield, Type of Hit: Adverse Media, Summary: Involved in financial scandal, URL: http://example.com/article",
                        ],
                        "ref_id": "x",
                    },
                    "data_citation": {
                        "address_sources": ["utility bill"],
                        "date_of_birth_sources": ["birth certificate", "government database lookup"],
                        "tax_id_sources": ["tax return", "government database lookup"],
                    },
                    "employment": {"employment_status": "UNEMPLOYED"},
                    "financial_profile": {
                        "funding_sources": ["EMPLOYMENT_INCOME"],
                        "liquid_net_worth_max": 0,
                        "liquid_net_worth_min": 0,
                    },
                    "identity": {
                        "city": "xx",
                        "country_of_citizenship": "xx",
                        "country_of_tax_residence": "US",
                        "date_of_birth": parse_date("2019-12-27"),
                        "email_address": "email_address",
                        "family_name": "xx",
                        "given_name": "x",
                        "phone_number": "+321669910225610",
                        "postal_code": "x",
                        "street_address": "xx",
                        "tax_id": "732-66-9102",
                    },
                    "kyc_metadata": {
                        "check_completed_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                        "check_initiated_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                        "ip_address": "192.0.2.1",
                        "ref_id": "x",
                    },
                    "non_professional_trader_attestation": {
                        "attestation_dt": parse_datetime("2019-12-27T18:11:19.117Z"),
                        "is_non_professional_trader": True,
                    },
                    "risk_disclosure": {
                        "immediate_family_exposed": True,
                        "is_affiliated_exchange_or_finra": True,
                        "is_control_person": True,
                        "is_politically_exposed": True,
                    },
                    "trusted_contact": {
                        "family_name": "family_name",
                        "given_name": "given_name",
                    },
                },
                provider_name="x",
            )
