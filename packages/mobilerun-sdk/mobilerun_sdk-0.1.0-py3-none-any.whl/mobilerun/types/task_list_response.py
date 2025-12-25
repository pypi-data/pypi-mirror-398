# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from pydantic import Field as FieldInfo

from .task import Task
from .._models import BaseModel

__all__ = ["TaskListResponse", "Pagination"]


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


class TaskListResponse(BaseModel):
    items: List[Task]
    """The paginated items"""

    pagination: Pagination
    """Pagination metadata"""
