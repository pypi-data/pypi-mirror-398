# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from arbi import Arbi, AsyncArbi
from arbi._utils import parse_date
from tests.utils import assert_matches_type
from arbi.types.api import (
    DocumentUpdateResponse,
    DocumentUploadResponse,
    DocumentRetrieveResponse,
    DocumentGetParsedResponse,
    DocumentUploadFromURLResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestDocument:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Arbi) -> None:
        document = client.api.document.retrieve(
            external_ids=["string"],
        )
        assert_matches_type(DocumentRetrieveResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_with_all_params(self, client: Arbi) -> None:
        document = client.api.document.retrieve(
            external_ids=["string"],
            workspace_key="workspace-key",
        )
        assert_matches_type(DocumentRetrieveResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Arbi) -> None:
        response = client.api.document.with_raw_response.retrieve(
            external_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = response.parse()
        assert_matches_type(DocumentRetrieveResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Arbi) -> None:
        with client.api.document.with_streaming_response.retrieve(
            external_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = response.parse()
            assert_matches_type(DocumentRetrieveResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: Arbi) -> None:
        document = client.api.document.update(
            documents=[{"external_id": "doc-bFXA5r3A"}],
        )
        assert_matches_type(DocumentUpdateResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: Arbi) -> None:
        document = client.api.document.update(
            documents=[
                {
                    "external_id": "doc-bFXA5r3A",
                    "doc_metadata": {
                        "doc_date": parse_date("2019-12-27"),
                        "doc_summary": "doc_summary",
                        "title": "title",
                    },
                    "shared": True,
                }
            ],
            workspace_key="workspace-key",
        )
        assert_matches_type(DocumentUpdateResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: Arbi) -> None:
        response = client.api.document.with_raw_response.update(
            documents=[{"external_id": "doc-bFXA5r3A"}],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = response.parse()
        assert_matches_type(DocumentUpdateResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: Arbi) -> None:
        with client.api.document.with_streaming_response.update(
            documents=[{"external_id": "doc-bFXA5r3A"}],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = response.parse()
            assert_matches_type(DocumentUpdateResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Arbi) -> None:
        document = client.api.document.delete(
            external_ids=["string"],
        )
        assert document is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Arbi) -> None:
        response = client.api.document.with_raw_response.delete(
            external_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = response.parse()
        assert document is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Arbi) -> None:
        with client.api.document.with_streaming_response.delete(
            external_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = response.parse()
            assert document is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_download(self, client: Arbi) -> None:
        document = client.api.document.download(
            document_ext_id="doc",
        )
        assert_matches_type(object, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_download_with_all_params(self, client: Arbi) -> None:
        document = client.api.document.download(
            document_ext_id="doc",
            workspace_key="workspace-key",
        )
        assert_matches_type(object, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_download(self, client: Arbi) -> None:
        response = client.api.document.with_raw_response.download(
            document_ext_id="doc",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = response.parse()
        assert_matches_type(object, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_download(self, client: Arbi) -> None:
        with client.api.document.with_streaming_response.download(
            document_ext_id="doc",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = response.parse()
            assert_matches_type(object, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_download(self, client: Arbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `document_ext_id` but received ''"):
            client.api.document.with_raw_response.download(
                document_ext_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_parsed(self, client: Arbi) -> None:
        document = client.api.document.get_parsed(
            stage="marker",
            document_ext_id="doc",
        )
        assert_matches_type(DocumentGetParsedResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_parsed_with_all_params(self, client: Arbi) -> None:
        document = client.api.document.get_parsed(
            stage="marker",
            document_ext_id="doc",
            workspace_key="workspace-key",
        )
        assert_matches_type(DocumentGetParsedResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_parsed(self, client: Arbi) -> None:
        response = client.api.document.with_raw_response.get_parsed(
            stage="marker",
            document_ext_id="doc",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = response.parse()
        assert_matches_type(DocumentGetParsedResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_parsed(self, client: Arbi) -> None:
        with client.api.document.with_streaming_response.get_parsed(
            stage="marker",
            document_ext_id="doc",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = response.parse()
            assert_matches_type(DocumentGetParsedResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_get_parsed(self, client: Arbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `document_ext_id` but received ''"):
            client.api.document.with_raw_response.get_parsed(
                stage="marker",
                document_ext_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_upload(self, client: Arbi) -> None:
        document = client.api.document.upload(
            workspace_ext_id="wrk",
            files=[b"raw file contents"],
        )
        assert_matches_type(DocumentUploadResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_upload_with_all_params(self, client: Arbi) -> None:
        document = client.api.document.upload(
            workspace_ext_id="wrk",
            files=[b"raw file contents"],
            config_ext_id="config_ext_id",
            shared=True,
            workspace_key="workspace-key",
        )
        assert_matches_type(DocumentUploadResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_upload(self, client: Arbi) -> None:
        response = client.api.document.with_raw_response.upload(
            workspace_ext_id="wrk",
            files=[b"raw file contents"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = response.parse()
        assert_matches_type(DocumentUploadResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_upload(self, client: Arbi) -> None:
        with client.api.document.with_streaming_response.upload(
            workspace_ext_id="wrk",
            files=[b"raw file contents"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = response.parse()
            assert_matches_type(DocumentUploadResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_upload_from_url(self, client: Arbi) -> None:
        document = client.api.document.upload_from_url(
            urls=["string"],
            workspace_ext_id="wrk",
        )
        assert_matches_type(DocumentUploadFromURLResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_upload_from_url_with_all_params(self, client: Arbi) -> None:
        document = client.api.document.upload_from_url(
            urls=["string"],
            workspace_ext_id="wrk",
            config_ext_id="config_ext_id",
            shared=True,
            workspace_key="workspace-key",
        )
        assert_matches_type(DocumentUploadFromURLResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_upload_from_url(self, client: Arbi) -> None:
        response = client.api.document.with_raw_response.upload_from_url(
            urls=["string"],
            workspace_ext_id="wrk",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = response.parse()
        assert_matches_type(DocumentUploadFromURLResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_upload_from_url(self, client: Arbi) -> None:
        with client.api.document.with_streaming_response.upload_from_url(
            urls=["string"],
            workspace_ext_id="wrk",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = response.parse()
            assert_matches_type(DocumentUploadFromURLResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_view(self, client: Arbi) -> None:
        document = client.api.document.view(
            document_ext_id="doc",
        )
        assert_matches_type(object, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_view_with_all_params(self, client: Arbi) -> None:
        document = client.api.document.view(
            document_ext_id="doc",
            workspace_key="workspace-key",
        )
        assert_matches_type(object, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_view(self, client: Arbi) -> None:
        response = client.api.document.with_raw_response.view(
            document_ext_id="doc",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = response.parse()
        assert_matches_type(object, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_view(self, client: Arbi) -> None:
        with client.api.document.with_streaming_response.view(
            document_ext_id="doc",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = response.parse()
            assert_matches_type(object, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_view(self, client: Arbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `document_ext_id` but received ''"):
            client.api.document.with_raw_response.view(
                document_ext_id="",
            )


class TestAsyncDocument:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncArbi) -> None:
        document = await async_client.api.document.retrieve(
            external_ids=["string"],
        )
        assert_matches_type(DocumentRetrieveResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_with_all_params(self, async_client: AsyncArbi) -> None:
        document = await async_client.api.document.retrieve(
            external_ids=["string"],
            workspace_key="workspace-key",
        )
        assert_matches_type(DocumentRetrieveResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.document.with_raw_response.retrieve(
            external_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = await response.parse()
        assert_matches_type(DocumentRetrieveResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncArbi) -> None:
        async with async_client.api.document.with_streaming_response.retrieve(
            external_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = await response.parse()
            assert_matches_type(DocumentRetrieveResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncArbi) -> None:
        document = await async_client.api.document.update(
            documents=[{"external_id": "doc-bFXA5r3A"}],
        )
        assert_matches_type(DocumentUpdateResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncArbi) -> None:
        document = await async_client.api.document.update(
            documents=[
                {
                    "external_id": "doc-bFXA5r3A",
                    "doc_metadata": {
                        "doc_date": parse_date("2019-12-27"),
                        "doc_summary": "doc_summary",
                        "title": "title",
                    },
                    "shared": True,
                }
            ],
            workspace_key="workspace-key",
        )
        assert_matches_type(DocumentUpdateResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.document.with_raw_response.update(
            documents=[{"external_id": "doc-bFXA5r3A"}],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = await response.parse()
        assert_matches_type(DocumentUpdateResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncArbi) -> None:
        async with async_client.api.document.with_streaming_response.update(
            documents=[{"external_id": "doc-bFXA5r3A"}],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = await response.parse()
            assert_matches_type(DocumentUpdateResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncArbi) -> None:
        document = await async_client.api.document.delete(
            external_ids=["string"],
        )
        assert document is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.document.with_raw_response.delete(
            external_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = await response.parse()
        assert document is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncArbi) -> None:
        async with async_client.api.document.with_streaming_response.delete(
            external_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = await response.parse()
            assert document is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_download(self, async_client: AsyncArbi) -> None:
        document = await async_client.api.document.download(
            document_ext_id="doc",
        )
        assert_matches_type(object, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_download_with_all_params(self, async_client: AsyncArbi) -> None:
        document = await async_client.api.document.download(
            document_ext_id="doc",
            workspace_key="workspace-key",
        )
        assert_matches_type(object, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_download(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.document.with_raw_response.download(
            document_ext_id="doc",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = await response.parse()
        assert_matches_type(object, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_download(self, async_client: AsyncArbi) -> None:
        async with async_client.api.document.with_streaming_response.download(
            document_ext_id="doc",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = await response.parse()
            assert_matches_type(object, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_download(self, async_client: AsyncArbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `document_ext_id` but received ''"):
            await async_client.api.document.with_raw_response.download(
                document_ext_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_parsed(self, async_client: AsyncArbi) -> None:
        document = await async_client.api.document.get_parsed(
            stage="marker",
            document_ext_id="doc",
        )
        assert_matches_type(DocumentGetParsedResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_parsed_with_all_params(self, async_client: AsyncArbi) -> None:
        document = await async_client.api.document.get_parsed(
            stage="marker",
            document_ext_id="doc",
            workspace_key="workspace-key",
        )
        assert_matches_type(DocumentGetParsedResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_parsed(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.document.with_raw_response.get_parsed(
            stage="marker",
            document_ext_id="doc",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = await response.parse()
        assert_matches_type(DocumentGetParsedResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_parsed(self, async_client: AsyncArbi) -> None:
        async with async_client.api.document.with_streaming_response.get_parsed(
            stage="marker",
            document_ext_id="doc",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = await response.parse()
            assert_matches_type(DocumentGetParsedResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_get_parsed(self, async_client: AsyncArbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `document_ext_id` but received ''"):
            await async_client.api.document.with_raw_response.get_parsed(
                stage="marker",
                document_ext_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_upload(self, async_client: AsyncArbi) -> None:
        document = await async_client.api.document.upload(
            workspace_ext_id="wrk",
            files=[b"raw file contents"],
        )
        assert_matches_type(DocumentUploadResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_upload_with_all_params(self, async_client: AsyncArbi) -> None:
        document = await async_client.api.document.upload(
            workspace_ext_id="wrk",
            files=[b"raw file contents"],
            config_ext_id="config_ext_id",
            shared=True,
            workspace_key="workspace-key",
        )
        assert_matches_type(DocumentUploadResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_upload(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.document.with_raw_response.upload(
            workspace_ext_id="wrk",
            files=[b"raw file contents"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = await response.parse()
        assert_matches_type(DocumentUploadResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_upload(self, async_client: AsyncArbi) -> None:
        async with async_client.api.document.with_streaming_response.upload(
            workspace_ext_id="wrk",
            files=[b"raw file contents"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = await response.parse()
            assert_matches_type(DocumentUploadResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_upload_from_url(self, async_client: AsyncArbi) -> None:
        document = await async_client.api.document.upload_from_url(
            urls=["string"],
            workspace_ext_id="wrk",
        )
        assert_matches_type(DocumentUploadFromURLResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_upload_from_url_with_all_params(self, async_client: AsyncArbi) -> None:
        document = await async_client.api.document.upload_from_url(
            urls=["string"],
            workspace_ext_id="wrk",
            config_ext_id="config_ext_id",
            shared=True,
            workspace_key="workspace-key",
        )
        assert_matches_type(DocumentUploadFromURLResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_upload_from_url(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.document.with_raw_response.upload_from_url(
            urls=["string"],
            workspace_ext_id="wrk",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = await response.parse()
        assert_matches_type(DocumentUploadFromURLResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_upload_from_url(self, async_client: AsyncArbi) -> None:
        async with async_client.api.document.with_streaming_response.upload_from_url(
            urls=["string"],
            workspace_ext_id="wrk",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = await response.parse()
            assert_matches_type(DocumentUploadFromURLResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_view(self, async_client: AsyncArbi) -> None:
        document = await async_client.api.document.view(
            document_ext_id="doc",
        )
        assert_matches_type(object, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_view_with_all_params(self, async_client: AsyncArbi) -> None:
        document = await async_client.api.document.view(
            document_ext_id="doc",
            workspace_key="workspace-key",
        )
        assert_matches_type(object, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_view(self, async_client: AsyncArbi) -> None:
        response = await async_client.api.document.with_raw_response.view(
            document_ext_id="doc",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = await response.parse()
        assert_matches_type(object, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_view(self, async_client: AsyncArbi) -> None:
        async with async_client.api.document.with_streaming_response.view(
            document_ext_id="doc",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = await response.parse()
            assert_matches_type(object, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_view(self, async_client: AsyncArbi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `document_ext_id` but received ''"):
            await async_client.api.document.with_raw_response.view(
                document_ext_id="",
            )
