# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal, TypeAlias

__all__ = ["LlmModel"]

LlmModel: TypeAlias = Literal[
    "openai/gpt-5",
    "google/gemini-2.5-flash",
    "google/gemini-2.5-pro",
    "google/gemini-3-pro-preview",
    "anthropic/claude-sonnet-4.5",
    "minimax/minimax-m2",
    "moonshotai/kimi-k2-thinking",
]
