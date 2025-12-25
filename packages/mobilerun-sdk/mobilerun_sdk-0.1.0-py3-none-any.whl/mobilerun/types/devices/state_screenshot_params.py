# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["StateScreenshotParams"]


class StateScreenshotParams(TypedDict, total=False):
    hide_overlay: Annotated[bool, PropertyInfo(alias="hideOverlay")]

    x_device_display_id: Annotated[int, PropertyInfo(alias="X-Device-Display-ID")]
