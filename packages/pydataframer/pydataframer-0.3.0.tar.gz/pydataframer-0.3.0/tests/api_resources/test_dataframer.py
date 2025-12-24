# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from dataframer import Dataframer, AsyncDataframer
from tests.utils import assert_matches_type
from dataframer.types import (
    DataframerListModelsResponse,
    DataframerCheckHealthResponse,
    DataframerListHistoricalRunsResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestDataframer:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_check_health(self, client: Dataframer) -> None:
        dataframer = client.dataframer.check_health()
        assert_matches_type(DataframerCheckHealthResponse, dataframer, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_check_health(self, client: Dataframer) -> None:
        response = client.dataframer.with_raw_response.check_health()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataframer = response.parse()
        assert_matches_type(DataframerCheckHealthResponse, dataframer, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_check_health(self, client: Dataframer) -> None:
        with client.dataframer.with_streaming_response.check_health() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataframer = response.parse()
            assert_matches_type(DataframerCheckHealthResponse, dataframer, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_historical_runs(self, client: Dataframer) -> None:
        dataframer = client.dataframer.list_historical_runs()
        assert_matches_type(DataframerListHistoricalRunsResponse, dataframer, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_historical_runs(self, client: Dataframer) -> None:
        response = client.dataframer.with_raw_response.list_historical_runs()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataframer = response.parse()
        assert_matches_type(DataframerListHistoricalRunsResponse, dataframer, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_historical_runs(self, client: Dataframer) -> None:
        with client.dataframer.with_streaming_response.list_historical_runs() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataframer = response.parse()
            assert_matches_type(DataframerListHistoricalRunsResponse, dataframer, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_models(self, client: Dataframer) -> None:
        dataframer = client.dataframer.list_models()
        assert_matches_type(DataframerListModelsResponse, dataframer, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_models(self, client: Dataframer) -> None:
        response = client.dataframer.with_raw_response.list_models()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataframer = response.parse()
        assert_matches_type(DataframerListModelsResponse, dataframer, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_models(self, client: Dataframer) -> None:
        with client.dataframer.with_streaming_response.list_models() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataframer = response.parse()
            assert_matches_type(DataframerListModelsResponse, dataframer, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncDataframer:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_check_health(self, async_client: AsyncDataframer) -> None:
        dataframer = await async_client.dataframer.check_health()
        assert_matches_type(DataframerCheckHealthResponse, dataframer, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_check_health(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.with_raw_response.check_health()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataframer = await response.parse()
        assert_matches_type(DataframerCheckHealthResponse, dataframer, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_check_health(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.with_streaming_response.check_health() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataframer = await response.parse()
            assert_matches_type(DataframerCheckHealthResponse, dataframer, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_historical_runs(self, async_client: AsyncDataframer) -> None:
        dataframer = await async_client.dataframer.list_historical_runs()
        assert_matches_type(DataframerListHistoricalRunsResponse, dataframer, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_historical_runs(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.with_raw_response.list_historical_runs()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataframer = await response.parse()
        assert_matches_type(DataframerListHistoricalRunsResponse, dataframer, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_historical_runs(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.with_streaming_response.list_historical_runs() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataframer = await response.parse()
            assert_matches_type(DataframerListHistoricalRunsResponse, dataframer, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_models(self, async_client: AsyncDataframer) -> None:
        dataframer = await async_client.dataframer.list_models()
        assert_matches_type(DataframerListModelsResponse, dataframer, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_models(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.with_raw_response.list_models()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataframer = await response.parse()
        assert_matches_type(DataframerListModelsResponse, dataframer, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_models(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.with_streaming_response.list_models() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataframer = await response.parse()
            assert_matches_type(DataframerListModelsResponse, dataframer, path=["response"])

        assert cast(Any, response.is_closed) is True
