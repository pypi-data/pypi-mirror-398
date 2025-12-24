# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from dataframer import Dataframer, AsyncDataframer
from tests.utils import assert_matches_type
from dataframer.types import SpecVersion
from dataframer.types.dataframer.specs import VersionListResponse, VersionCreateResponse, VersionUpdateResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestVersions:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Dataframer) -> None:
        version = client.dataframer.specs.versions.create(
            "spec_id",
        )
        assert_matches_type(VersionCreateResponse, version, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Dataframer) -> None:
        response = client.dataframer.specs.versions.with_raw_response.create(
            "spec_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        version = response.parse()
        assert_matches_type(VersionCreateResponse, version, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Dataframer) -> None:
        with client.dataframer.specs.versions.with_streaming_response.create(
            "spec_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            version = response.parse()
            assert_matches_type(VersionCreateResponse, version, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_create(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `spec_id` but received ''"):
            client.dataframer.specs.versions.with_raw_response.create(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Dataframer) -> None:
        version = client.dataframer.specs.versions.retrieve(
            version_id="version_id",
            spec_id="spec_id",
        )
        assert_matches_type(SpecVersion, version, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Dataframer) -> None:
        response = client.dataframer.specs.versions.with_raw_response.retrieve(
            version_id="version_id",
            spec_id="spec_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        version = response.parse()
        assert_matches_type(SpecVersion, version, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Dataframer) -> None:
        with client.dataframer.specs.versions.with_streaming_response.retrieve(
            version_id="version_id",
            spec_id="spec_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            version = response.parse()
            assert_matches_type(SpecVersion, version, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `spec_id` but received ''"):
            client.dataframer.specs.versions.with_raw_response.retrieve(
                version_id="version_id",
                spec_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `version_id` but received ''"):
            client.dataframer.specs.versions.with_raw_response.retrieve(
                version_id="",
                spec_id="spec_id",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: Dataframer) -> None:
        version = client.dataframer.specs.versions.update(
            version_id="version_id",
            spec_id="spec_id",
        )
        assert_matches_type(VersionUpdateResponse, version, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: Dataframer) -> None:
        response = client.dataframer.specs.versions.with_raw_response.update(
            version_id="version_id",
            spec_id="spec_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        version = response.parse()
        assert_matches_type(VersionUpdateResponse, version, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: Dataframer) -> None:
        with client.dataframer.specs.versions.with_streaming_response.update(
            version_id="version_id",
            spec_id="spec_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            version = response.parse()
            assert_matches_type(VersionUpdateResponse, version, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `spec_id` but received ''"):
            client.dataframer.specs.versions.with_raw_response.update(
                version_id="version_id",
                spec_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `version_id` but received ''"):
            client.dataframer.specs.versions.with_raw_response.update(
                version_id="",
                spec_id="spec_id",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Dataframer) -> None:
        version = client.dataframer.specs.versions.list(
            "spec_id",
        )
        assert_matches_type(VersionListResponse, version, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Dataframer) -> None:
        response = client.dataframer.specs.versions.with_raw_response.list(
            "spec_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        version = response.parse()
        assert_matches_type(VersionListResponse, version, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Dataframer) -> None:
        with client.dataframer.specs.versions.with_streaming_response.list(
            "spec_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            version = response.parse()
            assert_matches_type(VersionListResponse, version, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `spec_id` but received ''"):
            client.dataframer.specs.versions.with_raw_response.list(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Dataframer) -> None:
        version = client.dataframer.specs.versions.delete(
            version_id="version_id",
            spec_id="spec_id",
        )
        assert version is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Dataframer) -> None:
        response = client.dataframer.specs.versions.with_raw_response.delete(
            version_id="version_id",
            spec_id="spec_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        version = response.parse()
        assert version is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Dataframer) -> None:
        with client.dataframer.specs.versions.with_streaming_response.delete(
            version_id="version_id",
            spec_id="spec_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            version = response.parse()
            assert version is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: Dataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `spec_id` but received ''"):
            client.dataframer.specs.versions.with_raw_response.delete(
                version_id="version_id",
                spec_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `version_id` but received ''"):
            client.dataframer.specs.versions.with_raw_response.delete(
                version_id="",
                spec_id="spec_id",
            )


class TestAsyncVersions:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncDataframer) -> None:
        version = await async_client.dataframer.specs.versions.create(
            "spec_id",
        )
        assert_matches_type(VersionCreateResponse, version, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.specs.versions.with_raw_response.create(
            "spec_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        version = await response.parse()
        assert_matches_type(VersionCreateResponse, version, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.specs.versions.with_streaming_response.create(
            "spec_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            version = await response.parse()
            assert_matches_type(VersionCreateResponse, version, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_create(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `spec_id` but received ''"):
            await async_client.dataframer.specs.versions.with_raw_response.create(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncDataframer) -> None:
        version = await async_client.dataframer.specs.versions.retrieve(
            version_id="version_id",
            spec_id="spec_id",
        )
        assert_matches_type(SpecVersion, version, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.specs.versions.with_raw_response.retrieve(
            version_id="version_id",
            spec_id="spec_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        version = await response.parse()
        assert_matches_type(SpecVersion, version, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.specs.versions.with_streaming_response.retrieve(
            version_id="version_id",
            spec_id="spec_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            version = await response.parse()
            assert_matches_type(SpecVersion, version, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `spec_id` but received ''"):
            await async_client.dataframer.specs.versions.with_raw_response.retrieve(
                version_id="version_id",
                spec_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `version_id` but received ''"):
            await async_client.dataframer.specs.versions.with_raw_response.retrieve(
                version_id="",
                spec_id="spec_id",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncDataframer) -> None:
        version = await async_client.dataframer.specs.versions.update(
            version_id="version_id",
            spec_id="spec_id",
        )
        assert_matches_type(VersionUpdateResponse, version, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.specs.versions.with_raw_response.update(
            version_id="version_id",
            spec_id="spec_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        version = await response.parse()
        assert_matches_type(VersionUpdateResponse, version, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.specs.versions.with_streaming_response.update(
            version_id="version_id",
            spec_id="spec_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            version = await response.parse()
            assert_matches_type(VersionUpdateResponse, version, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `spec_id` but received ''"):
            await async_client.dataframer.specs.versions.with_raw_response.update(
                version_id="version_id",
                spec_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `version_id` but received ''"):
            await async_client.dataframer.specs.versions.with_raw_response.update(
                version_id="",
                spec_id="spec_id",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncDataframer) -> None:
        version = await async_client.dataframer.specs.versions.list(
            "spec_id",
        )
        assert_matches_type(VersionListResponse, version, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.specs.versions.with_raw_response.list(
            "spec_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        version = await response.parse()
        assert_matches_type(VersionListResponse, version, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.specs.versions.with_streaming_response.list(
            "spec_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            version = await response.parse()
            assert_matches_type(VersionListResponse, version, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `spec_id` but received ''"):
            await async_client.dataframer.specs.versions.with_raw_response.list(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncDataframer) -> None:
        version = await async_client.dataframer.specs.versions.delete(
            version_id="version_id",
            spec_id="spec_id",
        )
        assert version is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncDataframer) -> None:
        response = await async_client.dataframer.specs.versions.with_raw_response.delete(
            version_id="version_id",
            spec_id="spec_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        version = await response.parse()
        assert version is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncDataframer) -> None:
        async with async_client.dataframer.specs.versions.with_streaming_response.delete(
            version_id="version_id",
            spec_id="spec_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            version = await response.parse()
            assert version is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncDataframer) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `spec_id` but received ''"):
            await async_client.dataframer.specs.versions.with_raw_response.delete(
                version_id="version_id",
                spec_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `version_id` but received ''"):
            await async_client.dataframer.specs.versions.with_raw_response.delete(
                version_id="",
                spec_id="spec_id",
            )
