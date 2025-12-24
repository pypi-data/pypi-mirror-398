# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

__all__ = ["GenerateCreateParams"]


class GenerateCreateParams(TypedDict, total=False):
    generation_model: Required[
        Literal[
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
    ]
    """AI model to use for generation"""

    number_of_samples: Required[int]
    """Number of samples to generate"""

    spec_id: Required[str]
    """ID of the spec to use for generation"""

    enable_revisions: bool
    """Enable revision cycles"""

    evaluation_model: Literal[
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
    """AI model for evaluation (short samples only)"""

    evaluation_thinking_budget: int
    """Thinking budget for evaluation model (tokens, short samples)"""

    generation_thinking_budget: int
    """Thinking budget for generation model (tokens)"""

    max_examples_in_prompt: int
    """Maximum number of seed examples to include in prompts (long samples only).

    If not set, all seeds are used (subject to token limits).
    """

    max_iterations: int
    """Max feedback iterations (short samples only)"""

    max_revision_cycles: int
    """Max revision cycles (long samples only)"""

    num_examples_in_prompt: int
    """Number of examples to include in prompt (short samples only)"""

    outline_model: Literal[
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
    """AI model for outline generation (long samples only)"""

    outline_thinking_budget: int
    """Thinking budget for outline model (tokens, long samples)"""

    revision_model: Literal[
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
    """AI model for revisions (long samples only)"""

    revision_thinking_budget: int
    """Thinking budget for revision model (tokens, long samples)"""

    sample_type: Literal["short", "long"]
    """Type of samples to generate"""

    seed_shuffling_level: Literal["none", "sample", "field", "prompt"]
    """Seed shuffling level for long samples.

    Controls trade-off between prompt caching efficiency and data diversity.
    """

    spec_version_id: str
    """Specific version ID to use (optional, defaults to latest version)"""

    sql_validation_level: Literal["syntax", "syntax+schema", "syntax+schema+execute"]
    """SQL validation level for long samples with SQL content"""

    staged_generation: bool
    """Use staged generation approach (short samples only)"""

    use_historical_feedback: bool
    """Use historical feedback (short samples only)"""
