# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

import httpx

from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.dataframer import analyze_create_params
from ...types.dataframer.analyze_create_response import AnalyzeCreateResponse
from ...types.dataframer.analyze_get_status_response import AnalyzeGetStatusResponse

__all__ = ["AnalyzeResource", "AsyncAnalyzeResource"]


class AnalyzeResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AnalyzeResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AnalyzeResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AnalyzeResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#with_streaming_response
        """
        return AnalyzeResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        dataset_id: str,
        name: str,
        analysis_model_name: Literal[
            "anthropic/claude-opus-4-5",
            "anthropic/claude-opus-4-5-thinking",
            "anthropic/claude-sonnet-4-5",
            "anthropic/claude-sonnet-4-5-thinking",
            "anthropic/claude-haiku-4-5",
            "deepseek-ai/DeepSeek-V3.1",
            "moonshotai/Kimi-K2-Instruct",
            "openai/gpt-oss-120b",
            "deepseek-ai/DeepSeek-R1-0528-tput",
            "Qwen/Qwen2.5-72B-Instruct-Turbo",
        ]
        | Omit = omit,
        description: str | Omit = omit,
        extrapolate_axes: bool | Omit = omit,
        extrapolate_values: bool | Omit = omit,
        generate_distributions: bool | Omit = omit,
        generation_objectives: str | Omit = omit,
        use_truncation: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AnalyzeCreateResponse:
        """
        Analyze dataset files using AI to understand the data structure and patterns,
        then create a new spec with version 1 based on the analysis.

        The analysis process:

        1. Reads all files from the dataset
        2. Analyzes data structure, patterns, and relationships
        3. Generates spec configuration for synthetic data generation
        4. Creates spec with version 1 containing the analysis results

        Args:
          dataset_id: ID of the dataset to analyze

          name: Name for the new spec to be created

          analysis_model_name: AI model to use for analysis

          description: Description of the spec

          extrapolate_axes: Extrapolate to new axes/dimensions

          extrapolate_values: Extrapolate new values beyond existing data ranges

          generate_distributions: Generate statistical distributions from the data

          generation_objectives: Custom objectives or instructions for data generation

          use_truncation: Apply truncation to limit value ranges

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/dataframer/analyze/",
            body=maybe_transform(
                {
                    "dataset_id": dataset_id,
                    "name": name,
                    "analysis_model_name": analysis_model_name,
                    "description": description,
                    "extrapolate_axes": extrapolate_axes,
                    "extrapolate_values": extrapolate_values,
                    "generate_distributions": generate_distributions,
                    "generation_objectives": generation_objectives,
                    "use_truncation": use_truncation,
                },
                analyze_create_params.AnalyzeCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AnalyzeCreateResponse,
        )

    def get_status(
        self,
        task_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AnalyzeGetStatusResponse:
        """
        Get analysis status from external service (client-side polling)

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not task_id:
            raise ValueError(f"Expected a non-empty value for `task_id` but received {task_id!r}")
        return self._get(
            f"/api/dataframer/analyze/status/{task_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AnalyzeGetStatusResponse,
        )


class AsyncAnalyzeResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncAnalyzeResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncAnalyzeResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncAnalyzeResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#with_streaming_response
        """
        return AsyncAnalyzeResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        dataset_id: str,
        name: str,
        analysis_model_name: Literal[
            "anthropic/claude-opus-4-5",
            "anthropic/claude-opus-4-5-thinking",
            "anthropic/claude-sonnet-4-5",
            "anthropic/claude-sonnet-4-5-thinking",
            "anthropic/claude-haiku-4-5",
            "deepseek-ai/DeepSeek-V3.1",
            "moonshotai/Kimi-K2-Instruct",
            "openai/gpt-oss-120b",
            "deepseek-ai/DeepSeek-R1-0528-tput",
            "Qwen/Qwen2.5-72B-Instruct-Turbo",
        ]
        | Omit = omit,
        description: str | Omit = omit,
        extrapolate_axes: bool | Omit = omit,
        extrapolate_values: bool | Omit = omit,
        generate_distributions: bool | Omit = omit,
        generation_objectives: str | Omit = omit,
        use_truncation: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AnalyzeCreateResponse:
        """
        Analyze dataset files using AI to understand the data structure and patterns,
        then create a new spec with version 1 based on the analysis.

        The analysis process:

        1. Reads all files from the dataset
        2. Analyzes data structure, patterns, and relationships
        3. Generates spec configuration for synthetic data generation
        4. Creates spec with version 1 containing the analysis results

        Args:
          dataset_id: ID of the dataset to analyze

          name: Name for the new spec to be created

          analysis_model_name: AI model to use for analysis

          description: Description of the spec

          extrapolate_axes: Extrapolate to new axes/dimensions

          extrapolate_values: Extrapolate new values beyond existing data ranges

          generate_distributions: Generate statistical distributions from the data

          generation_objectives: Custom objectives or instructions for data generation

          use_truncation: Apply truncation to limit value ranges

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/dataframer/analyze/",
            body=await async_maybe_transform(
                {
                    "dataset_id": dataset_id,
                    "name": name,
                    "analysis_model_name": analysis_model_name,
                    "description": description,
                    "extrapolate_axes": extrapolate_axes,
                    "extrapolate_values": extrapolate_values,
                    "generate_distributions": generate_distributions,
                    "generation_objectives": generation_objectives,
                    "use_truncation": use_truncation,
                },
                analyze_create_params.AnalyzeCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AnalyzeCreateResponse,
        )

    async def get_status(
        self,
        task_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AnalyzeGetStatusResponse:
        """
        Get analysis status from external service (client-side polling)

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not task_id:
            raise ValueError(f"Expected a non-empty value for `task_id` but received {task_id!r}")
        return await self._get(
            f"/api/dataframer/analyze/status/{task_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AnalyzeGetStatusResponse,
        )


class AnalyzeResourceWithRawResponse:
    def __init__(self, analyze: AnalyzeResource) -> None:
        self._analyze = analyze

        self.create = to_raw_response_wrapper(
            analyze.create,
        )
        self.get_status = to_raw_response_wrapper(
            analyze.get_status,
        )


class AsyncAnalyzeResourceWithRawResponse:
    def __init__(self, analyze: AsyncAnalyzeResource) -> None:
        self._analyze = analyze

        self.create = async_to_raw_response_wrapper(
            analyze.create,
        )
        self.get_status = async_to_raw_response_wrapper(
            analyze.get_status,
        )


class AnalyzeResourceWithStreamingResponse:
    def __init__(self, analyze: AnalyzeResource) -> None:
        self._analyze = analyze

        self.create = to_streamed_response_wrapper(
            analyze.create,
        )
        self.get_status = to_streamed_response_wrapper(
            analyze.get_status,
        )


class AsyncAnalyzeResourceWithStreamingResponse:
    def __init__(self, analyze: AsyncAnalyzeResource) -> None:
        self._analyze = analyze

        self.create = async_to_streamed_response_wrapper(
            analyze.create,
        )
        self.get_status = async_to_streamed_response_wrapper(
            analyze.get_status,
        )
