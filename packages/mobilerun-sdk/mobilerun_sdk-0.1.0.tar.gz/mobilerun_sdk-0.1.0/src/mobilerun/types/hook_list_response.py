# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .task_status import TaskStatus

__all__ = ["HookListResponse", "Item", "Pagination"]


class Item(BaseModel):
    service: Literal["zapier", "n8n", "make", "internal", "other"]

    url: str

    user_id: str = FieldInfo(alias="userId")

    id: Optional[str] = None

    created_at: Optional[datetime] = FieldInfo(alias="createdAt", default=None)

    events: Optional[List[TaskStatus]] = None

    state: Optional[Literal["active", "disabled", "deleted"]] = None

    updated_at: Optional[datetime] = FieldInfo(alias="updatedAt", default=None)


class Pagination(BaseModel):
    """Pagination metadata"""

    has_next: bool = FieldInfo(alias="hasNext")
    """Whether there is a next page"""

    has_prev: bool = FieldInfo(alias="hasPrev")
    """Whether there is a previous page"""

    page: int
    """Current page number (1-based)"""

    pages: int
    """Total number of pages"""

    page_size: int = FieldInfo(alias="pageSize")
    """Number of items per page"""

    total: int
    """Total number of items"""


class HookListResponse(BaseModel):
    items: List[Item]
    """The paginated items"""

    pagination: Pagination
    """Pagination metadata"""
