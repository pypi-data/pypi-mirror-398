# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from payi import Payi, AsyncPayi
from payi.types import CategoryResourceResponse
from payi._utils import parse_datetime
from tests.utils import assert_matches_type
from payi.pagination import SyncCursorPage, AsyncCursorPage

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestResources:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: Payi) -> None:
        resource = client.categories.resources.create(
            resource="resource",
            category="category",
            units={"foo": {}},
        )
        assert_matches_type(CategoryResourceResponse, resource, path=["response"])

    @parametrize
    def test_method_create_with_all_params(self, client: Payi) -> None:
        resource = client.categories.resources.create(
            resource="resource",
            category="category",
            units={
                "foo": {
                    "input_price": 0,
                    "output_price": 0,
                }
            },
            max_input_units=0,
            max_output_units=0,
            max_total_units=0,
            start_timestamp=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(CategoryResourceResponse, resource, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: Payi) -> None:
        response = client.categories.resources.with_raw_response.create(
            resource="resource",
            category="category",
            units={"foo": {}},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource = response.parse()
        assert_matches_type(CategoryResourceResponse, resource, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: Payi) -> None:
        with client.categories.resources.with_streaming_response.create(
            resource="resource",
            category="category",
            units={"foo": {}},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource = response.parse()
            assert_matches_type(CategoryResourceResponse, resource, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_create(self, client: Payi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `category` but received ''"):
            client.categories.resources.with_raw_response.create(
                resource="resource",
                category="",
                units={"foo": {}},
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `resource` but received ''"):
            client.categories.resources.with_raw_response.create(
                resource="",
                category="category",
                units={"foo": {}},
            )

    @parametrize
    def test_method_retrieve(self, client: Payi) -> None:
        resource = client.categories.resources.retrieve(
            resource_id="resource_id",
            category="category",
            resource="resource",
        )
        assert_matches_type(CategoryResourceResponse, resource, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: Payi) -> None:
        response = client.categories.resources.with_raw_response.retrieve(
            resource_id="resource_id",
            category="category",
            resource="resource",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource = response.parse()
        assert_matches_type(CategoryResourceResponse, resource, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: Payi) -> None:
        with client.categories.resources.with_streaming_response.retrieve(
            resource_id="resource_id",
            category="category",
            resource="resource",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource = response.parse()
            assert_matches_type(CategoryResourceResponse, resource, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: Payi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `category` but received ''"):
            client.categories.resources.with_raw_response.retrieve(
                resource_id="resource_id",
                category="",
                resource="resource",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `resource` but received ''"):
            client.categories.resources.with_raw_response.retrieve(
                resource_id="resource_id",
                category="category",
                resource="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `resource_id` but received ''"):
            client.categories.resources.with_raw_response.retrieve(
                resource_id="",
                category="category",
                resource="resource",
            )

    @parametrize
    def test_method_list(self, client: Payi) -> None:
        resource = client.categories.resources.list(
            resource="resource",
            category="category",
        )
        assert_matches_type(SyncCursorPage[CategoryResourceResponse], resource, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: Payi) -> None:
        resource = client.categories.resources.list(
            resource="resource",
            category="category",
            active=True,
            cursor="cursor",
            limit=0,
            sort_ascending=True,
        )
        assert_matches_type(SyncCursorPage[CategoryResourceResponse], resource, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: Payi) -> None:
        response = client.categories.resources.with_raw_response.list(
            resource="resource",
            category="category",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource = response.parse()
        assert_matches_type(SyncCursorPage[CategoryResourceResponse], resource, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: Payi) -> None:
        with client.categories.resources.with_streaming_response.list(
            resource="resource",
            category="category",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource = response.parse()
            assert_matches_type(SyncCursorPage[CategoryResourceResponse], resource, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_list(self, client: Payi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `category` but received ''"):
            client.categories.resources.with_raw_response.list(
                resource="resource",
                category="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `resource` but received ''"):
            client.categories.resources.with_raw_response.list(
                resource="",
                category="category",
            )

    @parametrize
    def test_method_delete(self, client: Payi) -> None:
        resource = client.categories.resources.delete(
            resource_id="resource_id",
            category="category",
            resource="resource",
        )
        assert_matches_type(CategoryResourceResponse, resource, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: Payi) -> None:
        response = client.categories.resources.with_raw_response.delete(
            resource_id="resource_id",
            category="category",
            resource="resource",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource = response.parse()
        assert_matches_type(CategoryResourceResponse, resource, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: Payi) -> None:
        with client.categories.resources.with_streaming_response.delete(
            resource_id="resource_id",
            category="category",
            resource="resource",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource = response.parse()
            assert_matches_type(CategoryResourceResponse, resource, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: Payi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `category` but received ''"):
            client.categories.resources.with_raw_response.delete(
                resource_id="resource_id",
                category="",
                resource="resource",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `resource` but received ''"):
            client.categories.resources.with_raw_response.delete(
                resource_id="resource_id",
                category="category",
                resource="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `resource_id` but received ''"):
            client.categories.resources.with_raw_response.delete(
                resource_id="",
                category="category",
                resource="resource",
            )


class TestAsyncResources:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncPayi) -> None:
        resource = await async_client.categories.resources.create(
            resource="resource",
            category="category",
            units={"foo": {}},
        )
        assert_matches_type(CategoryResourceResponse, resource, path=["response"])

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncPayi) -> None:
        resource = await async_client.categories.resources.create(
            resource="resource",
            category="category",
            units={
                "foo": {
                    "input_price": 0,
                    "output_price": 0,
                }
            },
            max_input_units=0,
            max_output_units=0,
            max_total_units=0,
            start_timestamp=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(CategoryResourceResponse, resource, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncPayi) -> None:
        response = await async_client.categories.resources.with_raw_response.create(
            resource="resource",
            category="category",
            units={"foo": {}},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource = await response.parse()
        assert_matches_type(CategoryResourceResponse, resource, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncPayi) -> None:
        async with async_client.categories.resources.with_streaming_response.create(
            resource="resource",
            category="category",
            units={"foo": {}},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource = await response.parse()
            assert_matches_type(CategoryResourceResponse, resource, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_create(self, async_client: AsyncPayi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `category` but received ''"):
            await async_client.categories.resources.with_raw_response.create(
                resource="resource",
                category="",
                units={"foo": {}},
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `resource` but received ''"):
            await async_client.categories.resources.with_raw_response.create(
                resource="",
                category="category",
                units={"foo": {}},
            )

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncPayi) -> None:
        resource = await async_client.categories.resources.retrieve(
            resource_id="resource_id",
            category="category",
            resource="resource",
        )
        assert_matches_type(CategoryResourceResponse, resource, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncPayi) -> None:
        response = await async_client.categories.resources.with_raw_response.retrieve(
            resource_id="resource_id",
            category="category",
            resource="resource",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource = await response.parse()
        assert_matches_type(CategoryResourceResponse, resource, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncPayi) -> None:
        async with async_client.categories.resources.with_streaming_response.retrieve(
            resource_id="resource_id",
            category="category",
            resource="resource",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource = await response.parse()
            assert_matches_type(CategoryResourceResponse, resource, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncPayi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `category` but received ''"):
            await async_client.categories.resources.with_raw_response.retrieve(
                resource_id="resource_id",
                category="",
                resource="resource",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `resource` but received ''"):
            await async_client.categories.resources.with_raw_response.retrieve(
                resource_id="resource_id",
                category="category",
                resource="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `resource_id` but received ''"):
            await async_client.categories.resources.with_raw_response.retrieve(
                resource_id="",
                category="category",
                resource="resource",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncPayi) -> None:
        resource = await async_client.categories.resources.list(
            resource="resource",
            category="category",
        )
        assert_matches_type(AsyncCursorPage[CategoryResourceResponse], resource, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncPayi) -> None:
        resource = await async_client.categories.resources.list(
            resource="resource",
            category="category",
            active=True,
            cursor="cursor",
            limit=0,
            sort_ascending=True,
        )
        assert_matches_type(AsyncCursorPage[CategoryResourceResponse], resource, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncPayi) -> None:
        response = await async_client.categories.resources.with_raw_response.list(
            resource="resource",
            category="category",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource = await response.parse()
        assert_matches_type(AsyncCursorPage[CategoryResourceResponse], resource, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncPayi) -> None:
        async with async_client.categories.resources.with_streaming_response.list(
            resource="resource",
            category="category",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource = await response.parse()
            assert_matches_type(AsyncCursorPage[CategoryResourceResponse], resource, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_list(self, async_client: AsyncPayi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `category` but received ''"):
            await async_client.categories.resources.with_raw_response.list(
                resource="resource",
                category="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `resource` but received ''"):
            await async_client.categories.resources.with_raw_response.list(
                resource="",
                category="category",
            )

    @parametrize
    async def test_method_delete(self, async_client: AsyncPayi) -> None:
        resource = await async_client.categories.resources.delete(
            resource_id="resource_id",
            category="category",
            resource="resource",
        )
        assert_matches_type(CategoryResourceResponse, resource, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncPayi) -> None:
        response = await async_client.categories.resources.with_raw_response.delete(
            resource_id="resource_id",
            category="category",
            resource="resource",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource = await response.parse()
        assert_matches_type(CategoryResourceResponse, resource, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncPayi) -> None:
        async with async_client.categories.resources.with_streaming_response.delete(
            resource_id="resource_id",
            category="category",
            resource="resource",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource = await response.parse()
            assert_matches_type(CategoryResourceResponse, resource, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncPayi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `category` but received ''"):
            await async_client.categories.resources.with_raw_response.delete(
                resource_id="resource_id",
                category="",
                resource="resource",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `resource` but received ''"):
            await async_client.categories.resources.with_raw_response.delete(
                resource_id="resource_id",
                category="category",
                resource="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `resource_id` but received ''"):
            await async_client.categories.resources.with_raw_response.delete(
                resource_id="",
                category="category",
                resource="resource",
            )
