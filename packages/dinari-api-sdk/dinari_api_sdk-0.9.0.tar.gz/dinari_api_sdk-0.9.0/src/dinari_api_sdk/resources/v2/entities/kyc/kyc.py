# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Any, cast
from typing_extensions import Literal, overload

import httpx

from .document import (
    DocumentResource,
    AsyncDocumentResource,
    DocumentResourceWithRawResponse,
    AsyncDocumentResourceWithRawResponse,
    DocumentResourceWithStreamingResponse,
    AsyncDocumentResourceWithStreamingResponse,
)
from ....._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ....._utils import required_args, maybe_transform, async_maybe_transform
from ....._compat import cached_property
from ....._resource import SyncAPIResource, AsyncAPIResource
from ....._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ....._base_client import make_request_options
from .....types.v2.entities import kyc_submit_params
from .....types.v2.entities.kyc_info import KYCInfo
from .....types.v2.entities.us_kyc_check_data_param import UsKYCCheckDataParam
from .....types.v2.entities.baseline_kyc_check_data_param import BaselineKYCCheckDataParam
from .....types.v2.entities.kyc_create_managed_check_response import KYCCreateManagedCheckResponse

__all__ = ["KYCResource", "AsyncKYCResource"]


class KYCResource(SyncAPIResource):
    @cached_property
    def document(self) -> DocumentResource:
        return DocumentResource(self._client)

    @cached_property
    def with_raw_response(self) -> KYCResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return KYCResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> KYCResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#with_streaming_response
        """
        return KYCResourceWithStreamingResponse(self)

    def retrieve(
        self,
        entity_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> KYCInfo:
        """
        Get most recent KYC data of the `Entity`.

        If there are any completed KYC checks, data from the most recent one will be
        returned. If there are no completed KYC checks, the most recent KYC check
        information, regardless of status, will be returned.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not entity_id:
            raise ValueError(f"Expected a non-empty value for `entity_id` but received {entity_id!r}")
        return cast(
            KYCInfo,
            self._get(
                f"/api/v2/entities/{entity_id}/kyc",
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(Any, KYCInfo),  # Union types cannot be passed in as arguments in the type system
            ),
        )

    def create_managed_check(
        self,
        entity_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> KYCCreateManagedCheckResponse:
        """
        Create a Dinari-managed KYC Check and get a URL for your end customer to
        interact with.

        The URL points to a web-based KYC interface that can be presented to the end
        customer for KYC verification. Once the customer completes this KYC flow, the
        KYC check will be created and available in the KYC API.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not entity_id:
            raise ValueError(f"Expected a non-empty value for `entity_id` but received {entity_id!r}")
        return self._post(
            f"/api/v2/entities/{entity_id}/kyc/url",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=KYCCreateManagedCheckResponse,
        )

    @overload
    def submit(
        self,
        entity_id: str,
        *,
        data: BaselineKYCCheckDataParam,
        provider_name: str,
        jurisdiction: Literal["BASELINE"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> KYCInfo:
        """
        Submit KYC data directly, for partners that are provisioned to provide their own
        KYC data.

        This feature is available for everyone in sandbox mode, and for specifically
        provisioned partners in production.

        Args:
          data: KYC data for an `Entity` in the BASELINE jurisdiction.

          provider_name: Name of the KYC provider that provided the KYC information.

          jurisdiction: Jurisdiction of the KYC check.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @overload
    def submit(
        self,
        entity_id: str,
        *,
        data: UsKYCCheckDataParam,
        provider_name: str,
        jurisdiction: Literal["US"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> KYCInfo:
        """
        Submit KYC data directly, for partners that are provisioned to provide their own
        KYC data.

        This feature is available for everyone in sandbox mode, and for specifically
        provisioned partners in production.

        Args:
          data: KYC data for an `Entity` in the US jurisdiction.

          provider_name: Name of the KYC provider that provided the KYC information.

          jurisdiction: Jurisdiction of the KYC check.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @required_args(["data", "provider_name"])
    def submit(
        self,
        entity_id: str,
        *,
        data: BaselineKYCCheckDataParam | UsKYCCheckDataParam,
        provider_name: str,
        jurisdiction: Literal["BASELINE"] | Literal["US"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> KYCInfo:
        if not entity_id:
            raise ValueError(f"Expected a non-empty value for `entity_id` but received {entity_id!r}")
        return cast(
            KYCInfo,
            self._post(
                f"/api/v2/entities/{entity_id}/kyc",
                body=maybe_transform(
                    {
                        "data": data,
                        "provider_name": provider_name,
                        "jurisdiction": jurisdiction,
                    },
                    kyc_submit_params.KYCSubmitParams,
                ),
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(Any, KYCInfo),  # Union types cannot be passed in as arguments in the type system
            ),
        )


class AsyncKYCResource(AsyncAPIResource):
    @cached_property
    def document(self) -> AsyncDocumentResource:
        return AsyncDocumentResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncKYCResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncKYCResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncKYCResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#with_streaming_response
        """
        return AsyncKYCResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        entity_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> KYCInfo:
        """
        Get most recent KYC data of the `Entity`.

        If there are any completed KYC checks, data from the most recent one will be
        returned. If there are no completed KYC checks, the most recent KYC check
        information, regardless of status, will be returned.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not entity_id:
            raise ValueError(f"Expected a non-empty value for `entity_id` but received {entity_id!r}")
        return cast(
            KYCInfo,
            await self._get(
                f"/api/v2/entities/{entity_id}/kyc",
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(Any, KYCInfo),  # Union types cannot be passed in as arguments in the type system
            ),
        )

    async def create_managed_check(
        self,
        entity_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> KYCCreateManagedCheckResponse:
        """
        Create a Dinari-managed KYC Check and get a URL for your end customer to
        interact with.

        The URL points to a web-based KYC interface that can be presented to the end
        customer for KYC verification. Once the customer completes this KYC flow, the
        KYC check will be created and available in the KYC API.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not entity_id:
            raise ValueError(f"Expected a non-empty value for `entity_id` but received {entity_id!r}")
        return await self._post(
            f"/api/v2/entities/{entity_id}/kyc/url",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=KYCCreateManagedCheckResponse,
        )

    @overload
    async def submit(
        self,
        entity_id: str,
        *,
        data: BaselineKYCCheckDataParam,
        provider_name: str,
        jurisdiction: Literal["BASELINE"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> KYCInfo:
        """
        Submit KYC data directly, for partners that are provisioned to provide their own
        KYC data.

        This feature is available for everyone in sandbox mode, and for specifically
        provisioned partners in production.

        Args:
          data: KYC data for an `Entity` in the BASELINE jurisdiction.

          provider_name: Name of the KYC provider that provided the KYC information.

          jurisdiction: Jurisdiction of the KYC check.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @overload
    async def submit(
        self,
        entity_id: str,
        *,
        data: UsKYCCheckDataParam,
        provider_name: str,
        jurisdiction: Literal["US"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> KYCInfo:
        """
        Submit KYC data directly, for partners that are provisioned to provide their own
        KYC data.

        This feature is available for everyone in sandbox mode, and for specifically
        provisioned partners in production.

        Args:
          data: KYC data for an `Entity` in the US jurisdiction.

          provider_name: Name of the KYC provider that provided the KYC information.

          jurisdiction: Jurisdiction of the KYC check.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @required_args(["data", "provider_name"])
    async def submit(
        self,
        entity_id: str,
        *,
        data: BaselineKYCCheckDataParam | UsKYCCheckDataParam,
        provider_name: str,
        jurisdiction: Literal["BASELINE"] | Literal["US"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> KYCInfo:
        if not entity_id:
            raise ValueError(f"Expected a non-empty value for `entity_id` but received {entity_id!r}")
        return cast(
            KYCInfo,
            await self._post(
                f"/api/v2/entities/{entity_id}/kyc",
                body=await async_maybe_transform(
                    {
                        "data": data,
                        "provider_name": provider_name,
                        "jurisdiction": jurisdiction,
                    },
                    kyc_submit_params.KYCSubmitParams,
                ),
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(Any, KYCInfo),  # Union types cannot be passed in as arguments in the type system
            ),
        )


class KYCResourceWithRawResponse:
    def __init__(self, kyc: KYCResource) -> None:
        self._kyc = kyc

        self.retrieve = to_raw_response_wrapper(
            kyc.retrieve,
        )
        self.create_managed_check = to_raw_response_wrapper(
            kyc.create_managed_check,
        )
        self.submit = to_raw_response_wrapper(
            kyc.submit,
        )

    @cached_property
    def document(self) -> DocumentResourceWithRawResponse:
        return DocumentResourceWithRawResponse(self._kyc.document)


class AsyncKYCResourceWithRawResponse:
    def __init__(self, kyc: AsyncKYCResource) -> None:
        self._kyc = kyc

        self.retrieve = async_to_raw_response_wrapper(
            kyc.retrieve,
        )
        self.create_managed_check = async_to_raw_response_wrapper(
            kyc.create_managed_check,
        )
        self.submit = async_to_raw_response_wrapper(
            kyc.submit,
        )

    @cached_property
    def document(self) -> AsyncDocumentResourceWithRawResponse:
        return AsyncDocumentResourceWithRawResponse(self._kyc.document)


class KYCResourceWithStreamingResponse:
    def __init__(self, kyc: KYCResource) -> None:
        self._kyc = kyc

        self.retrieve = to_streamed_response_wrapper(
            kyc.retrieve,
        )
        self.create_managed_check = to_streamed_response_wrapper(
            kyc.create_managed_check,
        )
        self.submit = to_streamed_response_wrapper(
            kyc.submit,
        )

    @cached_property
    def document(self) -> DocumentResourceWithStreamingResponse:
        return DocumentResourceWithStreamingResponse(self._kyc.document)


class AsyncKYCResourceWithStreamingResponse:
    def __init__(self, kyc: AsyncKYCResource) -> None:
        self._kyc = kyc

        self.retrieve = async_to_streamed_response_wrapper(
            kyc.retrieve,
        )
        self.create_managed_check = async_to_streamed_response_wrapper(
            kyc.create_managed_check,
        )
        self.submit = async_to_streamed_response_wrapper(
            kyc.submit,
        )

    @cached_property
    def document(self) -> AsyncDocumentResourceWithStreamingResponse:
        return AsyncDocumentResourceWithStreamingResponse(self._kyc.document)
