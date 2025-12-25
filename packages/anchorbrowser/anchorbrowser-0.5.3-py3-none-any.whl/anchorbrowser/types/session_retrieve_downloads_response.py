# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from .._models import BaseModel

__all__ = ["SessionRetrieveDownloadsResponse", "Data", "DataItem"]


class DataItem(BaseModel):
    id: Optional[str] = None
    """The unique ID of the download record."""

    created_at: Optional[datetime] = None
    """The timestamp when the file record was created."""

    duration: Optional[int] = None
    """The time it took to process or download the file, in milliseconds."""

    file_link: Optional[str] = None
    """The URL to download the file from anchorbrowser servers.

    Requires api key authentication.
    """

    origin_url: Optional[str] = None
    """The original URL where the file was found."""

    original_download_url: Optional[str] = None
    """The URL used to download the file."""

    original_file_name: Optional[str] = None
    """The original file name before any modification."""

    size: Optional[int] = None
    """The size of the file in bytes."""

    suggested_file_name: Optional[str] = None
    """The suggested file name for saving the file."""


class Data(BaseModel):
    count: Optional[int] = None
    """Total number of downloads"""

    items: Optional[List[DataItem]] = None


class SessionRetrieveDownloadsResponse(BaseModel):
    data: Optional[Data] = None
