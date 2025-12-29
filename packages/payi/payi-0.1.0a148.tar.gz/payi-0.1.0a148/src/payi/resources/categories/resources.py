# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Optional
from datetime import datetime

import httpx

from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...pagination import SyncCursorPage, AsyncCursorPage
from ..._base_client import AsyncPaginator, make_request_options
from ...types.categories import resource_list_params, resource_create_params
from ...types.category_resource_response import CategoryResourceResponse

__all__ = ["ResourcesResource", "AsyncResourcesResource"]


class ResourcesResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ResourcesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Pay-i/pay-i-python#accessing-raw-response-data-eg-headers
        """
        return ResourcesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ResourcesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Pay-i/pay-i-python#with_streaming_response
        """
        return ResourcesResourceWithStreamingResponse(self)

    def create(
        self,
        resource: str,
        *,
        category: str,
        units: Dict[str, resource_create_params.Units],
        max_input_units: Optional[int] | Omit = omit,
        max_output_units: Optional[int] | Omit = omit,
        max_total_units: Optional[int] | Omit = omit,
        start_timestamp: Union[str, datetime, None] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CategoryResourceResponse:
        """
        Create a Resource

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not category:
            raise ValueError(f"Expected a non-empty value for `category` but received {category!r}")
        if not resource:
            raise ValueError(f"Expected a non-empty value for `resource` but received {resource!r}")
        return self._post(
            f"/api/v1/categories/{category}/resources/{resource}",
            body=maybe_transform(
                {
                    "units": units,
                    "max_input_units": max_input_units,
                    "max_output_units": max_output_units,
                    "max_total_units": max_total_units,
                    "start_timestamp": start_timestamp,
                },
                resource_create_params.ResourceCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CategoryResourceResponse,
        )

    def retrieve(
        self,
        resource_id: str,
        *,
        category: str,
        resource: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CategoryResourceResponse:
        """
        Get a Resource version details

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not category:
            raise ValueError(f"Expected a non-empty value for `category` but received {category!r}")
        if not resource:
            raise ValueError(f"Expected a non-empty value for `resource` but received {resource!r}")
        if not resource_id:
            raise ValueError(f"Expected a non-empty value for `resource_id` but received {resource_id!r}")
        return self._get(
            f"/api/v1/categories/{category}/resources/{resource}/{resource_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CategoryResourceResponse,
        )

    def list(
        self,
        resource: str,
        *,
        category: str,
        active: bool | Omit = omit,
        cursor: str | Omit = omit,
        limit: int | Omit = omit,
        sort_ascending: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursorPage[CategoryResourceResponse]:
        """
        Get a list of versions of a Resource

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not category:
            raise ValueError(f"Expected a non-empty value for `category` but received {category!r}")
        if not resource:
            raise ValueError(f"Expected a non-empty value for `resource` but received {resource!r}")
        return self._get_api_list(
            f"/api/v1/categories/{category}/resources/{resource}",
            page=SyncCursorPage[CategoryResourceResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "active": active,
                        "cursor": cursor,
                        "limit": limit,
                        "sort_ascending": sort_ascending,
                    },
                    resource_list_params.ResourceListParams,
                ),
            ),
            model=CategoryResourceResponse,
        )

    def delete(
        self,
        resource_id: str,
        *,
        category: str,
        resource: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CategoryResourceResponse:
        """
        Delete a version of the Resource

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not category:
            raise ValueError(f"Expected a non-empty value for `category` but received {category!r}")
        if not resource:
            raise ValueError(f"Expected a non-empty value for `resource` but received {resource!r}")
        if not resource_id:
            raise ValueError(f"Expected a non-empty value for `resource_id` but received {resource_id!r}")
        return self._delete(
            f"/api/v1/categories/{category}/resources/{resource}/{resource_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CategoryResourceResponse,
        )


class AsyncResourcesResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncResourcesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Pay-i/pay-i-python#accessing-raw-response-data-eg-headers
        """
        return AsyncResourcesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncResourcesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Pay-i/pay-i-python#with_streaming_response
        """
        return AsyncResourcesResourceWithStreamingResponse(self)

    async def create(
        self,
        resource: str,
        *,
        category: str,
        units: Dict[str, resource_create_params.Units],
        max_input_units: Optional[int] | Omit = omit,
        max_output_units: Optional[int] | Omit = omit,
        max_total_units: Optional[int] | Omit = omit,
        start_timestamp: Union[str, datetime, None] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CategoryResourceResponse:
        """
        Create a Resource

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not category:
            raise ValueError(f"Expected a non-empty value for `category` but received {category!r}")
        if not resource:
            raise ValueError(f"Expected a non-empty value for `resource` but received {resource!r}")
        return await self._post(
            f"/api/v1/categories/{category}/resources/{resource}",
            body=await async_maybe_transform(
                {
                    "units": units,
                    "max_input_units": max_input_units,
                    "max_output_units": max_output_units,
                    "max_total_units": max_total_units,
                    "start_timestamp": start_timestamp,
                },
                resource_create_params.ResourceCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CategoryResourceResponse,
        )

    async def retrieve(
        self,
        resource_id: str,
        *,
        category: str,
        resource: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CategoryResourceResponse:
        """
        Get a Resource version details

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not category:
            raise ValueError(f"Expected a non-empty value for `category` but received {category!r}")
        if not resource:
            raise ValueError(f"Expected a non-empty value for `resource` but received {resource!r}")
        if not resource_id:
            raise ValueError(f"Expected a non-empty value for `resource_id` but received {resource_id!r}")
        return await self._get(
            f"/api/v1/categories/{category}/resources/{resource}/{resource_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CategoryResourceResponse,
        )

    def list(
        self,
        resource: str,
        *,
        category: str,
        active: bool | Omit = omit,
        cursor: str | Omit = omit,
        limit: int | Omit = omit,
        sort_ascending: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[CategoryResourceResponse, AsyncCursorPage[CategoryResourceResponse]]:
        """
        Get a list of versions of a Resource

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not category:
            raise ValueError(f"Expected a non-empty value for `category` but received {category!r}")
        if not resource:
            raise ValueError(f"Expected a non-empty value for `resource` but received {resource!r}")
        return self._get_api_list(
            f"/api/v1/categories/{category}/resources/{resource}",
            page=AsyncCursorPage[CategoryResourceResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "active": active,
                        "cursor": cursor,
                        "limit": limit,
                        "sort_ascending": sort_ascending,
                    },
                    resource_list_params.ResourceListParams,
                ),
            ),
            model=CategoryResourceResponse,
        )

    async def delete(
        self,
        resource_id: str,
        *,
        category: str,
        resource: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CategoryResourceResponse:
        """
        Delete a version of the Resource

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not category:
            raise ValueError(f"Expected a non-empty value for `category` but received {category!r}")
        if not resource:
            raise ValueError(f"Expected a non-empty value for `resource` but received {resource!r}")
        if not resource_id:
            raise ValueError(f"Expected a non-empty value for `resource_id` but received {resource_id!r}")
        return await self._delete(
            f"/api/v1/categories/{category}/resources/{resource}/{resource_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CategoryResourceResponse,
        )


class ResourcesResourceWithRawResponse:
    def __init__(self, resources: ResourcesResource) -> None:
        self._resources = resources

        self.create = to_raw_response_wrapper(
            resources.create,
        )
        self.retrieve = to_raw_response_wrapper(
            resources.retrieve,
        )
        self.list = to_raw_response_wrapper(
            resources.list,
        )
        self.delete = to_raw_response_wrapper(
            resources.delete,
        )


class AsyncResourcesResourceWithRawResponse:
    def __init__(self, resources: AsyncResourcesResource) -> None:
        self._resources = resources

        self.create = async_to_raw_response_wrapper(
            resources.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            resources.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            resources.list,
        )
        self.delete = async_to_raw_response_wrapper(
            resources.delete,
        )


class ResourcesResourceWithStreamingResponse:
    def __init__(self, resources: ResourcesResource) -> None:
        self._resources = resources

        self.create = to_streamed_response_wrapper(
            resources.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            resources.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            resources.list,
        )
        self.delete = to_streamed_response_wrapper(
            resources.delete,
        )


class AsyncResourcesResourceWithStreamingResponse:
    def __init__(self, resources: AsyncResourcesResource) -> None:
        self._resources = resources

        self.create = async_to_streamed_response_wrapper(
            resources.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            resources.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            resources.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            resources.delete,
        )
