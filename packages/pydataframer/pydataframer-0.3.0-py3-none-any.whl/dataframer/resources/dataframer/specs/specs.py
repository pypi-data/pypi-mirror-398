# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict

import httpx

from .versions import (
    VersionsResource,
    AsyncVersionsResource,
    VersionsResourceWithRawResponse,
    AsyncVersionsResourceWithRawResponse,
    VersionsResourceWithStreamingResponse,
    AsyncVersionsResourceWithStreamingResponse,
)
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
from ....types.dataframer import spec_create_params, spec_update_params
from ....types.dataframer.spec_list_response import SpecListResponse
from ....types.dataframer.spec_create_response import SpecCreateResponse
from ....types.dataframer.spec_update_response import SpecUpdateResponse
from ....types.dataframer.spec_retrieve_response import SpecRetrieveResponse

__all__ = ["SpecsResource", "AsyncSpecsResource"]


class SpecsResource(SyncAPIResource):
    @cached_property
    def versions(self) -> VersionsResource:
        return VersionsResource(self._client)

    @cached_property
    def with_raw_response(self) -> SpecsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#accessing-raw-response-data-eg-headers
        """
        return SpecsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SpecsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#with_streaming_response
        """
        return SpecsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        datasets_id: str,
        name: str,
        description: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SpecCreateResponse:
        """
        Create a new spec manually without using the analyze endpoint.

        **Note**: Most users should use `/api/dataframer/analyze/` instead, which
        automatically analyzes a dataset and creates a spec with proper configuration.

        This endpoint allows manual spec creation for advanced use cases where you want
        to define the spec structure yourself.

        Args:
          datasets_id: UUID of the dataset this spec is based on

          name: Unique name for the spec (within dataset and company)

          description: Optional description of the spec

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/dataframer/specs/",
            body=maybe_transform(
                {
                    "datasets_id": datasets_id,
                    "name": name,
                    "description": description,
                },
                spec_create_params.SpecCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SpecCreateResponse,
        )

    def retrieve(
        self,
        spec_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SpecRetrieveResponse:
        """
        Get a specific spec, optionally with deletion impact info

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not spec_id:
            raise ValueError(f"Expected a non-empty value for `spec_id` but received {spec_id!r}")
        return self._get(
            f"/api/dataframer/specs/{spec_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SpecRetrieveResponse,
        )

    def update(
        self,
        spec_id: str,
        *,
        config_yaml: str,
        description: str | Omit = omit,
        name: str | Omit = omit,
        orig_results_yaml: str | Omit = omit,
        results_yaml: str | Omit = omit,
        runtime_params: Dict[str, object] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SpecUpdateResponse:
        """
        Update a spec by creating a new version with modified YAML configuration.

        Each update creates a new version (up to 30 versions per spec). You can update:

        - config_yaml: The spec configuration (required)
        - results_yaml: Results from analysis (optional)
        - orig_results_yaml: Original analysis results (optional)
        - runtime_params: Runtime parameters for generation (optional)
        - name: Update the spec name (optional)
        - description: Update the spec description (optional)

        The config_yaml contains the data property variations, distributions, and
        generation requirements.

        Args:
          config_yaml: YAML configuration for the spec (required)

          description: Update the spec description (optional)

          name: Update the spec name (optional)

          orig_results_yaml: Original results YAML (optional)

          results_yaml: Results YAML from analysis (optional)

          runtime_params: Runtime parameters for generation (optional)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not spec_id:
            raise ValueError(f"Expected a non-empty value for `spec_id` but received {spec_id!r}")
        return self._put(
            f"/api/dataframer/specs/{spec_id}/",
            body=maybe_transform(
                {
                    "config_yaml": config_yaml,
                    "description": description,
                    "name": name,
                    "orig_results_yaml": orig_results_yaml,
                    "results_yaml": results_yaml,
                    "runtime_params": runtime_params,
                },
                spec_update_params.SpecUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SpecUpdateResponse,
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
    ) -> SpecListResponse:
        """Get all specs for the user's company"""
        return self._get(
            "/api/dataframer/specs/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SpecListResponse,
        )

    def delete(
        self,
        spec_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Delete a spec and clean up associated runs and S3 files

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not spec_id:
            raise ValueError(f"Expected a non-empty value for `spec_id` but received {spec_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._delete(
            f"/api/dataframer/specs/{spec_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncSpecsResource(AsyncAPIResource):
    @cached_property
    def versions(self) -> AsyncVersionsResource:
        return AsyncVersionsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncSpecsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncSpecsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSpecsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#with_streaming_response
        """
        return AsyncSpecsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        datasets_id: str,
        name: str,
        description: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SpecCreateResponse:
        """
        Create a new spec manually without using the analyze endpoint.

        **Note**: Most users should use `/api/dataframer/analyze/` instead, which
        automatically analyzes a dataset and creates a spec with proper configuration.

        This endpoint allows manual spec creation for advanced use cases where you want
        to define the spec structure yourself.

        Args:
          datasets_id: UUID of the dataset this spec is based on

          name: Unique name for the spec (within dataset and company)

          description: Optional description of the spec

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/dataframer/specs/",
            body=await async_maybe_transform(
                {
                    "datasets_id": datasets_id,
                    "name": name,
                    "description": description,
                },
                spec_create_params.SpecCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SpecCreateResponse,
        )

    async def retrieve(
        self,
        spec_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SpecRetrieveResponse:
        """
        Get a specific spec, optionally with deletion impact info

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not spec_id:
            raise ValueError(f"Expected a non-empty value for `spec_id` but received {spec_id!r}")
        return await self._get(
            f"/api/dataframer/specs/{spec_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SpecRetrieveResponse,
        )

    async def update(
        self,
        spec_id: str,
        *,
        config_yaml: str,
        description: str | Omit = omit,
        name: str | Omit = omit,
        orig_results_yaml: str | Omit = omit,
        results_yaml: str | Omit = omit,
        runtime_params: Dict[str, object] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SpecUpdateResponse:
        """
        Update a spec by creating a new version with modified YAML configuration.

        Each update creates a new version (up to 30 versions per spec). You can update:

        - config_yaml: The spec configuration (required)
        - results_yaml: Results from analysis (optional)
        - orig_results_yaml: Original analysis results (optional)
        - runtime_params: Runtime parameters for generation (optional)
        - name: Update the spec name (optional)
        - description: Update the spec description (optional)

        The config_yaml contains the data property variations, distributions, and
        generation requirements.

        Args:
          config_yaml: YAML configuration for the spec (required)

          description: Update the spec description (optional)

          name: Update the spec name (optional)

          orig_results_yaml: Original results YAML (optional)

          results_yaml: Results YAML from analysis (optional)

          runtime_params: Runtime parameters for generation (optional)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not spec_id:
            raise ValueError(f"Expected a non-empty value for `spec_id` but received {spec_id!r}")
        return await self._put(
            f"/api/dataframer/specs/{spec_id}/",
            body=await async_maybe_transform(
                {
                    "config_yaml": config_yaml,
                    "description": description,
                    "name": name,
                    "orig_results_yaml": orig_results_yaml,
                    "results_yaml": results_yaml,
                    "runtime_params": runtime_params,
                },
                spec_update_params.SpecUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SpecUpdateResponse,
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
    ) -> SpecListResponse:
        """Get all specs for the user's company"""
        return await self._get(
            "/api/dataframer/specs/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SpecListResponse,
        )

    async def delete(
        self,
        spec_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Delete a spec and clean up associated runs and S3 files

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not spec_id:
            raise ValueError(f"Expected a non-empty value for `spec_id` but received {spec_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._delete(
            f"/api/dataframer/specs/{spec_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class SpecsResourceWithRawResponse:
    def __init__(self, specs: SpecsResource) -> None:
        self._specs = specs

        self.create = to_raw_response_wrapper(
            specs.create,
        )
        self.retrieve = to_raw_response_wrapper(
            specs.retrieve,
        )
        self.update = to_raw_response_wrapper(
            specs.update,
        )
        self.list = to_raw_response_wrapper(
            specs.list,
        )
        self.delete = to_raw_response_wrapper(
            specs.delete,
        )

    @cached_property
    def versions(self) -> VersionsResourceWithRawResponse:
        return VersionsResourceWithRawResponse(self._specs.versions)


class AsyncSpecsResourceWithRawResponse:
    def __init__(self, specs: AsyncSpecsResource) -> None:
        self._specs = specs

        self.create = async_to_raw_response_wrapper(
            specs.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            specs.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            specs.update,
        )
        self.list = async_to_raw_response_wrapper(
            specs.list,
        )
        self.delete = async_to_raw_response_wrapper(
            specs.delete,
        )

    @cached_property
    def versions(self) -> AsyncVersionsResourceWithRawResponse:
        return AsyncVersionsResourceWithRawResponse(self._specs.versions)


class SpecsResourceWithStreamingResponse:
    def __init__(self, specs: SpecsResource) -> None:
        self._specs = specs

        self.create = to_streamed_response_wrapper(
            specs.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            specs.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            specs.update,
        )
        self.list = to_streamed_response_wrapper(
            specs.list,
        )
        self.delete = to_streamed_response_wrapper(
            specs.delete,
        )

    @cached_property
    def versions(self) -> VersionsResourceWithStreamingResponse:
        return VersionsResourceWithStreamingResponse(self._specs.versions)


class AsyncSpecsResourceWithStreamingResponse:
    def __init__(self, specs: AsyncSpecsResource) -> None:
        self._specs = specs

        self.create = async_to_streamed_response_wrapper(
            specs.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            specs.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            specs.update,
        )
        self.list = async_to_streamed_response_wrapper(
            specs.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            specs.delete,
        )

    @cached_property
    def versions(self) -> AsyncVersionsResourceWithStreamingResponse:
        return AsyncVersionsResourceWithStreamingResponse(self._specs.versions)
