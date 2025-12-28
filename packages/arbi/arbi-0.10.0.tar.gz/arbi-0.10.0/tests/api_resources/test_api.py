# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from arbi import Arbi, AsyncArbi
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestAPI:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_index(self, client: Arbi) -> None:
        api = client.api.index()
        assert_matches_type(object, api, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_index(self, client: Arbi) -> None:
        response = client.api.with_raw_response.index()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        api = response.parse()
        assert_matches_type(object, api, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_index(self, client: Arbi) -> None:
        with client.api.with_streaming_response.index() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            api = response.parse()
            assert_matches_type(object, api, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncAPI:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_index(self, async_client: AsyncArbi) -> None:
        api = await async_client.api.index()
        assert_matches_type(object, api, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_index(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.with_raw_response.index()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        api = await response.parse()
        assert_matches_type(object, api, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_index(self, async_client: AsyncArbi) -> None:
        async with async_client.api.with_streaming_response.index() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            api = await response.parse()
            assert_matches_type(object, api, path=["response"])

        assert cast(Any, response.is_closed) is True
