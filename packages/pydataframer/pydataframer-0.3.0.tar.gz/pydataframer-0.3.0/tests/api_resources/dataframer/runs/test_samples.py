# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from dataframer import Dataframer, AsyncDataframer
from tests.utils import assert_matches_type
from dataframer.types.dataframer.runs import (
    SampleListResponse,
    SampleRetrieveByIndicesResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSamples:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Dataframer) -> None:
        sample = client.dataframer.runs.samples.list(
            run_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(SampleListResponse, sample, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Dataframer) -> None:
        sample = client.dataframer.runs.samples.list(
            run_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            limit=0,
            offset=0,
        )
        assert_matches_type(SampleListResponse, sample, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Dataframer) -> None:
        response = client.dataframer.runs.samples.with_raw_response.list(
            run_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sample = response.parse()
        assert_matches_type(SampleListResponse, sample, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Dataframer) -> None:
        with client.dataframer.runs.samples.with_streaming_response.list(
            run_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sample = response.parse()
            assert_matches_type(SampleListResponse, sample, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            client.dataframer.runs.samples.with_raw_response.list(
                run_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_by_indices(self, client: Dataframer) -> None:
        sample = client.dataframer.runs.samples.retrieve_by_indices(
            run_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            indices=[0, 1, 2, 5, 10],
        )
        assert_matches_type(SampleRetrieveByIndicesResponse, sample, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_by_indices(self, client: Dataframer) -> None:
        response = client.dataframer.runs.samples.with_raw_response.retrieve_by_indices(
            run_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            indices=[0, 1, 2, 5, 10],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sample = response.parse()
        assert_matches_type(SampleRetrieveByIndicesResponse, sample, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_by_indices(self, client: Dataframer) -> None:
        with client.dataframer.runs.samples.with_streaming_response.retrieve_by_indices(
            run_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            indices=[0, 1, 2, 5, 10],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sample = response.parse()
            assert_matches_type(SampleRetrieveByIndicesResponse, sample, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve_by_indices(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            client.dataframer.runs.samples.with_raw_response.retrieve_by_indices(
                run_id="",
                indices=[0, 1, 2, 5, 10],
            )


class TestAsyncSamples:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncDataframer) -> None:
        sample = await async_client.dataframer.runs.samples.list(
            run_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(SampleListResponse, sample, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncDataframer) -> None:
        sample = await async_client.dataframer.runs.samples.list(
            run_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            limit=0,
            offset=0,
        )
        assert_matches_type(SampleListResponse, sample, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.runs.samples.with_raw_response.list(
            run_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sample = await response.parse()
        assert_matches_type(SampleListResponse, sample, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.runs.samples.with_streaming_response.list(
            run_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sample = await response.parse()
            assert_matches_type(SampleListResponse, sample, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            await async_client.dataframer.runs.samples.with_raw_response.list(
                run_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_by_indices(self, async_client: AsyncDataframer) -> None:
        sample = await async_client.dataframer.runs.samples.retrieve_by_indices(
            run_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            indices=[0, 1, 2, 5, 10],
        )
        assert_matches_type(SampleRetrieveByIndicesResponse, sample, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_by_indices(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.runs.samples.with_raw_response.retrieve_by_indices(
            run_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            indices=[0, 1, 2, 5, 10],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sample = await response.parse()
        assert_matches_type(SampleRetrieveByIndicesResponse, sample, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_by_indices(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.runs.samples.with_streaming_response.retrieve_by_indices(
            run_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            indices=[0, 1, 2, 5, 10],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sample = await response.parse()
            assert_matches_type(SampleRetrieveByIndicesResponse, sample, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve_by_indices(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            await async_client.dataframer.runs.samples.with_raw_response.retrieve_by_indices(
                run_id="",
                indices=[0, 1, 2, 5, 10],
            )
