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
from ...types.dataframer import chat_send_message_params
from ...types.dataframer.chat_get_history_response import ChatGetHistoryResponse
from ...types.dataframer.chat_send_message_response import ChatSendMessageResponse

__all__ = ["ChatResource", "AsyncChatResource"]


class ChatResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ChatResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#accessing-raw-response-data-eg-headers
        """
        return ChatResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ChatResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#with_streaming_response
        """
        return ChatResourceWithStreamingResponse(self)

    def get_history(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChatGetHistoryResponse:
        """Get chat history for an evaluation"""
        return self._get(
            "/api/dataframer/chat/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChatGetHistoryResponse,
        )

    def send_message(
        self,
        *,
        evaluation_id: str,
        user_message: str,
        chat_model: Literal[
            "anthropic/claude-opus-4-5",
            "anthropic/claude-opus-4-5-thinking",
            "anthropic/claude-sonnet-4-5",
            "anthropic/claude-sonnet-4-5-thinking",
            "anthropic/claude-haiku-4-5",
        ]
        | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChatSendMessageResponse:
        """
        Send a natural language query about evaluation results and get AI-powered
        insights.

        The chat process:

        1. Retrieves generated samples from the run
        2. Includes previous chat history for context
        3. Sends query to AI model with evaluation context
        4. Returns AI response with insights
        5. Saves conversation for future reference

        **Use Cases**:

        - Ask why samples scored lower
        - Understand conformance issues
        - Get recommendations for improvement
        - Explore evaluation results interactively

        Args:
          evaluation_id: ID of the evaluation to chat about

          user_message: Your question or message about the evaluation results

          chat_model: AI model to use for chat (optional)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/dataframer/chat/",
            body=maybe_transform(
                {
                    "evaluation_id": evaluation_id,
                    "user_message": user_message,
                    "chat_model": chat_model,
                },
                chat_send_message_params.ChatSendMessageParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChatSendMessageResponse,
        )


class AsyncChatResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncChatResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncChatResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncChatResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#with_streaming_response
        """
        return AsyncChatResourceWithStreamingResponse(self)

    async def get_history(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChatGetHistoryResponse:
        """Get chat history for an evaluation"""
        return await self._get(
            "/api/dataframer/chat/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChatGetHistoryResponse,
        )

    async def send_message(
        self,
        *,
        evaluation_id: str,
        user_message: str,
        chat_model: Literal[
            "anthropic/claude-opus-4-5",
            "anthropic/claude-opus-4-5-thinking",
            "anthropic/claude-sonnet-4-5",
            "anthropic/claude-sonnet-4-5-thinking",
            "anthropic/claude-haiku-4-5",
        ]
        | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChatSendMessageResponse:
        """
        Send a natural language query about evaluation results and get AI-powered
        insights.

        The chat process:

        1. Retrieves generated samples from the run
        2. Includes previous chat history for context
        3. Sends query to AI model with evaluation context
        4. Returns AI response with insights
        5. Saves conversation for future reference

        **Use Cases**:

        - Ask why samples scored lower
        - Understand conformance issues
        - Get recommendations for improvement
        - Explore evaluation results interactively

        Args:
          evaluation_id: ID of the evaluation to chat about

          user_message: Your question or message about the evaluation results

          chat_model: AI model to use for chat (optional)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/dataframer/chat/",
            body=await async_maybe_transform(
                {
                    "evaluation_id": evaluation_id,
                    "user_message": user_message,
                    "chat_model": chat_model,
                },
                chat_send_message_params.ChatSendMessageParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChatSendMessageResponse,
        )


class ChatResourceWithRawResponse:
    def __init__(self, chat: ChatResource) -> None:
        self._chat = chat

        self.get_history = to_raw_response_wrapper(
            chat.get_history,
        )
        self.send_message = to_raw_response_wrapper(
            chat.send_message,
        )


class AsyncChatResourceWithRawResponse:
    def __init__(self, chat: AsyncChatResource) -> None:
        self._chat = chat

        self.get_history = async_to_raw_response_wrapper(
            chat.get_history,
        )
        self.send_message = async_to_raw_response_wrapper(
            chat.send_message,
        )


class ChatResourceWithStreamingResponse:
    def __init__(self, chat: ChatResource) -> None:
        self._chat = chat

        self.get_history = to_streamed_response_wrapper(
            chat.get_history,
        )
        self.send_message = to_streamed_response_wrapper(
            chat.send_message,
        )


class AsyncChatResourceWithStreamingResponse:
    def __init__(self, chat: AsyncChatResource) -> None:
        self._chat = chat

        self.get_history = async_to_streamed_response_wrapper(
            chat.get_history,
        )
        self.send_message = async_to_streamed_response_wrapper(
            chat.send_message,
        )
