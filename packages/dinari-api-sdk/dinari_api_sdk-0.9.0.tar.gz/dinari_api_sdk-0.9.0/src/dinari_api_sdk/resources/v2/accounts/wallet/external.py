# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ....._types import Body, Query, Headers, NotGiven, not_given
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
from .....types.v2.accounts.wallet import WalletChainID, external_connect_params, external_get_nonce_params
from .....types.v2.accounts.wallet.wallet import Wallet
from .....types.v2.accounts.wallet.wallet_chain_id import WalletChainID
from .....types.v2.accounts.wallet.external_get_nonce_response import ExternalGetNonceResponse

__all__ = ["ExternalResource", "AsyncExternalResource"]


class ExternalResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ExternalResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return ExternalResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ExternalResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#with_streaming_response
        """
        return ExternalResourceWithStreamingResponse(self)

    def connect(
        self,
        account_id: str,
        *,
        chain_id: WalletChainID,
        nonce: str,
        signature: str,
        wallet_address: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Wallet:
        """
        Connect a `Wallet` to the `Account` after verifying the signature.

        Args:
          chain_id: CAIP-2 formatted chain ID of the blockchain the `Wallet` to link is on. eip155:0
              is used for EOA wallets

          nonce: Nonce contained within the connection message.

          signature: Signature payload from signing the connection message with the `Wallet`.

          wallet_address: Address of the `Wallet`.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return self._post(
            f"/api/v2/accounts/{account_id}/wallet/external",
            body=maybe_transform(
                {
                    "chain_id": chain_id,
                    "nonce": nonce,
                    "signature": signature,
                    "wallet_address": wallet_address,
                },
                external_connect_params.ExternalConnectParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Wallet,
        )

    def get_nonce(
        self,
        account_id: str,
        *,
        chain_id: WalletChainID,
        wallet_address: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExternalGetNonceResponse:
        """
        Get a nonce and message to be signed in order to verify `Wallet` ownership.

        Args:
          chain_id: CAIP-2 formatted chain ID of the blockchain the `Wallet` is on. eip155:0 is used
              for EOA wallets

          wallet_address: Address of the `Wallet` to connect.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return self._get(
            f"/api/v2/accounts/{account_id}/wallet/external/nonce",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "chain_id": chain_id,
                        "wallet_address": wallet_address,
                    },
                    external_get_nonce_params.ExternalGetNonceParams,
                ),
            ),
            cast_to=ExternalGetNonceResponse,
        )


class AsyncExternalResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncExternalResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncExternalResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncExternalResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#with_streaming_response
        """
        return AsyncExternalResourceWithStreamingResponse(self)

    async def connect(
        self,
        account_id: str,
        *,
        chain_id: WalletChainID,
        nonce: str,
        signature: str,
        wallet_address: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Wallet:
        """
        Connect a `Wallet` to the `Account` after verifying the signature.

        Args:
          chain_id: CAIP-2 formatted chain ID of the blockchain the `Wallet` to link is on. eip155:0
              is used for EOA wallets

          nonce: Nonce contained within the connection message.

          signature: Signature payload from signing the connection message with the `Wallet`.

          wallet_address: Address of the `Wallet`.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return await self._post(
            f"/api/v2/accounts/{account_id}/wallet/external",
            body=await async_maybe_transform(
                {
                    "chain_id": chain_id,
                    "nonce": nonce,
                    "signature": signature,
                    "wallet_address": wallet_address,
                },
                external_connect_params.ExternalConnectParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Wallet,
        )

    async def get_nonce(
        self,
        account_id: str,
        *,
        chain_id: WalletChainID,
        wallet_address: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExternalGetNonceResponse:
        """
        Get a nonce and message to be signed in order to verify `Wallet` ownership.

        Args:
          chain_id: CAIP-2 formatted chain ID of the blockchain the `Wallet` is on. eip155:0 is used
              for EOA wallets

          wallet_address: Address of the `Wallet` to connect.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return await self._get(
            f"/api/v2/accounts/{account_id}/wallet/external/nonce",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "chain_id": chain_id,
                        "wallet_address": wallet_address,
                    },
                    external_get_nonce_params.ExternalGetNonceParams,
                ),
            ),
            cast_to=ExternalGetNonceResponse,
        )


class ExternalResourceWithRawResponse:
    def __init__(self, external: ExternalResource) -> None:
        self._external = external

        self.connect = to_raw_response_wrapper(
            external.connect,
        )
        self.get_nonce = to_raw_response_wrapper(
            external.get_nonce,
        )


class AsyncExternalResourceWithRawResponse:
    def __init__(self, external: AsyncExternalResource) -> None:
        self._external = external

        self.connect = async_to_raw_response_wrapper(
            external.connect,
        )
        self.get_nonce = async_to_raw_response_wrapper(
            external.get_nonce,
        )


class ExternalResourceWithStreamingResponse:
    def __init__(self, external: ExternalResource) -> None:
        self._external = external

        self.connect = to_streamed_response_wrapper(
            external.connect,
        )
        self.get_nonce = to_streamed_response_wrapper(
            external.get_nonce,
        )


class AsyncExternalResourceWithStreamingResponse:
    def __init__(self, external: AsyncExternalResource) -> None:
        self._external = external

        self.connect = async_to_streamed_response_wrapper(
            external.connect,
        )
        self.get_nonce = async_to_streamed_response_wrapper(
            external.get_nonce,
        )
