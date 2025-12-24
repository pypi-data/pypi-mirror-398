# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ... import _resource
from .tag import (
    TagResource,
    AsyncTagResource,
    TagResourceWithRawResponse,
    AsyncTagResourceWithRawResponse,
    TagResourceWithStreamingResponse,
    AsyncTagResourceWithStreamingResponse,
)
from .health import (
    HealthResource,
    AsyncHealthResource,
    HealthResourceWithRawResponse,
    AsyncHealthResourceWithRawResponse,
    HealthResourceWithStreamingResponse,
    AsyncHealthResourceWithStreamingResponse,
)
from .configs import (
    ConfigsResource,
    AsyncConfigsResource,
    ConfigsResourceWithRawResponse,
    AsyncConfigsResourceWithRawResponse,
    ConfigsResourceWithStreamingResponse,
    AsyncConfigsResourceWithStreamingResponse,
)
from ..._types import Body, Query, Headers, NotGiven, not_given
from ..._compat import cached_property
from .assistant import (
    AssistantResource,
    AsyncAssistantResource,
    AssistantResourceWithRawResponse,
    AsyncAssistantResourceWithRawResponse,
    AssistantResourceWithStreamingResponse,
    AsyncAssistantResourceWithStreamingResponse,
)
from .user.user import (
    UserResource,
    AsyncUserResource,
    UserResourceWithRawResponse,
    AsyncUserResourceWithRawResponse,
    UserResourceWithStreamingResponse,
    AsyncUserResourceWithStreamingResponse,
)
from .workspace import (
    WorkspaceResource,
    AsyncWorkspaceResource,
    WorkspaceResourceWithRawResponse,
    AsyncWorkspaceResourceWithRawResponse,
    WorkspaceResourceWithStreamingResponse,
    AsyncWorkspaceResourceWithStreamingResponse,
)
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .notifications import (
    NotificationsResource,
    AsyncNotificationsResource,
    NotificationsResourceWithRawResponse,
    AsyncNotificationsResourceWithRawResponse,
    NotificationsResourceWithStreamingResponse,
    AsyncNotificationsResourceWithStreamingResponse,
)
from ..._base_client import make_request_options
from .document.document import (
    DocumentResource,
    AsyncDocumentResource,
    DocumentResourceWithRawResponse,
    AsyncDocumentResourceWithRawResponse,
    DocumentResourceWithStreamingResponse,
    AsyncDocumentResourceWithStreamingResponse,
)
from .conversation.conversation import (
    ConversationResource,
    AsyncConversationResource,
    ConversationResourceWithRawResponse,
    AsyncConversationResourceWithRawResponse,
    ConversationResourceWithStreamingResponse,
    AsyncConversationResourceWithStreamingResponse,
)

__all__ = ["APIResource", "AsyncAPIResource"]


class APIResource(_resource.SyncAPIResource):
    @cached_property
    def user(self) -> UserResource:
        return UserResource(self._client)

    @cached_property
    def workspace(self) -> WorkspaceResource:
        return WorkspaceResource(self._client)

    @cached_property
    def document(self) -> DocumentResource:
        return DocumentResource(self._client)

    @cached_property
    def conversation(self) -> ConversationResource:
        return ConversationResource(self._client)

    @cached_property
    def assistant(self) -> AssistantResource:
        return AssistantResource(self._client)

    @cached_property
    def health(self) -> HealthResource:
        return HealthResource(self._client)

    @cached_property
    def tag(self) -> TagResource:
        return TagResource(self._client)

    @cached_property
    def configs(self) -> ConfigsResource:
        return ConfigsResource(self._client)

    @cached_property
    def notifications(self) -> NotificationsResource:
        return NotificationsResource(self._client)

    @cached_property
    def with_raw_response(self) -> APIResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#accessing-raw-response-data-eg-headers
        """
        return APIResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> APIResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#with_streaming_response
        """
        return APIResourceWithStreamingResponse(self)

    def index(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """Serves the admin application page with necessary configuration variables."""
        return self._get(
            "/api",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncAPIResource(_resource.AsyncAPIResource):
    @cached_property
    def user(self) -> AsyncUserResource:
        return AsyncUserResource(self._client)

    @cached_property
    def workspace(self) -> AsyncWorkspaceResource:
        return AsyncWorkspaceResource(self._client)

    @cached_property
    def document(self) -> AsyncDocumentResource:
        return AsyncDocumentResource(self._client)

    @cached_property
    def conversation(self) -> AsyncConversationResource:
        return AsyncConversationResource(self._client)

    @cached_property
    def assistant(self) -> AsyncAssistantResource:
        return AsyncAssistantResource(self._client)

    @cached_property
    def health(self) -> AsyncHealthResource:
        return AsyncHealthResource(self._client)

    @cached_property
    def tag(self) -> AsyncTagResource:
        return AsyncTagResource(self._client)

    @cached_property
    def configs(self) -> AsyncConfigsResource:
        return AsyncConfigsResource(self._client)

    @cached_property
    def notifications(self) -> AsyncNotificationsResource:
        return AsyncNotificationsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncAPIResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#accessing-raw-response-data-eg-headers
        """
        return AsyncAPIResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncAPIResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#with_streaming_response
        """
        return AsyncAPIResourceWithStreamingResponse(self)

    async def index(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """Serves the admin application page with necessary configuration variables."""
        return await self._get(
            "/api",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class APIResourceWithRawResponse:
    def __init__(self, api: APIResource) -> None:
        self._api = api

        self.index = to_raw_response_wrapper(
            api.index,
        )

    @cached_property
    def user(self) -> UserResourceWithRawResponse:
        return UserResourceWithRawResponse(self._api.user)

    @cached_property
    def workspace(self) -> WorkspaceResourceWithRawResponse:
        return WorkspaceResourceWithRawResponse(self._api.workspace)

    @cached_property
    def document(self) -> DocumentResourceWithRawResponse:
        return DocumentResourceWithRawResponse(self._api.document)

    @cached_property
    def conversation(self) -> ConversationResourceWithRawResponse:
        return ConversationResourceWithRawResponse(self._api.conversation)

    @cached_property
    def assistant(self) -> AssistantResourceWithRawResponse:
        return AssistantResourceWithRawResponse(self._api.assistant)

    @cached_property
    def health(self) -> HealthResourceWithRawResponse:
        return HealthResourceWithRawResponse(self._api.health)

    @cached_property
    def tag(self) -> TagResourceWithRawResponse:
        return TagResourceWithRawResponse(self._api.tag)

    @cached_property
    def configs(self) -> ConfigsResourceWithRawResponse:
        return ConfigsResourceWithRawResponse(self._api.configs)

    @cached_property
    def notifications(self) -> NotificationsResourceWithRawResponse:
        return NotificationsResourceWithRawResponse(self._api.notifications)


class AsyncAPIResourceWithRawResponse:
    def __init__(self, api: AsyncAPIResource) -> None:
        self._api = api

        self.index = async_to_raw_response_wrapper(
            api.index,
        )

    @cached_property
    def user(self) -> AsyncUserResourceWithRawResponse:
        return AsyncUserResourceWithRawResponse(self._api.user)

    @cached_property
    def workspace(self) -> AsyncWorkspaceResourceWithRawResponse:
        return AsyncWorkspaceResourceWithRawResponse(self._api.workspace)

    @cached_property
    def document(self) -> AsyncDocumentResourceWithRawResponse:
        return AsyncDocumentResourceWithRawResponse(self._api.document)

    @cached_property
    def conversation(self) -> AsyncConversationResourceWithRawResponse:
        return AsyncConversationResourceWithRawResponse(self._api.conversation)

    @cached_property
    def assistant(self) -> AsyncAssistantResourceWithRawResponse:
        return AsyncAssistantResourceWithRawResponse(self._api.assistant)

    @cached_property
    def health(self) -> AsyncHealthResourceWithRawResponse:
        return AsyncHealthResourceWithRawResponse(self._api.health)

    @cached_property
    def tag(self) -> AsyncTagResourceWithRawResponse:
        return AsyncTagResourceWithRawResponse(self._api.tag)

    @cached_property
    def configs(self) -> AsyncConfigsResourceWithRawResponse:
        return AsyncConfigsResourceWithRawResponse(self._api.configs)

    @cached_property
    def notifications(self) -> AsyncNotificationsResourceWithRawResponse:
        return AsyncNotificationsResourceWithRawResponse(self._api.notifications)


class APIResourceWithStreamingResponse:
    def __init__(self, api: APIResource) -> None:
        self._api = api

        self.index = to_streamed_response_wrapper(
            api.index,
        )

    @cached_property
    def user(self) -> UserResourceWithStreamingResponse:
        return UserResourceWithStreamingResponse(self._api.user)

    @cached_property
    def workspace(self) -> WorkspaceResourceWithStreamingResponse:
        return WorkspaceResourceWithStreamingResponse(self._api.workspace)

    @cached_property
    def document(self) -> DocumentResourceWithStreamingResponse:
        return DocumentResourceWithStreamingResponse(self._api.document)

    @cached_property
    def conversation(self) -> ConversationResourceWithStreamingResponse:
        return ConversationResourceWithStreamingResponse(self._api.conversation)

    @cached_property
    def assistant(self) -> AssistantResourceWithStreamingResponse:
        return AssistantResourceWithStreamingResponse(self._api.assistant)

    @cached_property
    def health(self) -> HealthResourceWithStreamingResponse:
        return HealthResourceWithStreamingResponse(self._api.health)

    @cached_property
    def tag(self) -> TagResourceWithStreamingResponse:
        return TagResourceWithStreamingResponse(self._api.tag)

    @cached_property
    def configs(self) -> ConfigsResourceWithStreamingResponse:
        return ConfigsResourceWithStreamingResponse(self._api.configs)

    @cached_property
    def notifications(self) -> NotificationsResourceWithStreamingResponse:
        return NotificationsResourceWithStreamingResponse(self._api.notifications)


class AsyncAPIResourceWithStreamingResponse:
    def __init__(self, api: AsyncAPIResource) -> None:
        self._api = api

        self.index = async_to_streamed_response_wrapper(
            api.index,
        )

    @cached_property
    def user(self) -> AsyncUserResourceWithStreamingResponse:
        return AsyncUserResourceWithStreamingResponse(self._api.user)

    @cached_property
    def workspace(self) -> AsyncWorkspaceResourceWithStreamingResponse:
        return AsyncWorkspaceResourceWithStreamingResponse(self._api.workspace)

    @cached_property
    def document(self) -> AsyncDocumentResourceWithStreamingResponse:
        return AsyncDocumentResourceWithStreamingResponse(self._api.document)

    @cached_property
    def conversation(self) -> AsyncConversationResourceWithStreamingResponse:
        return AsyncConversationResourceWithStreamingResponse(self._api.conversation)

    @cached_property
    def assistant(self) -> AsyncAssistantResourceWithStreamingResponse:
        return AsyncAssistantResourceWithStreamingResponse(self._api.assistant)

    @cached_property
    def health(self) -> AsyncHealthResourceWithStreamingResponse:
        return AsyncHealthResourceWithStreamingResponse(self._api.health)

    @cached_property
    def tag(self) -> AsyncTagResourceWithStreamingResponse:
        return AsyncTagResourceWithStreamingResponse(self._api.tag)

    @cached_property
    def configs(self) -> AsyncConfigsResourceWithStreamingResponse:
        return AsyncConfigsResourceWithStreamingResponse(self._api.configs)

    @cached_property
    def notifications(self) -> AsyncNotificationsResourceWithStreamingResponse:
        return AsyncNotificationsResourceWithStreamingResponse(self._api.notifications)
