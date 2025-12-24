# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from supermemory import Supermemory, AsyncSupermemory
from tests.utils import assert_matches_type
from supermemory.types import (
    DocumentAddResponse,
    DocumentGetResponse,
    DocumentListResponse,
    DocumentUpdateResponse,
    DocumentBatchAddResponse,
    DocumentDeleteBulkResponse,
    DocumentUploadFileResponse,
    DocumentListProcessingResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestDocuments:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: Supermemory) -> None:
        document = client.documents.update(
            id="id",
        )
        assert_matches_type(DocumentUpdateResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: Supermemory) -> None:
        document = client.documents.update(
            id="id",
            container_tag="user_123",
            container_tags=["user_123", "project_123"],
            content="This is a detailed article about machine learning concepts...",
            custom_id="mem_abc123",
            metadata={
                "category": "technology",
                "isPublic": True,
                "readingTime": 5,
                "source": "web",
                "tag_1": "ai",
                "tag_2": "machine-learning",
            },
        )
        assert_matches_type(DocumentUpdateResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: Supermemory) -> None:
        response = client.documents.with_raw_response.update(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = response.parse()
        assert_matches_type(DocumentUpdateResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: Supermemory) -> None:
        with client.documents.with_streaming_response.update(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = response.parse()
            assert_matches_type(DocumentUpdateResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: Supermemory) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.documents.with_raw_response.update(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Supermemory) -> None:
        document = client.documents.list()
        assert_matches_type(DocumentListResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Supermemory) -> None:
        document = client.documents.list(
            container_tags=["user_123", "project_123"],
            filters={
                "and_": [
                    {
                        "key": "group",
                        "value": "jira_users",
                        "filter_type": "metadata",
                        "ignore_case": True,
                        "negate": False,
                        "numeric_operator": ">",
                    },
                    {
                        "key": "timestamp",
                        "value": "1742745777",
                        "filter_type": "numeric",
                        "ignore_case": True,
                        "negate": False,
                        "numeric_operator": ">",
                    },
                ]
            },
            include_content=False,
            limit=10,
            order="desc",
            page=1,
            sort="createdAt",
        )
        assert_matches_type(DocumentListResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Supermemory) -> None:
        response = client.documents.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = response.parse()
        assert_matches_type(DocumentListResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Supermemory) -> None:
        with client.documents.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = response.parse()
            assert_matches_type(DocumentListResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Supermemory) -> None:
        document = client.documents.delete(
            "id",
        )
        assert document is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Supermemory) -> None:
        response = client.documents.with_raw_response.delete(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = response.parse()
        assert document is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Supermemory) -> None:
        with client.documents.with_streaming_response.delete(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = response.parse()
            assert document is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: Supermemory) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.documents.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_add(self, client: Supermemory) -> None:
        document = client.documents.add(
            content="content",
        )
        assert_matches_type(DocumentAddResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_add_with_all_params(self, client: Supermemory) -> None:
        document = client.documents.add(
            content="content",
            container_tag="containerTag",
            container_tags=["string"],
            custom_id="customId",
            metadata={"foo": "string"},
        )
        assert_matches_type(DocumentAddResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_add(self, client: Supermemory) -> None:
        response = client.documents.with_raw_response.add(
            content="content",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = response.parse()
        assert_matches_type(DocumentAddResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_add(self, client: Supermemory) -> None:
        with client.documents.with_streaming_response.add(
            content="content",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = response.parse()
            assert_matches_type(DocumentAddResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_batch_add(self, client: Supermemory) -> None:
        document = client.documents.batch_add(
            documents=[{"content": "This is a detailed article about machine learning concepts..."}],
        )
        assert_matches_type(DocumentBatchAddResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_batch_add_with_all_params(self, client: Supermemory) -> None:
        document = client.documents.batch_add(
            documents=[
                {
                    "content": "This is a detailed article about machine learning concepts...",
                    "container_tag": "user_123",
                    "container_tags": ["user_123", "project_123"],
                    "custom_id": "mem_abc123",
                    "metadata": {
                        "category": "technology",
                        "isPublic": True,
                        "readingTime": 5,
                        "source": "web",
                        "tag_1": "ai",
                        "tag_2": "machine-learning",
                    },
                }
            ],
            container_tag="user_123",
            container_tags=["user_123", "project_123"],
            content=None,
            metadata={
                "category": "technology",
                "isPublic": True,
                "readingTime": 5,
                "source": "web",
                "tag_1": "ai",
                "tag_2": "machine-learning",
            },
        )
        assert_matches_type(DocumentBatchAddResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_batch_add(self, client: Supermemory) -> None:
        response = client.documents.with_raw_response.batch_add(
            documents=[{"content": "This is a detailed article about machine learning concepts..."}],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = response.parse()
        assert_matches_type(DocumentBatchAddResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_batch_add(self, client: Supermemory) -> None:
        with client.documents.with_streaming_response.batch_add(
            documents=[{"content": "This is a detailed article about machine learning concepts..."}],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = response.parse()
            assert_matches_type(DocumentBatchAddResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete_bulk(self, client: Supermemory) -> None:
        document = client.documents.delete_bulk()
        assert_matches_type(DocumentDeleteBulkResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete_bulk_with_all_params(self, client: Supermemory) -> None:
        document = client.documents.delete_bulk(
            container_tags=["user_123", "project_123"],
            ids=["acxV5LHMEsG2hMSNb4umbn", "bxcV5LHMEsG2hMSNb4umbn"],
        )
        assert_matches_type(DocumentDeleteBulkResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete_bulk(self, client: Supermemory) -> None:
        response = client.documents.with_raw_response.delete_bulk()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = response.parse()
        assert_matches_type(DocumentDeleteBulkResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete_bulk(self, client: Supermemory) -> None:
        with client.documents.with_streaming_response.delete_bulk() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = response.parse()
            assert_matches_type(DocumentDeleteBulkResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get(self, client: Supermemory) -> None:
        document = client.documents.get(
            "id",
        )
        assert_matches_type(DocumentGetResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get(self, client: Supermemory) -> None:
        response = client.documents.with_raw_response.get(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = response.parse()
        assert_matches_type(DocumentGetResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get(self, client: Supermemory) -> None:
        with client.documents.with_streaming_response.get(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = response.parse()
            assert_matches_type(DocumentGetResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_get(self, client: Supermemory) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.documents.with_raw_response.get(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_processing(self, client: Supermemory) -> None:
        document = client.documents.list_processing()
        assert_matches_type(DocumentListProcessingResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_processing(self, client: Supermemory) -> None:
        response = client.documents.with_raw_response.list_processing()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = response.parse()
        assert_matches_type(DocumentListProcessingResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_processing(self, client: Supermemory) -> None:
        with client.documents.with_streaming_response.list_processing() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = response.parse()
            assert_matches_type(DocumentListProcessingResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_upload_file(self, client: Supermemory) -> None:
        document = client.documents.upload_file(
            file=b"raw file contents",
        )
        assert_matches_type(DocumentUploadFileResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_upload_file_with_all_params(self, client: Supermemory) -> None:
        document = client.documents.upload_file(
            file=b"raw file contents",
            container_tags='["user_123", "project_123"]',
            file_type="image",
            metadata='{"category": "technology", "isPublic": true, "readingTime": 5}',
            mime_type="mimeType",
            use_advanced_processing="true",
        )
        assert_matches_type(DocumentUploadFileResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_upload_file(self, client: Supermemory) -> None:
        response = client.documents.with_raw_response.upload_file(
            file=b"raw file contents",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = response.parse()
        assert_matches_type(DocumentUploadFileResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_upload_file(self, client: Supermemory) -> None:
        with client.documents.with_streaming_response.upload_file(
            file=b"raw file contents",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = response.parse()
            assert_matches_type(DocumentUploadFileResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncDocuments:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncSupermemory) -> None:
        document = await async_client.documents.update(
            id="id",
        )
        assert_matches_type(DocumentUpdateResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncSupermemory) -> None:
        document = await async_client.documents.update(
            id="id",
            container_tag="user_123",
            container_tags=["user_123", "project_123"],
            content="This is a detailed article about machine learning concepts...",
            custom_id="mem_abc123",
            metadata={
                "category": "technology",
                "isPublic": True,
                "readingTime": 5,
                "source": "web",
                "tag_1": "ai",
                "tag_2": "machine-learning",
            },
        )
        assert_matches_type(DocumentUpdateResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncSupermemory) -> None:
        response = await async_client.documents.with_raw_response.update(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = await response.parse()
        assert_matches_type(DocumentUpdateResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncSupermemory) -> None:
        async with async_client.documents.with_streaming_response.update(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = await response.parse()
            assert_matches_type(DocumentUpdateResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncSupermemory) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.documents.with_raw_response.update(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncSupermemory) -> None:
        document = await async_client.documents.list()
        assert_matches_type(DocumentListResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncSupermemory) -> None:
        document = await async_client.documents.list(
            container_tags=["user_123", "project_123"],
            filters={
                "and_": [
                    {
                        "key": "group",
                        "value": "jira_users",
                        "filter_type": "metadata",
                        "ignore_case": True,
                        "negate": False,
                        "numeric_operator": ">",
                    },
                    {
                        "key": "timestamp",
                        "value": "1742745777",
                        "filter_type": "numeric",
                        "ignore_case": True,
                        "negate": False,
                        "numeric_operator": ">",
                    },
                ]
            },
            include_content=False,
            limit=10,
            order="desc",
            page=1,
            sort="createdAt",
        )
        assert_matches_type(DocumentListResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncSupermemory) -> None:
        response = await async_client.documents.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = await response.parse()
        assert_matches_type(DocumentListResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncSupermemory) -> None:
        async with async_client.documents.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = await response.parse()
            assert_matches_type(DocumentListResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncSupermemory) -> None:
        document = await async_client.documents.delete(
            "id",
        )
        assert document is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncSupermemory) -> None:
        response = await async_client.documents.with_raw_response.delete(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = await response.parse()
        assert document is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncSupermemory) -> None:
        async with async_client.documents.with_streaming_response.delete(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = await response.parse()
            assert document is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncSupermemory) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.documents.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_add(self, async_client: AsyncSupermemory) -> None:
        document = await async_client.documents.add(
            content="content",
        )
        assert_matches_type(DocumentAddResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_add_with_all_params(self, async_client: AsyncSupermemory) -> None:
        document = await async_client.documents.add(
            content="content",
            container_tag="containerTag",
            container_tags=["string"],
            custom_id="customId",
            metadata={"foo": "string"},
        )
        assert_matches_type(DocumentAddResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_add(self, async_client: AsyncSupermemory) -> None:
        response = await async_client.documents.with_raw_response.add(
            content="content",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = await response.parse()
        assert_matches_type(DocumentAddResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_add(self, async_client: AsyncSupermemory) -> None:
        async with async_client.documents.with_streaming_response.add(
            content="content",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = await response.parse()
            assert_matches_type(DocumentAddResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_batch_add(self, async_client: AsyncSupermemory) -> None:
        document = await async_client.documents.batch_add(
            documents=[{"content": "This is a detailed article about machine learning concepts..."}],
        )
        assert_matches_type(DocumentBatchAddResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_batch_add_with_all_params(self, async_client: AsyncSupermemory) -> None:
        document = await async_client.documents.batch_add(
            documents=[
                {
                    "content": "This is a detailed article about machine learning concepts...",
                    "container_tag": "user_123",
                    "container_tags": ["user_123", "project_123"],
                    "custom_id": "mem_abc123",
                    "metadata": {
                        "category": "technology",
                        "isPublic": True,
                        "readingTime": 5,
                        "source": "web",
                        "tag_1": "ai",
                        "tag_2": "machine-learning",
                    },
                }
            ],
            container_tag="user_123",
            container_tags=["user_123", "project_123"],
            content=None,
            metadata={
                "category": "technology",
                "isPublic": True,
                "readingTime": 5,
                "source": "web",
                "tag_1": "ai",
                "tag_2": "machine-learning",
            },
        )
        assert_matches_type(DocumentBatchAddResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_batch_add(self, async_client: AsyncSupermemory) -> None:
        response = await async_client.documents.with_raw_response.batch_add(
            documents=[{"content": "This is a detailed article about machine learning concepts..."}],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = await response.parse()
        assert_matches_type(DocumentBatchAddResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_batch_add(self, async_client: AsyncSupermemory) -> None:
        async with async_client.documents.with_streaming_response.batch_add(
            documents=[{"content": "This is a detailed article about machine learning concepts..."}],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = await response.parse()
            assert_matches_type(DocumentBatchAddResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete_bulk(self, async_client: AsyncSupermemory) -> None:
        document = await async_client.documents.delete_bulk()
        assert_matches_type(DocumentDeleteBulkResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete_bulk_with_all_params(self, async_client: AsyncSupermemory) -> None:
        document = await async_client.documents.delete_bulk(
            container_tags=["user_123", "project_123"],
            ids=["acxV5LHMEsG2hMSNb4umbn", "bxcV5LHMEsG2hMSNb4umbn"],
        )
        assert_matches_type(DocumentDeleteBulkResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete_bulk(self, async_client: AsyncSupermemory) -> None:
        response = await async_client.documents.with_raw_response.delete_bulk()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = await response.parse()
        assert_matches_type(DocumentDeleteBulkResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete_bulk(self, async_client: AsyncSupermemory) -> None:
        async with async_client.documents.with_streaming_response.delete_bulk() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = await response.parse()
            assert_matches_type(DocumentDeleteBulkResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get(self, async_client: AsyncSupermemory) -> None:
        document = await async_client.documents.get(
            "id",
        )
        assert_matches_type(DocumentGetResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get(self, async_client: AsyncSupermemory) -> None:
        response = await async_client.documents.with_raw_response.get(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = await response.parse()
        assert_matches_type(DocumentGetResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get(self, async_client: AsyncSupermemory) -> None:
        async with async_client.documents.with_streaming_response.get(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = await response.parse()
            assert_matches_type(DocumentGetResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_get(self, async_client: AsyncSupermemory) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.documents.with_raw_response.get(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_processing(self, async_client: AsyncSupermemory) -> None:
        document = await async_client.documents.list_processing()
        assert_matches_type(DocumentListProcessingResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_processing(self, async_client: AsyncSupermemory) -> None:
        response = await async_client.documents.with_raw_response.list_processing()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = await response.parse()
        assert_matches_type(DocumentListProcessingResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_processing(self, async_client: AsyncSupermemory) -> None:
        async with async_client.documents.with_streaming_response.list_processing() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = await response.parse()
            assert_matches_type(DocumentListProcessingResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_upload_file(self, async_client: AsyncSupermemory) -> None:
        document = await async_client.documents.upload_file(
            file=b"raw file contents",
        )
        assert_matches_type(DocumentUploadFileResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_upload_file_with_all_params(self, async_client: AsyncSupermemory) -> None:
        document = await async_client.documents.upload_file(
            file=b"raw file contents",
            container_tags='["user_123", "project_123"]',
            file_type="image",
            metadata='{"category": "technology", "isPublic": true, "readingTime": 5}',
            mime_type="mimeType",
            use_advanced_processing="true",
        )
        assert_matches_type(DocumentUploadFileResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_upload_file(self, async_client: AsyncSupermemory) -> None:
        response = await async_client.documents.with_raw_response.upload_file(
            file=b"raw file contents",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = await response.parse()
        assert_matches_type(DocumentUploadFileResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_upload_file(self, async_client: AsyncSupermemory) -> None:
        async with async_client.documents.with_streaming_response.upload_file(
            file=b"raw file contents",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = await response.parse()
            assert_matches_type(DocumentUploadFileResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True
