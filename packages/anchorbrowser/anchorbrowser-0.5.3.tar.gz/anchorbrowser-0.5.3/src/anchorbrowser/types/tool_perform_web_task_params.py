# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["ToolPerformWebTaskParams"]


class ToolPerformWebTaskParams(TypedDict, total=False):
    prompt: Required[str]
    """The task to be autonomously completed."""

    session_id: Annotated[str, PropertyInfo(alias="sessionId")]
    """
    An optional browser session identifier to reference an existing running browser
    sessions. When passed, the tool will be executed on the provided browser
    session.
    """

    agent: Literal["browser-use", "openai-cua"]
    """The AI agent to use for task completion. Defaults to browser-use."""

    detect_elements: bool
    """Enable element detection for better interaction accuracy.

    Improves the agent's ability to identify and interact with UI elements.
    """

    highlight_elements: bool
    """Whether to highlight elements during task execution for better visibility."""

    human_intervention: bool
    """Allow human intervention during task execution.

    When enabled, the agent can request human input for ambiguous situations.
    """

    max_steps: int
    """Maximum number of steps the agent can take to complete the task.

    Defaults to 200.
    """

    model: str
    """The specific model to use for task completion.

    see our [models](/agentic-browser-control/ai-task-completion#available-models)
    page for more information.
    """

    output_schema: object
    """JSON Schema defining the expected structure of the output data."""

    provider: Literal["openai", "gemini", "groq", "azure", "xai"]
    """The AI provider to use for task completion."""

    secret_values: Dict[str, str]
    """Secret values to pass to the agent for secure credential handling.

    Keys and values are passed as environment variables to the agent.
    """

    url: str
    """The URL of the webpage.

    If not provided, the tool will use the current page in the session.
    """

    directly_open_url: bool
    """If true, the tool will directly open the URL in the browser."""