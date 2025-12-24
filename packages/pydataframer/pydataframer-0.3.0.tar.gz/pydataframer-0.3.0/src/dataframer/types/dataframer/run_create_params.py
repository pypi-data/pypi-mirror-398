# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict
from typing_extensions import Required, TypedDict

__all__ = ["RunCreateParams"]


class RunCreateParams(TypedDict, total=False):
    number_of_samples: Required[int]
    """Number of samples to generate"""

    runtime_params: Required[Dict[str, object]]
    """Runtime parameters for generation (model, settings, etc.)"""

    spec_version_id: Required[str]
    """ID of the spec version to use"""
