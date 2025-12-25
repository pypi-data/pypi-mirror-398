# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
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
from ...types.sessions import keyboard_type_params, keyboard_shortcut_params
from ...types.sessions.keyboard_type_response import KeyboardTypeResponse
from ...types.sessions.keyboard_shortcut_response import KeyboardShortcutResponse

__all__ = ["KeyboardResource", "AsyncKeyboardResource"]


class KeyboardResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> KeyboardResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#accessing-raw-response-data-eg-headers
        """
        return KeyboardResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> KeyboardResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#with_streaming_response
        """
        return KeyboardResourceWithStreamingResponse(self)

    def shortcut(
        self,
        session_id: str,
        *,
        keys: SequenceNotStr[str],
        hold_time: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> KeyboardShortcutResponse:
        """
        Performs a keyboard shortcut using the specified keys

        Args:
          keys: Array of keys to press simultaneously

          hold_time: Time to hold the keys down in milliseconds

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return self._post(
            f"/v1/sessions/{session_id}/keyboard/shortcut",
            body=maybe_transform(
                {
                    "keys": keys,
                    "hold_time": hold_time,
                },
                keyboard_shortcut_params.KeyboardShortcutParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=KeyboardShortcutResponse,
        )

    def type(
        self,
        session_id: str,
        *,
        text: str,
        delay: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> KeyboardTypeResponse:
        """
        Types the specified text with optional delay between keystrokes

        Args:
          text: Text to type

          delay: Delay between keystrokes in milliseconds

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return self._post(
            f"/v1/sessions/{session_id}/keyboard/type",
            body=maybe_transform(
                {
                    "text": text,
                    "delay": delay,
                },
                keyboard_type_params.KeyboardTypeParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=KeyboardTypeResponse,
        )


class AsyncKeyboardResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncKeyboardResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#accessing-raw-response-data-eg-headers
        """
        return AsyncKeyboardResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncKeyboardResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#with_streaming_response
        """
        return AsyncKeyboardResourceWithStreamingResponse(self)

    async def shortcut(
        self,
        session_id: str,
        *,
        keys: SequenceNotStr[str],
        hold_time: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> KeyboardShortcutResponse:
        """
        Performs a keyboard shortcut using the specified keys

        Args:
          keys: Array of keys to press simultaneously

          hold_time: Time to hold the keys down in milliseconds

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return await self._post(
            f"/v1/sessions/{session_id}/keyboard/shortcut",
            body=await async_maybe_transform(
                {
                    "keys": keys,
                    "hold_time": hold_time,
                },
                keyboard_shortcut_params.KeyboardShortcutParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=KeyboardShortcutResponse,
        )

    async def type(
        self,
        session_id: str,
        *,
        text: str,
        delay: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> KeyboardTypeResponse:
        """
        Types the specified text with optional delay between keystrokes

        Args:
          text: Text to type

          delay: Delay between keystrokes in milliseconds

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return await self._post(
            f"/v1/sessions/{session_id}/keyboard/type",
            body=await async_maybe_transform(
                {
                    "text": text,
                    "delay": delay,
                },
                keyboard_type_params.KeyboardTypeParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=KeyboardTypeResponse,
        )


class KeyboardResourceWithRawResponse:
    def __init__(self, keyboard: KeyboardResource) -> None:
        self._keyboard = keyboard

        self.shortcut = to_raw_response_wrapper(
            keyboard.shortcut,
        )
        self.type = to_raw_response_wrapper(
            keyboard.type,
        )


class AsyncKeyboardResourceWithRawResponse:
    def __init__(self, keyboard: AsyncKeyboardResource) -> None:
        self._keyboard = keyboard

        self.shortcut = async_to_raw_response_wrapper(
            keyboard.shortcut,
        )
        self.type = async_to_raw_response_wrapper(
            keyboard.type,
        )


class KeyboardResourceWithStreamingResponse:
    def __init__(self, keyboard: KeyboardResource) -> None:
        self._keyboard = keyboard

        self.shortcut = to_streamed_response_wrapper(
            keyboard.shortcut,
        )
        self.type = to_streamed_response_wrapper(
            keyboard.type,
        )


class AsyncKeyboardResourceWithStreamingResponse:
    def __init__(self, keyboard: AsyncKeyboardResource) -> None:
        self._keyboard = keyboard

        self.shortcut = async_to_streamed_response_wrapper(
            keyboard.shortcut,
        )
        self.type = async_to_streamed_response_wrapper(
            keyboard.type,
        )
