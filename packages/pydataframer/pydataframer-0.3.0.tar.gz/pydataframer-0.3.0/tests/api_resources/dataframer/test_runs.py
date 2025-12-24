# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from dataframer import Dataframer, AsyncDataframer
from tests.utils import assert_matches_type
from dataframer.types.dataframer import (
    RunListResponse,
    RunCreateResponse,
    RunStatusResponse,
    RunUpdateResponse,
    RunRetrieveResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestRuns:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Dataframer) -> None:
        run = client.dataframer.runs.create(
            number_of_samples=1,
            runtime_params={"foo": "bar"},
            spec_version_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(RunCreateResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Dataframer) -> None:
        response = client.dataframer.runs.with_raw_response.create(
            number_of_samples=1,
            runtime_params={"foo": "bar"},
            spec_version_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        run = response.parse()
        assert_matches_type(RunCreateResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Dataframer) -> None:
        with client.dataframer.runs.with_streaming_response.create(
            number_of_samples=1,
            runtime_params={"foo": "bar"},
            spec_version_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            run = response.parse()
            assert_matches_type(RunCreateResponse, run, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Dataframer) -> None:
        run = client.dataframer.runs.retrieve(
            "run_id",
        )
        assert_matches_type(RunRetrieveResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Dataframer) -> None:
        response = client.dataframer.runs.with_raw_response.retrieve(
            "run_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        run = response.parse()
        assert_matches_type(RunRetrieveResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Dataframer) -> None:
        with client.dataframer.runs.with_streaming_response.retrieve(
            "run_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            run = response.parse()
            assert_matches_type(RunRetrieveResponse, run, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            client.dataframer.runs.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: Dataframer) -> None:
        run = client.dataframer.runs.update(
            "run_id",
        )
        assert_matches_type(RunUpdateResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: Dataframer) -> None:
        response = client.dataframer.runs.with_raw_response.update(
            "run_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        run = response.parse()
        assert_matches_type(RunUpdateResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: Dataframer) -> None:
        with client.dataframer.runs.with_streaming_response.update(
            "run_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            run = response.parse()
            assert_matches_type(RunUpdateResponse, run, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            client.dataframer.runs.with_raw_response.update(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Dataframer) -> None:
        run = client.dataframer.runs.list()
        assert_matches_type(RunListResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Dataframer) -> None:
        response = client.dataframer.runs.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        run = response.parse()
        assert_matches_type(RunListResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Dataframer) -> None:
        with client.dataframer.runs.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            run = response.parse()
            assert_matches_type(RunListResponse, run, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Dataframer) -> None:
        run = client.dataframer.runs.delete(
            "run_id",
        )
        assert run is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Dataframer) -> None:
        response = client.dataframer.runs.with_raw_response.delete(
            "run_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        run = response.parse()
        assert run is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Dataframer) -> None:
        with client.dataframer.runs.with_streaming_response.delete(
            "run_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            run = response.parse()
            assert run is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            client.dataframer.runs.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_status(self, client: Dataframer) -> None:
        run = client.dataframer.runs.status(
            "run_id",
        )
        assert_matches_type(RunStatusResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_status(self, client: Dataframer) -> None:
        response = client.dataframer.runs.with_raw_response.status(
            "run_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        run = response.parse()
        assert_matches_type(RunStatusResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_status(self, client: Dataframer) -> None:
        with client.dataframer.runs.with_streaming_response.status(
            "run_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            run = response.parse()
            assert_matches_type(RunStatusResponse, run, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_status(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            client.dataframer.runs.with_raw_response.status(
                "",
            )


class TestAsyncRuns:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncDataframer) -> None:
        run = await async_client.dataframer.runs.create(
            number_of_samples=1,
            runtime_params={"foo": "bar"},
            spec_version_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(RunCreateResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.runs.with_raw_response.create(
            number_of_samples=1,
            runtime_params={"foo": "bar"},
            spec_version_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        run = await response.parse()
        assert_matches_type(RunCreateResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.runs.with_streaming_response.create(
            number_of_samples=1,
            runtime_params={"foo": "bar"},
            spec_version_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            run = await response.parse()
            assert_matches_type(RunCreateResponse, run, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncDataframer) -> None:
        run = await async_client.dataframer.runs.retrieve(
            "run_id",
        )
        assert_matches_type(RunRetrieveResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.runs.with_raw_response.retrieve(
            "run_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        run = await response.parse()
        assert_matches_type(RunRetrieveResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.runs.with_streaming_response.retrieve(
            "run_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            run = await response.parse()
            assert_matches_type(RunRetrieveResponse, run, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            await async_client.dataframer.runs.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncDataframer) -> None:
        run = await async_client.dataframer.runs.update(
            "run_id",
        )
        assert_matches_type(RunUpdateResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.runs.with_raw_response.update(
            "run_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        run = await response.parse()
        assert_matches_type(RunUpdateResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.runs.with_streaming_response.update(
            "run_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            run = await response.parse()
            assert_matches_type(RunUpdateResponse, run, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            await async_client.dataframer.runs.with_raw_response.update(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncDataframer) -> None:
        run = await async_client.dataframer.runs.list()
        assert_matches_type(RunListResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.runs.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        run = await response.parse()
        assert_matches_type(RunListResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.runs.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            run = await response.parse()
            assert_matches_type(RunListResponse, run, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncDataframer) -> None:
        run = await async_client.dataframer.runs.delete(
            "run_id",
        )
        assert run is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.runs.with_raw_response.delete(
            "run_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        run = await response.parse()
        assert run is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.runs.with_streaming_response.delete(
            "run_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            run = await response.parse()
            assert run is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            await async_client.dataframer.runs.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_status(self, async_client: AsyncDataframer) -> None:
        run = await async_client.dataframer.runs.status(
            "run_id",
        )
        assert_matches_type(RunStatusResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_status(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.runs.with_raw_response.status(
            "run_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        run = await response.parse()
        assert_matches_type(RunStatusResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_status(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.runs.with_streaming_response.status(
            "run_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            run = await response.parse()
            assert_matches_type(RunStatusResponse, run, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_status(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            await async_client.dataframer.runs.with_raw_response.status(
                "",
            )
