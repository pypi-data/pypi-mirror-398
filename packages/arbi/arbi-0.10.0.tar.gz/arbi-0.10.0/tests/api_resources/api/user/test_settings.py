# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from arbi import Arbi, AsyncArbi
from tests.utils import assert_matches_type
from arbi.types.api.user import SettingRetrieveResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSettings:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Arbi) -> None:
        setting = client.api.user.settings.retrieve()
        assert_matches_type(SettingRetrieveResponse, setting, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Arbi) -> None:
        response = client.api.user.settings.with_raw_response.retrieve()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        setting = response.parse()
        assert_matches_type(SettingRetrieveResponse, setting, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Arbi) -> None:
        with client.api.user.settings.with_streaming_response.retrieve() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            setting = response.parse()
            assert_matches_type(SettingRetrieveResponse, setting, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: Arbi) -> None:
        setting = client.api.user.settings.update()
        assert setting is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: Arbi) -> None:
        setting = client.api.user.settings.update(
            ai_mode="ai_mode",
            pinned_workspaces=["wrk-bFXA5r3A"],
            show_document_navigator=True,
            show_help_page=True,
            show_invite_tab=True,
            show_security_settings=True,
            show_smart_search=True,
            show_templates=True,
            show_thread_visualization=True,
            subscription={"trial_expires": 0},
            tableviews=[
                {
                    "columns": ["string"],
                    "name": "name",
                    "workspace": "wrk-bFXA5r3A",
                }
            ],
        )
        assert setting is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: Arbi) -> None:
        response = client.api.user.settings.with_raw_response.update()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        setting = response.parse()
        assert setting is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: Arbi) -> None:
        with client.api.user.settings.with_streaming_response.update() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            setting = response.parse()
            assert setting is None

        assert cast(Any, response.is_closed) is True


class TestAsyncSettings:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncArbi) -> None:
        setting = await async_client.api.user.settings.retrieve()
        assert_matches_type(SettingRetrieveResponse, setting, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.user.settings.with_raw_response.retrieve()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        setting = await response.parse()
        assert_matches_type(SettingRetrieveResponse, setting, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncArbi) -> None:
        async with async_client.api.user.settings.with_streaming_response.retrieve() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            setting = await response.parse()
            assert_matches_type(SettingRetrieveResponse, setting, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncArbi) -> None:
        setting = await async_client.api.user.settings.update()
        assert setting is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncArbi) -> None:
        setting = await async_client.api.user.settings.update(
            ai_mode="ai_mode",
            pinned_workspaces=["wrk-bFXA5r3A"],
            show_document_navigator=True,
            show_help_page=True,
            show_invite_tab=True,
            show_security_settings=True,
            show_smart_search=True,
            show_templates=True,
            show_thread_visualization=True,
            subscription={"trial_expires": 0},
            tableviews=[
                {
                    "columns": ["string"],
                    "name": "name",
                    "workspace": "wrk-bFXA5r3A",
                }
            ],
        )
        assert setting is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.user.settings.with_raw_response.update()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        setting = await response.parse()
        assert setting is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncArbi) -> None:
        async with async_client.api.user.settings.with_streaming_response.update() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            setting = await response.parse()
            assert setting is None

        assert cast(Any, response.is_closed) is True
