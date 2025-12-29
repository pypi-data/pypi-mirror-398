# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from .result import (
    ResultResource,
    AsyncResultResource,
    ResultResourceWithRawResponse,
    AsyncResultResourceWithRawResponse,
    ResultResourceWithStreamingResponse,
    AsyncResultResourceWithStreamingResponse,
)
from ...._compat import cached_property
from .properties import (
    PropertiesResource,
    AsyncPropertiesResource,
    PropertiesResourceWithRawResponse,
    AsyncPropertiesResourceWithRawResponse,
    PropertiesResourceWithStreamingResponse,
    AsyncPropertiesResourceWithStreamingResponse,
)
from ...._resource import SyncAPIResource, AsyncAPIResource

__all__ = ["RequestIDResource", "AsyncRequestIDResource"]


class RequestIDResource(SyncAPIResource):
    @cached_property
    def result(self) -> ResultResource:
        return ResultResource(self._client)

    @cached_property
    def properties(self) -> PropertiesResource:
        return PropertiesResource(self._client)

    @cached_property
    def with_raw_response(self) -> RequestIDResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Pay-i/pay-i-python#accessing-raw-response-data-eg-headers
        """
        return RequestIDResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> RequestIDResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Pay-i/pay-i-python#with_streaming_response
        """
        return RequestIDResourceWithStreamingResponse(self)


class AsyncRequestIDResource(AsyncAPIResource):
    @cached_property
    def result(self) -> AsyncResultResource:
        return AsyncResultResource(self._client)

    @cached_property
    def properties(self) -> AsyncPropertiesResource:
        return AsyncPropertiesResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncRequestIDResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Pay-i/pay-i-python#accessing-raw-response-data-eg-headers
        """
        return AsyncRequestIDResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncRequestIDResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Pay-i/pay-i-python#with_streaming_response
        """
        return AsyncRequestIDResourceWithStreamingResponse(self)


class RequestIDResourceWithRawResponse:
    def __init__(self, request_id: RequestIDResource) -> None:
        self._request_id = request_id

    @cached_property
    def result(self) -> ResultResourceWithRawResponse:
        return ResultResourceWithRawResponse(self._request_id.result)

    @cached_property
    def properties(self) -> PropertiesResourceWithRawResponse:
        return PropertiesResourceWithRawResponse(self._request_id.properties)


class AsyncRequestIDResourceWithRawResponse:
    def __init__(self, request_id: AsyncRequestIDResource) -> None:
        self._request_id = request_id

    @cached_property
    def result(self) -> AsyncResultResourceWithRawResponse:
        return AsyncResultResourceWithRawResponse(self._request_id.result)

    @cached_property
    def properties(self) -> AsyncPropertiesResourceWithRawResponse:
        return AsyncPropertiesResourceWithRawResponse(self._request_id.properties)


class RequestIDResourceWithStreamingResponse:
    def __init__(self, request_id: RequestIDResource) -> None:
        self._request_id = request_id

    @cached_property
    def result(self) -> ResultResourceWithStreamingResponse:
        return ResultResourceWithStreamingResponse(self._request_id.result)

    @cached_property
    def properties(self) -> PropertiesResourceWithStreamingResponse:
        return PropertiesResourceWithStreamingResponse(self._request_id.properties)


class AsyncRequestIDResourceWithStreamingResponse:
    def __init__(self, request_id: AsyncRequestIDResource) -> None:
        self._request_id = request_id

    @cached_property
    def result(self) -> AsyncResultResourceWithStreamingResponse:
        return AsyncResultResourceWithStreamingResponse(self._request_id.result)

    @cached_property
    def properties(self) -> AsyncPropertiesResourceWithStreamingResponse:
        return AsyncPropertiesResourceWithStreamingResponse(self._request_id.properties)
