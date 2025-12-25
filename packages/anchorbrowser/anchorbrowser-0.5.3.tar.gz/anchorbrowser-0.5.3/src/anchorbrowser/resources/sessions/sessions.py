# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Mapping, Iterable, cast
from typing_extensions import Literal

import httpx

from .all import (
    AllResource,
    AsyncAllResource,
    AllResourceWithRawResponse,
    AsyncAllResourceWithRawResponse,
    AllResourceWithStreamingResponse,
    AsyncAllResourceWithStreamingResponse,
)
from .mouse import (
    MouseResource,
    AsyncMouseResource,
    MouseResourceWithRawResponse,
    AsyncMouseResourceWithRawResponse,
    MouseResourceWithStreamingResponse,
    AsyncMouseResourceWithStreamingResponse,
)
from ...types import (
    session_goto_params,
    session_paste_params,
    session_create_params,
    session_scroll_params,
    session_upload_file_params,
    session_drag_and_drop_params,
)
from ..._types import Body, Omit, Query, Headers, NotGiven, FileTypes, omit, not_given
from ..._utils import extract_files, maybe_transform, deepcopy_minimal, async_maybe_transform
from .keyboard import (
    KeyboardResource,
    AsyncKeyboardResource,
    KeyboardResourceWithRawResponse,
    AsyncKeyboardResourceWithRawResponse,
    KeyboardResourceWithStreamingResponse,
    AsyncKeyboardResourceWithStreamingResponse,
)
from ..._compat import cached_property
from ..._models import construct_type
from .clipboard import (
    ClipboardResource,
    AsyncClipboardResource,
    ClipboardResourceWithRawResponse,
    AsyncClipboardResourceWithRawResponse,
    ClipboardResourceWithStreamingResponse,
    AsyncClipboardResourceWithStreamingResponse,
)
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    BinaryAPIResponse,
    AsyncBinaryAPIResponse,
    StreamedBinaryAPIResponse,
    AsyncStreamedBinaryAPIResponse,
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    to_custom_raw_response_wrapper,
    async_to_streamed_response_wrapper,
    to_custom_streamed_response_wrapper,
    async_to_custom_raw_response_wrapper,
    async_to_custom_streamed_response_wrapper,
)
from .agent.agent import (
    AgentResource,
    AsyncAgentResource,
    AgentResourceWithRawResponse,
    AsyncAgentResourceWithRawResponse,
    AgentResourceWithStreamingResponse,
    AsyncAgentResourceWithStreamingResponse,
)
from ..._base_client import make_request_options
from .recordings.recordings import (
    RecordingsResource,
    AsyncRecordingsResource,
    RecordingsResourceWithRawResponse,
    AsyncRecordingsResourceWithRawResponse,
    RecordingsResourceWithStreamingResponse,
    AsyncRecordingsResourceWithStreamingResponse,
)
from ...types.session_copy_response import SessionCopyResponse
from ...types.session_goto_response import SessionGotoResponse
from ...types.session_paste_response import SessionPasteResponse
from ...types.session_create_response import SessionCreateResponse
from ...types.session_scroll_response import SessionScrollResponse
from ...types.shared.success_response import SuccessResponse
from ...types.session_retrieve_response import SessionRetrieveResponse
from ...types.session_list_pages_response import SessionListPagesResponse
from ...types.session_upload_file_response import SessionUploadFileResponse
from ...types.session_drag_and_drop_response import SessionDragAndDropResponse
from ...types.session_retrieve_downloads_response import SessionRetrieveDownloadsResponse

__all__ = ["SessionsResource", "AsyncSessionsResource"]


class SessionsResource(SyncAPIResource):
    @cached_property
    def all(self) -> AllResource:
        return AllResource(self._client)

    @cached_property
    def recordings(self) -> RecordingsResource:
        return RecordingsResource(self._client)

    @cached_property
    def mouse(self) -> MouseResource:
        return MouseResource(self._client)

    @cached_property
    def keyboard(self) -> KeyboardResource:
        return KeyboardResource(self._client)

    @cached_property
    def clipboard(self) -> ClipboardResource:
        return ClipboardResource(self._client)
    @cached_property
    def agent(self) -> AgentResource:
        return AgentResource(self._client)

    @cached_property
    def with_raw_response(self) -> SessionsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#accessing-raw-response-data-eg-headers
        """
        return SessionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SessionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#with_streaming_response
        """
        return SessionsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        browser: session_create_params.Browser | Omit = omit,
        integrations: Iterable[session_create_params.Integration] | Omit = omit,
        session: session_create_params.Session | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionCreateResponse:
        """
        Allocates a new browser session for the user, with optional configurations for
        ad-blocking, captcha solving, proxy usage, and idle timeout.

        Args:
          browser: Browser-specific configurations.

          integrations: Array of integrations to load in the browser session. Integrations must be
              previously created using the Integrations API.

          session: Session-related configurations.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/sessions",
            body=maybe_transform(
                {
                    "browser": browser,
                    "integrations": integrations,
                    "session": session,
                },
                session_create_params.SessionCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionCreateResponse,
        )

    def retrieve(
        self,
        session_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionRetrieveResponse:
        """
        Retrieves detailed information about a specific browser session.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        
        # Get raw response to unwrap the data field
        raw_response = cast(dict[str, object], self._get(
            f"/v1/sessions/{session_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,  # Get as raw object (dict) to unwrap
        ))
        
        # Unwrap data field if API returns { data: {...} }
        data: object = raw_response.get("data", raw_response)
        
        # Construct the response type from the unwrapped data
        return cast(SessionRetrieveResponse, construct_type(type_=SessionRetrieveResponse, value=data))

    def delete(
        self,
        session_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SuccessResponse:
        """
        Deletes the browser session associated with the provided browser session ID.
        Requires a valid API key for authentication.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return self._delete(
            f"/v1/sessions/{session_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SuccessResponse,
        )

    def copy(
        self,
        session_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionCopyResponse:
        """
        Copies the currently selected text to the clipboard

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return self._post(
            f"/v1/sessions/{session_id}/copy",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionCopyResponse,
        )

    def drag_and_drop(
        self,
        session_id: str,
        *,
        end_x: int,
        end_y: int,
        start_x: int,
        start_y: int,
        button: Literal["left", "middle", "right"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionDragAndDropResponse:
        """
        Performs a drag and drop operation from start coordinates to end coordinates

        Args:
          end_x: Ending X coordinate

          end_y: Ending Y coordinate

          start_x: Starting X coordinate

          start_y: Starting Y coordinate

          button: Mouse button to use

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return self._post(
            f"/v1/sessions/{session_id}/drag-and-drop",
            body=maybe_transform(
                {
                    "end_x": end_x,
                    "end_y": end_y,
                    "start_x": start_x,
                    "start_y": start_y,
                    "button": button,
                },
                session_drag_and_drop_params.SessionDragAndDropParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionDragAndDropResponse,
        )

    def goto(
        self,
        session_id: str,
        *,
        url: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionGotoResponse:
        """
        Navigates the browser session to the specified URL

        Args:
          url: The URL to navigate to

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return self._post(
            f"/v1/sessions/{session_id}/goto",
            body=maybe_transform({"url": url}, session_goto_params.SessionGotoParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionGotoResponse,
        )

    def list_pages(
        self,
        session_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionListPagesResponse:
        """
        Retrieves a list of pages associated with a specific browser session.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return self._get(
            f"/v1/sessions/{session_id}/pages",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionListPagesResponse,
        )

    def paste(
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
    ) -> SessionPasteResponse:
        """
        Pastes text at the current cursor position

        Args:
          text: Text to paste

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return self._post(
            f"/v1/sessions/{session_id}/paste",
            body=maybe_transform({"text": text}, session_paste_params.SessionPasteParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionPasteResponse,
        )

    def retrieve_downloads(
        self,
        session_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionRetrieveDownloadsResponse:
        """Retrieves metadata of files downloaded during a browser session.

        Requires a
        valid API key for authentication.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return self._get(
            f"/v1/sessions/{session_id}/downloads",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionRetrieveDownloadsResponse,
        )

    def retrieve_screenshot(
        self,
        session_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BinaryAPIResponse:
        """
        Takes a screenshot of the current browser session and returns it as an image.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        extra_headers = {"Accept": "image/png", **(extra_headers or {})}
        return self._get(
            f"/v1/sessions/{session_id}/screenshot",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BinaryAPIResponse,
        )

    def scroll(
        self,
        session_id: str,
        *,
        delta_y: int,
        x: int,
        y: int,
        delta_x: int | Omit = omit,
        steps: int | Omit = omit,
        use_os: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionScrollResponse:
        """
        Performs a scroll action at the specified coordinates

        Args:
          delta_y: Vertical scroll amount (positive is down, negative is up)

          x: X coordinate

          y: Y coordinate

          delta_x: Horizontal scroll amount (positive is right, negative is left)

          steps: Number of steps to break the scroll into for smoother scrolling

          use_os: Whether to use the OS scroll or the Playwright scroll

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return self._post(
            f"/v1/sessions/{session_id}/scroll",
            body=maybe_transform(
                {
                    "delta_y": delta_y,
                    "x": x,
                    "y": y,
                    "delta_x": delta_x,
                    "steps": steps,
                    "use_os": use_os,
                },
                session_scroll_params.SessionScrollParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionScrollResponse,
        )

    def upload_file(
        self,
        session_id: str,
        *,
        file: FileTypes,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionUploadFileResponse:
        """
        Upload files directly to a browser session for use with web forms and file
        inputs.

        Files are saved to the session's uploads directory and can be referenced in CDP
        commands.

        Args:
          file: File to upload to the browser session

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        body = deepcopy_minimal({"file": file})
        files = extract_files(cast(Mapping[str, object], body), paths=[["file"]])
        # It should be noted that the actual Content-Type header that will be
        # sent to the server will contain a `boundary` parameter, e.g.
        # multipart/form-data; boundary=---abc--
        extra_headers = {"Content-Type": "multipart/form-data", **(extra_headers or {})}
        return self._post(
            f"/v1/sessions/{session_id}/uploads",
            body=maybe_transform(body, session_upload_file_params.SessionUploadFileParams),
            files=files,
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionUploadFileResponse,
        )


class AsyncSessionsResource(AsyncAPIResource):
    @cached_property
    def all(self) -> AsyncAllResource:
        return AsyncAllResource(self._client)

    @cached_property
    def recordings(self) -> AsyncRecordingsResource:
        return AsyncRecordingsResource(self._client)

    @cached_property
    def mouse(self) -> AsyncMouseResource:
        return AsyncMouseResource(self._client)

    @cached_property
    def keyboard(self) -> AsyncKeyboardResource:
        return AsyncKeyboardResource(self._client)

    @cached_property
    def clipboard(self) -> AsyncClipboardResource:
        return AsyncClipboardResource(self._client)
    @cached_property
    def agent(self) -> AsyncAgentResource:
        return AsyncAgentResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncSessionsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#accessing-raw-response-data-eg-headers
        """
        return AsyncSessionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSessionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#with_streaming_response
        """
        return AsyncSessionsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        browser: session_create_params.Browser | Omit = omit,
        integrations: Iterable[session_create_params.Integration] | Omit = omit,
        session: session_create_params.Session | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionCreateResponse:
        """
        Allocates a new browser session for the user, with optional configurations for
        ad-blocking, captcha solving, proxy usage, and idle timeout.

        Args:
          browser: Browser-specific configurations.

          integrations: Array of integrations to load in the browser session. Integrations must be
              previously created using the Integrations API.

          session: Session-related configurations.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/sessions",
            body=await async_maybe_transform(
                {
                    "browser": browser,
                    "integrations": integrations,
                    "session": session,
                },
                session_create_params.SessionCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionCreateResponse,
        )

    async def retrieve(
        self,
        session_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionRetrieveResponse:
        """
        Retrieves detailed information about a specific browser session.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        
        # Get raw response to unwrap the data field
        raw_response = cast(dict[str, object], await self._get(
            f"/v1/sessions/{session_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,  # Get as raw object (dict) to unwrap
        ))
        
        # Unwrap data field if API returns { data: {...} }
        data: object = raw_response.get("data", raw_response)
        
        # Construct the response type from the unwrapped data
        return cast(SessionRetrieveResponse, construct_type(type_=SessionRetrieveResponse, value=data))

    async def delete(
        self,
        session_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SuccessResponse:
        """
        Deletes the browser session associated with the provided browser session ID.
        Requires a valid API key for authentication.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return await self._delete(
            f"/v1/sessions/{session_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SuccessResponse,
        )

    async def copy(
        self,
        session_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionCopyResponse:
        """
        Copies the currently selected text to the clipboard

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return await self._post(
            f"/v1/sessions/{session_id}/copy",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionCopyResponse,
        )

    async def drag_and_drop(
        self,
        session_id: str,
        *,
        end_x: int,
        end_y: int,
        start_x: int,
        start_y: int,
        button: Literal["left", "middle", "right"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionDragAndDropResponse:
        """
        Performs a drag and drop operation from start coordinates to end coordinates

        Args:
          end_x: Ending X coordinate

          end_y: Ending Y coordinate

          start_x: Starting X coordinate

          start_y: Starting Y coordinate

          button: Mouse button to use

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return await self._post(
            f"/v1/sessions/{session_id}/drag-and-drop",
            body=await async_maybe_transform(
                {
                    "end_x": end_x,
                    "end_y": end_y,
                    "start_x": start_x,
                    "start_y": start_y,
                    "button": button,
                },
                session_drag_and_drop_params.SessionDragAndDropParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionDragAndDropResponse,
        )

    async def goto(
        self,
        session_id: str,
        *,
        url: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionGotoResponse:
        """
        Navigates the browser session to the specified URL

        Args:
          url: The URL to navigate to

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return await self._post(
            f"/v1/sessions/{session_id}/goto",
            body=await async_maybe_transform({"url": url}, session_goto_params.SessionGotoParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionGotoResponse,
        )

    async def list_pages(
        self,
        session_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionListPagesResponse:
        """
        Retrieves a list of pages associated with a specific browser session.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return await self._get(
            f"/v1/sessions/{session_id}/pages",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionListPagesResponse,
        )

    async def paste(
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
    ) -> SessionPasteResponse:
        """
        Pastes text at the current cursor position

        Args:
          text: Text to paste

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return await self._post(
            f"/v1/sessions/{session_id}/paste",
            body=await async_maybe_transform({"text": text}, session_paste_params.SessionPasteParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionPasteResponse,
        )

    async def retrieve_downloads(
        self,
        session_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionRetrieveDownloadsResponse:
        """Retrieves metadata of files downloaded during a browser session.

        Requires a
        valid API key for authentication.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return await self._get(
            f"/v1/sessions/{session_id}/downloads",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionRetrieveDownloadsResponse,
        )

    async def retrieve_screenshot(
        self,
        session_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncBinaryAPIResponse:
        """
        Takes a screenshot of the current browser session and returns it as an image.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        extra_headers = {"Accept": "image/png", **(extra_headers or {})}
        return await self._get(
            f"/v1/sessions/{session_id}/screenshot",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AsyncBinaryAPIResponse,
        )

    async def scroll(
        self,
        session_id: str,
        *,
        delta_y: int,
        x: int,
        y: int,
        delta_x: int | Omit = omit,
        steps: int | Omit = omit,
        use_os: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionScrollResponse:
        """
        Performs a scroll action at the specified coordinates

        Args:
          delta_y: Vertical scroll amount (positive is down, negative is up)

          x: X coordinate

          y: Y coordinate

          delta_x: Horizontal scroll amount (positive is right, negative is left)

          steps: Number of steps to break the scroll into for smoother scrolling

          use_os: Whether to use the OS scroll or the Playwright scroll

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return await self._post(
            f"/v1/sessions/{session_id}/scroll",
            body=await async_maybe_transform(
                {
                    "delta_y": delta_y,
                    "x": x,
                    "y": y,
                    "delta_x": delta_x,
                    "steps": steps,
                    "use_os": use_os,
                },
                session_scroll_params.SessionScrollParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionScrollResponse,
        )

    async def upload_file(
        self,
        session_id: str,
        *,
        file: FileTypes,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SessionUploadFileResponse:
        """
        Upload files directly to a browser session for use with web forms and file
        inputs.

        Files are saved to the session's uploads directory and can be referenced in CDP
        commands.

        Args:
          file: File to upload to the browser session

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        body = deepcopy_minimal({"file": file})
        files = extract_files(cast(Mapping[str, object], body), paths=[["file"]])
        # It should be noted that the actual Content-Type header that will be
        # sent to the server will contain a `boundary` parameter, e.g.
        # multipart/form-data; boundary=---abc--
        extra_headers = {"Content-Type": "multipart/form-data", **(extra_headers or {})}
        return await self._post(
            f"/v1/sessions/{session_id}/uploads",
            body=await async_maybe_transform(body, session_upload_file_params.SessionUploadFileParams),
            files=files,
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionUploadFileResponse,
        )


class SessionsResourceWithRawResponse:
    def __init__(self, sessions: SessionsResource) -> None:
        self._sessions = sessions

        self.create = to_raw_response_wrapper(
            sessions.create,
        )
        self.retrieve = to_raw_response_wrapper(
            sessions.retrieve,
        )
        self.delete = to_raw_response_wrapper(
            sessions.delete,
        )
        self.copy = to_raw_response_wrapper(
            sessions.copy,
        )
        self.drag_and_drop = to_raw_response_wrapper(
            sessions.drag_and_drop,
        )
        self.goto = to_raw_response_wrapper(
            sessions.goto,
        )
        self.list_pages = to_raw_response_wrapper(
            sessions.list_pages,
        )
        self.paste = to_raw_response_wrapper(
            sessions.paste,
        )
        self.retrieve_downloads = to_raw_response_wrapper(
            sessions.retrieve_downloads,
        )
        self.retrieve_screenshot = to_custom_raw_response_wrapper(
            sessions.retrieve_screenshot,
            BinaryAPIResponse,
        )
        self.scroll = to_raw_response_wrapper(
            sessions.scroll,
        )
        self.upload_file = to_raw_response_wrapper(
            sessions.upload_file,
        )

    @cached_property
    def all(self) -> AllResourceWithRawResponse:
        return AllResourceWithRawResponse(self._sessions.all)

    @cached_property
    def recordings(self) -> RecordingsResourceWithRawResponse:
        return RecordingsResourceWithRawResponse(self._sessions.recordings)

    @cached_property
    def mouse(self) -> MouseResourceWithRawResponse:
        return MouseResourceWithRawResponse(self._sessions.mouse)

    @cached_property
    def keyboard(self) -> KeyboardResourceWithRawResponse:
        return KeyboardResourceWithRawResponse(self._sessions.keyboard)

    @cached_property
    def clipboard(self) -> ClipboardResourceWithRawResponse:
        return ClipboardResourceWithRawResponse(self._sessions.clipboard)

    @cached_property
    def agent(self) -> AgentResourceWithRawResponse:
        return AgentResourceWithRawResponse(self._sessions.agent)


class AsyncSessionsResourceWithRawResponse:
    def __init__(self, sessions: AsyncSessionsResource) -> None:
        self._sessions = sessions

        self.create = async_to_raw_response_wrapper(
            sessions.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            sessions.retrieve,
        )
        self.delete = async_to_raw_response_wrapper(
            sessions.delete,
        )
        self.copy = async_to_raw_response_wrapper(
            sessions.copy,
        )
        self.drag_and_drop = async_to_raw_response_wrapper(
            sessions.drag_and_drop,
        )
        self.goto = async_to_raw_response_wrapper(
            sessions.goto,
        )
        self.list_pages = async_to_raw_response_wrapper(
            sessions.list_pages,
        )
        self.paste = async_to_raw_response_wrapper(
            sessions.paste,
        )
        self.retrieve_downloads = async_to_raw_response_wrapper(
            sessions.retrieve_downloads,
        )
        self.retrieve_screenshot = async_to_custom_raw_response_wrapper(
            sessions.retrieve_screenshot,
            AsyncBinaryAPIResponse,
        )
        self.scroll = async_to_raw_response_wrapper(
            sessions.scroll,
        )
        self.upload_file = async_to_raw_response_wrapper(
            sessions.upload_file,
        )

    @cached_property
    def all(self) -> AsyncAllResourceWithRawResponse:
        return AsyncAllResourceWithRawResponse(self._sessions.all)

    @cached_property
    def recordings(self) -> AsyncRecordingsResourceWithRawResponse:
        return AsyncRecordingsResourceWithRawResponse(self._sessions.recordings)

    @cached_property
    def mouse(self) -> AsyncMouseResourceWithRawResponse:
        return AsyncMouseResourceWithRawResponse(self._sessions.mouse)

    @cached_property
    def keyboard(self) -> AsyncKeyboardResourceWithRawResponse:
        return AsyncKeyboardResourceWithRawResponse(self._sessions.keyboard)

    @cached_property
    def clipboard(self) -> AsyncClipboardResourceWithRawResponse:
        return AsyncClipboardResourceWithRawResponse(self._sessions.clipboard)

    @cached_property
    def agent(self) -> AsyncAgentResourceWithRawResponse:
        return AsyncAgentResourceWithRawResponse(self._sessions.agent)

class SessionsResourceWithStreamingResponse:
    def __init__(self, sessions: SessionsResource) -> None:
        self._sessions = sessions

        self.create = to_streamed_response_wrapper(
            sessions.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            sessions.retrieve,
        )
        self.delete = to_streamed_response_wrapper(
            sessions.delete,
        )
        self.copy = to_streamed_response_wrapper(
            sessions.copy,
        )
        self.drag_and_drop = to_streamed_response_wrapper(
            sessions.drag_and_drop,
        )
        self.goto = to_streamed_response_wrapper(
            sessions.goto,
        )
        self.list_pages = to_streamed_response_wrapper(
            sessions.list_pages,
        )
        self.paste = to_streamed_response_wrapper(
            sessions.paste,
        )
        self.retrieve_downloads = to_streamed_response_wrapper(
            sessions.retrieve_downloads,
        )
        self.retrieve_screenshot = to_custom_streamed_response_wrapper(
            sessions.retrieve_screenshot,
            StreamedBinaryAPIResponse,
        )
        self.scroll = to_streamed_response_wrapper(
            sessions.scroll,
        )
        self.upload_file = to_streamed_response_wrapper(
            sessions.upload_file,
        )

    @cached_property
    def all(self) -> AllResourceWithStreamingResponse:
        return AllResourceWithStreamingResponse(self._sessions.all)

    @cached_property
    def recordings(self) -> RecordingsResourceWithStreamingResponse:
        return RecordingsResourceWithStreamingResponse(self._sessions.recordings)

    @cached_property
    def mouse(self) -> MouseResourceWithStreamingResponse:
        return MouseResourceWithStreamingResponse(self._sessions.mouse)

    @cached_property
    def keyboard(self) -> KeyboardResourceWithStreamingResponse:
        return KeyboardResourceWithStreamingResponse(self._sessions.keyboard)

    @cached_property
    def clipboard(self) -> ClipboardResourceWithStreamingResponse:
        return ClipboardResourceWithStreamingResponse(self._sessions.clipboard)

    @cached_property
    def agent(self) -> AgentResourceWithStreamingResponse:
        return AgentResourceWithStreamingResponse(self._sessions.agent)

class AsyncSessionsResourceWithStreamingResponse:
    def __init__(self, sessions: AsyncSessionsResource) -> None:
        self._sessions = sessions

        self.create = async_to_streamed_response_wrapper(
            sessions.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            sessions.retrieve,
        )
        self.delete = async_to_streamed_response_wrapper(
            sessions.delete,
        )
        self.copy = async_to_streamed_response_wrapper(
            sessions.copy,
        )
        self.drag_and_drop = async_to_streamed_response_wrapper(
            sessions.drag_and_drop,
        )
        self.goto = async_to_streamed_response_wrapper(
            sessions.goto,
        )
        self.list_pages = async_to_streamed_response_wrapper(
            sessions.list_pages,
        )
        self.paste = async_to_streamed_response_wrapper(
            sessions.paste,
        )
        self.retrieve_downloads = async_to_streamed_response_wrapper(
            sessions.retrieve_downloads,
        )
        self.retrieve_screenshot = async_to_custom_streamed_response_wrapper(
            sessions.retrieve_screenshot,
            AsyncStreamedBinaryAPIResponse,
        )
        self.scroll = async_to_streamed_response_wrapper(
            sessions.scroll,
        )
        self.upload_file = async_to_streamed_response_wrapper(
            sessions.upload_file,
        )

    @cached_property
    def all(self) -> AsyncAllResourceWithStreamingResponse:
        return AsyncAllResourceWithStreamingResponse(self._sessions.all)

    @cached_property
    def recordings(self) -> AsyncRecordingsResourceWithStreamingResponse:
        return AsyncRecordingsResourceWithStreamingResponse(self._sessions.recordings)

    @cached_property
    def mouse(self) -> AsyncMouseResourceWithStreamingResponse:
        return AsyncMouseResourceWithStreamingResponse(self._sessions.mouse)

    @cached_property
    def keyboard(self) -> AsyncKeyboardResourceWithStreamingResponse:
        return AsyncKeyboardResourceWithStreamingResponse(self._sessions.keyboard)

    @cached_property
    def clipboard(self) -> AsyncClipboardResourceWithStreamingResponse:
        return AsyncClipboardResourceWithStreamingResponse(self._sessions.clipboard)

    @cached_property
    def agent(self) -> AsyncAgentResourceWithStreamingResponse:
        return AsyncAgentResourceWithStreamingResponse(self._sessions.agent)