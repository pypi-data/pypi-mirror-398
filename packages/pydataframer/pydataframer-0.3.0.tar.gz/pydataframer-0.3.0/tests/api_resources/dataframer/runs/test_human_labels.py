# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from dataframer import Dataframer, AsyncDataframer
from tests.utils import assert_matches_type
from dataframer.types.dataframer.runs import HumanLabelListResponse, HumanLabelCreateResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestHumanLabels:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Dataframer) -> None:
        human_label = client.dataframer.runs.human_labels.create(
            "run_id",
        )
        assert_matches_type(HumanLabelCreateResponse, human_label, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Dataframer) -> None:
        response = client.dataframer.runs.human_labels.with_raw_response.create(
            "run_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        human_label = response.parse()
        assert_matches_type(HumanLabelCreateResponse, human_label, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Dataframer) -> None:
        with client.dataframer.runs.human_labels.with_streaming_response.create(
            "run_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            human_label = response.parse()
            assert_matches_type(HumanLabelCreateResponse, human_label, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_create(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            client.dataframer.runs.human_labels.with_raw_response.create(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Dataframer) -> None:
        human_label = client.dataframer.runs.human_labels.list(
            "run_id",
        )
        assert_matches_type(HumanLabelListResponse, human_label, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Dataframer) -> None:
        response = client.dataframer.runs.human_labels.with_raw_response.list(
            "run_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        human_label = response.parse()
        assert_matches_type(HumanLabelListResponse, human_label, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Dataframer) -> None:
        with client.dataframer.runs.human_labels.with_streaming_response.list(
            "run_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            human_label = response.parse()
            assert_matches_type(HumanLabelListResponse, human_label, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            client.dataframer.runs.human_labels.with_raw_response.list(
                "",
            )


class TestAsyncHumanLabels:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncDataframer) -> None:
        human_label = await async_client.dataframer.runs.human_labels.create(
            "run_id",
        )
        assert_matches_type(HumanLabelCreateResponse, human_label, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.runs.human_labels.with_raw_response.create(
            "run_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        human_label = await response.parse()
        assert_matches_type(HumanLabelCreateResponse, human_label, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.runs.human_labels.with_streaming_response.create(
            "run_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            human_label = await response.parse()
            assert_matches_type(HumanLabelCreateResponse, human_label, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_create(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            await async_client.dataframer.runs.human_labels.with_raw_response.create(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncDataframer) -> None:
        human_label = await async_client.dataframer.runs.human_labels.list(
            "run_id",
        )
        assert_matches_type(HumanLabelListResponse, human_label, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.runs.human_labels.with_raw_response.list(
            "run_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        human_label = await response.parse()
        assert_matches_type(HumanLabelListResponse, human_label, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.runs.human_labels.with_streaming_response.list(
            "run_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            human_label = await response.parse()
            assert_matches_type(HumanLabelListResponse, human_label, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            await async_client.dataframer.runs.human_labels.with_raw_response.list(
                "",
            )
