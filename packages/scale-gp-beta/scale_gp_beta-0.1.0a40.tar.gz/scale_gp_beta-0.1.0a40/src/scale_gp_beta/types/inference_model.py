# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import TYPE_CHECKING, Dict, List, Union, Optional
from datetime import datetime
from typing_extensions import Literal, TypeAlias

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = [
    "InferenceModel",
    "VendorConfiguration",
    "VendorConfigurationLaunchVendorConfiguration",
    "VendorConfigurationLaunchVendorConfigurationModelImage",
    "VendorConfigurationLaunchVendorConfigurationModelInfra",
    "VendorConfigurationLlmEngineVendorConfiguration",
]


class VendorConfigurationLaunchVendorConfigurationModelImage(BaseModel):
    command: List[str]

    registry: str

    repository: str

    tag: str

    env_vars: Optional[Dict[str, object]] = None

    healthcheck_route: Optional[str] = None

    predict_route: Optional[str] = None

    readiness_delay: Optional[int] = None

    request_schema: Optional[Dict[str, object]] = None

    response_schema: Optional[Dict[str, object]] = None

    streaming_command: Optional[List[str]] = None

    streaming_predict_route: Optional[str] = None


class VendorConfigurationLaunchVendorConfigurationModelInfra(BaseModel):
    cpus: Union[str, int, None] = None

    endpoint_type: Optional[Literal["async", "sync", "streaming"]] = None

    gpu_type: Optional[
        Literal[
            "nvidia-tesla-t4",
            "nvidia-ampere-a10",
            "nvidia-ampere-a100",
            "nvidia-ampere-a100e",
            "nvidia-hopper-h100",
            "nvidia-hopper-h100-1g20gb",
            "nvidia-hopper-h100-3g40gb",
        ]
    ] = None

    gpus: Optional[int] = None

    high_priority: Optional[bool] = None

    labels: Optional[Dict[str, str]] = None

    max_workers: Optional[int] = None

    memory: Optional[str] = None

    min_workers: Optional[int] = None

    per_worker: Optional[int] = None

    public_inference: Optional[bool] = None

    storage: Optional[str] = None


class VendorConfigurationLaunchVendorConfiguration(BaseModel):
    image: VendorConfigurationLaunchVendorConfigurationModelImage = FieldInfo(alias="model_image")

    infra: VendorConfigurationLaunchVendorConfigurationModelInfra = FieldInfo(alias="model_infra")


class VendorConfigurationLlmEngineVendorConfiguration(BaseModel):
    model: str

    checkpoint_path: Optional[str] = None

    cpus: Optional[int] = None

    default_callback_url: Optional[str] = None

    endpoint_type: Optional[str] = None

    gpu_type: Optional[str] = None

    gpus: Optional[int] = None

    high_priority: Optional[bool] = None

    inference_framework: Optional[str] = None

    inference_framework_image_tag: Optional[str] = None

    labels: Optional[Dict[str, str]] = None

    max_workers: Optional[int] = None

    memory: Optional[str] = None

    min_workers: Optional[int] = None

    nodes_per_worker: Optional[int] = None

    num_shards: Optional[int] = None

    per_worker: Optional[int] = None

    post_inference_hooks: Optional[List[str]] = None

    public_inference: Optional[bool] = None

    quantize: Optional[str] = None

    source: Optional[str] = None

    storage: Optional[str] = None

    if TYPE_CHECKING:
        # Some versions of Pydantic <2.8.0 have a bug and don’t allow assigning a
        # value to this field, so for compatibility we avoid doing it at runtime.
        __pydantic_extra__: Dict[str, object] = FieldInfo(init=False)  # pyright: ignore[reportIncompatibleVariableOverride]

        # Stub to indicate that arbitrary properties are accepted.
        # To access properties that are not valid identifiers you can use `getattr`, e.g.
        # `getattr(obj, '$type')`
        def __getattr__(self, attr: str) -> object: ...
    else:
        __pydantic_extra__: Dict[str, object]


VendorConfiguration: TypeAlias = Union[
    VendorConfigurationLaunchVendorConfiguration, VendorConfigurationLlmEngineVendorConfiguration
]


class InferenceModel(BaseModel):
    id: str

    created_at: datetime

    created_by_identity_type: Literal["user", "service_account"]

    created_by_user_id: str

    type: Literal["generic", "completion", "chat_completion"] = FieldInfo(alias="model_type")

    vendor: Literal[
        "openai",
        "cohere",
        "vertex_ai",
        "anthropic",
        "azure",
        "gemini",
        "launch",
        "llmengine",
        "model_zoo",
        "bedrock",
        "xai",
        "fireworks_ai",
    ] = FieldInfo(alias="model_vendor")

    name: str

    status: Literal["failed", "ready", "deploying"]

    availability: Optional[Literal["unknown", "available", "unavailable"]] = FieldInfo(
        alias="model_availability", default=None
    )

    metadata: Optional[Dict[str, object]] = FieldInfo(alias="model_metadata", default=None)

    object: Optional[Literal["model"]] = None

    vendor_configuration: Optional[VendorConfiguration] = None
