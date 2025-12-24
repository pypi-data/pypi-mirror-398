# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable

import httpx

from ...._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
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
from ....types.dataframer.runs import sample_list_params, sample_retrieve_by_indices_params
from ....types.dataframer.runs.sample_list_response import SampleListResponse
from ....types.dataframer.runs.sample_retrieve_by_indices_response import SampleRetrieveByIndicesResponse

__all__ = ["SamplesResource", "AsyncSamplesResource"]


class SamplesResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SamplesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#accessing-raw-response-data-eg-headers
        """
        return SamplesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SamplesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#with_streaming_response
        """
        return SamplesResourceWithStreamingResponse(self)

    def list(
        self,
        run_id: str,
        *,
        limit: int | Omit = omit,
        offset: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SampleListResponse:
        """
        Retrieve generated samples from a run, ordered by finish time (earliest first).

        **Ordering**: Samples are returned in FINISH TIME ORDER:

        - Position 0 = sample that finished first
        - Position 1 = sample that finished second
        - etc.

        **Pagination**: Use offset and limit for pagination:

        - offset: Starting position (default: 0)
        - limit: Maximum samples to return (default: all, max: 1000)

        **Use Cases**:

        - Stream samples as they complete during generation
        - Paginate through large result sets
        - Monitor generation progress in real-time

        **Out-of-range behavior**:

        - If offset >= total_samples: Returns empty result
        - If offset+limit > total_samples: Returns partial result
        - Check returned_count to detect end of data

        Args:
          limit: Maximum samples to return (default: all, max: 1000)

          offset: Starting position in finish-time-ordered list (default: 0)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return self._get(
            f"/api/dataframer/runs/{run_id}/samples/",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "limit": limit,
                        "offset": offset,
                    },
                    sample_list_params.SampleListParams,
                ),
            ),
            cast_to=SampleListResponse,
        )

    def retrieve_by_indices(
        self,
        run_id: str,
        *,
        indices: Iterable[int],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SampleRetrieveByIndicesResponse:
        """
        Retrieve specific samples by their FINISH-TIME positions.

        **Critical**: Indices refer to FINISH-TIME positions, NOT original task indices:

        - index=0: The sample that finished first
        - index=1: The sample that finished second
        - etc.

        **Use Cases**:

        - Retrieve specific samples you know completed
        - Get samples at known positions
        - Cherry-pick samples by finish order

        **Out-of-range handling**:

        - If index >= total_samples: Returns None with status="out_of_range"
        - No error raised - check sample_statuses for out-of-range markers

        **Example**: `{"indices": [0, 1, 2, 50]}` retrieves samples at those finish-time
        positions

        Args:
          indices: List of finish-time positions to retrieve (max 1000)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return self._post(
            f"/api/dataframer/runs/{run_id}/samples/",
            body=maybe_transform({"indices": indices}, sample_retrieve_by_indices_params.SampleRetrieveByIndicesParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SampleRetrieveByIndicesResponse,
        )


class AsyncSamplesResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSamplesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncSamplesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSamplesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#with_streaming_response
        """
        return AsyncSamplesResourceWithStreamingResponse(self)

    async def list(
        self,
        run_id: str,
        *,
        limit: int | Omit = omit,
        offset: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SampleListResponse:
        """
        Retrieve generated samples from a run, ordered by finish time (earliest first).

        **Ordering**: Samples are returned in FINISH TIME ORDER:

        - Position 0 = sample that finished first
        - Position 1 = sample that finished second
        - etc.

        **Pagination**: Use offset and limit for pagination:

        - offset: Starting position (default: 0)
        - limit: Maximum samples to return (default: all, max: 1000)

        **Use Cases**:

        - Stream samples as they complete during generation
        - Paginate through large result sets
        - Monitor generation progress in real-time

        **Out-of-range behavior**:

        - If offset >= total_samples: Returns empty result
        - If offset+limit > total_samples: Returns partial result
        - Check returned_count to detect end of data

        Args:
          limit: Maximum samples to return (default: all, max: 1000)

          offset: Starting position in finish-time-ordered list (default: 0)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return await self._get(
            f"/api/dataframer/runs/{run_id}/samples/",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "limit": limit,
                        "offset": offset,
                    },
                    sample_list_params.SampleListParams,
                ),
            ),
            cast_to=SampleListResponse,
        )

    async def retrieve_by_indices(
        self,
        run_id: str,
        *,
        indices: Iterable[int],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SampleRetrieveByIndicesResponse:
        """
        Retrieve specific samples by their FINISH-TIME positions.

        **Critical**: Indices refer to FINISH-TIME positions, NOT original task indices:

        - index=0: The sample that finished first
        - index=1: The sample that finished second
        - etc.

        **Use Cases**:

        - Retrieve specific samples you know completed
        - Get samples at known positions
        - Cherry-pick samples by finish order

        **Out-of-range handling**:

        - If index >= total_samples: Returns None with status="out_of_range"
        - No error raised - check sample_statuses for out-of-range markers

        **Example**: `{"indices": [0, 1, 2, 50]}` retrieves samples at those finish-time
        positions

        Args:
          indices: List of finish-time positions to retrieve (max 1000)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return await self._post(
            f"/api/dataframer/runs/{run_id}/samples/",
            body=await async_maybe_transform(
                {"indices": indices}, sample_retrieve_by_indices_params.SampleRetrieveByIndicesParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SampleRetrieveByIndicesResponse,
        )


class SamplesResourceWithRawResponse:
    def __init__(self, samples: SamplesResource) -> None:
        self._samples = samples

        self.list = to_raw_response_wrapper(
            samples.list,
        )
        self.retrieve_by_indices = to_raw_response_wrapper(
            samples.retrieve_by_indices,
        )


class AsyncSamplesResourceWithRawResponse:
    def __init__(self, samples: AsyncSamplesResource) -> None:
        self._samples = samples

        self.list = async_to_raw_response_wrapper(
            samples.list,
        )
        self.retrieve_by_indices = async_to_raw_response_wrapper(
            samples.retrieve_by_indices,
        )


class SamplesResourceWithStreamingResponse:
    def __init__(self, samples: SamplesResource) -> None:
        self._samples = samples

        self.list = to_streamed_response_wrapper(
            samples.list,
        )
        self.retrieve_by_indices = to_streamed_response_wrapper(
            samples.retrieve_by_indices,
        )


class AsyncSamplesResourceWithStreamingResponse:
    def __init__(self, samples: AsyncSamplesResource) -> None:
        self._samples = samples

        self.list = async_to_streamed_response_wrapper(
            samples.list,
        )
        self.retrieve_by_indices = async_to_streamed_response_wrapper(
            samples.retrieve_by_indices,
        )
