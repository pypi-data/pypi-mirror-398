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
from ...types.dataframer import generate_create_params
from ...types.dataframer.generate_create_response import GenerateCreateResponse
from ...types.dataframer.generate_retrieve_status_response import GenerateRetrieveStatusResponse

__all__ = ["GenerateResource", "AsyncGenerateResource"]


class GenerateResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> GenerateResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#accessing-raw-response-data-eg-headers
        """
        return GenerateResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> GenerateResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#with_streaming_response
        """
        return GenerateResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        generation_model: Literal[
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
        ],
        number_of_samples: int,
        spec_id: str,
        enable_revisions: bool | Omit = omit,
        evaluation_model: Literal[
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
        evaluation_thinking_budget: int | Omit = omit,
        generation_thinking_budget: int | Omit = omit,
        max_examples_in_prompt: int | Omit = omit,
        max_iterations: int | Omit = omit,
        max_revision_cycles: int | Omit = omit,
        num_examples_in_prompt: int | Omit = omit,
        outline_model: Literal[
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
        outline_thinking_budget: int | Omit = omit,
        revision_model: Literal[
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
        revision_thinking_budget: int | Omit = omit,
        sample_type: Literal["short", "long"] | Omit = omit,
        seed_shuffling_level: Literal["none", "sample", "field", "prompt"] | Omit = omit,
        spec_version_id: str | Omit = omit,
        sql_validation_level: Literal["syntax", "syntax+schema", "syntax+schema+execute"] | Omit = omit,
        staged_generation: bool | Omit = omit,
        use_historical_feedback: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> GenerateCreateResponse:
        """
        Generate synthetic data samples based on a spec using AI models.

        The generation process:

        1. Selects the spec version (specified version or latest)
        2. Submits generation job to external service
        3. Creates a Run record to track progress
        4. Returns immediately with run_id for status polling

        Supports two sample types:

        - **short**: Quick generation with optional feedback iterations
        - **long**: Multi-stage generation with outline, draft, and revision cycles

        Args:
          generation_model: AI model to use for generation

          number_of_samples: Number of samples to generate

          spec_id: ID of the spec to use for generation

          enable_revisions: Enable revision cycles

          evaluation_model: AI model for evaluation (short samples only)

          evaluation_thinking_budget: Thinking budget for evaluation model (tokens, short samples)

          generation_thinking_budget: Thinking budget for generation model (tokens)

          max_examples_in_prompt: Maximum number of seed examples to include in prompts (long samples only). If
              not set, all seeds are used (subject to token limits).

          max_iterations: Max feedback iterations (short samples only)

          max_revision_cycles: Max revision cycles (long samples only)

          num_examples_in_prompt: Number of examples to include in prompt (short samples only)

          outline_model: AI model for outline generation (long samples only)

          outline_thinking_budget: Thinking budget for outline model (tokens, long samples)

          revision_model: AI model for revisions (long samples only)

          revision_thinking_budget: Thinking budget for revision model (tokens, long samples)

          sample_type: Type of samples to generate

          seed_shuffling_level: Seed shuffling level for long samples. Controls trade-off between prompt caching
              efficiency and data diversity.

          spec_version_id: Specific version ID to use (optional, defaults to latest version)

          sql_validation_level: SQL validation level for long samples with SQL content

          staged_generation: Use staged generation approach (short samples only)

          use_historical_feedback: Use historical feedback (short samples only)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/dataframer/generate/",
            body=maybe_transform(
                {
                    "generation_model": generation_model,
                    "number_of_samples": number_of_samples,
                    "spec_id": spec_id,
                    "enable_revisions": enable_revisions,
                    "evaluation_model": evaluation_model,
                    "evaluation_thinking_budget": evaluation_thinking_budget,
                    "generation_thinking_budget": generation_thinking_budget,
                    "max_examples_in_prompt": max_examples_in_prompt,
                    "max_iterations": max_iterations,
                    "max_revision_cycles": max_revision_cycles,
                    "num_examples_in_prompt": num_examples_in_prompt,
                    "outline_model": outline_model,
                    "outline_thinking_budget": outline_thinking_budget,
                    "revision_model": revision_model,
                    "revision_thinking_budget": revision_thinking_budget,
                    "sample_type": sample_type,
                    "seed_shuffling_level": seed_shuffling_level,
                    "spec_version_id": spec_version_id,
                    "sql_validation_level": sql_validation_level,
                    "staged_generation": staged_generation,
                    "use_historical_feedback": use_historical_feedback,
                },
                generate_create_params.GenerateCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GenerateCreateResponse,
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
    ) -> GenerateRetrieveStatusResponse:
        """
        Get generation status from external service

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not task_id:
            raise ValueError(f"Expected a non-empty value for `task_id` but received {task_id!r}")
        return self._get(
            f"/api/dataframer/generate/status/{task_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GenerateRetrieveStatusResponse,
        )


class AsyncGenerateResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncGenerateResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncGenerateResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncGenerateResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#with_streaming_response
        """
        return AsyncGenerateResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        generation_model: Literal[
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
        ],
        number_of_samples: int,
        spec_id: str,
        enable_revisions: bool | Omit = omit,
        evaluation_model: Literal[
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
        evaluation_thinking_budget: int | Omit = omit,
        generation_thinking_budget: int | Omit = omit,
        max_examples_in_prompt: int | Omit = omit,
        max_iterations: int | Omit = omit,
        max_revision_cycles: int | Omit = omit,
        num_examples_in_prompt: int | Omit = omit,
        outline_model: Literal[
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
        outline_thinking_budget: int | Omit = omit,
        revision_model: Literal[
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
        revision_thinking_budget: int | Omit = omit,
        sample_type: Literal["short", "long"] | Omit = omit,
        seed_shuffling_level: Literal["none", "sample", "field", "prompt"] | Omit = omit,
        spec_version_id: str | Omit = omit,
        sql_validation_level: Literal["syntax", "syntax+schema", "syntax+schema+execute"] | Omit = omit,
        staged_generation: bool | Omit = omit,
        use_historical_feedback: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> GenerateCreateResponse:
        """
        Generate synthetic data samples based on a spec using AI models.

        The generation process:

        1. Selects the spec version (specified version or latest)
        2. Submits generation job to external service
        3. Creates a Run record to track progress
        4. Returns immediately with run_id for status polling

        Supports two sample types:

        - **short**: Quick generation with optional feedback iterations
        - **long**: Multi-stage generation with outline, draft, and revision cycles

        Args:
          generation_model: AI model to use for generation

          number_of_samples: Number of samples to generate

          spec_id: ID of the spec to use for generation

          enable_revisions: Enable revision cycles

          evaluation_model: AI model for evaluation (short samples only)

          evaluation_thinking_budget: Thinking budget for evaluation model (tokens, short samples)

          generation_thinking_budget: Thinking budget for generation model (tokens)

          max_examples_in_prompt: Maximum number of seed examples to include in prompts (long samples only). If
              not set, all seeds are used (subject to token limits).

          max_iterations: Max feedback iterations (short samples only)

          max_revision_cycles: Max revision cycles (long samples only)

          num_examples_in_prompt: Number of examples to include in prompt (short samples only)

          outline_model: AI model for outline generation (long samples only)

          outline_thinking_budget: Thinking budget for outline model (tokens, long samples)

          revision_model: AI model for revisions (long samples only)

          revision_thinking_budget: Thinking budget for revision model (tokens, long samples)

          sample_type: Type of samples to generate

          seed_shuffling_level: Seed shuffling level for long samples. Controls trade-off between prompt caching
              efficiency and data diversity.

          spec_version_id: Specific version ID to use (optional, defaults to latest version)

          sql_validation_level: SQL validation level for long samples with SQL content

          staged_generation: Use staged generation approach (short samples only)

          use_historical_feedback: Use historical feedback (short samples only)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/dataframer/generate/",
            body=await async_maybe_transform(
                {
                    "generation_model": generation_model,
                    "number_of_samples": number_of_samples,
                    "spec_id": spec_id,
                    "enable_revisions": enable_revisions,
                    "evaluation_model": evaluation_model,
                    "evaluation_thinking_budget": evaluation_thinking_budget,
                    "generation_thinking_budget": generation_thinking_budget,
                    "max_examples_in_prompt": max_examples_in_prompt,
                    "max_iterations": max_iterations,
                    "max_revision_cycles": max_revision_cycles,
                    "num_examples_in_prompt": num_examples_in_prompt,
                    "outline_model": outline_model,
                    "outline_thinking_budget": outline_thinking_budget,
                    "revision_model": revision_model,
                    "revision_thinking_budget": revision_thinking_budget,
                    "sample_type": sample_type,
                    "seed_shuffling_level": seed_shuffling_level,
                    "spec_version_id": spec_version_id,
                    "sql_validation_level": sql_validation_level,
                    "staged_generation": staged_generation,
                    "use_historical_feedback": use_historical_feedback,
                },
                generate_create_params.GenerateCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GenerateCreateResponse,
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
    ) -> GenerateRetrieveStatusResponse:
        """
        Get generation status from external service

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not task_id:
            raise ValueError(f"Expected a non-empty value for `task_id` but received {task_id!r}")
        return await self._get(
            f"/api/dataframer/generate/status/{task_id}/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GenerateRetrieveStatusResponse,
        )


class GenerateResourceWithRawResponse:
    def __init__(self, generate: GenerateResource) -> None:
        self._generate = generate

        self.create = to_raw_response_wrapper(
            generate.create,
        )
        self.retrieve_status = to_raw_response_wrapper(
            generate.retrieve_status,
        )


class AsyncGenerateResourceWithRawResponse:
    def __init__(self, generate: AsyncGenerateResource) -> None:
        self._generate = generate

        self.create = async_to_raw_response_wrapper(
            generate.create,
        )
        self.retrieve_status = async_to_raw_response_wrapper(
            generate.retrieve_status,
        )


class GenerateResourceWithStreamingResponse:
    def __init__(self, generate: GenerateResource) -> None:
        self._generate = generate

        self.create = to_streamed_response_wrapper(
            generate.create,
        )
        self.retrieve_status = to_streamed_response_wrapper(
            generate.retrieve_status,
        )


class AsyncGenerateResourceWithStreamingResponse:
    def __init__(self, generate: AsyncGenerateResource) -> None:
        self._generate = generate

        self.create = async_to_streamed_response_wrapper(
            generate.create,
        )
        self.retrieve_status = async_to_streamed_response_wrapper(
            generate.retrieve_status,
        )
