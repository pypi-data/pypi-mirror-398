# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["SessionDragAndDropParams"]


class SessionDragAndDropParams(TypedDict, total=False):
    end_x: Required[Annotated[int, PropertyInfo(alias="endX")]]
    """Ending X coordinate"""

    end_y: Required[Annotated[int, PropertyInfo(alias="endY")]]
    """Ending Y coordinate"""

    start_x: Required[Annotated[int, PropertyInfo(alias="startX")]]
    """Starting X coordinate"""

    start_y: Required[Annotated[int, PropertyInfo(alias="startY")]]
    """Starting Y coordinate"""

    button: Literal["left", "middle", "right"]
    """Mouse button to use"""
