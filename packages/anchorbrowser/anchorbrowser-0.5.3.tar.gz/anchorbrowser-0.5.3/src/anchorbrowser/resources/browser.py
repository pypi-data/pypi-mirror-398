from __future__ import annotations

from contextlib import _GeneratorContextManager, _AsyncGeneratorContextManager

from playwright.sync_api import Browser
from playwright.async_api import Browser as AsyncBrowser

from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..lib.browser import (
    get_playwright_chromium_from_cdp_url,
    get_async_playwright_chromium_from_cdp_url,
)

__all__ = ["BrowserResource", "AsyncBrowserResource"]


class BrowserResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> BrowserResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#accessing-raw-response-data-eg-headers
        """
        return BrowserResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> BrowserResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#with_streaming_response
        """
        return BrowserResourceWithStreamingResponse(self)

    def connect(self, session_id: str) -> _GeneratorContextManager[Browser]:
        """Connect to a browser session.

        Args:
            session_id (str): The ID of the session to connect to.

        Returns:
            BrowserContext: a context manager that can be used to interact with the browser(playwright)
        """
        return get_playwright_chromium_from_cdp_url(str(self._client.base_url), session_id, self._client.api_key)

    def create(self) -> _GeneratorContextManager[Browser]:
        session = self._client.sessions.create()
        if not session.data or not session.data.id:
            raise ValueError("Failed to create session")
        return get_playwright_chromium_from_cdp_url(str(self._client.base_url), session.data.id, self._client.api_key)


class AsyncBrowserResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncBrowserResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#accessing-raw-response-data-eg-headers
        """
        return AsyncBrowserResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncBrowserResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#with_streaming_response
        """
        return AsyncBrowserResourceWithStreamingResponse(self)

    async def connect(self, session_id: str) -> _AsyncGeneratorContextManager[AsyncBrowser]:
        """Connect to a browser session.

        Args:
            session_id (str): The ID of the session to connect to.

        Returns:
            BrowserContext: a context manager that can be used to interact with the browser(playwright)
        """
        return get_async_playwright_chromium_from_cdp_url(str(self._client.base_url), session_id, self._client.api_key)

    async def create(self) -> _AsyncGeneratorContextManager[AsyncBrowser]:
        """Create a new browser session.

        Returns:
            BrowserContext: a context manager that can be used to interact with the browser(playwright)
        """
        session = await self._client.sessions.create()
        if not session.data or not session.data.id:
            raise ValueError("Failed to create session")
        return get_async_playwright_chromium_from_cdp_url(
            str(self._client.base_url), session.data.id, self._client.api_key
        )


class BrowserResourceWithRawResponse:
    def __init__(self, browser: BrowserResource) -> None:
        self._browser = browser

        self.connect = to_raw_response_wrapper(
            browser.connect,
        )
        self.create = to_raw_response_wrapper(
            browser.create,
        )


class AsyncBrowserResourceWithRawResponse:
    def __init__(self, browser: AsyncBrowserResource) -> None:
        self._browser = browser

        self.connect = async_to_raw_response_wrapper(
            browser.connect,
        )
        self.create = async_to_raw_response_wrapper(
            browser.create,
        )


class BrowserResourceWithStreamingResponse:
    def __init__(self, browser: BrowserResource) -> None:
        self._browser = browser

        self.connect = to_streamed_response_wrapper(
            browser.connect,
        )
        self.create = to_streamed_response_wrapper(
            browser.create,
        )


class AsyncBrowserResourceWithStreamingResponse:
    def __init__(self, browser: AsyncBrowserResource) -> None:
        self._browser = browser

        self.connect = async_to_streamed_response_wrapper(
            browser.connect,
        )
        self.create = async_to_streamed_response_wrapper(
            browser.create,
        )
