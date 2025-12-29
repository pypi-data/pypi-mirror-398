# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union

import httpx

from ..._types import Body, Omit, Query, Headers, NoneType, NotGiven, omit, not_given
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
from ...types.use_cases import kpi_list_params, kpi_update_params
from ...types.use_cases.kpi_list_response import KpiListResponse

__all__ = ["KpisResource", "AsyncKpisResource"]


class KpisResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> KpisResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Pay-i/pay-i-python#accessing-raw-response-data-eg-headers
        """
        return KpisResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> KpisResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Pay-i/pay-i-python#with_streaming_response
        """
        return KpisResourceWithStreamingResponse(self)

    def update(
        self,
        kpi_name: str,
        *,
        use_case_name: str,
        use_case_id: str,
        score: Union[bool, float, None] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Update a KPI on a Use Case instance

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
        if not kpi_name:
            raise ValueError(f"Expected a non-empty value for `kpi_name` but received {kpi_name!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._put(
            f"/api/v1/use_cases/instances/{use_case_name}/{use_case_id}/kpis/{kpi_name}",
            body=maybe_transform({"score": score}, kpi_update_params.KpiUpdateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def list(
        self,
        use_case_id: str,
        *,
        use_case_name: str,
        cursor: str | Omit = omit,
        kpi_name: str | Omit = omit,
        limit: int | Omit = omit,
        sort_ascending: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursorPage[KpiListResponse]:
        """
        Return all KPI scores for a Use Case instance

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
        return self._get_api_list(
            f"/api/v1/use_cases/instances/{use_case_name}/{use_case_id}/kpis",
            page=SyncCursorPage[KpiListResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "cursor": cursor,
                        "kpi_name": kpi_name,
                        "limit": limit,
                        "sort_ascending": sort_ascending,
                    },
                    kpi_list_params.KpiListParams,
                ),
            ),
            model=KpiListResponse,
        )


class AsyncKpisResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncKpisResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Pay-i/pay-i-python#accessing-raw-response-data-eg-headers
        """
        return AsyncKpisResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncKpisResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Pay-i/pay-i-python#with_streaming_response
        """
        return AsyncKpisResourceWithStreamingResponse(self)

    async def update(
        self,
        kpi_name: str,
        *,
        use_case_name: str,
        use_case_id: str,
        score: Union[bool, float, None] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Update a KPI on a Use Case instance

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
        if not kpi_name:
            raise ValueError(f"Expected a non-empty value for `kpi_name` but received {kpi_name!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._put(
            f"/api/v1/use_cases/instances/{use_case_name}/{use_case_id}/kpis/{kpi_name}",
            body=await async_maybe_transform({"score": score}, kpi_update_params.KpiUpdateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def list(
        self,
        use_case_id: str,
        *,
        use_case_name: str,
        cursor: str | Omit = omit,
        kpi_name: str | Omit = omit,
        limit: int | Omit = omit,
        sort_ascending: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[KpiListResponse, AsyncCursorPage[KpiListResponse]]:
        """
        Return all KPI scores for a Use Case instance

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
        return self._get_api_list(
            f"/api/v1/use_cases/instances/{use_case_name}/{use_case_id}/kpis",
            page=AsyncCursorPage[KpiListResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "cursor": cursor,
                        "kpi_name": kpi_name,
                        "limit": limit,
                        "sort_ascending": sort_ascending,
                    },
                    kpi_list_params.KpiListParams,
                ),
            ),
            model=KpiListResponse,
        )


class KpisResourceWithRawResponse:
    def __init__(self, kpis: KpisResource) -> None:
        self._kpis = kpis

        self.update = to_raw_response_wrapper(
            kpis.update,
        )
        self.list = to_raw_response_wrapper(
            kpis.list,
        )


class AsyncKpisResourceWithRawResponse:
    def __init__(self, kpis: AsyncKpisResource) -> None:
        self._kpis = kpis

        self.update = async_to_raw_response_wrapper(
            kpis.update,
        )
        self.list = async_to_raw_response_wrapper(
            kpis.list,
        )


class KpisResourceWithStreamingResponse:
    def __init__(self, kpis: KpisResource) -> None:
        self._kpis = kpis

        self.update = to_streamed_response_wrapper(
            kpis.update,
        )
        self.list = to_streamed_response_wrapper(
            kpis.list,
        )


class AsyncKpisResourceWithStreamingResponse:
    def __init__(self, kpis: AsyncKpisResource) -> None:
        self._kpis = kpis

        self.update = async_to_streamed_response_wrapper(
            kpis.update,
        )
        self.list = async_to_streamed_response_wrapper(
            kpis.list,
        )
