# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Mapping, cast

import httpx

from ....._types import Body, Query, Headers, NotGiven, FileTypes, not_given
from ....._utils import extract_files, maybe_transform, deepcopy_minimal, async_maybe_transform
from ....._compat import cached_property
from ....._resource import SyncAPIResource, AsyncAPIResource
from ....._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ....._base_client import make_request_options
from .....types.v2.entities.kyc import KYCDocumentType, document_upload_params
from .....types.v2.entities.kyc.kyc_document import KYCDocument
from .....types.v2.entities.kyc.kyc_document_type import KYCDocumentType
from .....types.v2.entities.kyc.document_retrieve_response import DocumentRetrieveResponse

__all__ = ["DocumentResource", "AsyncDocumentResource"]


class DocumentResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> DocumentResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return DocumentResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> DocumentResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#with_streaming_response
        """
        return DocumentResourceWithStreamingResponse(self)

    def retrieve(
        self,
        kyc_id: str,
        *,
        entity_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DocumentRetrieveResponse:
        """
        Get uploaded documents for a KYC check

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not entity_id:
            raise ValueError(f"Expected a non-empty value for `entity_id` but received {entity_id!r}")
        if not kyc_id:
            raise ValueError(f"Expected a non-empty value for `kyc_id` but received {kyc_id!r}")
        return self._get(
            f"/api/v2/entities/{entity_id}/kyc/{kyc_id}/document",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DocumentRetrieveResponse,
        )

    def upload(
        self,
        kyc_id: str,
        *,
        entity_id: str,
        document_type: KYCDocumentType,
        file: FileTypes,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> KYCDocument:
        """
        Upload KYC-related documentation for partners that are provisioned to provide
        their own KYC data.

        Args:
          document_type: Type of `KYCDocument` to be uploaded.

          file: File to be uploaded. Must be a valid image or PDF file (jpg, jpeg, png, pdf)
              less than 10MB in size.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not entity_id:
            raise ValueError(f"Expected a non-empty value for `entity_id` but received {entity_id!r}")
        if not kyc_id:
            raise ValueError(f"Expected a non-empty value for `kyc_id` but received {kyc_id!r}")
        body = deepcopy_minimal({"file": file})
        files = extract_files(cast(Mapping[str, object], body), paths=[["file"]])
        # It should be noted that the actual Content-Type header that will be
        # sent to the server will contain a `boundary` parameter, e.g.
        # multipart/form-data; boundary=---abc--
        extra_headers = {"Content-Type": "multipart/form-data", **(extra_headers or {})}
        return self._post(
            f"/api/v2/entities/{entity_id}/kyc/{kyc_id}/document",
            body=maybe_transform(body, document_upload_params.DocumentUploadParams),
            files=files,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"document_type": document_type}, document_upload_params.DocumentUploadParams),
            ),
            cast_to=KYCDocument,
        )


class AsyncDocumentResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncDocumentResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncDocumentResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncDocumentResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dinaricrypto/dinari-api-sdk-python#with_streaming_response
        """
        return AsyncDocumentResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        kyc_id: str,
        *,
        entity_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DocumentRetrieveResponse:
        """
        Get uploaded documents for a KYC check

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not entity_id:
            raise ValueError(f"Expected a non-empty value for `entity_id` but received {entity_id!r}")
        if not kyc_id:
            raise ValueError(f"Expected a non-empty value for `kyc_id` but received {kyc_id!r}")
        return await self._get(
            f"/api/v2/entities/{entity_id}/kyc/{kyc_id}/document",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DocumentRetrieveResponse,
        )

    async def upload(
        self,
        kyc_id: str,
        *,
        entity_id: str,
        document_type: KYCDocumentType,
        file: FileTypes,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> KYCDocument:
        """
        Upload KYC-related documentation for partners that are provisioned to provide
        their own KYC data.

        Args:
          document_type: Type of `KYCDocument` to be uploaded.

          file: File to be uploaded. Must be a valid image or PDF file (jpg, jpeg, png, pdf)
              less than 10MB in size.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not entity_id:
            raise ValueError(f"Expected a non-empty value for `entity_id` but received {entity_id!r}")
        if not kyc_id:
            raise ValueError(f"Expected a non-empty value for `kyc_id` but received {kyc_id!r}")
        body = deepcopy_minimal({"file": file})
        files = extract_files(cast(Mapping[str, object], body), paths=[["file"]])
        # It should be noted that the actual Content-Type header that will be
        # sent to the server will contain a `boundary` parameter, e.g.
        # multipart/form-data; boundary=---abc--
        extra_headers = {"Content-Type": "multipart/form-data", **(extra_headers or {})}
        return await self._post(
            f"/api/v2/entities/{entity_id}/kyc/{kyc_id}/document",
            body=await async_maybe_transform(body, document_upload_params.DocumentUploadParams),
            files=files,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"document_type": document_type}, document_upload_params.DocumentUploadParams
                ),
            ),
            cast_to=KYCDocument,
        )


class DocumentResourceWithRawResponse:
    def __init__(self, document: DocumentResource) -> None:
        self._document = document

        self.retrieve = to_raw_response_wrapper(
            document.retrieve,
        )
        self.upload = to_raw_response_wrapper(
            document.upload,
        )


class AsyncDocumentResourceWithRawResponse:
    def __init__(self, document: AsyncDocumentResource) -> None:
        self._document = document

        self.retrieve = async_to_raw_response_wrapper(
            document.retrieve,
        )
        self.upload = async_to_raw_response_wrapper(
            document.upload,
        )


class DocumentResourceWithStreamingResponse:
    def __init__(self, document: DocumentResource) -> None:
        self._document = document

        self.retrieve = to_streamed_response_wrapper(
            document.retrieve,
        )
        self.upload = to_streamed_response_wrapper(
            document.upload,
        )


class AsyncDocumentResourceWithStreamingResponse:
    def __init__(self, document: AsyncDocumentResource) -> None:
        self._document = document

        self.retrieve = async_to_streamed_response_wrapper(
            document.retrieve,
        )
        self.upload = async_to_streamed_response_wrapper(
            document.upload,
        )
