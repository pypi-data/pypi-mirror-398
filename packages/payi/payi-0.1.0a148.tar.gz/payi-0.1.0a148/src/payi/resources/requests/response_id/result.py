# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ...._types import Body, Query, Headers, NotGiven, not_given
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.request_result import RequestResult

__all__ = ["ResultResource", "AsyncResultResource"]


class ResultResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ResultResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Pay-i/pay-i-python#accessing-raw-response-data-eg-headers
        """
        return ResultResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ResultResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Pay-i/pay-i-python#with_streaming_response
        """
        return ResultResourceWithStreamingResponse(self)

    def retrieve(
        self,
        provider_response_id: str,
        *,
        category: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RequestResult:
        """
        Get a Request results

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not category:
            raise ValueError(f"Expected a non-empty value for `category` but received {category!r}")
        if not provider_response_id:
            raise ValueError(
                f"Expected a non-empty value for `provider_response_id` but received {provider_response_id!r}"
            )
        return self._get(
            f"/api/v1/requests/provider/{category}/{provider_response_id}/result",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RequestResult,
        )


class AsyncResultResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncResultResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Pay-i/pay-i-python#accessing-raw-response-data-eg-headers
        """
        return AsyncResultResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncResultResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Pay-i/pay-i-python#with_streaming_response
        """
        return AsyncResultResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        provider_response_id: str,
        *,
        category: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RequestResult:
        """
        Get a Request results

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not category:
            raise ValueError(f"Expected a non-empty value for `category` but received {category!r}")
        if not provider_response_id:
            raise ValueError(
                f"Expected a non-empty value for `provider_response_id` but received {provider_response_id!r}"
            )
        return await self._get(
            f"/api/v1/requests/provider/{category}/{provider_response_id}/result",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RequestResult,
        )


class ResultResourceWithRawResponse:
    def __init__(self, result: ResultResource) -> None:
        self._result = result

        self.retrieve = to_raw_response_wrapper(
            result.retrieve,
        )


class AsyncResultResourceWithRawResponse:
    def __init__(self, result: AsyncResultResource) -> None:
        self._result = result

        self.retrieve = async_to_raw_response_wrapper(
            result.retrieve,
        )


class ResultResourceWithStreamingResponse:
    def __init__(self, result: ResultResource) -> None:
        self._result = result

        self.retrieve = to_streamed_response_wrapper(
            result.retrieve,
        )


class AsyncResultResourceWithStreamingResponse:
    def __init__(self, result: AsyncResultResource) -> None:
        self._result = result

        self.retrieve = async_to_streamed_response_wrapper(
            result.retrieve,
        )
