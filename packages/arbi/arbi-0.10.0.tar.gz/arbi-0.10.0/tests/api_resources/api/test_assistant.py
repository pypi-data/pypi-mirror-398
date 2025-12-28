# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from arbi import Arbi, AsyncArbi
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestAssistant:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Arbi) -> None:
        assistant = client.api.assistant.retrieve(
            content="content",
            workspace_ext_id="wrk-bFXA5r3A",
        )
        assert_matches_type(object, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_with_all_params(self, client: Arbi) -> None:
        assistant = client.api.assistant.retrieve(
            content="content",
            workspace_ext_id="wrk-bFXA5r3A",
            config_ext_id="config_ext_id",
            parent_message_ext_id="parent_message_ext_id",
            tools={
                "foo": {
                    "description": "description",
                    "name": "model_citation",
                    "tool_responses": {
                        "foo": {
                            "chunk_ids": ["string"],
                            "offset_end": 0,
                            "offset_start": 0,
                            "statement": "statement",
                        }
                    },
                }
            },
            workspace_key="workspace-key",
        )
        assert_matches_type(object, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Arbi) -> None:
        response = client.api.assistant.with_raw_response.retrieve(
            content="content",
            workspace_ext_id="wrk-bFXA5r3A",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        assistant = response.parse()
        assert_matches_type(object, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Arbi) -> None:
        with client.api.assistant.with_streaming_response.retrieve(
            content="content",
            workspace_ext_id="wrk-bFXA5r3A",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            assistant = response.parse()
            assert_matches_type(object, assistant, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_query(self, client: Arbi) -> None:
        assistant = client.api.assistant.query(
            content="content",
            workspace_ext_id="wrk-bFXA5r3A",
        )
        assert_matches_type(object, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_query_with_all_params(self, client: Arbi) -> None:
        assistant = client.api.assistant.query(
            content="content",
            workspace_ext_id="wrk-bFXA5r3A",
            config_ext_id="config_ext_id",
            parent_message_ext_id="parent_message_ext_id",
            tools={
                "foo": {
                    "description": "description",
                    "name": "model_citation",
                    "tool_responses": {
                        "foo": {
                            "chunk_ids": ["string"],
                            "offset_end": 0,
                            "offset_start": 0,
                            "statement": "statement",
                        }
                    },
                }
            },
            workspace_key="workspace-key",
        )
        assert_matches_type(object, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_query(self, client: Arbi) -> None:
        response = client.api.assistant.with_raw_response.query(
            content="content",
            workspace_ext_id="wrk-bFXA5r3A",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        assistant = response.parse()
        assert_matches_type(object, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_query(self, client: Arbi) -> None:
        with client.api.assistant.with_streaming_response.query(
            content="content",
            workspace_ext_id="wrk-bFXA5r3A",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            assistant = response.parse()
            assert_matches_type(object, assistant, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncAssistant:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncArbi) -> None:
        assistant = await async_client.api.assistant.retrieve(
            content="content",
            workspace_ext_id="wrk-bFXA5r3A",
        )
        assert_matches_type(object, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_with_all_params(self, async_client: AsyncArbi) -> None:
        assistant = await async_client.api.assistant.retrieve(
            content="content",
            workspace_ext_id="wrk-bFXA5r3A",
            config_ext_id="config_ext_id",
            parent_message_ext_id="parent_message_ext_id",
            tools={
                "foo": {
                    "description": "description",
                    "name": "model_citation",
                    "tool_responses": {
                        "foo": {
                            "chunk_ids": ["string"],
                            "offset_end": 0,
                            "offset_start": 0,
                            "statement": "statement",
                        }
                    },
                }
            },
            workspace_key="workspace-key",
        )
        assert_matches_type(object, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.assistant.with_raw_response.retrieve(
            content="content",
            workspace_ext_id="wrk-bFXA5r3A",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        assistant = await response.parse()
        assert_matches_type(object, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncArbi) -> None:
        async with async_client.api.assistant.with_streaming_response.retrieve(
            content="content",
            workspace_ext_id="wrk-bFXA5r3A",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            assistant = await response.parse()
            assert_matches_type(object, assistant, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_query(self, async_client: AsyncArbi) -> None:
        assistant = await async_client.api.assistant.query(
            content="content",
            workspace_ext_id="wrk-bFXA5r3A",
        )
        assert_matches_type(object, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_query_with_all_params(self, async_client: AsyncArbi) -> None:
        assistant = await async_client.api.assistant.query(
            content="content",
            workspace_ext_id="wrk-bFXA5r3A",
            config_ext_id="config_ext_id",
            parent_message_ext_id="parent_message_ext_id",
            tools={
                "foo": {
                    "description": "description",
                    "name": "model_citation",
                    "tool_responses": {
                        "foo": {
                            "chunk_ids": ["string"],
                            "offset_end": 0,
                            "offset_start": 0,
                            "statement": "statement",
                        }
                    },
                }
            },
            workspace_key="workspace-key",
        )
        assert_matches_type(object, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_query(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.assistant.with_raw_response.query(
            content="content",
            workspace_ext_id="wrk-bFXA5r3A",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        assistant = await response.parse()
        assert_matches_type(object, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_query(self, async_client: AsyncArbi) -> None:
        async with async_client.api.assistant.with_streaming_response.query(
            content="content",
            workspace_ext_id="wrk-bFXA5r3A",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            assistant = await response.parse()
            assert_matches_type(object, assistant, path=["response"])

        assert cast(Any, response.is_closed) is True
