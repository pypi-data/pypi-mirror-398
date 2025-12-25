# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from dinari_api_sdk import Dinari, AsyncDinari
from dinari_api_sdk.types import V2ListOrdersResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestV2:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_orders(self, client: Dinari) -> None:
        v2 = client.v2.list_orders()
        assert_matches_type(V2ListOrdersResponse, v2, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_orders_with_all_params(self, client: Dinari) -> None:
        v2 = client.v2.list_orders(
            chain_id="eip155:1",
            order_fulfillment_transaction_hash="order_fulfillment_transaction_hash",
            order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            order_transaction_hash="order_transaction_hash",
            page=1,
            page_size=1,
        )
        assert_matches_type(V2ListOrdersResponse, v2, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_orders(self, client: Dinari) -> None:
        response = client.v2.with_raw_response.list_orders()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        v2 = response.parse()
        assert_matches_type(V2ListOrdersResponse, v2, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_orders(self, client: Dinari) -> None:
        with client.v2.with_streaming_response.list_orders() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            v2 = response.parse()
            assert_matches_type(V2ListOrdersResponse, v2, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncV2:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_orders(self, async_client: AsyncDinari) -> None:
        v2 = await async_client.v2.list_orders()
        assert_matches_type(V2ListOrdersResponse, v2, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_orders_with_all_params(self, async_client: AsyncDinari) -> None:
        v2 = await async_client.v2.list_orders(
            chain_id="eip155:1",
            order_fulfillment_transaction_hash="order_fulfillment_transaction_hash",
            order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            order_transaction_hash="order_transaction_hash",
            page=1,
            page_size=1,
        )
        assert_matches_type(V2ListOrdersResponse, v2, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_orders(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.with_raw_response.list_orders()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        v2 = await response.parse()
        assert_matches_type(V2ListOrdersResponse, v2, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_orders(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.with_streaming_response.list_orders() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            v2 = await response.parse()
            assert_matches_type(V2ListOrdersResponse, v2, path=["response"])

        assert cast(Any, response.is_closed) is True
