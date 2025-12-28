# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Any, Optional, cast

import httpx

from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...types.api import (
    config_create_params,
)
from ..._base_client import make_request_options
from ...types.api.parser_config_param import ParserConfigParam
from ...types.api.chunker_config_param import ChunkerConfigParam
from ...types.api.embedder_config_param import EmbedderConfigParam
from ...types.api.reranker_config_param import RerankerConfigParam
from ...types.api.config_create_response import ConfigCreateResponse
from ...types.api.config_delete_response import ConfigDeleteResponse
from ...types.api.query_llm_config_param import QueryLlmConfigParam
from ...types.api.retriever_config_param import RetrieverConfigParam
from ...types.api.title_llm_config_param import TitleLlmConfigParam
from ...types.api.config_retrieve_response import ConfigRetrieveResponse
from ...types.api.model_citation_config_param import ModelCitationConfigParam
from ...types.api.config_get_versions_response import ConfigGetVersionsResponse
from ...types.api.document_date_extractor_llm_config_param import DocumentDateExtractorLlmConfigParam

__all__ = ["ConfigsResource", "AsyncConfigsResource"]


class ConfigsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ConfigsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#accessing-raw-response-data-eg-headers
        """
        return ConfigsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ConfigsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#with_streaming_response
        """
        return ConfigsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        agent_llm: Optional[config_create_params.AgentLlm] | Omit = omit,
        agents: Optional[config_create_params.Agents] | Omit = omit,
        chunker: Optional[ChunkerConfigParam] | Omit = omit,
        document_date_extractor_llm: Optional[DocumentDateExtractorLlmConfigParam] | Omit = omit,
        embedder: Optional[EmbedderConfigParam] | Omit = omit,
        model_citation: Optional[ModelCitationConfigParam] | Omit = omit,
        parent_message_ext_id: Optional[str] | Omit = omit,
        parser: Optional[ParserConfigParam] | Omit = omit,
        query_llm: Optional[QueryLlmConfigParam] | Omit = omit,
        reranker: Optional[RerankerConfigParam] | Omit = omit,
        retriever: Optional[RetrieverConfigParam] | Omit = omit,
        title: str | Omit = omit,
        title_llm: Optional[TitleLlmConfigParam] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ConfigCreateResponse:
        """
        Save a new configuration.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/configs/",
            body=maybe_transform(
                {
                    "agent_llm": agent_llm,
                    "agents": agents,
                    "chunker": chunker,
                    "document_date_extractor_llm": document_date_extractor_llm,
                    "embedder": embedder,
                    "model_citation": model_citation,
                    "parent_message_ext_id": parent_message_ext_id,
                    "parser": parser,
                    "query_llm": query_llm,
                    "reranker": reranker,
                    "retriever": retriever,
                    "title": title,
                    "title_llm": title_llm,
                },
                config_create_params.ConfigCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ConfigCreateResponse,
        )

    def retrieve(
        self,
        config_ext_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ConfigRetrieveResponse:
        """
        Read configurations from database to be displayed in the UI

        Args:
          config_ext_id: Config name: 'cfg-XXXXXXXX' or 'default' for system default

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not config_ext_id:
            raise ValueError(f"Expected a non-empty value for `config_ext_id` but received {config_ext_id!r}")
        return cast(
            ConfigRetrieveResponse,
            self._get(
                f"/api/configs/{config_ext_id}",
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(
                    Any, ConfigRetrieveResponse
                ),  # Union types cannot be passed in as arguments in the type system
            ),
        )

    def delete(
        self,
        config_ext_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ConfigDeleteResponse:
        """
        Delete a specific configuration from database

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not config_ext_id:
            raise ValueError(f"Expected a non-empty value for `config_ext_id` but received {config_ext_id!r}")
        return self._delete(
            f"/api/configs/{config_ext_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ConfigDeleteResponse,
        )

    def get_schema(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """Return the JSON schema for all config models"""
        return self._get(
            "/api/configs/schema",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def get_versions(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ConfigGetVersionsResponse:
        """Returns a list of available configuration versions for the current user"""
        return self._get(
            "/api/configs/versions",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ConfigGetVersionsResponse,
        )


class AsyncConfigsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncConfigsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#accessing-raw-response-data-eg-headers
        """
        return AsyncConfigsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncConfigsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#with_streaming_response
        """
        return AsyncConfigsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        agent_llm: Optional[config_create_params.AgentLlm] | Omit = omit,
        agents: Optional[config_create_params.Agents] | Omit = omit,
        chunker: Optional[ChunkerConfigParam] | Omit = omit,
        document_date_extractor_llm: Optional[DocumentDateExtractorLlmConfigParam] | Omit = omit,
        embedder: Optional[EmbedderConfigParam] | Omit = omit,
        model_citation: Optional[ModelCitationConfigParam] | Omit = omit,
        parent_message_ext_id: Optional[str] | Omit = omit,
        parser: Optional[ParserConfigParam] | Omit = omit,
        query_llm: Optional[QueryLlmConfigParam] | Omit = omit,
        reranker: Optional[RerankerConfigParam] | Omit = omit,
        retriever: Optional[RetrieverConfigParam] | Omit = omit,
        title: str | Omit = omit,
        title_llm: Optional[TitleLlmConfigParam] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ConfigCreateResponse:
        """
        Save a new configuration.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/configs/",
            body=await async_maybe_transform(
                {
                    "agent_llm": agent_llm,
                    "agents": agents,
                    "chunker": chunker,
                    "document_date_extractor_llm": document_date_extractor_llm,
                    "embedder": embedder,
                    "model_citation": model_citation,
                    "parent_message_ext_id": parent_message_ext_id,
                    "parser": parser,
                    "query_llm": query_llm,
                    "reranker": reranker,
                    "retriever": retriever,
                    "title": title,
                    "title_llm": title_llm,
                },
                config_create_params.ConfigCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ConfigCreateResponse,
        )

    async def retrieve(
        self,
        config_ext_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ConfigRetrieveResponse:
        """
        Read configurations from database to be displayed in the UI

        Args:
          config_ext_id: Config name: 'cfg-XXXXXXXX' or 'default' for system default

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not config_ext_id:
            raise ValueError(f"Expected a non-empty value for `config_ext_id` but received {config_ext_id!r}")
        return cast(
            ConfigRetrieveResponse,
            await self._get(
                f"/api/configs/{config_ext_id}",
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(
                    Any, ConfigRetrieveResponse
                ),  # Union types cannot be passed in as arguments in the type system
            ),
        )

    async def delete(
        self,
        config_ext_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ConfigDeleteResponse:
        """
        Delete a specific configuration from database

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not config_ext_id:
            raise ValueError(f"Expected a non-empty value for `config_ext_id` but received {config_ext_id!r}")
        return await self._delete(
            f"/api/configs/{config_ext_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ConfigDeleteResponse,
        )

    async def get_schema(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """Return the JSON schema for all config models"""
        return await self._get(
            "/api/configs/schema",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def get_versions(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ConfigGetVersionsResponse:
        """Returns a list of available configuration versions for the current user"""
        return await self._get(
            "/api/configs/versions",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ConfigGetVersionsResponse,
        )


class ConfigsResourceWithRawResponse:
    def __init__(self, configs: ConfigsResource) -> None:
        self._configs = configs

        self.create = to_raw_response_wrapper(
            configs.create,
        )
        self.retrieve = to_raw_response_wrapper(
            configs.retrieve,
        )
        self.delete = to_raw_response_wrapper(
            configs.delete,
        )
        self.get_schema = to_raw_response_wrapper(
            configs.get_schema,
        )
        self.get_versions = to_raw_response_wrapper(
            configs.get_versions,
        )


class AsyncConfigsResourceWithRawResponse:
    def __init__(self, configs: AsyncConfigsResource) -> None:
        self._configs = configs

        self.create = async_to_raw_response_wrapper(
            configs.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            configs.retrieve,
        )
        self.delete = async_to_raw_response_wrapper(
            configs.delete,
        )
        self.get_schema = async_to_raw_response_wrapper(
            configs.get_schema,
        )
        self.get_versions = async_to_raw_response_wrapper(
            configs.get_versions,
        )


class ConfigsResourceWithStreamingResponse:
    def __init__(self, configs: ConfigsResource) -> None:
        self._configs = configs

        self.create = to_streamed_response_wrapper(
            configs.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            configs.retrieve,
        )
        self.delete = to_streamed_response_wrapper(
            configs.delete,
        )
        self.get_schema = to_streamed_response_wrapper(
            configs.get_schema,
        )
        self.get_versions = to_streamed_response_wrapper(
            configs.get_versions,
        )


class AsyncConfigsResourceWithStreamingResponse:
    def __init__(self, configs: AsyncConfigsResource) -> None:
        self._configs = configs

        self.create = async_to_streamed_response_wrapper(
            configs.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            configs.retrieve,
        )
        self.delete = async_to_streamed_response_wrapper(
            configs.delete,
        )
        self.get_schema = async_to_streamed_response_wrapper(
            configs.get_schema,
        )
        self.get_versions = async_to_streamed_response_wrapper(
            configs.get_versions,
        )
