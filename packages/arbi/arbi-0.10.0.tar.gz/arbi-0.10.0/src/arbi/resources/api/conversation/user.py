# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ...._types import Body, Query, Headers, NotGiven, not_given
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
from ....types.api.conversation import user_add_params, user_remove_params
from ....types.api.conversation.user_add_response import UserAddResponse
from ....types.api.conversation.user_remove_response import UserRemoveResponse

__all__ = ["UserResource", "AsyncUserResource"]


class UserResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> UserResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#accessing-raw-response-data-eg-headers
        """
        return UserResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> UserResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#with_streaming_response
        """
        return UserResourceWithStreamingResponse(self)

    def add(
        self,
        conversation_ext_id: str,
        *,
        user_ext_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UserAddResponse:
        """
        Add a user to a conversation.

        RLS ensures the user can only add users to conversations they have access to.
        PostgreSQL constraints handle duplicate users.

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
            f"/api/conversation/{conversation_ext_id}/user",
            body=maybe_transform({"user_ext_id": user_ext_id}, user_add_params.UserAddParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserAddResponse,
        )

    def remove(
        self,
        conversation_ext_id: str,
        *,
        user_ext_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UserRemoveResponse:
        """
        Remove a user from a conversation.

        RLS ensures the user can only modify conversations they have access to.

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
            f"/api/conversation/{conversation_ext_id}/user",
            body=maybe_transform({"user_ext_id": user_ext_id}, user_remove_params.UserRemoveParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserRemoveResponse,
        )


class AsyncUserResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncUserResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#accessing-raw-response-data-eg-headers
        """
        return AsyncUserResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncUserResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#with_streaming_response
        """
        return AsyncUserResourceWithStreamingResponse(self)

    async def add(
        self,
        conversation_ext_id: str,
        *,
        user_ext_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UserAddResponse:
        """
        Add a user to a conversation.

        RLS ensures the user can only add users to conversations they have access to.
        PostgreSQL constraints handle duplicate users.

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
            f"/api/conversation/{conversation_ext_id}/user",
            body=await async_maybe_transform({"user_ext_id": user_ext_id}, user_add_params.UserAddParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserAddResponse,
        )

    async def remove(
        self,
        conversation_ext_id: str,
        *,
        user_ext_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UserRemoveResponse:
        """
        Remove a user from a conversation.

        RLS ensures the user can only modify conversations they have access to.

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
            f"/api/conversation/{conversation_ext_id}/user",
            body=await async_maybe_transform({"user_ext_id": user_ext_id}, user_remove_params.UserRemoveParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserRemoveResponse,
        )


class UserResourceWithRawResponse:
    def __init__(self, user: UserResource) -> None:
        self._user = user

        self.add = to_raw_response_wrapper(
            user.add,
        )
        self.remove = to_raw_response_wrapper(
            user.remove,
        )


class AsyncUserResourceWithRawResponse:
    def __init__(self, user: AsyncUserResource) -> None:
        self._user = user

        self.add = async_to_raw_response_wrapper(
            user.add,
        )
        self.remove = async_to_raw_response_wrapper(
            user.remove,
        )


class UserResourceWithStreamingResponse:
    def __init__(self, user: UserResource) -> None:
        self._user = user

        self.add = to_streamed_response_wrapper(
            user.add,
        )
        self.remove = to_streamed_response_wrapper(
            user.remove,
        )


class AsyncUserResourceWithStreamingResponse:
    def __init__(self, user: AsyncUserResource) -> None:
        self._user = user

        self.add = async_to_streamed_response_wrapper(
            user.add,
        )
        self.remove = async_to_streamed_response_wrapper(
            user.remove,
        )
