# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..._types import Body, Query, Headers, NotGiven, not_given
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.api.health_get_models_response import HealthGetModelsResponse
from ...types.api.health_check_models_response import HealthCheckModelsResponse
from ...types.api.health_retrieve_status_response import HealthRetrieveStatusResponse

__all__ = ["HealthResource", "AsyncHealthResource"]


class HealthResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> HealthResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#accessing-raw-response-data-eg-headers
        """
        return HealthResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> HealthResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#with_streaming_response
        """
        return HealthResourceWithStreamingResponse(self)

    def check_models(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HealthCheckModelsResponse:
        """
        Endpoint to check the health of various models hosted on the LiteLLM platform.
        This endpoint fetches a list of available models and checks if each one is
        operational.
        """
        return self._get(
            "/api/health/remote-models",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HealthCheckModelsResponse,
        )

    def get_models(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HealthGetModelsResponse:
        """Returns available models with model_name and api_type fields"""
        return self._get(
            "/api/health/models",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HealthGetModelsResponse,
        )

    def retrieve_status(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HealthRetrieveStatusResponse:
        """
        Consolidated health endpoint that returns status, version information, and
        service health. This combines the functionality of /app, /version, and /services
        endpoints.
        """
        return self._get(
            "/api/health/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HealthRetrieveStatusResponse,
        )


class AsyncHealthResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncHealthResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#accessing-raw-response-data-eg-headers
        """
        return AsyncHealthResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncHealthResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#with_streaming_response
        """
        return AsyncHealthResourceWithStreamingResponse(self)

    async def check_models(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HealthCheckModelsResponse:
        """
        Endpoint to check the health of various models hosted on the LiteLLM platform.
        This endpoint fetches a list of available models and checks if each one is
        operational.
        """
        return await self._get(
            "/api/health/remote-models",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HealthCheckModelsResponse,
        )

    async def get_models(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HealthGetModelsResponse:
        """Returns available models with model_name and api_type fields"""
        return await self._get(
            "/api/health/models",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HealthGetModelsResponse,
        )

    async def retrieve_status(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HealthRetrieveStatusResponse:
        """
        Consolidated health endpoint that returns status, version information, and
        service health. This combines the functionality of /app, /version, and /services
        endpoints.
        """
        return await self._get(
            "/api/health/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HealthRetrieveStatusResponse,
        )


class HealthResourceWithRawResponse:
    def __init__(self, health: HealthResource) -> None:
        self._health = health

        self.check_models = to_raw_response_wrapper(
            health.check_models,
        )
        self.get_models = to_raw_response_wrapper(
            health.get_models,
        )
        self.retrieve_status = to_raw_response_wrapper(
            health.retrieve_status,
        )


class AsyncHealthResourceWithRawResponse:
    def __init__(self, health: AsyncHealthResource) -> None:
        self._health = health

        self.check_models = async_to_raw_response_wrapper(
            health.check_models,
        )
        self.get_models = async_to_raw_response_wrapper(
            health.get_models,
        )
        self.retrieve_status = async_to_raw_response_wrapper(
            health.retrieve_status,
        )


class HealthResourceWithStreamingResponse:
    def __init__(self, health: HealthResource) -> None:
        self._health = health

        self.check_models = to_streamed_response_wrapper(
            health.check_models,
        )
        self.get_models = to_streamed_response_wrapper(
            health.get_models,
        )
        self.retrieve_status = to_streamed_response_wrapper(
            health.retrieve_status,
        )


class AsyncHealthResourceWithStreamingResponse:
    def __init__(self, health: AsyncHealthResource) -> None:
        self._health = health

        self.check_models = async_to_streamed_response_wrapper(
            health.check_models,
        )
        self.get_models = async_to_streamed_response_wrapper(
            health.get_models,
        )
        self.retrieve_status = async_to_streamed_response_wrapper(
            health.retrieve_status,
        )
