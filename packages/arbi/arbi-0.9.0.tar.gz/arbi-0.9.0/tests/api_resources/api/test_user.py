# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from arbi import Arbi, AsyncArbi
from tests.utils import assert_matches_type
from arbi.types.api import (
    UserLoginResponse,
    UserLogoutResponse,
    UserVerifyEmailResponse,
    UserListProductsResponse,
    UserChangePasswordResponse,
    UserCheckSSOStatusResponse,
    UserListWorkspacesResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestUser:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_change_password(self, client: Arbi) -> None:
        user = client.api.user.change_password(
            current_public_key="current_public_key",
            new_public_key="new_public_key",
            rewrapped_workspace_keys={"foo": "string"},
        )
        assert_matches_type(UserChangePasswordResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_change_password(self, client: Arbi) -> None:
        response = client.api.user.with_raw_response.change_password(
            current_public_key="current_public_key",
            new_public_key="new_public_key",
            rewrapped_workspace_keys={"foo": "string"},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = response.parse()
        assert_matches_type(UserChangePasswordResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_change_password(self, client: Arbi) -> None:
        with client.api.user.with_streaming_response.change_password(
            current_public_key="current_public_key",
            new_public_key="new_public_key",
            rewrapped_workspace_keys={"foo": "string"},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = response.parse()
            assert_matches_type(UserChangePasswordResponse, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_check_sso_status(self, client: Arbi) -> None:
        user = client.api.user.check_sso_status(
            email="dev@stainless.com",
            sso_token="sso_token",
        )
        assert_matches_type(UserCheckSSOStatusResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_check_sso_status(self, client: Arbi) -> None:
        response = client.api.user.with_raw_response.check_sso_status(
            email="dev@stainless.com",
            sso_token="sso_token",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = response.parse()
        assert_matches_type(UserCheckSSOStatusResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_check_sso_status(self, client: Arbi) -> None:
        with client.api.user.with_streaming_response.check_sso_status(
            email="dev@stainless.com",
            sso_token="sso_token",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = response.parse()
            assert_matches_type(UserCheckSSOStatusResponse, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_products(self, client: Arbi) -> None:
        user = client.api.user.list_products()
        assert_matches_type(UserListProductsResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_products(self, client: Arbi) -> None:
        response = client.api.user.with_raw_response.list_products()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = response.parse()
        assert_matches_type(UserListProductsResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_products(self, client: Arbi) -> None:
        with client.api.user.with_streaming_response.list_products() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = response.parse()
            assert_matches_type(UserListProductsResponse, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_workspaces(self, client: Arbi) -> None:
        user = client.api.user.list_workspaces()
        assert_matches_type(UserListWorkspacesResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_workspaces(self, client: Arbi) -> None:
        response = client.api.user.with_raw_response.list_workspaces()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = response.parse()
        assert_matches_type(UserListWorkspacesResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_workspaces(self, client: Arbi) -> None:
        with client.api.user.with_streaming_response.list_workspaces() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = response.parse()
            assert_matches_type(UserListWorkspacesResponse, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_login(self, client: Arbi) -> None:
        user = client.api.user.login(
            email="dev@stainless.com",
            public_key="public_key",
        )
        assert_matches_type(UserLoginResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_login_with_all_params(self, client: Arbi) -> None:
        user = client.api.user.login(
            email="dev@stainless.com",
            public_key="public_key",
            sso_token="sso_token",
        )
        assert_matches_type(UserLoginResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_login(self, client: Arbi) -> None:
        response = client.api.user.with_raw_response.login(
            email="dev@stainless.com",
            public_key="public_key",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = response.parse()
        assert_matches_type(UserLoginResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_login(self, client: Arbi) -> None:
        with client.api.user.with_streaming_response.login(
            email="dev@stainless.com",
            public_key="public_key",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = response.parse()
            assert_matches_type(UserLoginResponse, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_logout(self, client: Arbi) -> None:
        user = client.api.user.logout()
        assert_matches_type(UserLogoutResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_logout(self, client: Arbi) -> None:
        response = client.api.user.with_raw_response.logout()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = response.parse()
        assert_matches_type(UserLogoutResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_logout(self, client: Arbi) -> None:
        with client.api.user.with_streaming_response.logout() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = response.parse()
            assert_matches_type(UserLogoutResponse, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_register(self, client: Arbi) -> None:
        user = client.api.user.register(
            email="dev@stainless.com",
            public_key="public_key",
            verification_credential="verification_credential",
        )
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_register_with_all_params(self, client: Arbi) -> None:
        user = client.api.user.register(
            email="dev@stainless.com",
            public_key="public_key",
            verification_credential="verification_credential",
            last_name="last_name",
            name="name",
        )
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_register(self, client: Arbi) -> None:
        response = client.api.user.with_raw_response.register(
            email="dev@stainless.com",
            public_key="public_key",
            verification_credential="verification_credential",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = response.parse()
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_register(self, client: Arbi) -> None:
        with client.api.user.with_streaming_response.register(
            email="dev@stainless.com",
            public_key="public_key",
            verification_credential="verification_credential",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = response.parse()
            assert_matches_type(object, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_verify_email(self, client: Arbi) -> None:
        user = client.api.user.verify_email(
            email="dev@stainless.com",
        )
        assert_matches_type(UserVerifyEmailResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_verify_email(self, client: Arbi) -> None:
        response = client.api.user.with_raw_response.verify_email(
            email="dev@stainless.com",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = response.parse()
        assert_matches_type(UserVerifyEmailResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_verify_email(self, client: Arbi) -> None:
        with client.api.user.with_streaming_response.verify_email(
            email="dev@stainless.com",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = response.parse()
            assert_matches_type(UserVerifyEmailResponse, user, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncUser:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_change_password(self, async_client: AsyncArbi) -> None:
        user = await async_client.api.user.change_password(
            current_public_key="current_public_key",
            new_public_key="new_public_key",
            rewrapped_workspace_keys={"foo": "string"},
        )
        assert_matches_type(UserChangePasswordResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_change_password(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.user.with_raw_response.change_password(
            current_public_key="current_public_key",
            new_public_key="new_public_key",
            rewrapped_workspace_keys={"foo": "string"},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = await response.parse()
        assert_matches_type(UserChangePasswordResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_change_password(self, async_client: AsyncArbi) -> None:
        async with async_client.api.user.with_streaming_response.change_password(
            current_public_key="current_public_key",
            new_public_key="new_public_key",
            rewrapped_workspace_keys={"foo": "string"},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = await response.parse()
            assert_matches_type(UserChangePasswordResponse, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_check_sso_status(self, async_client: AsyncArbi) -> None:
        user = await async_client.api.user.check_sso_status(
            email="dev@stainless.com",
            sso_token="sso_token",
        )
        assert_matches_type(UserCheckSSOStatusResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_check_sso_status(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.user.with_raw_response.check_sso_status(
            email="dev@stainless.com",
            sso_token="sso_token",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = await response.parse()
        assert_matches_type(UserCheckSSOStatusResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_check_sso_status(self, async_client: AsyncArbi) -> None:
        async with async_client.api.user.with_streaming_response.check_sso_status(
            email="dev@stainless.com",
            sso_token="sso_token",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = await response.parse()
            assert_matches_type(UserCheckSSOStatusResponse, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_products(self, async_client: AsyncArbi) -> None:
        user = await async_client.api.user.list_products()
        assert_matches_type(UserListProductsResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_products(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.user.with_raw_response.list_products()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = await response.parse()
        assert_matches_type(UserListProductsResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_products(self, async_client: AsyncArbi) -> None:
        async with async_client.api.user.with_streaming_response.list_products() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = await response.parse()
            assert_matches_type(UserListProductsResponse, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_workspaces(self, async_client: AsyncArbi) -> None:
        user = await async_client.api.user.list_workspaces()
        assert_matches_type(UserListWorkspacesResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_workspaces(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.user.with_raw_response.list_workspaces()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = await response.parse()
        assert_matches_type(UserListWorkspacesResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_workspaces(self, async_client: AsyncArbi) -> None:
        async with async_client.api.user.with_streaming_response.list_workspaces() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = await response.parse()
            assert_matches_type(UserListWorkspacesResponse, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_login(self, async_client: AsyncArbi) -> None:
        user = await async_client.api.user.login(
            email="dev@stainless.com",
            public_key="public_key",
        )
        assert_matches_type(UserLoginResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_login_with_all_params(self, async_client: AsyncArbi) -> None:
        user = await async_client.api.user.login(
            email="dev@stainless.com",
            public_key="public_key",
            sso_token="sso_token",
        )
        assert_matches_type(UserLoginResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_login(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.user.with_raw_response.login(
            email="dev@stainless.com",
            public_key="public_key",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = await response.parse()
        assert_matches_type(UserLoginResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_login(self, async_client: AsyncArbi) -> None:
        async with async_client.api.user.with_streaming_response.login(
            email="dev@stainless.com",
            public_key="public_key",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = await response.parse()
            assert_matches_type(UserLoginResponse, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_logout(self, async_client: AsyncArbi) -> None:
        user = await async_client.api.user.logout()
        assert_matches_type(UserLogoutResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_logout(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.user.with_raw_response.logout()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = await response.parse()
        assert_matches_type(UserLogoutResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_logout(self, async_client: AsyncArbi) -> None:
        async with async_client.api.user.with_streaming_response.logout() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = await response.parse()
            assert_matches_type(UserLogoutResponse, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_register(self, async_client: AsyncArbi) -> None:
        user = await async_client.api.user.register(
            email="dev@stainless.com",
            public_key="public_key",
            verification_credential="verification_credential",
        )
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_register_with_all_params(self, async_client: AsyncArbi) -> None:
        user = await async_client.api.user.register(
            email="dev@stainless.com",
            public_key="public_key",
            verification_credential="verification_credential",
            last_name="last_name",
            name="name",
        )
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_register(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.user.with_raw_response.register(
            email="dev@stainless.com",
            public_key="public_key",
            verification_credential="verification_credential",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = await response.parse()
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_register(self, async_client: AsyncArbi) -> None:
        async with async_client.api.user.with_streaming_response.register(
            email="dev@stainless.com",
            public_key="public_key",
            verification_credential="verification_credential",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = await response.parse()
            assert_matches_type(object, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_verify_email(self, async_client: AsyncArbi) -> None:
        user = await async_client.api.user.verify_email(
            email="dev@stainless.com",
        )
        assert_matches_type(UserVerifyEmailResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_verify_email(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.user.with_raw_response.verify_email(
            email="dev@stainless.com",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = await response.parse()
        assert_matches_type(UserVerifyEmailResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_verify_email(self, async_client: AsyncArbi) -> None:
        async with async_client.api.user.with_streaming_response.verify_email(
            email="dev@stainless.com",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = await response.parse()
            assert_matches_type(UserVerifyEmailResponse, user, path=["response"])

        assert cast(Any, response.is_closed) is True
