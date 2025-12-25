# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from dinari_api_sdk import Dinari, AsyncDinari
from dinari_api_sdk.types.v2.accounts import (
    OrderRequest,
    OrderRequestListResponse,
    OrderRequestGetFeeQuoteResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestOrderRequests:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Dinari) -> None:
        order_request = client.v2.accounts.order_requests.retrieve(
            order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Dinari) -> None:
        response = client.v2.accounts.order_requests.with_raw_response.retrieve(
            order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        order_request = response.parse()
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Dinari) -> None:
        with client.v2.accounts.order_requests.with_streaming_response.retrieve(
            order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            order_request = response.parse()
            assert_matches_type(OrderRequest, order_request, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Dinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.v2.accounts.order_requests.with_raw_response.retrieve(
                order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                account_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `order_request_id` but received ''"):
            client.v2.accounts.order_requests.with_raw_response.retrieve(
                order_request_id="",
                account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Dinari) -> None:
        order_request = client.v2.accounts.order_requests.list(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(OrderRequestListResponse, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Dinari) -> None:
        order_request = client.v2.accounts.order_requests.list(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            client_order_id="client_order_id",
            order_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            page=1,
            page_size=1,
        )
        assert_matches_type(OrderRequestListResponse, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Dinari) -> None:
        response = client.v2.accounts.order_requests.with_raw_response.list(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        order_request = response.parse()
        assert_matches_type(OrderRequestListResponse, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Dinari) -> None:
        with client.v2.accounts.order_requests.with_streaming_response.list(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            order_request = response.parse()
            assert_matches_type(OrderRequestListResponse, order_request, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: Dinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.v2.accounts.order_requests.with_raw_response.list(
                account_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_limit_buy(self, client: Dinari) -> None:
        order_request = client.v2.accounts.order_requests.create_limit_buy(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            asset_quantity=0,
            limit_price=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_limit_buy_with_all_params(self, client: Dinari) -> None:
        order_request = client.v2.accounts.order_requests.create_limit_buy(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            asset_quantity=0,
            limit_price=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            client_order_id="client_order_id",
            recipient_account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create_limit_buy(self, client: Dinari) -> None:
        response = client.v2.accounts.order_requests.with_raw_response.create_limit_buy(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            asset_quantity=0,
            limit_price=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        order_request = response.parse()
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create_limit_buy(self, client: Dinari) -> None:
        with client.v2.accounts.order_requests.with_streaming_response.create_limit_buy(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            asset_quantity=0,
            limit_price=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            order_request = response.parse()
            assert_matches_type(OrderRequest, order_request, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_create_limit_buy(self, client: Dinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.v2.accounts.order_requests.with_raw_response.create_limit_buy(
                account_id="",
                asset_quantity=0,
                limit_price=0,
                stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_limit_sell(self, client: Dinari) -> None:
        order_request = client.v2.accounts.order_requests.create_limit_sell(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            asset_quantity=0,
            limit_price=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_limit_sell_with_all_params(self, client: Dinari) -> None:
        order_request = client.v2.accounts.order_requests.create_limit_sell(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            asset_quantity=0,
            limit_price=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            client_order_id="client_order_id",
            payment_token_address="payment_token_address",
            recipient_account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create_limit_sell(self, client: Dinari) -> None:
        response = client.v2.accounts.order_requests.with_raw_response.create_limit_sell(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            asset_quantity=0,
            limit_price=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        order_request = response.parse()
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create_limit_sell(self, client: Dinari) -> None:
        with client.v2.accounts.order_requests.with_streaming_response.create_limit_sell(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            asset_quantity=0,
            limit_price=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            order_request = response.parse()
            assert_matches_type(OrderRequest, order_request, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_create_limit_sell(self, client: Dinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.v2.accounts.order_requests.with_raw_response.create_limit_sell(
                account_id="",
                asset_quantity=0,
                limit_price=0,
                stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_market_buy(self, client: Dinari) -> None:
        order_request = client.v2.accounts.order_requests.create_market_buy(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            payment_amount=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_market_buy_with_all_params(self, client: Dinari) -> None:
        order_request = client.v2.accounts.order_requests.create_market_buy(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            payment_amount=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            client_order_id="client_order_id",
            recipient_account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create_market_buy(self, client: Dinari) -> None:
        response = client.v2.accounts.order_requests.with_raw_response.create_market_buy(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            payment_amount=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        order_request = response.parse()
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create_market_buy(self, client: Dinari) -> None:
        with client.v2.accounts.order_requests.with_streaming_response.create_market_buy(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            payment_amount=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            order_request = response.parse()
            assert_matches_type(OrderRequest, order_request, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_create_market_buy(self, client: Dinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.v2.accounts.order_requests.with_raw_response.create_market_buy(
                account_id="",
                payment_amount=0,
                stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_market_sell(self, client: Dinari) -> None:
        order_request = client.v2.accounts.order_requests.create_market_sell(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            asset_quantity=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_market_sell_with_all_params(self, client: Dinari) -> None:
        order_request = client.v2.accounts.order_requests.create_market_sell(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            asset_quantity=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            client_order_id="client_order_id",
            payment_token_address="payment_token_address",
            recipient_account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create_market_sell(self, client: Dinari) -> None:
        response = client.v2.accounts.order_requests.with_raw_response.create_market_sell(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            asset_quantity=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        order_request = response.parse()
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create_market_sell(self, client: Dinari) -> None:
        with client.v2.accounts.order_requests.with_streaming_response.create_market_sell(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            asset_quantity=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            order_request = response.parse()
            assert_matches_type(OrderRequest, order_request, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_create_market_sell(self, client: Dinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.v2.accounts.order_requests.with_raw_response.create_market_sell(
                account_id="",
                asset_quantity=0,
                stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_fee_quote(self, client: Dinari) -> None:
        order_request = client.v2.accounts.order_requests.get_fee_quote(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            order_side="BUY",
            order_type="MARKET",
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(OrderRequestGetFeeQuoteResponse, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_fee_quote_with_all_params(self, client: Dinari) -> None:
        order_request = client.v2.accounts.order_requests.get_fee_quote(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            order_side="BUY",
            order_type="MARKET",
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            asset_token_quantity=0,
            chain_id="eip155:1",
            limit_price=0,
            payment_token_address="payment_token_address",
            payment_token_quantity=0,
        )
        assert_matches_type(OrderRequestGetFeeQuoteResponse, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_fee_quote(self, client: Dinari) -> None:
        response = client.v2.accounts.order_requests.with_raw_response.get_fee_quote(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            order_side="BUY",
            order_type="MARKET",
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        order_request = response.parse()
        assert_matches_type(OrderRequestGetFeeQuoteResponse, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_fee_quote(self, client: Dinari) -> None:
        with client.v2.accounts.order_requests.with_streaming_response.get_fee_quote(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            order_side="BUY",
            order_type="MARKET",
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            order_request = response.parse()
            assert_matches_type(OrderRequestGetFeeQuoteResponse, order_request, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_get_fee_quote(self, client: Dinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.v2.accounts.order_requests.with_raw_response.get_fee_quote(
                account_id="",
                order_side="BUY",
                order_type="MARKET",
                stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            )


class TestAsyncOrderRequests:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncDinari) -> None:
        order_request = await async_client.v2.accounts.order_requests.retrieve(
            order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.accounts.order_requests.with_raw_response.retrieve(
            order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        order_request = await response.parse()
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.accounts.order_requests.with_streaming_response.retrieve(
            order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            order_request = await response.parse()
            assert_matches_type(OrderRequest, order_request, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncDinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.v2.accounts.order_requests.with_raw_response.retrieve(
                order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                account_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `order_request_id` but received ''"):
            await async_client.v2.accounts.order_requests.with_raw_response.retrieve(
                order_request_id="",
                account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncDinari) -> None:
        order_request = await async_client.v2.accounts.order_requests.list(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(OrderRequestListResponse, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncDinari) -> None:
        order_request = await async_client.v2.accounts.order_requests.list(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            client_order_id="client_order_id",
            order_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            order_request_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            page=1,
            page_size=1,
        )
        assert_matches_type(OrderRequestListResponse, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.accounts.order_requests.with_raw_response.list(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        order_request = await response.parse()
        assert_matches_type(OrderRequestListResponse, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.accounts.order_requests.with_streaming_response.list(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            order_request = await response.parse()
            assert_matches_type(OrderRequestListResponse, order_request, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncDinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.v2.accounts.order_requests.with_raw_response.list(
                account_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_limit_buy(self, async_client: AsyncDinari) -> None:
        order_request = await async_client.v2.accounts.order_requests.create_limit_buy(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            asset_quantity=0,
            limit_price=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_limit_buy_with_all_params(self, async_client: AsyncDinari) -> None:
        order_request = await async_client.v2.accounts.order_requests.create_limit_buy(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            asset_quantity=0,
            limit_price=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            client_order_id="client_order_id",
            recipient_account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create_limit_buy(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.accounts.order_requests.with_raw_response.create_limit_buy(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            asset_quantity=0,
            limit_price=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        order_request = await response.parse()
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create_limit_buy(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.accounts.order_requests.with_streaming_response.create_limit_buy(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            asset_quantity=0,
            limit_price=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            order_request = await response.parse()
            assert_matches_type(OrderRequest, order_request, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_create_limit_buy(self, async_client: AsyncDinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.v2.accounts.order_requests.with_raw_response.create_limit_buy(
                account_id="",
                asset_quantity=0,
                limit_price=0,
                stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_limit_sell(self, async_client: AsyncDinari) -> None:
        order_request = await async_client.v2.accounts.order_requests.create_limit_sell(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            asset_quantity=0,
            limit_price=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_limit_sell_with_all_params(self, async_client: AsyncDinari) -> None:
        order_request = await async_client.v2.accounts.order_requests.create_limit_sell(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            asset_quantity=0,
            limit_price=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            client_order_id="client_order_id",
            payment_token_address="payment_token_address",
            recipient_account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create_limit_sell(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.accounts.order_requests.with_raw_response.create_limit_sell(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            asset_quantity=0,
            limit_price=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        order_request = await response.parse()
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create_limit_sell(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.accounts.order_requests.with_streaming_response.create_limit_sell(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            asset_quantity=0,
            limit_price=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            order_request = await response.parse()
            assert_matches_type(OrderRequest, order_request, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_create_limit_sell(self, async_client: AsyncDinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.v2.accounts.order_requests.with_raw_response.create_limit_sell(
                account_id="",
                asset_quantity=0,
                limit_price=0,
                stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_market_buy(self, async_client: AsyncDinari) -> None:
        order_request = await async_client.v2.accounts.order_requests.create_market_buy(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            payment_amount=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_market_buy_with_all_params(self, async_client: AsyncDinari) -> None:
        order_request = await async_client.v2.accounts.order_requests.create_market_buy(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            payment_amount=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            client_order_id="client_order_id",
            recipient_account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create_market_buy(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.accounts.order_requests.with_raw_response.create_market_buy(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            payment_amount=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        order_request = await response.parse()
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create_market_buy(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.accounts.order_requests.with_streaming_response.create_market_buy(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            payment_amount=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            order_request = await response.parse()
            assert_matches_type(OrderRequest, order_request, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_create_market_buy(self, async_client: AsyncDinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.v2.accounts.order_requests.with_raw_response.create_market_buy(
                account_id="",
                payment_amount=0,
                stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_market_sell(self, async_client: AsyncDinari) -> None:
        order_request = await async_client.v2.accounts.order_requests.create_market_sell(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            asset_quantity=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_market_sell_with_all_params(self, async_client: AsyncDinari) -> None:
        order_request = await async_client.v2.accounts.order_requests.create_market_sell(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            asset_quantity=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            client_order_id="client_order_id",
            payment_token_address="payment_token_address",
            recipient_account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create_market_sell(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.accounts.order_requests.with_raw_response.create_market_sell(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            asset_quantity=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        order_request = await response.parse()
        assert_matches_type(OrderRequest, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create_market_sell(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.accounts.order_requests.with_streaming_response.create_market_sell(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            asset_quantity=0,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            order_request = await response.parse()
            assert_matches_type(OrderRequest, order_request, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_create_market_sell(self, async_client: AsyncDinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.v2.accounts.order_requests.with_raw_response.create_market_sell(
                account_id="",
                asset_quantity=0,
                stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_fee_quote(self, async_client: AsyncDinari) -> None:
        order_request = await async_client.v2.accounts.order_requests.get_fee_quote(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            order_side="BUY",
            order_type="MARKET",
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(OrderRequestGetFeeQuoteResponse, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_fee_quote_with_all_params(self, async_client: AsyncDinari) -> None:
        order_request = await async_client.v2.accounts.order_requests.get_fee_quote(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            order_side="BUY",
            order_type="MARKET",
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            asset_token_quantity=0,
            chain_id="eip155:1",
            limit_price=0,
            payment_token_address="payment_token_address",
            payment_token_quantity=0,
        )
        assert_matches_type(OrderRequestGetFeeQuoteResponse, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_fee_quote(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.accounts.order_requests.with_raw_response.get_fee_quote(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            order_side="BUY",
            order_type="MARKET",
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        order_request = await response.parse()
        assert_matches_type(OrderRequestGetFeeQuoteResponse, order_request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_fee_quote(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.accounts.order_requests.with_streaming_response.get_fee_quote(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            order_side="BUY",
            order_type="MARKET",
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            order_request = await response.parse()
            assert_matches_type(OrderRequestGetFeeQuoteResponse, order_request, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_get_fee_quote(self, async_client: AsyncDinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.v2.accounts.order_requests.with_raw_response.get_fee_quote(
                account_id="",
                order_side="BUY",
                order_type="MARKET",
                stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            )
