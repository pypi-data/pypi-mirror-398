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
from ....types.v2.accounts import token_transfer_list_params, token_transfer_create_params
from ....types.v2.accounts.token_transfer import TokenTransfer
from ....types.v2.accounts.token_transfer_list_response import TokenTransferListResponse

__all__ = ["TokenTransfersResource", "AsyncTokenTransfersResource"]


class TokenTransfersResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> TokenTransfersResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return TokenTransfersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> TokenTransfersResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#with_streaming_response
        """
        return TokenTransfersResourceWithStreamingResponse(self)

    def create(
        self,
        account_id: str,
        *,
        quantity: float,
        recipient_account_id: str,
        token_address: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TokenTransfer:
        """
        Creates a `TokenTransfer` from this `Account`.

        A `TokenTransfer` represents a transfer of tokens through the Dinari platform
        from one `Account` to another. As such, only `Account`s that are connected to
        Dinari-managed `Wallet`s can initiate `TokenTransfer`s.

        Args:
          quantity: Quantity of the token to transfer.

          recipient_account_id: ID of the recipient account to which the tokens will be transferred.

          token_address: Address of the token to transfer.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return self._post(
            f"/api/v2/accounts/{account_id}/token_transfers",
            body=maybe_transform(
                {
                    "quantity": quantity,
                    "recipient_account_id": recipient_account_id,
                    "token_address": token_address,
                },
                token_transfer_create_params.TokenTransferCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TokenTransfer,
        )

    def retrieve(
        self,
        transfer_id: str,
        *,
        account_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TokenTransfer:
        """
        Get a specific `TokenTransfer` made from this `Account` by its ID.

        A `TokenTransfer` represents a transfer of tokens through the Dinari platform
        from one `Account` to another. As such, only `Account`s that are connected to
        Dinari-managed `Wallet`s can initiate `TokenTransfer`s.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        if not transfer_id:
            raise ValueError(f"Expected a non-empty value for `transfer_id` but received {transfer_id!r}")
        return self._get(
            f"/api/v2/accounts/{account_id}/token_transfers/{transfer_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TokenTransfer,
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
    ) -> TokenTransferListResponse:
        """
        Get `TokenTransfer`s made from this `Account`.

        A `TokenTransfer` represents a transfer of tokens through the Dinari platform
        from one `Account` to another. As such, only `Account`s that are connected to
        Dinari-managed `Wallet`s can initiate `TokenTransfer`s.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return self._get(
            f"/api/v2/accounts/{account_id}/token_transfers",
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
                    token_transfer_list_params.TokenTransferListParams,
                ),
            ),
            cast_to=TokenTransferListResponse,
        )


class AsyncTokenTransfersResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncTokenTransfersResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncTokenTransfersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncTokenTransfersResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#with_streaming_response
        """
        return AsyncTokenTransfersResourceWithStreamingResponse(self)

    async def create(
        self,
        account_id: str,
        *,
        quantity: float,
        recipient_account_id: str,
        token_address: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TokenTransfer:
        """
        Creates a `TokenTransfer` from this `Account`.

        A `TokenTransfer` represents a transfer of tokens through the Dinari platform
        from one `Account` to another. As such, only `Account`s that are connected to
        Dinari-managed `Wallet`s can initiate `TokenTransfer`s.

        Args:
          quantity: Quantity of the token to transfer.

          recipient_account_id: ID of the recipient account to which the tokens will be transferred.

          token_address: Address of the token to transfer.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return await self._post(
            f"/api/v2/accounts/{account_id}/token_transfers",
            body=await async_maybe_transform(
                {
                    "quantity": quantity,
                    "recipient_account_id": recipient_account_id,
                    "token_address": token_address,
                },
                token_transfer_create_params.TokenTransferCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TokenTransfer,
        )

    async def retrieve(
        self,
        transfer_id: str,
        *,
        account_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TokenTransfer:
        """
        Get a specific `TokenTransfer` made from this `Account` by its ID.

        A `TokenTransfer` represents a transfer of tokens through the Dinari platform
        from one `Account` to another. As such, only `Account`s that are connected to
        Dinari-managed `Wallet`s can initiate `TokenTransfer`s.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        if not transfer_id:
            raise ValueError(f"Expected a non-empty value for `transfer_id` but received {transfer_id!r}")
        return await self._get(
            f"/api/v2/accounts/{account_id}/token_transfers/{transfer_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TokenTransfer,
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
    ) -> TokenTransferListResponse:
        """
        Get `TokenTransfer`s made from this `Account`.

        A `TokenTransfer` represents a transfer of tokens through the Dinari platform
        from one `Account` to another. As such, only `Account`s that are connected to
        Dinari-managed `Wallet`s can initiate `TokenTransfer`s.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return await self._get(
            f"/api/v2/accounts/{account_id}/token_transfers",
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
                    token_transfer_list_params.TokenTransferListParams,
                ),
            ),
            cast_to=TokenTransferListResponse,
        )


class TokenTransfersResourceWithRawResponse:
    def __init__(self, token_transfers: TokenTransfersResource) -> None:
        self._token_transfers = token_transfers

        self.create = to_raw_response_wrapper(
            token_transfers.create,
        )
        self.retrieve = to_raw_response_wrapper(
            token_transfers.retrieve,
        )
        self.list = to_raw_response_wrapper(
            token_transfers.list,
        )


class AsyncTokenTransfersResourceWithRawResponse:
    def __init__(self, token_transfers: AsyncTokenTransfersResource) -> None:
        self._token_transfers = token_transfers

        self.create = async_to_raw_response_wrapper(
            token_transfers.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            token_transfers.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            token_transfers.list,
        )


class TokenTransfersResourceWithStreamingResponse:
    def __init__(self, token_transfers: TokenTransfersResource) -> None:
        self._token_transfers = token_transfers

        self.create = to_streamed_response_wrapper(
            token_transfers.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            token_transfers.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            token_transfers.list,
        )


class AsyncTokenTransfersResourceWithStreamingResponse:
    def __init__(self, token_transfers: AsyncTokenTransfersResource) -> None:
        self._token_transfers = token_transfers

        self.create = async_to_streamed_response_wrapper(
            token_transfers.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            token_transfers.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            token_transfers.list,
        )
