# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Mapping
from typing_extensions import Self, override

import httpx

from . import _exceptions
from ._qs import Querystring
from ._types import (
    Omit,
    Timeout,
    NotGiven,
    Transport,
    ProxiesTypes,
    RequestOptions,
    not_given,
)
from ._utils import is_given, get_async_library
from ._compat import cached_property
from ._version import __version__
from ._streaming import Stream as Stream, AsyncStream as AsyncStream
from ._exceptions import PayiError, APIStatusError
from ._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
)

if TYPE_CHECKING:
    from .resources import ingest, limits, requests, use_cases, categories
    from .resources.ingest import IngestResource, AsyncIngestResource
    from .resources.limits.limits import LimitsResource, AsyncLimitsResource
    from .resources.requests.requests import RequestsResource, AsyncRequestsResource
    from .resources.use_cases.use_cases import UseCasesResource, AsyncUseCasesResource
    from .resources.categories.categories import CategoriesResource, AsyncCategoriesResource

__all__ = ["Timeout", "Transport", "ProxiesTypes", "RequestOptions", "Payi", "AsyncPayi", "Client", "AsyncClient"]


class Payi(SyncAPIClient):
    # client options
    api_key: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#client) for more details.
        http_client: httpx.Client | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new synchronous Payi client instance.

        This automatically infers the `api_key` argument from the `PAYI_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("PAYI_API_KEY")
        if api_key is None:
            raise PayiError(
                "The api_key client option must be set either by passing api_key to the client or by setting the PAYI_API_KEY environment variable"
            )
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("PAYI_BASE_URL")
        if base_url is None:
            base_url = f"https://api.pay-i.com"

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

    @cached_property
    def limits(self) -> LimitsResource:
        from .resources.limits import LimitsResource

        return LimitsResource(self)

    @cached_property
    def ingest(self) -> IngestResource:
        from .resources.ingest import IngestResource

        return IngestResource(self)

    @cached_property
    def categories(self) -> CategoriesResource:
        from .resources.categories import CategoriesResource

        return CategoriesResource(self)

    @cached_property
    def use_cases(self) -> UseCasesResource:
        from .resources.use_cases import UseCasesResource

        return UseCasesResource(self)

    @cached_property
    def requests(self) -> RequestsResource:
        from .resources.requests import RequestsResource

        return RequestsResource(self)

    @cached_property
    def with_raw_response(self) -> PayiWithRawResponse:
        return PayiWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PayiWithStreamedResponse:
        return PayiWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"xProxy-api-key": api_key}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": "false",
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx.Client | None = None,
        max_retries: int | NotGiven = not_given,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class AsyncPayi(AsyncAPIClient):
    # client options
    api_key: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultAsyncHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#asyncclient) for more details.
        http_client: httpx.AsyncClient | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new async AsyncPayi client instance.

        This automatically infers the `api_key` argument from the `PAYI_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("PAYI_API_KEY")
        if api_key is None:
            raise PayiError(
                "The api_key client option must be set either by passing api_key to the client or by setting the PAYI_API_KEY environment variable"
            )
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("PAYI_BASE_URL")
        if base_url is None:
            base_url = f"https://api.pay-i.com"

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

    @cached_property
    def limits(self) -> AsyncLimitsResource:
        from .resources.limits import AsyncLimitsResource

        return AsyncLimitsResource(self)

    @cached_property
    def ingest(self) -> AsyncIngestResource:
        from .resources.ingest import AsyncIngestResource

        return AsyncIngestResource(self)

    @cached_property
    def categories(self) -> AsyncCategoriesResource:
        from .resources.categories import AsyncCategoriesResource

        return AsyncCategoriesResource(self)

    @cached_property
    def use_cases(self) -> AsyncUseCasesResource:
        from .resources.use_cases import AsyncUseCasesResource

        return AsyncUseCasesResource(self)

    @cached_property
    def requests(self) -> AsyncRequestsResource:
        from .resources.requests import AsyncRequestsResource

        return AsyncRequestsResource(self)

    @cached_property
    def with_raw_response(self) -> AsyncPayiWithRawResponse:
        return AsyncPayiWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPayiWithStreamedResponse:
        return AsyncPayiWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"xProxy-api-key": api_key}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": f"async:{get_async_library()}",
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx.AsyncClient | None = None,
        max_retries: int | NotGiven = not_given,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class PayiWithRawResponse:
    _client: Payi

    def __init__(self, client: Payi) -> None:
        self._client = client

    @cached_property
    def limits(self) -> limits.LimitsResourceWithRawResponse:
        from .resources.limits import LimitsResourceWithRawResponse

        return LimitsResourceWithRawResponse(self._client.limits)

    @cached_property
    def ingest(self) -> ingest.IngestResourceWithRawResponse:
        from .resources.ingest import IngestResourceWithRawResponse

        return IngestResourceWithRawResponse(self._client.ingest)

    @cached_property
    def categories(self) -> categories.CategoriesResourceWithRawResponse:
        from .resources.categories import CategoriesResourceWithRawResponse

        return CategoriesResourceWithRawResponse(self._client.categories)

    @cached_property
    def use_cases(self) -> use_cases.UseCasesResourceWithRawResponse:
        from .resources.use_cases import UseCasesResourceWithRawResponse

        return UseCasesResourceWithRawResponse(self._client.use_cases)

    @cached_property
    def requests(self) -> requests.RequestsResourceWithRawResponse:
        from .resources.requests import RequestsResourceWithRawResponse

        return RequestsResourceWithRawResponse(self._client.requests)


class AsyncPayiWithRawResponse:
    _client: AsyncPayi

    def __init__(self, client: AsyncPayi) -> None:
        self._client = client

    @cached_property
    def limits(self) -> limits.AsyncLimitsResourceWithRawResponse:
        from .resources.limits import AsyncLimitsResourceWithRawResponse

        return AsyncLimitsResourceWithRawResponse(self._client.limits)

    @cached_property
    def ingest(self) -> ingest.AsyncIngestResourceWithRawResponse:
        from .resources.ingest import AsyncIngestResourceWithRawResponse

        return AsyncIngestResourceWithRawResponse(self._client.ingest)

    @cached_property
    def categories(self) -> categories.AsyncCategoriesResourceWithRawResponse:
        from .resources.categories import AsyncCategoriesResourceWithRawResponse

        return AsyncCategoriesResourceWithRawResponse(self._client.categories)

    @cached_property
    def use_cases(self) -> use_cases.AsyncUseCasesResourceWithRawResponse:
        from .resources.use_cases import AsyncUseCasesResourceWithRawResponse

        return AsyncUseCasesResourceWithRawResponse(self._client.use_cases)

    @cached_property
    def requests(self) -> requests.AsyncRequestsResourceWithRawResponse:
        from .resources.requests import AsyncRequestsResourceWithRawResponse

        return AsyncRequestsResourceWithRawResponse(self._client.requests)


class PayiWithStreamedResponse:
    _client: Payi

    def __init__(self, client: Payi) -> None:
        self._client = client

    @cached_property
    def limits(self) -> limits.LimitsResourceWithStreamingResponse:
        from .resources.limits import LimitsResourceWithStreamingResponse

        return LimitsResourceWithStreamingResponse(self._client.limits)

    @cached_property
    def ingest(self) -> ingest.IngestResourceWithStreamingResponse:
        from .resources.ingest import IngestResourceWithStreamingResponse

        return IngestResourceWithStreamingResponse(self._client.ingest)

    @cached_property
    def categories(self) -> categories.CategoriesResourceWithStreamingResponse:
        from .resources.categories import CategoriesResourceWithStreamingResponse

        return CategoriesResourceWithStreamingResponse(self._client.categories)

    @cached_property
    def use_cases(self) -> use_cases.UseCasesResourceWithStreamingResponse:
        from .resources.use_cases import UseCasesResourceWithStreamingResponse

        return UseCasesResourceWithStreamingResponse(self._client.use_cases)

    @cached_property
    def requests(self) -> requests.RequestsResourceWithStreamingResponse:
        from .resources.requests import RequestsResourceWithStreamingResponse

        return RequestsResourceWithStreamingResponse(self._client.requests)


class AsyncPayiWithStreamedResponse:
    _client: AsyncPayi

    def __init__(self, client: AsyncPayi) -> None:
        self._client = client

    @cached_property
    def limits(self) -> limits.AsyncLimitsResourceWithStreamingResponse:
        from .resources.limits import AsyncLimitsResourceWithStreamingResponse

        return AsyncLimitsResourceWithStreamingResponse(self._client.limits)

    @cached_property
    def ingest(self) -> ingest.AsyncIngestResourceWithStreamingResponse:
        from .resources.ingest import AsyncIngestResourceWithStreamingResponse

        return AsyncIngestResourceWithStreamingResponse(self._client.ingest)

    @cached_property
    def categories(self) -> categories.AsyncCategoriesResourceWithStreamingResponse:
        from .resources.categories import AsyncCategoriesResourceWithStreamingResponse

        return AsyncCategoriesResourceWithStreamingResponse(self._client.categories)

    @cached_property
    def use_cases(self) -> use_cases.AsyncUseCasesResourceWithStreamingResponse:
        from .resources.use_cases import AsyncUseCasesResourceWithStreamingResponse

        return AsyncUseCasesResourceWithStreamingResponse(self._client.use_cases)

    @cached_property
    def requests(self) -> requests.AsyncRequestsResourceWithStreamingResponse:
        from .resources.requests import AsyncRequestsResourceWithStreamingResponse

        return AsyncRequestsResourceWithStreamingResponse(self._client.requests)


Client = Payi

AsyncClient = AsyncPayi
