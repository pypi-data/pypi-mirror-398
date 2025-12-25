# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..._types import Body, Query, Headers, NotGiven, not_given
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.tasks.media_response import MediaResponse
from ...types.tasks.ui_state_list_response import UiStateListResponse

__all__ = ["UiStatesResource", "AsyncUiStatesResource"]


class UiStatesResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> UiStatesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/droidrun/mobilerun-sdk-python#accessing-raw-response-data-eg-headers
        """
        return UiStatesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> UiStatesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/droidrun/mobilerun-sdk-python#with_streaming_response
        """
        return UiStatesResourceWithStreamingResponse(self)

    def retrieve(
        self,
        index: int,
        *,
        task_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MediaResponse:
        """
        Get Task Ui State

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not task_id:
            raise ValueError(f"Expected a non-empty value for `task_id` but received {task_id!r}")
        return self._get(
            f"/tasks/{task_id}/ui_states/{index}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MediaResponse,
        )

    def list(
        self,
        task_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UiStateListResponse:
        """
        Get Task Ui States

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not task_id:
            raise ValueError(f"Expected a non-empty value for `task_id` but received {task_id!r}")
        return self._get(
            f"/tasks/{task_id}/ui_states",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UiStateListResponse,
        )


class AsyncUiStatesResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncUiStatesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/droidrun/mobilerun-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncUiStatesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncUiStatesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/droidrun/mobilerun-sdk-python#with_streaming_response
        """
        return AsyncUiStatesResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        index: int,
        *,
        task_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MediaResponse:
        """
        Get Task Ui State

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not task_id:
            raise ValueError(f"Expected a non-empty value for `task_id` but received {task_id!r}")
        return await self._get(
            f"/tasks/{task_id}/ui_states/{index}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MediaResponse,
        )

    async def list(
        self,
        task_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UiStateListResponse:
        """
        Get Task Ui States

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not task_id:
            raise ValueError(f"Expected a non-empty value for `task_id` but received {task_id!r}")
        return await self._get(
            f"/tasks/{task_id}/ui_states",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UiStateListResponse,
        )


class UiStatesResourceWithRawResponse:
    def __init__(self, ui_states: UiStatesResource) -> None:
        self._ui_states = ui_states

        self.retrieve = to_raw_response_wrapper(
            ui_states.retrieve,
        )
        self.list = to_raw_response_wrapper(
            ui_states.list,
        )


class AsyncUiStatesResourceWithRawResponse:
    def __init__(self, ui_states: AsyncUiStatesResource) -> None:
        self._ui_states = ui_states

        self.retrieve = async_to_raw_response_wrapper(
            ui_states.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            ui_states.list,
        )


class UiStatesResourceWithStreamingResponse:
    def __init__(self, ui_states: UiStatesResource) -> None:
        self._ui_states = ui_states

        self.retrieve = to_streamed_response_wrapper(
            ui_states.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            ui_states.list,
        )


class AsyncUiStatesResourceWithStreamingResponse:
    def __init__(self, ui_states: AsyncUiStatesResource) -> None:
        self._ui_states = ui_states

        self.retrieve = async_to_streamed_response_wrapper(
            ui_states.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            ui_states.list,
        )
