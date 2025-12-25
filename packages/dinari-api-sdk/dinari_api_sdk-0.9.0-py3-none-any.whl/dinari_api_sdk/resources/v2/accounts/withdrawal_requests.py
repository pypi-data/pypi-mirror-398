# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ...._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ...._utils import maybe_transform, async_maybe_transform
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.v2.accounts import withdrawal_request_list_params, withdrawal_request_create_params
from ....types.v2.accounts.withdrawal_request import WithdrawalRequest
from ....types.v2.accounts.withdrawal_request_list_response import WithdrawalRequestListResponse

__all__ = ["WithdrawalRequestsResource", "AsyncWithdrawalRequestsResource"]


class WithdrawalRequestsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> WithdrawalRequestsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return WithdrawalRequestsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> WithdrawalRequestsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#with_streaming_response
        """
        return WithdrawalRequestsResourceWithStreamingResponse(self)

    def create(
        self,
        account_id: str,
        *,
        payment_token_quantity: float,
        recipient_account_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WithdrawalRequest:
        """
        Request to withdraw USD+ payment tokens from a managed `Account` and send the
        equivalent amount of USDC to the specified recipient `Account`.

        The recipient `Account` must belong to the same `Entity` as the managed
        `Account`.

        Args:
          payment_token_quantity: Amount of USD+ payment tokens to be withdrawn. Must be greater than 0 and have
              at most 6 decimal places.

          recipient_account_id: ID of the `Account` that will receive payment tokens from the `Withdrawal`.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return self._post(
            f"/api/v2/accounts/{account_id}/withdrawal_requests",
            body=maybe_transform(
                {
                    "payment_token_quantity": payment_token_quantity,
                    "recipient_account_id": recipient_account_id,
                },
                withdrawal_request_create_params.WithdrawalRequestCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WithdrawalRequest,
        )

    def retrieve(
        self,
        withdrawal_request_id: str,
        *,
        account_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WithdrawalRequest:
        """
        Get a specific `WithdrawalRequest` by its ID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        if not withdrawal_request_id:
            raise ValueError(
                f"Expected a non-empty value for `withdrawal_request_id` but received {withdrawal_request_id!r}"
            )
        return self._get(
            f"/api/v2/accounts/{account_id}/withdrawal_requests/{withdrawal_request_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WithdrawalRequest,
        )

    def list(
        self,
        account_id: str,
        *,
        page: int | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WithdrawalRequestListResponse:
        """
        List `WithdrawalRequests` under the `Account`, sorted by most recent.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return self._get(
            f"/api/v2/accounts/{account_id}/withdrawal_requests",
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
                    withdrawal_request_list_params.WithdrawalRequestListParams,
                ),
            ),
            cast_to=WithdrawalRequestListResponse,
        )


class AsyncWithdrawalRequestsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncWithdrawalRequestsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncWithdrawalRequestsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncWithdrawalRequestsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#with_streaming_response
        """
        return AsyncWithdrawalRequestsResourceWithStreamingResponse(self)

    async def create(
        self,
        account_id: str,
        *,
        payment_token_quantity: float,
        recipient_account_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WithdrawalRequest:
        """
        Request to withdraw USD+ payment tokens from a managed `Account` and send the
        equivalent amount of USDC to the specified recipient `Account`.

        The recipient `Account` must belong to the same `Entity` as the managed
        `Account`.

        Args:
          payment_token_quantity: Amount of USD+ payment tokens to be withdrawn. Must be greater than 0 and have
              at most 6 decimal places.

          recipient_account_id: ID of the `Account` that will receive payment tokens from the `Withdrawal`.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return await self._post(
            f"/api/v2/accounts/{account_id}/withdrawal_requests",
            body=await async_maybe_transform(
                {
                    "payment_token_quantity": payment_token_quantity,
                    "recipient_account_id": recipient_account_id,
                },
                withdrawal_request_create_params.WithdrawalRequestCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WithdrawalRequest,
        )

    async def retrieve(
        self,
        withdrawal_request_id: str,
        *,
        account_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WithdrawalRequest:
        """
        Get a specific `WithdrawalRequest` by its ID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        if not withdrawal_request_id:
            raise ValueError(
                f"Expected a non-empty value for `withdrawal_request_id` but received {withdrawal_request_id!r}"
            )
        return await self._get(
            f"/api/v2/accounts/{account_id}/withdrawal_requests/{withdrawal_request_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WithdrawalRequest,
        )

    async def list(
        self,
        account_id: str,
        *,
        page: int | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WithdrawalRequestListResponse:
        """
        List `WithdrawalRequests` under the `Account`, sorted by most recent.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return await self._get(
            f"/api/v2/accounts/{account_id}/withdrawal_requests",
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
                    withdrawal_request_list_params.WithdrawalRequestListParams,
                ),
            ),
            cast_to=WithdrawalRequestListResponse,
        )


class WithdrawalRequestsResourceWithRawResponse:
    def __init__(self, withdrawal_requests: WithdrawalRequestsResource) -> None:
        self._withdrawal_requests = withdrawal_requests

        self.create = to_raw_response_wrapper(
            withdrawal_requests.create,
        )
        self.retrieve = to_raw_response_wrapper(
            withdrawal_requests.retrieve,
        )
        self.list = to_raw_response_wrapper(
            withdrawal_requests.list,
        )


class AsyncWithdrawalRequestsResourceWithRawResponse:
    def __init__(self, withdrawal_requests: AsyncWithdrawalRequestsResource) -> None:
        self._withdrawal_requests = withdrawal_requests

        self.create = async_to_raw_response_wrapper(
            withdrawal_requests.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            withdrawal_requests.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            withdrawal_requests.list,
        )


class WithdrawalRequestsResourceWithStreamingResponse:
    def __init__(self, withdrawal_requests: WithdrawalRequestsResource) -> None:
        self._withdrawal_requests = withdrawal_requests

        self.create = to_streamed_response_wrapper(
            withdrawal_requests.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            withdrawal_requests.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            withdrawal_requests.list,
        )


class AsyncWithdrawalRequestsResourceWithStreamingResponse:
    def __init__(self, withdrawal_requests: AsyncWithdrawalRequestsResource) -> None:
        self._withdrawal_requests = withdrawal_requests

        self.create = async_to_streamed_response_wrapper(
            withdrawal_requests.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            withdrawal_requests.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            withdrawal_requests.list,
        )
