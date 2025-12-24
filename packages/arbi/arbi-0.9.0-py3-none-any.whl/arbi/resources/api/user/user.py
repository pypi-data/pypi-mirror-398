# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional

import httpx

from .contacts import (
    ContactsResource,
    AsyncContactsResource,
    ContactsResourceWithRawResponse,
    AsyncContactsResourceWithRawResponse,
    ContactsResourceWithStreamingResponse,
    AsyncContactsResourceWithStreamingResponse,
)
from .settings import (
    SettingsResource,
    AsyncSettingsResource,
    SettingsResourceWithRawResponse,
    AsyncSettingsResourceWithRawResponse,
    SettingsResourceWithStreamingResponse,
    AsyncSettingsResourceWithStreamingResponse,
)
from ...._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ...._utils import maybe_transform, async_maybe_transform
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ....types.api import (
    user_login_params,
    user_register_params,
    user_verify_email_params,
    user_change_password_params,
    user_check_sso_status_params,
)
from .subscription import (
    SubscriptionResource,
    AsyncSubscriptionResource,
    SubscriptionResourceWithRawResponse,
    AsyncSubscriptionResourceWithRawResponse,
    SubscriptionResourceWithStreamingResponse,
    AsyncSubscriptionResourceWithStreamingResponse,
)
from ...._base_client import make_request_options
from ....types.api.user_login_response import UserLoginResponse
from ....types.api.user_logout_response import UserLogoutResponse
from ....types.api.user_verify_email_response import UserVerifyEmailResponse
from ....types.api.user_list_products_response import UserListProductsResponse
from ....types.api.user_change_password_response import UserChangePasswordResponse
from ....types.api.user_list_workspaces_response import UserListWorkspacesResponse
from ....types.api.user_check_sso_status_response import UserCheckSSOStatusResponse

__all__ = ["UserResource", "AsyncUserResource"]


class UserResource(SyncAPIResource):
    @cached_property
    def settings(self) -> SettingsResource:
        return SettingsResource(self._client)

    @cached_property
    def subscription(self) -> SubscriptionResource:
        return SubscriptionResource(self._client)

    @cached_property
    def contacts(self) -> ContactsResource:
        return ContactsResource(self._client)

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

    def change_password(
        self,
        *,
        current_public_key: str,
        new_public_key: str,
        rewrapped_workspace_keys: Dict[str, str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UserChangePasswordResponse:
        """Change user's master password by re-keying all workspace keys.

        Client must:

        1.

        Prove knowledge of current master password via X25519 public key
        2. Provide new X25519 public key (derived from new master password)
        3. Re-wrap all workspace keys with new X25519 public key

        Server will:

        1. Verify current master password (public key comparison)
        2. Update X25519 public key
        3. Update all workspace wrapped keys

        Note: This changes the master password (encryption password), not authentication
        password. Both local and SSO users can change their master password.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/user/change_password",
            body=maybe_transform(
                {
                    "current_public_key": current_public_key,
                    "new_public_key": new_public_key,
                    "rewrapped_workspace_keys": rewrapped_workspace_keys,
                },
                user_change_password_params.UserChangePasswordParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserChangePasswordResponse,
        )

    def check_sso_status(
        self,
        *,
        email: str,
        sso_token: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UserCheckSSOStatusResponse:
        """Check SSO user registration state.

        Returns one of three states:

        1.

        new_user: No user exists with this email
        2. local_exists: User exists but registered locally (can link to SSO)
        3. sso_exists: User exists and already linked to SSO

        Frontend uses this to show appropriate UI:

        - new_user -> "Set Master Password"
        - local_exists -> "Link SSO? Enter current master password"
        - sso_exists -> "Enter Master Password"

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/user/sso-status",
            body=maybe_transform(
                {
                    "email": email,
                    "sso_token": sso_token,
                },
                user_check_sso_status_params.UserCheckSSOStatusParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserCheckSSOStatusResponse,
        )

    def list_products(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UserListProductsResponse:
        """Get available subscription products and prices from Stripe."""
        return self._get(
            "/api/user/products",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserListProductsResponse,
        )

    def list_workspaces(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UserListWorkspacesResponse:
        """
        Retrieve the list of workspaces associated with the current authenticated user.
        Includes wrapped_key, stats (conversation/document counts with shared/private
        breakdown), and users for each workspace. All data is fetched efficiently using
        batch queries to avoid N+1 problems. Leverages RLS to enforce access control.
        """
        return self._get(
            "/api/user/workspaces",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserListWorkspacesResponse,
        )

    def login(
        self,
        *,
        email: str,
        public_key: str,
        sso_token: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UserLoginResponse:
        """
        Login with X25519 public key verification (local or SSO).

        SIMPLEST POSSIBLE AUTH: Client derives X25519 public key from password and sends
        it. Server compares with stored public key. Match = correct password!

        For SSO users: Also validates SSO token before proceeding. For local users: Only
        public key verification needed.

        Returns encrypted login response that only the correct password can decrypt.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/user/login",
            body=maybe_transform(
                {
                    "email": email,
                    "public_key": public_key,
                    "sso_token": sso_token,
                },
                user_login_params.UserLoginParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserLoginResponse,
        )

    def logout(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UserLogoutResponse:
        """Log out the current user by clearing the refresh token cookie and session key."""
        return self._post(
            "/api/user/logout",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserLogoutResponse,
        )

    def register(
        self,
        *,
        email: str,
        public_key: str,
        verification_credential: str,
        last_name: Optional[str] | Omit = omit,
        name: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Register a new user with email verification (local or SSO).

        Accepts either:

        - 3-word verification code for local users
        - SSO JWT token for SSO users

        Auto-detects credential type and handles both flows.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/user/register",
            body=maybe_transform(
                {
                    "email": email,
                    "public_key": public_key,
                    "verification_credential": verification_credential,
                    "last_name": last_name,
                    "name": name,
                },
                user_register_params.UserRegisterParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def verify_email(
        self,
        *,
        email: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UserVerifyEmailResponse:
        """Send verification email with 3-word code to user.

        Calls central server to send
        the email.

        Note: Fails silently if email already exists to prevent email enumeration
        attacks. Also returns success even on rate limit/errors to avoid information
        disclosure.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/user/verify-email",
            body=maybe_transform({"email": email}, user_verify_email_params.UserVerifyEmailParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserVerifyEmailResponse,
        )


class AsyncUserResource(AsyncAPIResource):
    @cached_property
    def settings(self) -> AsyncSettingsResource:
        return AsyncSettingsResource(self._client)

    @cached_property
    def subscription(self) -> AsyncSubscriptionResource:
        return AsyncSubscriptionResource(self._client)

    @cached_property
    def contacts(self) -> AsyncContactsResource:
        return AsyncContactsResource(self._client)

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

    async def change_password(
        self,
        *,
        current_public_key: str,
        new_public_key: str,
        rewrapped_workspace_keys: Dict[str, str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UserChangePasswordResponse:
        """Change user's master password by re-keying all workspace keys.

        Client must:

        1.

        Prove knowledge of current master password via X25519 public key
        2. Provide new X25519 public key (derived from new master password)
        3. Re-wrap all workspace keys with new X25519 public key

        Server will:

        1. Verify current master password (public key comparison)
        2. Update X25519 public key
        3. Update all workspace wrapped keys

        Note: This changes the master password (encryption password), not authentication
        password. Both local and SSO users can change their master password.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/user/change_password",
            body=await async_maybe_transform(
                {
                    "current_public_key": current_public_key,
                    "new_public_key": new_public_key,
                    "rewrapped_workspace_keys": rewrapped_workspace_keys,
                },
                user_change_password_params.UserChangePasswordParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserChangePasswordResponse,
        )

    async def check_sso_status(
        self,
        *,
        email: str,
        sso_token: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UserCheckSSOStatusResponse:
        """Check SSO user registration state.

        Returns one of three states:

        1.

        new_user: No user exists with this email
        2. local_exists: User exists but registered locally (can link to SSO)
        3. sso_exists: User exists and already linked to SSO

        Frontend uses this to show appropriate UI:

        - new_user -> "Set Master Password"
        - local_exists -> "Link SSO? Enter current master password"
        - sso_exists -> "Enter Master Password"

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/user/sso-status",
            body=await async_maybe_transform(
                {
                    "email": email,
                    "sso_token": sso_token,
                },
                user_check_sso_status_params.UserCheckSSOStatusParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserCheckSSOStatusResponse,
        )

    async def list_products(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UserListProductsResponse:
        """Get available subscription products and prices from Stripe."""
        return await self._get(
            "/api/user/products",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserListProductsResponse,
        )

    async def list_workspaces(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UserListWorkspacesResponse:
        """
        Retrieve the list of workspaces associated with the current authenticated user.
        Includes wrapped_key, stats (conversation/document counts with shared/private
        breakdown), and users for each workspace. All data is fetched efficiently using
        batch queries to avoid N+1 problems. Leverages RLS to enforce access control.
        """
        return await self._get(
            "/api/user/workspaces",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserListWorkspacesResponse,
        )

    async def login(
        self,
        *,
        email: str,
        public_key: str,
        sso_token: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UserLoginResponse:
        """
        Login with X25519 public key verification (local or SSO).

        SIMPLEST POSSIBLE AUTH: Client derives X25519 public key from password and sends
        it. Server compares with stored public key. Match = correct password!

        For SSO users: Also validates SSO token before proceeding. For local users: Only
        public key verification needed.

        Returns encrypted login response that only the correct password can decrypt.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/user/login",
            body=await async_maybe_transform(
                {
                    "email": email,
                    "public_key": public_key,
                    "sso_token": sso_token,
                },
                user_login_params.UserLoginParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserLoginResponse,
        )

    async def logout(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UserLogoutResponse:
        """Log out the current user by clearing the refresh token cookie and session key."""
        return await self._post(
            "/api/user/logout",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserLogoutResponse,
        )

    async def register(
        self,
        *,
        email: str,
        public_key: str,
        verification_credential: str,
        last_name: Optional[str] | Omit = omit,
        name: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Register a new user with email verification (local or SSO).

        Accepts either:

        - 3-word verification code for local users
        - SSO JWT token for SSO users

        Auto-detects credential type and handles both flows.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/user/register",
            body=await async_maybe_transform(
                {
                    "email": email,
                    "public_key": public_key,
                    "verification_credential": verification_credential,
                    "last_name": last_name,
                    "name": name,
                },
                user_register_params.UserRegisterParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def verify_email(
        self,
        *,
        email: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UserVerifyEmailResponse:
        """Send verification email with 3-word code to user.

        Calls central server to send
        the email.

        Note: Fails silently if email already exists to prevent email enumeration
        attacks. Also returns success even on rate limit/errors to avoid information
        disclosure.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/user/verify-email",
            body=await async_maybe_transform({"email": email}, user_verify_email_params.UserVerifyEmailParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserVerifyEmailResponse,
        )


class UserResourceWithRawResponse:
    def __init__(self, user: UserResource) -> None:
        self._user = user

        self.change_password = to_raw_response_wrapper(
            user.change_password,
        )
        self.check_sso_status = to_raw_response_wrapper(
            user.check_sso_status,
        )
        self.list_products = to_raw_response_wrapper(
            user.list_products,
        )
        self.list_workspaces = to_raw_response_wrapper(
            user.list_workspaces,
        )
        self.login = to_raw_response_wrapper(
            user.login,
        )
        self.logout = to_raw_response_wrapper(
            user.logout,
        )
        self.register = to_raw_response_wrapper(
            user.register,
        )
        self.verify_email = to_raw_response_wrapper(
            user.verify_email,
        )

    @cached_property
    def settings(self) -> SettingsResourceWithRawResponse:
        return SettingsResourceWithRawResponse(self._user.settings)

    @cached_property
    def subscription(self) -> SubscriptionResourceWithRawResponse:
        return SubscriptionResourceWithRawResponse(self._user.subscription)

    @cached_property
    def contacts(self) -> ContactsResourceWithRawResponse:
        return ContactsResourceWithRawResponse(self._user.contacts)


class AsyncUserResourceWithRawResponse:
    def __init__(self, user: AsyncUserResource) -> None:
        self._user = user

        self.change_password = async_to_raw_response_wrapper(
            user.change_password,
        )
        self.check_sso_status = async_to_raw_response_wrapper(
            user.check_sso_status,
        )
        self.list_products = async_to_raw_response_wrapper(
            user.list_products,
        )
        self.list_workspaces = async_to_raw_response_wrapper(
            user.list_workspaces,
        )
        self.login = async_to_raw_response_wrapper(
            user.login,
        )
        self.logout = async_to_raw_response_wrapper(
            user.logout,
        )
        self.register = async_to_raw_response_wrapper(
            user.register,
        )
        self.verify_email = async_to_raw_response_wrapper(
            user.verify_email,
        )

    @cached_property
    def settings(self) -> AsyncSettingsResourceWithRawResponse:
        return AsyncSettingsResourceWithRawResponse(self._user.settings)

    @cached_property
    def subscription(self) -> AsyncSubscriptionResourceWithRawResponse:
        return AsyncSubscriptionResourceWithRawResponse(self._user.subscription)

    @cached_property
    def contacts(self) -> AsyncContactsResourceWithRawResponse:
        return AsyncContactsResourceWithRawResponse(self._user.contacts)


class UserResourceWithStreamingResponse:
    def __init__(self, user: UserResource) -> None:
        self._user = user

        self.change_password = to_streamed_response_wrapper(
            user.change_password,
        )
        self.check_sso_status = to_streamed_response_wrapper(
            user.check_sso_status,
        )
        self.list_products = to_streamed_response_wrapper(
            user.list_products,
        )
        self.list_workspaces = to_streamed_response_wrapper(
            user.list_workspaces,
        )
        self.login = to_streamed_response_wrapper(
            user.login,
        )
        self.logout = to_streamed_response_wrapper(
            user.logout,
        )
        self.register = to_streamed_response_wrapper(
            user.register,
        )
        self.verify_email = to_streamed_response_wrapper(
            user.verify_email,
        )

    @cached_property
    def settings(self) -> SettingsResourceWithStreamingResponse:
        return SettingsResourceWithStreamingResponse(self._user.settings)

    @cached_property
    def subscription(self) -> SubscriptionResourceWithStreamingResponse:
        return SubscriptionResourceWithStreamingResponse(self._user.subscription)

    @cached_property
    def contacts(self) -> ContactsResourceWithStreamingResponse:
        return ContactsResourceWithStreamingResponse(self._user.contacts)


class AsyncUserResourceWithStreamingResponse:
    def __init__(self, user: AsyncUserResource) -> None:
        self._user = user

        self.change_password = async_to_streamed_response_wrapper(
            user.change_password,
        )
        self.check_sso_status = async_to_streamed_response_wrapper(
            user.check_sso_status,
        )
        self.list_products = async_to_streamed_response_wrapper(
            user.list_products,
        )
        self.list_workspaces = async_to_streamed_response_wrapper(
            user.list_workspaces,
        )
        self.login = async_to_streamed_response_wrapper(
            user.login,
        )
        self.logout = async_to_streamed_response_wrapper(
            user.logout,
        )
        self.register = async_to_streamed_response_wrapper(
            user.register,
        )
        self.verify_email = async_to_streamed_response_wrapper(
            user.verify_email,
        )

    @cached_property
    def settings(self) -> AsyncSettingsResourceWithStreamingResponse:
        return AsyncSettingsResourceWithStreamingResponse(self._user.settings)

    @cached_property
    def subscription(self) -> AsyncSubscriptionResourceWithStreamingResponse:
        return AsyncSubscriptionResourceWithStreamingResponse(self._user.subscription)

    @cached_property
    def contacts(self) -> AsyncContactsResourceWithStreamingResponse:
        return AsyncContactsResourceWithStreamingResponse(self._user.contacts)
