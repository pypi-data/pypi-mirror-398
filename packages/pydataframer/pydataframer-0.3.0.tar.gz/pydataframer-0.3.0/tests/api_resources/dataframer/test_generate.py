# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from dataframer import Dataframer, AsyncDataframer
from tests.utils import assert_matches_type
from dataframer.types.dataframer import GenerateCreateResponse, GenerateRetrieveStatusResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestGenerate:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Dataframer) -> None:
        generate = client.dataframer.generate.create(
            generation_model="anthropic/claude-opus-4-5",
            number_of_samples=1,
            spec_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(GenerateCreateResponse, generate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: Dataframer) -> None:
        generate = client.dataframer.generate.create(
            generation_model="anthropic/claude-opus-4-5",
            number_of_samples=1,
            spec_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            enable_revisions=True,
            evaluation_model="anthropic/claude-opus-4-5",
            evaluation_thinking_budget=1024,
            generation_thinking_budget=1024,
            max_examples_in_prompt=1,
            max_iterations=0,
            max_revision_cycles=1,
            num_examples_in_prompt=1,
            outline_model="anthropic/claude-opus-4-5",
            outline_thinking_budget=1024,
            revision_model="anthropic/claude-opus-4-5",
            revision_thinking_budget=1024,
            sample_type="short",
            seed_shuffling_level="none",
            spec_version_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            sql_validation_level="syntax",
            staged_generation=True,
            use_historical_feedback=True,
        )
        assert_matches_type(GenerateCreateResponse, generate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Dataframer) -> None:
        response = client.dataframer.generate.with_raw_response.create(
            generation_model="anthropic/claude-opus-4-5",
            number_of_samples=1,
            spec_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        generate = response.parse()
        assert_matches_type(GenerateCreateResponse, generate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Dataframer) -> None:
        with client.dataframer.generate.with_streaming_response.create(
            generation_model="anthropic/claude-opus-4-5",
            number_of_samples=1,
            spec_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            generate = response.parse()
            assert_matches_type(GenerateCreateResponse, generate, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_status(self, client: Dataframer) -> None:
        generate = client.dataframer.generate.retrieve_status(
            "task_id",
        )
        assert_matches_type(GenerateRetrieveStatusResponse, generate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_status(self, client: Dataframer) -> None:
        response = client.dataframer.generate.with_raw_response.retrieve_status(
            "task_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        generate = response.parse()
        assert_matches_type(GenerateRetrieveStatusResponse, generate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_status(self, client: Dataframer) -> None:
        with client.dataframer.generate.with_streaming_response.retrieve_status(
            "task_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            generate = response.parse()
            assert_matches_type(GenerateRetrieveStatusResponse, generate, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve_status(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `task_id` but received ''"):
            client.dataframer.generate.with_raw_response.retrieve_status(
                "",
            )


class TestAsyncGenerate:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncDataframer) -> None:
        generate = await async_client.dataframer.generate.create(
            generation_model="anthropic/claude-opus-4-5",
            number_of_samples=1,
            spec_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(GenerateCreateResponse, generate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncDataframer) -> None:
        generate = await async_client.dataframer.generate.create(
            generation_model="anthropic/claude-opus-4-5",
            number_of_samples=1,
            spec_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            enable_revisions=True,
            evaluation_model="anthropic/claude-opus-4-5",
            evaluation_thinking_budget=1024,
            generation_thinking_budget=1024,
            max_examples_in_prompt=1,
            max_iterations=0,
            max_revision_cycles=1,
            num_examples_in_prompt=1,
            outline_model="anthropic/claude-opus-4-5",
            outline_thinking_budget=1024,
            revision_model="anthropic/claude-opus-4-5",
            revision_thinking_budget=1024,
            sample_type="short",
            seed_shuffling_level="none",
            spec_version_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            sql_validation_level="syntax",
            staged_generation=True,
            use_historical_feedback=True,
        )
        assert_matches_type(GenerateCreateResponse, generate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.generate.with_raw_response.create(
            generation_model="anthropic/claude-opus-4-5",
            number_of_samples=1,
            spec_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        generate = await response.parse()
        assert_matches_type(GenerateCreateResponse, generate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.generate.with_streaming_response.create(
            generation_model="anthropic/claude-opus-4-5",
            number_of_samples=1,
            spec_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            generate = await response.parse()
            assert_matches_type(GenerateCreateResponse, generate, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_status(self, async_client: AsyncDataframer) -> None:
        generate = await async_client.dataframer.generate.retrieve_status(
            "task_id",
        )
        assert_matches_type(GenerateRetrieveStatusResponse, generate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_status(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.generate.with_raw_response.retrieve_status(
            "task_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        generate = await response.parse()
        assert_matches_type(GenerateRetrieveStatusResponse, generate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_status(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.generate.with_streaming_response.retrieve_status(
            "task_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            generate = await response.parse()
            assert_matches_type(GenerateRetrieveStatusResponse, generate, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve_status(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `task_id` but received ''"):
            await async_client.dataframer.generate.with_raw_response.retrieve_status(
                "",
            )
