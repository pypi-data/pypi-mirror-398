from typing import TYPE_CHECKING, Any, Dict, Callable, Optional, TypedDict
from contextlib import contextmanager, asynccontextmanager, _GeneratorContextManager, _AsyncGeneratorContextManager

from pydantic import BaseModel
from playwright.sync_api import Page, Worker, Browser, BrowserContext
from playwright.async_api import (
    Page as AsyncPage,
    Worker as AsyncWorker,
    Browser as AsyncBrowser,
    BrowserContext as AsyncBrowserContext,
)

if TYPE_CHECKING:
    from collections import Generator, AsyncGenerator


@contextmanager
def get_playwright_chromium_from_cdp_url(
    api_base_url: str, session_id: str, api_key: str
) -> "Generator[Browser, Any, None]":
    from playwright.sync_api import sync_playwright

    browser = None
    playwright = sync_playwright().start()
    try:
        browser = playwright.chromium.connect_over_cdp(get_cdp_url(api_base_url, session_id, api_key))
        yield browser
    finally:
        if browser:
            browser.close()
        playwright.stop()


@asynccontextmanager
async def get_async_playwright_chromium_from_cdp_url(
    api_base_url: str, session_id: str, api_key: str
) -> "AsyncGenerator[AsyncBrowser, None]":
    from playwright.async_api import async_playwright

    browser = None
    playwright = await async_playwright().start()
    try:
        browser = await playwright.chromium.connect_over_cdp(get_cdp_url(api_base_url, session_id, api_key))
        yield browser
    finally:
        if browser:
            await browser.close()
        await playwright.stop()


def get_cdp_url(api_base_url: str, session_id: str, api_key: str) -> str:
    return f"{api_base_url.replace('https://', 'wss://').replace('api.', 'connect.')}?apiKey={api_key}&sessionId={session_id}"


def get_agent_ws_url(api_base_url: str, session_id: str) -> str:
    return f"{api_base_url.replace('https://', 'wss://')}/ws?sessionId={session_id}"


def get_ai_service_worker(browser_context: "BrowserContext") -> Optional["Worker"]:
    return next(
        (
            sw
            for sw in browser_context.service_workers
            if "chrome-extension://bppehibnhionalpjigdjdilknbljaeai/background.js" in sw.url
        ),
        None,
    )


async def get_ai_service_worker_async(browser_context: "AsyncBrowserContext") -> Optional["AsyncWorker"]:
    return next(
        (
            sw
            for sw in browser_context.service_workers
            if "chrome-extension://bppehibnhionalpjigdjdilknbljaeai/background.js" in sw.url
        ),
        None,
    )


class BrowserSetup(BaseModel):
    session_id: str
    base_url: str
    api_key: str
    _browser: Optional[Browser] = None
    _async_browser: Optional[AsyncBrowser] = None
    _context_manager: Optional[_GeneratorContextManager[Browser]] = None
    _async_context_manager: Optional[_AsyncGeneratorContextManager[AsyncBrowser]] = None

    async def __aenter__(self) -> "BrowserSetup":
        self._async_context_manager = get_async_playwright_chromium_from_cdp_url(
            self.base_url,
            self.session_id,
            self.api_key,
        )
        self._async_browser = await self._async_context_manager.__aenter__()
        return self

    def __enter__(self) -> "BrowserSetup":
        self._context_manager = get_playwright_chromium_from_cdp_url(
            self.base_url,
            self.session_id,
            self.api_key,
        )
        self._browser = self._context_manager.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Optional[bool]:
        if self._context_manager:
            return self._context_manager.__exit__(exc_type, exc_val, exc_tb)
        return None

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Optional[bool]:
        if self._async_context_manager:
            return await self._async_context_manager.__aexit__(exc_type, exc_val, exc_tb)
        return None

    @property
    def browser_generator(self) -> _GeneratorContextManager[Browser]:
        return get_playwright_chromium_from_cdp_url(
            self.base_url,
            self.session_id,
            self.api_key,
        )

    @property
    def async_browser_generator(self) -> _AsyncGeneratorContextManager[AsyncBrowser]:
        return get_async_playwright_chromium_from_cdp_url(
            self.base_url,
            self.session_id,
            self.api_key,
        )

    @property
    def browser(self) -> Browser:
        if self._browser is None:
            raise RuntimeError("BrowserSetup must be used as a context manager")
        return self._browser

    @property
    async def async_browser(self) -> AsyncBrowser:
        if self._async_browser is None:
            raise RuntimeError("BrowserSetup must be used as a context manager")
        return self._async_browser

    @property
    def context(self) -> BrowserContext:
        return self.browser.contexts[0]

    @property
    async def async_context(self) -> AsyncBrowserContext:
        return (await self.async_browser).contexts[0]

    @property
    def page(self) -> Page:
        return self.context.pages[0]

    @property
    async def async_page(self) -> AsyncPage:
        return (await self.async_context).pages[0]

    @property
    def ai(self) -> Worker:
        ai_service_worker = get_ai_service_worker(self.context)
        if not ai_service_worker:
            raise ValueError("AI service worker not found")
        return ai_service_worker

    @property
    async def async_ai(self) -> AsyncWorker:
        ai_service_worker = await get_ai_service_worker_async(await self.async_context)
        if not ai_service_worker:
            raise ValueError("AI service worker not found")
        return ai_service_worker


class AgentTaskParams(TypedDict, total=False):
    url: Optional[str]
    output_schema: Optional[Dict[str, Any]]
    on_agent_step: Optional[Callable[[str], None]]
    agent: Optional[str]
    highlight_elements: Optional[bool]
    model: Optional[str]
    provider: Optional[str]
    detect_elements: Optional[bool]
    extended_system_message: Optional[str]
    human_intervention: Optional[bool]
    max_steps: Optional[int]
    secret_values: Optional[Dict[str, Any]]
    directly_open_url: Optional[bool]


class BrowserTaskResponse(TypedDict):
    session_id: str
    task_result_task: Any
    playwright_browser: Any
