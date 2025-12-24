# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from arbi import Arbi, AsyncArbi
from tests.utils import assert_matches_type
from arbi.types.api import (
    ConversationShareResponse,
    ConversationDeleteResponse,
    ConversationUpdateTitleResponse,
    ConversationDeleteMessageResponse,
    ConversationRetrieveMessageResponse,
    ConversationRetrieveThreadsResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestConversation:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Arbi) -> None:
        conversation = client.api.conversation.delete(
            "con",
        )
        assert_matches_type(ConversationDeleteResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Arbi) -> None:
        response = client.api.conversation.with_raw_response.delete(
            "con",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        conversation = response.parse()
        assert_matches_type(ConversationDeleteResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Arbi) -> None:
        with client.api.conversation.with_streaming_response.delete(
            "con",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            conversation = response.parse()
            assert_matches_type(ConversationDeleteResponse, conversation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: Arbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `conversation_ext_id` but received ''"):
            client.api.conversation.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete_message(self, client: Arbi) -> None:
        conversation = client.api.conversation.delete_message(
            "msg",
        )
        assert_matches_type(ConversationDeleteMessageResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete_message(self, client: Arbi) -> None:
        response = client.api.conversation.with_raw_response.delete_message(
            "msg",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        conversation = response.parse()
        assert_matches_type(ConversationDeleteMessageResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete_message(self, client: Arbi) -> None:
        with client.api.conversation.with_streaming_response.delete_message(
            "msg",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            conversation = response.parse()
            assert_matches_type(ConversationDeleteMessageResponse, conversation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete_message(self, client: Arbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `message_ext_id` but received ''"):
            client.api.conversation.with_raw_response.delete_message(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_message(self, client: Arbi) -> None:
        conversation = client.api.conversation.retrieve_message(
            message_ext_id="msg",
        )
        assert_matches_type(ConversationRetrieveMessageResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_message_with_all_params(self, client: Arbi) -> None:
        conversation = client.api.conversation.retrieve_message(
            message_ext_id="msg",
            workspace_key="workspace-key",
        )
        assert_matches_type(ConversationRetrieveMessageResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_message(self, client: Arbi) -> None:
        response = client.api.conversation.with_raw_response.retrieve_message(
            message_ext_id="msg",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        conversation = response.parse()
        assert_matches_type(ConversationRetrieveMessageResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_message(self, client: Arbi) -> None:
        with client.api.conversation.with_streaming_response.retrieve_message(
            message_ext_id="msg",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            conversation = response.parse()
            assert_matches_type(ConversationRetrieveMessageResponse, conversation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve_message(self, client: Arbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `message_ext_id` but received ''"):
            client.api.conversation.with_raw_response.retrieve_message(
                message_ext_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_threads(self, client: Arbi) -> None:
        conversation = client.api.conversation.retrieve_threads(
            conversation_ext_id="con",
        )
        assert_matches_type(ConversationRetrieveThreadsResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_threads_with_all_params(self, client: Arbi) -> None:
        conversation = client.api.conversation.retrieve_threads(
            conversation_ext_id="con",
            workspace_key="workspace-key",
        )
        assert_matches_type(ConversationRetrieveThreadsResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_threads(self, client: Arbi) -> None:
        response = client.api.conversation.with_raw_response.retrieve_threads(
            conversation_ext_id="con",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        conversation = response.parse()
        assert_matches_type(ConversationRetrieveThreadsResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_threads(self, client: Arbi) -> None:
        with client.api.conversation.with_streaming_response.retrieve_threads(
            conversation_ext_id="con",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            conversation = response.parse()
            assert_matches_type(ConversationRetrieveThreadsResponse, conversation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve_threads(self, client: Arbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `conversation_ext_id` but received ''"):
            client.api.conversation.with_raw_response.retrieve_threads(
                conversation_ext_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_share(self, client: Arbi) -> None:
        conversation = client.api.conversation.share(
            "con",
        )
        assert_matches_type(ConversationShareResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_share(self, client: Arbi) -> None:
        response = client.api.conversation.with_raw_response.share(
            "con",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        conversation = response.parse()
        assert_matches_type(ConversationShareResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_share(self, client: Arbi) -> None:
        with client.api.conversation.with_streaming_response.share(
            "con",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            conversation = response.parse()
            assert_matches_type(ConversationShareResponse, conversation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_share(self, client: Arbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `conversation_ext_id` but received ''"):
            client.api.conversation.with_raw_response.share(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_title(self, client: Arbi) -> None:
        conversation = client.api.conversation.update_title(
            conversation_ext_id="con",
            title="x",
        )
        assert_matches_type(ConversationUpdateTitleResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_title_with_all_params(self, client: Arbi) -> None:
        conversation = client.api.conversation.update_title(
            conversation_ext_id="con",
            title="x",
            workspace_key="workspace-key",
        )
        assert_matches_type(ConversationUpdateTitleResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update_title(self, client: Arbi) -> None:
        response = client.api.conversation.with_raw_response.update_title(
            conversation_ext_id="con",
            title="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        conversation = response.parse()
        assert_matches_type(ConversationUpdateTitleResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update_title(self, client: Arbi) -> None:
        with client.api.conversation.with_streaming_response.update_title(
            conversation_ext_id="con",
            title="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            conversation = response.parse()
            assert_matches_type(ConversationUpdateTitleResponse, conversation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update_title(self, client: Arbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `conversation_ext_id` but received ''"):
            client.api.conversation.with_raw_response.update_title(
                conversation_ext_id="",
                title="x",
            )


class TestAsyncConversation:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncArbi) -> None:
        conversation = await async_client.api.conversation.delete(
            "con",
        )
        assert_matches_type(ConversationDeleteResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.conversation.with_raw_response.delete(
            "con",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        conversation = await response.parse()
        assert_matches_type(ConversationDeleteResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncArbi) -> None:
        async with async_client.api.conversation.with_streaming_response.delete(
            "con",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            conversation = await response.parse()
            assert_matches_type(ConversationDeleteResponse, conversation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncArbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `conversation_ext_id` but received ''"):
            await async_client.api.conversation.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete_message(self, async_client: AsyncArbi) -> None:
        conversation = await async_client.api.conversation.delete_message(
            "msg",
        )
        assert_matches_type(ConversationDeleteMessageResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete_message(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.conversation.with_raw_response.delete_message(
            "msg",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        conversation = await response.parse()
        assert_matches_type(ConversationDeleteMessageResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete_message(self, async_client: AsyncArbi) -> None:
        async with async_client.api.conversation.with_streaming_response.delete_message(
            "msg",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            conversation = await response.parse()
            assert_matches_type(ConversationDeleteMessageResponse, conversation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete_message(self, async_client: AsyncArbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `message_ext_id` but received ''"):
            await async_client.api.conversation.with_raw_response.delete_message(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_message(self, async_client: AsyncArbi) -> None:
        conversation = await async_client.api.conversation.retrieve_message(
            message_ext_id="msg",
        )
        assert_matches_type(ConversationRetrieveMessageResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_message_with_all_params(self, async_client: AsyncArbi) -> None:
        conversation = await async_client.api.conversation.retrieve_message(
            message_ext_id="msg",
            workspace_key="workspace-key",
        )
        assert_matches_type(ConversationRetrieveMessageResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_message(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.conversation.with_raw_response.retrieve_message(
            message_ext_id="msg",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        conversation = await response.parse()
        assert_matches_type(ConversationRetrieveMessageResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_message(self, async_client: AsyncArbi) -> None:
        async with async_client.api.conversation.with_streaming_response.retrieve_message(
            message_ext_id="msg",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            conversation = await response.parse()
            assert_matches_type(ConversationRetrieveMessageResponse, conversation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve_message(self, async_client: AsyncArbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `message_ext_id` but received ''"):
            await async_client.api.conversation.with_raw_response.retrieve_message(
                message_ext_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_threads(self, async_client: AsyncArbi) -> None:
        conversation = await async_client.api.conversation.retrieve_threads(
            conversation_ext_id="con",
        )
        assert_matches_type(ConversationRetrieveThreadsResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_threads_with_all_params(self, async_client: AsyncArbi) -> None:
        conversation = await async_client.api.conversation.retrieve_threads(
            conversation_ext_id="con",
            workspace_key="workspace-key",
        )
        assert_matches_type(ConversationRetrieveThreadsResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_threads(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.conversation.with_raw_response.retrieve_threads(
            conversation_ext_id="con",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        conversation = await response.parse()
        assert_matches_type(ConversationRetrieveThreadsResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_threads(self, async_client: AsyncArbi) -> None:
        async with async_client.api.conversation.with_streaming_response.retrieve_threads(
            conversation_ext_id="con",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            conversation = await response.parse()
            assert_matches_type(ConversationRetrieveThreadsResponse, conversation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve_threads(self, async_client: AsyncArbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `conversation_ext_id` but received ''"):
            await async_client.api.conversation.with_raw_response.retrieve_threads(
                conversation_ext_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_share(self, async_client: AsyncArbi) -> None:
        conversation = await async_client.api.conversation.share(
            "con",
        )
        assert_matches_type(ConversationShareResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_share(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.conversation.with_raw_response.share(
            "con",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        conversation = await response.parse()
        assert_matches_type(ConversationShareResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_share(self, async_client: AsyncArbi) -> None:
        async with async_client.api.conversation.with_streaming_response.share(
            "con",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            conversation = await response.parse()
            assert_matches_type(ConversationShareResponse, conversation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_share(self, async_client: AsyncArbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `conversation_ext_id` but received ''"):
            await async_client.api.conversation.with_raw_response.share(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_title(self, async_client: AsyncArbi) -> None:
        conversation = await async_client.api.conversation.update_title(
            conversation_ext_id="con",
            title="x",
        )
        assert_matches_type(ConversationUpdateTitleResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_title_with_all_params(self, async_client: AsyncArbi) -> None:
        conversation = await async_client.api.conversation.update_title(
            conversation_ext_id="con",
            title="x",
            workspace_key="workspace-key",
        )
        assert_matches_type(ConversationUpdateTitleResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update_title(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.conversation.with_raw_response.update_title(
            conversation_ext_id="con",
            title="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        conversation = await response.parse()
        assert_matches_type(ConversationUpdateTitleResponse, conversation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update_title(self, async_client: AsyncArbi) -> None:
        async with async_client.api.conversation.with_streaming_response.update_title(
            conversation_ext_id="con",
            title="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            conversation = await response.parse()
            assert_matches_type(ConversationUpdateTitleResponse, conversation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update_title(self, async_client: AsyncArbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `conversation_ext_id` but received ''"):
            await async_client.api.conversation.with_raw_response.update_title(
                conversation_ext_id="",
                title="x",
            )
