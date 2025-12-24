# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

__all__ = ["AnalyzeCreateParams"]


class AnalyzeCreateParams(TypedDict, total=False):
    dataset_id: Required[str]
    """ID of the dataset to analyze"""

    name: Required[str]
    """Name for the new spec to be created"""

    analysis_model_name: Literal[
        "anthropic/claude-opus-4-5",
        "anthropic/claude-opus-4-5-thinking",
        "anthropic/claude-sonnet-4-5",
        "anthropic/claude-sonnet-4-5-thinking",
        "anthropic/claude-haiku-4-5",
        "deepseek-ai/DeepSeek-V3.1",
        "moonshotai/Kimi-K2-Instruct",
        "openai/gpt-oss-120b",
        "deepseek-ai/DeepSeek-R1-0528-tput",
        "Qwen/Qwen2.5-72B-Instruct-Turbo",
    ]
    """AI model to use for analysis"""

    description: str
    """Description of the spec"""

    extrapolate_axes: bool
    """Extrapolate to new axes/dimensions"""

    extrapolate_values: bool
    """Extrapolate new values beyond existing data ranges"""

    generate_distributions: bool
    """Generate statistical distributions from the data"""

    generation_objectives: str
    """Custom objectives or instructions for data generation"""

    use_truncation: bool
    """Apply truncation to limit value ranges"""
