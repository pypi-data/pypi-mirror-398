# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal

import httpx

from ..types import hook_list_params, hook_update_params, hook_subscribe_params
from .._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.hook_list_response import HookListResponse
from ..types.hook_update_response import HookUpdateResponse
from ..types.hook_perform_response import HookPerformResponse
from ..types.hook_retrieve_response import HookRetrieveResponse
from ..types.hook_subscribe_response import HookSubscribeResponse
from ..types.hook_unsubscribe_response import HookUnsubscribeResponse
from ..types.hook_get_sample_data_response import HookGetSampleDataResponse

__all__ = ["HooksResource", "AsyncHooksResource"]


class HooksResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> HooksResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/droidrun/mobilerun-sdk-python#accessing-raw-response-data-eg-headers
        """
        return HooksResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> HooksResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/droidrun/mobilerun-sdk-python#with_streaming_response
        """
        return HooksResourceWithStreamingResponse(self)

    def retrieve(
        self,
        hook_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HookRetrieveResponse:
        """
        Get a hook subscription by id.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not hook_id:
            raise ValueError(f"Expected a non-empty value for `hook_id` but received {hook_id!r}")
        return self._get(
            f"/hooks/{hook_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HookRetrieveResponse,
        )

    def update(
        self,
        hook_id: str,
        *,
        events: Optional[SequenceNotStr[str]] | Omit = omit,
        state: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HookUpdateResponse:
        """
        Edit a hook subscription (events or state).

        Allows updating the events filter and/or the state of a hook.

        Args:
          events: Updated list of events to subscribe to

          state: Updated hook state (active, disabled, deleted)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not hook_id:
            raise ValueError(f"Expected a non-empty value for `hook_id` but received {hook_id!r}")
        return self._post(
            f"/hooks/{hook_id}/edit",
            body=maybe_transform(
                {
                    "events": events,
                    "state": state,
                },
                hook_update_params.HookUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HookUpdateResponse,
        )

    def list(
        self,
        *,
        order_by: Optional[str] | Omit = omit,
        order_by_direction: Literal["asc", "desc"] | Omit = omit,
        page: int | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HookListResponse:
        """
        List hooks belonging to the requesting user (paginated).

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/hooks/",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "order_by": order_by,
                        "order_by_direction": order_by_direction,
                        "page": page,
                        "page_size": page_size,
                    },
                    hook_list_params.HookListParams,
                ),
            ),
            cast_to=HookListResponse,
        )

    def get_sample_data(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HookGetSampleDataResponse:
        """Get sample hook data for Zapier Perform List (testing/field mapping)."""
        return self._get(
            "/hooks/sample",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HookGetSampleDataResponse,
        )

    def perform(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HookPerformResponse:
        """Zapier Perform endpoint - processes webhook payloads."""
        return self._post(
            "/hooks/perform",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HookPerformResponse,
        )

    def subscribe(
        self,
        *,
        target_url: str,
        events: Optional[SequenceNotStr[str]] | Omit = omit,
        service: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HookSubscribeResponse:
        """Subscribe the current user to a webhook URL.

        Returns subscription id.

        Args:
          target_url: The webhook URL to send notifications to

          events: List of task events to subscribe to (created, running, completed, failed,
              cancelled, paused)

          service: Service that receives the webhook

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/hooks/subscribe",
            body=maybe_transform(
                {
                    "target_url": target_url,
                    "events": events,
                    "service": service,
                },
                hook_subscribe_params.HookSubscribeParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HookSubscribeResponse,
        )

    def unsubscribe(
        self,
        hook_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HookUnsubscribeResponse:
        """
        Unsubscribe a previously created subscription by id.

        Permanently deletes the subscription if it belongs to the user.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not hook_id:
            raise ValueError(f"Expected a non-empty value for `hook_id` but received {hook_id!r}")
        return self._post(
            f"/hooks/{hook_id}/unsubscribe",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HookUnsubscribeResponse,
        )


class AsyncHooksResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncHooksResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/droidrun/mobilerun-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncHooksResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncHooksResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/droidrun/mobilerun-sdk-python#with_streaming_response
        """
        return AsyncHooksResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        hook_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HookRetrieveResponse:
        """
        Get a hook subscription by id.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not hook_id:
            raise ValueError(f"Expected a non-empty value for `hook_id` but received {hook_id!r}")
        return await self._get(
            f"/hooks/{hook_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HookRetrieveResponse,
        )

    async def update(
        self,
        hook_id: str,
        *,
        events: Optional[SequenceNotStr[str]] | Omit = omit,
        state: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HookUpdateResponse:
        """
        Edit a hook subscription (events or state).

        Allows updating the events filter and/or the state of a hook.

        Args:
          events: Updated list of events to subscribe to

          state: Updated hook state (active, disabled, deleted)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not hook_id:
            raise ValueError(f"Expected a non-empty value for `hook_id` but received {hook_id!r}")
        return await self._post(
            f"/hooks/{hook_id}/edit",
            body=await async_maybe_transform(
                {
                    "events": events,
                    "state": state,
                },
                hook_update_params.HookUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HookUpdateResponse,
        )

    async def list(
        self,
        *,
        order_by: Optional[str] | Omit = omit,
        order_by_direction: Literal["asc", "desc"] | Omit = omit,
        page: int | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HookListResponse:
        """
        List hooks belonging to the requesting user (paginated).

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/hooks/",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "order_by": order_by,
                        "order_by_direction": order_by_direction,
                        "page": page,
                        "page_size": page_size,
                    },
                    hook_list_params.HookListParams,
                ),
            ),
            cast_to=HookListResponse,
        )

    async def get_sample_data(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HookGetSampleDataResponse:
        """Get sample hook data for Zapier Perform List (testing/field mapping)."""
        return await self._get(
            "/hooks/sample",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HookGetSampleDataResponse,
        )

    async def perform(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HookPerformResponse:
        """Zapier Perform endpoint - processes webhook payloads."""
        return await self._post(
            "/hooks/perform",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HookPerformResponse,
        )

    async def subscribe(
        self,
        *,
        target_url: str,
        events: Optional[SequenceNotStr[str]] | Omit = omit,
        service: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HookSubscribeResponse:
        """Subscribe the current user to a webhook URL.

        Returns subscription id.

        Args:
          target_url: The webhook URL to send notifications to

          events: List of task events to subscribe to (created, running, completed, failed,
              cancelled, paused)

          service: Service that receives the webhook

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/hooks/subscribe",
            body=await async_maybe_transform(
                {
                    "target_url": target_url,
                    "events": events,
                    "service": service,
                },
                hook_subscribe_params.HookSubscribeParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HookSubscribeResponse,
        )

    async def unsubscribe(
        self,
        hook_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HookUnsubscribeResponse:
        """
        Unsubscribe a previously created subscription by id.

        Permanently deletes the subscription if it belongs to the user.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not hook_id:
            raise ValueError(f"Expected a non-empty value for `hook_id` but received {hook_id!r}")
        return await self._post(
            f"/hooks/{hook_id}/unsubscribe",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HookUnsubscribeResponse,
        )


class HooksResourceWithRawResponse:
    def __init__(self, hooks: HooksResource) -> None:
        self._hooks = hooks

        self.retrieve = to_raw_response_wrapper(
            hooks.retrieve,
        )
        self.update = to_raw_response_wrapper(
            hooks.update,
        )
        self.list = to_raw_response_wrapper(
            hooks.list,
        )
        self.get_sample_data = to_raw_response_wrapper(
            hooks.get_sample_data,
        )
        self.perform = to_raw_response_wrapper(
            hooks.perform,
        )
        self.subscribe = to_raw_response_wrapper(
            hooks.subscribe,
        )
        self.unsubscribe = to_raw_response_wrapper(
            hooks.unsubscribe,
        )


class AsyncHooksResourceWithRawResponse:
    def __init__(self, hooks: AsyncHooksResource) -> None:
        self._hooks = hooks

        self.retrieve = async_to_raw_response_wrapper(
            hooks.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            hooks.update,
        )
        self.list = async_to_raw_response_wrapper(
            hooks.list,
        )
        self.get_sample_data = async_to_raw_response_wrapper(
            hooks.get_sample_data,
        )
        self.perform = async_to_raw_response_wrapper(
            hooks.perform,
        )
        self.subscribe = async_to_raw_response_wrapper(
            hooks.subscribe,
        )
        self.unsubscribe = async_to_raw_response_wrapper(
            hooks.unsubscribe,
        )


class HooksResourceWithStreamingResponse:
    def __init__(self, hooks: HooksResource) -> None:
        self._hooks = hooks

        self.retrieve = to_streamed_response_wrapper(
            hooks.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            hooks.update,
        )
        self.list = to_streamed_response_wrapper(
            hooks.list,
        )
        self.get_sample_data = to_streamed_response_wrapper(
            hooks.get_sample_data,
        )
        self.perform = to_streamed_response_wrapper(
            hooks.perform,
        )
        self.subscribe = to_streamed_response_wrapper(
            hooks.subscribe,
        )
        self.unsubscribe = to_streamed_response_wrapper(
            hooks.unsubscribe,
        )


class AsyncHooksResourceWithStreamingResponse:
    def __init__(self, hooks: AsyncHooksResource) -> None:
        self._hooks = hooks

        self.retrieve = async_to_streamed_response_wrapper(
            hooks.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            hooks.update,
        )
        self.list = async_to_streamed_response_wrapper(
            hooks.list,
        )
        self.get_sample_data = async_to_streamed_response_wrapper(
            hooks.get_sample_data,
        )
        self.perform = async_to_streamed_response_wrapper(
            hooks.perform,
        )
        self.subscribe = async_to_streamed_response_wrapper(
            hooks.subscribe,
        )
        self.unsubscribe = async_to_streamed_response_wrapper(
            hooks.unsubscribe,
        )
