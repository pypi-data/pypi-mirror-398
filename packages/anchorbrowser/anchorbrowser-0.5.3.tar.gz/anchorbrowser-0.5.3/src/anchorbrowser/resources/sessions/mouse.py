# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

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
from ..._base_client import make_request_options
from ...types.sessions import mouse_move_params, mouse_click_params, mouse_double_click_params
from ...types.sessions.mouse_move_response import MouseMoveResponse
from ...types.sessions.mouse_click_response import MouseClickResponse
from ...types.sessions.mouse_double_click_response import MouseDoubleClickResponse

__all__ = ["MouseResource", "AsyncMouseResource"]


class MouseResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> MouseResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#accessing-raw-response-data-eg-headers
        """
        return MouseResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> MouseResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#with_streaming_response
        """
        return MouseResourceWithStreamingResponse(self)

    def click(
        self,
        session_id: str,
        *,
        button: Literal["left", "middle", "right"] | Omit = omit,
        index: float | Omit = omit,
        selector: str | Omit = omit,
        selector_timeout_ms: float | Omit = omit,
        x: float | Omit = omit,
        y: float | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MouseClickResponse:
        """
        Performs a mouse click at the specified coordinates

        Args:
          button: Mouse button to use

          index: If a selector was passed and multiple elements match the selector, the index of
              the element in the list (0-based). Defaults to 0.

          selector: A valid CSS selector for the requested element

          selector_timeout_ms: If a selector was passed, timeout in ms for waiting for the DOM element to be
              selected. Defaults to 5000 (5 seconds).

          x: X coordinate

          y: Y coordinate

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return self._post(
            f"/v1/sessions/{session_id}/mouse/click",
            body=maybe_transform(
                {
                    "button": button,
                    "index": index,
                    "selector": selector,
                    "selector_timeout_ms": selector_timeout_ms,
                    "x": x,
                    "y": y,
                },
                mouse_click_params.MouseClickParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MouseClickResponse,
        )

    def double_click(
        self,
        session_id: str,
        *,
        x: int,
        y: int,
        button: Literal["left", "middle", "right"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MouseDoubleClickResponse:
        """
        Performs a double click at the specified coordinates

        Args:
          x: X coordinate

          y: Y coordinate

          button: Mouse button to use

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return self._post(
            f"/v1/sessions/{session_id}/mouse/doubleClick",
            body=maybe_transform(
                {
                    "x": x,
                    "y": y,
                    "button": button,
                },
                mouse_double_click_params.MouseDoubleClickParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MouseDoubleClickResponse,
        )

    def move(
        self,
        session_id: str,
        *,
        x: int,
        y: int,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MouseMoveResponse:
        """
        Moves the mouse cursor to the specified coordinates

        Args:
          x: X coordinate

          y: Y coordinate

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return self._post(
            f"/v1/sessions/{session_id}/mouse/move",
            body=maybe_transform(
                {
                    "x": x,
                    "y": y,
                },
                mouse_move_params.MouseMoveParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MouseMoveResponse,
        )


class AsyncMouseResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncMouseResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#accessing-raw-response-data-eg-headers
        """
        return AsyncMouseResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncMouseResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#with_streaming_response
        """
        return AsyncMouseResourceWithStreamingResponse(self)

    async def click(
        self,
        session_id: str,
        *,
        button: Literal["left", "middle", "right"] | Omit = omit,
        index: float | Omit = omit,
        selector: str | Omit = omit,
        selector_timeout_ms: float | Omit = omit,
        x: float | Omit = omit,
        y: float | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MouseClickResponse:
        """
        Performs a mouse click at the specified coordinates

        Args:
          button: Mouse button to use

          index: If a selector was passed and multiple elements match the selector, the index of
              the element in the list (0-based). Defaults to 0.

          selector: A valid CSS selector for the requested element

          selector_timeout_ms: If a selector was passed, timeout in ms for waiting for the DOM element to be
              selected. Defaults to 5000 (5 seconds).

          x: X coordinate

          y: Y coordinate

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return await self._post(
            f"/v1/sessions/{session_id}/mouse/click",
            body=await async_maybe_transform(
                {
                    "button": button,
                    "index": index,
                    "selector": selector,
                    "selector_timeout_ms": selector_timeout_ms,
                    "x": x,
                    "y": y,
                },
                mouse_click_params.MouseClickParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MouseClickResponse,
        )

    async def double_click(
        self,
        session_id: str,
        *,
        x: int,
        y: int,
        button: Literal["left", "middle", "right"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MouseDoubleClickResponse:
        """
        Performs a double click at the specified coordinates

        Args:
          x: X coordinate

          y: Y coordinate

          button: Mouse button to use

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return await self._post(
            f"/v1/sessions/{session_id}/mouse/doubleClick",
            body=await async_maybe_transform(
                {
                    "x": x,
                    "y": y,
                    "button": button,
                },
                mouse_double_click_params.MouseDoubleClickParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MouseDoubleClickResponse,
        )

    async def move(
        self,
        session_id: str,
        *,
        x: int,
        y: int,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MouseMoveResponse:
        """
        Moves the mouse cursor to the specified coordinates

        Args:
          x: X coordinate

          y: Y coordinate

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return await self._post(
            f"/v1/sessions/{session_id}/mouse/move",
            body=await async_maybe_transform(
                {
                    "x": x,
                    "y": y,
                },
                mouse_move_params.MouseMoveParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MouseMoveResponse,
        )


class MouseResourceWithRawResponse:
    def __init__(self, mouse: MouseResource) -> None:
        self._mouse = mouse

        self.click = to_raw_response_wrapper(
            mouse.click,
        )
        self.double_click = to_raw_response_wrapper(
            mouse.double_click,
        )
        self.move = to_raw_response_wrapper(
            mouse.move,
        )


class AsyncMouseResourceWithRawResponse:
    def __init__(self, mouse: AsyncMouseResource) -> None:
        self._mouse = mouse

        self.click = async_to_raw_response_wrapper(
            mouse.click,
        )
        self.double_click = async_to_raw_response_wrapper(
            mouse.double_click,
        )
        self.move = async_to_raw_response_wrapper(
            mouse.move,
        )


class MouseResourceWithStreamingResponse:
    def __init__(self, mouse: MouseResource) -> None:
        self._mouse = mouse

        self.click = to_streamed_response_wrapper(
            mouse.click,
        )
        self.double_click = to_streamed_response_wrapper(
            mouse.double_click,
        )
        self.move = to_streamed_response_wrapper(
            mouse.move,
        )


class AsyncMouseResourceWithStreamingResponse:
    def __init__(self, mouse: AsyncMouseResource) -> None:
        self._mouse = mouse

        self.click = async_to_streamed_response_wrapper(
            mouse.click,
        )
        self.double_click = async_to_streamed_response_wrapper(
            mouse.double_click,
        )
        self.move = async_to_streamed_response_wrapper(
            mouse.move,
        )
