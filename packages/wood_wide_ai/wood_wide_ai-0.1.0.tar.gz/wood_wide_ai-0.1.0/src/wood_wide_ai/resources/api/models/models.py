# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from .anomaly import (
    AnomalyResource,
    AsyncAnomalyResource,
    AnomalyResourceWithRawResponse,
    AsyncAnomalyResourceWithRawResponse,
    AnomalyResourceWithStreamingResponse,
    AsyncAnomalyResourceWithStreamingResponse,
)
from ...._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ...._utils import maybe_transform, async_maybe_transform
from .embedding import (
    EmbeddingResource,
    AsyncEmbeddingResource,
    EmbeddingResourceWithRawResponse,
    AsyncEmbeddingResourceWithRawResponse,
    EmbeddingResourceWithStreamingResponse,
    AsyncEmbeddingResourceWithStreamingResponse,
)
from ...._compat import cached_property
from .clustering import (
    ClusteringResource,
    AsyncClusteringResource,
    ClusteringResourceWithRawResponse,
    AsyncClusteringResourceWithRawResponse,
    ClusteringResourceWithStreamingResponse,
    AsyncClusteringResourceWithStreamingResponse,
)
from .prediction import (
    PredictionResource,
    AsyncPredictionResource,
    PredictionResourceWithRawResponse,
    AsyncPredictionResourceWithRawResponse,
    PredictionResourceWithStreamingResponse,
    AsyncPredictionResourceWithStreamingResponse,
)
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ....types.api import model_retrieve_params
from ...._base_client import make_request_options
from ....types.api.model_public import ModelPublic
from ....types.api.model_list_response import ModelListResponse

__all__ = ["ModelsResource", "AsyncModelsResource"]


class ModelsResource(SyncAPIResource):
    @cached_property
    def prediction(self) -> PredictionResource:
        return PredictionResource(self._client)

    @cached_property
    def clustering(self) -> ClusteringResource:
        return ClusteringResource(self._client)

    @cached_property
    def anomaly(self) -> AnomalyResource:
        return AnomalyResource(self._client)

    @cached_property
    def embedding(self) -> EmbeddingResource:
        return EmbeddingResource(self._client)

    @cached_property
    def with_raw_response(self) -> ModelsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Wood-Wide-AI/wwai-python-sdk#accessing-raw-response-data-eg-headers
        """
        return ModelsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ModelsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Wood-Wide-AI/wwai-python-sdk#with_streaming_response
        """
        return ModelsResourceWithStreamingResponse(self)

    def retrieve(
        self,
        model_id: str,
        *,
        model_name: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ModelPublic:
        """Retrieves detailed information for a specific model by its ID.

        Fails if the
        model is not found or does not belong to the user.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not model_id:
            raise ValueError(f"Expected a non-empty value for `model_id` but received {model_id!r}")
        return self._get(
            f"/api/models/{model_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"model_name": model_name}, model_retrieve_params.ModelRetrieveParams),
            ),
            cast_to=ModelPublic,
        )

    def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ModelListResponse:
        """Retrieves a list of all models associated with the current user.

        Returns model
        metadata including ID, type, status, and creation time.
        """
        return self._get(
            "/api/models",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ModelListResponse,
        )


class AsyncModelsResource(AsyncAPIResource):
    @cached_property
    def prediction(self) -> AsyncPredictionResource:
        return AsyncPredictionResource(self._client)

    @cached_property
    def clustering(self) -> AsyncClusteringResource:
        return AsyncClusteringResource(self._client)

    @cached_property
    def anomaly(self) -> AsyncAnomalyResource:
        return AsyncAnomalyResource(self._client)

    @cached_property
    def embedding(self) -> AsyncEmbeddingResource:
        return AsyncEmbeddingResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncModelsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Wood-Wide-AI/wwai-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncModelsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncModelsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Wood-Wide-AI/wwai-python-sdk#with_streaming_response
        """
        return AsyncModelsResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        model_id: str,
        *,
        model_name: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ModelPublic:
        """Retrieves detailed information for a specific model by its ID.

        Fails if the
        model is not found or does not belong to the user.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not model_id:
            raise ValueError(f"Expected a non-empty value for `model_id` but received {model_id!r}")
        return await self._get(
            f"/api/models/{model_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"model_name": model_name}, model_retrieve_params.ModelRetrieveParams
                ),
            ),
            cast_to=ModelPublic,
        )

    async def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ModelListResponse:
        """Retrieves a list of all models associated with the current user.

        Returns model
        metadata including ID, type, status, and creation time.
        """
        return await self._get(
            "/api/models",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ModelListResponse,
        )


class ModelsResourceWithRawResponse:
    def __init__(self, models: ModelsResource) -> None:
        self._models = models

        self.retrieve = to_raw_response_wrapper(
            models.retrieve,
        )
        self.list = to_raw_response_wrapper(
            models.list,
        )

    @cached_property
    def prediction(self) -> PredictionResourceWithRawResponse:
        return PredictionResourceWithRawResponse(self._models.prediction)

    @cached_property
    def clustering(self) -> ClusteringResourceWithRawResponse:
        return ClusteringResourceWithRawResponse(self._models.clustering)

    @cached_property
    def anomaly(self) -> AnomalyResourceWithRawResponse:
        return AnomalyResourceWithRawResponse(self._models.anomaly)

    @cached_property
    def embedding(self) -> EmbeddingResourceWithRawResponse:
        return EmbeddingResourceWithRawResponse(self._models.embedding)


class AsyncModelsResourceWithRawResponse:
    def __init__(self, models: AsyncModelsResource) -> None:
        self._models = models

        self.retrieve = async_to_raw_response_wrapper(
            models.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            models.list,
        )

    @cached_property
    def prediction(self) -> AsyncPredictionResourceWithRawResponse:
        return AsyncPredictionResourceWithRawResponse(self._models.prediction)

    @cached_property
    def clustering(self) -> AsyncClusteringResourceWithRawResponse:
        return AsyncClusteringResourceWithRawResponse(self._models.clustering)

    @cached_property
    def anomaly(self) -> AsyncAnomalyResourceWithRawResponse:
        return AsyncAnomalyResourceWithRawResponse(self._models.anomaly)

    @cached_property
    def embedding(self) -> AsyncEmbeddingResourceWithRawResponse:
        return AsyncEmbeddingResourceWithRawResponse(self._models.embedding)


class ModelsResourceWithStreamingResponse:
    def __init__(self, models: ModelsResource) -> None:
        self._models = models

        self.retrieve = to_streamed_response_wrapper(
            models.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            models.list,
        )

    @cached_property
    def prediction(self) -> PredictionResourceWithStreamingResponse:
        return PredictionResourceWithStreamingResponse(self._models.prediction)

    @cached_property
    def clustering(self) -> ClusteringResourceWithStreamingResponse:
        return ClusteringResourceWithStreamingResponse(self._models.clustering)

    @cached_property
    def anomaly(self) -> AnomalyResourceWithStreamingResponse:
        return AnomalyResourceWithStreamingResponse(self._models.anomaly)

    @cached_property
    def embedding(self) -> EmbeddingResourceWithStreamingResponse:
        return EmbeddingResourceWithStreamingResponse(self._models.embedding)


class AsyncModelsResourceWithStreamingResponse:
    def __init__(self, models: AsyncModelsResource) -> None:
        self._models = models

        self.retrieve = async_to_streamed_response_wrapper(
            models.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            models.list,
        )

    @cached_property
    def prediction(self) -> AsyncPredictionResourceWithStreamingResponse:
        return AsyncPredictionResourceWithStreamingResponse(self._models.prediction)

    @cached_property
    def clustering(self) -> AsyncClusteringResourceWithStreamingResponse:
        return AsyncClusteringResourceWithStreamingResponse(self._models.clustering)

    @cached_property
    def anomaly(self) -> AsyncAnomalyResourceWithStreamingResponse:
        return AsyncAnomalyResourceWithStreamingResponse(self._models.anomaly)

    @cached_property
    def embedding(self) -> AsyncEmbeddingResourceWithStreamingResponse:
        return AsyncEmbeddingResourceWithStreamingResponse(self._models.embedding)
