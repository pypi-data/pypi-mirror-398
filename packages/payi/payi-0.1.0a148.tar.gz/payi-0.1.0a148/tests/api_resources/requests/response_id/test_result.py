# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from payi import Payi, AsyncPayi
from payi.types import RequestResult
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestResult:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_retrieve(self, client: Payi) -> None:
        result = client.requests.response_id.result.retrieve(
            provider_response_id="provider_response_id",
            category="category",
        )
        assert_matches_type(RequestResult, result, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: Payi) -> None:
        response = client.requests.response_id.result.with_raw_response.retrieve(
            provider_response_id="provider_response_id",
            category="category",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        result = response.parse()
        assert_matches_type(RequestResult, result, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: Payi) -> None:
        with client.requests.response_id.result.with_streaming_response.retrieve(
            provider_response_id="provider_response_id",
            category="category",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            result = response.parse()
            assert_matches_type(RequestResult, result, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: Payi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `category` but received ''"):
            client.requests.response_id.result.with_raw_response.retrieve(
                provider_response_id="provider_response_id",
                category="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `provider_response_id` but received ''"):
            client.requests.response_id.result.with_raw_response.retrieve(
                provider_response_id="",
                category="category",
            )


class TestAsyncResult:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncPayi) -> None:
        result = await async_client.requests.response_id.result.retrieve(
            provider_response_id="provider_response_id",
            category="category",
        )
        assert_matches_type(RequestResult, result, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncPayi) -> None:
        response = await async_client.requests.response_id.result.with_raw_response.retrieve(
            provider_response_id="provider_response_id",
            category="category",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        result = await response.parse()
        assert_matches_type(RequestResult, result, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncPayi) -> None:
        async with async_client.requests.response_id.result.with_streaming_response.retrieve(
            provider_response_id="provider_response_id",
            category="category",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            result = await response.parse()
            assert_matches_type(RequestResult, result, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncPayi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `category` but received ''"):
            await async_client.requests.response_id.result.with_raw_response.retrieve(
                provider_response_id="provider_response_id",
                category="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `provider_response_id` but received ''"):
            await async_client.requests.response_id.result.with_raw_response.retrieve(
                provider_response_id="",
                category="category",
            )
