# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["ToolScreenshotWebpageParams"]


class ToolScreenshotWebpageParams(TypedDict, total=False):
    session_id: Annotated[str, PropertyInfo(alias="sessionId")]
    """
    An optional browser session identifier to reference an existing running browser
    sessions. When passed, the tool will be executed on the provided browser
    session.
    """

    capture_full_height: bool
    """If true, captures the entire height of the page, ignoring the viewport height."""

    height: int
    """The height of the browser viewport in pixels."""

    image_quality: int
    """Quality of the output image, on the range 1-100.

    100 will not perform any compression.
    """

    s3_target_address: str
    """Presigned S3 url target to upload the image to."""

    scroll_all_content: bool
    """If true, scrolls the page and captures all visible content."""

    url: str
    """The URL of the webpage to capture."""

    wait: int
    """
    Duration in milliseconds to wait after page has loaded, mainly used for sites
    with JS animations.
    """

    width: int
    """The width of the browser viewport in pixels."""
