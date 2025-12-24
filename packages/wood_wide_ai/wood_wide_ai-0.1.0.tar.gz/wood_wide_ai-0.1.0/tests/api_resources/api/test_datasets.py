# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from wood_wide_ai import WoodWideAI, AsyncWoodWideAI
from wood_wide_ai.types.api import (
    DatasetPublic,
    DatasetListResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestDatasets:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: WoodWideAI) -> None:
        dataset = client.api.datasets.retrieve(
            dataset_id="dataset_id",
        )
        assert_matches_type(DatasetPublic, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_with_all_params(self, client: WoodWideAI) -> None:
        dataset = client.api.datasets.retrieve(
            dataset_id="dataset_id",
            dataset_name="dataset_name",
        )
        assert_matches_type(DatasetPublic, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: WoodWideAI) -> None:
        response = client.api.datasets.with_raw_response.retrieve(
            dataset_id="dataset_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataset = response.parse()
        assert_matches_type(DatasetPublic, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: WoodWideAI) -> None:
        with client.api.datasets.with_streaming_response.retrieve(
            dataset_id="dataset_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataset = response.parse()
            assert_matches_type(DatasetPublic, dataset, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: WoodWideAI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `dataset_id` but received ''"):
            client.api.datasets.with_raw_response.retrieve(
                dataset_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: WoodWideAI) -> None:
        dataset = client.api.datasets.list()
        assert_matches_type(DatasetListResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: WoodWideAI) -> None:
        dataset = client.api.datasets.list(
            name="name",
        )
        assert_matches_type(DatasetListResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: WoodWideAI) -> None:
        response = client.api.datasets.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataset = response.parse()
        assert_matches_type(DatasetListResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: WoodWideAI) -> None:
        with client.api.datasets.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataset = response.parse()
            assert_matches_type(DatasetListResponse, dataset, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: WoodWideAI) -> None:
        dataset = client.api.datasets.delete(
            dataset_id="dataset_id",
        )
        assert_matches_type(object, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete_with_all_params(self, client: WoodWideAI) -> None:
        dataset = client.api.datasets.delete(
            dataset_id="dataset_id",
            dataset_name="dataset_name",
        )
        assert_matches_type(object, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: WoodWideAI) -> None:
        response = client.api.datasets.with_raw_response.delete(
            dataset_id="dataset_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataset = response.parse()
        assert_matches_type(object, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: WoodWideAI) -> None:
        with client.api.datasets.with_streaming_response.delete(
            dataset_id="dataset_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataset = response.parse()
            assert_matches_type(object, dataset, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: WoodWideAI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `dataset_id` but received ''"):
            client.api.datasets.with_raw_response.delete(
                dataset_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_upload(self, client: WoodWideAI) -> None:
        dataset = client.api.datasets.upload(
            file=b"raw file contents",
            name="name",
        )
        assert_matches_type(DatasetPublic, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_upload_with_all_params(self, client: WoodWideAI) -> None:
        dataset = client.api.datasets.upload(
            file=b"raw file contents",
            name="name",
            overwrite=True,
        )
        assert_matches_type(DatasetPublic, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_upload(self, client: WoodWideAI) -> None:
        response = client.api.datasets.with_raw_response.upload(
            file=b"raw file contents",
            name="name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataset = response.parse()
        assert_matches_type(DatasetPublic, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_upload(self, client: WoodWideAI) -> None:
        with client.api.datasets.with_streaming_response.upload(
            file=b"raw file contents",
            name="name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataset = response.parse()
            assert_matches_type(DatasetPublic, dataset, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncDatasets:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncWoodWideAI) -> None:
        dataset = await async_client.api.datasets.retrieve(
            dataset_id="dataset_id",
        )
        assert_matches_type(DatasetPublic, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_with_all_params(self, async_client: AsyncWoodWideAI) -> None:
        dataset = await async_client.api.datasets.retrieve(
            dataset_id="dataset_id",
            dataset_name="dataset_name",
        )
        assert_matches_type(DatasetPublic, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncWoodWideAI) -> None:
        response = await async_client.api.datasets.with_raw_response.retrieve(
            dataset_id="dataset_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataset = await response.parse()
        assert_matches_type(DatasetPublic, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncWoodWideAI) -> None:
        async with async_client.api.datasets.with_streaming_response.retrieve(
            dataset_id="dataset_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataset = await response.parse()
            assert_matches_type(DatasetPublic, dataset, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncWoodWideAI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `dataset_id` but received ''"):
            await async_client.api.datasets.with_raw_response.retrieve(
                dataset_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncWoodWideAI) -> None:
        dataset = await async_client.api.datasets.list()
        assert_matches_type(DatasetListResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncWoodWideAI) -> None:
        dataset = await async_client.api.datasets.list(
            name="name",
        )
        assert_matches_type(DatasetListResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncWoodWideAI) -> None:
        response = await async_client.api.datasets.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataset = await response.parse()
        assert_matches_type(DatasetListResponse, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncWoodWideAI) -> None:
        async with async_client.api.datasets.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataset = await response.parse()
            assert_matches_type(DatasetListResponse, dataset, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncWoodWideAI) -> None:
        dataset = await async_client.api.datasets.delete(
            dataset_id="dataset_id",
        )
        assert_matches_type(object, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete_with_all_params(self, async_client: AsyncWoodWideAI) -> None:
        dataset = await async_client.api.datasets.delete(
            dataset_id="dataset_id",
            dataset_name="dataset_name",
        )
        assert_matches_type(object, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncWoodWideAI) -> None:
        response = await async_client.api.datasets.with_raw_response.delete(
            dataset_id="dataset_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataset = await response.parse()
        assert_matches_type(object, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncWoodWideAI) -> None:
        async with async_client.api.datasets.with_streaming_response.delete(
            dataset_id="dataset_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataset = await response.parse()
            assert_matches_type(object, dataset, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncWoodWideAI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `dataset_id` but received ''"):
            await async_client.api.datasets.with_raw_response.delete(
                dataset_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_upload(self, async_client: AsyncWoodWideAI) -> None:
        dataset = await async_client.api.datasets.upload(
            file=b"raw file contents",
            name="name",
        )
        assert_matches_type(DatasetPublic, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_upload_with_all_params(self, async_client: AsyncWoodWideAI) -> None:
        dataset = await async_client.api.datasets.upload(
            file=b"raw file contents",
            name="name",
            overwrite=True,
        )
        assert_matches_type(DatasetPublic, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_upload(self, async_client: AsyncWoodWideAI) -> None:
        response = await async_client.api.datasets.with_raw_response.upload(
            file=b"raw file contents",
            name="name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dataset = await response.parse()
        assert_matches_type(DatasetPublic, dataset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_upload(self, async_client: AsyncWoodWideAI) -> None:
        async with async_client.api.datasets.with_streaming_response.upload(
            file=b"raw file contents",
            name="name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dataset = await response.parse()
            assert_matches_type(DatasetPublic, dataset, path=["response"])

        assert cast(Any, response.is_closed) is True
