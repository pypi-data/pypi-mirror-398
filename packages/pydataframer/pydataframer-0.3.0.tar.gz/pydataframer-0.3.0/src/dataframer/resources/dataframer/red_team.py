# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..._types import Body, Query, Headers, NotGiven, not_given
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.dataframer.red_team_create_task_response import RedTeamCreateTaskResponse
from ...types.dataframer.red_team_retrieve_status_response import RedTeamRetrieveStatusResponse

__all__ = ["RedTeamResource", "AsyncRedTeamResource"]


class RedTeamResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> RedTeamResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#accessing-raw-response-data-eg-headers
        """
        return RedTeamResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> RedTeamResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#with_streaming_response
        """
        return RedTeamResourceWithStreamingResponse(self)

    def create_task(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RedTeamCreateTaskResponse:
        """
        Expected payload: { "domain_description": "string", "num_behaviors": int,
        "num_prompts": int, "model_name": "string" }
        """
        return self._post(
            "/api/dataframer/red-team/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RedTeamCreateTaskResponse,
        )

    def retrieve_status(
        self,
        task_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RedTeamRetrieveStatusResponse:
        """
        Get the status of a red teaming task.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not task_id:
            raise ValueError(f"Expected a non-empty value for `task_id` but received {task_id!r}")
        return self._get(
            f"/api/dataframer/red-team/status/{task_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RedTeamRetrieveStatusResponse,
        )


class AsyncRedTeamResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncRedTeamResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncRedTeamResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncRedTeamResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#with_streaming_response
        """
        return AsyncRedTeamResourceWithStreamingResponse(self)

    async def create_task(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RedTeamCreateTaskResponse:
        """
        Expected payload: { "domain_description": "string", "num_behaviors": int,
        "num_prompts": int, "model_name": "string" }
        """
        return await self._post(
            "/api/dataframer/red-team/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RedTeamCreateTaskResponse,
        )

    async def retrieve_status(
        self,
        task_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RedTeamRetrieveStatusResponse:
        """
        Get the status of a red teaming task.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not task_id:
            raise ValueError(f"Expected a non-empty value for `task_id` but received {task_id!r}")
        return await self._get(
            f"/api/dataframer/red-team/status/{task_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RedTeamRetrieveStatusResponse,
        )


class RedTeamResourceWithRawResponse:
    def __init__(self, red_team: RedTeamResource) -> None:
        self._red_team = red_team

        self.create_task = to_raw_response_wrapper(
            red_team.create_task,
        )
        self.retrieve_status = to_raw_response_wrapper(
            red_team.retrieve_status,
        )


class AsyncRedTeamResourceWithRawResponse:
    def __init__(self, red_team: AsyncRedTeamResource) -> None:
        self._red_team = red_team

        self.create_task = async_to_raw_response_wrapper(
            red_team.create_task,
        )
        self.retrieve_status = async_to_raw_response_wrapper(
            red_team.retrieve_status,
        )


class RedTeamResourceWithStreamingResponse:
    def __init__(self, red_team: RedTeamResource) -> None:
        self._red_team = red_team

        self.create_task = to_streamed_response_wrapper(
            red_team.create_task,
        )
        self.retrieve_status = to_streamed_response_wrapper(
            red_team.retrieve_status,
        )


class AsyncRedTeamResourceWithStreamingResponse:
    def __init__(self, red_team: AsyncRedTeamResource) -> None:
        self._red_team = red_team

        self.create_task = async_to_streamed_response_wrapper(
            red_team.create_task,
        )
        self.retrieve_status = async_to_streamed_response_wrapper(
            red_team.retrieve_status,
        )
