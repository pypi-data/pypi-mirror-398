# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from dataframer import Dataframer, AsyncDataframer
from tests.utils import assert_matches_type
from dataframer.types.dataframer import ChatGetHistoryResponse, ChatSendMessageResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestChat:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_history(self, client: Dataframer) -> None:
        chat = client.dataframer.chat.get_history()
        assert_matches_type(ChatGetHistoryResponse, chat, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_history(self, client: Dataframer) -> None:
        response = client.dataframer.chat.with_raw_response.get_history()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        chat = response.parse()
        assert_matches_type(ChatGetHistoryResponse, chat, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_history(self, client: Dataframer) -> None:
        with client.dataframer.chat.with_streaming_response.get_history() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            chat = response.parse()
            assert_matches_type(ChatGetHistoryResponse, chat, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_send_message(self, client: Dataframer) -> None:
        chat = client.dataframer.chat.send_message(
            evaluation_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            user_message="Why did some samples score lower than others?",
        )
        assert_matches_type(ChatSendMessageResponse, chat, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_send_message_with_all_params(self, client: Dataframer) -> None:
        chat = client.dataframer.chat.send_message(
            evaluation_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            user_message="Why did some samples score lower than others?",
            chat_model="anthropic/claude-opus-4-5",
        )
        assert_matches_type(ChatSendMessageResponse, chat, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_send_message(self, client: Dataframer) -> None:
        response = client.dataframer.chat.with_raw_response.send_message(
            evaluation_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            user_message="Why did some samples score lower than others?",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        chat = response.parse()
        assert_matches_type(ChatSendMessageResponse, chat, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_send_message(self, client: Dataframer) -> None:
        with client.dataframer.chat.with_streaming_response.send_message(
            evaluation_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            user_message="Why did some samples score lower than others?",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            chat = response.parse()
            assert_matches_type(ChatSendMessageResponse, chat, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncChat:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_history(self, async_client: AsyncDataframer) -> None:
        chat = await async_client.dataframer.chat.get_history()
        assert_matches_type(ChatGetHistoryResponse, chat, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_history(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.chat.with_raw_response.get_history()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        chat = await response.parse()
        assert_matches_type(ChatGetHistoryResponse, chat, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_history(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.chat.with_streaming_response.get_history() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            chat = await response.parse()
            assert_matches_type(ChatGetHistoryResponse, chat, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_send_message(self, async_client: AsyncDataframer) -> None:
        chat = await async_client.dataframer.chat.send_message(
            evaluation_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            user_message="Why did some samples score lower than others?",
        )
        assert_matches_type(ChatSendMessageResponse, chat, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_send_message_with_all_params(self, async_client: AsyncDataframer) -> None:
        chat = await async_client.dataframer.chat.send_message(
            evaluation_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            user_message="Why did some samples score lower than others?",
            chat_model="anthropic/claude-opus-4-5",
        )
        assert_matches_type(ChatSendMessageResponse, chat, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_send_message(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.chat.with_raw_response.send_message(
            evaluation_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            user_message="Why did some samples score lower than others?",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        chat = await response.parse()
        assert_matches_type(ChatSendMessageResponse, chat, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_send_message(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.chat.with_streaming_response.send_message(
            evaluation_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            user_message="Why did some samples score lower than others?",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            chat = await response.parse()
            assert_matches_type(ChatSendMessageResponse, chat, path=["response"])

        assert cast(Any, response.is_closed) is True
