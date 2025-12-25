# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from dinari_api_sdk import Dinari, AsyncDinari
from dinari_api_sdk.types.v2.accounts.order_requests import (
    Eip155SubmitResponse,
    Eip155CreatePermitResponse,
    Eip155CreatePermitTransactionResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestEip155:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_permit(self, client: Dinari) -> None:
        eip155 = client.v2.accounts.order_requests.eip155.create_permit(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            chain_id="eip155:1",
            order_side="BUY",
            order_tif="DAY",
            order_type="MARKET",
            payment_token="payment_token",
        )
        assert_matches_type(Eip155CreatePermitResponse, eip155, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_permit_with_all_params(self, client: Dinari) -> None:
        eip155 = client.v2.accounts.order_requests.eip155.create_permit(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            chain_id="eip155:1",
            order_side="BUY",
            order_tif="DAY",
            order_type="MARKET",
            payment_token="payment_token",
            asset_token_quantity=0,
            client_order_id="client_order_id",
            limit_price=0,
            payment_token_quantity=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            token_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(Eip155CreatePermitResponse, eip155, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create_permit(self, client: Dinari) -> None:
        response = client.v2.accounts.order_requests.eip155.with_raw_response.create_permit(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            chain_id="eip155:1",
            order_side="BUY",
            order_tif="DAY",
            order_type="MARKET",
            payment_token="payment_token",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        eip155 = response.parse()
        assert_matches_type(Eip155CreatePermitResponse, eip155, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create_permit(self, client: Dinari) -> None:
        with client.v2.accounts.order_requests.eip155.with_streaming_response.create_permit(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            chain_id="eip155:1",
            order_side="BUY",
            order_tif="DAY",
            order_type="MARKET",
            payment_token="payment_token",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            eip155 = response.parse()
            assert_matches_type(Eip155CreatePermitResponse, eip155, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_create_permit(self, client: Dinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.v2.accounts.order_requests.eip155.with_raw_response.create_permit(
                account_id="",
                chain_id="eip155:1",
                order_side="BUY",
                order_tif="DAY",
                order_type="MARKET",
                payment_token="payment_token",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_permit_transaction(self, client: Dinari) -> None:
        eip155 = client.v2.accounts.order_requests.eip155.create_permit_transaction(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            permit_signature="0xeaF12bD1DfFd",
        )
        assert_matches_type(Eip155CreatePermitTransactionResponse, eip155, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create_permit_transaction(self, client: Dinari) -> None:
        response = client.v2.accounts.order_requests.eip155.with_raw_response.create_permit_transaction(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            permit_signature="0xeaF12bD1DfFd",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        eip155 = response.parse()
        assert_matches_type(Eip155CreatePermitTransactionResponse, eip155, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create_permit_transaction(self, client: Dinari) -> None:
        with client.v2.accounts.order_requests.eip155.with_streaming_response.create_permit_transaction(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            permit_signature="0xeaF12bD1DfFd",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            eip155 = response.parse()
            assert_matches_type(Eip155CreatePermitTransactionResponse, eip155, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_create_permit_transaction(self, client: Dinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.v2.accounts.order_requests.eip155.with_raw_response.create_permit_transaction(
                account_id="",
                order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                permit_signature="0xeaF12bD1DfFd",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_submit(self, client: Dinari) -> None:
        eip155 = client.v2.accounts.order_requests.eip155.submit(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            permit_signature="0xeaF12bD1DfFd",
        )
        assert_matches_type(Eip155SubmitResponse, eip155, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_submit(self, client: Dinari) -> None:
        response = client.v2.accounts.order_requests.eip155.with_raw_response.submit(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            permit_signature="0xeaF12bD1DfFd",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        eip155 = response.parse()
        assert_matches_type(Eip155SubmitResponse, eip155, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_submit(self, client: Dinari) -> None:
        with client.v2.accounts.order_requests.eip155.with_streaming_response.submit(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            permit_signature="0xeaF12bD1DfFd",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            eip155 = response.parse()
            assert_matches_type(Eip155SubmitResponse, eip155, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_submit(self, client: Dinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.v2.accounts.order_requests.eip155.with_raw_response.submit(
                account_id="",
                order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                permit_signature="0xeaF12bD1DfFd",
            )


class TestAsyncEip155:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_permit(self, async_client: AsyncDinari) -> None:
        eip155 = await async_client.v2.accounts.order_requests.eip155.create_permit(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            chain_id="eip155:1",
            order_side="BUY",
            order_tif="DAY",
            order_type="MARKET",
            payment_token="payment_token",
        )
        assert_matches_type(Eip155CreatePermitResponse, eip155, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_permit_with_all_params(self, async_client: AsyncDinari) -> None:
        eip155 = await async_client.v2.accounts.order_requests.eip155.create_permit(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            chain_id="eip155:1",
            order_side="BUY",
            order_tif="DAY",
            order_type="MARKET",
            payment_token="payment_token",
            asset_token_quantity=0,
            client_order_id="client_order_id",
            limit_price=0,
            payment_token_quantity=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            token_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(Eip155CreatePermitResponse, eip155, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create_permit(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.accounts.order_requests.eip155.with_raw_response.create_permit(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            chain_id="eip155:1",
            order_side="BUY",
            order_tif="DAY",
            order_type="MARKET",
            payment_token="payment_token",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        eip155 = await response.parse()
        assert_matches_type(Eip155CreatePermitResponse, eip155, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create_permit(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.accounts.order_requests.eip155.with_streaming_response.create_permit(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            chain_id="eip155:1",
            order_side="BUY",
            order_tif="DAY",
            order_type="MARKET",
            payment_token="payment_token",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            eip155 = await response.parse()
            assert_matches_type(Eip155CreatePermitResponse, eip155, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_create_permit(self, async_client: AsyncDinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.v2.accounts.order_requests.eip155.with_raw_response.create_permit(
                account_id="",
                chain_id="eip155:1",
                order_side="BUY",
                order_tif="DAY",
                order_type="MARKET",
                payment_token="payment_token",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_permit_transaction(self, async_client: AsyncDinari) -> None:
        eip155 = await async_client.v2.accounts.order_requests.eip155.create_permit_transaction(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            permit_signature="0xeaF12bD1DfFd",
        )
        assert_matches_type(Eip155CreatePermitTransactionResponse, eip155, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create_permit_transaction(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.accounts.order_requests.eip155.with_raw_response.create_permit_transaction(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            permit_signature="0xeaF12bD1DfFd",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        eip155 = await response.parse()
        assert_matches_type(Eip155CreatePermitTransactionResponse, eip155, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create_permit_transaction(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.accounts.order_requests.eip155.with_streaming_response.create_permit_transaction(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            permit_signature="0xeaF12bD1DfFd",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            eip155 = await response.parse()
            assert_matches_type(Eip155CreatePermitTransactionResponse, eip155, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_create_permit_transaction(self, async_client: AsyncDinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.v2.accounts.order_requests.eip155.with_raw_response.create_permit_transaction(
                account_id="",
                order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                permit_signature="0xeaF12bD1DfFd",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_submit(self, async_client: AsyncDinari) -> None:
        eip155 = await async_client.v2.accounts.order_requests.eip155.submit(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            permit_signature="0xeaF12bD1DfFd",
        )
        assert_matches_type(Eip155SubmitResponse, eip155, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_submit(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.accounts.order_requests.eip155.with_raw_response.submit(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            permit_signature="0xeaF12bD1DfFd",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        eip155 = await response.parse()
        assert_matches_type(Eip155SubmitResponse, eip155, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_submit(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.accounts.order_requests.eip155.with_streaming_response.submit(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            permit_signature="0xeaF12bD1DfFd",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            eip155 = await response.parse()
            assert_matches_type(Eip155SubmitResponse, eip155, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_submit(self, async_client: AsyncDinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.v2.accounts.order_requests.eip155.with_raw_response.submit(
                account_id="",
                order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                permit_signature="0xeaF12bD1DfFd",
            )
