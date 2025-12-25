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
    Headers,
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
from ._exceptions import APIStatusError
from ._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
)

if TYPE_CHECKING:
    from .resources import apps, hooks, tasks, devices, credentials
    from .resources.apps import AppsResource, AsyncAppsResource
    from .resources.hooks import HooksResource, AsyncHooksResource
    from .resources.tasks.tasks import TasksResource, AsyncTasksResource
    from .resources.devices.devices import DevicesResource, AsyncDevicesResource
    from .resources.credentials.credentials import CredentialsResource, AsyncCredentialsResource

__all__ = [
    "Timeout",
    "Transport",
    "ProxiesTypes",
    "RequestOptions",
    "Mobilerun",
    "AsyncMobilerun",
    "Client",
    "AsyncClient",
]


class Mobilerun(SyncAPIClient):
    # client options
    api_key: str | None

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
        """Construct a new synchronous Mobilerun client instance.

        This automatically infers the `api_key` argument from the `MOBILERUN_CLOUD_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("MOBILERUN_CLOUD_API_KEY")
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("MOBILERUN_BASE_URL")
        if base_url is None:
            base_url = f"https://api.mobilerun.ai/v1"

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
    def tasks(self) -> TasksResource:
        from .resources.tasks import TasksResource

        return TasksResource(self)

    @cached_property
    def devices(self) -> DevicesResource:
        from .resources.devices import DevicesResource

        return DevicesResource(self)

    @cached_property
    def apps(self) -> AppsResource:
        from .resources.apps import AppsResource

        return AppsResource(self)

    @cached_property
    def credentials(self) -> CredentialsResource:
        from .resources.credentials import CredentialsResource

        return CredentialsResource(self)

    @cached_property
    def hooks(self) -> HooksResource:
        from .resources.hooks import HooksResource

        return HooksResource(self)

    @cached_property
    def with_raw_response(self) -> MobilerunWithRawResponse:
        return MobilerunWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> MobilerunWithStreamedResponse:
        return MobilerunWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        if api_key is None:
            return {}
        return {"Authorization": f"Bearer {api_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": "false",
            **self._custom_headers,
        }

    @override
    def _validate_headers(self, headers: Headers, custom_headers: Headers) -> None:
        if self.api_key and headers.get("Authorization"):
            return
        if isinstance(custom_headers.get("Authorization"), Omit):
            return

        raise TypeError(
            '"Could not resolve authentication method. Expected the api_key to be set. Or for the `Authorization` headers to be explicitly omitted"'
        )

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


class AsyncMobilerun(AsyncAPIClient):
    # client options
    api_key: str | None

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
        """Construct a new async AsyncMobilerun client instance.

        This automatically infers the `api_key` argument from the `MOBILERUN_CLOUD_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("MOBILERUN_CLOUD_API_KEY")
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("MOBILERUN_BASE_URL")
        if base_url is None:
            base_url = f"https://api.mobilerun.ai/v1"

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
    def tasks(self) -> AsyncTasksResource:
        from .resources.tasks import AsyncTasksResource

        return AsyncTasksResource(self)

    @cached_property
    def devices(self) -> AsyncDevicesResource:
        from .resources.devices import AsyncDevicesResource

        return AsyncDevicesResource(self)

    @cached_property
    def apps(self) -> AsyncAppsResource:
        from .resources.apps import AsyncAppsResource

        return AsyncAppsResource(self)

    @cached_property
    def credentials(self) -> AsyncCredentialsResource:
        from .resources.credentials import AsyncCredentialsResource

        return AsyncCredentialsResource(self)

    @cached_property
    def hooks(self) -> AsyncHooksResource:
        from .resources.hooks import AsyncHooksResource

        return AsyncHooksResource(self)

    @cached_property
    def with_raw_response(self) -> AsyncMobilerunWithRawResponse:
        return AsyncMobilerunWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncMobilerunWithStreamedResponse:
        return AsyncMobilerunWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        if api_key is None:
            return {}
        return {"Authorization": f"Bearer {api_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": f"async:{get_async_library()}",
            **self._custom_headers,
        }

    @override
    def _validate_headers(self, headers: Headers, custom_headers: Headers) -> None:
        if self.api_key and headers.get("Authorization"):
            return
        if isinstance(custom_headers.get("Authorization"), Omit):
            return

        raise TypeError(
            '"Could not resolve authentication method. Expected the api_key to be set. Or for the `Authorization` headers to be explicitly omitted"'
        )

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


class MobilerunWithRawResponse:
    _client: Mobilerun

    def __init__(self, client: Mobilerun) -> None:
        self._client = client

    @cached_property
    def tasks(self) -> tasks.TasksResourceWithRawResponse:
        from .resources.tasks import TasksResourceWithRawResponse

        return TasksResourceWithRawResponse(self._client.tasks)

    @cached_property
    def devices(self) -> devices.DevicesResourceWithRawResponse:
        from .resources.devices import DevicesResourceWithRawResponse

        return DevicesResourceWithRawResponse(self._client.devices)

    @cached_property
    def apps(self) -> apps.AppsResourceWithRawResponse:
        from .resources.apps import AppsResourceWithRawResponse

        return AppsResourceWithRawResponse(self._client.apps)

    @cached_property
    def credentials(self) -> credentials.CredentialsResourceWithRawResponse:
        from .resources.credentials import CredentialsResourceWithRawResponse

        return CredentialsResourceWithRawResponse(self._client.credentials)

    @cached_property
    def hooks(self) -> hooks.HooksResourceWithRawResponse:
        from .resources.hooks import HooksResourceWithRawResponse

        return HooksResourceWithRawResponse(self._client.hooks)


class AsyncMobilerunWithRawResponse:
    _client: AsyncMobilerun

    def __init__(self, client: AsyncMobilerun) -> None:
        self._client = client

    @cached_property
    def tasks(self) -> tasks.AsyncTasksResourceWithRawResponse:
        from .resources.tasks import AsyncTasksResourceWithRawResponse

        return AsyncTasksResourceWithRawResponse(self._client.tasks)

    @cached_property
    def devices(self) -> devices.AsyncDevicesResourceWithRawResponse:
        from .resources.devices import AsyncDevicesResourceWithRawResponse

        return AsyncDevicesResourceWithRawResponse(self._client.devices)

    @cached_property
    def apps(self) -> apps.AsyncAppsResourceWithRawResponse:
        from .resources.apps import AsyncAppsResourceWithRawResponse

        return AsyncAppsResourceWithRawResponse(self._client.apps)

    @cached_property
    def credentials(self) -> credentials.AsyncCredentialsResourceWithRawResponse:
        from .resources.credentials import AsyncCredentialsResourceWithRawResponse

        return AsyncCredentialsResourceWithRawResponse(self._client.credentials)

    @cached_property
    def hooks(self) -> hooks.AsyncHooksResourceWithRawResponse:
        from .resources.hooks import AsyncHooksResourceWithRawResponse

        return AsyncHooksResourceWithRawResponse(self._client.hooks)


class MobilerunWithStreamedResponse:
    _client: Mobilerun

    def __init__(self, client: Mobilerun) -> None:
        self._client = client

    @cached_property
    def tasks(self) -> tasks.TasksResourceWithStreamingResponse:
        from .resources.tasks import TasksResourceWithStreamingResponse

        return TasksResourceWithStreamingResponse(self._client.tasks)

    @cached_property
    def devices(self) -> devices.DevicesResourceWithStreamingResponse:
        from .resources.devices import DevicesResourceWithStreamingResponse

        return DevicesResourceWithStreamingResponse(self._client.devices)

    @cached_property
    def apps(self) -> apps.AppsResourceWithStreamingResponse:
        from .resources.apps import AppsResourceWithStreamingResponse

        return AppsResourceWithStreamingResponse(self._client.apps)

    @cached_property
    def credentials(self) -> credentials.CredentialsResourceWithStreamingResponse:
        from .resources.credentials import CredentialsResourceWithStreamingResponse

        return CredentialsResourceWithStreamingResponse(self._client.credentials)

    @cached_property
    def hooks(self) -> hooks.HooksResourceWithStreamingResponse:
        from .resources.hooks import HooksResourceWithStreamingResponse

        return HooksResourceWithStreamingResponse(self._client.hooks)


class AsyncMobilerunWithStreamedResponse:
    _client: AsyncMobilerun

    def __init__(self, client: AsyncMobilerun) -> None:
        self._client = client

    @cached_property
    def tasks(self) -> tasks.AsyncTasksResourceWithStreamingResponse:
        from .resources.tasks import AsyncTasksResourceWithStreamingResponse

        return AsyncTasksResourceWithStreamingResponse(self._client.tasks)

    @cached_property
    def devices(self) -> devices.AsyncDevicesResourceWithStreamingResponse:
        from .resources.devices import AsyncDevicesResourceWithStreamingResponse

        return AsyncDevicesResourceWithStreamingResponse(self._client.devices)

    @cached_property
    def apps(self) -> apps.AsyncAppsResourceWithStreamingResponse:
        from .resources.apps import AsyncAppsResourceWithStreamingResponse

        return AsyncAppsResourceWithStreamingResponse(self._client.apps)

    @cached_property
    def credentials(self) -> credentials.AsyncCredentialsResourceWithStreamingResponse:
        from .resources.credentials import AsyncCredentialsResourceWithStreamingResponse

        return AsyncCredentialsResourceWithStreamingResponse(self._client.credentials)

    @cached_property
    def hooks(self) -> hooks.AsyncHooksResourceWithStreamingResponse:
        from .resources.hooks import AsyncHooksResourceWithStreamingResponse

        return AsyncHooksResourceWithStreamingResponse(self._client.hooks)


Client = Mobilerun

AsyncClient = AsyncMobilerun
