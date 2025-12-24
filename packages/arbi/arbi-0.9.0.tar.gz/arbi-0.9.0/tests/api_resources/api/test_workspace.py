# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from arbi import Arbi, AsyncArbi
from tests.utils import assert_matches_type
from arbi.types.api import (
    WorkspaceResponse,
    WorkspaceCopyResponse,
    WorkspaceShareResponse,
    WorkspaceDeleteResponse,
    WorkspaceGetTagsResponse,
    WorkspaceGetStatsResponse,
    WorkspaceGetUsersResponse,
    WorkspaceRemoveUserResponse,
    WorkspaceGetDocumentsResponse,
    WorkspaceGetConversationsResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestWorkspace:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: Arbi) -> None:
        workspace = client.api.workspace.update(
            workspace_ext_id="wrk",
        )
        assert_matches_type(WorkspaceResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: Arbi) -> None:
        workspace = client.api.workspace.update(
            workspace_ext_id="wrk",
            description="description",
            is_public=True,
            name="name",
            workspace_key="workspace-key",
        )
        assert_matches_type(WorkspaceResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: Arbi) -> None:
        response = client.api.workspace.with_raw_response.update(
            workspace_ext_id="wrk",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        workspace = response.parse()
        assert_matches_type(WorkspaceResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: Arbi) -> None:
        with client.api.workspace.with_streaming_response.update(
            workspace_ext_id="wrk",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            workspace = response.parse()
            assert_matches_type(WorkspaceResponse, workspace, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: Arbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workspace_ext_id` but received ''"):
            client.api.workspace.with_raw_response.update(
                workspace_ext_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Arbi) -> None:
        workspace = client.api.workspace.delete(
            "wrk",
        )
        assert_matches_type(WorkspaceDeleteResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Arbi) -> None:
        response = client.api.workspace.with_raw_response.delete(
            "wrk",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        workspace = response.parse()
        assert_matches_type(WorkspaceDeleteResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Arbi) -> None:
        with client.api.workspace.with_streaming_response.delete(
            "wrk",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            workspace = response.parse()
            assert_matches_type(WorkspaceDeleteResponse, workspace, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: Arbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workspace_ext_id` but received ''"):
            client.api.workspace.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_copy(self, client: Arbi) -> None:
        workspace = client.api.workspace.copy(
            workspace_ext_id="wrk",
            items=["string"],
            target_workspace_ext_id="wrk-bFXA5r3A",
        )
        assert_matches_type(WorkspaceCopyResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_copy_with_all_params(self, client: Arbi) -> None:
        workspace = client.api.workspace.copy(
            workspace_ext_id="wrk",
            items=["string"],
            target_workspace_ext_id="wrk-bFXA5r3A",
            target_workspace_key="target-workspace-key",
            workspace_key="workspace-key",
        )
        assert_matches_type(WorkspaceCopyResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_copy(self, client: Arbi) -> None:
        response = client.api.workspace.with_raw_response.copy(
            workspace_ext_id="wrk",
            items=["string"],
            target_workspace_ext_id="wrk-bFXA5r3A",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        workspace = response.parse()
        assert_matches_type(WorkspaceCopyResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_copy(self, client: Arbi) -> None:
        with client.api.workspace.with_streaming_response.copy(
            workspace_ext_id="wrk",
            items=["string"],
            target_workspace_ext_id="wrk-bFXA5r3A",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            workspace = response.parse()
            assert_matches_type(WorkspaceCopyResponse, workspace, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_copy(self, client: Arbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workspace_ext_id` but received ''"):
            client.api.workspace.with_raw_response.copy(
                workspace_ext_id="",
                items=["string"],
                target_workspace_ext_id="wrk-bFXA5r3A",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_protected(self, client: Arbi) -> None:
        workspace = client.api.workspace.create_protected(
            name="name",
        )
        assert_matches_type(WorkspaceResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_protected_with_all_params(self, client: Arbi) -> None:
        workspace = client.api.workspace.create_protected(
            name="name",
            description="description",
            is_public=True,
        )
        assert_matches_type(WorkspaceResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create_protected(self, client: Arbi) -> None:
        response = client.api.workspace.with_raw_response.create_protected(
            name="name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        workspace = response.parse()
        assert_matches_type(WorkspaceResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create_protected(self, client: Arbi) -> None:
        with client.api.workspace.with_streaming_response.create_protected(
            name="name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            workspace = response.parse()
            assert_matches_type(WorkspaceResponse, workspace, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_conversations(self, client: Arbi) -> None:
        workspace = client.api.workspace.get_conversations(
            workspace_ext_id="wrk",
        )
        assert_matches_type(WorkspaceGetConversationsResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_conversations_with_all_params(self, client: Arbi) -> None:
        workspace = client.api.workspace.get_conversations(
            workspace_ext_id="wrk",
            workspace_key="workspace-key",
        )
        assert_matches_type(WorkspaceGetConversationsResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_conversations(self, client: Arbi) -> None:
        response = client.api.workspace.with_raw_response.get_conversations(
            workspace_ext_id="wrk",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        workspace = response.parse()
        assert_matches_type(WorkspaceGetConversationsResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_conversations(self, client: Arbi) -> None:
        with client.api.workspace.with_streaming_response.get_conversations(
            workspace_ext_id="wrk",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            workspace = response.parse()
            assert_matches_type(WorkspaceGetConversationsResponse, workspace, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_get_conversations(self, client: Arbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workspace_ext_id` but received ''"):
            client.api.workspace.with_raw_response.get_conversations(
                workspace_ext_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_documents(self, client: Arbi) -> None:
        workspace = client.api.workspace.get_documents(
            workspace_ext_id="wrk",
        )
        assert_matches_type(WorkspaceGetDocumentsResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_documents_with_all_params(self, client: Arbi) -> None:
        workspace = client.api.workspace.get_documents(
            workspace_ext_id="wrk",
            workspace_key="workspace-key",
        )
        assert_matches_type(WorkspaceGetDocumentsResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_documents(self, client: Arbi) -> None:
        response = client.api.workspace.with_raw_response.get_documents(
            workspace_ext_id="wrk",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        workspace = response.parse()
        assert_matches_type(WorkspaceGetDocumentsResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_documents(self, client: Arbi) -> None:
        with client.api.workspace.with_streaming_response.get_documents(
            workspace_ext_id="wrk",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            workspace = response.parse()
            assert_matches_type(WorkspaceGetDocumentsResponse, workspace, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_get_documents(self, client: Arbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workspace_ext_id` but received ''"):
            client.api.workspace.with_raw_response.get_documents(
                workspace_ext_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_stats(self, client: Arbi) -> None:
        workspace = client.api.workspace.get_stats(
            "wrk",
        )
        assert_matches_type(WorkspaceGetStatsResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_stats(self, client: Arbi) -> None:
        response = client.api.workspace.with_raw_response.get_stats(
            "wrk",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        workspace = response.parse()
        assert_matches_type(WorkspaceGetStatsResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_stats(self, client: Arbi) -> None:
        with client.api.workspace.with_streaming_response.get_stats(
            "wrk",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            workspace = response.parse()
            assert_matches_type(WorkspaceGetStatsResponse, workspace, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_get_stats(self, client: Arbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workspace_ext_id` but received ''"):
            client.api.workspace.with_raw_response.get_stats(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_tags(self, client: Arbi) -> None:
        workspace = client.api.workspace.get_tags(
            workspace_ext_id="wrk",
        )
        assert_matches_type(WorkspaceGetTagsResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_tags_with_all_params(self, client: Arbi) -> None:
        workspace = client.api.workspace.get_tags(
            workspace_ext_id="wrk",
            workspace_key="workspace-key",
        )
        assert_matches_type(WorkspaceGetTagsResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_tags(self, client: Arbi) -> None:
        response = client.api.workspace.with_raw_response.get_tags(
            workspace_ext_id="wrk",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        workspace = response.parse()
        assert_matches_type(WorkspaceGetTagsResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_tags(self, client: Arbi) -> None:
        with client.api.workspace.with_streaming_response.get_tags(
            workspace_ext_id="wrk",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            workspace = response.parse()
            assert_matches_type(WorkspaceGetTagsResponse, workspace, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_get_tags(self, client: Arbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workspace_ext_id` but received ''"):
            client.api.workspace.with_raw_response.get_tags(
                workspace_ext_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_users(self, client: Arbi) -> None:
        workspace = client.api.workspace.get_users(
            "wrk",
        )
        assert_matches_type(WorkspaceGetUsersResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_users(self, client: Arbi) -> None:
        response = client.api.workspace.with_raw_response.get_users(
            "wrk",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        workspace = response.parse()
        assert_matches_type(WorkspaceGetUsersResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_users(self, client: Arbi) -> None:
        with client.api.workspace.with_streaming_response.get_users(
            "wrk",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            workspace = response.parse()
            assert_matches_type(WorkspaceGetUsersResponse, workspace, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_get_users(self, client: Arbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workspace_ext_id` but received ''"):
            client.api.workspace.with_raw_response.get_users(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_remove_user(self, client: Arbi) -> None:
        workspace = client.api.workspace.remove_user(
            workspace_ext_id="wrk",
            user_ext_id="usr-bFXA5r3A",
        )
        assert_matches_type(WorkspaceRemoveUserResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_remove_user(self, client: Arbi) -> None:
        response = client.api.workspace.with_raw_response.remove_user(
            workspace_ext_id="wrk",
            user_ext_id="usr-bFXA5r3A",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        workspace = response.parse()
        assert_matches_type(WorkspaceRemoveUserResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_remove_user(self, client: Arbi) -> None:
        with client.api.workspace.with_streaming_response.remove_user(
            workspace_ext_id="wrk",
            user_ext_id="usr-bFXA5r3A",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            workspace = response.parse()
            assert_matches_type(WorkspaceRemoveUserResponse, workspace, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_remove_user(self, client: Arbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workspace_ext_id` but received ''"):
            client.api.workspace.with_raw_response.remove_user(
                workspace_ext_id="",
                user_ext_id="usr-bFXA5r3A",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_share(self, client: Arbi) -> None:
        workspace = client.api.workspace.share(
            workspace_ext_id="wrk",
            recipient_email="recipient_email",
        )
        assert_matches_type(WorkspaceShareResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_share_with_all_params(self, client: Arbi) -> None:
        workspace = client.api.workspace.share(
            workspace_ext_id="wrk",
            recipient_email="recipient_email",
            workspace_key="workspace-key",
        )
        assert_matches_type(WorkspaceShareResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_share(self, client: Arbi) -> None:
        response = client.api.workspace.with_raw_response.share(
            workspace_ext_id="wrk",
            recipient_email="recipient_email",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        workspace = response.parse()
        assert_matches_type(WorkspaceShareResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_share(self, client: Arbi) -> None:
        with client.api.workspace.with_streaming_response.share(
            workspace_ext_id="wrk",
            recipient_email="recipient_email",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            workspace = response.parse()
            assert_matches_type(WorkspaceShareResponse, workspace, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_share(self, client: Arbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workspace_ext_id` but received ''"):
            client.api.workspace.with_raw_response.share(
                workspace_ext_id="",
                recipient_email="recipient_email",
            )


class TestAsyncWorkspace:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncArbi) -> None:
        workspace = await async_client.api.workspace.update(
            workspace_ext_id="wrk",
        )
        assert_matches_type(WorkspaceResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncArbi) -> None:
        workspace = await async_client.api.workspace.update(
            workspace_ext_id="wrk",
            description="description",
            is_public=True,
            name="name",
            workspace_key="workspace-key",
        )
        assert_matches_type(WorkspaceResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.workspace.with_raw_response.update(
            workspace_ext_id="wrk",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        workspace = await response.parse()
        assert_matches_type(WorkspaceResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncArbi) -> None:
        async with async_client.api.workspace.with_streaming_response.update(
            workspace_ext_id="wrk",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            workspace = await response.parse()
            assert_matches_type(WorkspaceResponse, workspace, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncArbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workspace_ext_id` but received ''"):
            await async_client.api.workspace.with_raw_response.update(
                workspace_ext_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncArbi) -> None:
        workspace = await async_client.api.workspace.delete(
            "wrk",
        )
        assert_matches_type(WorkspaceDeleteResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.workspace.with_raw_response.delete(
            "wrk",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        workspace = await response.parse()
        assert_matches_type(WorkspaceDeleteResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncArbi) -> None:
        async with async_client.api.workspace.with_streaming_response.delete(
            "wrk",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            workspace = await response.parse()
            assert_matches_type(WorkspaceDeleteResponse, workspace, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncArbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workspace_ext_id` but received ''"):
            await async_client.api.workspace.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_copy(self, async_client: AsyncArbi) -> None:
        workspace = await async_client.api.workspace.copy(
            workspace_ext_id="wrk",
            items=["string"],
            target_workspace_ext_id="wrk-bFXA5r3A",
        )
        assert_matches_type(WorkspaceCopyResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_copy_with_all_params(self, async_client: AsyncArbi) -> None:
        workspace = await async_client.api.workspace.copy(
            workspace_ext_id="wrk",
            items=["string"],
            target_workspace_ext_id="wrk-bFXA5r3A",
            target_workspace_key="target-workspace-key",
            workspace_key="workspace-key",
        )
        assert_matches_type(WorkspaceCopyResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_copy(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.workspace.with_raw_response.copy(
            workspace_ext_id="wrk",
            items=["string"],
            target_workspace_ext_id="wrk-bFXA5r3A",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        workspace = await response.parse()
        assert_matches_type(WorkspaceCopyResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_copy(self, async_client: AsyncArbi) -> None:
        async with async_client.api.workspace.with_streaming_response.copy(
            workspace_ext_id="wrk",
            items=["string"],
            target_workspace_ext_id="wrk-bFXA5r3A",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            workspace = await response.parse()
            assert_matches_type(WorkspaceCopyResponse, workspace, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_copy(self, async_client: AsyncArbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workspace_ext_id` but received ''"):
            await async_client.api.workspace.with_raw_response.copy(
                workspace_ext_id="",
                items=["string"],
                target_workspace_ext_id="wrk-bFXA5r3A",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_protected(self, async_client: AsyncArbi) -> None:
        workspace = await async_client.api.workspace.create_protected(
            name="name",
        )
        assert_matches_type(WorkspaceResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_protected_with_all_params(self, async_client: AsyncArbi) -> None:
        workspace = await async_client.api.workspace.create_protected(
            name="name",
            description="description",
            is_public=True,
        )
        assert_matches_type(WorkspaceResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create_protected(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.workspace.with_raw_response.create_protected(
            name="name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        workspace = await response.parse()
        assert_matches_type(WorkspaceResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create_protected(self, async_client: AsyncArbi) -> None:
        async with async_client.api.workspace.with_streaming_response.create_protected(
            name="name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            workspace = await response.parse()
            assert_matches_type(WorkspaceResponse, workspace, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_conversations(self, async_client: AsyncArbi) -> None:
        workspace = await async_client.api.workspace.get_conversations(
            workspace_ext_id="wrk",
        )
        assert_matches_type(WorkspaceGetConversationsResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_conversations_with_all_params(self, async_client: AsyncArbi) -> None:
        workspace = await async_client.api.workspace.get_conversations(
            workspace_ext_id="wrk",
            workspace_key="workspace-key",
        )
        assert_matches_type(WorkspaceGetConversationsResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_conversations(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.workspace.with_raw_response.get_conversations(
            workspace_ext_id="wrk",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        workspace = await response.parse()
        assert_matches_type(WorkspaceGetConversationsResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_conversations(self, async_client: AsyncArbi) -> None:
        async with async_client.api.workspace.with_streaming_response.get_conversations(
            workspace_ext_id="wrk",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            workspace = await response.parse()
            assert_matches_type(WorkspaceGetConversationsResponse, workspace, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_get_conversations(self, async_client: AsyncArbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workspace_ext_id` but received ''"):
            await async_client.api.workspace.with_raw_response.get_conversations(
                workspace_ext_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_documents(self, async_client: AsyncArbi) -> None:
        workspace = await async_client.api.workspace.get_documents(
            workspace_ext_id="wrk",
        )
        assert_matches_type(WorkspaceGetDocumentsResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_documents_with_all_params(self, async_client: AsyncArbi) -> None:
        workspace = await async_client.api.workspace.get_documents(
            workspace_ext_id="wrk",
            workspace_key="workspace-key",
        )
        assert_matches_type(WorkspaceGetDocumentsResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_documents(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.workspace.with_raw_response.get_documents(
            workspace_ext_id="wrk",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        workspace = await response.parse()
        assert_matches_type(WorkspaceGetDocumentsResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_documents(self, async_client: AsyncArbi) -> None:
        async with async_client.api.workspace.with_streaming_response.get_documents(
            workspace_ext_id="wrk",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            workspace = await response.parse()
            assert_matches_type(WorkspaceGetDocumentsResponse, workspace, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_get_documents(self, async_client: AsyncArbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workspace_ext_id` but received ''"):
            await async_client.api.workspace.with_raw_response.get_documents(
                workspace_ext_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_stats(self, async_client: AsyncArbi) -> None:
        workspace = await async_client.api.workspace.get_stats(
            "wrk",
        )
        assert_matches_type(WorkspaceGetStatsResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_stats(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.workspace.with_raw_response.get_stats(
            "wrk",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        workspace = await response.parse()
        assert_matches_type(WorkspaceGetStatsResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_stats(self, async_client: AsyncArbi) -> None:
        async with async_client.api.workspace.with_streaming_response.get_stats(
            "wrk",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            workspace = await response.parse()
            assert_matches_type(WorkspaceGetStatsResponse, workspace, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_get_stats(self, async_client: AsyncArbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workspace_ext_id` but received ''"):
            await async_client.api.workspace.with_raw_response.get_stats(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_tags(self, async_client: AsyncArbi) -> None:
        workspace = await async_client.api.workspace.get_tags(
            workspace_ext_id="wrk",
        )
        assert_matches_type(WorkspaceGetTagsResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_tags_with_all_params(self, async_client: AsyncArbi) -> None:
        workspace = await async_client.api.workspace.get_tags(
            workspace_ext_id="wrk",
            workspace_key="workspace-key",
        )
        assert_matches_type(WorkspaceGetTagsResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_tags(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.workspace.with_raw_response.get_tags(
            workspace_ext_id="wrk",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        workspace = await response.parse()
        assert_matches_type(WorkspaceGetTagsResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_tags(self, async_client: AsyncArbi) -> None:
        async with async_client.api.workspace.with_streaming_response.get_tags(
            workspace_ext_id="wrk",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            workspace = await response.parse()
            assert_matches_type(WorkspaceGetTagsResponse, workspace, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_get_tags(self, async_client: AsyncArbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workspace_ext_id` but received ''"):
            await async_client.api.workspace.with_raw_response.get_tags(
                workspace_ext_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_users(self, async_client: AsyncArbi) -> None:
        workspace = await async_client.api.workspace.get_users(
            "wrk",
        )
        assert_matches_type(WorkspaceGetUsersResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_users(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.workspace.with_raw_response.get_users(
            "wrk",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        workspace = await response.parse()
        assert_matches_type(WorkspaceGetUsersResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_users(self, async_client: AsyncArbi) -> None:
        async with async_client.api.workspace.with_streaming_response.get_users(
            "wrk",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            workspace = await response.parse()
            assert_matches_type(WorkspaceGetUsersResponse, workspace, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_get_users(self, async_client: AsyncArbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workspace_ext_id` but received ''"):
            await async_client.api.workspace.with_raw_response.get_users(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_remove_user(self, async_client: AsyncArbi) -> None:
        workspace = await async_client.api.workspace.remove_user(
            workspace_ext_id="wrk",
            user_ext_id="usr-bFXA5r3A",
        )
        assert_matches_type(WorkspaceRemoveUserResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_remove_user(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.workspace.with_raw_response.remove_user(
            workspace_ext_id="wrk",
            user_ext_id="usr-bFXA5r3A",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        workspace = await response.parse()
        assert_matches_type(WorkspaceRemoveUserResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_remove_user(self, async_client: AsyncArbi) -> None:
        async with async_client.api.workspace.with_streaming_response.remove_user(
            workspace_ext_id="wrk",
            user_ext_id="usr-bFXA5r3A",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            workspace = await response.parse()
            assert_matches_type(WorkspaceRemoveUserResponse, workspace, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_remove_user(self, async_client: AsyncArbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workspace_ext_id` but received ''"):
            await async_client.api.workspace.with_raw_response.remove_user(
                workspace_ext_id="",
                user_ext_id="usr-bFXA5r3A",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_share(self, async_client: AsyncArbi) -> None:
        workspace = await async_client.api.workspace.share(
            workspace_ext_id="wrk",
            recipient_email="recipient_email",
        )
        assert_matches_type(WorkspaceShareResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_share_with_all_params(self, async_client: AsyncArbi) -> None:
        workspace = await async_client.api.workspace.share(
            workspace_ext_id="wrk",
            recipient_email="recipient_email",
            workspace_key="workspace-key",
        )
        assert_matches_type(WorkspaceShareResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_share(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.workspace.with_raw_response.share(
            workspace_ext_id="wrk",
            recipient_email="recipient_email",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        workspace = await response.parse()
        assert_matches_type(WorkspaceShareResponse, workspace, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_share(self, async_client: AsyncArbi) -> None:
        async with async_client.api.workspace.with_streaming_response.share(
            workspace_ext_id="wrk",
            recipient_email="recipient_email",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            workspace = await response.parse()
            assert_matches_type(WorkspaceShareResponse, workspace, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_share(self, async_client: AsyncArbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workspace_ext_id` but received ''"):
            await async_client.api.workspace.with_raw_response.share(
                workspace_ext_id="",
                recipient_email="recipient_email",
            )
