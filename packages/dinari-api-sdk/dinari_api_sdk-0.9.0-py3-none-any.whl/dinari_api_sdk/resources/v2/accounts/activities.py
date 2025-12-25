# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ...._types import Body, Omit, Query, Headers, NoneType, NotGiven, omit, not_given
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
from ....types.v2.accounts import activity_retrieve_brokerage_params

__all__ = ["ActivitiesResource", "AsyncActivitiesResource"]


class ActivitiesResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ActivitiesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return ActivitiesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ActivitiesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#with_streaming_response
        """
        return ActivitiesResourceWithStreamingResponse(self)

    def retrieve_brokerage(
        self,
        account_id: str,
        *,
        page_size: Optional[int] | Omit = omit,
        page_token: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Get a list of brokerage activities tied to the specified `Account`.

        **⚠️ ALPHA: This endpoint is in early development and subject to breaking
        changes.**

        Args:
          page_size: The maximum number of entries to return in the response. Defaults to 100.

          page_token: Pagination token. Set to the `id` field of the last Activity returned in the
              previous page to get the next page of results.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._get(
            f"/api/v2/accounts/{account_id}/activities/brokerage",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "page_size": page_size,
                        "page_token": page_token,
                    },
                    activity_retrieve_brokerage_params.ActivityRetrieveBrokerageParams,
                ),
            ),
            cast_to=NoneType,
        )


class AsyncActivitiesResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncActivitiesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncActivitiesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncActivitiesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#with_streaming_response
        """
        return AsyncActivitiesResourceWithStreamingResponse(self)

    async def retrieve_brokerage(
        self,
        account_id: str,
        *,
        page_size: Optional[int] | Omit = omit,
        page_token: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Get a list of brokerage activities tied to the specified `Account`.

        **⚠️ ALPHA: This endpoint is in early development and subject to breaking
        changes.**

        Args:
          page_size: The maximum number of entries to return in the response. Defaults to 100.

          page_token: Pagination token. Set to the `id` field of the last Activity returned in the
              previous page to get the next page of results.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._get(
            f"/api/v2/accounts/{account_id}/activities/brokerage",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "page_size": page_size,
                        "page_token": page_token,
                    },
                    activity_retrieve_brokerage_params.ActivityRetrieveBrokerageParams,
                ),
            ),
            cast_to=NoneType,
        )


class ActivitiesResourceWithRawResponse:
    def __init__(self, activities: ActivitiesResource) -> None:
        self._activities = activities

        self.retrieve_brokerage = to_raw_response_wrapper(
            activities.retrieve_brokerage,
        )


class AsyncActivitiesResourceWithRawResponse:
    def __init__(self, activities: AsyncActivitiesResource) -> None:
        self._activities = activities

        self.retrieve_brokerage = async_to_raw_response_wrapper(
            activities.retrieve_brokerage,
        )


class ActivitiesResourceWithStreamingResponse:
    def __init__(self, activities: ActivitiesResource) -> None:
        self._activities = activities

        self.retrieve_brokerage = to_streamed_response_wrapper(
            activities.retrieve_brokerage,
        )


class AsyncActivitiesResourceWithStreamingResponse:
    def __init__(self, activities: AsyncActivitiesResource) -> None:
        self._activities = activities

        self.retrieve_brokerage = async_to_streamed_response_wrapper(
            activities.retrieve_brokerage,
        )
