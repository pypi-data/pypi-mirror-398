# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict

import httpx

from .samples import (
    SamplesResource,
    AsyncSamplesResource,
    SamplesResourceWithRawResponse,
    AsyncSamplesResourceWithRawResponse,
    SamplesResourceWithStreamingResponse,
    AsyncSamplesResourceWithStreamingResponse,
)
from ...._types import Body, Query, Headers, NoneType, NotGiven, not_given
from ...._utils import maybe_transform, async_maybe_transform
from ...._compat import cached_property
from .evaluations import (
    EvaluationsResource,
    AsyncEvaluationsResource,
    EvaluationsResourceWithRawResponse,
    AsyncEvaluationsResourceWithRawResponse,
    EvaluationsResourceWithStreamingResponse,
    AsyncEvaluationsResourceWithStreamingResponse,
)
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .human_labels import (
    HumanLabelsResource,
    AsyncHumanLabelsResource,
    HumanLabelsResourceWithRawResponse,
    AsyncHumanLabelsResourceWithRawResponse,
    HumanLabelsResourceWithStreamingResponse,
    AsyncHumanLabelsResourceWithStreamingResponse,
)
from ...._base_client import make_request_options
from .generated_files import (
    GeneratedFilesResource,
    AsyncGeneratedFilesResource,
    GeneratedFilesResourceWithRawResponse,
    AsyncGeneratedFilesResourceWithRawResponse,
    GeneratedFilesResourceWithStreamingResponse,
    AsyncGeneratedFilesResourceWithStreamingResponse,
)
from ....types.dataframer import run_create_params
from ....types.dataframer.run_list_response import RunListResponse
from ....types.dataframer.run_create_response import RunCreateResponse
from ....types.dataframer.run_status_response import RunStatusResponse
from ....types.dataframer.run_update_response import RunUpdateResponse
from ....types.dataframer.run_retrieve_response import RunRetrieveResponse

__all__ = ["RunsResource", "AsyncRunsResource"]


class RunsResource(SyncAPIResource):
    @cached_property
    def evaluations(self) -> EvaluationsResource:
        return EvaluationsResource(self._client)

    @cached_property
    def generated_files(self) -> GeneratedFilesResource:
        return GeneratedFilesResource(self._client)

    @cached_property
    def human_labels(self) -> HumanLabelsResource:
        return HumanLabelsResource(self._client)

    @cached_property
    def samples(self) -> SamplesResource:
        return SamplesResource(self._client)

    @cached_property
    def with_raw_response(self) -> RunsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#accessing-raw-response-data-eg-headers
        """
        return RunsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> RunsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#with_streaming_response
        """
        return RunsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        number_of_samples: int,
        runtime_params: Dict[str, object],
        spec_version_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RunCreateResponse:
        """
        Create a generation run directly without using the /generate/ endpoint.

        **Note**: Most users should use `/api/dataframer/generate/` instead, which
        handles the full workflow of creating a run and submitting to the generation
        service.

        This endpoint creates a Run record in the database but does NOT submit it to the
        generation service. Use this only for advanced workflows or testing.

        Args:
          number_of_samples: Number of samples to generate

          runtime_params: Runtime parameters for generation (model, settings, etc.)

          spec_version_id: ID of the spec version to use

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/dataframer/runs/",
            body=maybe_transform(
                {
                    "number_of_samples": number_of_samples,
                    "runtime_params": runtime_params,
                    "spec_version_id": spec_version_id,
                },
                run_create_params.RunCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RunCreateResponse,
        )

    def retrieve(
        self,
        run_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RunRetrieveResponse:
        """
        Get a specific run

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return self._get(
            f"/api/dataframer/runs/{run_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RunRetrieveResponse,
        )

    def update(
        self,
        run_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RunUpdateResponse:
        """
        Update a run (only certain fields)

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return self._put(
            f"/api/dataframer/runs/{run_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RunUpdateResponse,
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
    ) -> RunListResponse:
        """
        Get all generation runs for the authenticated user's company, ordered by
        creation time (newest first).
        """
        return self._get(
            "/api/dataframer/runs/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RunListResponse,
        )

    def delete(
        self,
        run_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Delete a run and clean up associated S3 files

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._delete(
            f"/api/dataframer/runs/{run_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def status(
        self,
        run_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RunStatusResponse:
        """
        Get run status

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return self._get(
            f"/api/dataframer/runs/{run_id}/status/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RunStatusResponse,
        )


class AsyncRunsResource(AsyncAPIResource):
    @cached_property
    def evaluations(self) -> AsyncEvaluationsResource:
        return AsyncEvaluationsResource(self._client)

    @cached_property
    def generated_files(self) -> AsyncGeneratedFilesResource:
        return AsyncGeneratedFilesResource(self._client)

    @cached_property
    def human_labels(self) -> AsyncHumanLabelsResource:
        return AsyncHumanLabelsResource(self._client)

    @cached_property
    def samples(self) -> AsyncSamplesResource:
        return AsyncSamplesResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncRunsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncRunsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncRunsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#with_streaming_response
        """
        return AsyncRunsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        number_of_samples: int,
        runtime_params: Dict[str, object],
        spec_version_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RunCreateResponse:
        """
        Create a generation run directly without using the /generate/ endpoint.

        **Note**: Most users should use `/api/dataframer/generate/` instead, which
        handles the full workflow of creating a run and submitting to the generation
        service.

        This endpoint creates a Run record in the database but does NOT submit it to the
        generation service. Use this only for advanced workflows or testing.

        Args:
          number_of_samples: Number of samples to generate

          runtime_params: Runtime parameters for generation (model, settings, etc.)

          spec_version_id: ID of the spec version to use

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/dataframer/runs/",
            body=await async_maybe_transform(
                {
                    "number_of_samples": number_of_samples,
                    "runtime_params": runtime_params,
                    "spec_version_id": spec_version_id,
                },
                run_create_params.RunCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RunCreateResponse,
        )

    async def retrieve(
        self,
        run_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RunRetrieveResponse:
        """
        Get a specific run

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return await self._get(
            f"/api/dataframer/runs/{run_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RunRetrieveResponse,
        )

    async def update(
        self,
        run_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RunUpdateResponse:
        """
        Update a run (only certain fields)

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return await self._put(
            f"/api/dataframer/runs/{run_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RunUpdateResponse,
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
    ) -> RunListResponse:
        """
        Get all generation runs for the authenticated user's company, ordered by
        creation time (newest first).
        """
        return await self._get(
            "/api/dataframer/runs/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RunListResponse,
        )

    async def delete(
        self,
        run_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Delete a run and clean up associated S3 files

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._delete(
            f"/api/dataframer/runs/{run_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def status(
        self,
        run_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RunStatusResponse:
        """
        Get run status

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return await self._get(
            f"/api/dataframer/runs/{run_id}/status/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RunStatusResponse,
        )


class RunsResourceWithRawResponse:
    def __init__(self, runs: RunsResource) -> None:
        self._runs = runs

        self.create = to_raw_response_wrapper(
            runs.create,
        )
        self.retrieve = to_raw_response_wrapper(
            runs.retrieve,
        )
        self.update = to_raw_response_wrapper(
            runs.update,
        )
        self.list = to_raw_response_wrapper(
            runs.list,
        )
        self.delete = to_raw_response_wrapper(
            runs.delete,
        )
        self.status = to_raw_response_wrapper(
            runs.status,
        )

    @cached_property
    def evaluations(self) -> EvaluationsResourceWithRawResponse:
        return EvaluationsResourceWithRawResponse(self._runs.evaluations)

    @cached_property
    def generated_files(self) -> GeneratedFilesResourceWithRawResponse:
        return GeneratedFilesResourceWithRawResponse(self._runs.generated_files)

    @cached_property
    def human_labels(self) -> HumanLabelsResourceWithRawResponse:
        return HumanLabelsResourceWithRawResponse(self._runs.human_labels)

    @cached_property
    def samples(self) -> SamplesResourceWithRawResponse:
        return SamplesResourceWithRawResponse(self._runs.samples)


class AsyncRunsResourceWithRawResponse:
    def __init__(self, runs: AsyncRunsResource) -> None:
        self._runs = runs

        self.create = async_to_raw_response_wrapper(
            runs.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            runs.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            runs.update,
        )
        self.list = async_to_raw_response_wrapper(
            runs.list,
        )
        self.delete = async_to_raw_response_wrapper(
            runs.delete,
        )
        self.status = async_to_raw_response_wrapper(
            runs.status,
        )

    @cached_property
    def evaluations(self) -> AsyncEvaluationsResourceWithRawResponse:
        return AsyncEvaluationsResourceWithRawResponse(self._runs.evaluations)

    @cached_property
    def generated_files(self) -> AsyncGeneratedFilesResourceWithRawResponse:
        return AsyncGeneratedFilesResourceWithRawResponse(self._runs.generated_files)

    @cached_property
    def human_labels(self) -> AsyncHumanLabelsResourceWithRawResponse:
        return AsyncHumanLabelsResourceWithRawResponse(self._runs.human_labels)

    @cached_property
    def samples(self) -> AsyncSamplesResourceWithRawResponse:
        return AsyncSamplesResourceWithRawResponse(self._runs.samples)


class RunsResourceWithStreamingResponse:
    def __init__(self, runs: RunsResource) -> None:
        self._runs = runs

        self.create = to_streamed_response_wrapper(
            runs.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            runs.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            runs.update,
        )
        self.list = to_streamed_response_wrapper(
            runs.list,
        )
        self.delete = to_streamed_response_wrapper(
            runs.delete,
        )
        self.status = to_streamed_response_wrapper(
            runs.status,
        )

    @cached_property
    def evaluations(self) -> EvaluationsResourceWithStreamingResponse:
        return EvaluationsResourceWithStreamingResponse(self._runs.evaluations)

    @cached_property
    def generated_files(self) -> GeneratedFilesResourceWithStreamingResponse:
        return GeneratedFilesResourceWithStreamingResponse(self._runs.generated_files)

    @cached_property
    def human_labels(self) -> HumanLabelsResourceWithStreamingResponse:
        return HumanLabelsResourceWithStreamingResponse(self._runs.human_labels)

    @cached_property
    def samples(self) -> SamplesResourceWithStreamingResponse:
        return SamplesResourceWithStreamingResponse(self._runs.samples)


class AsyncRunsResourceWithStreamingResponse:
    def __init__(self, runs: AsyncRunsResource) -> None:
        self._runs = runs

        self.create = async_to_streamed_response_wrapper(
            runs.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            runs.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            runs.update,
        )
        self.list = async_to_streamed_response_wrapper(
            runs.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            runs.delete,
        )
        self.status = async_to_streamed_response_wrapper(
            runs.status,
        )

    @cached_property
    def evaluations(self) -> AsyncEvaluationsResourceWithStreamingResponse:
        return AsyncEvaluationsResourceWithStreamingResponse(self._runs.evaluations)

    @cached_property
    def generated_files(self) -> AsyncGeneratedFilesResourceWithStreamingResponse:
        return AsyncGeneratedFilesResourceWithStreamingResponse(self._runs.generated_files)

    @cached_property
    def human_labels(self) -> AsyncHumanLabelsResourceWithStreamingResponse:
        return AsyncHumanLabelsResourceWithStreamingResponse(self._runs.human_labels)

    @cached_property
    def samples(self) -> AsyncSamplesResourceWithStreamingResponse:
        return AsyncSamplesResourceWithStreamingResponse(self._runs.samples)
