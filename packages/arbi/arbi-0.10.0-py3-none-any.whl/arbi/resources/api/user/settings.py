# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable, Optional

import httpx

from ...._types import Body, Omit, Query, Headers, NoneType, NotGiven, SequenceNotStr, omit, not_given
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
from ....types.api.user import setting_update_params
from ....types.api.user.setting_retrieve_response import SettingRetrieveResponse

__all__ = ["SettingsResource", "AsyncSettingsResource"]


class SettingsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SettingsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#accessing-raw-response-data-eg-headers
        """
        return SettingsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SettingsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#with_streaming_response
        """
        return SettingsResourceWithStreamingResponse(self)

    def retrieve(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SettingRetrieveResponse:
        """Get current user's settings."""
        return self._get(
            "/api/user/settings",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SettingRetrieveResponse,
        )

    def update(
        self,
        *,
        ai_mode: Optional[str] | Omit = omit,
        pinned_workspaces: Optional[SequenceNotStr[str]] | Omit = omit,
        show_document_navigator: Optional[bool] | Omit = omit,
        show_help_page: Optional[bool] | Omit = omit,
        show_invite_tab: Optional[bool] | Omit = omit,
        show_security_settings: Optional[bool] | Omit = omit,
        show_smart_search: Optional[bool] | Omit = omit,
        show_templates: Optional[bool] | Omit = omit,
        show_thread_visualization: Optional[bool] | Omit = omit,
        subscription: Optional[setting_update_params.Subscription] | Omit = omit,
        tableviews: Optional[Iterable[setting_update_params.Tableview]] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Update user's settings (merge with existing).

        Note: subscription fields are managed automatically and cannot be patched.

        Args:
          subscription: Trial update - only trial_expires can be set, and only if currently null.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._patch(
            "/api/user/settings",
            body=maybe_transform(
                {
                    "ai_mode": ai_mode,
                    "pinned_workspaces": pinned_workspaces,
                    "show_document_navigator": show_document_navigator,
                    "show_help_page": show_help_page,
                    "show_invite_tab": show_invite_tab,
                    "show_security_settings": show_security_settings,
                    "show_smart_search": show_smart_search,
                    "show_templates": show_templates,
                    "show_thread_visualization": show_thread_visualization,
                    "subscription": subscription,
                    "tableviews": tableviews,
                },
                setting_update_params.SettingUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncSettingsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSettingsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#accessing-raw-response-data-eg-headers
        """
        return AsyncSettingsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSettingsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#with_streaming_response
        """
        return AsyncSettingsResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SettingRetrieveResponse:
        """Get current user's settings."""
        return await self._get(
            "/api/user/settings",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SettingRetrieveResponse,
        )

    async def update(
        self,
        *,
        ai_mode: Optional[str] | Omit = omit,
        pinned_workspaces: Optional[SequenceNotStr[str]] | Omit = omit,
        show_document_navigator: Optional[bool] | Omit = omit,
        show_help_page: Optional[bool] | Omit = omit,
        show_invite_tab: Optional[bool] | Omit = omit,
        show_security_settings: Optional[bool] | Omit = omit,
        show_smart_search: Optional[bool] | Omit = omit,
        show_templates: Optional[bool] | Omit = omit,
        show_thread_visualization: Optional[bool] | Omit = omit,
        subscription: Optional[setting_update_params.Subscription] | Omit = omit,
        tableviews: Optional[Iterable[setting_update_params.Tableview]] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Update user's settings (merge with existing).

        Note: subscription fields are managed automatically and cannot be patched.

        Args:
          subscription: Trial update - only trial_expires can be set, and only if currently null.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._patch(
            "/api/user/settings",
            body=await async_maybe_transform(
                {
                    "ai_mode": ai_mode,
                    "pinned_workspaces": pinned_workspaces,
                    "show_document_navigator": show_document_navigator,
                    "show_help_page": show_help_page,
                    "show_invite_tab": show_invite_tab,
                    "show_security_settings": show_security_settings,
                    "show_smart_search": show_smart_search,
                    "show_templates": show_templates,
                    "show_thread_visualization": show_thread_visualization,
                    "subscription": subscription,
                    "tableviews": tableviews,
                },
                setting_update_params.SettingUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class SettingsResourceWithRawResponse:
    def __init__(self, settings: SettingsResource) -> None:
        self._settings = settings

        self.retrieve = to_raw_response_wrapper(
            settings.retrieve,
        )
        self.update = to_raw_response_wrapper(
            settings.update,
        )


class AsyncSettingsResourceWithRawResponse:
    def __init__(self, settings: AsyncSettingsResource) -> None:
        self._settings = settings

        self.retrieve = async_to_raw_response_wrapper(
            settings.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            settings.update,
        )


class SettingsResourceWithStreamingResponse:
    def __init__(self, settings: SettingsResource) -> None:
        self._settings = settings

        self.retrieve = to_streamed_response_wrapper(
            settings.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            settings.update,
        )


class AsyncSettingsResourceWithStreamingResponse:
    def __init__(self, settings: AsyncSettingsResource) -> None:
        self._settings = settings

        self.retrieve = async_to_streamed_response_wrapper(
            settings.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            settings.update,
        )
