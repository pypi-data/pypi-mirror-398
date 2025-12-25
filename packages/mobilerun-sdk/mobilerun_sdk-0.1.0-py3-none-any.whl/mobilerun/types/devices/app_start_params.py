# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["AppStartParams"]


class AppStartParams(TypedDict, total=False):
    device_id: Required[Annotated[str, PropertyInfo(alias="deviceId")]]

    activity: str

    x_device_display_id: Annotated[int, PropertyInfo(alias="X-Device-Display-ID")]
