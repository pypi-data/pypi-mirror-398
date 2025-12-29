# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from .kpis import (
    KpisResource,
    AsyncKpisResource,
    KpisResourceWithRawResponse,
    AsyncKpisResourceWithRawResponse,
    KpisResourceWithStreamingResponse,
    AsyncKpisResourceWithStreamingResponse,
)
from ..._types import Body, Query, Headers, NotGiven, not_given
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
from ..._base_client import make_request_options
from .definitions.definitions import (
    DefinitionsResource,
    AsyncDefinitionsResource,
    DefinitionsResourceWithRawResponse,
    AsyncDefinitionsResourceWithRawResponse,
    DefinitionsResourceWithStreamingResponse,
    AsyncDefinitionsResourceWithStreamingResponse,
)
from ...types.use_case_instance_response import UseCaseInstanceResponse

__all__ = ["UseCasesResource", "AsyncUseCasesResource"]


class UseCasesResource(SyncAPIResource):
    @cached_property
    def kpis(self) -> KpisResource:
        return KpisResource(self._client)

    @cached_property
    def definitions(self) -> DefinitionsResource:
        return DefinitionsResource(self._client)

    @cached_property
    def properties(self) -> PropertiesResource:
        return PropertiesResource(self._client)

    @cached_property
    def with_raw_response(self) -> UseCasesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Pay-i/pay-i-python#accessing-raw-response-data-eg-headers
        """
        return UseCasesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> UseCasesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Pay-i/pay-i-python#with_streaming_response
        """
        return UseCasesResourceWithStreamingResponse(self)

    def create(
        self,
        use_case_name: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UseCaseInstanceResponse:
        """
        Create a Use Case instance

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not use_case_name:
            raise ValueError(f"Expected a non-empty value for `use_case_name` but received {use_case_name!r}")
        return self._post(
            f"/api/v1/use_cases/instances/{use_case_name}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UseCaseInstanceResponse,
        )

    def retrieve(
        self,
        use_case_id: str,
        *,
        use_case_name: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UseCaseInstanceResponse:
        """
        Get a Use Case instance details

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not use_case_name:
            raise ValueError(f"Expected a non-empty value for `use_case_name` but received {use_case_name!r}")
        if not use_case_id:
            raise ValueError(f"Expected a non-empty value for `use_case_id` but received {use_case_id!r}")
        return self._get(
            f"/api/v1/use_cases/instances/{use_case_name}/{use_case_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UseCaseInstanceResponse,
        )

    def delete(
        self,
        use_case_id: str,
        *,
        use_case_name: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UseCaseInstanceResponse:
        """
        Delete a Use Case instance

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not use_case_name:
            raise ValueError(f"Expected a non-empty value for `use_case_name` but received {use_case_name!r}")
        if not use_case_id:
            raise ValueError(f"Expected a non-empty value for `use_case_id` but received {use_case_id!r}")
        return self._delete(
            f"/api/v1/use_cases/instances/{use_case_name}/{use_case_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UseCaseInstanceResponse,
        )


class AsyncUseCasesResource(AsyncAPIResource):
    @cached_property
    def kpis(self) -> AsyncKpisResource:
        return AsyncKpisResource(self._client)

    @cached_property
    def definitions(self) -> AsyncDefinitionsResource:
        return AsyncDefinitionsResource(self._client)

    @cached_property
    def properties(self) -> AsyncPropertiesResource:
        return AsyncPropertiesResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncUseCasesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Pay-i/pay-i-python#accessing-raw-response-data-eg-headers
        """
        return AsyncUseCasesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncUseCasesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Pay-i/pay-i-python#with_streaming_response
        """
        return AsyncUseCasesResourceWithStreamingResponse(self)

    async def create(
        self,
        use_case_name: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UseCaseInstanceResponse:
        """
        Create a Use Case instance

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not use_case_name:
            raise ValueError(f"Expected a non-empty value for `use_case_name` but received {use_case_name!r}")
        return await self._post(
            f"/api/v1/use_cases/instances/{use_case_name}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UseCaseInstanceResponse,
        )

    async def retrieve(
        self,
        use_case_id: str,
        *,
        use_case_name: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UseCaseInstanceResponse:
        """
        Get a Use Case instance details

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not use_case_name:
            raise ValueError(f"Expected a non-empty value for `use_case_name` but received {use_case_name!r}")
        if not use_case_id:
            raise ValueError(f"Expected a non-empty value for `use_case_id` but received {use_case_id!r}")
        return await self._get(
            f"/api/v1/use_cases/instances/{use_case_name}/{use_case_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UseCaseInstanceResponse,
        )

    async def delete(
        self,
        use_case_id: str,
        *,
        use_case_name: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UseCaseInstanceResponse:
        """
        Delete a Use Case instance

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not use_case_name:
            raise ValueError(f"Expected a non-empty value for `use_case_name` but received {use_case_name!r}")
        if not use_case_id:
            raise ValueError(f"Expected a non-empty value for `use_case_id` but received {use_case_id!r}")
        return await self._delete(
            f"/api/v1/use_cases/instances/{use_case_name}/{use_case_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UseCaseInstanceResponse,
        )


class UseCasesResourceWithRawResponse:
    def __init__(self, use_cases: UseCasesResource) -> None:
        self._use_cases = use_cases

        self.create = to_raw_response_wrapper(
            use_cases.create,
        )
        self.retrieve = to_raw_response_wrapper(
            use_cases.retrieve,
        )
        self.delete = to_raw_response_wrapper(
            use_cases.delete,
        )

    @cached_property
    def kpis(self) -> KpisResourceWithRawResponse:
        return KpisResourceWithRawResponse(self._use_cases.kpis)

    @cached_property
    def definitions(self) -> DefinitionsResourceWithRawResponse:
        return DefinitionsResourceWithRawResponse(self._use_cases.definitions)

    @cached_property
    def properties(self) -> PropertiesResourceWithRawResponse:
        return PropertiesResourceWithRawResponse(self._use_cases.properties)


class AsyncUseCasesResourceWithRawResponse:
    def __init__(self, use_cases: AsyncUseCasesResource) -> None:
        self._use_cases = use_cases

        self.create = async_to_raw_response_wrapper(
            use_cases.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            use_cases.retrieve,
        )
        self.delete = async_to_raw_response_wrapper(
            use_cases.delete,
        )

    @cached_property
    def kpis(self) -> AsyncKpisResourceWithRawResponse:
        return AsyncKpisResourceWithRawResponse(self._use_cases.kpis)

    @cached_property
    def definitions(self) -> AsyncDefinitionsResourceWithRawResponse:
        return AsyncDefinitionsResourceWithRawResponse(self._use_cases.definitions)

    @cached_property
    def properties(self) -> AsyncPropertiesResourceWithRawResponse:
        return AsyncPropertiesResourceWithRawResponse(self._use_cases.properties)


class UseCasesResourceWithStreamingResponse:
    def __init__(self, use_cases: UseCasesResource) -> None:
        self._use_cases = use_cases

        self.create = to_streamed_response_wrapper(
            use_cases.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            use_cases.retrieve,
        )
        self.delete = to_streamed_response_wrapper(
            use_cases.delete,
        )

    @cached_property
    def kpis(self) -> KpisResourceWithStreamingResponse:
        return KpisResourceWithStreamingResponse(self._use_cases.kpis)

    @cached_property
    def definitions(self) -> DefinitionsResourceWithStreamingResponse:
        return DefinitionsResourceWithStreamingResponse(self._use_cases.definitions)

    @cached_property
    def properties(self) -> PropertiesResourceWithStreamingResponse:
        return PropertiesResourceWithStreamingResponse(self._use_cases.properties)


class AsyncUseCasesResourceWithStreamingResponse:
    def __init__(self, use_cases: AsyncUseCasesResource) -> None:
        self._use_cases = use_cases

        self.create = async_to_streamed_response_wrapper(
            use_cases.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            use_cases.retrieve,
        )
        self.delete = async_to_streamed_response_wrapper(
            use_cases.delete,
        )

    @cached_property
    def kpis(self) -> AsyncKpisResourceWithStreamingResponse:
        return AsyncKpisResourceWithStreamingResponse(self._use_cases.kpis)

    @cached_property
    def definitions(self) -> AsyncDefinitionsResourceWithStreamingResponse:
        return AsyncDefinitionsResourceWithStreamingResponse(self._use_cases.definitions)

    @cached_property
    def properties(self) -> AsyncPropertiesResourceWithStreamingResponse:
        return AsyncPropertiesResourceWithStreamingResponse(self._use_cases.properties)
