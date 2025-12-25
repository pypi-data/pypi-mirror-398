# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ...._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from ...._utils import maybe_transform, async_maybe_transform
from ...._compat import cached_property
from ....types.v2 import Chain
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.v2.chain import Chain
from ....types.v2.accounts import order_list_params, order_batch_cancel_params, order_get_fulfillments_params
from ....types.v2.accounts.order import Order
from ....types.v2.accounts.order_list_response import OrderListResponse
from ....types.v2.accounts.order_batch_cancel_response import OrderBatchCancelResponse
from ....types.v2.accounts.order_get_fulfillments_response import OrderGetFulfillmentsResponse

__all__ = ["OrdersResource", "AsyncOrdersResource"]


class OrdersResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> OrdersResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return OrdersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> OrdersResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#with_streaming_response
        """
        return OrdersResourceWithStreamingResponse(self)

    def retrieve(
        self,
        order_id: str,
        *,
        account_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Order:
        """
        Get a specific `Order` by its ID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        if not order_id:
            raise ValueError(f"Expected a non-empty value for `order_id` but received {order_id!r}")
        return self._get(
            f"/api/v2/accounts/{account_id}/orders/{order_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Order,
        )

    def list(
        self,
        account_id: str,
        *,
        chain_id: Optional[Chain] | Omit = omit,
        client_order_id: Optional[str] | Omit = omit,
        order_transaction_hash: Optional[str] | Omit = omit,
        page: int | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OrderListResponse:
        """Get a list of all `Orders` under the `Account`.

        Optionally `Orders` can be
        filtered by chain ID, transaction hash, or client order ID.

        Args:
          chain_id: CAIP-2 formatted chain ID of the blockchain the `Order` was made on.

          client_order_id: Customer-supplied identifier to search for `Order`s.

          order_transaction_hash: Transaction hash of the `Order`.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return self._get(
            f"/api/v2/accounts/{account_id}/orders",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "chain_id": chain_id,
                        "client_order_id": client_order_id,
                        "order_transaction_hash": order_transaction_hash,
                        "page": page,
                        "page_size": page_size,
                    },
                    order_list_params.OrderListParams,
                ),
            ),
            cast_to=OrderListResponse,
        )

    def batch_cancel(
        self,
        account_id: str,
        *,
        order_ids: SequenceNotStr[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OrderBatchCancelResponse:
        """Cancel multiple `Orders` by their IDs in a single request.

        Note that this
        requires the `Order` IDs, not the `OrderRequest` IDs. Once you submit a
        cancellation request, it cannot be undone. Be advised that orders with a status
        of PENDING_FILL, PENDING_ESCROW, FILLED, REJECTED, or CANCELLED cannot be
        cancelled.

        `Order` cancellation is not guaranteed nor is it immediate. The `Orders` may
        still be executed if the cancellation request is not received in time.

        The response will indicate which orders were successfully queued to cancel and
        which failed to queue. Check the status using the "Get Order by ID" endpoint to
        confirm whether individual `Orders` have been cancelled.

        Args:
          order_ids: List of `Order` IDs to cancel

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return self._post(
            f"/api/v2/accounts/{account_id}/orders/cancel",
            body=maybe_transform({"order_ids": order_ids}, order_batch_cancel_params.OrderBatchCancelParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OrderBatchCancelResponse,
        )

    def cancel(
        self,
        order_id: str,
        *,
        account_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Order:
        """Cancel an `Order` by its ID.

        Note that this requires the `Order` ID, not the
        `OrderRequest` ID. Once you submit a cancellation request, it cannot be undone.
        Be advised that orders with a status of PENDING_FILL, PENDING_ESCROW, FILLED,
        REJECTED, or CANCELLED cannot be cancelled.

        `Order` cancellation is not guaranteed nor is it immediate. The `Order` may
        still be executed if the cancellation request is not received in time.

        Check the status using the "Get Order by ID" endpoint to confirm whether the
        `Order` has been cancelled.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        if not order_id:
            raise ValueError(f"Expected a non-empty value for `order_id` but received {order_id!r}")
        return self._post(
            f"/api/v2/accounts/{account_id}/orders/{order_id}/cancel",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Order,
        )

    def get_fulfillments(
        self,
        order_id: str,
        *,
        account_id: str,
        page: int | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OrderGetFulfillmentsResponse:
        """
        Get `OrderFulfillments` for a specific `Order`.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        if not order_id:
            raise ValueError(f"Expected a non-empty value for `order_id` but received {order_id!r}")
        return self._get(
            f"/api/v2/accounts/{account_id}/orders/{order_id}/fulfillments",
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
                    order_get_fulfillments_params.OrderGetFulfillmentsParams,
                ),
            ),
            cast_to=OrderGetFulfillmentsResponse,
        )


class AsyncOrdersResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncOrdersResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncOrdersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncOrdersResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#with_streaming_response
        """
        return AsyncOrdersResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        order_id: str,
        *,
        account_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Order:
        """
        Get a specific `Order` by its ID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        if not order_id:
            raise ValueError(f"Expected a non-empty value for `order_id` but received {order_id!r}")
        return await self._get(
            f"/api/v2/accounts/{account_id}/orders/{order_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Order,
        )

    async def list(
        self,
        account_id: str,
        *,
        chain_id: Optional[Chain] | Omit = omit,
        client_order_id: Optional[str] | Omit = omit,
        order_transaction_hash: Optional[str] | Omit = omit,
        page: int | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OrderListResponse:
        """Get a list of all `Orders` under the `Account`.

        Optionally `Orders` can be
        filtered by chain ID, transaction hash, or client order ID.

        Args:
          chain_id: CAIP-2 formatted chain ID of the blockchain the `Order` was made on.

          client_order_id: Customer-supplied identifier to search for `Order`s.

          order_transaction_hash: Transaction hash of the `Order`.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return await self._get(
            f"/api/v2/accounts/{account_id}/orders",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "chain_id": chain_id,
                        "client_order_id": client_order_id,
                        "order_transaction_hash": order_transaction_hash,
                        "page": page,
                        "page_size": page_size,
                    },
                    order_list_params.OrderListParams,
                ),
            ),
            cast_to=OrderListResponse,
        )

    async def batch_cancel(
        self,
        account_id: str,
        *,
        order_ids: SequenceNotStr[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OrderBatchCancelResponse:
        """Cancel multiple `Orders` by their IDs in a single request.

        Note that this
        requires the `Order` IDs, not the `OrderRequest` IDs. Once you submit a
        cancellation request, it cannot be undone. Be advised that orders with a status
        of PENDING_FILL, PENDING_ESCROW, FILLED, REJECTED, or CANCELLED cannot be
        cancelled.

        `Order` cancellation is not guaranteed nor is it immediate. The `Orders` may
        still be executed if the cancellation request is not received in time.

        The response will indicate which orders were successfully queued to cancel and
        which failed to queue. Check the status using the "Get Order by ID" endpoint to
        confirm whether individual `Orders` have been cancelled.

        Args:
          order_ids: List of `Order` IDs to cancel

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return await self._post(
            f"/api/v2/accounts/{account_id}/orders/cancel",
            body=await async_maybe_transform(
                {"order_ids": order_ids}, order_batch_cancel_params.OrderBatchCancelParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OrderBatchCancelResponse,
        )

    async def cancel(
        self,
        order_id: str,
        *,
        account_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Order:
        """Cancel an `Order` by its ID.

        Note that this requires the `Order` ID, not the
        `OrderRequest` ID. Once you submit a cancellation request, it cannot be undone.
        Be advised that orders with a status of PENDING_FILL, PENDING_ESCROW, FILLED,
        REJECTED, or CANCELLED cannot be cancelled.

        `Order` cancellation is not guaranteed nor is it immediate. The `Order` may
        still be executed if the cancellation request is not received in time.

        Check the status using the "Get Order by ID" endpoint to confirm whether the
        `Order` has been cancelled.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        if not order_id:
            raise ValueError(f"Expected a non-empty value for `order_id` but received {order_id!r}")
        return await self._post(
            f"/api/v2/accounts/{account_id}/orders/{order_id}/cancel",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Order,
        )

    async def get_fulfillments(
        self,
        order_id: str,
        *,
        account_id: str,
        page: int | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OrderGetFulfillmentsResponse:
        """
        Get `OrderFulfillments` for a specific `Order`.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        if not order_id:
            raise ValueError(f"Expected a non-empty value for `order_id` but received {order_id!r}")
        return await self._get(
            f"/api/v2/accounts/{account_id}/orders/{order_id}/fulfillments",
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
                    order_get_fulfillments_params.OrderGetFulfillmentsParams,
                ),
            ),
            cast_to=OrderGetFulfillmentsResponse,
        )


class OrdersResourceWithRawResponse:
    def __init__(self, orders: OrdersResource) -> None:
        self._orders = orders

        self.retrieve = to_raw_response_wrapper(
            orders.retrieve,
        )
        self.list = to_raw_response_wrapper(
            orders.list,
        )
        self.batch_cancel = to_raw_response_wrapper(
            orders.batch_cancel,
        )
        self.cancel = to_raw_response_wrapper(
            orders.cancel,
        )
        self.get_fulfillments = to_raw_response_wrapper(
            orders.get_fulfillments,
        )


class AsyncOrdersResourceWithRawResponse:
    def __init__(self, orders: AsyncOrdersResource) -> None:
        self._orders = orders

        self.retrieve = async_to_raw_response_wrapper(
            orders.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            orders.list,
        )
        self.batch_cancel = async_to_raw_response_wrapper(
            orders.batch_cancel,
        )
        self.cancel = async_to_raw_response_wrapper(
            orders.cancel,
        )
        self.get_fulfillments = async_to_raw_response_wrapper(
            orders.get_fulfillments,
        )


class OrdersResourceWithStreamingResponse:
    def __init__(self, orders: OrdersResource) -> None:
        self._orders = orders

        self.retrieve = to_streamed_response_wrapper(
            orders.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            orders.list,
        )
        self.batch_cancel = to_streamed_response_wrapper(
            orders.batch_cancel,
        )
        self.cancel = to_streamed_response_wrapper(
            orders.cancel,
        )
        self.get_fulfillments = to_streamed_response_wrapper(
            orders.get_fulfillments,
        )


class AsyncOrdersResourceWithStreamingResponse:
    def __init__(self, orders: AsyncOrdersResource) -> None:
        self._orders = orders

        self.retrieve = async_to_streamed_response_wrapper(
            orders.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            orders.list,
        )
        self.batch_cancel = async_to_streamed_response_wrapper(
            orders.batch_cancel,
        )
        self.cancel = async_to_streamed_response_wrapper(
            orders.cancel,
        )
        self.get_fulfillments = async_to_streamed_response_wrapper(
            orders.get_fulfillments,
        )
