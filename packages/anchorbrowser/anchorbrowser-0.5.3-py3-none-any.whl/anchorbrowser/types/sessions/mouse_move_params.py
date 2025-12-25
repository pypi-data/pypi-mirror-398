# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["MouseMoveParams"]


class MouseMoveParams(TypedDict, total=False):
    x: Required[int]
    """X coordinate"""

    y: Required[int]
    """Y coordinate"""
