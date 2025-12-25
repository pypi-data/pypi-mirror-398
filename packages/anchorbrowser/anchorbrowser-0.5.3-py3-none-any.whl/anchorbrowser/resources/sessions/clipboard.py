# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..._types import Body, Query, Headers, NotGiven, not_given
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
from ...types.sessions import clipboard_set_params
from ...types.sessions.clipboard_get_response import ClipboardGetResponse
from ...types.sessions.clipboard_set_response import ClipboardSetResponse

__all__ = ["ClipboardResource", "AsyncClipboardResource"]


class ClipboardResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ClipboardResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#accessing-raw-response-data-eg-headers
        """
        return ClipboardResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ClipboardResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#with_streaming_response
        """
        return ClipboardResourceWithStreamingResponse(self)

    def get(
        self,
        session_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ClipboardGetResponse:
        """
        Retrieves the current content of the clipboard

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return self._get(
            f"/v1/sessions/{session_id}/clipboard",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ClipboardGetResponse,
        )

    def set(
        self,
        session_id: str,
        *,
        text: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ClipboardSetResponse:
        """
        Sets the content of the clipboard

        Args:
          text: Text to set in the clipboard

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return self._post(
            f"/v1/sessions/{session_id}/clipboard",
            body=maybe_transform({"text": text}, clipboard_set_params.ClipboardSetParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ClipboardSetResponse,
        )


class AsyncClipboardResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncClipboardResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#accessing-raw-response-data-eg-headers
        """
        return AsyncClipboardResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncClipboardResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#with_streaming_response
        """
        return AsyncClipboardResourceWithStreamingResponse(self)

    async def get(
        self,
        session_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ClipboardGetResponse:
        """
        Retrieves the current content of the clipboard

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return await self._get(
            f"/v1/sessions/{session_id}/clipboard",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ClipboardGetResponse,
        )

    async def set(
        self,
        session_id: str,
        *,
        text: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ClipboardSetResponse:
        """
        Sets the content of the clipboard

        Args:
          text: Text to set in the clipboard

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return await self._post(
            f"/v1/sessions/{session_id}/clipboard",
            body=await async_maybe_transform({"text": text}, clipboard_set_params.ClipboardSetParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ClipboardSetResponse,
        )


class ClipboardResourceWithRawResponse:
    def __init__(self, clipboard: ClipboardResource) -> None:
        self._clipboard = clipboard

        self.get = to_raw_response_wrapper(
            clipboard.get,
        )
        self.set = to_raw_response_wrapper(
            clipboard.set,
        )


class AsyncClipboardResourceWithRawResponse:
    def __init__(self, clipboard: AsyncClipboardResource) -> None:
        self._clipboard = clipboard

        self.get = async_to_raw_response_wrapper(
            clipboard.get,
        )
        self.set = async_to_raw_response_wrapper(
            clipboard.set,
        )


class ClipboardResourceWithStreamingResponse:
    def __init__(self, clipboard: ClipboardResource) -> None:
        self._clipboard = clipboard

        self.get = to_streamed_response_wrapper(
            clipboard.get,
        )
        self.set = to_streamed_response_wrapper(
            clipboard.set,
        )


class AsyncClipboardResourceWithStreamingResponse:
    def __init__(self, clipboard: AsyncClipboardResource) -> None:
        self._clipboard = clipboard

        self.get = async_to_streamed_response_wrapper(
            clipboard.get,
        )
        self.set = async_to_streamed_response_wrapper(
            clipboard.set,
        )
