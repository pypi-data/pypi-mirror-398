# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Mapping, cast
from typing_extensions import Literal

import httpx

from ..._types import (
    Body,
    Omit,
    Query,
    Headers,
    NoneType,
    NotGiven,
    FileTypes,
    SequenceNotStr,
    omit,
    not_given,
)
from ..._utils import extract_files, maybe_transform, deepcopy_minimal, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.dataframer import dataset_update_params, dataset_create_from_zip_params, dataset_create_with_files_params
from ...types.dataframer.dataset_list_response import DatasetListResponse
from ...types.dataframer.dataset_update_response import DatasetUpdateResponse
from ...types.dataframer.dataset_retrieve_response import DatasetRetrieveResponse
from ...types.dataframer.dataset_list_files_response import DatasetListFilesResponse
from ...types.dataframer.dataset_list_folders_response import DatasetListFoldersResponse
from ...types.dataframer.dataset_create_from_zip_response import DatasetCreateFromZipResponse
from ...types.dataframer.dataset_create_with_files_response import DatasetCreateWithFilesResponse

__all__ = ["DatasetsResource", "AsyncDatasetsResource"]


class DatasetsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> DatasetsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#accessing-raw-response-data-eg-headers
        """
        return DatasetsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> DatasetsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#with_streaming_response
        """
        return DatasetsResourceWithStreamingResponse(self)

    def retrieve(
        self,
        dataset_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DatasetRetrieveResponse:
        """
        Retrieve detailed information about a specific dataset including all files and
        folders.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not dataset_id:
            raise ValueError(f"Expected a non-empty value for `dataset_id` but received {dataset_id!r}")
        return self._get(
            f"/api/dataframer/datasets/{dataset_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DatasetRetrieveResponse,
        )

    def update(
        self,
        dataset_id: str,
        *,
        description: str | Omit = omit,
        name: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DatasetUpdateResponse:
        """Update dataset name and description.

        **Note:** Only metadata can be updated.

        Dataset type and structure cannot be
        changed after creation.

        Args:
          description: New dataset description

          name: New dataset name

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not dataset_id:
            raise ValueError(f"Expected a non-empty value for `dataset_id` but received {dataset_id!r}")
        return self._put(
            f"/api/dataframer/datasets/{dataset_id}/",
            body=maybe_transform(
                {
                    "description": description,
                    "name": name,
                },
                dataset_update_params.DatasetUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DatasetUpdateResponse,
        )

    def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DatasetListResponse:
        """
        Retrieve all datasets belonging to the authenticated user's company.

        Returns dataset metadata including:

        - Dataset type (SINGLE_FILE, MULTI_FILE, MULTI_FOLDER)
        - File and folder counts
        - Short sample compatibility status
        - Creation information
        """
        return self._get(
            "/api/dataframer/datasets/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DatasetListResponse,
        )

    def delete(
        self,
        dataset_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Delete a dataset and all associated files from storage.

        **Warning:** This action cannot be undone. All files will be permanently deleted
        from S3.

        **Restrictions:** Cannot delete a dataset that is referenced by any specs.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not dataset_id:
            raise ValueError(f"Expected a non-empty value for `dataset_id` but received {dataset_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._delete(
            f"/api/dataframer/datasets/{dataset_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def create_from_zip(
        self,
        *,
        name: str,
        zip_file: FileTypes,
        description: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DatasetCreateFromZipResponse:
        """Upload a ZIP file containing dataset files.

        The backend will automatically:

        1. Extract and analyze the ZIP structure
        2. Auto-detect dataset type (SINGLE_FILE/MULTI_FILE/MULTI_FOLDER)
        3. Validate file types and sizes
        4. Create dataset with proper folder structure

        **Supported ZIP Structures:**

        1. **SINGLE_FILE**: ZIP contains exactly one valid file

           - Supported: CSV, JSON, JSONL
           - Max size: 50MB

        2. **MULTI_FILE**: ZIP contains multiple files in root

           - Supported: TXT, MD, JSON, CSV, JSONL
           - Max: 1MB per file, 50MB total, 1000 files

        3. **MULTI_FOLDER**: ZIP contains multiple folders with files
           - Supported: TXT, MD, JSON, CSV, JSONL
           - Max: 1MB per file, 50MB total, 20 files per folder
           - Requires at least 2 folders

        **Benefits:**

        - Single upload operation
        - Automatic structure detection
        - No need to specify dataset_type or folder_names
        - Works for all dataset types

        Args:
          name: Dataset name (unique within company)

          zip_file: ZIP file containing dataset files

          description: Optional dataset description

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        body = deepcopy_minimal(
            {
                "name": name,
                "zip_file": zip_file,
                "description": description,
            }
        )
        files = extract_files(cast(Mapping[str, object], body), paths=[["zip_file"]])
        # It should be noted that the actual Content-Type header that will be
        # sent to the server will contain a `boundary` parameter, e.g.
        # multipart/form-data; boundary=---abc--
        extra_headers = {"Content-Type": "multipart/form-data", **(extra_headers or {})}
        return self._post(
            "/api/dataframer/datasets/create-from-zip/",
            body=maybe_transform(body, dataset_create_from_zip_params.DatasetCreateFromZipParams),
            files=files,
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DatasetCreateFromZipResponse,
        )

    def create_with_files(
        self,
        *,
        dataset_type: Literal["SINGLE_FILE", "MULTI_FILE", "MULTI_FOLDER"],
        name: str,
        config_json: str | Omit = omit,
        csv_headers: str | Omit = omit,
        description: str | Omit = omit,
        file: FileTypes | Omit = omit,
        files: SequenceNotStr[FileTypes] | Omit = omit,
        folder_names: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DatasetCreateWithFilesResponse:
        """Create a new dataset and upload files in a single atomic operation.

        Files are
        validated first, and dataset is only created if validation passes. **Empty
        datasets cannot be created with this endpoint.**

        **Dataset Types:**

        1. **SINGLE_FILE**: Upload one file

           - Supported types: CSV, JSON, JSONL only
           - Max size: 50MB
           - Send file as 'file' parameter
           - Optional: 'csv_headers' as JSON array for CSV files

        2. **MULTI_FILE**: Upload multiple individual files

           - Supported types: TXT, MD, JSON, CSV, JSONL
           - Max size: 1MB per file, 50MB total
           - Max 1000 files per dataset
           - Send files as 'files' array parameter

        3. **MULTI_FOLDER**: Upload files in folders
           - Supported types: TXT, MD, JSON, CSV, JSONL
           - Max size: 1MB per file, 50MB total
           - Minimum 2 folders required, each folder must have at least 1 file
           - Max 1000 files total, 20 files per folder
           - Send files as 'files' array parameter
           - Send corresponding folder names as 'folder_names' array (parallel arrays)

        **Request Format:**

        - All requests must be multipart/form-data
        - Dataset metadata: name, description, dataset_type, config_json
        - Files depend on dataset_type (see above)

        **Benefits:**

        - Atomic operation - either everything succeeds or nothing is created
        - Validation before dataset creation
        - No empty datasets
        - Single API call instead of two

        Args:
          dataset_type: Dataset type: SINGLE_FILE, MULTI_FILE, or MULTI_FOLDER

          name: Dataset name (unique within company)

          config_json: Optional configuration JSON as string

          csv_headers: Optional CSV headers as JSON array for SINGLE_FILE CSV files

          description: Optional dataset description

          file: Single file for SINGLE_FILE dataset type

          files: Multiple files for MULTI_FILE or MULTI_FOLDER dataset types. Each file will be
              sent as a separate form field named 'files'. For MULTI_FOLDER: minimum 2 files
              required (at least 1 file per folder, across at least 2 folders).

          folder_names: Folder names for MULTI_FOLDER (parallel array with files). Each folder name is
              sent as a separate 'folder_names' form field. Minimum 2 unique folder names
              required.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        body = deepcopy_minimal(
            {
                "dataset_type": dataset_type,
                "name": name,
                "config_json": config_json,
                "csv_headers": csv_headers,
                "description": description,
                "file": file,
                "files": files,
                "folder_names": folder_names,
            }
        )
        extracted_files = extract_files(cast(Mapping[str, object], body), paths=[["file"], ["files", "<array>"]])
        # It should be noted that the actual Content-Type header that will be
        # sent to the server will contain a `boundary` parameter, e.g.
        # multipart/form-data; boundary=---abc--
        extra_headers = {"Content-Type": "multipart/form-data", **(extra_headers or {})}
        return self._post(
            "/api/dataframer/datasets/create/",
            body=maybe_transform(body, dataset_create_with_files_params.DatasetCreateWithFilesParams),
            files=extracted_files,
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DatasetCreateWithFilesResponse,
        )

    def list_files(
        self,
        dataset_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DatasetListFilesResponse:
        """
        Get all files in a specific dataset.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not dataset_id:
            raise ValueError(f"Expected a non-empty value for `dataset_id` but received {dataset_id!r}")
        return self._get(
            f"/api/dataframer/datasets/{dataset_id}/files/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DatasetListFilesResponse,
        )

    def list_folders(
        self,
        dataset_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DatasetListFoldersResponse:
        """
        Get all folders in a specific dataset.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not dataset_id:
            raise ValueError(f"Expected a non-empty value for `dataset_id` but received {dataset_id!r}")
        return self._get(
            f"/api/dataframer/datasets/{dataset_id}/folders/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DatasetListFoldersResponse,
        )


class AsyncDatasetsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncDatasetsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncDatasetsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncDatasetsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#with_streaming_response
        """
        return AsyncDatasetsResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        dataset_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DatasetRetrieveResponse:
        """
        Retrieve detailed information about a specific dataset including all files and
        folders.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not dataset_id:
            raise ValueError(f"Expected a non-empty value for `dataset_id` but received {dataset_id!r}")
        return await self._get(
            f"/api/dataframer/datasets/{dataset_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DatasetRetrieveResponse,
        )

    async def update(
        self,
        dataset_id: str,
        *,
        description: str | Omit = omit,
        name: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DatasetUpdateResponse:
        """Update dataset name and description.

        **Note:** Only metadata can be updated.

        Dataset type and structure cannot be
        changed after creation.

        Args:
          description: New dataset description

          name: New dataset name

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not dataset_id:
            raise ValueError(f"Expected a non-empty value for `dataset_id` but received {dataset_id!r}")
        return await self._put(
            f"/api/dataframer/datasets/{dataset_id}/",
            body=await async_maybe_transform(
                {
                    "description": description,
                    "name": name,
                },
                dataset_update_params.DatasetUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DatasetUpdateResponse,
        )

    async def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DatasetListResponse:
        """
        Retrieve all datasets belonging to the authenticated user's company.

        Returns dataset metadata including:

        - Dataset type (SINGLE_FILE, MULTI_FILE, MULTI_FOLDER)
        - File and folder counts
        - Short sample compatibility status
        - Creation information
        """
        return await self._get(
            "/api/dataframer/datasets/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DatasetListResponse,
        )

    async def delete(
        self,
        dataset_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Delete a dataset and all associated files from storage.

        **Warning:** This action cannot be undone. All files will be permanently deleted
        from S3.

        **Restrictions:** Cannot delete a dataset that is referenced by any specs.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not dataset_id:
            raise ValueError(f"Expected a non-empty value for `dataset_id` but received {dataset_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._delete(
            f"/api/dataframer/datasets/{dataset_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def create_from_zip(
        self,
        *,
        name: str,
        zip_file: FileTypes,
        description: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DatasetCreateFromZipResponse:
        """Upload a ZIP file containing dataset files.

        The backend will automatically:

        1. Extract and analyze the ZIP structure
        2. Auto-detect dataset type (SINGLE_FILE/MULTI_FILE/MULTI_FOLDER)
        3. Validate file types and sizes
        4. Create dataset with proper folder structure

        **Supported ZIP Structures:**

        1. **SINGLE_FILE**: ZIP contains exactly one valid file

           - Supported: CSV, JSON, JSONL
           - Max size: 50MB

        2. **MULTI_FILE**: ZIP contains multiple files in root

           - Supported: TXT, MD, JSON, CSV, JSONL
           - Max: 1MB per file, 50MB total, 1000 files

        3. **MULTI_FOLDER**: ZIP contains multiple folders with files
           - Supported: TXT, MD, JSON, CSV, JSONL
           - Max: 1MB per file, 50MB total, 20 files per folder
           - Requires at least 2 folders

        **Benefits:**

        - Single upload operation
        - Automatic structure detection
        - No need to specify dataset_type or folder_names
        - Works for all dataset types

        Args:
          name: Dataset name (unique within company)

          zip_file: ZIP file containing dataset files

          description: Optional dataset description

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        body = deepcopy_minimal(
            {
                "name": name,
                "zip_file": zip_file,
                "description": description,
            }
        )
        files = extract_files(cast(Mapping[str, object], body), paths=[["zip_file"]])
        # It should be noted that the actual Content-Type header that will be
        # sent to the server will contain a `boundary` parameter, e.g.
        # multipart/form-data; boundary=---abc--
        extra_headers = {"Content-Type": "multipart/form-data", **(extra_headers or {})}
        return await self._post(
            "/api/dataframer/datasets/create-from-zip/",
            body=await async_maybe_transform(body, dataset_create_from_zip_params.DatasetCreateFromZipParams),
            files=files,
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DatasetCreateFromZipResponse,
        )

    async def create_with_files(
        self,
        *,
        dataset_type: Literal["SINGLE_FILE", "MULTI_FILE", "MULTI_FOLDER"],
        name: str,
        config_json: str | Omit = omit,
        csv_headers: str | Omit = omit,
        description: str | Omit = omit,
        file: FileTypes | Omit = omit,
        files: SequenceNotStr[FileTypes] | Omit = omit,
        folder_names: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DatasetCreateWithFilesResponse:
        """Create a new dataset and upload files in a single atomic operation.

        Files are
        validated first, and dataset is only created if validation passes. **Empty
        datasets cannot be created with this endpoint.**

        **Dataset Types:**

        1. **SINGLE_FILE**: Upload one file

           - Supported types: CSV, JSON, JSONL only
           - Max size: 50MB
           - Send file as 'file' parameter
           - Optional: 'csv_headers' as JSON array for CSV files

        2. **MULTI_FILE**: Upload multiple individual files

           - Supported types: TXT, MD, JSON, CSV, JSONL
           - Max size: 1MB per file, 50MB total
           - Max 1000 files per dataset
           - Send files as 'files' array parameter

        3. **MULTI_FOLDER**: Upload files in folders
           - Supported types: TXT, MD, JSON, CSV, JSONL
           - Max size: 1MB per file, 50MB total
           - Minimum 2 folders required, each folder must have at least 1 file
           - Max 1000 files total, 20 files per folder
           - Send files as 'files' array parameter
           - Send corresponding folder names as 'folder_names' array (parallel arrays)

        **Request Format:**

        - All requests must be multipart/form-data
        - Dataset metadata: name, description, dataset_type, config_json
        - Files depend on dataset_type (see above)

        **Benefits:**

        - Atomic operation - either everything succeeds or nothing is created
        - Validation before dataset creation
        - No empty datasets
        - Single API call instead of two

        Args:
          dataset_type: Dataset type: SINGLE_FILE, MULTI_FILE, or MULTI_FOLDER

          name: Dataset name (unique within company)

          config_json: Optional configuration JSON as string

          csv_headers: Optional CSV headers as JSON array for SINGLE_FILE CSV files

          description: Optional dataset description

          file: Single file for SINGLE_FILE dataset type

          files: Multiple files for MULTI_FILE or MULTI_FOLDER dataset types. Each file will be
              sent as a separate form field named 'files'. For MULTI_FOLDER: minimum 2 files
              required (at least 1 file per folder, across at least 2 folders).

          folder_names: Folder names for MULTI_FOLDER (parallel array with files). Each folder name is
              sent as a separate 'folder_names' form field. Minimum 2 unique folder names
              required.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        body = deepcopy_minimal(
            {
                "dataset_type": dataset_type,
                "name": name,
                "config_json": config_json,
                "csv_headers": csv_headers,
                "description": description,
                "file": file,
                "files": files,
                "folder_names": folder_names,
            }
        )
        extracted_files = extract_files(cast(Mapping[str, object], body), paths=[["file"], ["files", "<array>"]])
        # It should be noted that the actual Content-Type header that will be
        # sent to the server will contain a `boundary` parameter, e.g.
        # multipart/form-data; boundary=---abc--
        extra_headers = {"Content-Type": "multipart/form-data", **(extra_headers or {})}
        return await self._post(
            "/api/dataframer/datasets/create/",
            body=await async_maybe_transform(body, dataset_create_with_files_params.DatasetCreateWithFilesParams),
            files=extracted_files,
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DatasetCreateWithFilesResponse,
        )

    async def list_files(
        self,
        dataset_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DatasetListFilesResponse:
        """
        Get all files in a specific dataset.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not dataset_id:
            raise ValueError(f"Expected a non-empty value for `dataset_id` but received {dataset_id!r}")
        return await self._get(
            f"/api/dataframer/datasets/{dataset_id}/files/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DatasetListFilesResponse,
        )

    async def list_folders(
        self,
        dataset_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DatasetListFoldersResponse:
        """
        Get all folders in a specific dataset.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not dataset_id:
            raise ValueError(f"Expected a non-empty value for `dataset_id` but received {dataset_id!r}")
        return await self._get(
            f"/api/dataframer/datasets/{dataset_id}/folders/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DatasetListFoldersResponse,
        )


class DatasetsResourceWithRawResponse:
    def __init__(self, datasets: DatasetsResource) -> None:
        self._datasets = datasets

        self.retrieve = to_raw_response_wrapper(
            datasets.retrieve,
        )
        self.update = to_raw_response_wrapper(
            datasets.update,
        )
        self.list = to_raw_response_wrapper(
            datasets.list,
        )
        self.delete = to_raw_response_wrapper(
            datasets.delete,
        )
        self.create_from_zip = to_raw_response_wrapper(
            datasets.create_from_zip,
        )
        self.create_with_files = to_raw_response_wrapper(
            datasets.create_with_files,
        )
        self.list_files = to_raw_response_wrapper(
            datasets.list_files,
        )
        self.list_folders = to_raw_response_wrapper(
            datasets.list_folders,
        )


class AsyncDatasetsResourceWithRawResponse:
    def __init__(self, datasets: AsyncDatasetsResource) -> None:
        self._datasets = datasets

        self.retrieve = async_to_raw_response_wrapper(
            datasets.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            datasets.update,
        )
        self.list = async_to_raw_response_wrapper(
            datasets.list,
        )
        self.delete = async_to_raw_response_wrapper(
            datasets.delete,
        )
        self.create_from_zip = async_to_raw_response_wrapper(
            datasets.create_from_zip,
        )
        self.create_with_files = async_to_raw_response_wrapper(
            datasets.create_with_files,
        )
        self.list_files = async_to_raw_response_wrapper(
            datasets.list_files,
        )
        self.list_folders = async_to_raw_response_wrapper(
            datasets.list_folders,
        )


class DatasetsResourceWithStreamingResponse:
    def __init__(self, datasets: DatasetsResource) -> None:
        self._datasets = datasets

        self.retrieve = to_streamed_response_wrapper(
            datasets.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            datasets.update,
        )
        self.list = to_streamed_response_wrapper(
            datasets.list,
        )
        self.delete = to_streamed_response_wrapper(
            datasets.delete,
        )
        self.create_from_zip = to_streamed_response_wrapper(
            datasets.create_from_zip,
        )
        self.create_with_files = to_streamed_response_wrapper(
            datasets.create_with_files,
        )
        self.list_files = to_streamed_response_wrapper(
            datasets.list_files,
        )
        self.list_folders = to_streamed_response_wrapper(
            datasets.list_folders,
        )


class AsyncDatasetsResourceWithStreamingResponse:
    def __init__(self, datasets: AsyncDatasetsResource) -> None:
        self._datasets = datasets

        self.retrieve = async_to_streamed_response_wrapper(
            datasets.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            datasets.update,
        )
        self.list = async_to_streamed_response_wrapper(
            datasets.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            datasets.delete,
        )
        self.create_from_zip = async_to_streamed_response_wrapper(
            datasets.create_from_zip,
        )
        self.create_with_files = async_to_streamed_response_wrapper(
            datasets.create_with_files,
        )
        self.list_files = async_to_streamed_response_wrapper(
            datasets.list_files,
        )
        self.list_folders = async_to_streamed_response_wrapper(
            datasets.list_folders,
        )
