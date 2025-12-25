# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import TypeAlias

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["AppListResponse", "AppListResponseItem"]


class AppListResponseItem(BaseModel):
    is_system_app: bool = FieldInfo(alias="isSystemApp")

    label: str

    package_name: str = FieldInfo(alias="packageName")

    version_code: int = FieldInfo(alias="versionCode")

    version_name: str = FieldInfo(alias="versionName")


AppListResponse: TypeAlias = List[AppListResponseItem]
