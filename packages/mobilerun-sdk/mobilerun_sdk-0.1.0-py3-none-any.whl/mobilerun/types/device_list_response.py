# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from .device import Device
from .._models import BaseModel

__all__ = ["DeviceListResponse", "Pagination"]


class Pagination(BaseModel):
    has_next: bool = FieldInfo(alias="hasNext")

    has_prev: bool = FieldInfo(alias="hasPrev")

    page: int

    pages: int

    page_size: int = FieldInfo(alias="pageSize")

    total: int


class DeviceListResponse(BaseModel):
    items: Optional[List[Device]] = None

    pagination: Pagination

    schema_: Optional[str] = FieldInfo(alias="$schema", default=None)
    """A URL to the JSON Schema for this object."""
