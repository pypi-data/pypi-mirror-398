# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from payi import Payi, AsyncPayi
from tests.utils import assert_matches_type
from payi.types.limits import PropertyUpdateResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestProperties:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_update(self, client: Payi) -> None:
        property = client.limits.properties.update(
            limit_id="limit_id",
            properties={"foo": "string"},
        )
        assert_matches_type(PropertyUpdateResponse, property, path=["response"])

    @parametrize
    def test_raw_response_update(self, client: Payi) -> None:
        response = client.limits.properties.with_raw_response.update(
            limit_id="limit_id",
            properties={"foo": "string"},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        property = response.parse()
        assert_matches_type(PropertyUpdateResponse, property, path=["response"])

    @parametrize
    def test_streaming_response_update(self, client: Payi) -> None:
        with client.limits.properties.with_streaming_response.update(
            limit_id="limit_id",
            properties={"foo": "string"},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            property = response.parse()
            assert_matches_type(PropertyUpdateResponse, property, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update(self, client: Payi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `limit_id` but received ''"):
            client.limits.properties.with_raw_response.update(
                limit_id="",
                properties={"foo": "string"},
            )


class TestAsyncProperties:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_update(self, async_client: AsyncPayi) -> None:
        property = await async_client.limits.properties.update(
            limit_id="limit_id",
            properties={"foo": "string"},
        )
        assert_matches_type(PropertyUpdateResponse, property, path=["response"])

    @parametrize
    async def test_raw_response_update(self, async_client: AsyncPayi) -> None:
        response = await async_client.limits.properties.with_raw_response.update(
            limit_id="limit_id",
            properties={"foo": "string"},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        property = await response.parse()
        assert_matches_type(PropertyUpdateResponse, property, path=["response"])

    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncPayi) -> None:
        async with async_client.limits.properties.with_streaming_response.update(
            limit_id="limit_id",
            properties={"foo": "string"},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            property = await response.parse()
            assert_matches_type(PropertyUpdateResponse, property, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update(self, async_client: AsyncPayi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `limit_id` but received ''"):
            await async_client.limits.properties.with_raw_response.update(
                limit_id="",
                properties={"foo": "string"},
            )
