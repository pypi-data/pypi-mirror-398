# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

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
from ....types.v2.accounts import withdrawal_list_params
from ....types.v2.accounts.withdrawal import Withdrawal
from ....types.v2.accounts.withdrawal_list_response import WithdrawalListResponse

__all__ = ["WithdrawalsResource", "AsyncWithdrawalsResource"]


class WithdrawalsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> WithdrawalsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return WithdrawalsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> WithdrawalsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#with_streaming_response
        """
        return WithdrawalsResourceWithStreamingResponse(self)

    def retrieve(
        self,
        withdrawal_id: str,
        *,
        account_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Withdrawal:
        """
        Get a specific `Withdrawal` by its ID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        if not withdrawal_id:
            raise ValueError(f"Expected a non-empty value for `withdrawal_id` but received {withdrawal_id!r}")
        return self._get(
            f"/api/v2/accounts/{account_id}/withdrawals/{withdrawal_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Withdrawal,
        )

    def list(
        self,
        account_id: str,
        *,
        page: int | Omit = omit,
        page_size: int | Omit = omit,
        withdrawal_request_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WithdrawalListResponse:
        """
        Get a list of all `Withdrawals` under the `Account`, sorted by most recent.

        Args:
          withdrawal_request_id: ID of the `WithdrawalRequest` to find `Withdrawals` for.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return self._get(
            f"/api/v2/accounts/{account_id}/withdrawals",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "page": page,
                        "page_size": page_size,
                        "withdrawal_request_id": withdrawal_request_id,
                    },
                    withdrawal_list_params.WithdrawalListParams,
                ),
            ),
            cast_to=WithdrawalListResponse,
        )


class AsyncWithdrawalsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncWithdrawalsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncWithdrawalsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncWithdrawalsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#with_streaming_response
        """
        return AsyncWithdrawalsResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        withdrawal_id: str,
        *,
        account_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Withdrawal:
        """
        Get a specific `Withdrawal` by its ID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        if not withdrawal_id:
            raise ValueError(f"Expected a non-empty value for `withdrawal_id` but received {withdrawal_id!r}")
        return await self._get(
            f"/api/v2/accounts/{account_id}/withdrawals/{withdrawal_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Withdrawal,
        )

    async def list(
        self,
        account_id: str,
        *,
        page: int | Omit = omit,
        page_size: int | Omit = omit,
        withdrawal_request_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WithdrawalListResponse:
        """
        Get a list of all `Withdrawals` under the `Account`, sorted by most recent.

        Args:
          withdrawal_request_id: ID of the `WithdrawalRequest` to find `Withdrawals` for.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return await self._get(
            f"/api/v2/accounts/{account_id}/withdrawals",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "page": page,
                        "page_size": page_size,
                        "withdrawal_request_id": withdrawal_request_id,
                    },
                    withdrawal_list_params.WithdrawalListParams,
                ),
            ),
            cast_to=WithdrawalListResponse,
        )


class WithdrawalsResourceWithRawResponse:
    def __init__(self, withdrawals: WithdrawalsResource) -> None:
        self._withdrawals = withdrawals

        self.retrieve = to_raw_response_wrapper(
            withdrawals.retrieve,
        )
        self.list = to_raw_response_wrapper(
            withdrawals.list,
        )


class AsyncWithdrawalsResourceWithRawResponse:
    def __init__(self, withdrawals: AsyncWithdrawalsResource) -> None:
        self._withdrawals = withdrawals

        self.retrieve = async_to_raw_response_wrapper(
            withdrawals.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            withdrawals.list,
        )


class WithdrawalsResourceWithStreamingResponse:
    def __init__(self, withdrawals: WithdrawalsResource) -> None:
        self._withdrawals = withdrawals

        self.retrieve = to_streamed_response_wrapper(
            withdrawals.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            withdrawals.list,
        )


class AsyncWithdrawalsResourceWithStreamingResponse:
    def __init__(self, withdrawals: AsyncWithdrawalsResource) -> None:
        self._withdrawals = withdrawals

        self.retrieve = async_to_streamed_response_wrapper(
            withdrawals.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            withdrawals.list,
        )
