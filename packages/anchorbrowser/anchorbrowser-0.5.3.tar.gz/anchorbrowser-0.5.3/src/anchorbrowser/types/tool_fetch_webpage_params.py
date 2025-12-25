# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["ToolFetchWebpageParams"]


class ToolFetchWebpageParams(TypedDict, total=False):
    session_id: Annotated[str, PropertyInfo(alias="sessionId")]
    """
    An optional browser session identifier to reference an existing running browser
    session. If provided, the tool will execute within that browser session.
    """

    format: Literal["html", "markdown"]
    """The output format of the content."""

    new_page: bool
    """Whether to create a new page for the content."""

    page_index: int
    """The index of the page to fetch content from. **Overides new_page**."""

    return_partial_on_timeout: bool
    """
    Whether to return partial content if the content is not loaded within the 20
    seconds.
    """

    url: str
    """The URL of the webpage to fetch content from.

    When left empty, the current webpage is used.
    """

    wait: int
    """The time to wait for **dynamic** content to load in **milliseconds**."""
