# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["ActionSwipeParams"]


class ActionSwipeParams(TypedDict, total=False):
    duration: Required[int]
    """Swipe duration in milliseconds"""

    end_x: Required[Annotated[int, PropertyInfo(alias="endX")]]

    end_y: Required[Annotated[int, PropertyInfo(alias="endY")]]

    start_x: Required[Annotated[int, PropertyInfo(alias="startX")]]

    start_y: Required[Annotated[int, PropertyInfo(alias="startY")]]

    x_device_display_id: Annotated[int, PropertyInfo(alias="X-Device-Display-ID")]
