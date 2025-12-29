# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Optional
from datetime import datetime
from typing_extensions import Literal

import httpx

from ...types import limit_list_params, limit_reset_params, limit_create_params, limit_update_params
from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from .properties import (
    PropertiesResource,
    AsyncPropertiesResource,
    PropertiesResourceWithRawResponse,
    AsyncPropertiesResourceWithRawResponse,
    PropertiesResourceWithStreamingResponse,
    AsyncPropertiesResourceWithStreamingResponse,
)
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...pagination import SyncCursorPage, AsyncCursorPage
from ..._base_client import AsyncPaginator, make_request_options
from ...types.limit_response import LimitResponse
from ...types.default_response import DefaultResponse
from ...types.limit_list_response import LimitListResponse
from ...types.limit_history_response import LimitHistoryResponse

__all__ = ["LimitsResource", "AsyncLimitsResource"]


class LimitsResource(SyncAPIResource):
    @cached_property
    def properties(self) -> PropertiesResource:
        return PropertiesResource(self._client)

    @cached_property
    def with_raw_response(self) -> LimitsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Pay-i/pay-i-python#accessing-raw-response-data-eg-headers
        """
        return LimitsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> LimitsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Pay-i/pay-i-python#with_streaming_response
        """
        return LimitsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        limit_name: str,
        max: float,
        limit_id: Optional[str] | Omit = omit,
        limit_type: Literal["block", "allow"] | Omit = omit,
        properties: Optional[Dict[str, Optional[str]]] | Omit = omit,
        threshold: Optional[float] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LimitResponse:
        """
        Create a Limit

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/v1/limits",
            body=maybe_transform(
                {
                    "limit_name": limit_name,
                    "max": max,
                    "limit_id": limit_id,
                    "limit_type": limit_type,
                    "properties": properties,
                    "threshold": threshold,
                },
                limit_create_params.LimitCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LimitResponse,
        )

    def retrieve(
        self,
        limit_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LimitResponse:
        """
        Get Limit details

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not limit_id:
            raise ValueError(f"Expected a non-empty value for `limit_id` but received {limit_id!r}")
        return self._get(
            f"/api/v1/limits/{limit_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LimitResponse,
        )

    def update(
        self,
        limit_id: str,
        *,
        limit_name: Optional[str] | Omit = omit,
        max: Optional[float] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LimitResponse:
        """
        Update a Limit

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not limit_id:
            raise ValueError(f"Expected a non-empty value for `limit_id` but received {limit_id!r}")
        return self._put(
            f"/api/v1/limits/{limit_id}",
            body=maybe_transform(
                {
                    "limit_name": limit_name,
                    "max": max,
                },
                limit_update_params.LimitUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LimitResponse,
        )

    def list(
        self,
        *,
        cursor: str | Omit = omit,
        limit: int | Omit = omit,
        limit_name: str | Omit = omit,
        sort_ascending: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursorPage[LimitListResponse]:
        """
        Get all Limits

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/api/v1/limits",
            page=SyncCursorPage[LimitListResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "cursor": cursor,
                        "limit": limit,
                        "limit_name": limit_name,
                        "sort_ascending": sort_ascending,
                    },
                    limit_list_params.LimitListParams,
                ),
            ),
            model=LimitListResponse,
        )

    def delete(
        self,
        limit_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DefaultResponse:
        """
        Delete a Limit

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not limit_id:
            raise ValueError(f"Expected a non-empty value for `limit_id` but received {limit_id!r}")
        return self._delete(
            f"/api/v1/limits/{limit_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DefaultResponse,
        )

    def reset(
        self,
        limit_id: str,
        *,
        reset_date: Union[str, datetime] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LimitHistoryResponse:
        """
        Reset a Limit

        Args:
          reset_date: Effective reset date

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not limit_id:
            raise ValueError(f"Expected a non-empty value for `limit_id` but received {limit_id!r}")
        return self._post(
            f"/api/v1/limits/{limit_id}/reset",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"reset_date": reset_date}, limit_reset_params.LimitResetParams),
            ),
            cast_to=LimitHistoryResponse,
        )


class AsyncLimitsResource(AsyncAPIResource):
    @cached_property
    def properties(self) -> AsyncPropertiesResource:
        return AsyncPropertiesResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncLimitsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Pay-i/pay-i-python#accessing-raw-response-data-eg-headers
        """
        return AsyncLimitsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncLimitsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Pay-i/pay-i-python#with_streaming_response
        """
        return AsyncLimitsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        limit_name: str,
        max: float,
        limit_id: Optional[str] | Omit = omit,
        limit_type: Literal["block", "allow"] | Omit = omit,
        properties: Optional[Dict[str, Optional[str]]] | Omit = omit,
        threshold: Optional[float] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LimitResponse:
        """
        Create a Limit

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/v1/limits",
            body=await async_maybe_transform(
                {
                    "limit_name": limit_name,
                    "max": max,
                    "limit_id": limit_id,
                    "limit_type": limit_type,
                    "properties": properties,
                    "threshold": threshold,
                },
                limit_create_params.LimitCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LimitResponse,
        )

    async def retrieve(
        self,
        limit_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LimitResponse:
        """
        Get Limit details

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not limit_id:
            raise ValueError(f"Expected a non-empty value for `limit_id` but received {limit_id!r}")
        return await self._get(
            f"/api/v1/limits/{limit_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LimitResponse,
        )

    async def update(
        self,
        limit_id: str,
        *,
        limit_name: Optional[str] | Omit = omit,
        max: Optional[float] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LimitResponse:
        """
        Update a Limit

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not limit_id:
            raise ValueError(f"Expected a non-empty value for `limit_id` but received {limit_id!r}")
        return await self._put(
            f"/api/v1/limits/{limit_id}",
            body=await async_maybe_transform(
                {
                    "limit_name": limit_name,
                    "max": max,
                },
                limit_update_params.LimitUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LimitResponse,
        )

    def list(
        self,
        *,
        cursor: str | Omit = omit,
        limit: int | Omit = omit,
        limit_name: str | Omit = omit,
        sort_ascending: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[LimitListResponse, AsyncCursorPage[LimitListResponse]]:
        """
        Get all Limits

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/api/v1/limits",
            page=AsyncCursorPage[LimitListResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "cursor": cursor,
                        "limit": limit,
                        "limit_name": limit_name,
                        "sort_ascending": sort_ascending,
                    },
                    limit_list_params.LimitListParams,
                ),
            ),
            model=LimitListResponse,
        )

    async def delete(
        self,
        limit_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DefaultResponse:
        """
        Delete a Limit

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not limit_id:
            raise ValueError(f"Expected a non-empty value for `limit_id` but received {limit_id!r}")
        return await self._delete(
            f"/api/v1/limits/{limit_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DefaultResponse,
        )

    async def reset(
        self,
        limit_id: str,
        *,
        reset_date: Union[str, datetime] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LimitHistoryResponse:
        """
        Reset a Limit

        Args:
          reset_date: Effective reset date

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not limit_id:
            raise ValueError(f"Expected a non-empty value for `limit_id` but received {limit_id!r}")
        return await self._post(
            f"/api/v1/limits/{limit_id}/reset",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform({"reset_date": reset_date}, limit_reset_params.LimitResetParams),
            ),
            cast_to=LimitHistoryResponse,
        )


class LimitsResourceWithRawResponse:
    def __init__(self, limits: LimitsResource) -> None:
        self._limits = limits

        self.create = to_raw_response_wrapper(
            limits.create,
        )
        self.retrieve = to_raw_response_wrapper(
            limits.retrieve,
        )
        self.update = to_raw_response_wrapper(
            limits.update,
        )
        self.list = to_raw_response_wrapper(
            limits.list,
        )
        self.delete = to_raw_response_wrapper(
            limits.delete,
        )
        self.reset = to_raw_response_wrapper(
            limits.reset,
        )

    @cached_property
    def properties(self) -> PropertiesResourceWithRawResponse:
        return PropertiesResourceWithRawResponse(self._limits.properties)


class AsyncLimitsResourceWithRawResponse:
    def __init__(self, limits: AsyncLimitsResource) -> None:
        self._limits = limits

        self.create = async_to_raw_response_wrapper(
            limits.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            limits.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            limits.update,
        )
        self.list = async_to_raw_response_wrapper(
            limits.list,
        )
        self.delete = async_to_raw_response_wrapper(
            limits.delete,
        )
        self.reset = async_to_raw_response_wrapper(
            limits.reset,
        )

    @cached_property
    def properties(self) -> AsyncPropertiesResourceWithRawResponse:
        return AsyncPropertiesResourceWithRawResponse(self._limits.properties)


class LimitsResourceWithStreamingResponse:
    def __init__(self, limits: LimitsResource) -> None:
        self._limits = limits

        self.create = to_streamed_response_wrapper(
            limits.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            limits.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            limits.update,
        )
        self.list = to_streamed_response_wrapper(
            limits.list,
        )
        self.delete = to_streamed_response_wrapper(
            limits.delete,
        )
        self.reset = to_streamed_response_wrapper(
            limits.reset,
        )

    @cached_property
    def properties(self) -> PropertiesResourceWithStreamingResponse:
        return PropertiesResourceWithStreamingResponse(self._limits.properties)


class AsyncLimitsResourceWithStreamingResponse:
    def __init__(self, limits: AsyncLimitsResource) -> None:
        self._limits = limits

        self.create = async_to_streamed_response_wrapper(
            limits.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            limits.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            limits.update,
        )
        self.list = async_to_streamed_response_wrapper(
            limits.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            limits.delete,
        )
        self.reset = async_to_streamed_response_wrapper(
            limits.reset,
        )

    @cached_property
    def properties(self) -> AsyncPropertiesResourceWithStreamingResponse:
        return AsyncPropertiesResourceWithStreamingResponse(self._limits.properties)
