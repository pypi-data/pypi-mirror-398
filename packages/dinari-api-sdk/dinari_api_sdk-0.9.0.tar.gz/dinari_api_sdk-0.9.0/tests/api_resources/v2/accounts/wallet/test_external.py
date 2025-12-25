# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from dinari_api_sdk import Dinari, AsyncDinari
from dinari_api_sdk.types.v2.accounts.wallet import (
    Wallet,
    ExternalGetNonceResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestExternal:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_connect(self, client: Dinari) -> None:
        external = client.v2.accounts.wallet.external.connect(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            chain_id="eip155:0",
            nonce="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            signature="0xeaF12bD1DfFd",
            wallet_address="wallet_address",
        )
        assert_matches_type(Wallet, external, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_connect(self, client: Dinari) -> None:
        response = client.v2.accounts.wallet.external.with_raw_response.connect(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            chain_id="eip155:0",
            nonce="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            signature="0xeaF12bD1DfFd",
            wallet_address="wallet_address",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        external = response.parse()
        assert_matches_type(Wallet, external, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_connect(self, client: Dinari) -> None:
        with client.v2.accounts.wallet.external.with_streaming_response.connect(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            chain_id="eip155:0",
            nonce="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            signature="0xeaF12bD1DfFd",
            wallet_address="wallet_address",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            external = response.parse()
            assert_matches_type(Wallet, external, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_connect(self, client: Dinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.v2.accounts.wallet.external.with_raw_response.connect(
                account_id="",
                chain_id="eip155:0",
                nonce="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                signature="0xeaF12bD1DfFd",
                wallet_address="wallet_address",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_nonce(self, client: Dinari) -> None:
        external = client.v2.accounts.wallet.external.get_nonce(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            chain_id="eip155:0",
            wallet_address="wallet_address",
        )
        assert_matches_type(ExternalGetNonceResponse, external, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_nonce(self, client: Dinari) -> None:
        response = client.v2.accounts.wallet.external.with_raw_response.get_nonce(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            chain_id="eip155:0",
            wallet_address="wallet_address",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        external = response.parse()
        assert_matches_type(ExternalGetNonceResponse, external, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_nonce(self, client: Dinari) -> None:
        with client.v2.accounts.wallet.external.with_streaming_response.get_nonce(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            chain_id="eip155:0",
            wallet_address="wallet_address",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            external = response.parse()
            assert_matches_type(ExternalGetNonceResponse, external, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_get_nonce(self, client: Dinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.v2.accounts.wallet.external.with_raw_response.get_nonce(
                account_id="",
                chain_id="eip155:0",
                wallet_address="wallet_address",
            )


class TestAsyncExternal:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_connect(self, async_client: AsyncDinari) -> None:
        external = await async_client.v2.accounts.wallet.external.connect(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            chain_id="eip155:0",
            nonce="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            signature="0xeaF12bD1DfFd",
            wallet_address="wallet_address",
        )
        assert_matches_type(Wallet, external, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_connect(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.accounts.wallet.external.with_raw_response.connect(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            chain_id="eip155:0",
            nonce="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            signature="0xeaF12bD1DfFd",
            wallet_address="wallet_address",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        external = await response.parse()
        assert_matches_type(Wallet, external, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_connect(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.accounts.wallet.external.with_streaming_response.connect(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            chain_id="eip155:0",
            nonce="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            signature="0xeaF12bD1DfFd",
            wallet_address="wallet_address",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            external = await response.parse()
            assert_matches_type(Wallet, external, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_connect(self, async_client: AsyncDinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.v2.accounts.wallet.external.with_raw_response.connect(
                account_id="",
                chain_id="eip155:0",
                nonce="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
                signature="0xeaF12bD1DfFd",
                wallet_address="wallet_address",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_nonce(self, async_client: AsyncDinari) -> None:
        external = await async_client.v2.accounts.wallet.external.get_nonce(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            chain_id="eip155:0",
            wallet_address="wallet_address",
        )
        assert_matches_type(ExternalGetNonceResponse, external, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_nonce(self, async_client: AsyncDinari) -> None:
        response = await async_client.v2.accounts.wallet.external.with_raw_response.get_nonce(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            chain_id="eip155:0",
            wallet_address="wallet_address",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        external = await response.parse()
        assert_matches_type(ExternalGetNonceResponse, external, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_nonce(self, async_client: AsyncDinari) -> None:
        async with async_client.v2.accounts.wallet.external.with_streaming_response.get_nonce(
            account_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            chain_id="eip155:0",
            wallet_address="wallet_address",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            external = await response.parse()
            assert_matches_type(ExternalGetNonceResponse, external, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_get_nonce(self, async_client: AsyncDinari) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.v2.accounts.wallet.external.with_raw_response.get_nonce(
                account_id="",
                chain_id="eip155:0",
                wallet_address="wallet_address",
            )
