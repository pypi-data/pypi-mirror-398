# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

__all__ = ["MouseDoubleClickParams"]


class MouseDoubleClickParams(TypedDict, total=False):
    x: Required[int]
    """X coordinate"""

    y: Required[int]
    """Y coordinate"""

    button: Literal["left", "middle", "right"]
    """Mouse button to use"""
