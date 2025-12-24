# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from dataframer import Dataframer, AsyncDataframer
from tests.utils import assert_matches_type
from dataframer.types.dataframer import RedTeamCreateTaskResponse, RedTeamRetrieveStatusResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestRedTeam:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_task(self, client: Dataframer) -> None:
        red_team = client.dataframer.red_team.create_task()
        assert_matches_type(RedTeamCreateTaskResponse, red_team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create_task(self, client: Dataframer) -> None:
        response = client.dataframer.red_team.with_raw_response.create_task()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        red_team = response.parse()
        assert_matches_type(RedTeamCreateTaskResponse, red_team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create_task(self, client: Dataframer) -> None:
        with client.dataframer.red_team.with_streaming_response.create_task() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            red_team = response.parse()
            assert_matches_type(RedTeamCreateTaskResponse, red_team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_status(self, client: Dataframer) -> None:
        red_team = client.dataframer.red_team.retrieve_status(
            "task_id",
        )
        assert_matches_type(RedTeamRetrieveStatusResponse, red_team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_status(self, client: Dataframer) -> None:
        response = client.dataframer.red_team.with_raw_response.retrieve_status(
            "task_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        red_team = response.parse()
        assert_matches_type(RedTeamRetrieveStatusResponse, red_team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_status(self, client: Dataframer) -> None:
        with client.dataframer.red_team.with_streaming_response.retrieve_status(
            "task_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            red_team = response.parse()
            assert_matches_type(RedTeamRetrieveStatusResponse, red_team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve_status(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `task_id` but received ''"):
            client.dataframer.red_team.with_raw_response.retrieve_status(
                "",
            )


class TestAsyncRedTeam:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_task(self, async_client: AsyncDataframer) -> None:
        red_team = await async_client.dataframer.red_team.create_task()
        assert_matches_type(RedTeamCreateTaskResponse, red_team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create_task(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.red_team.with_raw_response.create_task()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        red_team = await response.parse()
        assert_matches_type(RedTeamCreateTaskResponse, red_team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create_task(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.red_team.with_streaming_response.create_task() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            red_team = await response.parse()
            assert_matches_type(RedTeamCreateTaskResponse, red_team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_status(self, async_client: AsyncDataframer) -> None:
        red_team = await async_client.dataframer.red_team.retrieve_status(
            "task_id",
        )
        assert_matches_type(RedTeamRetrieveStatusResponse, red_team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_status(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.red_team.with_raw_response.retrieve_status(
            "task_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        red_team = await response.parse()
        assert_matches_type(RedTeamRetrieveStatusResponse, red_team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_status(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.red_team.with_streaming_response.retrieve_status(
            "task_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            red_team = await response.parse()
            assert_matches_type(RedTeamRetrieveStatusResponse, red_team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve_status(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `task_id` but received ''"):
            await async_client.dataframer.red_team.with_raw_response.retrieve_status(
                "",
            )
