# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, TypedDict

__all__ = ["EvaluationCreateParams"]


class EvaluationCreateParams(TypedDict, total=False):
    evaluation_model: Literal[
        "anthropic/claude-opus-4-5",
        "anthropic/claude-opus-4-5-thinking",
        "anthropic/claude-sonnet-4-5",
        "anthropic/claude-sonnet-4-5-thinking",
        "anthropic/claude-haiku-4-5",
    ]
    """AI model to use for evaluation (optional)"""
