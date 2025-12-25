# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["AppListParams"]


class AppListParams(TypedDict, total=False):
    order: Literal["asc", "desc"]

    page: int

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]

    query: str

    sort_by: Annotated[Literal["createdAt", "name"], PropertyInfo(alias="sortBy")]

    source: Literal["all", "uploaded", "store", "queued"]
