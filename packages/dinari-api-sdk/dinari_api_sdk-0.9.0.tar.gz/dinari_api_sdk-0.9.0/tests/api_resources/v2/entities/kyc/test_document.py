# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from dinari_api_sdk import Dinari, AsyncDinari
from dinari_api_sdk.types.v2.entities.kyc import (
    KYCDocument,
    DocumentRetrieveResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestDocument:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Dinari) -> None:
        document = client.v2.entities.kyc.document.retrieve(
            kyc_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(DocumentRetrieveResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Dinari) -> None:
        response = client.v2.entities.kyc.document.with_raw_response.retrieve(
            kyc_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = response.parse()
        assert_matches_type(DocumentRetrieveResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Dinari) -> None:
        with client.v2.entities.kyc.document.with_streaming_response.retrieve(
            kyc_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = response.parse()
            assert_matches_type(DocumentRetrieveResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Dinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `entity_id` but received ''"):
            client.v2.entities.kyc.document.with_raw_response.retrieve(
                kyc_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                entity_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `kyc_id` but received ''"):
            client.v2.entities.kyc.document.with_raw_response.retrieve(
                kyc_id="",
                entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_upload(self, client: Dinari) -> None:
        document = client.v2.entities.kyc.document.upload(
            kyc_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            document_type="GOVERNMENT_ID",
            file=b"raw file contents",
        )
        assert_matches_type(KYCDocument, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_upload(self, client: Dinari) -> None:
        response = client.v2.entities.kyc.document.with_raw_response.upload(
            kyc_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            document_type="GOVERNMENT_ID",
            file=b"raw file contents",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = response.parse()
        assert_matches_type(KYCDocument, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_upload(self, client: Dinari) -> None:
        with client.v2.entities.kyc.document.with_streaming_response.upload(
            kyc_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            document_type="GOVERNMENT_ID",
            file=b"raw file contents",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = response.parse()
            assert_matches_type(KYCDocument, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_upload(self, client: Dinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `entity_id` but received ''"):
            client.v2.entities.kyc.document.with_raw_response.upload(
                kyc_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                entity_id="",
                document_type="GOVERNMENT_ID",
                file=b"raw file contents",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `kyc_id` but received ''"):
            client.v2.entities.kyc.document.with_raw_response.upload(
                kyc_id="",
                entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                document_type="GOVERNMENT_ID",
                file=b"raw file contents",
            )


class TestAsyncDocument:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncDinari) -> None:
        document = await async_client.v2.entities.kyc.document.retrieve(
            kyc_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(DocumentRetrieveResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.entities.kyc.document.with_raw_response.retrieve(
            kyc_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = await response.parse()
        assert_matches_type(DocumentRetrieveResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.entities.kyc.document.with_streaming_response.retrieve(
            kyc_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = await response.parse()
            assert_matches_type(DocumentRetrieveResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncDinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `entity_id` but received ''"):
            await async_client.v2.entities.kyc.document.with_raw_response.retrieve(
                kyc_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                entity_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `kyc_id` but received ''"):
            await async_client.v2.entities.kyc.document.with_raw_response.retrieve(
                kyc_id="",
                entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_upload(self, async_client: AsyncDinari) -> None:
        document = await async_client.v2.entities.kyc.document.upload(
            kyc_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            document_type="GOVERNMENT_ID",
            file=b"raw file contents",
        )
        assert_matches_type(KYCDocument, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_upload(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.entities.kyc.document.with_raw_response.upload(
            kyc_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            document_type="GOVERNMENT_ID",
            file=b"raw file contents",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = await response.parse()
        assert_matches_type(KYCDocument, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_upload(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.entities.kyc.document.with_streaming_response.upload(
            kyc_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            document_type="GOVERNMENT_ID",
            file=b"raw file contents",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = await response.parse()
            assert_matches_type(KYCDocument, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_upload(self, async_client: AsyncDinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `entity_id` but received ''"):
            await async_client.v2.entities.kyc.document.with_raw_response.upload(
                kyc_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                entity_id="",
                document_type="GOVERNMENT_ID",
                file=b"raw file contents",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `kyc_id` but received ''"):
            await async_client.v2.entities.kyc.document.with_raw_response.upload(
                kyc_id="",
                entity_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                document_type="GOVERNMENT_ID",
                file=b"raw file contents",
            )
