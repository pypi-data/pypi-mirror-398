# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from payi import Payi, AsyncPayi
from tests.utils import assert_matches_type
from payi.pagination import SyncCursorPage, AsyncCursorPage
from payi.types.use_cases.definitions import (
    KpiListResponse,
    KpiCreateResponse,
    KpiDeleteResponse,
    KpiUpdateResponse,
    KpiRetrieveResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestKpis:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: Payi) -> None:
        kpi = client.use_cases.definitions.kpis.create(
            use_case_name="use_case_name",
            description="x",
            name="x",
            goal=0,
            kpi_type="boolean",
        )
        assert_matches_type(KpiCreateResponse, kpi, path=["response"])

    @parametrize
    def test_method_create_with_all_params(self, client: Payi) -> None:
        kpi = client.use_cases.definitions.kpis.create(
            use_case_name="use_case_name",
            description="x",
            name="x",
            goal=0,
            kpi_type="boolean",
        )
        assert_matches_type(KpiCreateResponse, kpi, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: Payi) -> None:
        response = client.use_cases.definitions.kpis.with_raw_response.create(
            use_case_name="use_case_name",
            description="x",
            goal=0,
            kpi_type="boolean",
            name="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        kpi = response.parse()
        assert_matches_type(KpiCreateResponse, kpi, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: Payi) -> None:
        with client.use_cases.definitions.kpis.with_streaming_response.create(
            use_case_name="use_case_name",
            description="x",
            goal=0,
            kpi_type="boolean",
            name="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            kpi = response.parse()
            assert_matches_type(KpiCreateResponse, kpi, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_create(self, client: Payi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `use_case_name` but received ''"):
            client.use_cases.definitions.kpis.with_raw_response.create(
                use_case_name="",
                description="x",
                goal=0,
                kpi_type="boolean",
                name="x",
            )

    @parametrize
    def test_method_retrieve(self, client: Payi) -> None:
        kpi = client.use_cases.definitions.kpis.retrieve(
            kpi_name="kpi_name",
            use_case_name="use_case_name",
        )
        assert_matches_type(KpiRetrieveResponse, kpi, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: Payi) -> None:
        response = client.use_cases.definitions.kpis.with_raw_response.retrieve(
            kpi_name="kpi_name",
            use_case_name="use_case_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        kpi = response.parse()
        assert_matches_type(KpiRetrieveResponse, kpi, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: Payi) -> None:
        with client.use_cases.definitions.kpis.with_streaming_response.retrieve(
            kpi_name="kpi_name",
            use_case_name="use_case_name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            kpi = response.parse()
            assert_matches_type(KpiRetrieveResponse, kpi, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: Payi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `use_case_name` but received ''"):
            client.use_cases.definitions.kpis.with_raw_response.retrieve(
                kpi_name="kpi_name",
                use_case_name="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `kpi_name` but received ''"):
            client.use_cases.definitions.kpis.with_raw_response.retrieve(
                kpi_name="",
                use_case_name="use_case_name",
            )

    @parametrize
    def test_method_update(self, client: Payi) -> None:
        kpi = client.use_cases.definitions.kpis.update(
            kpi_name="kpi_name",
            use_case_name="use_case_name",
        )
        assert_matches_type(KpiUpdateResponse, kpi, path=["response"])

    @parametrize
    def test_method_update_with_all_params(self, client: Payi) -> None:
        kpi = client.use_cases.definitions.kpis.update(
            kpi_name="kpi_name",
            use_case_name="use_case_name",
            description="description",
            goal=0,
        )
        assert_matches_type(KpiUpdateResponse, kpi, path=["response"])

    @parametrize
    def test_raw_response_update(self, client: Payi) -> None:
        response = client.use_cases.definitions.kpis.with_raw_response.update(
            kpi_name="kpi_name",
            use_case_name="use_case_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        kpi = response.parse()
        assert_matches_type(KpiUpdateResponse, kpi, path=["response"])

    @parametrize
    def test_streaming_response_update(self, client: Payi) -> None:
        with client.use_cases.definitions.kpis.with_streaming_response.update(
            kpi_name="kpi_name",
            use_case_name="use_case_name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            kpi = response.parse()
            assert_matches_type(KpiUpdateResponse, kpi, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update(self, client: Payi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `use_case_name` but received ''"):
            client.use_cases.definitions.kpis.with_raw_response.update(
                kpi_name="kpi_name",
                use_case_name="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `kpi_name` but received ''"):
            client.use_cases.definitions.kpis.with_raw_response.update(
                kpi_name="",
                use_case_name="use_case_name",
            )

    @parametrize
    def test_method_list(self, client: Payi) -> None:
        kpi = client.use_cases.definitions.kpis.list(
            use_case_name="use_case_name",
        )
        assert_matches_type(SyncCursorPage[KpiListResponse], kpi, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: Payi) -> None:
        kpi = client.use_cases.definitions.kpis.list(
            use_case_name="use_case_name",
            cursor="cursor",
            kpi_name="kpi_name",
            limit=0,
            sort_ascending=True,
        )
        assert_matches_type(SyncCursorPage[KpiListResponse], kpi, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: Payi) -> None:
        response = client.use_cases.definitions.kpis.with_raw_response.list(
            use_case_name="use_case_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        kpi = response.parse()
        assert_matches_type(SyncCursorPage[KpiListResponse], kpi, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: Payi) -> None:
        with client.use_cases.definitions.kpis.with_streaming_response.list(
            use_case_name="use_case_name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            kpi = response.parse()
            assert_matches_type(SyncCursorPage[KpiListResponse], kpi, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_list(self, client: Payi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `use_case_name` but received ''"):
            client.use_cases.definitions.kpis.with_raw_response.list(
                use_case_name="",
            )

    @parametrize
    def test_method_delete(self, client: Payi) -> None:
        kpi = client.use_cases.definitions.kpis.delete(
            kpi_name="kpi_name",
            use_case_name="use_case_name",
        )
        assert_matches_type(KpiDeleteResponse, kpi, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: Payi) -> None:
        response = client.use_cases.definitions.kpis.with_raw_response.delete(
            kpi_name="kpi_name",
            use_case_name="use_case_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        kpi = response.parse()
        assert_matches_type(KpiDeleteResponse, kpi, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: Payi) -> None:
        with client.use_cases.definitions.kpis.with_streaming_response.delete(
            kpi_name="kpi_name",
            use_case_name="use_case_name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            kpi = response.parse()
            assert_matches_type(KpiDeleteResponse, kpi, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: Payi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `use_case_name` but received ''"):
            client.use_cases.definitions.kpis.with_raw_response.delete(
                kpi_name="kpi_name",
                use_case_name="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `kpi_name` but received ''"):
            client.use_cases.definitions.kpis.with_raw_response.delete(
                kpi_name="",
                use_case_name="use_case_name",
            )


class TestAsyncKpis:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncPayi) -> None:
        kpi = await async_client.use_cases.definitions.kpis.create(
            use_case_name="use_case_name",
            description="x",
            name="x",
            goal=0,
            kpi_type="boolean",
        )
        assert_matches_type(KpiCreateResponse, kpi, path=["response"])

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncPayi) -> None:
        kpi = await async_client.use_cases.definitions.kpis.create(
            use_case_name="use_case_name",
            description="x",
            name="x",
            goal=0,
            kpi_type="boolean",
        )
        assert_matches_type(KpiCreateResponse, kpi, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncPayi) -> None:
        response = await async_client.use_cases.definitions.kpis.with_raw_response.create(
            use_case_name="use_case_name",
            description="x",
            goal=0,
            kpi_type="boolean",
            name="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        kpi = await response.parse()
        assert_matches_type(KpiCreateResponse, kpi, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncPayi) -> None:
        async with async_client.use_cases.definitions.kpis.with_streaming_response.create(
            use_case_name="use_case_name",
            description="x",
            goal=0,
            kpi_type="boolean",
            name="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            kpi = await response.parse()
            assert_matches_type(KpiCreateResponse, kpi, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_create(self, async_client: AsyncPayi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `use_case_name` but received ''"):
            await async_client.use_cases.definitions.kpis.with_raw_response.create(
                use_case_name="",
                description="x",
                goal=0,
                kpi_type="boolean",
                name="x",
            )

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncPayi) -> None:
        kpi = await async_client.use_cases.definitions.kpis.retrieve(
            kpi_name="kpi_name",
            use_case_name="use_case_name",
        )
        assert_matches_type(KpiRetrieveResponse, kpi, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncPayi) -> None:
        response = await async_client.use_cases.definitions.kpis.with_raw_response.retrieve(
            kpi_name="kpi_name",
            use_case_name="use_case_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        kpi = await response.parse()
        assert_matches_type(KpiRetrieveResponse, kpi, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncPayi) -> None:
        async with async_client.use_cases.definitions.kpis.with_streaming_response.retrieve(
            kpi_name="kpi_name",
            use_case_name="use_case_name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            kpi = await response.parse()
            assert_matches_type(KpiRetrieveResponse, kpi, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncPayi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `use_case_name` but received ''"):
            await async_client.use_cases.definitions.kpis.with_raw_response.retrieve(
                kpi_name="kpi_name",
                use_case_name="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `kpi_name` but received ''"):
            await async_client.use_cases.definitions.kpis.with_raw_response.retrieve(
                kpi_name="",
                use_case_name="use_case_name",
            )

    @parametrize
    async def test_method_update(self, async_client: AsyncPayi) -> None:
        kpi = await async_client.use_cases.definitions.kpis.update(
            kpi_name="kpi_name",
            use_case_name="use_case_name",
        )
        assert_matches_type(KpiUpdateResponse, kpi, path=["response"])

    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncPayi) -> None:
        kpi = await async_client.use_cases.definitions.kpis.update(
            kpi_name="kpi_name",
            use_case_name="use_case_name",
            description="description",
            goal=0,
        )
        assert_matches_type(KpiUpdateResponse, kpi, path=["response"])

    @parametrize
    async def test_raw_response_update(self, async_client: AsyncPayi) -> None:
        response = await async_client.use_cases.definitions.kpis.with_raw_response.update(
            kpi_name="kpi_name",
            use_case_name="use_case_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        kpi = await response.parse()
        assert_matches_type(KpiUpdateResponse, kpi, path=["response"])

    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncPayi) -> None:
        async with async_client.use_cases.definitions.kpis.with_streaming_response.update(
            kpi_name="kpi_name",
            use_case_name="use_case_name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            kpi = await response.parse()
            assert_matches_type(KpiUpdateResponse, kpi, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update(self, async_client: AsyncPayi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `use_case_name` but received ''"):
            await async_client.use_cases.definitions.kpis.with_raw_response.update(
                kpi_name="kpi_name",
                use_case_name="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `kpi_name` but received ''"):
            await async_client.use_cases.definitions.kpis.with_raw_response.update(
                kpi_name="",
                use_case_name="use_case_name",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncPayi) -> None:
        kpi = await async_client.use_cases.definitions.kpis.list(
            use_case_name="use_case_name",
        )
        assert_matches_type(AsyncCursorPage[KpiListResponse], kpi, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncPayi) -> None:
        kpi = await async_client.use_cases.definitions.kpis.list(
            use_case_name="use_case_name",
            cursor="cursor",
            kpi_name="kpi_name",
            limit=0,
            sort_ascending=True,
        )
        assert_matches_type(AsyncCursorPage[KpiListResponse], kpi, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncPayi) -> None:
        response = await async_client.use_cases.definitions.kpis.with_raw_response.list(
            use_case_name="use_case_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        kpi = await response.parse()
        assert_matches_type(AsyncCursorPage[KpiListResponse], kpi, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncPayi) -> None:
        async with async_client.use_cases.definitions.kpis.with_streaming_response.list(
            use_case_name="use_case_name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            kpi = await response.parse()
            assert_matches_type(AsyncCursorPage[KpiListResponse], kpi, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_list(self, async_client: AsyncPayi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `use_case_name` but received ''"):
            await async_client.use_cases.definitions.kpis.with_raw_response.list(
                use_case_name="",
            )

    @parametrize
    async def test_method_delete(self, async_client: AsyncPayi) -> None:
        kpi = await async_client.use_cases.definitions.kpis.delete(
            kpi_name="kpi_name",
            use_case_name="use_case_name",
        )
        assert_matches_type(KpiDeleteResponse, kpi, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncPayi) -> None:
        response = await async_client.use_cases.definitions.kpis.with_raw_response.delete(
            kpi_name="kpi_name",
            use_case_name="use_case_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        kpi = await response.parse()
        assert_matches_type(KpiDeleteResponse, kpi, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncPayi) -> None:
        async with async_client.use_cases.definitions.kpis.with_streaming_response.delete(
            kpi_name="kpi_name",
            use_case_name="use_case_name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            kpi = await response.parse()
            assert_matches_type(KpiDeleteResponse, kpi, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncPayi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `use_case_name` but received ''"):
            await async_client.use_cases.definitions.kpis.with_raw_response.delete(
                kpi_name="kpi_name",
                use_case_name="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `kpi_name` but received ''"):
            await async_client.use_cases.definitions.kpis.with_raw_response.delete(
                kpi_name="",
                use_case_name="use_case_name",
            )
