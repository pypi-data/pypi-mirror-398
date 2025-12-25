from __future__ import annotations

from typing import Optional

from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..lib.agent import on_agent_step_sync, create_task_payload, on_agent_step_async
from ..lib.browser import (
    BrowserSetup,
    AgentTaskParams,
    BrowserTaskResponse,
)
from ..types.session_create_params import Session

__all__ = ["AgentResource", "AsyncAgentResource"]


class AgentResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AgentResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#accessing-raw-response-data-eg-headers
        """
        return AgentResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AgentResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#with_streaming_response
        """
        return AgentResourceWithStreamingResponse(self)

    def task(
        self,
        prompt: str,
        *,
        session_options: Optional[Session] = None,
        task_options: Optional[AgentTaskParams] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """Execute an AI agent task within a browser session.

        Creates a new browser session and executes the given prompt as an AI agent task.
        The agent can optionally navigate to a specific URL and use a structured output schema.

        Args:
            prompt (str): The task prompt/instruction for the AI agent to execute.
            session_options (Optional[Session], optional): Configuration options for the
                browser session. Defaults to None, which creates a session with default settings.
            task_options (Optional[AgentTaskParams], optional): Additional task configuration

        Returns:
            str: The result of the AI agent task execution.
        """
        if session_id:
            retrieved_session = self._client.sessions.retrieve(session_id)
            if not retrieved_session or not retrieved_session or not retrieved_session.session_id:
                raise ValueError("Failed to retrieve session: No session ID returned")
            actual_session_id = retrieved_session.session_id
        else:
            created_session = self._client.sessions.create(session=session_options or {})
            if not created_session or not created_session.data or not created_session.data.id:
                raise ValueError("Failed to create session: No session ID returned")
            actual_session_id = created_session.data.id

        with BrowserSetup(
            session_id=actual_session_id,
            base_url=str(self._client.base_url),
            api_key=self._client.api_key,
        ) as browser_setup:
            output_schema = None
            url = None
            agent = None
            highlight_elements = None
            model = None
            provider = None
            detect_elements = None
            extended_system_message = None
            human_intervention = None
            max_steps = None
            secret_values = None
            directly_open_url = None
            if task_options:
                output_schema = task_options.get("output_schema")
                url = task_options.get("url")
                agent = task_options.get("agent")
                highlight_elements = task_options.get("highlight_elements")
                model = task_options.get("model")
                provider = task_options.get("provider")
                detect_elements = task_options.get("detect_elements")
                extended_system_message = task_options.get("extended_system_message")
                human_intervention = task_options.get("human_intervention")
                max_steps = task_options.get("max_steps")
                secret_values = task_options.get("secret_values")
                directly_open_url = task_options.get("directly_open_url")
                if url:
                    browser_setup.page.goto(url)
                on_agent_step = task_options.get("on_agent_step")
                if on_agent_step:
                    on_agent_step_sync(on_agent_step, browser_setup)
            task_payload = create_task_payload(
                prompt,
                output_schema=output_schema,
                agent=agent,
                highlight_elements=highlight_elements,
                model=model,
                provider=provider,
                detect_elements=detect_elements,
                extended_system_message=extended_system_message,
                human_intervention=human_intervention,
                max_steps=max_steps,
                secret_values=secret_values,
                directly_open_url=directly_open_url,
            )
            task_result = str(browser_setup.ai.evaluate(task_payload))
            return task_result

    def browser_task(
        self,
        prompt: str,
        *,
        session_options: Optional[Session] = None,
        task_options: Optional[AgentTaskParams] = None,
    ) -> BrowserTaskResponse:
        """Execute an AI agent task and return a browser task response with session control.

        Creates a new browser session, executes the given prompt as an AI agent task \n
        returns a object that includes the session ID, task result, and browser instance for continued interaction by the caller. \n
        This method differs from `task()` by returning control of the browser session to the caller rather than automatically closing it after task completion. \n
        Args:
            prompt (str): The task prompt/instruction for the AI agent to execute. \n
            session_options (Optional[Session], optional): Configuration options for the browser session. Defaults to None, which creates a session with default settings. \n
            task_options (Optional[AgentTaskParams], optional): Additional task configuration including: \n
        - output_schema: Schema for structured output formatting
        - url: URL to navigate to before executing the task
        - on_agent_step: Callback function for agent step events
                Defaults to None.

        Returns:
            Response object containing:
                - session_id: The ID of the created browser session
                - task_result_task: The result of the AI agent task execution
                - playwright_browser: Browser instance for continued interaction
        """
        session = self._client.sessions.create(session=session_options or {})
        if not session.data or not session.data.id:
            raise ValueError("Failed to create session: No session ID returned")

        with BrowserSetup(
            session_id=session.data.id,
            base_url=str(self._client.base_url),
            api_key=self._client.api_key,
        ) as browser_setup:
            output_schema = None
            url = None
            agent = None
            highlight_elements = None
            model = None
            provider = None
            detect_elements = None
            extended_system_message = None
            human_intervention = None
            max_steps = None
            secret_values = None
            directly_open_url = None
            if task_options:
                output_schema = task_options.get("output_schema")
                url = task_options.get("url")
                agent = task_options.get("agent")
                highlight_elements = task_options.get("highlight_elements")
                model = task_options.get("model")
                provider = task_options.get("provider")
                detect_elements = task_options.get("detect_elements")
                extended_system_message = task_options.get("extended_system_message")
                human_intervention = task_options.get("human_intervention")
                max_steps = task_options.get("max_steps")
                secret_values = task_options.get("secret_values")
                directly_open_url = task_options.get("directly_open_url")
                if url:
                    browser_setup.page.goto(url)
                on_agent_step = task_options.get("on_agent_step")
                if on_agent_step:
                    on_agent_step_sync(on_agent_step, browser_setup)
            task_payload = create_task_payload(
                prompt,
                output_schema=output_schema,
                agent=agent,
                highlight_elements=highlight_elements,
                model=model,
                provider=provider,
                detect_elements=detect_elements,
                extended_system_message=extended_system_message,
                human_intervention=human_intervention,
                max_steps=max_steps,
                secret_values=secret_values,
                directly_open_url=directly_open_url,
            )
            task_result = str(browser_setup.ai.evaluate(task_payload))
            return BrowserTaskResponse(
                session_id=session.data.id,
                task_result_task=task_result,
                playwright_browser=browser_setup.browser_generator,
            )


class AsyncAgentResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncAgentResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#accessing-raw-response-data-eg-headers
        """
        return AsyncAgentResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncAgentResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/anchorbrowser/AnchorBrowser-SDK-Python#with_streaming_response
        """
        return AsyncAgentResourceWithStreamingResponse(self)

    async def task(
        self,
        prompt: str,
        *,
        session_options: Optional[Session] = None,
        task_options: Optional[AgentTaskParams] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """Execute an AI agent task within a browser session.

        Creates a new browser session and executes the given prompt as an AI agent task.
        The agent can optionally navigate to a specific URL and use a structured output schema.

        Args:
            prompt (str): The task prompt/instruction for the AI agent to execute.
            session_options (Optional[Session], optional): Configuration options for the
                browser session. Defaults to None, which creates a session with default settings.
            task_options (Optional[AgentTaskParams], optional): Additional task configuration

        Returns:
            str: The result of the AI agent task execution.
        """
        if session_id:
            retrieved_session = await self._client.sessions.retrieve(session_id)
            if not retrieved_session or not retrieved_session.session_id:
                raise ValueError("Failed to retrieve session: No session ID returned")
            actual_session_id = retrieved_session.session_id
        else:
            created_session = await self._client.sessions.create(session=session_options or {})
            if not created_session or not created_session.data or not created_session.data.id:
                raise ValueError("Failed to create session: No session ID returned")
            actual_session_id = created_session.data.id

        browser_setup = BrowserSetup(
            session_id=actual_session_id,
            base_url=str(self._client.base_url),
            api_key=self._client.api_key,
        )

        async with browser_setup:
            output_schema = None
            url = None
            agent = None
            highlight_elements = None
            model = None
            provider = None
            detect_elements = None
            extended_system_message = None
            human_intervention = None
            max_steps = None
            secret_values = None
            directly_open_url = None
            if task_options:
                output_schema = task_options.get("output_schema")
                url = task_options.get("url")
                agent = task_options.get("agent")
                highlight_elements = task_options.get("highlight_elements")
                model = task_options.get("model")
                provider = task_options.get("provider")
                detect_elements = task_options.get("detect_elements")
                extended_system_message = task_options.get("extended_system_message")
                human_intervention = task_options.get("human_intervention")
                max_steps = task_options.get("max_steps")
                secret_values = task_options.get("secret_values")
                directly_open_url = task_options.get("directly_open_url")
                if url:
                    await (await browser_setup.async_page).goto(url)
                on_agent_step = task_options.get("on_agent_step")
                if on_agent_step:
                    on_agent_step_async(on_agent_step, browser_setup)
            task_payload = create_task_payload(
                prompt,
                output_schema=output_schema,
                agent=agent,
                highlight_elements=highlight_elements,
                model=model,
                provider=provider,
                detect_elements=detect_elements,
                extended_system_message=extended_system_message,
                human_intervention=human_intervention,
                max_steps=max_steps,
                secret_values=secret_values,
                directly_open_url=directly_open_url,
            )
            task_result = await (await browser_setup.async_ai).evaluate(task_payload)
            return str(task_result)

    async def browser_task(
        self,
        prompt: str,
        *,
        session_options: Optional[Session] = None,
        task_options: Optional[AgentTaskParams] = None,
    ) -> BrowserTaskResponse:
        """Execute an AI agent task and return a browser task response with session control.

        Creates a new browser session, executes the given prompt as an AI agent task \n
        returns a object that includes the session ID, task result, and browser instance for continued interaction by the caller. \n
        This method differs from `task()` by returning control of the browser session to the caller rather than automatically closing it after task completion. \n
        Args:
            prompt (str): The task prompt/instruction for the AI agent to execute. \n
            session_options (Optional[Session], optional): Configuration options for the browser session. Defaults to None, which creates a session with default settings. \n
            task_options (Optional[AgentTaskParams], optional): Additional task configuration including: \n
        - output_schema: Schema for structured output formatting
        - url: URL to navigate to before executing the task
        - on_agent_step: Callback function for agent step events
                Defaults to None.

        Returns:
            Response object containing:
                - session_id: The ID of the created browser session
                - task_result_task: The result of the AI agent task execution
                - playwright_browser: Browser instance for continued interaction
        """
        session = await self._client.sessions.create(session=session_options or {})
        if not session.data or not session.data.id:
            raise ValueError("Failed to create session: No session ID returned")

        async with BrowserSetup(
            session_id=session.data.id,
            base_url=str(self._client.base_url),
            api_key=self._client.api_key,
        ) as browser_setup:
            output_schema = None
            url = None
            agent = None
            highlight_elements = None
            model = None
            provider = None
            detect_elements = None
            extended_system_message = None
            human_intervention = None
            max_steps = None
            secret_values = None
            directly_open_url = None
            if task_options:
                output_schema = task_options.get("output_schema")
                url = task_options.get("url")
                agent = task_options.get("agent")
                highlight_elements = task_options.get("highlight_elements")
                model = task_options.get("model")
                provider = task_options.get("provider")
                detect_elements = task_options.get("detect_elements")
                extended_system_message = task_options.get("extended_system_message")
                human_intervention = task_options.get("human_intervention")
                max_steps = task_options.get("max_steps")
                secret_values = task_options.get("secret_values")
                directly_open_url = task_options.get("directly_open_url")
                if url:
                    await (await browser_setup.async_page).goto(url)
                on_agent_step = task_options.get("on_agent_step")
                if on_agent_step:
                    on_agent_step_async(on_agent_step, browser_setup)
            task_payload = create_task_payload(
                prompt,
                output_schema=output_schema,
                agent=agent,
                highlight_elements=highlight_elements,
                model=model,
                provider=provider,
                detect_elements=detect_elements,
                extended_system_message=extended_system_message,
                human_intervention=human_intervention,
                max_steps=max_steps,
                secret_values=secret_values,
                directly_open_url=directly_open_url,
            )
            task_result = await (await browser_setup.async_ai).evaluate(task_payload)
            return BrowserTaskResponse(
                session_id=session.data.id,
                task_result_task=task_result,
                playwright_browser=browser_setup.async_browser_generator,
            )


class AgentResourceWithRawResponse:
    def __init__(self, agent: AgentResource) -> None:
        self._agent = agent

        self.task = to_raw_response_wrapper(
            agent.task,
        )
        self.browser_task = to_raw_response_wrapper(
            agent.browser_task,
        )


class AsyncAgentResourceWithRawResponse:
    def __init__(self, agent: AsyncAgentResource) -> None:
        self._agent = agent

        self.task = async_to_raw_response_wrapper(
            agent.task,
        )
        self.browser_task = async_to_raw_response_wrapper(
            agent.browser_task,
        )


class AgentResourceWithStreamingResponse:
    def __init__(self, agent: AgentResource) -> None:
        self._agent = agent

        self.task = to_streamed_response_wrapper(
            agent.task,
        )
        self.browser_task = to_streamed_response_wrapper(
            agent.browser_task,
        )


class AsyncAgentResourceWithStreamingResponse:
    def __init__(self, agent: AsyncAgentResource) -> None:
        self._agent = agent

        self.task = async_to_streamed_response_wrapper(
            agent.task,
        )
        self.browser_task = async_to_streamed_response_wrapper(
            agent.browser_task,
        )
