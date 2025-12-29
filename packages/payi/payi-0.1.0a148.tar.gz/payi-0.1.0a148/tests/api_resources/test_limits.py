# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from payi import Payi, AsyncPayi
from payi.types import (
    LimitResponse,
    DefaultResponse,
    LimitListResponse,
    LimitHistoryResponse,
)
from payi._utils import parse_datetime
from tests.utils import assert_matches_type
from payi.pagination import SyncCursorPage, AsyncCursorPage

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestLimits:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: Payi) -> None:
        limit = client.limits.create(
            limit_name="x",
            max=0,
        )
        assert_matches_type(LimitResponse, limit, path=["response"])

    @parametrize
    def test_method_create_with_all_params(self, client: Payi) -> None:
        limit = client.limits.create(
            limit_name="x",
            max=0,
            limit_id="limit_id",
            limit_type="block",
            properties={"foo": "string"},
            threshold=0,
        )
        assert_matches_type(LimitResponse, limit, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: Payi) -> None:
        response = client.limits.with_raw_response.create(
            limit_name="x",
            max=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        limit = response.parse()
        assert_matches_type(LimitResponse, limit, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: Payi) -> None:
        with client.limits.with_streaming_response.create(
            limit_name="x",
            max=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            limit = response.parse()
            assert_matches_type(LimitResponse, limit, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_retrieve(self, client: Payi) -> None:
        limit = client.limits.retrieve(
            "limit_id",
        )
        assert_matches_type(LimitResponse, limit, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: Payi) -> None:
        response = client.limits.with_raw_response.retrieve(
            "limit_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        limit = response.parse()
        assert_matches_type(LimitResponse, limit, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: Payi) -> None:
        with client.limits.with_streaming_response.retrieve(
            "limit_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            limit = response.parse()
            assert_matches_type(LimitResponse, limit, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: Payi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `limit_id` but received ''"):
            client.limits.with_raw_response.retrieve(
                "",
            )

    @parametrize
    def test_method_update(self, client: Payi) -> None:
        limit = client.limits.update(
            limit_id="limit_id",
        )
        assert_matches_type(LimitResponse, limit, path=["response"])

    @parametrize
    def test_method_update_with_all_params(self, client: Payi) -> None:
        limit = client.limits.update(
            limit_id="limit_id",
            limit_name="limit_name",
            max=1,
        )
        assert_matches_type(LimitResponse, limit, path=["response"])

    @parametrize
    def test_raw_response_update(self, client: Payi) -> None:
        response = client.limits.with_raw_response.update(
            limit_id="limit_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        limit = response.parse()
        assert_matches_type(LimitResponse, limit, path=["response"])

    @parametrize
    def test_streaming_response_update(self, client: Payi) -> None:
        with client.limits.with_streaming_response.update(
            limit_id="limit_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            limit = response.parse()
            assert_matches_type(LimitResponse, limit, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update(self, client: Payi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `limit_id` but received ''"):
            client.limits.with_raw_response.update(
                limit_id="",
            )

    @parametrize
    def test_method_list(self, client: Payi) -> None:
        limit = client.limits.list()
        assert_matches_type(SyncCursorPage[LimitListResponse], limit, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: Payi) -> None:
        limit = client.limits.list(
            cursor="cursor",
            limit=0,
            limit_name="limit_name",
            sort_ascending=True,
        )
        assert_matches_type(SyncCursorPage[LimitListResponse], limit, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: Payi) -> None:
        response = client.limits.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        limit = response.parse()
        assert_matches_type(SyncCursorPage[LimitListResponse], limit, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: Payi) -> None:
        with client.limits.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            limit = response.parse()
            assert_matches_type(SyncCursorPage[LimitListResponse], limit, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_delete(self, client: Payi) -> None:
        limit = client.limits.delete(
            "limit_id",
        )
        assert_matches_type(DefaultResponse, limit, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: Payi) -> None:
        response = client.limits.with_raw_response.delete(
            "limit_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        limit = response.parse()
        assert_matches_type(DefaultResponse, limit, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: Payi) -> None:
        with client.limits.with_streaming_response.delete(
            "limit_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            limit = response.parse()
            assert_matches_type(DefaultResponse, limit, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: Payi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `limit_id` but received ''"):
            client.limits.with_raw_response.delete(
                "",
            )

    @parametrize
    def test_method_reset(self, client: Payi) -> None:
        limit = client.limits.reset(
            limit_id="limit_id",
        )
        assert_matches_type(LimitHistoryResponse, limit, path=["response"])

    @parametrize
    def test_method_reset_with_all_params(self, client: Payi) -> None:
        limit = client.limits.reset(
            limit_id="limit_id",
            reset_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(LimitHistoryResponse, limit, path=["response"])

    @parametrize
    def test_raw_response_reset(self, client: Payi) -> None:
        response = client.limits.with_raw_response.reset(
            limit_id="limit_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        limit = response.parse()
        assert_matches_type(LimitHistoryResponse, limit, path=["response"])

    @parametrize
    def test_streaming_response_reset(self, client: Payi) -> None:
        with client.limits.with_streaming_response.reset(
            limit_id="limit_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            limit = response.parse()
            assert_matches_type(LimitHistoryResponse, limit, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_reset(self, client: Payi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `limit_id` but received ''"):
            client.limits.with_raw_response.reset(
                limit_id="",
            )


class TestAsyncLimits:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncPayi) -> None:
        limit = await async_client.limits.create(
            limit_name="x",
            max=0,
        )
        assert_matches_type(LimitResponse, limit, path=["response"])

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncPayi) -> None:
        limit = await async_client.limits.create(
            limit_name="x",
            max=0,
            limit_id="limit_id",
            limit_type="block",
            properties={"foo": "string"},
            threshold=0,
        )
        assert_matches_type(LimitResponse, limit, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncPayi) -> None:
        response = await async_client.limits.with_raw_response.create(
            limit_name="x",
            max=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        limit = await response.parse()
        assert_matches_type(LimitResponse, limit, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncPayi) -> None:
        async with async_client.limits.with_streaming_response.create(
            limit_name="x",
            max=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            limit = await response.parse()
            assert_matches_type(LimitResponse, limit, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncPayi) -> None:
        limit = await async_client.limits.retrieve(
            "limit_id",
        )
        assert_matches_type(LimitResponse, limit, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncPayi) -> None:
        response = await async_client.limits.with_raw_response.retrieve(
            "limit_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        limit = await response.parse()
        assert_matches_type(LimitResponse, limit, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncPayi) -> None:
        async with async_client.limits.with_streaming_response.retrieve(
            "limit_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            limit = await response.parse()
            assert_matches_type(LimitResponse, limit, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncPayi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `limit_id` but received ''"):
            await async_client.limits.with_raw_response.retrieve(
                "",
            )

    @parametrize
    async def test_method_update(self, async_client: AsyncPayi) -> None:
        limit = await async_client.limits.update(
            limit_id="limit_id",
        )
        assert_matches_type(LimitResponse, limit, path=["response"])

    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncPayi) -> None:
        limit = await async_client.limits.update(
            limit_id="limit_id",
            limit_name="limit_name",
            max=1,
        )
        assert_matches_type(LimitResponse, limit, path=["response"])

    @parametrize
    async def test_raw_response_update(self, async_client: AsyncPayi) -> None:
        response = await async_client.limits.with_raw_response.update(
            limit_id="limit_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        limit = await response.parse()
        assert_matches_type(LimitResponse, limit, path=["response"])

    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncPayi) -> None:
        async with async_client.limits.with_streaming_response.update(
            limit_id="limit_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            limit = await response.parse()
            assert_matches_type(LimitResponse, limit, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update(self, async_client: AsyncPayi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `limit_id` but received ''"):
            await async_client.limits.with_raw_response.update(
                limit_id="",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncPayi) -> None:
        limit = await async_client.limits.list()
        assert_matches_type(AsyncCursorPage[LimitListResponse], limit, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncPayi) -> None:
        limit = await async_client.limits.list(
            cursor="cursor",
            limit=0,
            limit_name="limit_name",
            sort_ascending=True,
        )
        assert_matches_type(AsyncCursorPage[LimitListResponse], limit, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncPayi) -> None:
        response = await async_client.limits.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        limit = await response.parse()
        assert_matches_type(AsyncCursorPage[LimitListResponse], limit, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncPayi) -> None:
        async with async_client.limits.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            limit = await response.parse()
            assert_matches_type(AsyncCursorPage[LimitListResponse], limit, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_delete(self, async_client: AsyncPayi) -> None:
        limit = await async_client.limits.delete(
            "limit_id",
        )
        assert_matches_type(DefaultResponse, limit, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncPayi) -> None:
        response = await async_client.limits.with_raw_response.delete(
            "limit_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        limit = await response.parse()
        assert_matches_type(DefaultResponse, limit, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncPayi) -> None:
        async with async_client.limits.with_streaming_response.delete(
            "limit_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            limit = await response.parse()
            assert_matches_type(DefaultResponse, limit, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncPayi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `limit_id` but received ''"):
            await async_client.limits.with_raw_response.delete(
                "",
            )

    @parametrize
    async def test_method_reset(self, async_client: AsyncPayi) -> None:
        limit = await async_client.limits.reset(
            limit_id="limit_id",
        )
        assert_matches_type(LimitHistoryResponse, limit, path=["response"])

    @parametrize
    async def test_method_reset_with_all_params(self, async_client: AsyncPayi) -> None:
        limit = await async_client.limits.reset(
            limit_id="limit_id",
            reset_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(LimitHistoryResponse, limit, path=["response"])

    @parametrize
    async def test_raw_response_reset(self, async_client: AsyncPayi) -> None:
        response = await async_client.limits.with_raw_response.reset(
            limit_id="limit_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        limit = await response.parse()
        assert_matches_type(LimitHistoryResponse, limit, path=["response"])

    @parametrize
    async def test_streaming_response_reset(self, async_client: AsyncPayi) -> None:
        async with async_client.limits.with_streaming_response.reset(
            limit_id="limit_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            limit = await response.parse()
            assert_matches_type(LimitHistoryResponse, limit, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_reset(self, async_client: AsyncPayi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `limit_id` but received ''"):
            await async_client.limits.with_raw_response.reset(
                limit_id="",
            )
