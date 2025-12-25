# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["MouseClickParams"]


class MouseClickParams(TypedDict, total=False):
    button: Literal["left", "middle", "right"]
    """Mouse button to use"""

    index: float
    """
    If a selector was passed and multiple elements match the selector, the index of
    the element in the list (0-based). Defaults to 0.
    """

    selector: str
    """A valid CSS selector for the requested element"""

    selector_timeout_ms: Annotated[float, PropertyInfo(alias="timeout")]
    """
    If a selector was passed, timeout in ms for waiting for the DOM element to be
    selected. Defaults to 5000 (5 seconds).
    """

    x: float
    """X coordinate"""

    y: float
    """Y coordinate"""
