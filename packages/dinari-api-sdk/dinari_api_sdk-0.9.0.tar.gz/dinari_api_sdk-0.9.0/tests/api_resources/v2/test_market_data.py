# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from dinari_api_sdk import Dinari, AsyncDinari
from dinari_api_sdk.types.v2 import MarketDataRetrieveMarketHoursResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestMarketData:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_market_hours(self, client: Dinari) -> None:
        market_data = client.v2.market_data.retrieve_market_hours()
        assert_matches_type(MarketDataRetrieveMarketHoursResponse, market_data, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_market_hours(self, client: Dinari) -> None:
        response = client.v2.market_data.with_raw_response.retrieve_market_hours()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        market_data = response.parse()
        assert_matches_type(MarketDataRetrieveMarketHoursResponse, market_data, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_market_hours(self, client: Dinari) -> None:
        with client.v2.market_data.with_streaming_response.retrieve_market_hours() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            market_data = response.parse()
            assert_matches_type(MarketDataRetrieveMarketHoursResponse, market_data, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncMarketData:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_market_hours(self, async_client: AsyncDinari) -> None:
        market_data = await async_client.v2.market_data.retrieve_market_hours()
        assert_matches_type(MarketDataRetrieveMarketHoursResponse, market_data, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_market_hours(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.market_data.with_raw_response.retrieve_market_hours()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        market_data = await response.parse()
        assert_matches_type(MarketDataRetrieveMarketHoursResponse, market_data, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_market_hours(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.market_data.with_streaming_response.retrieve_market_hours() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            market_data = await response.parse()
            assert_matches_type(MarketDataRetrieveMarketHoursResponse, market_data, path=["response"])

        assert cast(Any, response.is_closed) is True
