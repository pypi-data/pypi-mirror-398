# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from arbi import Arbi, AsyncArbi
from tests.utils import assert_matches_type
from arbi.types.api import (
    ConfigCreateResponse,
    ConfigDeleteResponse,
    ConfigRetrieveResponse,
    ConfigGetVersionsResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestConfigs:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Arbi) -> None:
        config = client.api.configs.create()
        assert_matches_type(ConfigCreateResponse, config, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: Arbi) -> None:
        config = client.api.configs.create(
            agent_llm={
                "api_type": "local",
                "enabled": True,
                "max_char_size_to_answer": 0,
                "max_context_tokens": 1000,
                "max_iterations": 0,
                "max_tokens": 0,
                "model_name": "MODEL_NAME",
                "show_interim_steps": True,
                "system_instruction": "SYSTEM_INSTRUCTION",
                "temperature": 0,
            },
            agents={
                "agent_model_name": "AGENT_MODEL_NAME",
                "agent_prompt": "AGENT_PROMPT",
                "enabled": True,
                "llm_agent_temperature": 0,
                "llm_page_filter_model_name": "LLM_PAGE_FILTER_MODEL_NAME",
                "llm_page_filter_prompt": "LLM_PAGE_FILTER_PROMPT",
                "llm_page_filter_temperature": 0,
                "llm_summarise_model_name": "LLM_SUMMARISE_MODEL_NAME",
                "llm_summarise_prompt": "LLM_SUMMARISE_PROMPT",
                "llm_summarise_temperature": 0,
            },
            chunker={},
            document_date_extractor_llm={
                "api_type": "local",
                "max_char_context_to_answer": 0,
                "max_tokens": 0,
                "model_name": "MODEL_NAME",
                "system_instruction": "SYSTEM_INSTRUCTION",
                "temperature": 0,
            },
            embedder={
                "api_type": "local",
                "batch_size": 0,
                "embed_prefix": "EMBED_PREFIX",
                "max_concurrent_requests": 0,
                "model_name": "MODEL_NAME",
                "query_prefix": "QUERY_PREFIX",
            },
            model_citation={
                "max_numb_citations": 0,
                "min_char_size_to_answer": 0,
                "sim_model_name": "SIM_MODEL_NAME",
                "sim_threashold": 0,
            },
            parent_message_ext_id="parent_message_ext_id",
            parser={},
            query_llm={
                "api_type": "local",
                "max_char_size_to_answer": 0,
                "max_tokens": 0,
                "model_name": "MODEL_NAME",
                "system_instruction": "SYSTEM_INSTRUCTION",
                "temperature": 0,
            },
            reranker={
                "api_type": "local",
                "max_numb_of_chunks": 1,
                "model_name": "MODEL_NAME",
            },
            retriever={
                "group_size": 1000,
                "max_distinct_documents": 100,
                "max_total_chunks_to_retrieve": 100,
                "min_retrieval_sim_score": 0,
            },
            title="title",
            title_llm={
                "api_type": "local",
                "max_char_size_to_answer": 0,
                "max_tokens": 0,
                "model_name": "MODEL_NAME",
                "system_instruction": "SYSTEM_INSTRUCTION",
                "temperature": 0,
            },
        )
        assert_matches_type(ConfigCreateResponse, config, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Arbi) -> None:
        response = client.api.configs.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        config = response.parse()
        assert_matches_type(ConfigCreateResponse, config, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Arbi) -> None:
        with client.api.configs.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            config = response.parse()
            assert_matches_type(ConfigCreateResponse, config, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Arbi) -> None:
        config = client.api.configs.retrieve(
            "config_ext_id",
        )
        assert_matches_type(ConfigRetrieveResponse, config, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Arbi) -> None:
        response = client.api.configs.with_raw_response.retrieve(
            "config_ext_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        config = response.parse()
        assert_matches_type(ConfigRetrieveResponse, config, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Arbi) -> None:
        with client.api.configs.with_streaming_response.retrieve(
            "config_ext_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            config = response.parse()
            assert_matches_type(ConfigRetrieveResponse, config, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Arbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `config_ext_id` but received ''"):
            client.api.configs.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Arbi) -> None:
        config = client.api.configs.delete(
            "config_ext_id",
        )
        assert_matches_type(ConfigDeleteResponse, config, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Arbi) -> None:
        response = client.api.configs.with_raw_response.delete(
            "config_ext_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        config = response.parse()
        assert_matches_type(ConfigDeleteResponse, config, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Arbi) -> None:
        with client.api.configs.with_streaming_response.delete(
            "config_ext_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            config = response.parse()
            assert_matches_type(ConfigDeleteResponse, config, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: Arbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `config_ext_id` but received ''"):
            client.api.configs.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_schema(self, client: Arbi) -> None:
        config = client.api.configs.get_schema()
        assert_matches_type(object, config, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_schema(self, client: Arbi) -> None:
        response = client.api.configs.with_raw_response.get_schema()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        config = response.parse()
        assert_matches_type(object, config, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_schema(self, client: Arbi) -> None:
        with client.api.configs.with_streaming_response.get_schema() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            config = response.parse()
            assert_matches_type(object, config, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_versions(self, client: Arbi) -> None:
        config = client.api.configs.get_versions()
        assert_matches_type(ConfigGetVersionsResponse, config, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_versions(self, client: Arbi) -> None:
        response = client.api.configs.with_raw_response.get_versions()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        config = response.parse()
        assert_matches_type(ConfigGetVersionsResponse, config, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_versions(self, client: Arbi) -> None:
        with client.api.configs.with_streaming_response.get_versions() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            config = response.parse()
            assert_matches_type(ConfigGetVersionsResponse, config, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncConfigs:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncArbi) -> None:
        config = await async_client.api.configs.create()
        assert_matches_type(ConfigCreateResponse, config, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncArbi) -> None:
        config = await async_client.api.configs.create(
            agent_llm={
                "api_type": "local",
                "enabled": True,
                "max_char_size_to_answer": 0,
                "max_context_tokens": 1000,
                "max_iterations": 0,
                "max_tokens": 0,
                "model_name": "MODEL_NAME",
                "show_interim_steps": True,
                "system_instruction": "SYSTEM_INSTRUCTION",
                "temperature": 0,
            },
            agents={
                "agent_model_name": "AGENT_MODEL_NAME",
                "agent_prompt": "AGENT_PROMPT",
                "enabled": True,
                "llm_agent_temperature": 0,
                "llm_page_filter_model_name": "LLM_PAGE_FILTER_MODEL_NAME",
                "llm_page_filter_prompt": "LLM_PAGE_FILTER_PROMPT",
                "llm_page_filter_temperature": 0,
                "llm_summarise_model_name": "LLM_SUMMARISE_MODEL_NAME",
                "llm_summarise_prompt": "LLM_SUMMARISE_PROMPT",
                "llm_summarise_temperature": 0,
            },
            chunker={},
            document_date_extractor_llm={
                "api_type": "local",
                "max_char_context_to_answer": 0,
                "max_tokens": 0,
                "model_name": "MODEL_NAME",
                "system_instruction": "SYSTEM_INSTRUCTION",
                "temperature": 0,
            },
            embedder={
                "api_type": "local",
                "batch_size": 0,
                "embed_prefix": "EMBED_PREFIX",
                "max_concurrent_requests": 0,
                "model_name": "MODEL_NAME",
                "query_prefix": "QUERY_PREFIX",
            },
            model_citation={
                "max_numb_citations": 0,
                "min_char_size_to_answer": 0,
                "sim_model_name": "SIM_MODEL_NAME",
                "sim_threashold": 0,
            },
            parent_message_ext_id="parent_message_ext_id",
            parser={},
            query_llm={
                "api_type": "local",
                "max_char_size_to_answer": 0,
                "max_tokens": 0,
                "model_name": "MODEL_NAME",
                "system_instruction": "SYSTEM_INSTRUCTION",
                "temperature": 0,
            },
            reranker={
                "api_type": "local",
                "max_numb_of_chunks": 1,
                "model_name": "MODEL_NAME",
            },
            retriever={
                "group_size": 1000,
                "max_distinct_documents": 100,
                "max_total_chunks_to_retrieve": 100,
                "min_retrieval_sim_score": 0,
            },
            title="title",
            title_llm={
                "api_type": "local",
                "max_char_size_to_answer": 0,
                "max_tokens": 0,
                "model_name": "MODEL_NAME",
                "system_instruction": "SYSTEM_INSTRUCTION",
                "temperature": 0,
            },
        )
        assert_matches_type(ConfigCreateResponse, config, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.configs.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        config = await response.parse()
        assert_matches_type(ConfigCreateResponse, config, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncArbi) -> None:
        async with async_client.api.configs.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            config = await response.parse()
            assert_matches_type(ConfigCreateResponse, config, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncArbi) -> None:
        config = await async_client.api.configs.retrieve(
            "config_ext_id",
        )
        assert_matches_type(ConfigRetrieveResponse, config, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.configs.with_raw_response.retrieve(
            "config_ext_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        config = await response.parse()
        assert_matches_type(ConfigRetrieveResponse, config, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncArbi) -> None:
        async with async_client.api.configs.with_streaming_response.retrieve(
            "config_ext_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            config = await response.parse()
            assert_matches_type(ConfigRetrieveResponse, config, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncArbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `config_ext_id` but received ''"):
            await async_client.api.configs.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncArbi) -> None:
        config = await async_client.api.configs.delete(
            "config_ext_id",
        )
        assert_matches_type(ConfigDeleteResponse, config, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.configs.with_raw_response.delete(
            "config_ext_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        config = await response.parse()
        assert_matches_type(ConfigDeleteResponse, config, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncArbi) -> None:
        async with async_client.api.configs.with_streaming_response.delete(
            "config_ext_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            config = await response.parse()
            assert_matches_type(ConfigDeleteResponse, config, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncArbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `config_ext_id` but received ''"):
            await async_client.api.configs.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_schema(self, async_client: AsyncArbi) -> None:
        config = await async_client.api.configs.get_schema()
        assert_matches_type(object, config, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_schema(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.configs.with_raw_response.get_schema()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        config = await response.parse()
        assert_matches_type(object, config, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_schema(self, async_client: AsyncArbi) -> None:
        async with async_client.api.configs.with_streaming_response.get_schema() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            config = await response.parse()
            assert_matches_type(object, config, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_versions(self, async_client: AsyncArbi) -> None:
        config = await async_client.api.configs.get_versions()
        assert_matches_type(ConfigGetVersionsResponse, config, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_versions(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.configs.with_raw_response.get_versions()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        config = await response.parse()
        assert_matches_type(ConfigGetVersionsResponse, config, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_versions(self, async_client: AsyncArbi) -> None:
        async with async_client.api.configs.with_streaming_response.get_versions() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            config = await response.parse()
            assert_matches_type(ConfigGetVersionsResponse, config, path=["response"])

        assert cast(Any, response.is_closed) is True
