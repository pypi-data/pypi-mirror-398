# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

import httpx

from ....._types import Body, Query, Headers, NotGiven, not_given
from ....._utils import maybe_transform, async_maybe_transform
from ....._compat import cached_property
from ....._resource import SyncAPIResource, AsyncAPIResource
from ....._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ....._base_client import make_request_options
from .....types.credentials.packages.credentials import field_create_params, field_update_params
from .....types.credentials.packages.credentials.field_create_response import FieldCreateResponse
from .....types.credentials.packages.credentials.field_delete_response import FieldDeleteResponse
from .....types.credentials.packages.credentials.field_update_response import FieldUpdateResponse

__all__ = ["FieldsResource", "AsyncFieldsResource"]


class FieldsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> FieldsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/droidrun/mobilerun-sdk-python#accessing-raw-response-data-eg-headers
        """
        return FieldsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> FieldsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/droidrun/mobilerun-sdk-python#with_streaming_response
        """
        return FieldsResourceWithStreamingResponse(self)

    def create(
        self,
        credential_name: str,
        *,
        package_name: str,
        field_type: Literal[
            "email", "username", "password", "api_token", "phone_number", "two_factor_secret", "backup_codes"
        ],
        value: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> FieldCreateResponse:
        """
        Add a new field to an existing credential

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not package_name:
            raise ValueError(f"Expected a non-empty value for `package_name` but received {package_name!r}")
        if not credential_name:
            raise ValueError(f"Expected a non-empty value for `credential_name` but received {credential_name!r}")
        return self._post(
            f"/credentials/packages/{package_name}/credentials/{credential_name}/fields",
            body=maybe_transform(
                {
                    "field_type": field_type,
                    "value": value,
                },
                field_create_params.FieldCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=FieldCreateResponse,
        )

    def update(
        self,
        field_type: Literal[
            "email", "username", "password", "api_token", "phone_number", "two_factor_secret", "backup_codes"
        ],
        *,
        package_name: str,
        credential_name: str,
        value: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> FieldUpdateResponse:
        """
        Update the value of a credential field

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not package_name:
            raise ValueError(f"Expected a non-empty value for `package_name` but received {package_name!r}")
        if not credential_name:
            raise ValueError(f"Expected a non-empty value for `credential_name` but received {credential_name!r}")
        if not field_type:
            raise ValueError(f"Expected a non-empty value for `field_type` but received {field_type!r}")
        return self._patch(
            f"/credentials/packages/{package_name}/credentials/{credential_name}/fields/{field_type}",
            body=maybe_transform({"value": value}, field_update_params.FieldUpdateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=FieldUpdateResponse,
        )

    def delete(
        self,
        field_type: Literal[
            "email", "username", "password", "api_token", "phone_number", "two_factor_secret", "backup_codes"
        ],
        *,
        package_name: str,
        credential_name: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> FieldDeleteResponse:
        """
        Delete a field from a credential

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not package_name:
            raise ValueError(f"Expected a non-empty value for `package_name` but received {package_name!r}")
        if not credential_name:
            raise ValueError(f"Expected a non-empty value for `credential_name` but received {credential_name!r}")
        if not field_type:
            raise ValueError(f"Expected a non-empty value for `field_type` but received {field_type!r}")
        return self._delete(
            f"/credentials/packages/{package_name}/credentials/{credential_name}/fields/{field_type}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=FieldDeleteResponse,
        )


class AsyncFieldsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncFieldsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/droidrun/mobilerun-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncFieldsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncFieldsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/droidrun/mobilerun-sdk-python#with_streaming_response
        """
        return AsyncFieldsResourceWithStreamingResponse(self)

    async def create(
        self,
        credential_name: str,
        *,
        package_name: str,
        field_type: Literal[
            "email", "username", "password", "api_token", "phone_number", "two_factor_secret", "backup_codes"
        ],
        value: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> FieldCreateResponse:
        """
        Add a new field to an existing credential

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not package_name:
            raise ValueError(f"Expected a non-empty value for `package_name` but received {package_name!r}")
        if not credential_name:
            raise ValueError(f"Expected a non-empty value for `credential_name` but received {credential_name!r}")
        return await self._post(
            f"/credentials/packages/{package_name}/credentials/{credential_name}/fields",
            body=await async_maybe_transform(
                {
                    "field_type": field_type,
                    "value": value,
                },
                field_create_params.FieldCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=FieldCreateResponse,
        )

    async def update(
        self,
        field_type: Literal[
            "email", "username", "password", "api_token", "phone_number", "two_factor_secret", "backup_codes"
        ],
        *,
        package_name: str,
        credential_name: str,
        value: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> FieldUpdateResponse:
        """
        Update the value of a credential field

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not package_name:
            raise ValueError(f"Expected a non-empty value for `package_name` but received {package_name!r}")
        if not credential_name:
            raise ValueError(f"Expected a non-empty value for `credential_name` but received {credential_name!r}")
        if not field_type:
            raise ValueError(f"Expected a non-empty value for `field_type` but received {field_type!r}")
        return await self._patch(
            f"/credentials/packages/{package_name}/credentials/{credential_name}/fields/{field_type}",
            body=await async_maybe_transform({"value": value}, field_update_params.FieldUpdateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=FieldUpdateResponse,
        )

    async def delete(
        self,
        field_type: Literal[
            "email", "username", "password", "api_token", "phone_number", "two_factor_secret", "backup_codes"
        ],
        *,
        package_name: str,
        credential_name: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> FieldDeleteResponse:
        """
        Delete a field from a credential

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not package_name:
            raise ValueError(f"Expected a non-empty value for `package_name` but received {package_name!r}")
        if not credential_name:
            raise ValueError(f"Expected a non-empty value for `credential_name` but received {credential_name!r}")
        if not field_type:
            raise ValueError(f"Expected a non-empty value for `field_type` but received {field_type!r}")
        return await self._delete(
            f"/credentials/packages/{package_name}/credentials/{credential_name}/fields/{field_type}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=FieldDeleteResponse,
        )


class FieldsResourceWithRawResponse:
    def __init__(self, fields: FieldsResource) -> None:
        self._fields = fields

        self.create = to_raw_response_wrapper(
            fields.create,
        )
        self.update = to_raw_response_wrapper(
            fields.update,
        )
        self.delete = to_raw_response_wrapper(
            fields.delete,
        )


class AsyncFieldsResourceWithRawResponse:
    def __init__(self, fields: AsyncFieldsResource) -> None:
        self._fields = fields

        self.create = async_to_raw_response_wrapper(
            fields.create,
        )
        self.update = async_to_raw_response_wrapper(
            fields.update,
        )
        self.delete = async_to_raw_response_wrapper(
            fields.delete,
        )


class FieldsResourceWithStreamingResponse:
    def __init__(self, fields: FieldsResource) -> None:
        self._fields = fields

        self.create = to_streamed_response_wrapper(
            fields.create,
        )
        self.update = to_streamed_response_wrapper(
            fields.update,
        )
        self.delete = to_streamed_response_wrapper(
            fields.delete,
        )


class AsyncFieldsResourceWithStreamingResponse:
    def __init__(self, fields: AsyncFieldsResource) -> None:
        self._fields = fields

        self.create = async_to_streamed_response_wrapper(
            fields.create,
        )
        self.update = async_to_streamed_response_wrapper(
            fields.update,
        )
        self.delete = async_to_streamed_response_wrapper(
            fields.delete,
        )
