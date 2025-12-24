# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from dataframer import Dataframer, AsyncDataframer
from tests.utils import assert_matches_type
from dataframer.types.dataframer import FileListResponse, FileDownloadResponse, FileGetContentResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestFiles:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Dataframer) -> None:
        file = client.dataframer.files.list()
        assert_matches_type(FileListResponse, file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Dataframer) -> None:
        response = client.dataframer.files.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        file = response.parse()
        assert_matches_type(FileListResponse, file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Dataframer) -> None:
        with client.dataframer.files.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            file = response.parse()
            assert_matches_type(FileListResponse, file, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_download(self, client: Dataframer) -> None:
        file = client.dataframer.files.download(
            "file_id",
        )
        assert_matches_type(FileDownloadResponse, file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_download(self, client: Dataframer) -> None:
        response = client.dataframer.files.with_raw_response.download(
            "file_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        file = response.parse()
        assert_matches_type(FileDownloadResponse, file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_download(self, client: Dataframer) -> None:
        with client.dataframer.files.with_streaming_response.download(
            "file_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            file = response.parse()
            assert_matches_type(FileDownloadResponse, file, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_download(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `file_id` but received ''"):
            client.dataframer.files.with_raw_response.download(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_content(self, client: Dataframer) -> None:
        file = client.dataframer.files.get_content(
            "file_id",
        )
        assert_matches_type(FileGetContentResponse, file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_content(self, client: Dataframer) -> None:
        response = client.dataframer.files.with_raw_response.get_content(
            "file_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        file = response.parse()
        assert_matches_type(FileGetContentResponse, file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_content(self, client: Dataframer) -> None:
        with client.dataframer.files.with_streaming_response.get_content(
            "file_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            file = response.parse()
            assert_matches_type(FileGetContentResponse, file, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_get_content(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `file_id` but received ''"):
            client.dataframer.files.with_raw_response.get_content(
                "",
            )


class TestAsyncFiles:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncDataframer) -> None:
        file = await async_client.dataframer.files.list()
        assert_matches_type(FileListResponse, file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.files.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        file = await response.parse()
        assert_matches_type(FileListResponse, file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.files.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            file = await response.parse()
            assert_matches_type(FileListResponse, file, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_download(self, async_client: AsyncDataframer) -> None:
        file = await async_client.dataframer.files.download(
            "file_id",
        )
        assert_matches_type(FileDownloadResponse, file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_download(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.files.with_raw_response.download(
            "file_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        file = await response.parse()
        assert_matches_type(FileDownloadResponse, file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_download(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.files.with_streaming_response.download(
            "file_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            file = await response.parse()
            assert_matches_type(FileDownloadResponse, file, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_download(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `file_id` but received ''"):
            await async_client.dataframer.files.with_raw_response.download(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_content(self, async_client: AsyncDataframer) -> None:
        file = await async_client.dataframer.files.get_content(
            "file_id",
        )
        assert_matches_type(FileGetContentResponse, file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_content(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.files.with_raw_response.get_content(
            "file_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        file = await response.parse()
        assert_matches_type(FileGetContentResponse, file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_content(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.files.with_streaming_response.get_content(
            "file_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            file = await response.parse()
            assert_matches_type(FileGetContentResponse, file, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_get_content(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `file_id` but received ''"):
            await async_client.dataframer.files.with_raw_response.get_content(
                "",
            )
