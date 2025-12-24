# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from supermemory import Supermemory, AsyncSupermemory
from tests.utils import assert_matches_type
from supermemory.types import (
    MemoryAddResponse,
    MemoryGetResponse,
    MemoryListResponse,
    MemoryForgetResponse,
    MemoryUpdateResponse,
    MemoryUploadFileResponse,
    MemoryUpdateMemoryResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestMemories:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: Supermemory) -> None:
        memory = client.memories.update(
            id="id",
        )
        assert_matches_type(MemoryUpdateResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: Supermemory) -> None:
        memory = client.memories.update(
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
        assert_matches_type(MemoryUpdateResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: Supermemory) -> None:
        response = client.memories.with_raw_response.update(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = response.parse()
        assert_matches_type(MemoryUpdateResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: Supermemory) -> None:
        with client.memories.with_streaming_response.update(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = response.parse()
            assert_matches_type(MemoryUpdateResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: Supermemory) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.memories.with_raw_response.update(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Supermemory) -> None:
        memory = client.memories.list()
        assert_matches_type(MemoryListResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Supermemory) -> None:
        memory = client.memories.list(
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
        assert_matches_type(MemoryListResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Supermemory) -> None:
        response = client.memories.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = response.parse()
        assert_matches_type(MemoryListResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Supermemory) -> None:
        with client.memories.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = response.parse()
            assert_matches_type(MemoryListResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Supermemory) -> None:
        memory = client.memories.delete(
            "id",
        )
        assert memory is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Supermemory) -> None:
        response = client.memories.with_raw_response.delete(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = response.parse()
        assert memory is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Supermemory) -> None:
        with client.memories.with_streaming_response.delete(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = response.parse()
            assert memory is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: Supermemory) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.memories.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_add(self, client: Supermemory) -> None:
        memory = client.memories.add(
            content="content",
        )
        assert_matches_type(MemoryAddResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_add_with_all_params(self, client: Supermemory) -> None:
        memory = client.memories.add(
            content="content",
            container_tag="containerTag",
            container_tags=["string"],
            custom_id="customId",
            metadata={"foo": "string"},
        )
        assert_matches_type(MemoryAddResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_add(self, client: Supermemory) -> None:
        response = client.memories.with_raw_response.add(
            content="content",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = response.parse()
        assert_matches_type(MemoryAddResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_add(self, client: Supermemory) -> None:
        with client.memories.with_streaming_response.add(
            content="content",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = response.parse()
            assert_matches_type(MemoryAddResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_forget(self, client: Supermemory) -> None:
        memory = client.memories.forget(
            container_tag="user_123",
        )
        assert_matches_type(MemoryForgetResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_forget_with_all_params(self, client: Supermemory) -> None:
        memory = client.memories.forget(
            container_tag="user_123",
            id="mem_abc123",
            content="John prefers dark mode",
            reason="outdated information",
        )
        assert_matches_type(MemoryForgetResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_forget(self, client: Supermemory) -> None:
        response = client.memories.with_raw_response.forget(
            container_tag="user_123",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = response.parse()
        assert_matches_type(MemoryForgetResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_forget(self, client: Supermemory) -> None:
        with client.memories.with_streaming_response.forget(
            container_tag="user_123",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = response.parse()
            assert_matches_type(MemoryForgetResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get(self, client: Supermemory) -> None:
        memory = client.memories.get(
            "id",
        )
        assert_matches_type(MemoryGetResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get(self, client: Supermemory) -> None:
        response = client.memories.with_raw_response.get(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = response.parse()
        assert_matches_type(MemoryGetResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get(self, client: Supermemory) -> None:
        with client.memories.with_streaming_response.get(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = response.parse()
            assert_matches_type(MemoryGetResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_get(self, client: Supermemory) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.memories.with_raw_response.get(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_memory(self, client: Supermemory) -> None:
        memory = client.memories.update_memory(
            container_tag="user_123",
            new_content="John now prefers light mode",
        )
        assert_matches_type(MemoryUpdateMemoryResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_memory_with_all_params(self, client: Supermemory) -> None:
        memory = client.memories.update_memory(
            container_tag="user_123",
            new_content="John now prefers light mode",
            id="mem_abc123",
            content="John prefers dark mode",
            metadata={"foo": "string"},
        )
        assert_matches_type(MemoryUpdateMemoryResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update_memory(self, client: Supermemory) -> None:
        response = client.memories.with_raw_response.update_memory(
            container_tag="user_123",
            new_content="John now prefers light mode",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = response.parse()
        assert_matches_type(MemoryUpdateMemoryResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update_memory(self, client: Supermemory) -> None:
        with client.memories.with_streaming_response.update_memory(
            container_tag="user_123",
            new_content="John now prefers light mode",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = response.parse()
            assert_matches_type(MemoryUpdateMemoryResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_upload_file(self, client: Supermemory) -> None:
        memory = client.memories.upload_file(
            file=b"raw file contents",
        )
        assert_matches_type(MemoryUploadFileResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_upload_file_with_all_params(self, client: Supermemory) -> None:
        memory = client.memories.upload_file(
            file=b"raw file contents",
            container_tags='["user_123", "project_123"]',
            file_type="image",
            metadata='{"category": "technology", "isPublic": true, "readingTime": 5}',
            mime_type="mimeType",
            use_advanced_processing="true",
        )
        assert_matches_type(MemoryUploadFileResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_upload_file(self, client: Supermemory) -> None:
        response = client.memories.with_raw_response.upload_file(
            file=b"raw file contents",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = response.parse()
        assert_matches_type(MemoryUploadFileResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_upload_file(self, client: Supermemory) -> None:
        with client.memories.with_streaming_response.upload_file(
            file=b"raw file contents",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = response.parse()
            assert_matches_type(MemoryUploadFileResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncMemories:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncSupermemory) -> None:
        memory = await async_client.memories.update(
            id="id",
        )
        assert_matches_type(MemoryUpdateResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncSupermemory) -> None:
        memory = await async_client.memories.update(
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
        assert_matches_type(MemoryUpdateResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncSupermemory) -> None:
        response = await async_client.memories.with_raw_response.update(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = await response.parse()
        assert_matches_type(MemoryUpdateResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncSupermemory) -> None:
        async with async_client.memories.with_streaming_response.update(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = await response.parse()
            assert_matches_type(MemoryUpdateResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncSupermemory) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.memories.with_raw_response.update(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncSupermemory) -> None:
        memory = await async_client.memories.list()
        assert_matches_type(MemoryListResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncSupermemory) -> None:
        memory = await async_client.memories.list(
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
        assert_matches_type(MemoryListResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncSupermemory) -> None:
        response = await async_client.memories.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = await response.parse()
        assert_matches_type(MemoryListResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncSupermemory) -> None:
        async with async_client.memories.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = await response.parse()
            assert_matches_type(MemoryListResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncSupermemory) -> None:
        memory = await async_client.memories.delete(
            "id",
        )
        assert memory is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncSupermemory) -> None:
        response = await async_client.memories.with_raw_response.delete(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = await response.parse()
        assert memory is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncSupermemory) -> None:
        async with async_client.memories.with_streaming_response.delete(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = await response.parse()
            assert memory is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncSupermemory) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.memories.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_add(self, async_client: AsyncSupermemory) -> None:
        memory = await async_client.memories.add(
            content="content",
        )
        assert_matches_type(MemoryAddResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_add_with_all_params(self, async_client: AsyncSupermemory) -> None:
        memory = await async_client.memories.add(
            content="content",
            container_tag="containerTag",
            container_tags=["string"],
            custom_id="customId",
            metadata={"foo": "string"},
        )
        assert_matches_type(MemoryAddResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_add(self, async_client: AsyncSupermemory) -> None:
        response = await async_client.memories.with_raw_response.add(
            content="content",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = await response.parse()
        assert_matches_type(MemoryAddResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_add(self, async_client: AsyncSupermemory) -> None:
        async with async_client.memories.with_streaming_response.add(
            content="content",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = await response.parse()
            assert_matches_type(MemoryAddResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_forget(self, async_client: AsyncSupermemory) -> None:
        memory = await async_client.memories.forget(
            container_tag="user_123",
        )
        assert_matches_type(MemoryForgetResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_forget_with_all_params(self, async_client: AsyncSupermemory) -> None:
        memory = await async_client.memories.forget(
            container_tag="user_123",
            id="mem_abc123",
            content="John prefers dark mode",
            reason="outdated information",
        )
        assert_matches_type(MemoryForgetResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_forget(self, async_client: AsyncSupermemory) -> None:
        response = await async_client.memories.with_raw_response.forget(
            container_tag="user_123",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = await response.parse()
        assert_matches_type(MemoryForgetResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_forget(self, async_client: AsyncSupermemory) -> None:
        async with async_client.memories.with_streaming_response.forget(
            container_tag="user_123",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = await response.parse()
            assert_matches_type(MemoryForgetResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get(self, async_client: AsyncSupermemory) -> None:
        memory = await async_client.memories.get(
            "id",
        )
        assert_matches_type(MemoryGetResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get(self, async_client: AsyncSupermemory) -> None:
        response = await async_client.memories.with_raw_response.get(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = await response.parse()
        assert_matches_type(MemoryGetResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get(self, async_client: AsyncSupermemory) -> None:
        async with async_client.memories.with_streaming_response.get(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = await response.parse()
            assert_matches_type(MemoryGetResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_get(self, async_client: AsyncSupermemory) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.memories.with_raw_response.get(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_memory(self, async_client: AsyncSupermemory) -> None:
        memory = await async_client.memories.update_memory(
            container_tag="user_123",
            new_content="John now prefers light mode",
        )
        assert_matches_type(MemoryUpdateMemoryResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_memory_with_all_params(self, async_client: AsyncSupermemory) -> None:
        memory = await async_client.memories.update_memory(
            container_tag="user_123",
            new_content="John now prefers light mode",
            id="mem_abc123",
            content="John prefers dark mode",
            metadata={"foo": "string"},
        )
        assert_matches_type(MemoryUpdateMemoryResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update_memory(self, async_client: AsyncSupermemory) -> None:
        response = await async_client.memories.with_raw_response.update_memory(
            container_tag="user_123",
            new_content="John now prefers light mode",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = await response.parse()
        assert_matches_type(MemoryUpdateMemoryResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update_memory(self, async_client: AsyncSupermemory) -> None:
        async with async_client.memories.with_streaming_response.update_memory(
            container_tag="user_123",
            new_content="John now prefers light mode",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = await response.parse()
            assert_matches_type(MemoryUpdateMemoryResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_upload_file(self, async_client: AsyncSupermemory) -> None:
        memory = await async_client.memories.upload_file(
            file=b"raw file contents",
        )
        assert_matches_type(MemoryUploadFileResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_upload_file_with_all_params(self, async_client: AsyncSupermemory) -> None:
        memory = await async_client.memories.upload_file(
            file=b"raw file contents",
            container_tags='["user_123", "project_123"]',
            file_type="image",
            metadata='{"category": "technology", "isPublic": true, "readingTime": 5}',
            mime_type="mimeType",
            use_advanced_processing="true",
        )
        assert_matches_type(MemoryUploadFileResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_upload_file(self, async_client: AsyncSupermemory) -> None:
        response = await async_client.memories.with_raw_response.upload_file(
            file=b"raw file contents",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = await response.parse()
        assert_matches_type(MemoryUploadFileResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_upload_file(self, async_client: AsyncSupermemory) -> None:
        async with async_client.memories.with_streaming_response.upload_file(
            file=b"raw file contents",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = await response.parse()
            assert_matches_type(MemoryUploadFileResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True
