# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from dinari_api_sdk import Dinari, AsyncDinari
from dinari_api_sdk._utils import parse_date
from dinari_api_sdk.types.v2 import (
    AccountGetPortfolioResponse,
    AccountGetCashBalancesResponse,
    AccountGetDividendPaymentsResponse,
    AccountGetInterestPaymentsResponse,
)
from dinari_api_sdk.types.v2.entities import Account

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestAccounts:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Dinari) -> None:
        account = client.v2.accounts.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Dinari) -> None:
        response = client.v2.accounts.with_raw_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Dinari) -> None:
        with client.v2.accounts.with_streaming_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Dinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.v2.accounts.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_deactivate(self, client: Dinari) -> None:
        account = client.v2.accounts.deactivate(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_deactivate(self, client: Dinari) -> None:
        response = client.v2.accounts.with_raw_response.deactivate(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_deactivate(self, client: Dinari) -> None:
        with client.v2.accounts.with_streaming_response.deactivate(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_deactivate(self, client: Dinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.v2.accounts.with_raw_response.deactivate(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_cash_balances(self, client: Dinari) -> None:
        account = client.v2.accounts.get_cash_balances(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(AccountGetCashBalancesResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_cash_balances(self, client: Dinari) -> None:
        response = client.v2.accounts.with_raw_response.get_cash_balances(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(AccountGetCashBalancesResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_cash_balances(self, client: Dinari) -> None:
        with client.v2.accounts.with_streaming_response.get_cash_balances(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(AccountGetCashBalancesResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_get_cash_balances(self, client: Dinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.v2.accounts.with_raw_response.get_cash_balances(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_dividend_payments(self, client: Dinari) -> None:
        account = client.v2.accounts.get_dividend_payments(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
        )
        assert_matches_type(AccountGetDividendPaymentsResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_dividend_payments_with_all_params(self, client: Dinari) -> None:
        account = client.v2.accounts.get_dividend_payments(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
            page=1,
            page_size=1,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(AccountGetDividendPaymentsResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_dividend_payments(self, client: Dinari) -> None:
        response = client.v2.accounts.with_raw_response.get_dividend_payments(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(AccountGetDividendPaymentsResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_dividend_payments(self, client: Dinari) -> None:
        with client.v2.accounts.with_streaming_response.get_dividend_payments(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(AccountGetDividendPaymentsResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_get_dividend_payments(self, client: Dinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.v2.accounts.with_raw_response.get_dividend_payments(
                account_id="",
                end_date=parse_date("2019-12-27"),
                start_date=parse_date("2019-12-27"),
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_interest_payments(self, client: Dinari) -> None:
        account = client.v2.accounts.get_interest_payments(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
        )
        assert_matches_type(AccountGetInterestPaymentsResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_interest_payments_with_all_params(self, client: Dinari) -> None:
        account = client.v2.accounts.get_interest_payments(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
            page=1,
            page_size=1,
        )
        assert_matches_type(AccountGetInterestPaymentsResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_interest_payments(self, client: Dinari) -> None:
        response = client.v2.accounts.with_raw_response.get_interest_payments(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(AccountGetInterestPaymentsResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_interest_payments(self, client: Dinari) -> None:
        with client.v2.accounts.with_streaming_response.get_interest_payments(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(AccountGetInterestPaymentsResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_get_interest_payments(self, client: Dinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.v2.accounts.with_raw_response.get_interest_payments(
                account_id="",
                end_date=parse_date("2019-12-27"),
                start_date=parse_date("2019-12-27"),
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_portfolio(self, client: Dinari) -> None:
        account = client.v2.accounts.get_portfolio(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(AccountGetPortfolioResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_portfolio_with_all_params(self, client: Dinari) -> None:
        account = client.v2.accounts.get_portfolio(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            page=1,
            page_size=1,
        )
        assert_matches_type(AccountGetPortfolioResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_portfolio(self, client: Dinari) -> None:
        response = client.v2.accounts.with_raw_response.get_portfolio(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(AccountGetPortfolioResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_portfolio(self, client: Dinari) -> None:
        with client.v2.accounts.with_streaming_response.get_portfolio(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(AccountGetPortfolioResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_get_portfolio(self, client: Dinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.v2.accounts.with_raw_response.get_portfolio(
                account_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_mint_sandbox_tokens(self, client: Dinari) -> None:
        account = client.v2.accounts.mint_sandbox_tokens(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert account is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_mint_sandbox_tokens_with_all_params(self, client: Dinari) -> None:
        account = client.v2.accounts.mint_sandbox_tokens(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            chain_id="eip155:1",
        )
        assert account is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_mint_sandbox_tokens(self, client: Dinari) -> None:
        response = client.v2.accounts.with_raw_response.mint_sandbox_tokens(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert account is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_mint_sandbox_tokens(self, client: Dinari) -> None:
        with client.v2.accounts.with_streaming_response.mint_sandbox_tokens(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert account is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_mint_sandbox_tokens(self, client: Dinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.v2.accounts.with_raw_response.mint_sandbox_tokens(
                account_id="",
            )


class TestAsyncAccounts:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncDinari) -> None:
        account = await async_client.v2.accounts.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.accounts.with_raw_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.accounts.with_streaming_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncDinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.v2.accounts.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_deactivate(self, async_client: AsyncDinari) -> None:
        account = await async_client.v2.accounts.deactivate(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_deactivate(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.accounts.with_raw_response.deactivate(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(Account, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_deactivate(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.accounts.with_streaming_response.deactivate(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(Account, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_deactivate(self, async_client: AsyncDinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.v2.accounts.with_raw_response.deactivate(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_cash_balances(self, async_client: AsyncDinari) -> None:
        account = await async_client.v2.accounts.get_cash_balances(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(AccountGetCashBalancesResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_cash_balances(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.accounts.with_raw_response.get_cash_balances(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(AccountGetCashBalancesResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_cash_balances(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.accounts.with_streaming_response.get_cash_balances(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(AccountGetCashBalancesResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_get_cash_balances(self, async_client: AsyncDinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.v2.accounts.with_raw_response.get_cash_balances(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_dividend_payments(self, async_client: AsyncDinari) -> None:
        account = await async_client.v2.accounts.get_dividend_payments(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
        )
        assert_matches_type(AccountGetDividendPaymentsResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_dividend_payments_with_all_params(self, async_client: AsyncDinari) -> None:
        account = await async_client.v2.accounts.get_dividend_payments(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
            page=1,
            page_size=1,
            stock_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(AccountGetDividendPaymentsResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_dividend_payments(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.accounts.with_raw_response.get_dividend_payments(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(AccountGetDividendPaymentsResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_dividend_payments(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.accounts.with_streaming_response.get_dividend_payments(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(AccountGetDividendPaymentsResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_get_dividend_payments(self, async_client: AsyncDinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.v2.accounts.with_raw_response.get_dividend_payments(
                account_id="",
                end_date=parse_date("2019-12-27"),
                start_date=parse_date("2019-12-27"),
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_interest_payments(self, async_client: AsyncDinari) -> None:
        account = await async_client.v2.accounts.get_interest_payments(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
        )
        assert_matches_type(AccountGetInterestPaymentsResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_interest_payments_with_all_params(self, async_client: AsyncDinari) -> None:
        account = await async_client.v2.accounts.get_interest_payments(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
            page=1,
            page_size=1,
        )
        assert_matches_type(AccountGetInterestPaymentsResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_interest_payments(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.accounts.with_raw_response.get_interest_payments(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(AccountGetInterestPaymentsResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_interest_payments(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.accounts.with_streaming_response.get_interest_payments(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(AccountGetInterestPaymentsResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_get_interest_payments(self, async_client: AsyncDinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.v2.accounts.with_raw_response.get_interest_payments(
                account_id="",
                end_date=parse_date("2019-12-27"),
                start_date=parse_date("2019-12-27"),
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_portfolio(self, async_client: AsyncDinari) -> None:
        account = await async_client.v2.accounts.get_portfolio(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(AccountGetPortfolioResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_portfolio_with_all_params(self, async_client: AsyncDinari) -> None:
        account = await async_client.v2.accounts.get_portfolio(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            page=1,
            page_size=1,
        )
        assert_matches_type(AccountGetPortfolioResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_portfolio(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.accounts.with_raw_response.get_portfolio(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(AccountGetPortfolioResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_portfolio(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.accounts.with_streaming_response.get_portfolio(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(AccountGetPortfolioResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_get_portfolio(self, async_client: AsyncDinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.v2.accounts.with_raw_response.get_portfolio(
                account_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_mint_sandbox_tokens(self, async_client: AsyncDinari) -> None:
        account = await async_client.v2.accounts.mint_sandbox_tokens(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert account is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_mint_sandbox_tokens_with_all_params(self, async_client: AsyncDinari) -> None:
        account = await async_client.v2.accounts.mint_sandbox_tokens(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            chain_id="eip155:1",
        )
        assert account is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_mint_sandbox_tokens(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.accounts.with_raw_response.mint_sandbox_tokens(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert account is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_mint_sandbox_tokens(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.accounts.with_streaming_response.mint_sandbox_tokens(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert account is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_mint_sandbox_tokens(self, async_client: AsyncDinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.v2.accounts.with_raw_response.mint_sandbox_tokens(
                account_id="",
            )
