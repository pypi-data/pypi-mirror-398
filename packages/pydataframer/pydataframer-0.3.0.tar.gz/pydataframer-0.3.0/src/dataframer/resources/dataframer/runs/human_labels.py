# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ...._types import Body, Query, Headers, NotGiven, not_given
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.dataframer.runs.human_label_list_response import HumanLabelListResponse
from ....types.dataframer.runs.human_label_create_response import HumanLabelCreateResponse

__all__ = ["HumanLabelsResource", "AsyncHumanLabelsResource"]


class HumanLabelsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> HumanLabelsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#accessing-raw-response-data-eg-headers
        """
        return HumanLabelsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> HumanLabelsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#with_streaming_response
        """
        return HumanLabelsResourceWithStreamingResponse(self)

    def create(
        self,
        run_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HumanLabelCreateResponse:
        """
        Create a new human label for a run

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return self._post(
            f"/api/dataframer/runs/{run_id}/human-labels/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HumanLabelCreateResponse,
        )

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
    ) -> HumanLabelListResponse:
        """
        Get all human labels for a run

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return self._get(
            f"/api/dataframer/runs/{run_id}/human-labels/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HumanLabelListResponse,
        )


class AsyncHumanLabelsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncHumanLabelsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncHumanLabelsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncHumanLabelsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#with_streaming_response
        """
        return AsyncHumanLabelsResourceWithStreamingResponse(self)

    async def create(
        self,
        run_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HumanLabelCreateResponse:
        """
        Create a new human label for a run

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return await self._post(
            f"/api/dataframer/runs/{run_id}/human-labels/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HumanLabelCreateResponse,
        )

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
    ) -> HumanLabelListResponse:
        """
        Get all human labels for a run

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return await self._get(
            f"/api/dataframer/runs/{run_id}/human-labels/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HumanLabelListResponse,
        )


class HumanLabelsResourceWithRawResponse:
    def __init__(self, human_labels: HumanLabelsResource) -> None:
        self._human_labels = human_labels

        self.create = to_raw_response_wrapper(
            human_labels.create,
        )
        self.list = to_raw_response_wrapper(
            human_labels.list,
        )


class AsyncHumanLabelsResourceWithRawResponse:
    def __init__(self, human_labels: AsyncHumanLabelsResource) -> None:
        self._human_labels = human_labels

        self.create = async_to_raw_response_wrapper(
            human_labels.create,
        )
        self.list = async_to_raw_response_wrapper(
            human_labels.list,
        )


class HumanLabelsResourceWithStreamingResponse:
    def __init__(self, human_labels: HumanLabelsResource) -> None:
        self._human_labels = human_labels

        self.create = to_streamed_response_wrapper(
            human_labels.create,
        )
        self.list = to_streamed_response_wrapper(
            human_labels.list,
        )


class AsyncHumanLabelsResourceWithStreamingResponse:
    def __init__(self, human_labels: AsyncHumanLabelsResource) -> None:
        self._human_labels = human_labels

        self.create = async_to_streamed_response_wrapper(
            human_labels.create,
        )
        self.list = async_to_streamed_response_wrapper(
            human_labels.list,
        )
