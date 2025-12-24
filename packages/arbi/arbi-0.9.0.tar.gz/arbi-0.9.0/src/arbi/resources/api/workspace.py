# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ..._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from ..._utils import maybe_transform, strip_not_given, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...types.api import (
    workspace_copy_params,
    workspace_share_params,
    workspace_update_params,
    workspace_remove_user_params,
    workspace_create_protected_params,
)
from ..._base_client import make_request_options
from ...types.api.workspace_response import WorkspaceResponse
from ...types.api.workspace_copy_response import WorkspaceCopyResponse
from ...types.api.workspace_share_response import WorkspaceShareResponse
from ...types.api.workspace_delete_response import WorkspaceDeleteResponse
from ...types.api.workspace_get_tags_response import WorkspaceGetTagsResponse
from ...types.api.workspace_get_stats_response import WorkspaceGetStatsResponse
from ...types.api.workspace_get_users_response import WorkspaceGetUsersResponse
from ...types.api.workspace_remove_user_response import WorkspaceRemoveUserResponse
from ...types.api.workspace_get_documents_response import WorkspaceGetDocumentsResponse
from ...types.api.workspace_get_conversations_response import WorkspaceGetConversationsResponse

__all__ = ["WorkspaceResource", "AsyncWorkspaceResource"]


class WorkspaceResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> WorkspaceResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#accessing-raw-response-data-eg-headers
        """
        return WorkspaceResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> WorkspaceResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#with_streaming_response
        """
        return WorkspaceResourceWithStreamingResponse(self)

    def update(
        self,
        workspace_ext_id: str,
        *,
        description: Optional[str] | Omit = omit,
        is_public: Optional[bool] | Omit = omit,
        name: Optional[str] | Omit = omit,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkspaceResponse:
        """Update workspace metadata such as name, description, or public status.

        Changes
        are persisted to the database.

        Only developers can change the is_public field. When making a workspace public,
        the backend uses the Workspace-Key header to get the workspace key.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workspace_ext_id:
            raise ValueError(f"Expected a non-empty value for `workspace_ext_id` but received {workspace_ext_id!r}")
        extra_headers = {**strip_not_given({"workspace-key": workspace_key}), **(extra_headers or {})}
        return self._patch(
            f"/api/workspace/{workspace_ext_id}",
            body=maybe_transform(
                {
                    "description": description,
                    "is_public": is_public,
                    "name": name,
                },
                workspace_update_params.WorkspaceUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkspaceResponse,
        )

    def delete(
        self,
        workspace_ext_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkspaceDeleteResponse:
        """Delete a workspace.

        Only the creator of the workspace is allowed to delete it.

        If the workspace
        deletion fails (e.g., due to RLS policy), the operation aborts.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workspace_ext_id:
            raise ValueError(f"Expected a non-empty value for `workspace_ext_id` but received {workspace_ext_id!r}")
        return self._delete(
            f"/api/workspace/{workspace_ext_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkspaceDeleteResponse,
        )

    def copy(
        self,
        workspace_ext_id: str,
        *,
        items: SequenceNotStr[str],
        target_workspace_ext_id: str,
        target_workspace_key: str | Omit = omit,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkspaceCopyResponse:
        """
        Copy documents from source workspace to target workspace.

        Requires:

        - User must have access to source workspace (RLS enforced)
        - Target workspace must exist and user must have access
        - Workspace-Key header with source workspace key (optional for public
          workspaces, required for private)
        - Target-Workspace-Key header with target workspace key (required)

        Copies:

        - Document metadata (title, doc_date, shared status, etc.)
        - MinIO encrypted files (downloaded to server memory, re-encrypted, uploaded)
        - Qdrant vectors (with updated doc_ext_id and chunk_ext_id references)

        Args:
          items: List of document external IDs to copy (e.g., ['doc-a1b2c3d4', 'doc-e5f6g7h8'])

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workspace_ext_id:
            raise ValueError(f"Expected a non-empty value for `workspace_ext_id` but received {workspace_ext_id!r}")
        extra_headers = {
            **strip_not_given(
                {
                    "target-workspace-key": target_workspace_key,
                    "workspace-key": workspace_key,
                }
            ),
            **(extra_headers or {}),
        }
        return self._post(
            f"/api/workspace/{workspace_ext_id}/copy",
            body=maybe_transform(
                {
                    "items": items,
                    "target_workspace_ext_id": target_workspace_ext_id,
                },
                workspace_copy_params.WorkspaceCopyParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkspaceCopyResponse,
        )

    def create_protected(
        self,
        *,
        name: str,
        description: Optional[str] | Omit = omit,
        is_public: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkspaceResponse:
        """Create a new workspace with encryption and access controls.

        Sets up vector
        storage and associates the creator as the initial workspace user.

        Server generates the workspace symmetric key and wraps it with the user's public
        key. The wrapped key is returned in the response for client-side storage.

        Public workspaces are visible to all users and grant non-members limited access:

        - Non-members can view shared documents and tags
        - Non-members can create conversations and send messages
        - Only members can upload documents
        - Only members can see the member list

        Only users with developer flag can create public workspaces.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/workspace/create_protected",
            body=maybe_transform(
                {
                    "name": name,
                    "description": description,
                    "is_public": is_public,
                },
                workspace_create_protected_params.WorkspaceCreateProtectedParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkspaceResponse,
        )

    def get_conversations(
        self,
        workspace_ext_id: str,
        *,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkspaceGetConversationsResponse:
        """
        Retrieve conversations for a workspace where the current user is:

        - The creator of the conversation, or
        - Listed in the ConvoUsers table.

        Return conversation metadata including:

        - External ID
        - Title
        - Last updated date
        - Number of messages
        - Whether the current user is the creator

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workspace_ext_id:
            raise ValueError(f"Expected a non-empty value for `workspace_ext_id` but received {workspace_ext_id!r}")
        extra_headers = {**strip_not_given({"workspace-key": workspace_key}), **(extra_headers or {})}
        return self._get(
            f"/api/workspace/{workspace_ext_id}/conversations",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkspaceGetConversationsResponse,
        )

    def get_documents(
        self,
        workspace_ext_id: str,
        *,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkspaceGetDocumentsResponse:
        """Retrieve all documents in a workspace with proper access controls.

        Decrypts
        document metadata for authorized users.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workspace_ext_id:
            raise ValueError(f"Expected a non-empty value for `workspace_ext_id` but received {workspace_ext_id!r}")
        extra_headers = {**strip_not_given({"workspace-key": workspace_key}), **(extra_headers or {})}
        return self._get(
            f"/api/workspace/{workspace_ext_id}/documents",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkspaceGetDocumentsResponse,
        )

    def get_stats(
        self,
        workspace_ext_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkspaceGetStatsResponse:
        """
        Retrieves conversation and document counts with shared/private breakdown for a
        specific workspace.

        - Conversations are "shared" if they have at least one shared message
        - Documents are "shared" if their shared field is True

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workspace_ext_id:
            raise ValueError(f"Expected a non-empty value for `workspace_ext_id` but received {workspace_ext_id!r}")
        return self._get(
            f"/api/workspace/{workspace_ext_id}/stats",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkspaceGetStatsResponse,
        )

    def get_tags(
        self,
        workspace_ext_id: str,
        *,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkspaceGetTagsResponse:
        """
        Get all tags in a given workspace created by the current user.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workspace_ext_id:
            raise ValueError(f"Expected a non-empty value for `workspace_ext_id` but received {workspace_ext_id!r}")
        extra_headers = {**strip_not_given({"workspace-key": workspace_key}), **(extra_headers or {})}
        return self._get(
            f"/api/workspace/{workspace_ext_id}/tags",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkspaceGetTagsResponse,
        )

    def get_users(
        self,
        workspace_ext_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkspaceGetUsersResponse:
        """Retrieve users with access to a specific workspace.

        RLS handles access control:
        members can view private workspaces, anyone can view public workspaces.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workspace_ext_id:
            raise ValueError(f"Expected a non-empty value for `workspace_ext_id` but received {workspace_ext_id!r}")
        return self._get(
            f"/api/workspace/{workspace_ext_id}/users",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkspaceGetUsersResponse,
        )

    def remove_user(
        self,
        workspace_ext_id: str,
        *,
        user_ext_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkspaceRemoveUserResponse:
        """
        Remove a user from a workspace.

        RLS ensures the user can only modify workspaces they have access to.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workspace_ext_id:
            raise ValueError(f"Expected a non-empty value for `workspace_ext_id` but received {workspace_ext_id!r}")
        return self._delete(
            f"/api/workspace/{workspace_ext_id}/user",
            body=maybe_transform({"user_ext_id": user_ext_id}, workspace_remove_user_params.WorkspaceRemoveUserParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkspaceRemoveUserResponse,
        )

    def share(
        self,
        workspace_ext_id: str,
        *,
        recipient_email: str,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkspaceShareResponse:
        """
        Share a workspace with another user via their email address.

        Client provides SealedBox-encrypted workspace key via Workspace-Key header.
        Server decrypts it using session key, then wraps it with recipient's public key.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workspace_ext_id:
            raise ValueError(f"Expected a non-empty value for `workspace_ext_id` but received {workspace_ext_id!r}")
        extra_headers = {**strip_not_given({"workspace-key": workspace_key}), **(extra_headers or {})}
        return self._post(
            f"/api/workspace/{workspace_ext_id}/share",
            body=maybe_transform({"recipient_email": recipient_email}, workspace_share_params.WorkspaceShareParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkspaceShareResponse,
        )


class AsyncWorkspaceResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncWorkspaceResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#accessing-raw-response-data-eg-headers
        """
        return AsyncWorkspaceResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncWorkspaceResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#with_streaming_response
        """
        return AsyncWorkspaceResourceWithStreamingResponse(self)

    async def update(
        self,
        workspace_ext_id: str,
        *,
        description: Optional[str] | Omit = omit,
        is_public: Optional[bool] | Omit = omit,
        name: Optional[str] | Omit = omit,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkspaceResponse:
        """Update workspace metadata such as name, description, or public status.

        Changes
        are persisted to the database.

        Only developers can change the is_public field. When making a workspace public,
        the backend uses the Workspace-Key header to get the workspace key.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workspace_ext_id:
            raise ValueError(f"Expected a non-empty value for `workspace_ext_id` but received {workspace_ext_id!r}")
        extra_headers = {**strip_not_given({"workspace-key": workspace_key}), **(extra_headers or {})}
        return await self._patch(
            f"/api/workspace/{workspace_ext_id}",
            body=await async_maybe_transform(
                {
                    "description": description,
                    "is_public": is_public,
                    "name": name,
                },
                workspace_update_params.WorkspaceUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkspaceResponse,
        )

    async def delete(
        self,
        workspace_ext_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkspaceDeleteResponse:
        """Delete a workspace.

        Only the creator of the workspace is allowed to delete it.

        If the workspace
        deletion fails (e.g., due to RLS policy), the operation aborts.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workspace_ext_id:
            raise ValueError(f"Expected a non-empty value for `workspace_ext_id` but received {workspace_ext_id!r}")
        return await self._delete(
            f"/api/workspace/{workspace_ext_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkspaceDeleteResponse,
        )

    async def copy(
        self,
        workspace_ext_id: str,
        *,
        items: SequenceNotStr[str],
        target_workspace_ext_id: str,
        target_workspace_key: str | Omit = omit,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkspaceCopyResponse:
        """
        Copy documents from source workspace to target workspace.

        Requires:

        - User must have access to source workspace (RLS enforced)
        - Target workspace must exist and user must have access
        - Workspace-Key header with source workspace key (optional for public
          workspaces, required for private)
        - Target-Workspace-Key header with target workspace key (required)

        Copies:

        - Document metadata (title, doc_date, shared status, etc.)
        - MinIO encrypted files (downloaded to server memory, re-encrypted, uploaded)
        - Qdrant vectors (with updated doc_ext_id and chunk_ext_id references)

        Args:
          items: List of document external IDs to copy (e.g., ['doc-a1b2c3d4', 'doc-e5f6g7h8'])

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workspace_ext_id:
            raise ValueError(f"Expected a non-empty value for `workspace_ext_id` but received {workspace_ext_id!r}")
        extra_headers = {
            **strip_not_given(
                {
                    "target-workspace-key": target_workspace_key,
                    "workspace-key": workspace_key,
                }
            ),
            **(extra_headers or {}),
        }
        return await self._post(
            f"/api/workspace/{workspace_ext_id}/copy",
            body=await async_maybe_transform(
                {
                    "items": items,
                    "target_workspace_ext_id": target_workspace_ext_id,
                },
                workspace_copy_params.WorkspaceCopyParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkspaceCopyResponse,
        )

    async def create_protected(
        self,
        *,
        name: str,
        description: Optional[str] | Omit = omit,
        is_public: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkspaceResponse:
        """Create a new workspace with encryption and access controls.

        Sets up vector
        storage and associates the creator as the initial workspace user.

        Server generates the workspace symmetric key and wraps it with the user's public
        key. The wrapped key is returned in the response for client-side storage.

        Public workspaces are visible to all users and grant non-members limited access:

        - Non-members can view shared documents and tags
        - Non-members can create conversations and send messages
        - Only members can upload documents
        - Only members can see the member list

        Only users with developer flag can create public workspaces.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/workspace/create_protected",
            body=await async_maybe_transform(
                {
                    "name": name,
                    "description": description,
                    "is_public": is_public,
                },
                workspace_create_protected_params.WorkspaceCreateProtectedParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkspaceResponse,
        )

    async def get_conversations(
        self,
        workspace_ext_id: str,
        *,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkspaceGetConversationsResponse:
        """
        Retrieve conversations for a workspace where the current user is:

        - The creator of the conversation, or
        - Listed in the ConvoUsers table.

        Return conversation metadata including:

        - External ID
        - Title
        - Last updated date
        - Number of messages
        - Whether the current user is the creator

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workspace_ext_id:
            raise ValueError(f"Expected a non-empty value for `workspace_ext_id` but received {workspace_ext_id!r}")
        extra_headers = {**strip_not_given({"workspace-key": workspace_key}), **(extra_headers or {})}
        return await self._get(
            f"/api/workspace/{workspace_ext_id}/conversations",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkspaceGetConversationsResponse,
        )

    async def get_documents(
        self,
        workspace_ext_id: str,
        *,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkspaceGetDocumentsResponse:
        """Retrieve all documents in a workspace with proper access controls.

        Decrypts
        document metadata for authorized users.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workspace_ext_id:
            raise ValueError(f"Expected a non-empty value for `workspace_ext_id` but received {workspace_ext_id!r}")
        extra_headers = {**strip_not_given({"workspace-key": workspace_key}), **(extra_headers or {})}
        return await self._get(
            f"/api/workspace/{workspace_ext_id}/documents",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkspaceGetDocumentsResponse,
        )

    async def get_stats(
        self,
        workspace_ext_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkspaceGetStatsResponse:
        """
        Retrieves conversation and document counts with shared/private breakdown for a
        specific workspace.

        - Conversations are "shared" if they have at least one shared message
        - Documents are "shared" if their shared field is True

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workspace_ext_id:
            raise ValueError(f"Expected a non-empty value for `workspace_ext_id` but received {workspace_ext_id!r}")
        return await self._get(
            f"/api/workspace/{workspace_ext_id}/stats",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkspaceGetStatsResponse,
        )

    async def get_tags(
        self,
        workspace_ext_id: str,
        *,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkspaceGetTagsResponse:
        """
        Get all tags in a given workspace created by the current user.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workspace_ext_id:
            raise ValueError(f"Expected a non-empty value for `workspace_ext_id` but received {workspace_ext_id!r}")
        extra_headers = {**strip_not_given({"workspace-key": workspace_key}), **(extra_headers or {})}
        return await self._get(
            f"/api/workspace/{workspace_ext_id}/tags",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkspaceGetTagsResponse,
        )

    async def get_users(
        self,
        workspace_ext_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkspaceGetUsersResponse:
        """Retrieve users with access to a specific workspace.

        RLS handles access control:
        members can view private workspaces, anyone can view public workspaces.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workspace_ext_id:
            raise ValueError(f"Expected a non-empty value for `workspace_ext_id` but received {workspace_ext_id!r}")
        return await self._get(
            f"/api/workspace/{workspace_ext_id}/users",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkspaceGetUsersResponse,
        )

    async def remove_user(
        self,
        workspace_ext_id: str,
        *,
        user_ext_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkspaceRemoveUserResponse:
        """
        Remove a user from a workspace.

        RLS ensures the user can only modify workspaces they have access to.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workspace_ext_id:
            raise ValueError(f"Expected a non-empty value for `workspace_ext_id` but received {workspace_ext_id!r}")
        return await self._delete(
            f"/api/workspace/{workspace_ext_id}/user",
            body=await async_maybe_transform(
                {"user_ext_id": user_ext_id}, workspace_remove_user_params.WorkspaceRemoveUserParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkspaceRemoveUserResponse,
        )

    async def share(
        self,
        workspace_ext_id: str,
        *,
        recipient_email: str,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkspaceShareResponse:
        """
        Share a workspace with another user via their email address.

        Client provides SealedBox-encrypted workspace key via Workspace-Key header.
        Server decrypts it using session key, then wraps it with recipient's public key.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workspace_ext_id:
            raise ValueError(f"Expected a non-empty value for `workspace_ext_id` but received {workspace_ext_id!r}")
        extra_headers = {**strip_not_given({"workspace-key": workspace_key}), **(extra_headers or {})}
        return await self._post(
            f"/api/workspace/{workspace_ext_id}/share",
            body=await async_maybe_transform(
                {"recipient_email": recipient_email}, workspace_share_params.WorkspaceShareParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkspaceShareResponse,
        )


class WorkspaceResourceWithRawResponse:
    def __init__(self, workspace: WorkspaceResource) -> None:
        self._workspace = workspace

        self.update = to_raw_response_wrapper(
            workspace.update,
        )
        self.delete = to_raw_response_wrapper(
            workspace.delete,
        )
        self.copy = to_raw_response_wrapper(
            workspace.copy,
        )
        self.create_protected = to_raw_response_wrapper(
            workspace.create_protected,
        )
        self.get_conversations = to_raw_response_wrapper(
            workspace.get_conversations,
        )
        self.get_documents = to_raw_response_wrapper(
            workspace.get_documents,
        )
        self.get_stats = to_raw_response_wrapper(
            workspace.get_stats,
        )
        self.get_tags = to_raw_response_wrapper(
            workspace.get_tags,
        )
        self.get_users = to_raw_response_wrapper(
            workspace.get_users,
        )
        self.remove_user = to_raw_response_wrapper(
            workspace.remove_user,
        )
        self.share = to_raw_response_wrapper(
            workspace.share,
        )


class AsyncWorkspaceResourceWithRawResponse:
    def __init__(self, workspace: AsyncWorkspaceResource) -> None:
        self._workspace = workspace

        self.update = async_to_raw_response_wrapper(
            workspace.update,
        )
        self.delete = async_to_raw_response_wrapper(
            workspace.delete,
        )
        self.copy = async_to_raw_response_wrapper(
            workspace.copy,
        )
        self.create_protected = async_to_raw_response_wrapper(
            workspace.create_protected,
        )
        self.get_conversations = async_to_raw_response_wrapper(
            workspace.get_conversations,
        )
        self.get_documents = async_to_raw_response_wrapper(
            workspace.get_documents,
        )
        self.get_stats = async_to_raw_response_wrapper(
            workspace.get_stats,
        )
        self.get_tags = async_to_raw_response_wrapper(
            workspace.get_tags,
        )
        self.get_users = async_to_raw_response_wrapper(
            workspace.get_users,
        )
        self.remove_user = async_to_raw_response_wrapper(
            workspace.remove_user,
        )
        self.share = async_to_raw_response_wrapper(
            workspace.share,
        )


class WorkspaceResourceWithStreamingResponse:
    def __init__(self, workspace: WorkspaceResource) -> None:
        self._workspace = workspace

        self.update = to_streamed_response_wrapper(
            workspace.update,
        )
        self.delete = to_streamed_response_wrapper(
            workspace.delete,
        )
        self.copy = to_streamed_response_wrapper(
            workspace.copy,
        )
        self.create_protected = to_streamed_response_wrapper(
            workspace.create_protected,
        )
        self.get_conversations = to_streamed_response_wrapper(
            workspace.get_conversations,
        )
        self.get_documents = to_streamed_response_wrapper(
            workspace.get_documents,
        )
        self.get_stats = to_streamed_response_wrapper(
            workspace.get_stats,
        )
        self.get_tags = to_streamed_response_wrapper(
            workspace.get_tags,
        )
        self.get_users = to_streamed_response_wrapper(
            workspace.get_users,
        )
        self.remove_user = to_streamed_response_wrapper(
            workspace.remove_user,
        )
        self.share = to_streamed_response_wrapper(
            workspace.share,
        )


class AsyncWorkspaceResourceWithStreamingResponse:
    def __init__(self, workspace: AsyncWorkspaceResource) -> None:
        self._workspace = workspace

        self.update = async_to_streamed_response_wrapper(
            workspace.update,
        )
        self.delete = async_to_streamed_response_wrapper(
            workspace.delete,
        )
        self.copy = async_to_streamed_response_wrapper(
            workspace.copy,
        )
        self.create_protected = async_to_streamed_response_wrapper(
            workspace.create_protected,
        )
        self.get_conversations = async_to_streamed_response_wrapper(
            workspace.get_conversations,
        )
        self.get_documents = async_to_streamed_response_wrapper(
            workspace.get_documents,
        )
        self.get_stats = async_to_streamed_response_wrapper(
            workspace.get_stats,
        )
        self.get_tags = async_to_streamed_response_wrapper(
            workspace.get_tags,
        )
        self.get_users = async_to_streamed_response_wrapper(
            workspace.get_users,
        )
        self.remove_user = async_to_streamed_response_wrapper(
            workspace.remove_user,
        )
        self.share = async_to_streamed_response_wrapper(
            workspace.share,
        )
