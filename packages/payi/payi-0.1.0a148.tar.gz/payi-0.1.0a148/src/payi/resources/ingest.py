# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Iterable, Optional
from datetime import datetime

import httpx

from payi._utils._utils import is_given

from ..types import ingest_units_params
from .._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from .._utils import maybe_transform, strip_not_given, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.ingest_response import IngestResponse
from ..types.bulk_ingest_response import BulkIngestResponse
from ..types.bulk_ingest_request_param import BulkIngestRequestParam
from ..types.shared_params.ingest_units import IngestUnits
from ..types.pay_i_common_models_api_router_header_info_param import PayICommonModelsAPIRouterHeaderInfoParam

__all__ = ["IngestResource", "AsyncIngestResource"]

def convert_property_values_to_str(properties: Dict[str, Optional[str]]) -> Dict[str, Optional[str]]:
    converted_properties: Dict[str, Optional[str]] = {}
    for k, v in properties.items():
        if v is None:
            converted_properties[k] = None
        else:
            try:
                converted_properties[k] = str(v)
            except Exception:
                pass  # Skip this key-value pair if str() fails

    return converted_properties

class IngestResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> IngestResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Pay-i/pay-i-python#accessing-raw-response-data-eg-headers
        """
        return IngestResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> IngestResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Pay-i/pay-i-python#with_streaming_response
        """
        return IngestResourceWithStreamingResponse(self)

    def bulk(
        self,
        *,
        events: Iterable[BulkIngestRequestParam] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BulkIngestResponse:
        """
        Bulk Ingest

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/v1/ingest/bulk",
            body=maybe_transform(events, Iterable[BulkIngestRequestParam]),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BulkIngestResponse,
        )

    def units(
        self,
        *,
        category: str,
        units: Dict[str, IngestUnits],
        end_to_end_latency_ms: Optional[int] | Omit = omit,
        event_timestamp: Union[str, datetime, None] | Omit = omit,
        http_status_code: Optional[int] | Omit = omit,
        properties: Optional[Dict[str, Optional[str]]] | Omit = omit,
        provider_request_headers: Optional[Iterable[PayICommonModelsAPIRouterHeaderInfoParam]] | Omit = omit,
        provider_request_json: Optional[str] | Omit = omit,
        provider_request_reasoning_json: Optional[str] | Omit = omit,
        provider_response_function_calls: Optional[Iterable[ingest_units_params.ProviderResponseFunctionCall]]
        | Omit = omit,
        provider_response_headers: Optional[Iterable[PayICommonModelsAPIRouterHeaderInfoParam]] | Omit = omit,
        provider_response_id: Optional[str] | Omit = omit,
        provider_response_json: Union[str, SequenceNotStr[str], None] | Omit = omit,
        provider_uri: Optional[str] | Omit = omit,
        resource: Optional[str] | Omit = omit,
        time_to_first_completion_token_ms: Optional[int] | Omit = omit,
        time_to_first_token_ms: Optional[int] | Omit = omit,
        use_case_properties: Optional[Dict[str, Optional[str]]] | Omit = omit,
        limit_ids: Optional[list[str]] | Omit = omit,
        disable_logging: Optional[bool] | Omit = omit,
        request_tags: Optional[list[str]] | Omit = omit,
        use_case_id: Optional[str] | Omit = omit,
        use_case_name: Optional[str] | Omit = omit,
        use_case_step: Optional[str] | Omit = omit,
        use_case_version: Optional[int] | Omit = omit,
        user_id: Optional[str] | Omit = omit,
        resource_scope: Optional[str] | Omit = omit,
        account_name: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> IngestResponse:
        """
        Ingest an Event

        Args:
          category (str): The name of the category

          resource (str): The name of the resource

          input (int): The number of input units

          output (int): The number of output units

          event_timestamp: (str, datetime, None): The timestamp of the event

          disable_logging (bool, optional): Disable logging for the request

          limit_ids (list[str], optional): The limit IDs to associate with the request

          properties (Dict[str, Optional[str]], optional): Properties to associate with the request

          request_tags (list[str], optional): The request tags to associate with the request

          use_case_name (str, optional): The use case name

          use_case_id (str, optional): The use case instance id

          use_case_step (str, optional): The use case step

          use_case_version (int, optional): The use case instance version

          use_case_properties (Dict[str, Optional[str]], optional): The use case properties

          user_id (str, optional): The user id
          
          resource_scope(str, optional): The scope of the resource

          account_name (str, optional): The account name

          extra_headers (Dict[str, str], optional): Additional headers for the request. Defaults to None.

          extra_query (Dict[str, str], optional): Additional query parameters. Defaults to None.

          extra_body (Dict[str, Any], optional): Additional body parameters. Defaults to None.

          timeout (Union[float, None], optional): The timeout for the request in seconds. Defaults to None.
        """
        request_tags = request_tags
        valid_ids_str: str | Omit = omit
        use_case_version_str: str | Omit = omit

        if limit_ids is None or not is_given(limit_ids):
            valid_ids_str = omit
        elif not isinstance(limit_ids, list):  # type: ignore
            raise TypeError("limit_ids must be a list")
        else:
            # Proceed with the list comprehension if limit_ids is given
            valid_ids = [id.strip() for id in limit_ids if id.strip()]
            valid_ids_str = ",".join(valid_ids) if valid_ids else omit

        if use_case_name is None or not is_given(use_case_name):
            use_case_name = omit

        if use_case_step is None or not is_given(use_case_step):
            use_case_step = omit

        if use_case_id is None or not is_given(use_case_id):
            use_case_id = omit

        if use_case_version is None or not is_given(use_case_version):
            use_case_version_str = omit
        else:
            use_case_version_str = str(use_case_version)

        if use_case_properties and is_given(use_case_properties):
            use_case_properties = convert_property_values_to_str(use_case_properties)

        if user_id is None or not is_given(user_id):
            user_id = omit

        if resource_scope is None or not is_given(resource_scope):
            resource_scope = omit

        if account_name is None or not is_given(account_name):
            account_name = omit

        if properties and is_given(properties):
            properties = convert_property_values_to_str(properties)
        
        extra_headers = {
            **strip_not_given(
                {
                    "xProxy-Limit-IDs": valid_ids_str,
                    "xProxy-Request-Tags": omit,
                    "xProxy-UseCase-ID": use_case_id,
                    "xProxy-UseCase-Name": use_case_name,
                    "xProxy-UseCase-Step": use_case_step,
                    "xProxy-UseCase-Version": use_case_version_str
                    if is_given(use_case_version)
                    else not_given,
                    "xProxy-User-ID": user_id,
                    "xProxy-Resource-Scope": resource_scope,
                    "xProxy-Account-Name": account_name,
                    "xProxy-Logging-Disable": str(disable_logging)
                    if is_given(disable_logging)
                    else not_given,
                }
            ),
            **(extra_headers or {}),
        }

        return self._post(
            "/api/v1/ingest",
            body=maybe_transform(
                {
                    "category": category,
                    "units": units,
                    "end_to_end_latency_ms": end_to_end_latency_ms,
                    "event_timestamp": event_timestamp,
                    "http_status_code": http_status_code,
                    "properties": properties,
                    "provider_request_headers": provider_request_headers,
                    "provider_request_json": provider_request_json,
                    "provider_request_reasoning_json": provider_request_reasoning_json,
                    "provider_response_function_calls": provider_response_function_calls,
                    "provider_response_headers": provider_response_headers,
                    "provider_response_id": provider_response_id,
                    "provider_response_json": provider_response_json,
                    "provider_uri": provider_uri,
                    "resource": resource,
                    "time_to_first_completion_token_ms": time_to_first_completion_token_ms,
                    "time_to_first_token_ms": time_to_first_token_ms,
                    "use_case_properties": use_case_properties,
                },
                ingest_units_params.IngestUnitsParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=IngestResponse,
        )


class AsyncIngestResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncIngestResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Pay-i/pay-i-python#accessing-raw-response-data-eg-headers
        """
        return AsyncIngestResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncIngestResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Pay-i/pay-i-python#with_streaming_response
        """
        return AsyncIngestResourceWithStreamingResponse(self)

    async def bulk(
        self,
        *,
        events: Iterable[BulkIngestRequestParam] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BulkIngestResponse:
        """
        Bulk Ingest

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/v1/ingest/bulk",
            body=await async_maybe_transform(events, Iterable[BulkIngestRequestParam]),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BulkIngestResponse,
        )

    async def units(
        self,
        *,
        category: str,
        units: Dict[str, IngestUnits],
        end_to_end_latency_ms: Optional[int] | Omit = omit,
        event_timestamp: Union[str, datetime, None] | Omit = omit,
        http_status_code: Optional[int] | Omit = omit,
        properties: Optional[Dict[str, Optional[str]]] | Omit = omit,
        provider_request_headers: Optional[Iterable[PayICommonModelsAPIRouterHeaderInfoParam]] | Omit = omit,
        provider_request_json: Optional[str] | Omit = omit,
        provider_request_reasoning_json: Optional[str] | Omit = omit,
        provider_response_function_calls: Optional[Iterable[ingest_units_params.ProviderResponseFunctionCall]]
        | Omit = omit,
        provider_response_headers: Optional[Iterable[PayICommonModelsAPIRouterHeaderInfoParam]] | Omit = omit,
        provider_response_id: Optional[str] | Omit = omit,
        provider_response_json: Union[str, SequenceNotStr[str], None] | Omit = omit,
        provider_uri: Optional[str] | Omit = omit,
        resource: Optional[str] | Omit = omit,
        time_to_first_completion_token_ms: Optional[int] | Omit = omit,
        time_to_first_token_ms: Optional[int] | Omit = omit,
        use_case_properties: Optional[Dict[str, Optional[str]]] | Omit = omit,
        limit_ids: Optional[list[str]] | Omit = omit,
        disable_logging: Optional[bool] | Omit = omit,
        request_tags: Optional[list[str]] | Omit = omit,
        use_case_id: Optional[str] | Omit = omit,
        use_case_name: Optional[str] | Omit = omit,
        use_case_step: Optional[str] | Omit = omit,
        use_case_version: Optional[int] | Omit = omit,
        user_id: Optional[str] | Omit = omit,
        resource_scope: Union[str, None] | Omit = omit,
        account_name: Optional[str] | Omit = omit,
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> IngestResponse:
        """
        Ingest an Event

        Args:
          category (str): The name of the category

          resource (str): The name of the resource

          input (int): The number of input units

          output (int): The number of output units

          event_timestamp: (datetime, None): The timestamp of the event

          disable_logging: (bool, optional): Disable logging for the request
          
          limit_ids (list[str], optional): The limit IDs to associate with the request 

          properties (Dict[str, Optional[str]], optional): Properties to associate with the request

          request_tags (list[str], optional): The request tags to associate with the request

          use_case_name (str, optional): The use case name

          use_case_step (str, optional): The use case step

          use_case_id (str, optional): The use case instance id

          use_case_version (int, optional): The use case instance version

          use_case_properties (Dict[str, Optional[str]], optional): The use case properties

          user_id (str, optional): The user id
          
          resource_scope (str, optional): The scope of the resource

          account_name (str, optional): The account name

          extra_headers (Dict[str, str], optional): Additional headers for the request. Defaults to None.

          extra_query (Dict[str, str], optional): Additional query parameters. Defaults to None.

          extra_body (Dict[str, Any], optional): Additional body parameters. Defaults to None.

          timeout (Union[float, None], optional): The timeout for the request in seconds. Defaults to None.
        """
        request_tags = request_tags
        valid_ids_str: str | Omit = omit
        use_case_version_str: str | Omit = omit

        if limit_ids is None or not is_given(limit_ids):
            valid_ids_str = omit
        elif not isinstance(limit_ids, list):  # type: ignore
            raise TypeError("limit_ids must be a list")
        else:
            # Proceed with the list comprehension if limit_ids is given
            valid_ids = [id.strip() for id in limit_ids if id.strip()]
            valid_ids_str = ",".join(valid_ids) if valid_ids else omit

        if use_case_name is None or not is_given(use_case_name):
            use_case_name = omit

        if use_case_step is None or not is_given(use_case_step):
            use_case_step = omit

        if use_case_id is None or not is_given(use_case_id):
            use_case_id = omit

        if use_case_version is None or not is_given(use_case_version):
            use_case_version_str = omit
        else:
            use_case_version_str = str(use_case_version)

        if use_case_properties and is_given(use_case_properties):
            use_case_properties = convert_property_values_to_str(use_case_properties)

        if user_id is None or not is_given(user_id):
            user_id = omit

        if resource_scope is None or not is_given(resource_scope):
            resource_scope = omit

        if account_name is None or not is_given(account_name):
            account_name = omit

        if properties and is_given(properties):
            properties = convert_property_values_to_str(properties)
        
        extra_headers = {
            **strip_not_given(
                {
                    "xProxy-Account-Name": account_name,
                    "xProxy-Limit-IDs": valid_ids_str,
                    "xProxy-Request-Tags": omit,
                    "xProxy-UseCase-ID": use_case_id,
                    "xProxy-UseCase-Name": use_case_name,
                    "xProxy-UseCase-Step": use_case_step,
                    "xProxy-UseCase-Version": use_case_version_str
                    if is_given(use_case_version)
                    else not_given,
                    "xProxy-User-ID": user_id,
                    "xProxy-Resource-Scope": resource_scope,
                    "xProxy-Logging-Disable": str(disable_logging)
                    if is_given(disable_logging)
                    else not_given,
                }
            ),
            **(extra_headers or {}),
        }
        return await self._post(
            "/api/v1/ingest",
            body=await async_maybe_transform(
                {
                    "category": category,
                    "units": units,
                    "end_to_end_latency_ms": end_to_end_latency_ms,
                    "event_timestamp": event_timestamp,
                    "http_status_code": http_status_code,
                    "properties": properties,
                    "provider_request_headers": provider_request_headers,
                    "provider_request_json": provider_request_json,
                    "provider_request_reasoning_json": provider_request_reasoning_json,
                    "provider_response_function_calls": provider_response_function_calls,
                    "provider_response_headers": provider_response_headers,
                    "provider_response_id": provider_response_id,
                    "provider_response_json": provider_response_json,
                    "provider_uri": provider_uri,
                    "resource": resource,
                    "time_to_first_completion_token_ms": time_to_first_completion_token_ms,
                    "time_to_first_token_ms": time_to_first_token_ms,
                    "use_case_properties": use_case_properties,
                },
                ingest_units_params.IngestUnitsParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=IngestResponse,
        )


class IngestResourceWithRawResponse:
    def __init__(self, ingest: IngestResource) -> None:
        self._ingest = ingest

        self.bulk = to_raw_response_wrapper(
            ingest.bulk,
        )
        self.units = to_raw_response_wrapper(
            ingest.units,
        )


class AsyncIngestResourceWithRawResponse:
    def __init__(self, ingest: AsyncIngestResource) -> None:
        self._ingest = ingest

        self.bulk = async_to_raw_response_wrapper(
            ingest.bulk,
        )
        self.units = async_to_raw_response_wrapper(
            ingest.units,
        )


class IngestResourceWithStreamingResponse:
    def __init__(self, ingest: IngestResource) -> None:
        self._ingest = ingest

        self.bulk = to_streamed_response_wrapper(
            ingest.bulk,
        )
        self.units = to_streamed_response_wrapper(
            ingest.units,
        )


class AsyncIngestResourceWithStreamingResponse:
    def __init__(self, ingest: AsyncIngestResource) -> None:
        self._ingest = ingest

        self.bulk = async_to_streamed_response_wrapper(
            ingest.bulk,
        )
        self.units = async_to_streamed_response_wrapper(
            ingest.units,
        )
