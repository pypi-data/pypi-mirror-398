# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import Literal

import httpx

from ...._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ...._utils import maybe_transform, async_maybe_transform
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.use_cases.definitions import limit_config_create_params
from ....types.use_cases.use_case_definition_response import UseCaseDefinitionResponse

__all__ = ["LimitConfigResource", "AsyncLimitConfigResource"]


class LimitConfigResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> LimitConfigResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Pay-i/pay-i-python#accessing-raw-response-data-eg-headers
        """
        return LimitConfigResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> LimitConfigResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Pay-i/pay-i-python#with_streaming_response
        """
        return LimitConfigResourceWithStreamingResponse(self)

    def create(
        self,
        use_case_name: str,
        *,
        max: float,
        limit_type: Literal["block", "allow"] | Omit = omit,
        properties: Optional[Dict[str, Optional[str]]] | Omit = omit,
        threshold: Optional[float] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UseCaseDefinitionResponse:
        """
        Create a new Use Case default limit configuration

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not use_case_name:
            raise ValueError(f"Expected a non-empty value for `use_case_name` but received {use_case_name!r}")
        return self._post(
            f"/api/v1/use_cases/definitions/{use_case_name}/limit_config",
            body=maybe_transform(
                {
                    "max": max,
                    "limit_type": limit_type,
                    "properties": properties,
                    "threshold": threshold,
                },
                limit_config_create_params.LimitConfigCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UseCaseDefinitionResponse,
        )

    def delete(
        self,
        use_case_name: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UseCaseDefinitionResponse:
        """
        Delete a Use Case default limit configuration

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not use_case_name:
            raise ValueError(f"Expected a non-empty value for `use_case_name` but received {use_case_name!r}")
        return self._delete(
            f"/api/v1/use_cases/definitions/{use_case_name}/limit_config",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UseCaseDefinitionResponse,
        )


class AsyncLimitConfigResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncLimitConfigResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Pay-i/pay-i-python#accessing-raw-response-data-eg-headers
        """
        return AsyncLimitConfigResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncLimitConfigResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Pay-i/pay-i-python#with_streaming_response
        """
        return AsyncLimitConfigResourceWithStreamingResponse(self)

    async def create(
        self,
        use_case_name: str,
        *,
        max: float,
        limit_type: Literal["block", "allow"] | Omit = omit,
        properties: Optional[Dict[str, Optional[str]]] | Omit = omit,
        threshold: Optional[float] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UseCaseDefinitionResponse:
        """
        Create a new Use Case default limit configuration

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not use_case_name:
            raise ValueError(f"Expected a non-empty value for `use_case_name` but received {use_case_name!r}")
        return await self._post(
            f"/api/v1/use_cases/definitions/{use_case_name}/limit_config",
            body=await async_maybe_transform(
                {
                    "max": max,
                    "limit_type": limit_type,
                    "properties": properties,
                    "threshold": threshold,
                },
                limit_config_create_params.LimitConfigCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UseCaseDefinitionResponse,
        )

    async def delete(
        self,
        use_case_name: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UseCaseDefinitionResponse:
        """
        Delete a Use Case default limit configuration

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not use_case_name:
            raise ValueError(f"Expected a non-empty value for `use_case_name` but received {use_case_name!r}")
        return await self._delete(
            f"/api/v1/use_cases/definitions/{use_case_name}/limit_config",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UseCaseDefinitionResponse,
        )


class LimitConfigResourceWithRawResponse:
    def __init__(self, limit_config: LimitConfigResource) -> None:
        self._limit_config = limit_config

        self.create = to_raw_response_wrapper(
            limit_config.create,
        )
        self.delete = to_raw_response_wrapper(
            limit_config.delete,
        )


class AsyncLimitConfigResourceWithRawResponse:
    def __init__(self, limit_config: AsyncLimitConfigResource) -> None:
        self._limit_config = limit_config

        self.create = async_to_raw_response_wrapper(
            limit_config.create,
        )
        self.delete = async_to_raw_response_wrapper(
            limit_config.delete,
        )


class LimitConfigResourceWithStreamingResponse:
    def __init__(self, limit_config: LimitConfigResource) -> None:
        self._limit_config = limit_config

        self.create = to_streamed_response_wrapper(
            limit_config.create,
        )
        self.delete = to_streamed_response_wrapper(
            limit_config.delete,
        )


class AsyncLimitConfigResourceWithStreamingResponse:
    def __init__(self, limit_config: AsyncLimitConfigResource) -> None:
        self._limit_config = limit_config

        self.create = async_to_streamed_response_wrapper(
            limit_config.create,
        )
        self.delete = async_to_streamed_response_wrapper(
            limit_config.delete,
        )
