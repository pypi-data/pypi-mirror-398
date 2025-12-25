# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["AppListParams"]


class AppListParams(TypedDict, total=False):
    include_system_apps: Annotated[bool, PropertyInfo(alias="includeSystemApps")]

    x_device_display_id: Annotated[int, PropertyInfo(alias="X-Device-Display-ID")]
