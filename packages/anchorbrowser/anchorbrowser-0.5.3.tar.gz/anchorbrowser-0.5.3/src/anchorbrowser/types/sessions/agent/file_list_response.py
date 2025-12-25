# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["FileListResponse", "Data", "DataFile"]


class DataFile(BaseModel):
    last_modified: Optional[datetime] = FieldInfo(alias="lastModified", default=None)
    """When the resource was last modified"""

    name: Optional[str] = None
    """The resource name"""

    size: Optional[int] = None
    """Resource size in bytes"""

    type: Optional[str] = None
    """Resource extension/type"""


class Data(BaseModel):
    files: Optional[List[DataFile]] = None


class FileListResponse(BaseModel):
    data: Optional[Data] = None
