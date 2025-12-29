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

__all__ = ["ResponseIDResource", "AsyncResponseIDResource"]


class ResponseIDResource(SyncAPIResource):
    @cached_property
    def result(self) -> ResultResource:
        return ResultResource(self._client)

    @cached_property
    def properties(self) -> PropertiesResource:
        return PropertiesResource(self._client)

    @cached_property
    def with_raw_response(self) -> ResponseIDResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Pay-i/pay-i-python#accessing-raw-response-data-eg-headers
        """
        return ResponseIDResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ResponseIDResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Pay-i/pay-i-python#with_streaming_response
        """
        return ResponseIDResourceWithStreamingResponse(self)


class AsyncResponseIDResource(AsyncAPIResource):
    @cached_property
    def result(self) -> AsyncResultResource:
        return AsyncResultResource(self._client)

    @cached_property
    def properties(self) -> AsyncPropertiesResource:
        return AsyncPropertiesResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncResponseIDResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Pay-i/pay-i-python#accessing-raw-response-data-eg-headers
        """
        return AsyncResponseIDResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncResponseIDResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Pay-i/pay-i-python#with_streaming_response
        """
        return AsyncResponseIDResourceWithStreamingResponse(self)


class ResponseIDResourceWithRawResponse:
    def __init__(self, response_id: ResponseIDResource) -> None:
        self._response_id = response_id

    @cached_property
    def result(self) -> ResultResourceWithRawResponse:
        return ResultResourceWithRawResponse(self._response_id.result)

    @cached_property
    def properties(self) -> PropertiesResourceWithRawResponse:
        return PropertiesResourceWithRawResponse(self._response_id.properties)


class AsyncResponseIDResourceWithRawResponse:
    def __init__(self, response_id: AsyncResponseIDResource) -> None:
        self._response_id = response_id

    @cached_property
    def result(self) -> AsyncResultResourceWithRawResponse:
        return AsyncResultResourceWithRawResponse(self._response_id.result)

    @cached_property
    def properties(self) -> AsyncPropertiesResourceWithRawResponse:
        return AsyncPropertiesResourceWithRawResponse(self._response_id.properties)


class ResponseIDResourceWithStreamingResponse:
    def __init__(self, response_id: ResponseIDResource) -> None:
        self._response_id = response_id

    @cached_property
    def result(self) -> ResultResourceWithStreamingResponse:
        return ResultResourceWithStreamingResponse(self._response_id.result)

    @cached_property
    def properties(self) -> PropertiesResourceWithStreamingResponse:
        return PropertiesResourceWithStreamingResponse(self._response_id.properties)


class AsyncResponseIDResourceWithStreamingResponse:
    def __init__(self, response_id: AsyncResponseIDResource) -> None:
        self._response_id = response_id

    @cached_property
    def result(self) -> AsyncResultResourceWithStreamingResponse:
        return AsyncResultResourceWithStreamingResponse(self._response_id.result)

    @cached_property
    def properties(self) -> AsyncPropertiesResourceWithStreamingResponse:
        return AsyncPropertiesResourceWithStreamingResponse(self._response_id.properties)
