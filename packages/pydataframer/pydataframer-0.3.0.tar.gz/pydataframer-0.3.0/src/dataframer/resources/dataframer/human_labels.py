# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..._types import Body, Query, Headers, NoneType, NotGiven, not_given
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.dataframer.human_label_update_response import HumanLabelUpdateResponse
from ...types.dataframer.human_label_retrieve_response import HumanLabelRetrieveResponse

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

    def retrieve(
        self,
        label_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HumanLabelRetrieveResponse:
        """
        Get a specific human label

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not label_id:
            raise ValueError(f"Expected a non-empty value for `label_id` but received {label_id!r}")
        return self._get(
            f"/api/dataframer/human-labels/{label_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HumanLabelRetrieveResponse,
        )

    def update(
        self,
        label_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HumanLabelUpdateResponse:
        """
        Update a human label

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not label_id:
            raise ValueError(f"Expected a non-empty value for `label_id` but received {label_id!r}")
        return self._put(
            f"/api/dataframer/human-labels/{label_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HumanLabelUpdateResponse,
        )

    def delete(
        self,
        label_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Delete a human label

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not label_id:
            raise ValueError(f"Expected a non-empty value for `label_id` but received {label_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._delete(
            f"/api/dataframer/human-labels/{label_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
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

    async def retrieve(
        self,
        label_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HumanLabelRetrieveResponse:
        """
        Get a specific human label

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not label_id:
            raise ValueError(f"Expected a non-empty value for `label_id` but received {label_id!r}")
        return await self._get(
            f"/api/dataframer/human-labels/{label_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HumanLabelRetrieveResponse,
        )

    async def update(
        self,
        label_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HumanLabelUpdateResponse:
        """
        Update a human label

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not label_id:
            raise ValueError(f"Expected a non-empty value for `label_id` but received {label_id!r}")
        return await self._put(
            f"/api/dataframer/human-labels/{label_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HumanLabelUpdateResponse,
        )

    async def delete(
        self,
        label_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Delete a human label

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not label_id:
            raise ValueError(f"Expected a non-empty value for `label_id` but received {label_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._delete(
            f"/api/dataframer/human-labels/{label_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class HumanLabelsResourceWithRawResponse:
    def __init__(self, human_labels: HumanLabelsResource) -> None:
        self._human_labels = human_labels

        self.retrieve = to_raw_response_wrapper(
            human_labels.retrieve,
        )
        self.update = to_raw_response_wrapper(
            human_labels.update,
        )
        self.delete = to_raw_response_wrapper(
            human_labels.delete,
        )


class AsyncHumanLabelsResourceWithRawResponse:
    def __init__(self, human_labels: AsyncHumanLabelsResource) -> None:
        self._human_labels = human_labels

        self.retrieve = async_to_raw_response_wrapper(
            human_labels.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            human_labels.update,
        )
        self.delete = async_to_raw_response_wrapper(
            human_labels.delete,
        )


class HumanLabelsResourceWithStreamingResponse:
    def __init__(self, human_labels: HumanLabelsResource) -> None:
        self._human_labels = human_labels

        self.retrieve = to_streamed_response_wrapper(
            human_labels.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            human_labels.update,
        )
        self.delete = to_streamed_response_wrapper(
            human_labels.delete,
        )


class AsyncHumanLabelsResourceWithStreamingResponse:
    def __init__(self, human_labels: AsyncHumanLabelsResource) -> None:
        self._human_labels = human_labels

        self.retrieve = async_to_streamed_response_wrapper(
            human_labels.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            human_labels.update,
        )
        self.delete = async_to_streamed_response_wrapper(
            human_labels.delete,
        )
