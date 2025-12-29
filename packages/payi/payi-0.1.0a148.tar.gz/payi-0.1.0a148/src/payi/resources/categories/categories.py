# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ...types import category_list_params, category_list_resources_params
from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import maybe_transform
from ..._compat import cached_property
from .resources import (
    ResourcesResource,
    AsyncResourcesResource,
    ResourcesResourceWithRawResponse,
    AsyncResourcesResourceWithRawResponse,
    ResourcesResourceWithStreamingResponse,
    AsyncResourcesResourceWithStreamingResponse,
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
from ...types.category_response import CategoryResponse
from ...types.category_delete_response import CategoryDeleteResponse
from ...types.category_resource_response import CategoryResourceResponse
from ...types.category_delete_resource_response import CategoryDeleteResourceResponse

__all__ = ["CategoriesResource", "AsyncCategoriesResource"]


class CategoriesResource(SyncAPIResource):
    @cached_property
    def resources(self) -> ResourcesResource:
        return ResourcesResource(self._client)

    @cached_property
    def with_raw_response(self) -> CategoriesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Pay-i/pay-i-python#accessing-raw-response-data-eg-headers
        """
        return CategoriesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CategoriesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Pay-i/pay-i-python#with_streaming_response
        """
        return CategoriesResourceWithStreamingResponse(self)

    def list(
        self,
        *,
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
    ) -> SyncCursorPage[CategoryResponse]:
        """
        Get all Categories

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/api/v1/categories",
            page=SyncCursorPage[CategoryResponse],
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
                    category_list_params.CategoryListParams,
                ),
            ),
            model=CategoryResponse,
        )

    def delete(
        self,
        category: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CategoryDeleteResponse:
        """
        Delete a Category and all of its Resources

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not category:
            raise ValueError(f"Expected a non-empty value for `category` but received {category!r}")
        return self._delete(
            f"/api/v1/categories/{category}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CategoryDeleteResponse,
        )

    def delete_resource(
        self,
        resource: str,
        *,
        category: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CategoryDeleteResourceResponse:
        """
        Delete all versions of Resource from a Category

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
        return self._delete(
            f"/api/v1/categories/{category}/resources/{resource}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CategoryDeleteResourceResponse,
        )

    def list_resources(
        self,
        category: str,
        *,
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
        Get all Resources for a Category

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not category:
            raise ValueError(f"Expected a non-empty value for `category` but received {category!r}")
        return self._get_api_list(
            f"/api/v1/categories/{category}/resources",
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
                    category_list_resources_params.CategoryListResourcesParams,
                ),
            ),
            model=CategoryResourceResponse,
        )


class AsyncCategoriesResource(AsyncAPIResource):
    @cached_property
    def resources(self) -> AsyncResourcesResource:
        return AsyncResourcesResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncCategoriesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Pay-i/pay-i-python#accessing-raw-response-data-eg-headers
        """
        return AsyncCategoriesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCategoriesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Pay-i/pay-i-python#with_streaming_response
        """
        return AsyncCategoriesResourceWithStreamingResponse(self)

    def list(
        self,
        *,
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
    ) -> AsyncPaginator[CategoryResponse, AsyncCursorPage[CategoryResponse]]:
        """
        Get all Categories

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/api/v1/categories",
            page=AsyncCursorPage[CategoryResponse],
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
                    category_list_params.CategoryListParams,
                ),
            ),
            model=CategoryResponse,
        )

    async def delete(
        self,
        category: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CategoryDeleteResponse:
        """
        Delete a Category and all of its Resources

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not category:
            raise ValueError(f"Expected a non-empty value for `category` but received {category!r}")
        return await self._delete(
            f"/api/v1/categories/{category}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CategoryDeleteResponse,
        )

    async def delete_resource(
        self,
        resource: str,
        *,
        category: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CategoryDeleteResourceResponse:
        """
        Delete all versions of Resource from a Category

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
        return await self._delete(
            f"/api/v1/categories/{category}/resources/{resource}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CategoryDeleteResourceResponse,
        )

    def list_resources(
        self,
        category: str,
        *,
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
        Get all Resources for a Category

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not category:
            raise ValueError(f"Expected a non-empty value for `category` but received {category!r}")
        return self._get_api_list(
            f"/api/v1/categories/{category}/resources",
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
                    category_list_resources_params.CategoryListResourcesParams,
                ),
            ),
            model=CategoryResourceResponse,
        )


class CategoriesResourceWithRawResponse:
    def __init__(self, categories: CategoriesResource) -> None:
        self._categories = categories

        self.list = to_raw_response_wrapper(
            categories.list,
        )
        self.delete = to_raw_response_wrapper(
            categories.delete,
        )
        self.delete_resource = to_raw_response_wrapper(
            categories.delete_resource,
        )
        self.list_resources = to_raw_response_wrapper(
            categories.list_resources,
        )

    @cached_property
    def resources(self) -> ResourcesResourceWithRawResponse:
        return ResourcesResourceWithRawResponse(self._categories.resources)


class AsyncCategoriesResourceWithRawResponse:
    def __init__(self, categories: AsyncCategoriesResource) -> None:
        self._categories = categories

        self.list = async_to_raw_response_wrapper(
            categories.list,
        )
        self.delete = async_to_raw_response_wrapper(
            categories.delete,
        )
        self.delete_resource = async_to_raw_response_wrapper(
            categories.delete_resource,
        )
        self.list_resources = async_to_raw_response_wrapper(
            categories.list_resources,
        )

    @cached_property
    def resources(self) -> AsyncResourcesResourceWithRawResponse:
        return AsyncResourcesResourceWithRawResponse(self._categories.resources)


class CategoriesResourceWithStreamingResponse:
    def __init__(self, categories: CategoriesResource) -> None:
        self._categories = categories

        self.list = to_streamed_response_wrapper(
            categories.list,
        )
        self.delete = to_streamed_response_wrapper(
            categories.delete,
        )
        self.delete_resource = to_streamed_response_wrapper(
            categories.delete_resource,
        )
        self.list_resources = to_streamed_response_wrapper(
            categories.list_resources,
        )

    @cached_property
    def resources(self) -> ResourcesResourceWithStreamingResponse:
        return ResourcesResourceWithStreamingResponse(self._categories.resources)


class AsyncCategoriesResourceWithStreamingResponse:
    def __init__(self, categories: AsyncCategoriesResource) -> None:
        self._categories = categories

        self.list = async_to_streamed_response_wrapper(
            categories.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            categories.delete,
        )
        self.delete_resource = async_to_streamed_response_wrapper(
            categories.delete_resource,
        )
        self.list_resources = async_to_streamed_response_wrapper(
            categories.list_resources,
        )

    @cached_property
    def resources(self) -> AsyncResourcesResourceWithStreamingResponse:
        return AsyncResourcesResourceWithStreamingResponse(self._categories.resources)
