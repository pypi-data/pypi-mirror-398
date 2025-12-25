# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ...._types import Body, Query, Headers, NotGiven, not_given
from ...._utils import maybe_transform, async_maybe_transform
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.credentials import package_create_params
from .credentials.credentials import (
    CredentialsResource,
    AsyncCredentialsResource,
    CredentialsResourceWithRawResponse,
    AsyncCredentialsResourceWithRawResponse,
    CredentialsResourceWithStreamingResponse,
    AsyncCredentialsResourceWithStreamingResponse,
)
from ....types.credentials.package_list_response import PackageListResponse
from ....types.credentials.package_create_response import PackageCreateResponse

__all__ = ["PackagesResource", "AsyncPackagesResource"]


class PackagesResource(SyncAPIResource):
    @cached_property
    def credentials(self) -> CredentialsResource:
        return CredentialsResource(self._client)

    @cached_property
    def with_raw_response(self) -> PackagesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/droidrun/mobilerun-sdk-python#accessing-raw-response-data-eg-headers
        """
        return PackagesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PackagesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/droidrun/mobilerun-sdk-python#with_streaming_response
        """
        return PackagesResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        package_name: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PackageCreateResponse:
        """
        Initialize a new package/app

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/credentials/packages",
            body=maybe_transform({"package_name": package_name}, package_create_params.PackageCreateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PackageCreateResponse,
        )

    def list(
        self,
        package_name: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PackageListResponse:
        """
        List credentials for a specific package

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not package_name:
            raise ValueError(f"Expected a non-empty value for `package_name` but received {package_name!r}")
        return self._get(
            f"/credentials/packages/{package_name}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PackageListResponse,
        )


class AsyncPackagesResource(AsyncAPIResource):
    @cached_property
    def credentials(self) -> AsyncCredentialsResource:
        return AsyncCredentialsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncPackagesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/droidrun/mobilerun-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncPackagesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPackagesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/droidrun/mobilerun-sdk-python#with_streaming_response
        """
        return AsyncPackagesResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        package_name: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PackageCreateResponse:
        """
        Initialize a new package/app

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/credentials/packages",
            body=await async_maybe_transform({"package_name": package_name}, package_create_params.PackageCreateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PackageCreateResponse,
        )

    async def list(
        self,
        package_name: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PackageListResponse:
        """
        List credentials for a specific package

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not package_name:
            raise ValueError(f"Expected a non-empty value for `package_name` but received {package_name!r}")
        return await self._get(
            f"/credentials/packages/{package_name}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PackageListResponse,
        )


class PackagesResourceWithRawResponse:
    def __init__(self, packages: PackagesResource) -> None:
        self._packages = packages

        self.create = to_raw_response_wrapper(
            packages.create,
        )
        self.list = to_raw_response_wrapper(
            packages.list,
        )

    @cached_property
    def credentials(self) -> CredentialsResourceWithRawResponse:
        return CredentialsResourceWithRawResponse(self._packages.credentials)


class AsyncPackagesResourceWithRawResponse:
    def __init__(self, packages: AsyncPackagesResource) -> None:
        self._packages = packages

        self.create = async_to_raw_response_wrapper(
            packages.create,
        )
        self.list = async_to_raw_response_wrapper(
            packages.list,
        )

    @cached_property
    def credentials(self) -> AsyncCredentialsResourceWithRawResponse:
        return AsyncCredentialsResourceWithRawResponse(self._packages.credentials)


class PackagesResourceWithStreamingResponse:
    def __init__(self, packages: PackagesResource) -> None:
        self._packages = packages

        self.create = to_streamed_response_wrapper(
            packages.create,
        )
        self.list = to_streamed_response_wrapper(
            packages.list,
        )

    @cached_property
    def credentials(self) -> CredentialsResourceWithStreamingResponse:
        return CredentialsResourceWithStreamingResponse(self._packages.credentials)


class AsyncPackagesResourceWithStreamingResponse:
    def __init__(self, packages: AsyncPackagesResource) -> None:
        self._packages = packages

        self.create = async_to_streamed_response_wrapper(
            packages.create,
        )
        self.list = async_to_streamed_response_wrapper(
            packages.list,
        )

    @cached_property
    def credentials(self) -> AsyncCredentialsResourceWithStreamingResponse:
        return AsyncCredentialsResourceWithStreamingResponse(self._packages.credentials)
