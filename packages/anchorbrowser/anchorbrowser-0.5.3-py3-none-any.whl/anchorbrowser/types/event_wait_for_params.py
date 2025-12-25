# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["EventWaitForParams"]


class EventWaitForParams(TypedDict, total=False):
    timeout_ms: Annotated[int, PropertyInfo(alias="timeoutMs")]
    """Timeout in milliseconds to wait for the event. Defaults to 60000ms (1 minute)."""
