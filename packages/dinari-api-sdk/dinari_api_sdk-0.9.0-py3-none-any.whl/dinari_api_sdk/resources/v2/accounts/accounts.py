# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Optional
from datetime import date

import httpx

from .orders import (
    OrdersResource,
    AsyncOrdersResource,
    OrdersResourceWithRawResponse,
    AsyncOrdersResourceWithRawResponse,
    OrdersResourceWithStreamingResponse,
    AsyncOrdersResourceWithStreamingResponse,
)
from ...._types import Body, Omit, Query, Headers, NoneType, NotGiven, omit, not_given
from ...._utils import maybe_transform, async_maybe_transform
from ...._compat import cached_property
from .activities import (
    ActivitiesResource,
    AsyncActivitiesResource,
    ActivitiesResourceWithRawResponse,
    AsyncActivitiesResourceWithRawResponse,
    ActivitiesResourceWithStreamingResponse,
    AsyncActivitiesResourceWithStreamingResponse,
)
from ....types.v2 import (
    Chain,
    account_get_portfolio_params,
    account_mint_sandbox_tokens_params,
    account_get_dividend_payments_params,
    account_get_interest_payments_params,
)
from .withdrawals import (
    WithdrawalsResource,
    AsyncWithdrawalsResource,
    WithdrawalsResourceWithRawResponse,
    AsyncWithdrawalsResourceWithRawResponse,
    WithdrawalsResourceWithStreamingResponse,
    AsyncWithdrawalsResourceWithStreamingResponse,
)
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .wallet.wallet import (
    WalletResource,
    AsyncWalletResource,
    WalletResourceWithRawResponse,
    AsyncWalletResourceWithRawResponse,
    WalletResourceWithStreamingResponse,
    AsyncWalletResourceWithStreamingResponse,
)
from ...._base_client import make_request_options
from .token_transfers import (
    TokenTransfersResource,
    AsyncTokenTransfersResource,
    TokenTransfersResourceWithRawResponse,
    AsyncTokenTransfersResourceWithRawResponse,
    TokenTransfersResourceWithStreamingResponse,
    AsyncTokenTransfersResourceWithStreamingResponse,
)
from ....types.v2.chain import Chain
from .order_fulfillments import (
    OrderFulfillmentsResource,
    AsyncOrderFulfillmentsResource,
    OrderFulfillmentsResourceWithRawResponse,
    AsyncOrderFulfillmentsResourceWithRawResponse,
    OrderFulfillmentsResourceWithStreamingResponse,
    AsyncOrderFulfillmentsResourceWithStreamingResponse,
)
from .withdrawal_requests import (
    WithdrawalRequestsResource,
    AsyncWithdrawalRequestsResource,
    WithdrawalRequestsResourceWithRawResponse,
    AsyncWithdrawalRequestsResourceWithRawResponse,
    WithdrawalRequestsResourceWithStreamingResponse,
    AsyncWithdrawalRequestsResourceWithStreamingResponse,
)
from ....types.v2.entities.account import Account
from .order_requests.order_requests import (
    OrderRequestsResource,
    AsyncOrderRequestsResource,
    OrderRequestsResourceWithRawResponse,
    AsyncOrderRequestsResourceWithRawResponse,
    OrderRequestsResourceWithStreamingResponse,
    AsyncOrderRequestsResourceWithStreamingResponse,
)
from ....types.v2.account_get_portfolio_response import AccountGetPortfolioResponse
from ....types.v2.account_get_cash_balances_response import AccountGetCashBalancesResponse
from ....types.v2.account_get_dividend_payments_response import AccountGetDividendPaymentsResponse
from ....types.v2.account_get_interest_payments_response import AccountGetInterestPaymentsResponse

__all__ = ["AccountsResource", "AsyncAccountsResource"]


class AccountsResource(SyncAPIResource):
    @cached_property
    def wallet(self) -> WalletResource:
        return WalletResource(self._client)

    @cached_property
    def orders(self) -> OrdersResource:
        return OrdersResource(self._client)

    @cached_property
    def order_fulfillments(self) -> OrderFulfillmentsResource:
        return OrderFulfillmentsResource(self._client)

    @cached_property
    def order_requests(self) -> OrderRequestsResource:
        return OrderRequestsResource(self._client)

    @cached_property
    def withdrawal_requests(self) -> WithdrawalRequestsResource:
        return WithdrawalRequestsResource(self._client)

    @cached_property
    def withdrawals(self) -> WithdrawalsResource:
        return WithdrawalsResource(self._client)

    @cached_property
    def token_transfers(self) -> TokenTransfersResource:
        return TokenTransfersResource(self._client)

    @cached_property
    def activities(self) -> ActivitiesResource:
        return ActivitiesResource(self._client)

    @cached_property
    def with_raw_response(self) -> AccountsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AccountsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AccountsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#with_streaming_response
        """
        return AccountsResourceWithStreamingResponse(self)

    def retrieve(
        self,
        account_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Get a specific `Account` by its ID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return self._get(
            f"/api/v2/accounts/{account_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    def deactivate(
        self,
        account_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """Set the `Account` to be inactive.

        Inactive accounts cannot be used for trading.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return self._post(
            f"/api/v2/accounts/{account_id}/deactivate",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    def get_cash_balances(
        self,
        account_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountGetCashBalancesResponse:
        """
        Get the cash balances of the `Account`, including stablecoins and other cash
        equivalents.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return self._get(
            f"/api/v2/accounts/{account_id}/cash",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountGetCashBalancesResponse,
        )

    def get_dividend_payments(
        self,
        account_id: str,
        *,
        end_date: Union[str, date],
        start_date: Union[str, date],
        page: int | Omit = omit,
        page_size: int | Omit = omit,
        stock_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountGetDividendPaymentsResponse:
        """
        Get dividend payments made to the `Account` from dividend-bearing stock
        holdings.

        Args:
          end_date: End date, exclusive, in US Eastern time zone. ISO 8601 format, YYYY-MM-DD.

          start_date: Start date, inclusive, in US Eastern time zone. ISO 8601 format, YYYY-MM-DD.

          stock_id: Optional ID of the `Stock` to filter by

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return self._get(
            f"/api/v2/accounts/{account_id}/dividend_payments",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "end_date": end_date,
                        "start_date": start_date,
                        "page": page,
                        "page_size": page_size,
                        "stock_id": stock_id,
                    },
                    account_get_dividend_payments_params.AccountGetDividendPaymentsParams,
                ),
            ),
            cast_to=AccountGetDividendPaymentsResponse,
        )

    def get_interest_payments(
        self,
        account_id: str,
        *,
        end_date: Union[str, date],
        start_date: Union[str, date],
        page: int | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountGetInterestPaymentsResponse:
        """
        Get interest payments made to the `Account` from yield-bearing cash holdings.

        Currently, the only yield-bearing stablecoin accepted by Dinari is
        [USD+](https://usd.dinari.com/).

        Args:
          end_date: End date, exclusive, in US Eastern time zone. ISO 8601 format, YYYY-MM-DD.

          start_date: Start date, inclusive, in US Eastern time zone. ISO 8601 format, YYYY-MM-DD.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return self._get(
            f"/api/v2/accounts/{account_id}/interest_payments",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "end_date": end_date,
                        "start_date": start_date,
                        "page": page,
                        "page_size": page_size,
                    },
                    account_get_interest_payments_params.AccountGetInterestPaymentsParams,
                ),
            ),
            cast_to=AccountGetInterestPaymentsResponse,
        )

    def get_portfolio(
        self,
        account_id: str,
        *,
        page: Optional[int] | Omit = omit,
        page_size: Optional[int] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountGetPortfolioResponse:
        """
        Get the portfolio of the `Account`, excluding cash equivalents such as
        stablecoins.

        Args:
          page: The page number.

          page_size: The number of stocks to return per page, maximum number is 200.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return self._get(
            f"/api/v2/accounts/{account_id}/portfolio",
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
                    account_get_portfolio_params.AccountGetPortfolioParams,
                ),
            ),
            cast_to=AccountGetPortfolioResponse,
        )

    def mint_sandbox_tokens(
        self,
        account_id: str,
        *,
        chain_id: Optional[Chain] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Mints 1,000 mockUSD sandbox payment tokens to the `Wallet` connected to the
        `Account`.

        This feature is only supported in sandbox mode.

        Args:
          chain_id: CAIP-2 chain ID of blockchain in which to mint the sandbox payment tokens. If
              none specified, defaults to eip155:421614. If the `Account` is linked to a
              Dinari-managed `Wallet`, only eip155:42161 is allowed.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            f"/api/v2/accounts/{account_id}/faucet",
            body=maybe_transform(
                {"chain_id": chain_id}, account_mint_sandbox_tokens_params.AccountMintSandboxTokensParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncAccountsResource(AsyncAPIResource):
    @cached_property
    def wallet(self) -> AsyncWalletResource:
        return AsyncWalletResource(self._client)

    @cached_property
    def orders(self) -> AsyncOrdersResource:
        return AsyncOrdersResource(self._client)

    @cached_property
    def order_fulfillments(self) -> AsyncOrderFulfillmentsResource:
        return AsyncOrderFulfillmentsResource(self._client)

    @cached_property
    def order_requests(self) -> AsyncOrderRequestsResource:
        return AsyncOrderRequestsResource(self._client)

    @cached_property
    def withdrawal_requests(self) -> AsyncWithdrawalRequestsResource:
        return AsyncWithdrawalRequestsResource(self._client)

    @cached_property
    def withdrawals(self) -> AsyncWithdrawalsResource:
        return AsyncWithdrawalsResource(self._client)

    @cached_property
    def token_transfers(self) -> AsyncTokenTransfersResource:
        return AsyncTokenTransfersResource(self._client)

    @cached_property
    def activities(self) -> AsyncActivitiesResource:
        return AsyncActivitiesResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncAccountsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncAccountsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncAccountsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#with_streaming_response
        """
        return AsyncAccountsResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        account_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """
        Get a specific `Account` by its ID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return await self._get(
            f"/api/v2/accounts/{account_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    async def deactivate(
        self,
        account_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Account:
        """Set the `Account` to be inactive.

        Inactive accounts cannot be used for trading.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return await self._post(
            f"/api/v2/accounts/{account_id}/deactivate",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Account,
        )

    async def get_cash_balances(
        self,
        account_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountGetCashBalancesResponse:
        """
        Get the cash balances of the `Account`, including stablecoins and other cash
        equivalents.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return await self._get(
            f"/api/v2/accounts/{account_id}/cash",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountGetCashBalancesResponse,
        )

    async def get_dividend_payments(
        self,
        account_id: str,
        *,
        end_date: Union[str, date],
        start_date: Union[str, date],
        page: int | Omit = omit,
        page_size: int | Omit = omit,
        stock_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountGetDividendPaymentsResponse:
        """
        Get dividend payments made to the `Account` from dividend-bearing stock
        holdings.

        Args:
          end_date: End date, exclusive, in US Eastern time zone. ISO 8601 format, YYYY-MM-DD.

          start_date: Start date, inclusive, in US Eastern time zone. ISO 8601 format, YYYY-MM-DD.

          stock_id: Optional ID of the `Stock` to filter by

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return await self._get(
            f"/api/v2/accounts/{account_id}/dividend_payments",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "end_date": end_date,
                        "start_date": start_date,
                        "page": page,
                        "page_size": page_size,
                        "stock_id": stock_id,
                    },
                    account_get_dividend_payments_params.AccountGetDividendPaymentsParams,
                ),
            ),
            cast_to=AccountGetDividendPaymentsResponse,
        )

    async def get_interest_payments(
        self,
        account_id: str,
        *,
        end_date: Union[str, date],
        start_date: Union[str, date],
        page: int | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountGetInterestPaymentsResponse:
        """
        Get interest payments made to the `Account` from yield-bearing cash holdings.

        Currently, the only yield-bearing stablecoin accepted by Dinari is
        [USD+](https://usd.dinari.com/).

        Args:
          end_date: End date, exclusive, in US Eastern time zone. ISO 8601 format, YYYY-MM-DD.

          start_date: Start date, inclusive, in US Eastern time zone. ISO 8601 format, YYYY-MM-DD.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return await self._get(
            f"/api/v2/accounts/{account_id}/interest_payments",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "end_date": end_date,
                        "start_date": start_date,
                        "page": page,
                        "page_size": page_size,
                    },
                    account_get_interest_payments_params.AccountGetInterestPaymentsParams,
                ),
            ),
            cast_to=AccountGetInterestPaymentsResponse,
        )

    async def get_portfolio(
        self,
        account_id: str,
        *,
        page: Optional[int] | Omit = omit,
        page_size: Optional[int] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountGetPortfolioResponse:
        """
        Get the portfolio of the `Account`, excluding cash equivalents such as
        stablecoins.

        Args:
          page: The page number.

          page_size: The number of stocks to return per page, maximum number is 200.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return await self._get(
            f"/api/v2/accounts/{account_id}/portfolio",
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
                    account_get_portfolio_params.AccountGetPortfolioParams,
                ),
            ),
            cast_to=AccountGetPortfolioResponse,
        )

    async def mint_sandbox_tokens(
        self,
        account_id: str,
        *,
        chain_id: Optional[Chain] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Mints 1,000 mockUSD sandbox payment tokens to the `Wallet` connected to the
        `Account`.

        This feature is only supported in sandbox mode.

        Args:
          chain_id: CAIP-2 chain ID of blockchain in which to mint the sandbox payment tokens. If
              none specified, defaults to eip155:421614. If the `Account` is linked to a
              Dinari-managed `Wallet`, only eip155:42161 is allowed.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            f"/api/v2/accounts/{account_id}/faucet",
            body=await async_maybe_transform(
                {"chain_id": chain_id}, account_mint_sandbox_tokens_params.AccountMintSandboxTokensParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AccountsResourceWithRawResponse:
    def __init__(self, accounts: AccountsResource) -> None:
        self._accounts = accounts

        self.retrieve = to_raw_response_wrapper(
            accounts.retrieve,
        )
        self.deactivate = to_raw_response_wrapper(
            accounts.deactivate,
        )
        self.get_cash_balances = to_raw_response_wrapper(
            accounts.get_cash_balances,
        )
        self.get_dividend_payments = to_raw_response_wrapper(
            accounts.get_dividend_payments,
        )
        self.get_interest_payments = to_raw_response_wrapper(
            accounts.get_interest_payments,
        )
        self.get_portfolio = to_raw_response_wrapper(
            accounts.get_portfolio,
        )
        self.mint_sandbox_tokens = to_raw_response_wrapper(
            accounts.mint_sandbox_tokens,
        )

    @cached_property
    def wallet(self) -> WalletResourceWithRawResponse:
        return WalletResourceWithRawResponse(self._accounts.wallet)

    @cached_property
    def orders(self) -> OrdersResourceWithRawResponse:
        return OrdersResourceWithRawResponse(self._accounts.orders)

    @cached_property
    def order_fulfillments(self) -> OrderFulfillmentsResourceWithRawResponse:
        return OrderFulfillmentsResourceWithRawResponse(self._accounts.order_fulfillments)

    @cached_property
    def order_requests(self) -> OrderRequestsResourceWithRawResponse:
        return OrderRequestsResourceWithRawResponse(self._accounts.order_requests)

    @cached_property
    def withdrawal_requests(self) -> WithdrawalRequestsResourceWithRawResponse:
        return WithdrawalRequestsResourceWithRawResponse(self._accounts.withdrawal_requests)

    @cached_property
    def withdrawals(self) -> WithdrawalsResourceWithRawResponse:
        return WithdrawalsResourceWithRawResponse(self._accounts.withdrawals)

    @cached_property
    def token_transfers(self) -> TokenTransfersResourceWithRawResponse:
        return TokenTransfersResourceWithRawResponse(self._accounts.token_transfers)

    @cached_property
    def activities(self) -> ActivitiesResourceWithRawResponse:
        return ActivitiesResourceWithRawResponse(self._accounts.activities)


class AsyncAccountsResourceWithRawResponse:
    def __init__(self, accounts: AsyncAccountsResource) -> None:
        self._accounts = accounts

        self.retrieve = async_to_raw_response_wrapper(
            accounts.retrieve,
        )
        self.deactivate = async_to_raw_response_wrapper(
            accounts.deactivate,
        )
        self.get_cash_balances = async_to_raw_response_wrapper(
            accounts.get_cash_balances,
        )
        self.get_dividend_payments = async_to_raw_response_wrapper(
            accounts.get_dividend_payments,
        )
        self.get_interest_payments = async_to_raw_response_wrapper(
            accounts.get_interest_payments,
        )
        self.get_portfolio = async_to_raw_response_wrapper(
            accounts.get_portfolio,
        )
        self.mint_sandbox_tokens = async_to_raw_response_wrapper(
            accounts.mint_sandbox_tokens,
        )

    @cached_property
    def wallet(self) -> AsyncWalletResourceWithRawResponse:
        return AsyncWalletResourceWithRawResponse(self._accounts.wallet)

    @cached_property
    def orders(self) -> AsyncOrdersResourceWithRawResponse:
        return AsyncOrdersResourceWithRawResponse(self._accounts.orders)

    @cached_property
    def order_fulfillments(self) -> AsyncOrderFulfillmentsResourceWithRawResponse:
        return AsyncOrderFulfillmentsResourceWithRawResponse(self._accounts.order_fulfillments)

    @cached_property
    def order_requests(self) -> AsyncOrderRequestsResourceWithRawResponse:
        return AsyncOrderRequestsResourceWithRawResponse(self._accounts.order_requests)

    @cached_property
    def withdrawal_requests(self) -> AsyncWithdrawalRequestsResourceWithRawResponse:
        return AsyncWithdrawalRequestsResourceWithRawResponse(self._accounts.withdrawal_requests)

    @cached_property
    def withdrawals(self) -> AsyncWithdrawalsResourceWithRawResponse:
        return AsyncWithdrawalsResourceWithRawResponse(self._accounts.withdrawals)

    @cached_property
    def token_transfers(self) -> AsyncTokenTransfersResourceWithRawResponse:
        return AsyncTokenTransfersResourceWithRawResponse(self._accounts.token_transfers)

    @cached_property
    def activities(self) -> AsyncActivitiesResourceWithRawResponse:
        return AsyncActivitiesResourceWithRawResponse(self._accounts.activities)


class AccountsResourceWithStreamingResponse:
    def __init__(self, accounts: AccountsResource) -> None:
        self._accounts = accounts

        self.retrieve = to_streamed_response_wrapper(
            accounts.retrieve,
        )
        self.deactivate = to_streamed_response_wrapper(
            accounts.deactivate,
        )
        self.get_cash_balances = to_streamed_response_wrapper(
            accounts.get_cash_balances,
        )
        self.get_dividend_payments = to_streamed_response_wrapper(
            accounts.get_dividend_payments,
        )
        self.get_interest_payments = to_streamed_response_wrapper(
            accounts.get_interest_payments,
        )
        self.get_portfolio = to_streamed_response_wrapper(
            accounts.get_portfolio,
        )
        self.mint_sandbox_tokens = to_streamed_response_wrapper(
            accounts.mint_sandbox_tokens,
        )

    @cached_property
    def wallet(self) -> WalletResourceWithStreamingResponse:
        return WalletResourceWithStreamingResponse(self._accounts.wallet)

    @cached_property
    def orders(self) -> OrdersResourceWithStreamingResponse:
        return OrdersResourceWithStreamingResponse(self._accounts.orders)

    @cached_property
    def order_fulfillments(self) -> OrderFulfillmentsResourceWithStreamingResponse:
        return OrderFulfillmentsResourceWithStreamingResponse(self._accounts.order_fulfillments)

    @cached_property
    def order_requests(self) -> OrderRequestsResourceWithStreamingResponse:
        return OrderRequestsResourceWithStreamingResponse(self._accounts.order_requests)

    @cached_property
    def withdrawal_requests(self) -> WithdrawalRequestsResourceWithStreamingResponse:
        return WithdrawalRequestsResourceWithStreamingResponse(self._accounts.withdrawal_requests)

    @cached_property
    def withdrawals(self) -> WithdrawalsResourceWithStreamingResponse:
        return WithdrawalsResourceWithStreamingResponse(self._accounts.withdrawals)

    @cached_property
    def token_transfers(self) -> TokenTransfersResourceWithStreamingResponse:
        return TokenTransfersResourceWithStreamingResponse(self._accounts.token_transfers)

    @cached_property
    def activities(self) -> ActivitiesResourceWithStreamingResponse:
        return ActivitiesResourceWithStreamingResponse(self._accounts.activities)


class AsyncAccountsResourceWithStreamingResponse:
    def __init__(self, accounts: AsyncAccountsResource) -> None:
        self._accounts = accounts

        self.retrieve = async_to_streamed_response_wrapper(
            accounts.retrieve,
        )
        self.deactivate = async_to_streamed_response_wrapper(
            accounts.deactivate,
        )
        self.get_cash_balances = async_to_streamed_response_wrapper(
            accounts.get_cash_balances,
        )
        self.get_dividend_payments = async_to_streamed_response_wrapper(
            accounts.get_dividend_payments,
        )
        self.get_interest_payments = async_to_streamed_response_wrapper(
            accounts.get_interest_payments,
        )
        self.get_portfolio = async_to_streamed_response_wrapper(
            accounts.get_portfolio,
        )
        self.mint_sandbox_tokens = async_to_streamed_response_wrapper(
            accounts.mint_sandbox_tokens,
        )

    @cached_property
    def wallet(self) -> AsyncWalletResourceWithStreamingResponse:
        return AsyncWalletResourceWithStreamingResponse(self._accounts.wallet)

    @cached_property
    def orders(self) -> AsyncOrdersResourceWithStreamingResponse:
        return AsyncOrdersResourceWithStreamingResponse(self._accounts.orders)

    @cached_property
    def order_fulfillments(self) -> AsyncOrderFulfillmentsResourceWithStreamingResponse:
        return AsyncOrderFulfillmentsResourceWithStreamingResponse(self._accounts.order_fulfillments)

    @cached_property
    def order_requests(self) -> AsyncOrderRequestsResourceWithStreamingResponse:
        return AsyncOrderRequestsResourceWithStreamingResponse(self._accounts.order_requests)

    @cached_property
    def withdrawal_requests(self) -> AsyncWithdrawalRequestsResourceWithStreamingResponse:
        return AsyncWithdrawalRequestsResourceWithStreamingResponse(self._accounts.withdrawal_requests)

    @cached_property
    def withdrawals(self) -> AsyncWithdrawalsResourceWithStreamingResponse:
        return AsyncWithdrawalsResourceWithStreamingResponse(self._accounts.withdrawals)

    @cached_property
    def token_transfers(self) -> AsyncTokenTransfersResourceWithStreamingResponse:
        return AsyncTokenTransfersResourceWithStreamingResponse(self._accounts.token_transfers)

    @cached_property
    def activities(self) -> AsyncActivitiesResourceWithStreamingResponse:
        return AsyncActivitiesResourceWithStreamingResponse(self._accounts.activities)
