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
from ...types.api.notification_get_schemas_response import NotificationGetSchemasResponse

__all__ = ["NotificationsResource", "AsyncNotificationsResource"]


class NotificationsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> NotificationsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#accessing-raw-response-data-eg-headers
        """
        return NotificationsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> NotificationsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#with_streaming_response
        """
        return NotificationsResourceWithStreamingResponse(self)

    def get_schemas(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> NotificationGetSchemasResponse:
        """Expose WebSocket message types in the OpenAPI schema.

        Frontend can autogenerate
        TypeScript types from the OpenAPI schema components.

        This endpoint returns an empty list at runtime but includes all WebSocket
        message types in the OpenAPI schema components for type generation purposes.

        All message types are available in the OpenAPI schema at:
        components.schemas.TaskUpdateMessage components.schemas.AuthResultMessage
        components.schemas.NotificationMessage etc.
        """
        return self._get(
            "/api/notifications/ws-schemas",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NotificationGetSchemasResponse,
        )


class AsyncNotificationsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncNotificationsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#accessing-raw-response-data-eg-headers
        """
        return AsyncNotificationsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncNotificationsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#with_streaming_response
        """
        return AsyncNotificationsResourceWithStreamingResponse(self)

    async def get_schemas(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> NotificationGetSchemasResponse:
        """Expose WebSocket message types in the OpenAPI schema.

        Frontend can autogenerate
        TypeScript types from the OpenAPI schema components.

        This endpoint returns an empty list at runtime but includes all WebSocket
        message types in the OpenAPI schema components for type generation purposes.

        All message types are available in the OpenAPI schema at:
        components.schemas.TaskUpdateMessage components.schemas.AuthResultMessage
        components.schemas.NotificationMessage etc.
        """
        return await self._get(
            "/api/notifications/ws-schemas",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NotificationGetSchemasResponse,
        )


class NotificationsResourceWithRawResponse:
    def __init__(self, notifications: NotificationsResource) -> None:
        self._notifications = notifications

        self.get_schemas = to_raw_response_wrapper(
            notifications.get_schemas,
        )


class AsyncNotificationsResourceWithRawResponse:
    def __init__(self, notifications: AsyncNotificationsResource) -> None:
        self._notifications = notifications

        self.get_schemas = async_to_raw_response_wrapper(
            notifications.get_schemas,
        )


class NotificationsResourceWithStreamingResponse:
    def __init__(self, notifications: NotificationsResource) -> None:
        self._notifications = notifications

        self.get_schemas = to_streamed_response_wrapper(
            notifications.get_schemas,
        )


class AsyncNotificationsResourceWithStreamingResponse:
    def __init__(self, notifications: AsyncNotificationsResource) -> None:
        self._notifications = notifications

        self.get_schemas = async_to_streamed_response_wrapper(
            notifications.get_schemas,
        )
