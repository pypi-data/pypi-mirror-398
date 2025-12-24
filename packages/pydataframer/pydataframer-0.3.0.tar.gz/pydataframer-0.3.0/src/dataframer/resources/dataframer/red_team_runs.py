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
from ...types.dataframer.red_team_run_list_response import RedTeamRunListResponse
from ...types.dataframer.red_team_run_create_response import RedTeamRunCreateResponse
from ...types.dataframer.red_team_run_retrieve_response import RedTeamRunRetrieveResponse
from ...types.dataframer.red_team_run_retrieve_status_response import RedTeamRunRetrieveStatusResponse

__all__ = ["RedTeamRunsResource", "AsyncRedTeamRunsResource"]


class RedTeamRunsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> RedTeamRunsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#accessing-raw-response-data-eg-headers
        """
        return RedTeamRunsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> RedTeamRunsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#with_streaming_response
        """
        return RedTeamRunsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RedTeamRunCreateResponse:
        """Create a new red team run and submit to data_gen backend"""
        return self._post(
            "/api/dataframer/red-team-runs/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RedTeamRunCreateResponse,
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
    ) -> RedTeamRunRetrieveResponse:
        """
        Retrieve a red team run

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return self._get(
            f"/api/dataframer/red-team-runs/{run_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RedTeamRunRetrieveResponse,
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
    ) -> RedTeamRunListResponse:
        """List all red team runs for the user's company"""
        return self._get(
            "/api/dataframer/red-team-runs/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RedTeamRunListResponse,
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
        Delete a red team run

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
            f"/api/dataframer/red-team-runs/{run_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def retrieve_status(
        self,
        run_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RedTeamRunRetrieveStatusResponse:
        """
        Get red team run status and sync with data_gen backend

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return self._get(
            f"/api/dataframer/red-team-runs/{run_id}/status/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RedTeamRunRetrieveStatusResponse,
        )


class AsyncRedTeamRunsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncRedTeamRunsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncRedTeamRunsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncRedTeamRunsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#with_streaming_response
        """
        return AsyncRedTeamRunsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RedTeamRunCreateResponse:
        """Create a new red team run and submit to data_gen backend"""
        return await self._post(
            "/api/dataframer/red-team-runs/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RedTeamRunCreateResponse,
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
    ) -> RedTeamRunRetrieveResponse:
        """
        Retrieve a red team run

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return await self._get(
            f"/api/dataframer/red-team-runs/{run_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RedTeamRunRetrieveResponse,
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
    ) -> RedTeamRunListResponse:
        """List all red team runs for the user's company"""
        return await self._get(
            "/api/dataframer/red-team-runs/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RedTeamRunListResponse,
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
        Delete a red team run

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
            f"/api/dataframer/red-team-runs/{run_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def retrieve_status(
        self,
        run_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RedTeamRunRetrieveStatusResponse:
        """
        Get red team run status and sync with data_gen backend

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return await self._get(
            f"/api/dataframer/red-team-runs/{run_id}/status/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RedTeamRunRetrieveStatusResponse,
        )


class RedTeamRunsResourceWithRawResponse:
    def __init__(self, red_team_runs: RedTeamRunsResource) -> None:
        self._red_team_runs = red_team_runs

        self.create = to_raw_response_wrapper(
            red_team_runs.create,
        )
        self.retrieve = to_raw_response_wrapper(
            red_team_runs.retrieve,
        )
        self.list = to_raw_response_wrapper(
            red_team_runs.list,
        )
        self.delete = to_raw_response_wrapper(
            red_team_runs.delete,
        )
        self.retrieve_status = to_raw_response_wrapper(
            red_team_runs.retrieve_status,
        )


class AsyncRedTeamRunsResourceWithRawResponse:
    def __init__(self, red_team_runs: AsyncRedTeamRunsResource) -> None:
        self._red_team_runs = red_team_runs

        self.create = async_to_raw_response_wrapper(
            red_team_runs.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            red_team_runs.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            red_team_runs.list,
        )
        self.delete = async_to_raw_response_wrapper(
            red_team_runs.delete,
        )
        self.retrieve_status = async_to_raw_response_wrapper(
            red_team_runs.retrieve_status,
        )


class RedTeamRunsResourceWithStreamingResponse:
    def __init__(self, red_team_runs: RedTeamRunsResource) -> None:
        self._red_team_runs = red_team_runs

        self.create = to_streamed_response_wrapper(
            red_team_runs.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            red_team_runs.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            red_team_runs.list,
        )
        self.delete = to_streamed_response_wrapper(
            red_team_runs.delete,
        )
        self.retrieve_status = to_streamed_response_wrapper(
            red_team_runs.retrieve_status,
        )


class AsyncRedTeamRunsResourceWithStreamingResponse:
    def __init__(self, red_team_runs: AsyncRedTeamRunsResource) -> None:
        self._red_team_runs = red_team_runs

        self.create = async_to_streamed_response_wrapper(
            red_team_runs.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            red_team_runs.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            red_team_runs.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            red_team_runs.delete,
        )
        self.retrieve_status = async_to_streamed_response_wrapper(
            red_team_runs.retrieve_status,
        )
