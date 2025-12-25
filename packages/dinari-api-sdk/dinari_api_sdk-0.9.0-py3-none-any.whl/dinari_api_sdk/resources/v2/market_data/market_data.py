# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ...._types import Body, Query, Headers, NotGiven, not_given
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .stocks.stocks import (
    StocksResource,
    AsyncStocksResource,
    StocksResourceWithRawResponse,
    AsyncStocksResourceWithRawResponse,
    StocksResourceWithStreamingResponse,
    AsyncStocksResourceWithStreamingResponse,
)
from ...._base_client import make_request_options
from ....types.v2.market_data_retrieve_market_hours_response import MarketDataRetrieveMarketHoursResponse

__all__ = ["MarketDataResource", "AsyncMarketDataResource"]


class MarketDataResource(SyncAPIResource):
    @cached_property
    def stocks(self) -> StocksResource:
        return StocksResource(self._client)

    @cached_property
    def with_raw_response(self) -> MarketDataResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return MarketDataResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> MarketDataResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#with_streaming_response
        """
        return MarketDataResourceWithStreamingResponse(self)

    def retrieve_market_hours(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MarketDataRetrieveMarketHoursResponse:
        """
        Get the market hours for the current trading session and next open trading
        session.
        """
        return self._get(
            "/api/v2/market_data/market_hours/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MarketDataRetrieveMarketHoursResponse,
        )


class AsyncMarketDataResource(AsyncAPIResource):
    @cached_property
    def stocks(self) -> AsyncStocksResource:
        return AsyncStocksResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncMarketDataResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncMarketDataResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncMarketDataResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#with_streaming_response
        """
        return AsyncMarketDataResourceWithStreamingResponse(self)

    async def retrieve_market_hours(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MarketDataRetrieveMarketHoursResponse:
        """
        Get the market hours for the current trading session and next open trading
        session.
        """
        return await self._get(
            "/api/v2/market_data/market_hours/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MarketDataRetrieveMarketHoursResponse,
        )


class MarketDataResourceWithRawResponse:
    def __init__(self, market_data: MarketDataResource) -> None:
        self._market_data = market_data

        self.retrieve_market_hours = to_raw_response_wrapper(
            market_data.retrieve_market_hours,
        )

    @cached_property
    def stocks(self) -> StocksResourceWithRawResponse:
        return StocksResourceWithRawResponse(self._market_data.stocks)


class AsyncMarketDataResourceWithRawResponse:
    def __init__(self, market_data: AsyncMarketDataResource) -> None:
        self._market_data = market_data

        self.retrieve_market_hours = async_to_raw_response_wrapper(
            market_data.retrieve_market_hours,
        )

    @cached_property
    def stocks(self) -> AsyncStocksResourceWithRawResponse:
        return AsyncStocksResourceWithRawResponse(self._market_data.stocks)


class MarketDataResourceWithStreamingResponse:
    def __init__(self, market_data: MarketDataResource) -> None:
        self._market_data = market_data

        self.retrieve_market_hours = to_streamed_response_wrapper(
            market_data.retrieve_market_hours,
        )

    @cached_property
    def stocks(self) -> StocksResourceWithStreamingResponse:
        return StocksResourceWithStreamingResponse(self._market_data.stocks)


class AsyncMarketDataResourceWithStreamingResponse:
    def __init__(self, market_data: AsyncMarketDataResource) -> None:
        self._market_data = market_data

        self.retrieve_market_hours = async_to_streamed_response_wrapper(
            market_data.retrieve_market_hours,
        )

    @cached_property
    def stocks(self) -> AsyncStocksResourceWithStreamingResponse:
        return AsyncStocksResourceWithStreamingResponse(self._market_data.stocks)
