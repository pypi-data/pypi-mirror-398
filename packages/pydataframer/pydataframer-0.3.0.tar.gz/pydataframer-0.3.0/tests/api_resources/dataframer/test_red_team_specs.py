# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from dataframer import Dataframer, AsyncDataframer
from tests.utils import assert_matches_type
from dataframer.types.dataframer import (
    RedTeamSpecListResponse,
    RedTeamSpecCreateResponse,
    RedTeamSpecUpdateResponse,
    RedTeamSpecRetrieveResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestRedTeamSpecs:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Dataframer) -> None:
        red_team_spec = client.dataframer.red_team_specs.create()
        assert_matches_type(RedTeamSpecCreateResponse, red_team_spec, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Dataframer) -> None:
        response = client.dataframer.red_team_specs.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        red_team_spec = response.parse()
        assert_matches_type(RedTeamSpecCreateResponse, red_team_spec, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Dataframer) -> None:
        with client.dataframer.red_team_specs.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            red_team_spec = response.parse()
            assert_matches_type(RedTeamSpecCreateResponse, red_team_spec, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Dataframer) -> None:
        red_team_spec = client.dataframer.red_team_specs.retrieve(
            "spec_id",
        )
        assert_matches_type(RedTeamSpecRetrieveResponse, red_team_spec, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Dataframer) -> None:
        response = client.dataframer.red_team_specs.with_raw_response.retrieve(
            "spec_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        red_team_spec = response.parse()
        assert_matches_type(RedTeamSpecRetrieveResponse, red_team_spec, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Dataframer) -> None:
        with client.dataframer.red_team_specs.with_streaming_response.retrieve(
            "spec_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            red_team_spec = response.parse()
            assert_matches_type(RedTeamSpecRetrieveResponse, red_team_spec, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `spec_id` but received ''"):
            client.dataframer.red_team_specs.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: Dataframer) -> None:
        red_team_spec = client.dataframer.red_team_specs.update(
            "spec_id",
        )
        assert_matches_type(RedTeamSpecUpdateResponse, red_team_spec, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: Dataframer) -> None:
        response = client.dataframer.red_team_specs.with_raw_response.update(
            "spec_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        red_team_spec = response.parse()
        assert_matches_type(RedTeamSpecUpdateResponse, red_team_spec, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: Dataframer) -> None:
        with client.dataframer.red_team_specs.with_streaming_response.update(
            "spec_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            red_team_spec = response.parse()
            assert_matches_type(RedTeamSpecUpdateResponse, red_team_spec, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `spec_id` but received ''"):
            client.dataframer.red_team_specs.with_raw_response.update(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Dataframer) -> None:
        red_team_spec = client.dataframer.red_team_specs.list()
        assert_matches_type(RedTeamSpecListResponse, red_team_spec, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Dataframer) -> None:
        response = client.dataframer.red_team_specs.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        red_team_spec = response.parse()
        assert_matches_type(RedTeamSpecListResponse, red_team_spec, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Dataframer) -> None:
        with client.dataframer.red_team_specs.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            red_team_spec = response.parse()
            assert_matches_type(RedTeamSpecListResponse, red_team_spec, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Dataframer) -> None:
        red_team_spec = client.dataframer.red_team_specs.delete(
            "spec_id",
        )
        assert red_team_spec is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Dataframer) -> None:
        response = client.dataframer.red_team_specs.with_raw_response.delete(
            "spec_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        red_team_spec = response.parse()
        assert red_team_spec is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Dataframer) -> None:
        with client.dataframer.red_team_specs.with_streaming_response.delete(
            "spec_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            red_team_spec = response.parse()
            assert red_team_spec is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `spec_id` but received ''"):
            client.dataframer.red_team_specs.with_raw_response.delete(
                "",
            )


class TestAsyncRedTeamSpecs:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncDataframer) -> None:
        red_team_spec = await async_client.dataframer.red_team_specs.create()
        assert_matches_type(RedTeamSpecCreateResponse, red_team_spec, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.red_team_specs.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        red_team_spec = await response.parse()
        assert_matches_type(RedTeamSpecCreateResponse, red_team_spec, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.red_team_specs.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            red_team_spec = await response.parse()
            assert_matches_type(RedTeamSpecCreateResponse, red_team_spec, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncDataframer) -> None:
        red_team_spec = await async_client.dataframer.red_team_specs.retrieve(
            "spec_id",
        )
        assert_matches_type(RedTeamSpecRetrieveResponse, red_team_spec, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.red_team_specs.with_raw_response.retrieve(
            "spec_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        red_team_spec = await response.parse()
        assert_matches_type(RedTeamSpecRetrieveResponse, red_team_spec, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.red_team_specs.with_streaming_response.retrieve(
            "spec_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            red_team_spec = await response.parse()
            assert_matches_type(RedTeamSpecRetrieveResponse, red_team_spec, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `spec_id` but received ''"):
            await async_client.dataframer.red_team_specs.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncDataframer) -> None:
        red_team_spec = await async_client.dataframer.red_team_specs.update(
            "spec_id",
        )
        assert_matches_type(RedTeamSpecUpdateResponse, red_team_spec, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.red_team_specs.with_raw_response.update(
            "spec_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        red_team_spec = await response.parse()
        assert_matches_type(RedTeamSpecUpdateResponse, red_team_spec, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.red_team_specs.with_streaming_response.update(
            "spec_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            red_team_spec = await response.parse()
            assert_matches_type(RedTeamSpecUpdateResponse, red_team_spec, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `spec_id` but received ''"):
            await async_client.dataframer.red_team_specs.with_raw_response.update(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncDataframer) -> None:
        red_team_spec = await async_client.dataframer.red_team_specs.list()
        assert_matches_type(RedTeamSpecListResponse, red_team_spec, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.red_team_specs.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        red_team_spec = await response.parse()
        assert_matches_type(RedTeamSpecListResponse, red_team_spec, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.red_team_specs.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            red_team_spec = await response.parse()
            assert_matches_type(RedTeamSpecListResponse, red_team_spec, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncDataframer) -> None:
        red_team_spec = await async_client.dataframer.red_team_specs.delete(
            "spec_id",
        )
        assert red_team_spec is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.red_team_specs.with_raw_response.delete(
            "spec_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        red_team_spec = await response.parse()
        assert red_team_spec is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.red_team_specs.with_streaming_response.delete(
            "spec_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            red_team_spec = await response.parse()
            assert red_team_spec is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `spec_id` but received ''"):
            await async_client.dataframer.red_team_specs.with_raw_response.delete(
                "",
            )
