# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["TaskRunResponse"]


class TaskRunResponse(BaseModel):
    id: str
    """The ID of the task"""

    token: str
    """The token of the stream"""

    stream_url: str = FieldInfo(alias="streamUrl")
    """The URL of the stream"""
