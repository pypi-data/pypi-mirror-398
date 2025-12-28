# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from .user import (
    UserResource,
    AsyncUserResource,
    UserResourceWithRawResponse,
    AsyncUserResourceWithRawResponse,
    UserResourceWithStreamingResponse,
    AsyncUserResourceWithStreamingResponse,
)
from ...._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ...._utils import maybe_transform, strip_not_given, async_maybe_transform
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ....types.api import conversation_update_title_params
from ...._base_client import make_request_options
from ....types.api.conversation_share_response import ConversationShareResponse
from ....types.api.conversation_delete_response import ConversationDeleteResponse
from ....types.api.conversation_update_title_response import ConversationUpdateTitleResponse
from ....types.api.conversation_delete_message_response import ConversationDeleteMessageResponse
from ....types.api.conversation_retrieve_message_response import ConversationRetrieveMessageResponse
from ....types.api.conversation_retrieve_threads_response import ConversationRetrieveThreadsResponse

__all__ = ["ConversationResource", "AsyncConversationResource"]


class ConversationResource(SyncAPIResource):
    @cached_property
    def user(self) -> UserResource:
        return UserResource(self._client)

    @cached_property
    def with_raw_response(self) -> ConversationResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#accessing-raw-response-data-eg-headers
        """
        return ConversationResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ConversationResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#with_streaming_response
        """
        return ConversationResourceWithStreamingResponse(self)

    def delete(
        self,
        conversation_ext_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ConversationDeleteResponse:
        """Delete a conversation.

        RLS ensures the user can only delete conversations they
        have access to. Deleting a conversation will also delete all associated messages
        due to cascade delete.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not conversation_ext_id:
            raise ValueError(
                f"Expected a non-empty value for `conversation_ext_id` but received {conversation_ext_id!r}"
            )
        return self._delete(
            f"/api/conversation/{conversation_ext_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ConversationDeleteResponse,
        )

    def delete_message(
        self,
        message_ext_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ConversationDeleteMessageResponse:
        """
        Delete a message along with all descendants.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not message_ext_id:
            raise ValueError(f"Expected a non-empty value for `message_ext_id` but received {message_ext_id!r}")
        return self._delete(
            f"/api/conversation/message/{message_ext_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ConversationDeleteMessageResponse,
        )

    def retrieve_message(
        self,
        message_ext_id: str,
        *,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ConversationRetrieveMessageResponse:
        """
        Get a single message with full details including decrypted execution trace.
        Always includes the trace with decrypted sensitive fields.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not message_ext_id:
            raise ValueError(f"Expected a non-empty value for `message_ext_id` but received {message_ext_id!r}")
        extra_headers = {**strip_not_given({"workspace-key": workspace_key}), **(extra_headers or {})}
        return self._get(
            f"/api/conversation/message/{message_ext_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ConversationRetrieveMessageResponse,
        )

    def retrieve_threads(
        self,
        conversation_ext_id: str,
        *,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ConversationRetrieveThreadsResponse:
        """
        Retrieve all conversation threads (leaf messages and their histories) for a
        given conversation external ID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not conversation_ext_id:
            raise ValueError(
                f"Expected a non-empty value for `conversation_ext_id` but received {conversation_ext_id!r}"
            )
        extra_headers = {**strip_not_given({"workspace-key": workspace_key}), **(extra_headers or {})}
        return self._get(
            f"/api/conversation/{conversation_ext_id}/threads",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ConversationRetrieveThreadsResponse,
        )

    def share(
        self,
        conversation_ext_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ConversationShareResponse:
        """
        Share all messages in a conversation by setting their shared flag to true.

        Only the conversation creator can share a conversation.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not conversation_ext_id:
            raise ValueError(
                f"Expected a non-empty value for `conversation_ext_id` but received {conversation_ext_id!r}"
            )
        return self._post(
            f"/api/conversation/{conversation_ext_id}/share",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ConversationShareResponse,
        )

    def update_title(
        self,
        conversation_ext_id: str,
        *,
        title: str,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ConversationUpdateTitleResponse:
        """Update a conversation title.

        RLS ensures the user can only update conversations
        they have access to.

        Args:
          title: New conversation title (1-60 characters)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not conversation_ext_id:
            raise ValueError(
                f"Expected a non-empty value for `conversation_ext_id` but received {conversation_ext_id!r}"
            )
        extra_headers = {**strip_not_given({"workspace-key": workspace_key}), **(extra_headers or {})}
        return self._patch(
            f"/api/conversation/{conversation_ext_id}/title",
            body=maybe_transform({"title": title}, conversation_update_title_params.ConversationUpdateTitleParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ConversationUpdateTitleResponse,
        )


class AsyncConversationResource(AsyncAPIResource):
    @cached_property
    def user(self) -> AsyncUserResource:
        return AsyncUserResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncConversationResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#accessing-raw-response-data-eg-headers
        """
        return AsyncConversationResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncConversationResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#with_streaming_response
        """
        return AsyncConversationResourceWithStreamingResponse(self)

    async def delete(
        self,
        conversation_ext_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ConversationDeleteResponse:
        """Delete a conversation.

        RLS ensures the user can only delete conversations they
        have access to. Deleting a conversation will also delete all associated messages
        due to cascade delete.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not conversation_ext_id:
            raise ValueError(
                f"Expected a non-empty value for `conversation_ext_id` but received {conversation_ext_id!r}"
            )
        return await self._delete(
            f"/api/conversation/{conversation_ext_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ConversationDeleteResponse,
        )

    async def delete_message(
        self,
        message_ext_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ConversationDeleteMessageResponse:
        """
        Delete a message along with all descendants.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not message_ext_id:
            raise ValueError(f"Expected a non-empty value for `message_ext_id` but received {message_ext_id!r}")
        return await self._delete(
            f"/api/conversation/message/{message_ext_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ConversationDeleteMessageResponse,
        )

    async def retrieve_message(
        self,
        message_ext_id: str,
        *,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ConversationRetrieveMessageResponse:
        """
        Get a single message with full details including decrypted execution trace.
        Always includes the trace with decrypted sensitive fields.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not message_ext_id:
            raise ValueError(f"Expected a non-empty value for `message_ext_id` but received {message_ext_id!r}")
        extra_headers = {**strip_not_given({"workspace-key": workspace_key}), **(extra_headers or {})}
        return await self._get(
            f"/api/conversation/message/{message_ext_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ConversationRetrieveMessageResponse,
        )

    async def retrieve_threads(
        self,
        conversation_ext_id: str,
        *,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ConversationRetrieveThreadsResponse:
        """
        Retrieve all conversation threads (leaf messages and their histories) for a
        given conversation external ID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not conversation_ext_id:
            raise ValueError(
                f"Expected a non-empty value for `conversation_ext_id` but received {conversation_ext_id!r}"
            )
        extra_headers = {**strip_not_given({"workspace-key": workspace_key}), **(extra_headers or {})}
        return await self._get(
            f"/api/conversation/{conversation_ext_id}/threads",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ConversationRetrieveThreadsResponse,
        )

    async def share(
        self,
        conversation_ext_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ConversationShareResponse:
        """
        Share all messages in a conversation by setting their shared flag to true.

        Only the conversation creator can share a conversation.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not conversation_ext_id:
            raise ValueError(
                f"Expected a non-empty value for `conversation_ext_id` but received {conversation_ext_id!r}"
            )
        return await self._post(
            f"/api/conversation/{conversation_ext_id}/share",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ConversationShareResponse,
        )

    async def update_title(
        self,
        conversation_ext_id: str,
        *,
        title: str,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ConversationUpdateTitleResponse:
        """Update a conversation title.

        RLS ensures the user can only update conversations
        they have access to.

        Args:
          title: New conversation title (1-60 characters)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not conversation_ext_id:
            raise ValueError(
                f"Expected a non-empty value for `conversation_ext_id` but received {conversation_ext_id!r}"
            )
        extra_headers = {**strip_not_given({"workspace-key": workspace_key}), **(extra_headers or {})}
        return await self._patch(
            f"/api/conversation/{conversation_ext_id}/title",
            body=await async_maybe_transform(
                {"title": title}, conversation_update_title_params.ConversationUpdateTitleParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ConversationUpdateTitleResponse,
        )


class ConversationResourceWithRawResponse:
    def __init__(self, conversation: ConversationResource) -> None:
        self._conversation = conversation

        self.delete = to_raw_response_wrapper(
            conversation.delete,
        )
        self.delete_message = to_raw_response_wrapper(
            conversation.delete_message,
        )
        self.retrieve_message = to_raw_response_wrapper(
            conversation.retrieve_message,
        )
        self.retrieve_threads = to_raw_response_wrapper(
            conversation.retrieve_threads,
        )
        self.share = to_raw_response_wrapper(
            conversation.share,
        )
        self.update_title = to_raw_response_wrapper(
            conversation.update_title,
        )

    @cached_property
    def user(self) -> UserResourceWithRawResponse:
        return UserResourceWithRawResponse(self._conversation.user)


class AsyncConversationResourceWithRawResponse:
    def __init__(self, conversation: AsyncConversationResource) -> None:
        self._conversation = conversation

        self.delete = async_to_raw_response_wrapper(
            conversation.delete,
        )
        self.delete_message = async_to_raw_response_wrapper(
            conversation.delete_message,
        )
        self.retrieve_message = async_to_raw_response_wrapper(
            conversation.retrieve_message,
        )
        self.retrieve_threads = async_to_raw_response_wrapper(
            conversation.retrieve_threads,
        )
        self.share = async_to_raw_response_wrapper(
            conversation.share,
        )
        self.update_title = async_to_raw_response_wrapper(
            conversation.update_title,
        )

    @cached_property
    def user(self) -> AsyncUserResourceWithRawResponse:
        return AsyncUserResourceWithRawResponse(self._conversation.user)


class ConversationResourceWithStreamingResponse:
    def __init__(self, conversation: ConversationResource) -> None:
        self._conversation = conversation

        self.delete = to_streamed_response_wrapper(
            conversation.delete,
        )
        self.delete_message = to_streamed_response_wrapper(
            conversation.delete_message,
        )
        self.retrieve_message = to_streamed_response_wrapper(
            conversation.retrieve_message,
        )
        self.retrieve_threads = to_streamed_response_wrapper(
            conversation.retrieve_threads,
        )
        self.share = to_streamed_response_wrapper(
            conversation.share,
        )
        self.update_title = to_streamed_response_wrapper(
            conversation.update_title,
        )

    @cached_property
    def user(self) -> UserResourceWithStreamingResponse:
        return UserResourceWithStreamingResponse(self._conversation.user)


class AsyncConversationResourceWithStreamingResponse:
    def __init__(self, conversation: AsyncConversationResource) -> None:
        self._conversation = conversation

        self.delete = async_to_streamed_response_wrapper(
            conversation.delete,
        )
        self.delete_message = async_to_streamed_response_wrapper(
            conversation.delete_message,
        )
        self.retrieve_message = async_to_streamed_response_wrapper(
            conversation.retrieve_message,
        )
        self.retrieve_threads = async_to_streamed_response_wrapper(
            conversation.retrieve_threads,
        )
        self.share = async_to_streamed_response_wrapper(
            conversation.share,
        )
        self.update_title = async_to_streamed_response_wrapper(
            conversation.update_title,
        )

    @cached_property
    def user(self) -> AsyncUserResourceWithStreamingResponse:
        return AsyncUserResourceWithStreamingResponse(self._conversation.user)
