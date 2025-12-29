# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from .request_id.request_id import (
    RequestIDResource,
    AsyncRequestIDResource,
    RequestIDResourceWithRawResponse,
    AsyncRequestIDResourceWithRawResponse,
    RequestIDResourceWithStreamingResponse,
    AsyncRequestIDResourceWithStreamingResponse,
)
from .response_id.response_id import (
    ResponseIDResource,
    AsyncResponseIDResource,
    ResponseIDResourceWithRawResponse,
    AsyncResponseIDResourceWithRawResponse,
    ResponseIDResourceWithStreamingResponse,
    AsyncResponseIDResourceWithStreamingResponse,
)

__all__ = ["RequestsResource", "AsyncRequestsResource"]


class RequestsResource(SyncAPIResource):
    @cached_property
    def request_id(self) -> RequestIDResource:
        return RequestIDResource(self._client)

    @cached_property
    def response_id(self) -> ResponseIDResource:
        return ResponseIDResource(self._client)

    @cached_property
    def with_raw_response(self) -> RequestsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Pay-i/pay-i-python#accessing-raw-response-data-eg-headers
        """
        return RequestsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> RequestsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Pay-i/pay-i-python#with_streaming_response
        """
        return RequestsResourceWithStreamingResponse(self)


class AsyncRequestsResource(AsyncAPIResource):
    @cached_property
    def request_id(self) -> AsyncRequestIDResource:
        return AsyncRequestIDResource(self._client)

    @cached_property
    def response_id(self) -> AsyncResponseIDResource:
        return AsyncResponseIDResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncRequestsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Pay-i/pay-i-python#accessing-raw-response-data-eg-headers
        """
        return AsyncRequestsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncRequestsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Pay-i/pay-i-python#with_streaming_response
        """
        return AsyncRequestsResourceWithStreamingResponse(self)


class RequestsResourceWithRawResponse:
    def __init__(self, requests: RequestsResource) -> None:
        self._requests = requests

    @cached_property
    def request_id(self) -> RequestIDResourceWithRawResponse:
        return RequestIDResourceWithRawResponse(self._requests.request_id)

    @cached_property
    def response_id(self) -> ResponseIDResourceWithRawResponse:
        return ResponseIDResourceWithRawResponse(self._requests.response_id)


class AsyncRequestsResourceWithRawResponse:
    def __init__(self, requests: AsyncRequestsResource) -> None:
        self._requests = requests

    @cached_property
    def request_id(self) -> AsyncRequestIDResourceWithRawResponse:
        return AsyncRequestIDResourceWithRawResponse(self._requests.request_id)

    @cached_property
    def response_id(self) -> AsyncResponseIDResourceWithRawResponse:
        return AsyncResponseIDResourceWithRawResponse(self._requests.response_id)


class RequestsResourceWithStreamingResponse:
    def __init__(self, requests: RequestsResource) -> None:
        self._requests = requests

    @cached_property
    def request_id(self) -> RequestIDResourceWithStreamingResponse:
        return RequestIDResourceWithStreamingResponse(self._requests.request_id)

    @cached_property
    def response_id(self) -> ResponseIDResourceWithStreamingResponse:
        return ResponseIDResourceWithStreamingResponse(self._requests.response_id)


class AsyncRequestsResourceWithStreamingResponse:
    def __init__(self, requests: AsyncRequestsResource) -> None:
        self._requests = requests

    @cached_property
    def request_id(self) -> AsyncRequestIDResourceWithStreamingResponse:
        return AsyncRequestIDResourceWithStreamingResponse(self._requests.request_id)

    @cached_property
    def response_id(self) -> AsyncResponseIDResourceWithStreamingResponse:
        return AsyncResponseIDResourceWithStreamingResponse(self._requests.response_id)
