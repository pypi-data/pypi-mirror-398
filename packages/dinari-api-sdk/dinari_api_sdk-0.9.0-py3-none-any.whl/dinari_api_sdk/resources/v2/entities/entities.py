# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from .kyc.kyc import (
    KYCResource,
    AsyncKYCResource,
    KYCResourceWithRawResponse,
    AsyncKYCResourceWithRawResponse,
    KYCResourceWithStreamingResponse,
    AsyncKYCResourceWithStreamingResponse,
)
from .accounts import (
    AccountsResource,
    AsyncAccountsResource,
    AccountsResourceWithRawResponse,
    AsyncAccountsResourceWithRawResponse,
    AccountsResourceWithStreamingResponse,
    AsyncAccountsResourceWithStreamingResponse,
)
from ...._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ...._utils import maybe_transform, async_maybe_transform
from ...._compat import cached_property
from ....types.v2 import entity_list_params, entity_create_params, entity_update_params
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.v2.entity import Entity
from ....types.v2.entity_list_response import EntityListResponse

__all__ = ["EntitiesResource", "AsyncEntitiesResource"]


class EntitiesResource(SyncAPIResource):
    @cached_property
    def accounts(self) -> AccountsResource:
        return AccountsResource(self._client)

    @cached_property
    def kyc(self) -> KYCResource:
        return KYCResource(self._client)

    @cached_property
    def with_raw_response(self) -> EntitiesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return EntitiesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> EntitiesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#with_streaming_response
        """
        return EntitiesResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        name: str,
        reference_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Entity:
        """Create a new `Entity` to be managed by your organization.

        This `Entity`
        represents an individual customer of your organization.

        Args:
          name: Name of the `Entity`.

          reference_id: Case sensitive unique reference ID for the `Entity`. We recommend setting this
              to the unique ID of the `Entity` in your system.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/v2/entities/",
            body=maybe_transform(
                {
                    "name": name,
                    "reference_id": reference_id,
                },
                entity_create_params.EntityCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Entity,
        )

    def update(
        self,
        entity_id: str,
        *,
        reference_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Entity:
        """
        Update a specific customer `Entity` of your organization.

        Args:
          reference_id: Case sensitive unique reference ID for the `Entity`. We recommend setting this
              to the unique ID of the `Entity` in your system.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not entity_id:
            raise ValueError(f"Expected a non-empty value for `entity_id` but received {entity_id!r}")
        return self._patch(
            f"/api/v2/entities/{entity_id}",
            body=maybe_transform({"reference_id": reference_id}, entity_update_params.EntityUpdateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Entity,
        )

    def list(
        self,
        *,
        page: int | Omit = omit,
        page_size: int | Omit = omit,
        reference_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EntityListResponse:
        """Get a list of direct `Entities` your organization manages.

        These `Entities`
        represent individual customers of your organization.

        Args:
          reference_id: Case sensitive unique reference ID for the `Entity`.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/api/v2/entities/",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "page": page,
                        "page_size": page_size,
                        "reference_id": reference_id,
                    },
                    entity_list_params.EntityListParams,
                ),
            ),
            cast_to=EntityListResponse,
        )

    def retrieve_by_id(
        self,
        entity_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Entity:
        """
        Get a specific customer `Entity` of your organization by their ID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not entity_id:
            raise ValueError(f"Expected a non-empty value for `entity_id` but received {entity_id!r}")
        return self._get(
            f"/api/v2/entities/{entity_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Entity,
        )

    def retrieve_current(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Entity:
        """Get the current authenticated `Entity`, which represents your organization."""
        return self._get(
            "/api/v2/entities/me",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Entity,
        )


class AsyncEntitiesResource(AsyncAPIResource):
    @cached_property
    def accounts(self) -> AsyncAccountsResource:
        return AsyncAccountsResource(self._client)

    @cached_property
    def kyc(self) -> AsyncKYCResource:
        return AsyncKYCResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncEntitiesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncEntitiesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncEntitiesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#with_streaming_response
        """
        return AsyncEntitiesResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        name: str,
        reference_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Entity:
        """Create a new `Entity` to be managed by your organization.

        This `Entity`
        represents an individual customer of your organization.

        Args:
          name: Name of the `Entity`.

          reference_id: Case sensitive unique reference ID for the `Entity`. We recommend setting this
              to the unique ID of the `Entity` in your system.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/v2/entities/",
            body=await async_maybe_transform(
                {
                    "name": name,
                    "reference_id": reference_id,
                },
                entity_create_params.EntityCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Entity,
        )

    async def update(
        self,
        entity_id: str,
        *,
        reference_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Entity:
        """
        Update a specific customer `Entity` of your organization.

        Args:
          reference_id: Case sensitive unique reference ID for the `Entity`. We recommend setting this
              to the unique ID of the `Entity` in your system.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not entity_id:
            raise ValueError(f"Expected a non-empty value for `entity_id` but received {entity_id!r}")
        return await self._patch(
            f"/api/v2/entities/{entity_id}",
            body=await async_maybe_transform({"reference_id": reference_id}, entity_update_params.EntityUpdateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Entity,
        )

    async def list(
        self,
        *,
        page: int | Omit = omit,
        page_size: int | Omit = omit,
        reference_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EntityListResponse:
        """Get a list of direct `Entities` your organization manages.

        These `Entities`
        represent individual customers of your organization.

        Args:
          reference_id: Case sensitive unique reference ID for the `Entity`.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/api/v2/entities/",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "page": page,
                        "page_size": page_size,
                        "reference_id": reference_id,
                    },
                    entity_list_params.EntityListParams,
                ),
            ),
            cast_to=EntityListResponse,
        )

    async def retrieve_by_id(
        self,
        entity_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Entity:
        """
        Get a specific customer `Entity` of your organization by their ID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not entity_id:
            raise ValueError(f"Expected a non-empty value for `entity_id` but received {entity_id!r}")
        return await self._get(
            f"/api/v2/entities/{entity_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Entity,
        )

    async def retrieve_current(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Entity:
        """Get the current authenticated `Entity`, which represents your organization."""
        return await self._get(
            "/api/v2/entities/me",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Entity,
        )


class EntitiesResourceWithRawResponse:
    def __init__(self, entities: EntitiesResource) -> None:
        self._entities = entities

        self.create = to_raw_response_wrapper(
            entities.create,
        )
        self.update = to_raw_response_wrapper(
            entities.update,
        )
        self.list = to_raw_response_wrapper(
            entities.list,
        )
        self.retrieve_by_id = to_raw_response_wrapper(
            entities.retrieve_by_id,
        )
        self.retrieve_current = to_raw_response_wrapper(
            entities.retrieve_current,
        )

    @cached_property
    def accounts(self) -> AccountsResourceWithRawResponse:
        return AccountsResourceWithRawResponse(self._entities.accounts)

    @cached_property
    def kyc(self) -> KYCResourceWithRawResponse:
        return KYCResourceWithRawResponse(self._entities.kyc)


class AsyncEntitiesResourceWithRawResponse:
    def __init__(self, entities: AsyncEntitiesResource) -> None:
        self._entities = entities

        self.create = async_to_raw_response_wrapper(
            entities.create,
        )
        self.update = async_to_raw_response_wrapper(
            entities.update,
        )
        self.list = async_to_raw_response_wrapper(
            entities.list,
        )
        self.retrieve_by_id = async_to_raw_response_wrapper(
            entities.retrieve_by_id,
        )
        self.retrieve_current = async_to_raw_response_wrapper(
            entities.retrieve_current,
        )

    @cached_property
    def accounts(self) -> AsyncAccountsResourceWithRawResponse:
        return AsyncAccountsResourceWithRawResponse(self._entities.accounts)

    @cached_property
    def kyc(self) -> AsyncKYCResourceWithRawResponse:
        return AsyncKYCResourceWithRawResponse(self._entities.kyc)


class EntitiesResourceWithStreamingResponse:
    def __init__(self, entities: EntitiesResource) -> None:
        self._entities = entities

        self.create = to_streamed_response_wrapper(
            entities.create,
        )
        self.update = to_streamed_response_wrapper(
            entities.update,
        )
        self.list = to_streamed_response_wrapper(
            entities.list,
        )
        self.retrieve_by_id = to_streamed_response_wrapper(
            entities.retrieve_by_id,
        )
        self.retrieve_current = to_streamed_response_wrapper(
            entities.retrieve_current,
        )

    @cached_property
    def accounts(self) -> AccountsResourceWithStreamingResponse:
        return AccountsResourceWithStreamingResponse(self._entities.accounts)

    @cached_property
    def kyc(self) -> KYCResourceWithStreamingResponse:
        return KYCResourceWithStreamingResponse(self._entities.kyc)


class AsyncEntitiesResourceWithStreamingResponse:
    def __init__(self, entities: AsyncEntitiesResource) -> None:
        self._entities = entities

        self.create = async_to_streamed_response_wrapper(
            entities.create,
        )
        self.update = async_to_streamed_response_wrapper(
            entities.update,
        )
        self.list = async_to_streamed_response_wrapper(
            entities.list,
        )
        self.retrieve_by_id = async_to_streamed_response_wrapper(
            entities.retrieve_by_id,
        )
        self.retrieve_current = async_to_streamed_response_wrapper(
            entities.retrieve_current,
        )

    @cached_property
    def accounts(self) -> AsyncAccountsResourceWithStreamingResponse:
        return AsyncAccountsResourceWithStreamingResponse(self._entities.accounts)

    @cached_property
    def kyc(self) -> AsyncKYCResourceWithStreamingResponse:
        return AsyncKYCResourceWithStreamingResponse(self._entities.kyc)
