# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import httpx
import pytest
from respx import MockRouter

from dataframer import Dataframer, AsyncDataframer
from tests.utils import assert_matches_type
from dataframer._response import (
    BinaryAPIResponse,
    AsyncBinaryAPIResponse,
    StreamedBinaryAPIResponse,
    AsyncStreamedBinaryAPIResponse,
)
from dataframer.types.dataframer.runs import (
    GeneratedFileListResponse,
    GeneratedFileDownloadResponse,
    GeneratedFileGetContentResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestGeneratedFiles:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Dataframer) -> None:
        generated_file = client.dataframer.runs.generated_files.list(
            "run_id",
        )
        assert_matches_type(GeneratedFileListResponse, generated_file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Dataframer) -> None:
        response = client.dataframer.runs.generated_files.with_raw_response.list(
            "run_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        generated_file = response.parse()
        assert_matches_type(GeneratedFileListResponse, generated_file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Dataframer) -> None:
        with client.dataframer.runs.generated_files.with_streaming_response.list(
            "run_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            generated_file = response.parse()
            assert_matches_type(GeneratedFileListResponse, generated_file, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            client.dataframer.runs.generated_files.with_raw_response.list(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_download(self, client: Dataframer) -> None:
        generated_file = client.dataframer.runs.generated_files.download(
            file_id="file_id",
            run_id="run_id",
        )
        assert_matches_type(GeneratedFileDownloadResponse, generated_file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_download(self, client: Dataframer) -> None:
        response = client.dataframer.runs.generated_files.with_raw_response.download(
            file_id="file_id",
            run_id="run_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        generated_file = response.parse()
        assert_matches_type(GeneratedFileDownloadResponse, generated_file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_download(self, client: Dataframer) -> None:
        with client.dataframer.runs.generated_files.with_streaming_response.download(
            file_id="file_id",
            run_id="run_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            generated_file = response.parse()
            assert_matches_type(GeneratedFileDownloadResponse, generated_file, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_download(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            client.dataframer.runs.generated_files.with_raw_response.download(
                file_id="file_id",
                run_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `file_id` but received ''"):
            client.dataframer.runs.generated_files.with_raw_response.download(
                file_id="",
                run_id="run_id",
            )

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_method_download_all(self, client: Dataframer, respx_mock: MockRouter) -> None:
        respx_mock.get("/api/dataframer/runs/run_id/generated-files/download-all/").mock(
            return_value=httpx.Response(200, json={"foo": "bar"})
        )
        generated_file = client.dataframer.runs.generated_files.download_all(
            "run_id",
        )
        assert generated_file.is_closed
        assert generated_file.json() == {"foo": "bar"}
        assert cast(Any, generated_file.is_closed) is True
        assert isinstance(generated_file, BinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_raw_response_download_all(self, client: Dataframer, respx_mock: MockRouter) -> None:
        respx_mock.get("/api/dataframer/runs/run_id/generated-files/download-all/").mock(
            return_value=httpx.Response(200, json={"foo": "bar"})
        )

        generated_file = client.dataframer.runs.generated_files.with_raw_response.download_all(
            "run_id",
        )

        assert generated_file.is_closed is True
        assert generated_file.http_request.headers.get("X-Stainless-Lang") == "python"
        assert generated_file.json() == {"foo": "bar"}
        assert isinstance(generated_file, BinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_streaming_response_download_all(self, client: Dataframer, respx_mock: MockRouter) -> None:
        respx_mock.get("/api/dataframer/runs/run_id/generated-files/download-all/").mock(
            return_value=httpx.Response(200, json={"foo": "bar"})
        )
        with client.dataframer.runs.generated_files.with_streaming_response.download_all(
            "run_id",
        ) as generated_file:
            assert not generated_file.is_closed
            assert generated_file.http_request.headers.get("X-Stainless-Lang") == "python"

            assert generated_file.json() == {"foo": "bar"}
            assert cast(Any, generated_file.is_closed) is True
            assert isinstance(generated_file, StreamedBinaryAPIResponse)

        assert cast(Any, generated_file.is_closed) is True

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_path_params_download_all(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            client.dataframer.runs.generated_files.with_raw_response.download_all(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_content(self, client: Dataframer) -> None:
        generated_file = client.dataframer.runs.generated_files.get_content(
            file_id="file_id",
            run_id="run_id",
        )
        assert_matches_type(GeneratedFileGetContentResponse, generated_file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_content(self, client: Dataframer) -> None:
        response = client.dataframer.runs.generated_files.with_raw_response.get_content(
            file_id="file_id",
            run_id="run_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        generated_file = response.parse()
        assert_matches_type(GeneratedFileGetContentResponse, generated_file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_content(self, client: Dataframer) -> None:
        with client.dataframer.runs.generated_files.with_streaming_response.get_content(
            file_id="file_id",
            run_id="run_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            generated_file = response.parse()
            assert_matches_type(GeneratedFileGetContentResponse, generated_file, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_get_content(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            client.dataframer.runs.generated_files.with_raw_response.get_content(
                file_id="file_id",
                run_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `file_id` but received ''"):
            client.dataframer.runs.generated_files.with_raw_response.get_content(
                file_id="",
                run_id="run_id",
            )


class TestAsyncGeneratedFiles:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncDataframer) -> None:
        generated_file = await async_client.dataframer.runs.generated_files.list(
            "run_id",
        )
        assert_matches_type(GeneratedFileListResponse, generated_file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.runs.generated_files.with_raw_response.list(
            "run_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        generated_file = await response.parse()
        assert_matches_type(GeneratedFileListResponse, generated_file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.runs.generated_files.with_streaming_response.list(
            "run_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            generated_file = await response.parse()
            assert_matches_type(GeneratedFileListResponse, generated_file, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            await async_client.dataframer.runs.generated_files.with_raw_response.list(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_download(self, async_client: AsyncDataframer) -> None:
        generated_file = await async_client.dataframer.runs.generated_files.download(
            file_id="file_id",
            run_id="run_id",
        )
        assert_matches_type(GeneratedFileDownloadResponse, generated_file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_download(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.runs.generated_files.with_raw_response.download(
            file_id="file_id",
            run_id="run_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        generated_file = await response.parse()
        assert_matches_type(GeneratedFileDownloadResponse, generated_file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_download(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.runs.generated_files.with_streaming_response.download(
            file_id="file_id",
            run_id="run_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            generated_file = await response.parse()
            assert_matches_type(GeneratedFileDownloadResponse, generated_file, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_download(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            await async_client.dataframer.runs.generated_files.with_raw_response.download(
                file_id="file_id",
                run_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `file_id` but received ''"):
            await async_client.dataframer.runs.generated_files.with_raw_response.download(
                file_id="",
                run_id="run_id",
            )

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_method_download_all(self, async_client: AsyncDataframer, respx_mock: MockRouter) -> None:
        respx_mock.get("/api/dataframer/runs/run_id/generated-files/download-all/").mock(
            return_value=httpx.Response(200, json={"foo": "bar"})
        )
        generated_file = await async_client.dataframer.runs.generated_files.download_all(
            "run_id",
        )
        assert generated_file.is_closed
        assert await generated_file.json() == {"foo": "bar"}
        assert cast(Any, generated_file.is_closed) is True
        assert isinstance(generated_file, AsyncBinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_raw_response_download_all(self, async_client: AsyncDataframer, respx_mock: MockRouter) -> None:
        respx_mock.get("/api/dataframer/runs/run_id/generated-files/download-all/").mock(
            return_value=httpx.Response(200, json={"foo": "bar"})
        )

        generated_file = await async_client.dataframer.runs.generated_files.with_raw_response.download_all(
            "run_id",
        )

        assert generated_file.is_closed is True
        assert generated_file.http_request.headers.get("X-Stainless-Lang") == "python"
        assert await generated_file.json() == {"foo": "bar"}
        assert isinstance(generated_file, AsyncBinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_streaming_response_download_all(self, async_client: AsyncDataframer, respx_mock: MockRouter) -> None:
        respx_mock.get("/api/dataframer/runs/run_id/generated-files/download-all/").mock(
            return_value=httpx.Response(200, json={"foo": "bar"})
        )
        async with async_client.dataframer.runs.generated_files.with_streaming_response.download_all(
            "run_id",
        ) as generated_file:
            assert not generated_file.is_closed
            assert generated_file.http_request.headers.get("X-Stainless-Lang") == "python"

            assert await generated_file.json() == {"foo": "bar"}
            assert cast(Any, generated_file.is_closed) is True
            assert isinstance(generated_file, AsyncStreamedBinaryAPIResponse)

        assert cast(Any, generated_file.is_closed) is True

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_path_params_download_all(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            await async_client.dataframer.runs.generated_files.with_raw_response.download_all(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_content(self, async_client: AsyncDataframer) -> None:
        generated_file = await async_client.dataframer.runs.generated_files.get_content(
            file_id="file_id",
            run_id="run_id",
        )
        assert_matches_type(GeneratedFileGetContentResponse, generated_file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_content(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.runs.generated_files.with_raw_response.get_content(
            file_id="file_id",
            run_id="run_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        generated_file = await response.parse()
        assert_matches_type(GeneratedFileGetContentResponse, generated_file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_content(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.runs.generated_files.with_streaming_response.get_content(
            file_id="file_id",
            run_id="run_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            generated_file = await response.parse()
            assert_matches_type(GeneratedFileGetContentResponse, generated_file, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_get_content(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            await async_client.dataframer.runs.generated_files.with_raw_response.get_content(
                file_id="file_id",
                run_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `file_id` but received ''"):
            await async_client.dataframer.runs.generated_files.with_raw_response.get_content(
                file_id="",
                run_id="run_id",
            )
