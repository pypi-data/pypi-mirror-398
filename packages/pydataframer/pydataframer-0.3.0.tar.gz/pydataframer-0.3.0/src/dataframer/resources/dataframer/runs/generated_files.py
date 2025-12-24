# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ...._types import Body, Query, Headers, NotGiven, not_given
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    BinaryAPIResponse,
    AsyncBinaryAPIResponse,
    StreamedBinaryAPIResponse,
    AsyncStreamedBinaryAPIResponse,
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    to_custom_raw_response_wrapper,
    async_to_streamed_response_wrapper,
    to_custom_streamed_response_wrapper,
    async_to_custom_raw_response_wrapper,
    async_to_custom_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.dataframer.runs.generated_file_list_response import GeneratedFileListResponse
from ....types.dataframer.runs.generated_file_download_response import GeneratedFileDownloadResponse
from ....types.dataframer.runs.generated_file_get_content_response import GeneratedFileGetContentResponse

__all__ = ["GeneratedFilesResource", "AsyncGeneratedFilesResource"]


class GeneratedFilesResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> GeneratedFilesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#accessing-raw-response-data-eg-headers
        """
        return GeneratedFilesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> GeneratedFilesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#with_streaming_response
        """
        return GeneratedFilesResourceWithStreamingResponse(self)

    def list(
        self,
        run_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> GeneratedFileListResponse:
        """
        Get all generated files from a run

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return self._get(
            f"/api/dataframer/runs/{run_id}/generated-files/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GeneratedFileListResponse,
        )

    def download(
        self,
        file_id: str,
        *,
        run_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> GeneratedFileDownloadResponse:
        """
        Generate presigned URL for downloading a generated file

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        if not file_id:
            raise ValueError(f"Expected a non-empty value for `file_id` but received {file_id!r}")
        return self._get(
            f"/api/dataframer/runs/{run_id}/generated-files/{file_id}/download/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GeneratedFileDownloadResponse,
        )

    def download_all(
        self,
        run_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BinaryAPIResponse:
        """
        Download all generated files and their metadata as a single ZIP archive.

        The ZIP file contains:

        - **All generated files** with proper folder structure (for MULTI_FOLDER
          datasets)
        - **Metadata files** (.metadata) with evaluation classifications and tags
        - **Top-level metadata** (top_level.metadata) with evaluation summary and
          distribution analysis

        The metadata is automatically generated when evaluation completes and includes:

        - Per-file/per-folder tags (classifications from evaluation)
        - Human annotation tags (if any)
        - Distribution analysis comparing expected vs observed distributions
        - Conformance scores and explanations

        This endpoint is used by the web UI for downloads and is the recommended way to
        download evaluated results.

        **Benefits:**

        - Single HTTP request downloads everything
        - Preserves folder structure automatically
        - Includes all metadata pre-formatted
        - More efficient for large datasets
        - Consistent with UI behavior

        **Use Cases:**

        - Download evaluated dataset with tags for analysis
        - Export results for external tools
        - Backup generated samples with metadata
        - Share evaluated results with team members

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        extra_headers = {"Accept": "application/zip", **(extra_headers or {})}
        return self._get(
            f"/api/dataframer/runs/{run_id}/generated-files/download-all/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BinaryAPIResponse,
        )

    def get_content(
        self,
        file_id: str,
        *,
        run_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> GeneratedFileGetContentResponse:
        """
        Get content of a generated file for viewing

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        if not file_id:
            raise ValueError(f"Expected a non-empty value for `file_id` but received {file_id!r}")
        return self._get(
            f"/api/dataframer/runs/{run_id}/generated-files/{file_id}/content/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GeneratedFileGetContentResponse,
        )


class AsyncGeneratedFilesResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncGeneratedFilesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncGeneratedFilesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncGeneratedFilesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#with_streaming_response
        """
        return AsyncGeneratedFilesResourceWithStreamingResponse(self)

    async def list(
        self,
        run_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> GeneratedFileListResponse:
        """
        Get all generated files from a run

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return await self._get(
            f"/api/dataframer/runs/{run_id}/generated-files/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GeneratedFileListResponse,
        )

    async def download(
        self,
        file_id: str,
        *,
        run_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> GeneratedFileDownloadResponse:
        """
        Generate presigned URL for downloading a generated file

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        if not file_id:
            raise ValueError(f"Expected a non-empty value for `file_id` but received {file_id!r}")
        return await self._get(
            f"/api/dataframer/runs/{run_id}/generated-files/{file_id}/download/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GeneratedFileDownloadResponse,
        )

    async def download_all(
        self,
        run_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncBinaryAPIResponse:
        """
        Download all generated files and their metadata as a single ZIP archive.

        The ZIP file contains:

        - **All generated files** with proper folder structure (for MULTI_FOLDER
          datasets)
        - **Metadata files** (.metadata) with evaluation classifications and tags
        - **Top-level metadata** (top_level.metadata) with evaluation summary and
          distribution analysis

        The metadata is automatically generated when evaluation completes and includes:

        - Per-file/per-folder tags (classifications from evaluation)
        - Human annotation tags (if any)
        - Distribution analysis comparing expected vs observed distributions
        - Conformance scores and explanations

        This endpoint is used by the web UI for downloads and is the recommended way to
        download evaluated results.

        **Benefits:**

        - Single HTTP request downloads everything
        - Preserves folder structure automatically
        - Includes all metadata pre-formatted
        - More efficient for large datasets
        - Consistent with UI behavior

        **Use Cases:**

        - Download evaluated dataset with tags for analysis
        - Export results for external tools
        - Backup generated samples with metadata
        - Share evaluated results with team members

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        extra_headers = {"Accept": "application/zip", **(extra_headers or {})}
        return await self._get(
            f"/api/dataframer/runs/{run_id}/generated-files/download-all/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AsyncBinaryAPIResponse,
        )

    async def get_content(
        self,
        file_id: str,
        *,
        run_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> GeneratedFileGetContentResponse:
        """
        Get content of a generated file for viewing

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        if not file_id:
            raise ValueError(f"Expected a non-empty value for `file_id` but received {file_id!r}")
        return await self._get(
            f"/api/dataframer/runs/{run_id}/generated-files/{file_id}/content/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GeneratedFileGetContentResponse,
        )


class GeneratedFilesResourceWithRawResponse:
    def __init__(self, generated_files: GeneratedFilesResource) -> None:
        self._generated_files = generated_files

        self.list = to_raw_response_wrapper(
            generated_files.list,
        )
        self.download = to_raw_response_wrapper(
            generated_files.download,
        )
        self.download_all = to_custom_raw_response_wrapper(
            generated_files.download_all,
            BinaryAPIResponse,
        )
        self.get_content = to_raw_response_wrapper(
            generated_files.get_content,
        )


class AsyncGeneratedFilesResourceWithRawResponse:
    def __init__(self, generated_files: AsyncGeneratedFilesResource) -> None:
        self._generated_files = generated_files

        self.list = async_to_raw_response_wrapper(
            generated_files.list,
        )
        self.download = async_to_raw_response_wrapper(
            generated_files.download,
        )
        self.download_all = async_to_custom_raw_response_wrapper(
            generated_files.download_all,
            AsyncBinaryAPIResponse,
        )
        self.get_content = async_to_raw_response_wrapper(
            generated_files.get_content,
        )


class GeneratedFilesResourceWithStreamingResponse:
    def __init__(self, generated_files: GeneratedFilesResource) -> None:
        self._generated_files = generated_files

        self.list = to_streamed_response_wrapper(
            generated_files.list,
        )
        self.download = to_streamed_response_wrapper(
            generated_files.download,
        )
        self.download_all = to_custom_streamed_response_wrapper(
            generated_files.download_all,
            StreamedBinaryAPIResponse,
        )
        self.get_content = to_streamed_response_wrapper(
            generated_files.get_content,
        )


class AsyncGeneratedFilesResourceWithStreamingResponse:
    def __init__(self, generated_files: AsyncGeneratedFilesResource) -> None:
        self._generated_files = generated_files

        self.list = async_to_streamed_response_wrapper(
            generated_files.list,
        )
        self.download = async_to_streamed_response_wrapper(
            generated_files.download,
        )
        self.download_all = async_to_custom_streamed_response_wrapper(
            generated_files.download_all,
            AsyncStreamedBinaryAPIResponse,
        )
        self.get_content = async_to_streamed_response_wrapper(
            generated_files.get_content,
        )
