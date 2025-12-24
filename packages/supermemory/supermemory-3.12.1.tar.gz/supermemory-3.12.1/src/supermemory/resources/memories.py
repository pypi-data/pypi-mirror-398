# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Mapping, cast
from typing_extensions import Literal

import httpx

from ..types import (
    memory_add_params,
    memory_list_params,
    memory_forget_params,
    memory_update_params,
    memory_upload_file_params,
    memory_update_memory_params,
)
from .._types import Body, Omit, Query, Headers, NoneType, NotGiven, FileTypes, SequenceNotStr, omit, not_given
from .._utils import extract_files, maybe_transform, deepcopy_minimal, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.memory_add_response import MemoryAddResponse
from ..types.memory_get_response import MemoryGetResponse
from ..types.memory_list_response import MemoryListResponse
from ..types.memory_forget_response import MemoryForgetResponse
from ..types.memory_update_response import MemoryUpdateResponse
from ..types.memory_upload_file_response import MemoryUploadFileResponse
from ..types.memory_update_memory_response import MemoryUpdateMemoryResponse

__all__ = ["MemoriesResource", "AsyncMemoriesResource"]


class MemoriesResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> MemoriesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/supermemoryai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return MemoriesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> MemoriesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/supermemoryai/python-sdk#with_streaming_response
        """
        return MemoriesResourceWithStreamingResponse(self)

    def update(
        self,
        id: str,
        *,
        container_tag: str | Omit = omit,
        container_tags: SequenceNotStr[str] | Omit = omit,
        content: str | Omit = omit,
        custom_id: str | Omit = omit,
        metadata: Dict[str, Union[str, float, bool, SequenceNotStr[str]]] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MemoryUpdateResponse:
        """
        Update a document with any content type (text, url, file, etc.) and metadata

        Args:
          container_tag: Optional tag this document should be containerized by. This can be an ID for
              your user, a project ID, or any other identifier you wish to use to group
              documents.

          container_tags: (DEPRECATED: Use containerTag instead) Optional tags this document should be
              containerized by. This can be an ID for your user, a project ID, or any other
              identifier you wish to use to group documents.

          content: The content to extract and process into a document. This can be a URL to a
              website, a PDF, an image, or a video.

              Plaintext: Any plaintext format

              URL: A URL to a website, PDF, image, or video

              We automatically detect the content type from the url's response format.

          custom_id: Optional custom ID of the document. This could be an ID from your database that
              will uniquely identify this document.

          metadata: Optional metadata for the document. This is used to store additional information
              about the document. You can use this to store any additional information you
              need about the document. Metadata can be filtered through. Keys must be strings
              and are case sensitive. Values can be strings, numbers, or booleans. You cannot
              nest objects.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._patch(
            f"/v3/documents/{id}",
            body=maybe_transform(
                {
                    "container_tag": container_tag,
                    "container_tags": container_tags,
                    "content": content,
                    "custom_id": custom_id,
                    "metadata": metadata,
                },
                memory_update_params.MemoryUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemoryUpdateResponse,
        )

    def list(
        self,
        *,
        container_tags: SequenceNotStr[str] | Omit = omit,
        filters: memory_list_params.Filters | Omit = omit,
        include_content: bool | Omit = omit,
        limit: Union[str, float] | Omit = omit,
        order: Literal["asc", "desc"] | Omit = omit,
        page: Union[str, float] | Omit = omit,
        sort: Literal["createdAt", "updatedAt"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MemoryListResponse:
        """
        Retrieves a paginated list of documents with their metadata and workflow status

        Args:
          container_tags: Optional tags this document should be containerized by. This can be an ID for
              your user, a project ID, or any other identifier you wish to use to group
              documents.

          filters: Optional filters to apply to the search. Can be a JSON string or Query object.

          include_content: Whether to include the content field in the response. Warning: This can make
              responses significantly larger.

          limit: Number of items per page

          order: Sort order

          page: Page number to fetch

          sort: Field to sort by

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v3/documents/list",
            body=maybe_transform(
                {
                    "container_tags": container_tags,
                    "filters": filters,
                    "include_content": include_content,
                    "limit": limit,
                    "order": order,
                    "page": page,
                    "sort": sort,
                },
                memory_list_params.MemoryListParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemoryListResponse,
        )

    def delete(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Delete a document by ID or customId

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._delete(
            f"/v3/documents/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def add(
        self,
        *,
        content: str,
        container_tag: str | Omit = omit,
        container_tags: SequenceNotStr[str] | Omit = omit,
        custom_id: str | Omit = omit,
        metadata: Dict[str, Union[str, float, bool, SequenceNotStr[str]]] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MemoryAddResponse:
        """
        Add a document with any content type (text, url, file, etc.) and metadata

        Args:
          content: The content to extract and process into a document. This can be a URL to a
              website, a PDF, an image, or a video.

          container_tag: Optional tag this document should be containerized by. Max 100 characters,
              alphanumeric with hyphens and underscores only.

          custom_id: Optional custom ID of the document. Max 100 characters, alphanumeric with
              hyphens and underscores only.

          metadata: Optional metadata for the document.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v3/documents",
            body=maybe_transform(
                {
                    "content": content,
                    "container_tag": container_tag,
                    "container_tags": container_tags,
                    "custom_id": custom_id,
                    "metadata": metadata,
                },
                memory_add_params.MemoryAddParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemoryAddResponse,
        )

    def forget(
        self,
        *,
        container_tag: str,
        id: str | Omit = omit,
        content: str | Omit = omit,
        reason: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MemoryForgetResponse:
        """Forget (soft delete) a memory entry.

        The memory is marked as forgotten but not
        permanently deleted.

        Args:
          container_tag: Container tag / space identifier. Required to scope the operation.

          id: ID of the memory entry to operate on

          content: Exact content match of the memory entry to operate on. Use this when you don't
              have the ID.

          reason: Optional reason for forgetting this memory

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._delete(
            "/v4/memories",
            body=maybe_transform(
                {
                    "container_tag": container_tag,
                    "id": id,
                    "content": content,
                    "reason": reason,
                },
                memory_forget_params.MemoryForgetParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemoryForgetResponse,
        )

    def get(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MemoryGetResponse:
        """
        Get a document by ID

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/v3/documents/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemoryGetResponse,
        )

    def update_memory(
        self,
        *,
        container_tag: str,
        new_content: str,
        id: str | Omit = omit,
        content: str | Omit = omit,
        metadata: Dict[str, Union[str, float, bool, SequenceNotStr[str]]] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MemoryUpdateMemoryResponse:
        """Update a memory by creating a new version.

        The original memory is preserved with
        isLatest=false.

        Args:
          container_tag: Container tag / space identifier. Required to scope the operation.

          new_content: The new content that will replace the existing memory

          id: ID of the memory entry to operate on

          content: Exact content match of the memory entry to operate on. Use this when you don't
              have the ID.

          metadata: Optional metadata. If not provided, inherits from the previous version.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._patch(
            "/v4/memories",
            body=maybe_transform(
                {
                    "container_tag": container_tag,
                    "new_content": new_content,
                    "id": id,
                    "content": content,
                    "metadata": metadata,
                },
                memory_update_memory_params.MemoryUpdateMemoryParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemoryUpdateMemoryResponse,
        )

    def upload_file(
        self,
        *,
        file: FileTypes,
        container_tags: str | Omit = omit,
        file_type: str | Omit = omit,
        metadata: str | Omit = omit,
        mime_type: str | Omit = omit,
        use_advanced_processing: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MemoryUploadFileResponse:
        """
        Upload a file to be processed

        Args:
          file: File to upload and process

          container_tags: Optional container tags. Can be either a JSON string of an array (e.g.,
              '["user_123", "project_123"]') or a single string (e.g., 'user_123'). Single
              strings will be automatically converted to an array.

          file_type:
              Optional file type override to force specific processing behavior. Valid values:
              text, pdf, tweet, google_doc, google_slide, google_sheet, image, video,
              notion_doc, webpage, onedrive

          metadata: Optional metadata for the document as a JSON string. This is used to store
              additional information about the document. Keys must be strings and values can
              be strings, numbers, or booleans.

          mime_type: Required when fileType is 'image' or 'video'. Specifies the exact MIME type to
              use (e.g., 'image/png', 'image/jpeg', 'video/mp4', 'video/webm')

          use_advanced_processing: Use advanced processing with Reducto for better PDF extraction and chunking.
              This costs 3x tokens but provides superior quality for complex documents.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        body = deepcopy_minimal(
            {
                "file": file,
                "container_tags": container_tags,
                "file_type": file_type,
                "metadata": metadata,
                "mime_type": mime_type,
                "use_advanced_processing": use_advanced_processing,
            }
        )
        files = extract_files(cast(Mapping[str, object], body), paths=[["file"]])
        # It should be noted that the actual Content-Type header that will be
        # sent to the server will contain a `boundary` parameter, e.g.
        # multipart/form-data; boundary=---abc--
        extra_headers = {"Content-Type": "multipart/form-data", **(extra_headers or {})}
        return self._post(
            "/v3/documents/file",
            body=maybe_transform(body, memory_upload_file_params.MemoryUploadFileParams),
            files=files,
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemoryUploadFileResponse,
        )


class AsyncMemoriesResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncMemoriesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/supermemoryai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncMemoriesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncMemoriesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/supermemoryai/python-sdk#with_streaming_response
        """
        return AsyncMemoriesResourceWithStreamingResponse(self)

    async def update(
        self,
        id: str,
        *,
        container_tag: str | Omit = omit,
        container_tags: SequenceNotStr[str] | Omit = omit,
        content: str | Omit = omit,
        custom_id: str | Omit = omit,
        metadata: Dict[str, Union[str, float, bool, SequenceNotStr[str]]] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MemoryUpdateResponse:
        """
        Update a document with any content type (text, url, file, etc.) and metadata

        Args:
          container_tag: Optional tag this document should be containerized by. This can be an ID for
              your user, a project ID, or any other identifier you wish to use to group
              documents.

          container_tags: (DEPRECATED: Use containerTag instead) Optional tags this document should be
              containerized by. This can be an ID for your user, a project ID, or any other
              identifier you wish to use to group documents.

          content: The content to extract and process into a document. This can be a URL to a
              website, a PDF, an image, or a video.

              Plaintext: Any plaintext format

              URL: A URL to a website, PDF, image, or video

              We automatically detect the content type from the url's response format.

          custom_id: Optional custom ID of the document. This could be an ID from your database that
              will uniquely identify this document.

          metadata: Optional metadata for the document. This is used to store additional information
              about the document. You can use this to store any additional information you
              need about the document. Metadata can be filtered through. Keys must be strings
              and are case sensitive. Values can be strings, numbers, or booleans. You cannot
              nest objects.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._patch(
            f"/v3/documents/{id}",
            body=await async_maybe_transform(
                {
                    "container_tag": container_tag,
                    "container_tags": container_tags,
                    "content": content,
                    "custom_id": custom_id,
                    "metadata": metadata,
                },
                memory_update_params.MemoryUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemoryUpdateResponse,
        )

    async def list(
        self,
        *,
        container_tags: SequenceNotStr[str] | Omit = omit,
        filters: memory_list_params.Filters | Omit = omit,
        include_content: bool | Omit = omit,
        limit: Union[str, float] | Omit = omit,
        order: Literal["asc", "desc"] | Omit = omit,
        page: Union[str, float] | Omit = omit,
        sort: Literal["createdAt", "updatedAt"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MemoryListResponse:
        """
        Retrieves a paginated list of documents with their metadata and workflow status

        Args:
          container_tags: Optional tags this document should be containerized by. This can be an ID for
              your user, a project ID, or any other identifier you wish to use to group
              documents.

          filters: Optional filters to apply to the search. Can be a JSON string or Query object.

          include_content: Whether to include the content field in the response. Warning: This can make
              responses significantly larger.

          limit: Number of items per page

          order: Sort order

          page: Page number to fetch

          sort: Field to sort by

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v3/documents/list",
            body=await async_maybe_transform(
                {
                    "container_tags": container_tags,
                    "filters": filters,
                    "include_content": include_content,
                    "limit": limit,
                    "order": order,
                    "page": page,
                    "sort": sort,
                },
                memory_list_params.MemoryListParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemoryListResponse,
        )

    async def delete(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Delete a document by ID or customId

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._delete(
            f"/v3/documents/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def add(
        self,
        *,
        content: str,
        container_tag: str | Omit = omit,
        container_tags: SequenceNotStr[str] | Omit = omit,
        custom_id: str | Omit = omit,
        metadata: Dict[str, Union[str, float, bool, SequenceNotStr[str]]] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MemoryAddResponse:
        """
        Add a document with any content type (text, url, file, etc.) and metadata

        Args:
          content: The content to extract and process into a document. This can be a URL to a
              website, a PDF, an image, or a video.

          container_tag: Optional tag this document should be containerized by. Max 100 characters,
              alphanumeric with hyphens and underscores only.

          custom_id: Optional custom ID of the document. Max 100 characters, alphanumeric with
              hyphens and underscores only.

          metadata: Optional metadata for the document.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v3/documents",
            body=await async_maybe_transform(
                {
                    "content": content,
                    "container_tag": container_tag,
                    "container_tags": container_tags,
                    "custom_id": custom_id,
                    "metadata": metadata,
                },
                memory_add_params.MemoryAddParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemoryAddResponse,
        )

    async def forget(
        self,
        *,
        container_tag: str,
        id: str | Omit = omit,
        content: str | Omit = omit,
        reason: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MemoryForgetResponse:
        """Forget (soft delete) a memory entry.

        The memory is marked as forgotten but not
        permanently deleted.

        Args:
          container_tag: Container tag / space identifier. Required to scope the operation.

          id: ID of the memory entry to operate on

          content: Exact content match of the memory entry to operate on. Use this when you don't
              have the ID.

          reason: Optional reason for forgetting this memory

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._delete(
            "/v4/memories",
            body=await async_maybe_transform(
                {
                    "container_tag": container_tag,
                    "id": id,
                    "content": content,
                    "reason": reason,
                },
                memory_forget_params.MemoryForgetParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemoryForgetResponse,
        )

    async def get(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MemoryGetResponse:
        """
        Get a document by ID

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/v3/documents/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemoryGetResponse,
        )

    async def update_memory(
        self,
        *,
        container_tag: str,
        new_content: str,
        id: str | Omit = omit,
        content: str | Omit = omit,
        metadata: Dict[str, Union[str, float, bool, SequenceNotStr[str]]] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MemoryUpdateMemoryResponse:
        """Update a memory by creating a new version.

        The original memory is preserved with
        isLatest=false.

        Args:
          container_tag: Container tag / space identifier. Required to scope the operation.

          new_content: The new content that will replace the existing memory

          id: ID of the memory entry to operate on

          content: Exact content match of the memory entry to operate on. Use this when you don't
              have the ID.

          metadata: Optional metadata. If not provided, inherits from the previous version.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._patch(
            "/v4/memories",
            body=await async_maybe_transform(
                {
                    "container_tag": container_tag,
                    "new_content": new_content,
                    "id": id,
                    "content": content,
                    "metadata": metadata,
                },
                memory_update_memory_params.MemoryUpdateMemoryParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemoryUpdateMemoryResponse,
        )

    async def upload_file(
        self,
        *,
        file: FileTypes,
        container_tags: str | Omit = omit,
        file_type: str | Omit = omit,
        metadata: str | Omit = omit,
        mime_type: str | Omit = omit,
        use_advanced_processing: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MemoryUploadFileResponse:
        """
        Upload a file to be processed

        Args:
          file: File to upload and process

          container_tags: Optional container tags. Can be either a JSON string of an array (e.g.,
              '["user_123", "project_123"]') or a single string (e.g., 'user_123'). Single
              strings will be automatically converted to an array.

          file_type:
              Optional file type override to force specific processing behavior. Valid values:
              text, pdf, tweet, google_doc, google_slide, google_sheet, image, video,
              notion_doc, webpage, onedrive

          metadata: Optional metadata for the document as a JSON string. This is used to store
              additional information about the document. Keys must be strings and values can
              be strings, numbers, or booleans.

          mime_type: Required when fileType is 'image' or 'video'. Specifies the exact MIME type to
              use (e.g., 'image/png', 'image/jpeg', 'video/mp4', 'video/webm')

          use_advanced_processing: Use advanced processing with Reducto for better PDF extraction and chunking.
              This costs 3x tokens but provides superior quality for complex documents.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        body = deepcopy_minimal(
            {
                "file": file,
                "container_tags": container_tags,
                "file_type": file_type,
                "metadata": metadata,
                "mime_type": mime_type,
                "use_advanced_processing": use_advanced_processing,
            }
        )
        files = extract_files(cast(Mapping[str, object], body), paths=[["file"]])
        # It should be noted that the actual Content-Type header that will be
        # sent to the server will contain a `boundary` parameter, e.g.
        # multipart/form-data; boundary=---abc--
        extra_headers = {"Content-Type": "multipart/form-data", **(extra_headers or {})}
        return await self._post(
            "/v3/documents/file",
            body=await async_maybe_transform(body, memory_upload_file_params.MemoryUploadFileParams),
            files=files,
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemoryUploadFileResponse,
        )


class MemoriesResourceWithRawResponse:
    def __init__(self, memories: MemoriesResource) -> None:
        self._memories = memories

        self.update = to_raw_response_wrapper(
            memories.update,
        )
        self.list = to_raw_response_wrapper(
            memories.list,
        )
        self.delete = to_raw_response_wrapper(
            memories.delete,
        )
        self.add = to_raw_response_wrapper(
            memories.add,
        )
        self.forget = to_raw_response_wrapper(
            memories.forget,
        )
        self.get = to_raw_response_wrapper(
            memories.get,
        )
        self.update_memory = to_raw_response_wrapper(
            memories.update_memory,
        )
        self.upload_file = to_raw_response_wrapper(
            memories.upload_file,
        )


class AsyncMemoriesResourceWithRawResponse:
    def __init__(self, memories: AsyncMemoriesResource) -> None:
        self._memories = memories

        self.update = async_to_raw_response_wrapper(
            memories.update,
        )
        self.list = async_to_raw_response_wrapper(
            memories.list,
        )
        self.delete = async_to_raw_response_wrapper(
            memories.delete,
        )
        self.add = async_to_raw_response_wrapper(
            memories.add,
        )
        self.forget = async_to_raw_response_wrapper(
            memories.forget,
        )
        self.get = async_to_raw_response_wrapper(
            memories.get,
        )
        self.update_memory = async_to_raw_response_wrapper(
            memories.update_memory,
        )
        self.upload_file = async_to_raw_response_wrapper(
            memories.upload_file,
        )


class MemoriesResourceWithStreamingResponse:
    def __init__(self, memories: MemoriesResource) -> None:
        self._memories = memories

        self.update = to_streamed_response_wrapper(
            memories.update,
        )
        self.list = to_streamed_response_wrapper(
            memories.list,
        )
        self.delete = to_streamed_response_wrapper(
            memories.delete,
        )
        self.add = to_streamed_response_wrapper(
            memories.add,
        )
        self.forget = to_streamed_response_wrapper(
            memories.forget,
        )
        self.get = to_streamed_response_wrapper(
            memories.get,
        )
        self.update_memory = to_streamed_response_wrapper(
            memories.update_memory,
        )
        self.upload_file = to_streamed_response_wrapper(
            memories.upload_file,
        )


class AsyncMemoriesResourceWithStreamingResponse:
    def __init__(self, memories: AsyncMemoriesResource) -> None:
        self._memories = memories

        self.update = async_to_streamed_response_wrapper(
            memories.update,
        )
        self.list = async_to_streamed_response_wrapper(
            memories.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            memories.delete,
        )
        self.add = async_to_streamed_response_wrapper(
            memories.add,
        )
        self.forget = async_to_streamed_response_wrapper(
            memories.forget,
        )
        self.get = async_to_streamed_response_wrapper(
            memories.get,
        )
        self.update_memory = async_to_streamed_response_wrapper(
            memories.update_memory,
        )
        self.upload_file = async_to_streamed_response_wrapper(
            memories.upload_file,
        )
