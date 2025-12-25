# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["SessionScrollParams"]


class SessionScrollParams(TypedDict, total=False):
    delta_y: Required[Annotated[int, PropertyInfo(alias="deltaY")]]
    """Vertical scroll amount (positive is down, negative is up)"""

    x: Required[int]
    """X coordinate"""

    y: Required[int]
    """Y coordinate"""

    delta_x: Annotated[int, PropertyInfo(alias="deltaX")]
    """Horizontal scroll amount (positive is right, negative is left)"""

    steps: int
    """Number of steps to break the scroll into for smoother scrolling"""

    use_os: Annotated[bool, PropertyInfo(alias="useOs")]
    """Whether to use the OS scroll or the Playwright scroll"""
