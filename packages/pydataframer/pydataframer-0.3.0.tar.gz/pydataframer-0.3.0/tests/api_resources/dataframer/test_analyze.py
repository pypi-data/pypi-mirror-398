# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from dataframer import Dataframer, AsyncDataframer
from tests.utils import assert_matches_type
from dataframer.types.dataframer import AnalyzeCreateResponse, AnalyzeGetStatusResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestAnalyze:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Dataframer) -> None:
        analyze = client.dataframer.analyze.create(
            dataset_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            name="name",
        )
        assert_matches_type(AnalyzeCreateResponse, analyze, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: Dataframer) -> None:
        analyze = client.dataframer.analyze.create(
            dataset_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            name="name",
            analysis_model_name="anthropic/claude-opus-4-5",
            description="description",
            extrapolate_axes=True,
            extrapolate_values=True,
            generate_distributions=True,
            generation_objectives="generation_objectives",
            use_truncation=True,
        )
        assert_matches_type(AnalyzeCreateResponse, analyze, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Dataframer) -> None:
        response = client.dataframer.analyze.with_raw_response.create(
            dataset_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            name="name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        analyze = response.parse()
        assert_matches_type(AnalyzeCreateResponse, analyze, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Dataframer) -> None:
        with client.dataframer.analyze.with_streaming_response.create(
            dataset_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            name="name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            analyze = response.parse()
            assert_matches_type(AnalyzeCreateResponse, analyze, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_status(self, client: Dataframer) -> None:
        analyze = client.dataframer.analyze.get_status(
            "task_id",
        )
        assert_matches_type(AnalyzeGetStatusResponse, analyze, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_status(self, client: Dataframer) -> None:
        response = client.dataframer.analyze.with_raw_response.get_status(
            "task_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        analyze = response.parse()
        assert_matches_type(AnalyzeGetStatusResponse, analyze, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_status(self, client: Dataframer) -> None:
        with client.dataframer.analyze.with_streaming_response.get_status(
            "task_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            analyze = response.parse()
            assert_matches_type(AnalyzeGetStatusResponse, analyze, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_get_status(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `task_id` but received ''"):
            client.dataframer.analyze.with_raw_response.get_status(
                "",
            )


class TestAsyncAnalyze:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncDataframer) -> None:
        analyze = await async_client.dataframer.analyze.create(
            dataset_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            name="name",
        )
        assert_matches_type(AnalyzeCreateResponse, analyze, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncDataframer) -> None:
        analyze = await async_client.dataframer.analyze.create(
            dataset_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            name="name",
            analysis_model_name="anthropic/claude-opus-4-5",
            description="description",
            extrapolate_axes=True,
            extrapolate_values=True,
            generate_distributions=True,
            generation_objectives="generation_objectives",
            use_truncation=True,
        )
        assert_matches_type(AnalyzeCreateResponse, analyze, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.analyze.with_raw_response.create(
            dataset_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            name="name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        analyze = await response.parse()
        assert_matches_type(AnalyzeCreateResponse, analyze, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.analyze.with_streaming_response.create(
            dataset_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            name="name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            analyze = await response.parse()
            assert_matches_type(AnalyzeCreateResponse, analyze, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_status(self, async_client: AsyncDataframer) -> None:
        analyze = await async_client.dataframer.analyze.get_status(
            "task_id",
        )
        assert_matches_type(AnalyzeGetStatusResponse, analyze, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_status(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.analyze.with_raw_response.get_status(
            "task_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        analyze = await response.parse()
        assert_matches_type(AnalyzeGetStatusResponse, analyze, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_status(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.analyze.with_streaming_response.get_status(
            "task_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            analyze = await response.parse()
            assert_matches_type(AnalyzeGetStatusResponse, analyze, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_get_status(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `task_id` but received ''"):
            await async_client.dataframer.analyze.with_raw_response.get_status(
                "",
            )
