# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["Device"]


class Device(BaseModel):
    id: str

    apps: Optional[List[str]] = None

    assigned_at: Optional[datetime] = FieldInfo(alias="assignedAt", default=None)

    country: str

    created_at: datetime = FieldInfo(alias="createdAt")

    files: Optional[List[str]] = None

    name: str

    state: str

    state_message: str = FieldInfo(alias="stateMessage")

    stream_token: str = FieldInfo(alias="streamToken")

    stream_url: str = FieldInfo(alias="streamUrl")

    task_count: int = FieldInfo(alias="taskCount")

    updated_at: datetime = FieldInfo(alias="updatedAt")

    schema_: Optional[str] = FieldInfo(alias="$schema", default=None)
    """A URL to the JSON Schema for this object."""
