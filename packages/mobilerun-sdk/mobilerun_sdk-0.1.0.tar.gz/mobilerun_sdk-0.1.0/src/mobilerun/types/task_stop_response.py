# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .._models import BaseModel

__all__ = ["TaskStopResponse"]


class TaskStopResponse(BaseModel):
    cancelled: bool
    """Whether the task was cancelled"""
