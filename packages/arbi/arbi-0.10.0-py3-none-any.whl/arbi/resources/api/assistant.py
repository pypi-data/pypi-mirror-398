# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional

import httpx

from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import maybe_transform, strip_not_given, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...types.api import assistant_query_params, assistant_retrieve_params
from ..._base_client import make_request_options

__all__ = ["AssistantResource", "AsyncAssistantResource"]


class AssistantResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AssistantResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#accessing-raw-response-data-eg-headers
        """
        return AssistantResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AssistantResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#with_streaming_response
        """
        return AssistantResourceWithStreamingResponse(self)

    def retrieve(
        self,
        *,
        content: str,
        workspace_ext_id: str,
        config_ext_id: Optional[str] | Omit = omit,
        parent_message_ext_id: Optional[str] | Omit = omit,
        tools: Dict[str, assistant_retrieve_params.Tools] | Omit = omit,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """Retrieve relevant document chunks for a user message.

        Returns tool responses
        with context from documents without generating an answer.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"workspace-key": workspace_key}), **(extra_headers or {})}
        return self._post(
            "/api/assistant/retrieve",
            body=maybe_transform(
                {
                    "content": content,
                    "workspace_ext_id": workspace_ext_id,
                    "config_ext_id": config_ext_id,
                    "parent_message_ext_id": parent_message_ext_id,
                    "tools": tools,
                },
                assistant_retrieve_params.AssistantRetrieveParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def query(
        self,
        *,
        content: str,
        workspace_ext_id: str,
        config_ext_id: Optional[str] | Omit = omit,
        parent_message_ext_id: Optional[str] | Omit = omit,
        tools: Dict[str, assistant_query_params.Tools] | Omit = omit,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """Process a user query against documents in a workspace.

        Performs retrieval
        augmented generation with streaming response.

        Requires active subscription (paid/trial/dev) if Stripe is configured.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"workspace-key": workspace_key}), **(extra_headers or {})}
        return self._post(
            "/api/assistant/query",
            body=maybe_transform(
                {
                    "content": content,
                    "workspace_ext_id": workspace_ext_id,
                    "config_ext_id": config_ext_id,
                    "parent_message_ext_id": parent_message_ext_id,
                    "tools": tools,
                },
                assistant_query_params.AssistantQueryParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncAssistantResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncAssistantResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#accessing-raw-response-data-eg-headers
        """
        return AsyncAssistantResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncAssistantResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#with_streaming_response
        """
        return AsyncAssistantResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        *,
        content: str,
        workspace_ext_id: str,
        config_ext_id: Optional[str] | Omit = omit,
        parent_message_ext_id: Optional[str] | Omit = omit,
        tools: Dict[str, assistant_retrieve_params.Tools] | Omit = omit,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """Retrieve relevant document chunks for a user message.

        Returns tool responses
        with context from documents without generating an answer.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"workspace-key": workspace_key}), **(extra_headers or {})}
        return await self._post(
            "/api/assistant/retrieve",
            body=await async_maybe_transform(
                {
                    "content": content,
                    "workspace_ext_id": workspace_ext_id,
                    "config_ext_id": config_ext_id,
                    "parent_message_ext_id": parent_message_ext_id,
                    "tools": tools,
                },
                assistant_retrieve_params.AssistantRetrieveParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def query(
        self,
        *,
        content: str,
        workspace_ext_id: str,
        config_ext_id: Optional[str] | Omit = omit,
        parent_message_ext_id: Optional[str] | Omit = omit,
        tools: Dict[str, assistant_query_params.Tools] | Omit = omit,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """Process a user query against documents in a workspace.

        Performs retrieval
        augmented generation with streaming response.

        Requires active subscription (paid/trial/dev) if Stripe is configured.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"workspace-key": workspace_key}), **(extra_headers or {})}
        return await self._post(
            "/api/assistant/query",
            body=await async_maybe_transform(
                {
                    "content": content,
                    "workspace_ext_id": workspace_ext_id,
                    "config_ext_id": config_ext_id,
                    "parent_message_ext_id": parent_message_ext_id,
                    "tools": tools,
                },
                assistant_query_params.AssistantQueryParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AssistantResourceWithRawResponse:
    def __init__(self, assistant: AssistantResource) -> None:
        self._assistant = assistant

        self.retrieve = to_raw_response_wrapper(
            assistant.retrieve,
        )
        self.query = to_raw_response_wrapper(
            assistant.query,
        )


class AsyncAssistantResourceWithRawResponse:
    def __init__(self, assistant: AsyncAssistantResource) -> None:
        self._assistant = assistant

        self.retrieve = async_to_raw_response_wrapper(
            assistant.retrieve,
        )
        self.query = async_to_raw_response_wrapper(
            assistant.query,
        )


class AssistantResourceWithStreamingResponse:
    def __init__(self, assistant: AssistantResource) -> None:
        self._assistant = assistant

        self.retrieve = to_streamed_response_wrapper(
            assistant.retrieve,
        )
        self.query = to_streamed_response_wrapper(
            assistant.query,
        )


class AsyncAssistantResourceWithStreamingResponse:
    def __init__(self, assistant: AsyncAssistantResource) -> None:
        self._assistant = assistant

        self.retrieve = async_to_streamed_response_wrapper(
            assistant.retrieve,
        )
        self.query = async_to_streamed_response_wrapper(
            assistant.query,
        )
