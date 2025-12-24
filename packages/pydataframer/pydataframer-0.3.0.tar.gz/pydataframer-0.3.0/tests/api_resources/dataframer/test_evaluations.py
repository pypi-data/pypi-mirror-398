# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from dataframer import Dataframer, AsyncDataframer
from tests.utils import assert_matches_type
from dataframer.types.dataframer import (
    EvaluationListResponse,
    EvaluationCreateResponse,
    EvaluationRetrieveResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestEvaluations:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Dataframer) -> None:
        evaluation = client.dataframer.evaluations.create(
            run_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(EvaluationCreateResponse, evaluation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: Dataframer) -> None:
        evaluation = client.dataframer.evaluations.create(
            run_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            evaluation_model="anthropic/claude-opus-4-5",
        )
        assert_matches_type(EvaluationCreateResponse, evaluation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Dataframer) -> None:
        response = client.dataframer.evaluations.with_raw_response.create(
            run_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluation = response.parse()
        assert_matches_type(EvaluationCreateResponse, evaluation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Dataframer) -> None:
        with client.dataframer.evaluations.with_streaming_response.create(
            run_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluation = response.parse()
            assert_matches_type(EvaluationCreateResponse, evaluation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Dataframer) -> None:
        evaluation = client.dataframer.evaluations.retrieve(
            "evaluation_id",
        )
        assert_matches_type(EvaluationRetrieveResponse, evaluation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Dataframer) -> None:
        response = client.dataframer.evaluations.with_raw_response.retrieve(
            "evaluation_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluation = response.parse()
        assert_matches_type(EvaluationRetrieveResponse, evaluation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Dataframer) -> None:
        with client.dataframer.evaluations.with_streaming_response.retrieve(
            "evaluation_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluation = response.parse()
            assert_matches_type(EvaluationRetrieveResponse, evaluation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `evaluation_id` but received ''"):
            client.dataframer.evaluations.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Dataframer) -> None:
        evaluation = client.dataframer.evaluations.list()
        assert_matches_type(EvaluationListResponse, evaluation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Dataframer) -> None:
        response = client.dataframer.evaluations.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluation = response.parse()
        assert_matches_type(EvaluationListResponse, evaluation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Dataframer) -> None:
        with client.dataframer.evaluations.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluation = response.parse()
            assert_matches_type(EvaluationListResponse, evaluation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Dataframer) -> None:
        evaluation = client.dataframer.evaluations.delete(
            "evaluation_id",
        )
        assert evaluation is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Dataframer) -> None:
        response = client.dataframer.evaluations.with_raw_response.delete(
            "evaluation_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluation = response.parse()
        assert evaluation is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Dataframer) -> None:
        with client.dataframer.evaluations.with_streaming_response.delete(
            "evaluation_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluation = response.parse()
            assert evaluation is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `evaluation_id` but received ''"):
            client.dataframer.evaluations.with_raw_response.delete(
                "",
            )


class TestAsyncEvaluations:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncDataframer) -> None:
        evaluation = await async_client.dataframer.evaluations.create(
            run_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(EvaluationCreateResponse, evaluation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncDataframer) -> None:
        evaluation = await async_client.dataframer.evaluations.create(
            run_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            evaluation_model="anthropic/claude-opus-4-5",
        )
        assert_matches_type(EvaluationCreateResponse, evaluation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.evaluations.with_raw_response.create(
            run_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluation = await response.parse()
        assert_matches_type(EvaluationCreateResponse, evaluation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.evaluations.with_streaming_response.create(
            run_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluation = await response.parse()
            assert_matches_type(EvaluationCreateResponse, evaluation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncDataframer) -> None:
        evaluation = await async_client.dataframer.evaluations.retrieve(
            "evaluation_id",
        )
        assert_matches_type(EvaluationRetrieveResponse, evaluation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.evaluations.with_raw_response.retrieve(
            "evaluation_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluation = await response.parse()
        assert_matches_type(EvaluationRetrieveResponse, evaluation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.evaluations.with_streaming_response.retrieve(
            "evaluation_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluation = await response.parse()
            assert_matches_type(EvaluationRetrieveResponse, evaluation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `evaluation_id` but received ''"):
            await async_client.dataframer.evaluations.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncDataframer) -> None:
        evaluation = await async_client.dataframer.evaluations.list()
        assert_matches_type(EvaluationListResponse, evaluation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.evaluations.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluation = await response.parse()
        assert_matches_type(EvaluationListResponse, evaluation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.evaluations.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluation = await response.parse()
            assert_matches_type(EvaluationListResponse, evaluation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncDataframer) -> None:
        evaluation = await async_client.dataframer.evaluations.delete(
            "evaluation_id",
        )
        assert evaluation is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.evaluations.with_raw_response.delete(
            "evaluation_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluation = await response.parse()
        assert evaluation is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.evaluations.with_streaming_response.delete(
            "evaluation_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluation = await response.parse()
            assert evaluation is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `evaluation_id` but received ''"):
            await async_client.dataframer.evaluations.with_raw_response.delete(
                "",
            )
