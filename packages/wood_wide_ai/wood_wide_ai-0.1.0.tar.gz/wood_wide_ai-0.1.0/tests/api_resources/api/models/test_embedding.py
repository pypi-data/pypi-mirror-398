# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from wood_wide_ai import WoodWideAI, AsyncWoodWideAI
from wood_wide_ai.types.api import ModelPublic

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestEmbedding:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_infer(self, client: WoodWideAI) -> None:
        embedding = client.api.models.embedding.infer(
            model_id="model_id",
        )
        assert_matches_type(object, embedding, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_infer_with_all_params(self, client: WoodWideAI) -> None:
        embedding = client.api.models.embedding.infer(
            model_id="model_id",
            dataset_id="dataset_id",
            dataset_name="dataset_name",
            model_name="model_name",
            coerce_schema=True,
        )
        assert_matches_type(object, embedding, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_infer(self, client: WoodWideAI) -> None:
        response = client.api.models.embedding.with_raw_response.infer(
            model_id="model_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        embedding = response.parse()
        assert_matches_type(object, embedding, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_infer(self, client: WoodWideAI) -> None:
        with client.api.models.embedding.with_streaming_response.infer(
            model_id="model_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            embedding = response.parse()
            assert_matches_type(object, embedding, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_infer(self, client: WoodWideAI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `model_id` but received ''"):
            client.api.models.embedding.with_raw_response.infer(
                model_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_train(self, client: WoodWideAI) -> None:
        embedding = client.api.models.embedding.train(
            model_name="model_name",
        )
        assert_matches_type(ModelPublic, embedding, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_train_with_all_params(self, client: WoodWideAI) -> None:
        embedding = client.api.models.embedding.train(
            model_name="model_name",
            dataset_id="dataset_id",
            dataset_name="dataset_name",
            hyperparameters="hyperparameters",
            input_columns=["string"],
            label_column="label_column",
            overwrite=True,
        )
        assert_matches_type(ModelPublic, embedding, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_train(self, client: WoodWideAI) -> None:
        response = client.api.models.embedding.with_raw_response.train(
            model_name="model_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        embedding = response.parse()
        assert_matches_type(ModelPublic, embedding, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_train(self, client: WoodWideAI) -> None:
        with client.api.models.embedding.with_streaming_response.train(
            model_name="model_name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            embedding = response.parse()
            assert_matches_type(ModelPublic, embedding, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncEmbedding:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_infer(self, async_client: AsyncWoodWideAI) -> None:
        embedding = await async_client.api.models.embedding.infer(
            model_id="model_id",
        )
        assert_matches_type(object, embedding, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_infer_with_all_params(self, async_client: AsyncWoodWideAI) -> None:
        embedding = await async_client.api.models.embedding.infer(
            model_id="model_id",
            dataset_id="dataset_id",
            dataset_name="dataset_name",
            model_name="model_name",
            coerce_schema=True,
        )
        assert_matches_type(object, embedding, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_infer(self, async_client: AsyncWoodWideAI) -> None:
        response = await async_client.api.models.embedding.with_raw_response.infer(
            model_id="model_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        embedding = await response.parse()
        assert_matches_type(object, embedding, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_infer(self, async_client: AsyncWoodWideAI) -> None:
        async with async_client.api.models.embedding.with_streaming_response.infer(
            model_id="model_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            embedding = await response.parse()
            assert_matches_type(object, embedding, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_infer(self, async_client: AsyncWoodWideAI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `model_id` but received ''"):
            await async_client.api.models.embedding.with_raw_response.infer(
                model_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_train(self, async_client: AsyncWoodWideAI) -> None:
        embedding = await async_client.api.models.embedding.train(
            model_name="model_name",
        )
        assert_matches_type(ModelPublic, embedding, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_train_with_all_params(self, async_client: AsyncWoodWideAI) -> None:
        embedding = await async_client.api.models.embedding.train(
            model_name="model_name",
            dataset_id="dataset_id",
            dataset_name="dataset_name",
            hyperparameters="hyperparameters",
            input_columns=["string"],
            label_column="label_column",
            overwrite=True,
        )
        assert_matches_type(ModelPublic, embedding, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_train(self, async_client: AsyncWoodWideAI) -> None:
        response = await async_client.api.models.embedding.with_raw_response.train(
            model_name="model_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        embedding = await response.parse()
        assert_matches_type(ModelPublic, embedding, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_train(self, async_client: AsyncWoodWideAI) -> None:
        async with async_client.api.models.embedding.with_streaming_response.train(
            model_name="model_name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            embedding = await response.parse()
            assert_matches_type(ModelPublic, embedding, path=["response"])

        assert cast(Any, response.is_closed) is True
