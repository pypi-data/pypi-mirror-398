# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["ClipboardSetParams"]


class ClipboardSetParams(TypedDict, total=False):
    text: Required[str]
    """Text to set in the clipboard"""
