# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from payi import Payi, AsyncPayi
from payi.types import IngestResponse, BulkIngestResponse
from payi._utils import parse_datetime
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestIngest:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_bulk(self, client: Payi) -> None:
        ingest = client.ingest.bulk()
        assert_matches_type(BulkIngestResponse, ingest, path=["response"])

    @parametrize
    def test_method_bulk_with_all_params(self, client: Payi) -> None:
        ingest = client.ingest.bulk(
            events=[
                {
                    "category": "x",
                    "units": {
                        "foo": {
                            "input": 0,
                            "output": 0,
                        }
                    },
                    "account_name": "account_name",
                    "end_to_end_latency_ms": 0,
                    "event_timestamp": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "http_status_code": 0,
                    "limit_ids": ["string"],
                    "properties": {"foo": "string"},
                    "provider_request_headers": [
                        {
                            "name": "x",
                            "value": "value",
                        }
                    ],
                    "provider_request_json": "provider_request_json",
                    "provider_request_reasoning_json": "provider_request_reasoning_json",
                    "provider_response_function_calls": [
                        {
                            "name": "x",
                            "arguments": "arguments",
                        }
                    ],
                    "provider_response_headers": [
                        {
                            "name": "x",
                            "value": "value",
                        }
                    ],
                    "provider_response_id": "provider_response_id",
                    "provider_response_json": "string",
                    "provider_uri": "provider_uri",
                    "request_tags": ["string"],
                    "resource": "resource",
                    "time_to_first_completion_token_ms": 0,
                    "time_to_first_token_ms": 0,
                    "use_case_id": "use_case_id",
                    "use_case_name": "use_case_name",
                    "use_case_properties": {"foo": "string"},
                    "use_case_step": "use_case_step",
                    "use_case_version": 0,
                    "user_id": "user_id",
                }
            ],
        )
        assert_matches_type(BulkIngestResponse, ingest, path=["response"])

    @parametrize
    def test_raw_response_bulk(self, client: Payi) -> None:
        response = client.ingest.with_raw_response.bulk()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        ingest = response.parse()
        assert_matches_type(BulkIngestResponse, ingest, path=["response"])

    @parametrize
    def test_streaming_response_bulk(self, client: Payi) -> None:
        with client.ingest.with_streaming_response.bulk() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            ingest = response.parse()
            assert_matches_type(BulkIngestResponse, ingest, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_units(self, client: Payi) -> None:
        ingest = client.ingest.units(
            category="x",
            units={"foo": {}},
        )
        assert_matches_type(IngestResponse, ingest, path=["response"])

    @parametrize
    def test_method_units_with_all_params(self, client: Payi) -> None:
        ingest = client.ingest.units(
            category="x",
            units={
                "foo": {
                    "input": 0,
                    "output": 0,
                }
            },
            end_to_end_latency_ms=0,
            event_timestamp=parse_datetime("2019-12-27T18:11:19.117Z"),
            http_status_code=0,
            properties={"foo": "string"},
            provider_request_headers=[
                {
                    "name": "x",
                    "value": "value",
                }
            ],
            provider_request_json="provider_request_json",
            provider_request_reasoning_json="provider_request_reasoning_json",
            provider_response_function_calls=[
                {
                    "name": "x",
                    "arguments": "arguments",
                }
            ],
            provider_response_headers=[
                {
                    "name": "x",
                    "value": "value",
                }
            ],
            provider_response_id="provider_response_id",
            provider_response_json="string",
            provider_uri="provider_uri",
            resource="resource",
            time_to_first_completion_token_ms=0,
            time_to_first_token_ms=0,
            use_case_properties={"foo": "string"},
            account_name="account_name",
            limit_ids=["limitId1", "limitId_2"],
            request_tags=["requestTag1", "request_tag_2"],
            use_case_name="use_case_name",
            use_case_step="step_1",
            use_case_id="use_case_id",
            use_case_version=0,
            resource_scope="datazone",
            user_id="UserName123",
        )
        assert_matches_type(IngestResponse, ingest, path=["response"])

    @parametrize
    def test_raw_response_units(self, client: Payi) -> None:
        response = client.ingest.with_raw_response.units(
            category="x",
            units={"foo": {}},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        ingest = response.parse()
        assert_matches_type(IngestResponse, ingest, path=["response"])

    @parametrize
    def test_streaming_response_units(self, client: Payi) -> None:
        with client.ingest.with_streaming_response.units(
            category="x",
            units={"foo": {}},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            ingest = response.parse()
            assert_matches_type(IngestResponse, ingest, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncIngest:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_bulk(self, async_client: AsyncPayi) -> None:
        ingest = await async_client.ingest.bulk()
        assert_matches_type(BulkIngestResponse, ingest, path=["response"])

    @parametrize
    async def test_method_bulk_with_all_params(self, async_client: AsyncPayi) -> None:
        ingest = await async_client.ingest.bulk(
            events=[
                {
                    "category": "x",
                    "units": {
                        "foo": {
                            "input": 0,
                            "output": 0,
                        }
                    },
                    "account_name": "account_name",
                    "end_to_end_latency_ms": 0,
                    "event_timestamp": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "http_status_code": 0,
                    "limit_ids": ["string"],
                    "properties": {"foo": "string"},
                    "provider_request_headers": [
                        {
                            "name": "x",
                            "value": "value",
                        }
                    ],
                    "provider_request_json": "provider_request_json",
                    "provider_request_reasoning_json": "provider_request_reasoning_json",
                    "provider_response_function_calls": [
                        {
                            "name": "x",
                            "arguments": "arguments",
                        }
                    ],
                    "provider_response_headers": [
                        {
                            "name": "x",
                            "value": "value",
                        }
                    ],
                    "provider_response_id": "provider_response_id",
                    "provider_response_json": "string",
                    "provider_uri": "provider_uri",
                    "request_tags": ["string"],
                    "resource": "resource",
                    "time_to_first_completion_token_ms": 0,
                    "time_to_first_token_ms": 0,
                    "use_case_id": "use_case_id",
                    "use_case_name": "use_case_name",
                    "use_case_properties": {"foo": "string"},
                    "use_case_step": "use_case_step",
                    "use_case_version": 0,
                    "user_id": "user_id",
                }
            ],
        )
        assert_matches_type(BulkIngestResponse, ingest, path=["response"])

    @parametrize
    async def test_raw_response_bulk(self, async_client: AsyncPayi) -> None:
        response = await async_client.ingest.with_raw_response.bulk()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        ingest = await response.parse()
        assert_matches_type(BulkIngestResponse, ingest, path=["response"])

    @parametrize
    async def test_streaming_response_bulk(self, async_client: AsyncPayi) -> None:
        async with async_client.ingest.with_streaming_response.bulk() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            ingest = await response.parse()
            assert_matches_type(BulkIngestResponse, ingest, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_units(self, async_client: AsyncPayi) -> None:
        ingest = await async_client.ingest.units(
            category="x",
            units={"foo": {}},
        )
        assert_matches_type(IngestResponse, ingest, path=["response"])

    @parametrize
    async def test_method_units_with_all_params(self, async_client: AsyncPayi) -> None:
        ingest = await async_client.ingest.units(
            category="x",
            units={
                "foo": {
                    "input": 0,
                    "output": 0,
                }
            },
            end_to_end_latency_ms=0,
            event_timestamp=parse_datetime("2019-12-27T18:11:19.117Z"),
            http_status_code=0,
            properties={"foo": "string"},
            provider_request_headers=[
                {
                    "name": "x",
                    "value": "value",
                }
            ],
            provider_request_json="provider_request_json",
            provider_request_reasoning_json="provider_request_reasoning_json",
            provider_response_function_calls=[
                {
                    "name": "x",
                    "arguments": "arguments",
                }
            ],
            provider_response_headers=[
                {
                    "name": "x",
                    "value": "value",
                }
            ],
            provider_response_id="provider_response_id",
            provider_response_json="string",
            provider_uri="provider_uri",
            resource="resource",
            time_to_first_completion_token_ms=0,
            time_to_first_token_ms=0,
            use_case_properties={"foo": "string"},
            account_name="account_name",
            limit_ids=["limitId1", "limitId_2"],
            request_tags=["requestTag1", "request_tag_2"],
            use_case_name="use_case_name",
            use_case_id="use_case_id",
            use_case_step="step_1",
            use_case_version=0,
            resource_scope="datazone",
            user_id="UserName123",
        )
        assert_matches_type(IngestResponse, ingest, path=["response"])

    @parametrize
    async def test_raw_response_units(self, async_client: AsyncPayi) -> None:
        response = await async_client.ingest.with_raw_response.units(
            category="x",
            units={"foo": {}},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        ingest = await response.parse()
        assert_matches_type(IngestResponse, ingest, path=["response"])

    @parametrize
    async def test_streaming_response_units(self, async_client: AsyncPayi) -> None:
        async with async_client.ingest.with_streaming_response.units(
            category="x",
            units={"foo": {}},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            ingest = await response.parse()
            assert_matches_type(IngestResponse, ingest, path=["response"])

        assert cast(Any, response.is_closed) is True
