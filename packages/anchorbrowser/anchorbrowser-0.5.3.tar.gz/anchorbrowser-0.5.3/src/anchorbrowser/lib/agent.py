import json
import asyncio
import threading
from typing import Any, Dict, Callable, Optional, TypedDict
from asyncio import Future

from ..lib.browser import BrowserSetup, get_agent_ws_url


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


def create_task_payload(
    prompt: str,
    output_schema: Optional[Dict[str, Any]] = None,
    agent: Optional[str] = None,
    highlight_elements: Optional[bool] = None,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    detect_elements: Optional[bool] = None,
    extended_system_message: Optional[str] = None,
    human_intervention: Optional[bool] = None,
    max_steps: Optional[int] = None,
    secret_values: Optional[Dict[str, Any]] = None,
    directly_open_url: Optional[bool] = None,
) -> str:
    if not prompt or prompt.strip() == "":
        raise ValueError("Prompt cannot be empty")

    payload: Dict[str, Any] = {
        "prompt": prompt,
        "output_schema": output_schema,
    }
    
    if agent is not None:
        payload["agent"] = agent
    if highlight_elements is not None:
        payload["highlight_elements"] = highlight_elements
    if model is not None:
        payload["model"] = model
    if provider is not None:
        payload["provider"] = provider
    if detect_elements is not None:
        payload["detect_elements"] = detect_elements
    if extended_system_message is not None:
        payload["extended_system_message"] = extended_system_message
    if human_intervention is not None:
        payload["human_intervention"] = human_intervention
    if max_steps is not None:
        payload["max_steps"] = max_steps
    if secret_values is not None:
        payload["secret_values"] = secret_values
    if directly_open_url is not None:
        payload["directly_open_url"] = directly_open_url
    return json.dumps(payload)


def on_agent_step_sync(on_agent_step: Callable[[str], None], browser_setup: BrowserSetup) -> Future[None]:
    import websockets

    async def websocket_listener() -> None:
        ws_url = get_agent_ws_url(browser_setup.base_url, browser_setup.session_id)
        try:
            async with websockets.connect(ws_url) as ws:
                async for ws_msg in ws:
                    on_agent_step(str(ws_msg))
        except Exception as e:
            future.set_exception(e)

    def run_in_thread() -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(websocket_listener())
        finally:
            loop.close()

    # Create a future to track the task
    future = Future[None]()
    try:
        thread = threading.Thread(target=lambda: future.set_result(run_in_thread()))
        thread.daemon = True
        thread.start()
    except Exception:
        pass

    return future


def on_agent_step_async(on_agent_step: Callable[[str], None], browser_setup: BrowserSetup) -> None:
    import websockets

    async def websocket_listener() -> None:
        ws_url = get_agent_ws_url(browser_setup.base_url, browser_setup.session_id)
        async with websockets.connect(ws_url) as ws:
            async for ws_msg in ws:
                on_agent_step(str(ws_msg))

    asyncio.create_task(websocket_listener())
