# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from .external import (
    ExternalResource,
    AsyncExternalResource,
    ExternalResourceWithRawResponse,
    AsyncExternalResourceWithRawResponse,
    ExternalResourceWithStreamingResponse,
    AsyncExternalResourceWithStreamingResponse,
)
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
from .....types.v2.accounts import wallet_connect_internal_params
from .....types.v2.accounts.wallet import WalletChainID
from .....types.v2.accounts.wallet.wallet import Wallet
from .....types.v2.accounts.wallet.wallet_chain_id import WalletChainID

__all__ = ["WalletResource", "AsyncWalletResource"]


class WalletResource(SyncAPIResource):
    @cached_property
    def external(self) -> ExternalResource:
        return ExternalResource(self._client)

    @cached_property
    def with_raw_response(self) -> WalletResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return WalletResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> WalletResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#with_streaming_response
        """
        return WalletResourceWithStreamingResponse(self)

    def connect_internal(
        self,
        account_id: str,
        *,
        chain_id: WalletChainID,
        wallet_address: str,
        is_shared: Optional[bool] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Wallet:
        """
        Connect an internal `Wallet` to the `Account`.

        Args:
          chain_id: CAIP-2 formatted chain ID of the blockchain the `Wallet` to link is on. eip155:0
              is used for EOA wallets

          wallet_address: Address of the `Wallet`.

          is_shared: Is the linked Wallet shared or not

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return self._post(
            f"/api/v2/accounts/{account_id}/wallet/internal",
            body=maybe_transform(
                {
                    "chain_id": chain_id,
                    "wallet_address": wallet_address,
                    "is_shared": is_shared,
                },
                wallet_connect_internal_params.WalletConnectInternalParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Wallet,
        )

    def get(
        self,
        account_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Wallet:
        """
        Get the wallet connected to the `Account`.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return self._get(
            f"/api/v2/accounts/{account_id}/wallet",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Wallet,
        )


class AsyncWalletResource(AsyncAPIResource):
    @cached_property
    def external(self) -> AsyncExternalResource:
        return AsyncExternalResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncWalletResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncWalletResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncWalletResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#with_streaming_response
        """
        return AsyncWalletResourceWithStreamingResponse(self)

    async def connect_internal(
        self,
        account_id: str,
        *,
        chain_id: WalletChainID,
        wallet_address: str,
        is_shared: Optional[bool] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Wallet:
        """
        Connect an internal `Wallet` to the `Account`.

        Args:
          chain_id: CAIP-2 formatted chain ID of the blockchain the `Wallet` to link is on. eip155:0
              is used for EOA wallets

          wallet_address: Address of the `Wallet`.

          is_shared: Is the linked Wallet shared or not

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return await self._post(
            f"/api/v2/accounts/{account_id}/wallet/internal",
            body=await async_maybe_transform(
                {
                    "chain_id": chain_id,
                    "wallet_address": wallet_address,
                    "is_shared": is_shared,
                },
                wallet_connect_internal_params.WalletConnectInternalParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Wallet,
        )

    async def get(
        self,
        account_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Wallet:
        """
        Get the wallet connected to the `Account`.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return await self._get(
            f"/api/v2/accounts/{account_id}/wallet",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Wallet,
        )


class WalletResourceWithRawResponse:
    def __init__(self, wallet: WalletResource) -> None:
        self._wallet = wallet

        self.connect_internal = to_raw_response_wrapper(
            wallet.connect_internal,
        )
        self.get = to_raw_response_wrapper(
            wallet.get,
        )

    @cached_property
    def external(self) -> ExternalResourceWithRawResponse:
        return ExternalResourceWithRawResponse(self._wallet.external)


class AsyncWalletResourceWithRawResponse:
    def __init__(self, wallet: AsyncWalletResource) -> None:
        self._wallet = wallet

        self.connect_internal = async_to_raw_response_wrapper(
            wallet.connect_internal,
        )
        self.get = async_to_raw_response_wrapper(
            wallet.get,
        )

    @cached_property
    def external(self) -> AsyncExternalResourceWithRawResponse:
        return AsyncExternalResourceWithRawResponse(self._wallet.external)


class WalletResourceWithStreamingResponse:
    def __init__(self, wallet: WalletResource) -> None:
        self._wallet = wallet

        self.connect_internal = to_streamed_response_wrapper(
            wallet.connect_internal,
        )
        self.get = to_streamed_response_wrapper(
            wallet.get,
        )

    @cached_property
    def external(self) -> ExternalResourceWithStreamingResponse:
        return ExternalResourceWithStreamingResponse(self._wallet.external)


class AsyncWalletResourceWithStreamingResponse:
    def __init__(self, wallet: AsyncWalletResource) -> None:
        self._wallet = wallet

        self.connect_internal = async_to_streamed_response_wrapper(
            wallet.connect_internal,
        )
        self.get = async_to_streamed_response_wrapper(
            wallet.get,
        )

    @cached_property
    def external(self) -> AsyncExternalResourceWithStreamingResponse:
        return AsyncExternalResourceWithStreamingResponse(self._wallet.external)
