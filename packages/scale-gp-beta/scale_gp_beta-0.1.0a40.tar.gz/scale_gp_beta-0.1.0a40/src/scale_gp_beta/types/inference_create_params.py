# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict
from typing_extensions import Required, TypedDict

__all__ = ["InferenceCreateParams", "InferenceConfiguration"]


class InferenceCreateParams(TypedDict, total=False):
    model: Required[str]
    """model specified as `vendor/name` (ex. openai/gpt-5)"""

    args: Dict[str, object]
    """Arguments passed into model"""

    inference_configuration: InferenceConfiguration
    """Vendor specific configuration"""


class InferenceConfiguration(TypedDict, total=False):
    """Vendor specific configuration"""

    num_retries: int

    timeout_seconds: int
