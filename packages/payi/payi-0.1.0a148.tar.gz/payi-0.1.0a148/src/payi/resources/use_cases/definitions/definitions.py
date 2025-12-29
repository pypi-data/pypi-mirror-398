# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from .kpis import (
    KpisResource,
    AsyncKpisResource,
    KpisResourceWithRawResponse,
    AsyncKpisResourceWithRawResponse,
    KpisResourceWithStreamingResponse,
    AsyncKpisResourceWithStreamingResponse,
)
from .version import (
    VersionResource,
    AsyncVersionResource,
    VersionResourceWithRawResponse,
    AsyncVersionResourceWithRawResponse,
    VersionResourceWithStreamingResponse,
    AsyncVersionResourceWithStreamingResponse,
)
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
from .limit_config import (
    LimitConfigResource,
    AsyncLimitConfigResource,
    LimitConfigResourceWithRawResponse,
    AsyncLimitConfigResourceWithRawResponse,
    LimitConfigResourceWithStreamingResponse,
    AsyncLimitConfigResourceWithStreamingResponse,
)
from ....pagination import SyncCursorPage, AsyncCursorPage
from ...._base_client import AsyncPaginator, make_request_options
from ....types.use_cases import definition_list_params, definition_create_params, definition_update_params
from ....types.use_cases.use_case_definition_response import UseCaseDefinitionResponse
from ....types.shared_params.pay_i_common_models_budget_management_create_limit_base import (
    PayICommonModelsBudgetManagementCreateLimitBase,
)

__all__ = ["DefinitionsResource", "AsyncDefinitionsResource"]


class DefinitionsResource(SyncAPIResource):
    @cached_property
    def kpis(self) -> KpisResource:
        return KpisResource(self._client)

    @cached_property
    def limit_config(self) -> LimitConfigResource:
        return LimitConfigResource(self._client)

    @cached_property
    def version(self) -> VersionResource:
        return VersionResource(self._client)

    @cached_property
    def with_raw_response(self) -> DefinitionsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Pay-i/pay-i-python#accessing-raw-response-data-eg-headers
        """
        return DefinitionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> DefinitionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Pay-i/pay-i-python#with_streaming_response
        """
        return DefinitionsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        description: str,
        name: str,
        limit_config: PayICommonModelsBudgetManagementCreateLimitBase | Omit = omit,
        logging_enabled: Optional[bool] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UseCaseDefinitionResponse:
        """
        Create a new Use Case

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/v1/use_cases/definitions",
            body=maybe_transform(
                {
                    "description": description,
                    "name": name,
                    "limit_config": limit_config,
                    "logging_enabled": logging_enabled,
                },
                definition_create_params.DefinitionCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UseCaseDefinitionResponse,
        )

    def retrieve(
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
        Get Use Case details

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not use_case_name:
            raise ValueError(f"Expected a non-empty value for `use_case_name` but received {use_case_name!r}")
        return self._get(
            f"/api/v1/use_cases/definitions/{use_case_name}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UseCaseDefinitionResponse,
        )

    def update(
        self,
        use_case_name: str,
        *,
        description: Optional[str] | Omit = omit,
        logging_enabled: Optional[bool] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UseCaseDefinitionResponse:
        """
        Update a Use Case definition

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not use_case_name:
            raise ValueError(f"Expected a non-empty value for `use_case_name` but received {use_case_name!r}")
        return self._put(
            f"/api/v1/use_cases/definitions/{use_case_name}",
            body=maybe_transform(
                {
                    "description": description,
                    "logging_enabled": logging_enabled,
                },
                definition_update_params.DefinitionUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UseCaseDefinitionResponse,
        )

    def list(
        self,
        *,
        cursor: str | Omit = omit,
        limit: int | Omit = omit,
        sort_ascending: bool | Omit = omit,
        use_case_name: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursorPage[UseCaseDefinitionResponse]:
        """
        Get all Use Cases

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/api/v1/use_cases/definitions",
            page=SyncCursorPage[UseCaseDefinitionResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "cursor": cursor,
                        "limit": limit,
                        "sort_ascending": sort_ascending,
                        "use_case_name": use_case_name,
                    },
                    definition_list_params.DefinitionListParams,
                ),
            ),
            model=UseCaseDefinitionResponse,
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
        Delete a Use Case

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not use_case_name:
            raise ValueError(f"Expected a non-empty value for `use_case_name` but received {use_case_name!r}")
        return self._delete(
            f"/api/v1/use_cases/definitions/{use_case_name}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UseCaseDefinitionResponse,
        )


class AsyncDefinitionsResource(AsyncAPIResource):
    @cached_property
    def kpis(self) -> AsyncKpisResource:
        return AsyncKpisResource(self._client)

    @cached_property
    def limit_config(self) -> AsyncLimitConfigResource:
        return AsyncLimitConfigResource(self._client)

    @cached_property
    def version(self) -> AsyncVersionResource:
        return AsyncVersionResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncDefinitionsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Pay-i/pay-i-python#accessing-raw-response-data-eg-headers
        """
        return AsyncDefinitionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncDefinitionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Pay-i/pay-i-python#with_streaming_response
        """
        return AsyncDefinitionsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        description: str,
        name: str,
        limit_config: PayICommonModelsBudgetManagementCreateLimitBase | Omit = omit,
        logging_enabled: Optional[bool] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UseCaseDefinitionResponse:
        """
        Create a new Use Case

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/v1/use_cases/definitions",
            body=await async_maybe_transform(
                {
                    "description": description,
                    "name": name,
                    "limit_config": limit_config,
                    "logging_enabled": logging_enabled,
                },
                definition_create_params.DefinitionCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UseCaseDefinitionResponse,
        )

    async def retrieve(
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
        Get Use Case details

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not use_case_name:
            raise ValueError(f"Expected a non-empty value for `use_case_name` but received {use_case_name!r}")
        return await self._get(
            f"/api/v1/use_cases/definitions/{use_case_name}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UseCaseDefinitionResponse,
        )

    async def update(
        self,
        use_case_name: str,
        *,
        description: Optional[str] | Omit = omit,
        logging_enabled: Optional[bool] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UseCaseDefinitionResponse:
        """
        Update a Use Case definition

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not use_case_name:
            raise ValueError(f"Expected a non-empty value for `use_case_name` but received {use_case_name!r}")
        return await self._put(
            f"/api/v1/use_cases/definitions/{use_case_name}",
            body=await async_maybe_transform(
                {
                    "description": description,
                    "logging_enabled": logging_enabled,
                },
                definition_update_params.DefinitionUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UseCaseDefinitionResponse,
        )

    def list(
        self,
        *,
        cursor: str | Omit = omit,
        limit: int | Omit = omit,
        sort_ascending: bool | Omit = omit,
        use_case_name: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[UseCaseDefinitionResponse, AsyncCursorPage[UseCaseDefinitionResponse]]:
        """
        Get all Use Cases

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/api/v1/use_cases/definitions",
            page=AsyncCursorPage[UseCaseDefinitionResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "cursor": cursor,
                        "limit": limit,
                        "sort_ascending": sort_ascending,
                        "use_case_name": use_case_name,
                    },
                    definition_list_params.DefinitionListParams,
                ),
            ),
            model=UseCaseDefinitionResponse,
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
        Delete a Use Case

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not use_case_name:
            raise ValueError(f"Expected a non-empty value for `use_case_name` but received {use_case_name!r}")
        return await self._delete(
            f"/api/v1/use_cases/definitions/{use_case_name}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UseCaseDefinitionResponse,
        )


class DefinitionsResourceWithRawResponse:
    def __init__(self, definitions: DefinitionsResource) -> None:
        self._definitions = definitions

        self.create = to_raw_response_wrapper(
            definitions.create,
        )
        self.retrieve = to_raw_response_wrapper(
            definitions.retrieve,
        )
        self.update = to_raw_response_wrapper(
            definitions.update,
        )
        self.list = to_raw_response_wrapper(
            definitions.list,
        )
        self.delete = to_raw_response_wrapper(
            definitions.delete,
        )

    @cached_property
    def kpis(self) -> KpisResourceWithRawResponse:
        return KpisResourceWithRawResponse(self._definitions.kpis)

    @cached_property
    def limit_config(self) -> LimitConfigResourceWithRawResponse:
        return LimitConfigResourceWithRawResponse(self._definitions.limit_config)

    @cached_property
    def version(self) -> VersionResourceWithRawResponse:
        return VersionResourceWithRawResponse(self._definitions.version)


class AsyncDefinitionsResourceWithRawResponse:
    def __init__(self, definitions: AsyncDefinitionsResource) -> None:
        self._definitions = definitions

        self.create = async_to_raw_response_wrapper(
            definitions.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            definitions.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            definitions.update,
        )
        self.list = async_to_raw_response_wrapper(
            definitions.list,
        )
        self.delete = async_to_raw_response_wrapper(
            definitions.delete,
        )

    @cached_property
    def kpis(self) -> AsyncKpisResourceWithRawResponse:
        return AsyncKpisResourceWithRawResponse(self._definitions.kpis)

    @cached_property
    def limit_config(self) -> AsyncLimitConfigResourceWithRawResponse:
        return AsyncLimitConfigResourceWithRawResponse(self._definitions.limit_config)

    @cached_property
    def version(self) -> AsyncVersionResourceWithRawResponse:
        return AsyncVersionResourceWithRawResponse(self._definitions.version)


class DefinitionsResourceWithStreamingResponse:
    def __init__(self, definitions: DefinitionsResource) -> None:
        self._definitions = definitions

        self.create = to_streamed_response_wrapper(
            definitions.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            definitions.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            definitions.update,
        )
        self.list = to_streamed_response_wrapper(
            definitions.list,
        )
        self.delete = to_streamed_response_wrapper(
            definitions.delete,
        )

    @cached_property
    def kpis(self) -> KpisResourceWithStreamingResponse:
        return KpisResourceWithStreamingResponse(self._definitions.kpis)

    @cached_property
    def limit_config(self) -> LimitConfigResourceWithStreamingResponse:
        return LimitConfigResourceWithStreamingResponse(self._definitions.limit_config)

    @cached_property
    def version(self) -> VersionResourceWithStreamingResponse:
        return VersionResourceWithStreamingResponse(self._definitions.version)


class AsyncDefinitionsResourceWithStreamingResponse:
    def __init__(self, definitions: AsyncDefinitionsResource) -> None:
        self._definitions = definitions

        self.create = async_to_streamed_response_wrapper(
            definitions.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            definitions.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            definitions.update,
        )
        self.list = async_to_streamed_response_wrapper(
            definitions.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            definitions.delete,
        )

    @cached_property
    def kpis(self) -> AsyncKpisResourceWithStreamingResponse:
        return AsyncKpisResourceWithStreamingResponse(self._definitions.kpis)

    @cached_property
    def limit_config(self) -> AsyncLimitConfigResourceWithStreamingResponse:
        return AsyncLimitConfigResourceWithStreamingResponse(self._definitions.limit_config)

    @cached_property
    def version(self) -> AsyncVersionResourceWithStreamingResponse:
        return AsyncVersionResourceWithStreamingResponse(self._definitions.version)
