# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ...._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from ...._utils import maybe_transform, async_maybe_transform
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.api.models import anomaly_infer_params, anomaly_train_params
from ....types.api.model_public import ModelPublic

__all__ = ["AnomalyResource", "AsyncAnomalyResource"]


class AnomalyResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AnomalyResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Wood-Wide-AI/wwai-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AnomalyResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AnomalyResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Wood-Wide-AI/wwai-python-sdk#with_streaming_response
        """
        return AnomalyResourceWithStreamingResponse(self)

    def infer(
        self,
        model_id: str,
        *,
        dataset_id: Optional[str] | Omit = omit,
        dataset_name: Optional[str] | Omit = omit,
        model_name: Optional[str] | Omit = omit,
        coerce_schema: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Detects anomalies in the input dataset using a trained anomaly detection model.
        The model must be in COMPLETE status. Returns an anomaly score or flag for each
        instance. By default, attempts to coerce the given dataset into the input schema
        required by the model (e.g., adding missing required columns and populating them
        with null values). Set coerce_schema=False to prevent schema coercion and
        enforce strict validation. When coerce_schema=False, the system specifically
        expects that the required input columns associated with the model are a subset
        of the columns of the dataset and that the types match.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not model_id:
            raise ValueError(f"Expected a non-empty value for `model_id` but received {model_id!r}")
        return self._post(
            f"/api/models/anomaly/{model_id}/infer",
            body=maybe_transform({"coerce_schema": coerce_schema}, anomaly_infer_params.AnomalyInferParams),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "dataset_id": dataset_id,
                        "dataset_name": dataset_name,
                        "model_name": model_name,
                    },
                    anomaly_infer_params.AnomalyInferParams,
                ),
            ),
            cast_to=object,
        )

    def train(
        self,
        *,
        model_name: str,
        dataset_id: Optional[str] | Omit = omit,
        dataset_name: Optional[str] | Omit = omit,
        hyperparameters: Optional[str] | Omit = omit,
        input_columns: Optional[SequenceNotStr[str]] | Omit = omit,
        overwrite: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ModelPublic:
        """Initiates training for an anomaly detection model.

        This is an asynchronous
        operation. Returns a model ID with PENDING status. Use GET /models/{model_id} to
        monitor progress. Once COMPLETE, inference is available via
        /models/anomaly/{model_id}/infer.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/models/anomaly/train",
            body=maybe_transform(
                {
                    "model_name": model_name,
                    "hyperparameters": hyperparameters,
                    "input_columns": input_columns,
                    "overwrite": overwrite,
                },
                anomaly_train_params.AnomalyTrainParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "dataset_id": dataset_id,
                        "dataset_name": dataset_name,
                    },
                    anomaly_train_params.AnomalyTrainParams,
                ),
            ),
            cast_to=ModelPublic,
        )


class AsyncAnomalyResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncAnomalyResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Wood-Wide-AI/wwai-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncAnomalyResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncAnomalyResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Wood-Wide-AI/wwai-python-sdk#with_streaming_response
        """
        return AsyncAnomalyResourceWithStreamingResponse(self)

    async def infer(
        self,
        model_id: str,
        *,
        dataset_id: Optional[str] | Omit = omit,
        dataset_name: Optional[str] | Omit = omit,
        model_name: Optional[str] | Omit = omit,
        coerce_schema: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Detects anomalies in the input dataset using a trained anomaly detection model.
        The model must be in COMPLETE status. Returns an anomaly score or flag for each
        instance. By default, attempts to coerce the given dataset into the input schema
        required by the model (e.g., adding missing required columns and populating them
        with null values). Set coerce_schema=False to prevent schema coercion and
        enforce strict validation. When coerce_schema=False, the system specifically
        expects that the required input columns associated with the model are a subset
        of the columns of the dataset and that the types match.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not model_id:
            raise ValueError(f"Expected a non-empty value for `model_id` but received {model_id!r}")
        return await self._post(
            f"/api/models/anomaly/{model_id}/infer",
            body=await async_maybe_transform({"coerce_schema": coerce_schema}, anomaly_infer_params.AnomalyInferParams),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "dataset_id": dataset_id,
                        "dataset_name": dataset_name,
                        "model_name": model_name,
                    },
                    anomaly_infer_params.AnomalyInferParams,
                ),
            ),
            cast_to=object,
        )

    async def train(
        self,
        *,
        model_name: str,
        dataset_id: Optional[str] | Omit = omit,
        dataset_name: Optional[str] | Omit = omit,
        hyperparameters: Optional[str] | Omit = omit,
        input_columns: Optional[SequenceNotStr[str]] | Omit = omit,
        overwrite: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ModelPublic:
        """Initiates training for an anomaly detection model.

        This is an asynchronous
        operation. Returns a model ID with PENDING status. Use GET /models/{model_id} to
        monitor progress. Once COMPLETE, inference is available via
        /models/anomaly/{model_id}/infer.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/models/anomaly/train",
            body=await async_maybe_transform(
                {
                    "model_name": model_name,
                    "hyperparameters": hyperparameters,
                    "input_columns": input_columns,
                    "overwrite": overwrite,
                },
                anomaly_train_params.AnomalyTrainParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "dataset_id": dataset_id,
                        "dataset_name": dataset_name,
                    },
                    anomaly_train_params.AnomalyTrainParams,
                ),
            ),
            cast_to=ModelPublic,
        )


class AnomalyResourceWithRawResponse:
    def __init__(self, anomaly: AnomalyResource) -> None:
        self._anomaly = anomaly

        self.infer = to_raw_response_wrapper(
            anomaly.infer,
        )
        self.train = to_raw_response_wrapper(
            anomaly.train,
        )


class AsyncAnomalyResourceWithRawResponse:
    def __init__(self, anomaly: AsyncAnomalyResource) -> None:
        self._anomaly = anomaly

        self.infer = async_to_raw_response_wrapper(
            anomaly.infer,
        )
        self.train = async_to_raw_response_wrapper(
            anomaly.train,
        )


class AnomalyResourceWithStreamingResponse:
    def __init__(self, anomaly: AnomalyResource) -> None:
        self._anomaly = anomaly

        self.infer = to_streamed_response_wrapper(
            anomaly.infer,
        )
        self.train = to_streamed_response_wrapper(
            anomaly.train,
        )


class AsyncAnomalyResourceWithStreamingResponse:
    def __init__(self, anomaly: AsyncAnomalyResource) -> None:
        self._anomaly = anomaly

        self.infer = async_to_streamed_response_wrapper(
            anomaly.infer,
        )
        self.train = async_to_streamed_response_wrapper(
            anomaly.train,
        )
