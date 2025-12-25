# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ....._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ....._utils import maybe_transform, async_maybe_transform
from ....._compat import cached_property
from ....._resource import SyncAPIResource, AsyncAPIResource
from ....._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ....._base_client import make_request_options
from .....types.v2.market_data.stocks import split_list_params, split_list_for_stock_params
from .....types.v2.market_data.stocks.split_list_response import SplitListResponse
from .....types.v2.market_data.stocks.split_list_for_stock_response import SplitListForStockResponse

__all__ = ["SplitsResource", "AsyncSplitsResource"]


class SplitsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SplitsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return SplitsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SplitsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#with_streaming_response
        """
        return SplitsResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        page: int | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SplitListResponse:
        """Get a list of stock splits for `Stocks` available for trade via Dinari.

        The
        splits are ordered by the date they were created, with the most recent split
        first.

        In an example 10-for-1 stock split, trading will be halted for the stock at the
        end of the `payable_date`, as the split transitions from `PENDING` to
        `IN_PROGRESS`. This usually occurs over a weekend to minimize trading
        disruptions. Each share of stock owned by a shareholder will then be converted
        into 10 shares, and the split becomes `COMPLETE` as trading resumes on the
        `ex_date` with new split-adjusted prices.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/api/v2/market_data/stocks/splits",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "page": page,
                        "page_size": page_size,
                    },
                    split_list_params.SplitListParams,
                ),
            ),
            cast_to=SplitListResponse,
        )

    def list_for_stock(
        self,
        stock_id: str,
        *,
        page: int | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SplitListForStockResponse:
        """Get a list of stock splits for a specific `Stock`.

        The splits are ordered by the
        date they were created, with the most recent split first.

        In an example 10-for-1 stock split, trading will be halted for the stock at the
        end of the `payable_date`, as the split transitions from `PENDING` to
        `IN_PROGRESS`. This usually occurs over a weekend to minimize trading
        disruptions. Each share of stock owned by a shareholder will then be converted
        into 10 shares, and the split becomes `COMPLETE` as trading resumes on the
        `ex_date` with new split-adjusted prices.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not stock_id:
            raise ValueError(f"Expected a non-empty value for `stock_id` but received {stock_id!r}")
        return self._get(
            f"/api/v2/market_data/stocks/{stock_id}/splits",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "page": page,
                        "page_size": page_size,
                    },
                    split_list_for_stock_params.SplitListForStockParams,
                ),
            ),
            cast_to=SplitListForStockResponse,
        )


class AsyncSplitsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSplitsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncSplitsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSplitsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#with_streaming_response
        """
        return AsyncSplitsResourceWithStreamingResponse(self)

    async def list(
        self,
        *,
        page: int | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SplitListResponse:
        """Get a list of stock splits for `Stocks` available for trade via Dinari.

        The
        splits are ordered by the date they were created, with the most recent split
        first.

        In an example 10-for-1 stock split, trading will be halted for the stock at the
        end of the `payable_date`, as the split transitions from `PENDING` to
        `IN_PROGRESS`. This usually occurs over a weekend to minimize trading
        disruptions. Each share of stock owned by a shareholder will then be converted
        into 10 shares, and the split becomes `COMPLETE` as trading resumes on the
        `ex_date` with new split-adjusted prices.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/api/v2/market_data/stocks/splits",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "page": page,
                        "page_size": page_size,
                    },
                    split_list_params.SplitListParams,
                ),
            ),
            cast_to=SplitListResponse,
        )

    async def list_for_stock(
        self,
        stock_id: str,
        *,
        page: int | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SplitListForStockResponse:
        """Get a list of stock splits for a specific `Stock`.

        The splits are ordered by the
        date they were created, with the most recent split first.

        In an example 10-for-1 stock split, trading will be halted for the stock at the
        end of the `payable_date`, as the split transitions from `PENDING` to
        `IN_PROGRESS`. This usually occurs over a weekend to minimize trading
        disruptions. Each share of stock owned by a shareholder will then be converted
        into 10 shares, and the split becomes `COMPLETE` as trading resumes on the
        `ex_date` with new split-adjusted prices.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not stock_id:
            raise ValueError(f"Expected a non-empty value for `stock_id` but received {stock_id!r}")
        return await self._get(
            f"/api/v2/market_data/stocks/{stock_id}/splits",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "page": page,
                        "page_size": page_size,
                    },
                    split_list_for_stock_params.SplitListForStockParams,
                ),
            ),
            cast_to=SplitListForStockResponse,
        )


class SplitsResourceWithRawResponse:
    def __init__(self, splits: SplitsResource) -> None:
        self._splits = splits

        self.list = to_raw_response_wrapper(
            splits.list,
        )
        self.list_for_stock = to_raw_response_wrapper(
            splits.list_for_stock,
        )


class AsyncSplitsResourceWithRawResponse:
    def __init__(self, splits: AsyncSplitsResource) -> None:
        self._splits = splits

        self.list = async_to_raw_response_wrapper(
            splits.list,
        )
        self.list_for_stock = async_to_raw_response_wrapper(
            splits.list_for_stock,
        )


class SplitsResourceWithStreamingResponse:
    def __init__(self, splits: SplitsResource) -> None:
        self._splits = splits

        self.list = to_streamed_response_wrapper(
            splits.list,
        )
        self.list_for_stock = to_streamed_response_wrapper(
            splits.list_for_stock,
        )


class AsyncSplitsResourceWithStreamingResponse:
    def __init__(self, splits: AsyncSplitsResource) -> None:
        self._splits = splits

        self.list = async_to_streamed_response_wrapper(
            splits.list,
        )
        self.list_for_stock = async_to_streamed_response_wrapper(
            splits.list_for_stock,
        )
