# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from payi import Payi, AsyncPayi
from tests.utils import assert_matches_type
from payi.types.use_cases import UseCaseDefinitionResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestVersion:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_increment(self, client: Payi) -> None:
        version = client.use_cases.definitions.version.increment(
            "use_case_name",
        )
        assert_matches_type(UseCaseDefinitionResponse, version, path=["response"])

    @parametrize
    def test_raw_response_increment(self, client: Payi) -> None:
        response = client.use_cases.definitions.version.with_raw_response.increment(
            "use_case_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        version = response.parse()
        assert_matches_type(UseCaseDefinitionResponse, version, path=["response"])

    @parametrize
    def test_streaming_response_increment(self, client: Payi) -> None:
        with client.use_cases.definitions.version.with_streaming_response.increment(
            "use_case_name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            version = response.parse()
            assert_matches_type(UseCaseDefinitionResponse, version, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_increment(self, client: Payi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `use_case_name` but received ''"):
            client.use_cases.definitions.version.with_raw_response.increment(
                "",
            )


class TestAsyncVersion:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_increment(self, async_client: AsyncPayi) -> None:
        version = await async_client.use_cases.definitions.version.increment(
            "use_case_name",
        )
        assert_matches_type(UseCaseDefinitionResponse, version, path=["response"])

    @parametrize
    async def test_raw_response_increment(self, async_client: AsyncPayi) -> None:
        response = await async_client.use_cases.definitions.version.with_raw_response.increment(
            "use_case_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        version = await response.parse()
        assert_matches_type(UseCaseDefinitionResponse, version, path=["response"])

    @parametrize
    async def test_streaming_response_increment(self, async_client: AsyncPayi) -> None:
        async with async_client.use_cases.definitions.version.with_streaming_response.increment(
            "use_case_name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            version = await response.parse()
            assert_matches_type(UseCaseDefinitionResponse, version, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_increment(self, async_client: AsyncPayi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `use_case_name` but received ''"):
            await async_client.use_cases.definitions.version.with_raw_response.increment(
                "",
            )
