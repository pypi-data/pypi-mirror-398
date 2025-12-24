# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .._types import SequenceNotStr

__all__ = [
    "ModelCreateParams",
    "LaunchModelCreateRequest",
    "LaunchModelCreateRequestVendorConfiguration",
    "LaunchModelCreateRequestVendorConfigurationModelImage",
    "LaunchModelCreateRequestVendorConfigurationModelInfra",
    "LlmEngineModelCreateRequest",
    "LlmEngineModelCreateRequestVendorConfiguration",
]


class LaunchModelCreateRequest(TypedDict, total=False):
    name: Required[str]
    """Unique name to reference your model"""

    vendor_configuration: Required[LaunchModelCreateRequestVendorConfiguration]

    model_metadata: Dict[str, object]

    model_type: Literal["generic"]

    model_vendor: Literal["launch"]

    on_conflict: Literal["error", "update"]


class LaunchModelCreateRequestVendorConfigurationModelImage(TypedDict, total=False):
    command: Required[SequenceNotStr[str]]

    registry: Required[str]

    repository: Required[str]

    tag: Required[str]

    env_vars: Dict[str, object]

    healthcheck_route: str

    predict_route: str

    readiness_delay: int

    request_schema: Dict[str, object]

    response_schema: Dict[str, object]

    streaming_command: SequenceNotStr[str]

    streaming_predict_route: str


class LaunchModelCreateRequestVendorConfigurationModelInfra(TypedDict, total=False):
    cpus: Union[str, int]

    endpoint_type: Literal["async", "sync", "streaming"]

    gpu_type: Literal[
        "nvidia-tesla-t4",
        "nvidia-ampere-a10",
        "nvidia-ampere-a100",
        "nvidia-ampere-a100e",
        "nvidia-hopper-h100",
        "nvidia-hopper-h100-1g20gb",
        "nvidia-hopper-h100-3g40gb",
    ]

    gpus: int

    high_priority: bool

    labels: Dict[str, str]

    max_workers: int

    memory: str

    min_workers: int

    per_worker: int

    public_inference: bool

    storage: str


class LaunchModelCreateRequestVendorConfiguration(TypedDict, total=False):
    model_image: Required[LaunchModelCreateRequestVendorConfigurationModelImage]

    model_infra: Required[LaunchModelCreateRequestVendorConfigurationModelInfra]


class LlmEngineModelCreateRequest(TypedDict, total=False):
    name: Required[str]
    """Unique name to reference your model"""

    vendor_configuration: Required[LlmEngineModelCreateRequestVendorConfiguration]

    model_metadata: Dict[str, object]

    model_type: Literal["chat_completion"]

    model_vendor: Literal["llmengine"]

    on_conflict: Literal["error", "update"]


class LlmEngineModelCreateRequestVendorConfigurationTyped(TypedDict, total=False):
    model: Required[str]

    checkpoint_path: str

    cpus: int

    default_callback_url: str

    endpoint_type: str

    gpu_type: str

    gpus: int

    high_priority: bool

    inference_framework: str

    inference_framework_image_tag: str

    labels: Dict[str, str]

    max_workers: int

    memory: str

    min_workers: int

    nodes_per_worker: int

    num_shards: int

    per_worker: int

    post_inference_hooks: SequenceNotStr[str]

    public_inference: bool

    quantize: str

    source: str

    storage: str


LlmEngineModelCreateRequestVendorConfiguration: TypeAlias = Union[
    LlmEngineModelCreateRequestVendorConfigurationTyped, Dict[str, object]
]

ModelCreateParams: TypeAlias = Union[LaunchModelCreateRequest, LlmEngineModelCreateRequest]
