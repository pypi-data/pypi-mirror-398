# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict

import httpx

from ..types import event_signal_params, event_wait_for_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
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
from ..types.event_wait_for_response import EventWaitForResponse
from ..types.shared.success_response import SuccessResponse

__all__ = ["EventsResource", "AsyncEventsResource"]


class EventsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> EventsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#accessing-raw-response-data-eg-headers
        """
        return EventsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> EventsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#with_streaming_response
        """
        return EventsResourceWithStreamingResponse(self)

    def signal(
        self,
        event_name: str,
        *,
        data: Dict[str, object],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SuccessResponse:
        """
        Signals an event with associated data, unblocking any clients waiting for this
        event. This enables coordination between different browser sessions, workflows,
        or external processes.

        Args:
          data: Event data to be passed to waiting clients

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not event_name:
            raise ValueError(f"Expected a non-empty value for `event_name` but received {event_name!r}")
        return self._post(
            f"/v1/events/{event_name}",
            body=maybe_transform({"data": data}, event_signal_params.EventSignalParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SuccessResponse,
        )

    def wait_for(
        self,
        event_name: str,
        *,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EventWaitForResponse:
        """
        Waits for a specific event to be signaled by another process, workflow, or
        session. This endpoint blocks until the event is signaled or the timeout is
        reached. Useful for coordinating between multiple browser sessions or workflows.

        Args:
          timeout_ms: Timeout in milliseconds to wait for the event. Defaults to 60000ms (1 minute).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not event_name:
            raise ValueError(f"Expected a non-empty value for `event_name` but received {event_name!r}")
        return self._post(
            f"/v1/events/{event_name}/wait",
            body=maybe_transform({"timeout_ms": timeout_ms}, event_wait_for_params.EventWaitForParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EventWaitForResponse,
        )


class AsyncEventsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncEventsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#accessing-raw-response-data-eg-headers
        """
        return AsyncEventsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncEventsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#with_streaming_response
        """
        return AsyncEventsResourceWithStreamingResponse(self)

    async def signal(
        self,
        event_name: str,
        *,
        data: Dict[str, object],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SuccessResponse:
        """
        Signals an event with associated data, unblocking any clients waiting for this
        event. This enables coordination between different browser sessions, workflows,
        or external processes.

        Args:
          data: Event data to be passed to waiting clients

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not event_name:
            raise ValueError(f"Expected a non-empty value for `event_name` but received {event_name!r}")
        return await self._post(
            f"/v1/events/{event_name}",
            body=await async_maybe_transform({"data": data}, event_signal_params.EventSignalParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SuccessResponse,
        )

    async def wait_for(
        self,
        event_name: str,
        *,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EventWaitForResponse:
        """
        Waits for a specific event to be signaled by another process, workflow, or
        session. This endpoint blocks until the event is signaled or the timeout is
        reached. Useful for coordinating between multiple browser sessions or workflows.

        Args:
          timeout_ms: Timeout in milliseconds to wait for the event. Defaults to 60000ms (1 minute).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not event_name:
            raise ValueError(f"Expected a non-empty value for `event_name` but received {event_name!r}")
        return await self._post(
            f"/v1/events/{event_name}/wait",
            body=await async_maybe_transform({"timeout_ms": timeout_ms}, event_wait_for_params.EventWaitForParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EventWaitForResponse,
        )


class EventsResourceWithRawResponse:
    def __init__(self, events: EventsResource) -> None:
        self._events = events

        self.signal = to_raw_response_wrapper(
            events.signal,
        )
        self.wait_for = to_raw_response_wrapper(
            events.wait_for,
        )


class AsyncEventsResourceWithRawResponse:
    def __init__(self, events: AsyncEventsResource) -> None:
        self._events = events

        self.signal = async_to_raw_response_wrapper(
            events.signal,
        )
        self.wait_for = async_to_raw_response_wrapper(
            events.wait_for,
        )


class EventsResourceWithStreamingResponse:
    def __init__(self, events: EventsResource) -> None:
        self._events = events

        self.signal = to_streamed_response_wrapper(
            events.signal,
        )
        self.wait_for = to_streamed_response_wrapper(
            events.wait_for,
        )


class AsyncEventsResourceWithStreamingResponse:
    def __init__(self, events: AsyncEventsResource) -> None:
        self._events = events

        self.signal = async_to_streamed_response_wrapper(
            events.signal,
        )
        self.wait_for = async_to_streamed_response_wrapper(
            events.wait_for,
        )
