# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["PackageListParams"]


class PackageListParams(TypedDict, total=False):
    include_system_packages: Annotated[bool, PropertyInfo(alias="includeSystemPackages")]

    x_device_display_id: Annotated[int, PropertyInfo(alias="X-Device-Display-ID")]
