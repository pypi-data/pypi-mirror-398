# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from dataframer import Dataframer, AsyncDataframer
from tests.utils import assert_matches_type
from dataframer.types.dataframer import (
    DatasetListResponse,
    DatasetUpdateResponse,
    DatasetRetrieveResponse,
    DatasetListFilesResponse,
    DatasetListFoldersResponse,
    DatasetCreateFromZipResponse,
    DatasetCreateWithFilesResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestDatasets:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Dataframer) -> None:
        dataset = client.dataframer.datasets.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(DatasetRetrieveResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Dataframer) -> None:
        response = client.dataframer.datasets.with_raw_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataset = response.parse()
        assert_matches_type(DatasetRetrieveResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Dataframer) -> None:
        with client.dataframer.datasets.with_streaming_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataset = response.parse()
            assert_matches_type(DatasetRetrieveResponse, dataset, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `dataset_id` but received ''"):
            client.dataframer.datasets.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: Dataframer) -> None:
        dataset = client.dataframer.datasets.update(
            dataset_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(DatasetUpdateResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: Dataframer) -> None:
        dataset = client.dataframer.datasets.update(
            dataset_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            description="description",
            name="name",
        )
        assert_matches_type(DatasetUpdateResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: Dataframer) -> None:
        response = client.dataframer.datasets.with_raw_response.update(
            dataset_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataset = response.parse()
        assert_matches_type(DatasetUpdateResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: Dataframer) -> None:
        with client.dataframer.datasets.with_streaming_response.update(
            dataset_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataset = response.parse()
            assert_matches_type(DatasetUpdateResponse, dataset, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `dataset_id` but received ''"):
            client.dataframer.datasets.with_raw_response.update(
                dataset_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Dataframer) -> None:
        dataset = client.dataframer.datasets.list()
        assert_matches_type(DatasetListResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Dataframer) -> None:
        response = client.dataframer.datasets.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataset = response.parse()
        assert_matches_type(DatasetListResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Dataframer) -> None:
        with client.dataframer.datasets.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataset = response.parse()
            assert_matches_type(DatasetListResponse, dataset, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Dataframer) -> None:
        dataset = client.dataframer.datasets.delete(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert dataset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Dataframer) -> None:
        response = client.dataframer.datasets.with_raw_response.delete(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataset = response.parse()
        assert dataset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Dataframer) -> None:
        with client.dataframer.datasets.with_streaming_response.delete(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataset = response.parse()
            assert dataset is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `dataset_id` but received ''"):
            client.dataframer.datasets.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_from_zip(self, client: Dataframer) -> None:
        dataset = client.dataframer.datasets.create_from_zip(
            name="name",
            zip_file=b"raw file contents",
        )
        assert_matches_type(DatasetCreateFromZipResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_from_zip_with_all_params(self, client: Dataframer) -> None:
        dataset = client.dataframer.datasets.create_from_zip(
            name="name",
            zip_file=b"raw file contents",
            description="description",
        )
        assert_matches_type(DatasetCreateFromZipResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create_from_zip(self, client: Dataframer) -> None:
        response = client.dataframer.datasets.with_raw_response.create_from_zip(
            name="name",
            zip_file=b"raw file contents",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataset = response.parse()
        assert_matches_type(DatasetCreateFromZipResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create_from_zip(self, client: Dataframer) -> None:
        with client.dataframer.datasets.with_streaming_response.create_from_zip(
            name="name",
            zip_file=b"raw file contents",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataset = response.parse()
            assert_matches_type(DatasetCreateFromZipResponse, dataset, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_files(self, client: Dataframer) -> None:
        dataset = client.dataframer.datasets.create_with_files(
            dataset_type="SINGLE_FILE",
            name="name",
        )
        assert_matches_type(DatasetCreateWithFilesResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_files_with_all_params(self, client: Dataframer) -> None:
        dataset = client.dataframer.datasets.create_with_files(
            dataset_type="SINGLE_FILE",
            name="name",
            config_json="config_json",
            csv_headers="csv_headers",
            description="description",
            file=b"raw file contents",
            files=[b"raw file contents"],
            folder_names=["string", "string"],
        )
        assert_matches_type(DatasetCreateWithFilesResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create_with_files(self, client: Dataframer) -> None:
        response = client.dataframer.datasets.with_raw_response.create_with_files(
            dataset_type="SINGLE_FILE",
            name="name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataset = response.parse()
        assert_matches_type(DatasetCreateWithFilesResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create_with_files(self, client: Dataframer) -> None:
        with client.dataframer.datasets.with_streaming_response.create_with_files(
            dataset_type="SINGLE_FILE",
            name="name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataset = response.parse()
            assert_matches_type(DatasetCreateWithFilesResponse, dataset, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_files(self, client: Dataframer) -> None:
        dataset = client.dataframer.datasets.list_files(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(DatasetListFilesResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_files(self, client: Dataframer) -> None:
        response = client.dataframer.datasets.with_raw_response.list_files(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataset = response.parse()
        assert_matches_type(DatasetListFilesResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_files(self, client: Dataframer) -> None:
        with client.dataframer.datasets.with_streaming_response.list_files(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataset = response.parse()
            assert_matches_type(DatasetListFilesResponse, dataset, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list_files(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `dataset_id` but received ''"):
            client.dataframer.datasets.with_raw_response.list_files(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_folders(self, client: Dataframer) -> None:
        dataset = client.dataframer.datasets.list_folders(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(DatasetListFoldersResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_folders(self, client: Dataframer) -> None:
        response = client.dataframer.datasets.with_raw_response.list_folders(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataset = response.parse()
        assert_matches_type(DatasetListFoldersResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_folders(self, client: Dataframer) -> None:
        with client.dataframer.datasets.with_streaming_response.list_folders(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataset = response.parse()
            assert_matches_type(DatasetListFoldersResponse, dataset, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list_folders(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `dataset_id` but received ''"):
            client.dataframer.datasets.with_raw_response.list_folders(
                "",
            )


class TestAsyncDatasets:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncDataframer) -> None:
        dataset = await async_client.dataframer.datasets.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(DatasetRetrieveResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.datasets.with_raw_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataset = await response.parse()
        assert_matches_type(DatasetRetrieveResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.datasets.with_streaming_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataset = await response.parse()
            assert_matches_type(DatasetRetrieveResponse, dataset, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `dataset_id` but received ''"):
            await async_client.dataframer.datasets.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncDataframer) -> None:
        dataset = await async_client.dataframer.datasets.update(
            dataset_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(DatasetUpdateResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncDataframer) -> None:
        dataset = await async_client.dataframer.datasets.update(
            dataset_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            description="description",
            name="name",
        )
        assert_matches_type(DatasetUpdateResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.datasets.with_raw_response.update(
            dataset_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataset = await response.parse()
        assert_matches_type(DatasetUpdateResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.datasets.with_streaming_response.update(
            dataset_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataset = await response.parse()
            assert_matches_type(DatasetUpdateResponse, dataset, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `dataset_id` but received ''"):
            await async_client.dataframer.datasets.with_raw_response.update(
                dataset_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncDataframer) -> None:
        dataset = await async_client.dataframer.datasets.list()
        assert_matches_type(DatasetListResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.datasets.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataset = await response.parse()
        assert_matches_type(DatasetListResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.datasets.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataset = await response.parse()
            assert_matches_type(DatasetListResponse, dataset, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncDataframer) -> None:
        dataset = await async_client.dataframer.datasets.delete(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert dataset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.datasets.with_raw_response.delete(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataset = await response.parse()
        assert dataset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.datasets.with_streaming_response.delete(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataset = await response.parse()
            assert dataset is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `dataset_id` but received ''"):
            await async_client.dataframer.datasets.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_from_zip(self, async_client: AsyncDataframer) -> None:
        dataset = await async_client.dataframer.datasets.create_from_zip(
            name="name",
            zip_file=b"raw file contents",
        )
        assert_matches_type(DatasetCreateFromZipResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_from_zip_with_all_params(self, async_client: AsyncDataframer) -> None:
        dataset = await async_client.dataframer.datasets.create_from_zip(
            name="name",
            zip_file=b"raw file contents",
            description="description",
        )
        assert_matches_type(DatasetCreateFromZipResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create_from_zip(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.datasets.with_raw_response.create_from_zip(
            name="name",
            zip_file=b"raw file contents",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataset = await response.parse()
        assert_matches_type(DatasetCreateFromZipResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create_from_zip(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.datasets.with_streaming_response.create_from_zip(
            name="name",
            zip_file=b"raw file contents",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataset = await response.parse()
            assert_matches_type(DatasetCreateFromZipResponse, dataset, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_files(self, async_client: AsyncDataframer) -> None:
        dataset = await async_client.dataframer.datasets.create_with_files(
            dataset_type="SINGLE_FILE",
            name="name",
        )
        assert_matches_type(DatasetCreateWithFilesResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_files_with_all_params(self, async_client: AsyncDataframer) -> None:
        dataset = await async_client.dataframer.datasets.create_with_files(
            dataset_type="SINGLE_FILE",
            name="name",
            config_json="config_json",
            csv_headers="csv_headers",
            description="description",
            file=b"raw file contents",
            files=[b"raw file contents"],
            folder_names=["string", "string"],
        )
        assert_matches_type(DatasetCreateWithFilesResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create_with_files(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.datasets.with_raw_response.create_with_files(
            dataset_type="SINGLE_FILE",
            name="name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataset = await response.parse()
        assert_matches_type(DatasetCreateWithFilesResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create_with_files(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.datasets.with_streaming_response.create_with_files(
            dataset_type="SINGLE_FILE",
            name="name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataset = await response.parse()
            assert_matches_type(DatasetCreateWithFilesResponse, dataset, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_files(self, async_client: AsyncDataframer) -> None:
        dataset = await async_client.dataframer.datasets.list_files(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(DatasetListFilesResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_files(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.datasets.with_raw_response.list_files(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataset = await response.parse()
        assert_matches_type(DatasetListFilesResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_files(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.datasets.with_streaming_response.list_files(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataset = await response.parse()
            assert_matches_type(DatasetListFilesResponse, dataset, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list_files(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `dataset_id` but received ''"):
            await async_client.dataframer.datasets.with_raw_response.list_files(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_folders(self, async_client: AsyncDataframer) -> None:
        dataset = await async_client.dataframer.datasets.list_folders(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(DatasetListFoldersResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_folders(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.datasets.with_raw_response.list_folders(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataset = await response.parse()
        assert_matches_type(DatasetListFoldersResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_folders(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.datasets.with_streaming_response.list_folders(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataset = await response.parse()
            assert_matches_type(DatasetListFoldersResponse, dataset, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list_folders(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `dataset_id` but received ''"):
            await async_client.dataframer.datasets.with_raw_response.list_folders(
                "",
            )
