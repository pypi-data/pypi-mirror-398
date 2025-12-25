# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict
from typing_extensions import Required, TypedDict

__all__ = ["EventSignalParams"]


class EventSignalParams(TypedDict, total=False):
    data: Required[Dict[str, object]]
    """Event data to be passed to waiting clients"""
