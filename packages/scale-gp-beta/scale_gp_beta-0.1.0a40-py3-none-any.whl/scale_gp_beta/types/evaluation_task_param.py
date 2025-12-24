# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Iterable
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .._types import SequenceNotStr
from .item_locator import ItemLocator

__all__ = [
    "EvaluationTaskParam",
    "ChatCompletionEvaluationTask",
    "ChatCompletionEvaluationTaskConfiguration",
    "GenericInferenceEvaluationTask",
    "GenericInferenceEvaluationTaskConfiguration",
    "GenericInferenceEvaluationTaskConfigurationInferenceConfiguration",
    "GenericInferenceEvaluationTaskConfigurationInferenceConfigurationLaunchInferenceConfiguration",
    "ApplicationVariantV1EvaluationTask",
    "ApplicationVariantV1EvaluationTaskConfiguration",
    "ApplicationVariantV1EvaluationTaskConfigurationHistoryApplicationRequestResponsePairArray",
    "ApplicationVariantV1EvaluationTaskConfigurationOverrides",
    "ApplicationVariantV1EvaluationTaskConfigurationOverridesAgenticApplicationOverrides",
    "ApplicationVariantV1EvaluationTaskConfigurationOverridesAgenticApplicationOverridesInitialState",
    "ApplicationVariantV1EvaluationTaskConfigurationOverridesAgenticApplicationOverridesPartialTrace",
    "AgentexOutputEvaluationTask",
    "AgentexOutputEvaluationTaskConfiguration",
    "MetricEvaluationTask",
    "MetricEvaluationTaskConfiguration",
    "MetricEvaluationTaskConfigurationBleuScorerConfigWithItemLocator",
    "MetricEvaluationTaskConfigurationMeteorScorerConfigWithItemLocator",
    "MetricEvaluationTaskConfigurationCosineSimilarityScorerConfigWithItemLocator",
    "MetricEvaluationTaskConfigurationF1ScorerConfigWithItemLocator",
    "MetricEvaluationTaskConfigurationRougeScorer1ConfigWithItemLocator",
    "MetricEvaluationTaskConfigurationRougeScorer2ConfigWithItemLocator",
    "MetricEvaluationTaskConfigurationRougeScorerLConfigWithItemLocator",
    "AutoEvaluationQuestionTask",
    "AutoEvaluationQuestionTaskConfiguration",
    "AutoEvaluationGuidedDecodingEvaluationTask",
    "AutoEvaluationGuidedDecodingEvaluationTaskConfiguration",
    "AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationStructuredOutputTaskRequestWithItemLocator",
    "AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationGuidedDecodingTaskRequestWithItemLocator",
    "AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocator",
    "AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedTo",
    "AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedToApeAgent",
    "AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedToApeAgentConfig",
    "AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedToIfAgent",
    "AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedToIfAgentConfig",
    "AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedToTruthfulnessAgent",
    "AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedToTruthfulnessAgentConfig",
    "AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedToBaseAgent",
    "AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedToBaseAgentConfig",
    "AutoEvaluationAgentEvaluationTask",
    "AutoEvaluationAgentEvaluationTaskConfiguration",
    "AutoEvaluationAgentEvaluationTaskConfigurationDesignatedTo",
    "AutoEvaluationAgentEvaluationTaskConfigurationDesignatedToApeAgent",
    "AutoEvaluationAgentEvaluationTaskConfigurationDesignatedToApeAgentConfig",
    "AutoEvaluationAgentEvaluationTaskConfigurationDesignatedToIfAgent",
    "AutoEvaluationAgentEvaluationTaskConfigurationDesignatedToIfAgentConfig",
    "AutoEvaluationAgentEvaluationTaskConfigurationDesignatedToTruthfulnessAgent",
    "AutoEvaluationAgentEvaluationTaskConfigurationDesignatedToTruthfulnessAgentConfig",
    "AutoEvaluationAgentEvaluationTaskConfigurationDesignatedToBaseAgent",
    "AutoEvaluationAgentEvaluationTaskConfigurationDesignatedToBaseAgentConfig",
    "ContributorEvaluationQuestionTask",
    "ContributorEvaluationQuestionTaskConfiguration",
]


class ChatCompletionEvaluationTaskConfigurationTyped(TypedDict, total=False):
    messages: Required[Union[Iterable[Dict[str, object]], ItemLocator]]

    model: Required[str]

    audio: Union[Dict[str, object], ItemLocator]

    frequency_penalty: Union[float, ItemLocator]

    function_call: Union[Dict[str, object], ItemLocator]

    functions: Union[Iterable[Dict[str, object]], ItemLocator]

    logit_bias: Union[Dict[str, int], ItemLocator]

    logprobs: Union[bool, ItemLocator]

    max_completion_tokens: Union[int, ItemLocator]

    max_tokens: Union[int, ItemLocator]

    metadata: Union[Dict[str, str], ItemLocator]

    modalities: Union[SequenceNotStr[str], ItemLocator]

    n: Union[int, ItemLocator]

    parallel_tool_calls: Union[bool, ItemLocator]

    prediction: Union[Dict[str, object], ItemLocator]

    presence_penalty: Union[float, ItemLocator]

    reasoning_effort: str

    response_format: Union[Dict[str, object], ItemLocator]

    seed: Union[int, ItemLocator]

    stop: str

    store: Union[bool, ItemLocator]

    temperature: Union[float, ItemLocator]

    tool_choice: str

    tools: Union[Iterable[Dict[str, object]], ItemLocator]

    top_k: Union[int, ItemLocator]

    top_logprobs: Union[int, ItemLocator]

    top_p: Union[float, ItemLocator]


ChatCompletionEvaluationTaskConfiguration: TypeAlias = Union[
    ChatCompletionEvaluationTaskConfigurationTyped, Dict[str, object]
]


class ChatCompletionEvaluationTask(TypedDict, total=False):
    configuration: Required[ChatCompletionEvaluationTaskConfiguration]

    alias: str
    """Alias to title the results column. Defaults to the `chat_completion`"""

    task_type: Literal["chat_completion"]


class GenericInferenceEvaluationTaskConfigurationInferenceConfigurationLaunchInferenceConfiguration(
    TypedDict, total=False
):
    num_retries: int

    timeout_seconds: int


GenericInferenceEvaluationTaskConfigurationInferenceConfiguration: TypeAlias = Union[
    GenericInferenceEvaluationTaskConfigurationInferenceConfigurationLaunchInferenceConfiguration, ItemLocator
]


class GenericInferenceEvaluationTaskConfiguration(TypedDict, total=False):
    model: Required[str]

    args: Union[Dict[str, object], ItemLocator]

    inference_configuration: GenericInferenceEvaluationTaskConfigurationInferenceConfiguration


class GenericInferenceEvaluationTask(TypedDict, total=False):
    configuration: Required[GenericInferenceEvaluationTaskConfiguration]

    alias: str
    """Alias to title the results column. Defaults to the `inference`"""

    task_type: Literal["inference"]


class ApplicationVariantV1EvaluationTaskConfigurationHistoryApplicationRequestResponsePairArray(TypedDict, total=False):
    request: Required[str]
    """Request inputs"""

    response: Required[str]
    """Response outputs"""

    session_data: Dict[str, object]
    """Session data corresponding to the request response pair"""


class ApplicationVariantV1EvaluationTaskConfigurationOverridesAgenticApplicationOverridesInitialState(
    TypedDict, total=False
):
    current_node: Required[str]

    state: Required[Dict[str, object]]


class ApplicationVariantV1EvaluationTaskConfigurationOverridesAgenticApplicationOverridesPartialTrace(
    TypedDict, total=False
):
    duration_ms: Required[int]

    node_id: Required[str]

    operation_input: Required[str]

    operation_output: Required[str]

    operation_type: Required[str]

    start_timestamp: Required[str]

    workflow_id: Required[str]

    operation_metadata: Dict[str, object]


class ApplicationVariantV1EvaluationTaskConfigurationOverridesAgenticApplicationOverrides(TypedDict, total=False):
    """Execution override options for agentic applications"""

    concurrent: bool

    initial_state: ApplicationVariantV1EvaluationTaskConfigurationOverridesAgenticApplicationOverridesInitialState

    partial_trace: Iterable[
        ApplicationVariantV1EvaluationTaskConfigurationOverridesAgenticApplicationOverridesPartialTrace
    ]

    return_span: bool

    use_channels: bool


ApplicationVariantV1EvaluationTaskConfigurationOverrides: TypeAlias = Union[
    ApplicationVariantV1EvaluationTaskConfigurationOverridesAgenticApplicationOverrides, ItemLocator
]


class ApplicationVariantV1EvaluationTaskConfiguration(TypedDict, total=False):
    application_variant_id: Required[str]

    inputs: Required[Union[Dict[str, object], ItemLocator]]

    history: Union[
        Iterable[ApplicationVariantV1EvaluationTaskConfigurationHistoryApplicationRequestResponsePairArray], ItemLocator
    ]

    operation_metadata: Union[Dict[str, object], ItemLocator]

    overrides: ApplicationVariantV1EvaluationTaskConfigurationOverrides
    """Execution override options for agentic applications"""


class ApplicationVariantV1EvaluationTask(TypedDict, total=False):
    configuration: Required[ApplicationVariantV1EvaluationTaskConfiguration]

    alias: str
    """Alias to title the results column. Defaults to the `application_variant`"""

    task_type: Literal["application_variant"]


class AgentexOutputEvaluationTaskConfiguration(TypedDict, total=False):
    agentex_agent_id: Required[str]

    input_column: Required[Union[ItemLocator, object]]

    include_traces: Union[bool, ItemLocator]


class AgentexOutputEvaluationTask(TypedDict, total=False):
    configuration: Required[AgentexOutputEvaluationTaskConfiguration]

    alias: str
    """Alias to title the results column. Defaults to the `agentex_output`"""

    task_type: Literal["agentex_output"]


class MetricEvaluationTaskConfigurationBleuScorerConfigWithItemLocator(TypedDict, total=False):
    candidate: Required[str]

    reference: Required[str]

    type: Required[Literal["bleu"]]


class MetricEvaluationTaskConfigurationMeteorScorerConfigWithItemLocator(TypedDict, total=False):
    candidate: Required[str]

    reference: Required[str]

    type: Required[Literal["meteor"]]


class MetricEvaluationTaskConfigurationCosineSimilarityScorerConfigWithItemLocator(TypedDict, total=False):
    candidate: Required[str]

    reference: Required[str]

    type: Required[Literal["cosine_similarity"]]


class MetricEvaluationTaskConfigurationF1ScorerConfigWithItemLocator(TypedDict, total=False):
    candidate: Required[str]

    reference: Required[str]

    type: Required[Literal["f1"]]


class MetricEvaluationTaskConfigurationRougeScorer1ConfigWithItemLocator(TypedDict, total=False):
    candidate: Required[str]

    reference: Required[str]

    type: Required[Literal["rouge1"]]


class MetricEvaluationTaskConfigurationRougeScorer2ConfigWithItemLocator(TypedDict, total=False):
    candidate: Required[str]

    reference: Required[str]

    type: Required[Literal["rouge2"]]


class MetricEvaluationTaskConfigurationRougeScorerLConfigWithItemLocator(TypedDict, total=False):
    candidate: Required[str]

    reference: Required[str]

    type: Required[Literal["rougeL"]]


MetricEvaluationTaskConfiguration: TypeAlias = Union[
    MetricEvaluationTaskConfigurationBleuScorerConfigWithItemLocator,
    MetricEvaluationTaskConfigurationMeteorScorerConfigWithItemLocator,
    MetricEvaluationTaskConfigurationCosineSimilarityScorerConfigWithItemLocator,
    MetricEvaluationTaskConfigurationF1ScorerConfigWithItemLocator,
    MetricEvaluationTaskConfigurationRougeScorer1ConfigWithItemLocator,
    MetricEvaluationTaskConfigurationRougeScorer2ConfigWithItemLocator,
    MetricEvaluationTaskConfigurationRougeScorerLConfigWithItemLocator,
]


class MetricEvaluationTask(TypedDict, total=False):
    configuration: Required[MetricEvaluationTaskConfiguration]

    alias: str
    """Alias to title the results column.

    Defaults to the metric type specified in the configuration
    """

    task_type: Literal["metric"]


class AutoEvaluationQuestionTaskConfiguration(TypedDict, total=False):
    model: Required[str]
    """model specified as `model_vendor/model_name`"""

    prompt: Required[str]

    question_id: Required[str]
    """question to be evaluated"""


class AutoEvaluationQuestionTask(TypedDict, total=False):
    configuration: Required[AutoEvaluationQuestionTaskConfiguration]

    alias: str
    """Alias to title the results column. Defaults to the `auto_evaluation_question`"""

    task_type: Literal["auto_evaluation.question"]


class AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationStructuredOutputTaskRequestWithItemLocator(
    TypedDict, total=False
):
    model: Required[str]
    """model specified as `model_vendor/model_name`"""

    prompt: Required[str]

    response_format: Required[Dict[str, object]]
    """JSON schema used for structuring the model response"""

    inference_args: Dict[str, object]
    """Additional arguments to pass to the inference request"""

    system_prompt: str


class AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationGuidedDecodingTaskRequestWithItemLocator(
    TypedDict, total=False
):
    choices: Required[SequenceNotStr[str]]
    """Choices array cannot be empty"""

    model: Required[str]
    """model specified as `model_vendor/model_name`"""

    prompt: Required[str]

    inference_args: Dict[str, object]
    """Additional arguments to pass to the inference request"""

    system_prompt: str


class AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedToApeAgentConfig(
    TypedDict, total=False
):
    model: str

    temperature: float


class AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedToApeAgent(
    TypedDict, total=False
):
    config: Required[
        AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedToApeAgentConfig
    ]

    agent_name: Literal["APEAgent"]


class AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedToIfAgentConfig(
    TypedDict, total=False
):
    model: str


class AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedToIfAgent(
    TypedDict, total=False
):
    config: Required[
        AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedToIfAgentConfig
    ]

    agent_name: Literal["IFAgent"]


class AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedToTruthfulnessAgentConfig(
    TypedDict, total=False
):
    model: str


class AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedToTruthfulnessAgent(
    TypedDict, total=False
):
    config: Required[
        AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedToTruthfulnessAgentConfig
    ]

    agent_name: Literal["TruthfulnessAgent"]


class AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedToBaseAgentConfig(
    TypedDict, total=False
):
    model: str


class AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedToBaseAgent(
    TypedDict, total=False
):
    config: Required[
        AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedToBaseAgentConfig
    ]

    agent_name: Literal["BaseAgent"]


AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedTo: TypeAlias = Union[
    AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedToApeAgent,
    AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedToIfAgent,
    AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedToTruthfulnessAgent,
    AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedToBaseAgent,
]


class AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocator(
    TypedDict, total=False
):
    definition: Required[str]

    name: Required[str]

    output_rules: Required[SequenceNotStr[str]]

    data_fields: SequenceNotStr[str]

    designated_to: (
        AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocatorDesignatedTo
    )

    output_type: Literal["text", "integer", "float", "boolean"]

    output_values: SequenceNotStr[Union[str, float, bool]]


AutoEvaluationGuidedDecodingEvaluationTaskConfiguration: TypeAlias = Union[
    AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationStructuredOutputTaskRequestWithItemLocator,
    AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationGuidedDecodingTaskRequestWithItemLocator,
    AutoEvaluationGuidedDecodingEvaluationTaskConfigurationAutoEvaluationAgentTaskRequestWithItemLocator,
]


class AutoEvaluationGuidedDecodingEvaluationTask(TypedDict, total=False):
    configuration: Required[AutoEvaluationGuidedDecodingEvaluationTaskConfiguration]

    alias: str
    """Alias to title the results column.

    Defaults to the `auto_evaluation_guided_decoding`
    """

    task_type: Literal["auto_evaluation.guided_decoding"]


class AutoEvaluationAgentEvaluationTaskConfigurationDesignatedToApeAgentConfig(TypedDict, total=False):
    model: str

    temperature: float


class AutoEvaluationAgentEvaluationTaskConfigurationDesignatedToApeAgent(TypedDict, total=False):
    config: Required[AutoEvaluationAgentEvaluationTaskConfigurationDesignatedToApeAgentConfig]

    agent_name: Literal["APEAgent"]


class AutoEvaluationAgentEvaluationTaskConfigurationDesignatedToIfAgentConfig(TypedDict, total=False):
    model: str


class AutoEvaluationAgentEvaluationTaskConfigurationDesignatedToIfAgent(TypedDict, total=False):
    config: Required[AutoEvaluationAgentEvaluationTaskConfigurationDesignatedToIfAgentConfig]

    agent_name: Literal["IFAgent"]


class AutoEvaluationAgentEvaluationTaskConfigurationDesignatedToTruthfulnessAgentConfig(TypedDict, total=False):
    model: str


class AutoEvaluationAgentEvaluationTaskConfigurationDesignatedToTruthfulnessAgent(TypedDict, total=False):
    config: Required[AutoEvaluationAgentEvaluationTaskConfigurationDesignatedToTruthfulnessAgentConfig]

    agent_name: Literal["TruthfulnessAgent"]


class AutoEvaluationAgentEvaluationTaskConfigurationDesignatedToBaseAgentConfig(TypedDict, total=False):
    model: str


class AutoEvaluationAgentEvaluationTaskConfigurationDesignatedToBaseAgent(TypedDict, total=False):
    config: Required[AutoEvaluationAgentEvaluationTaskConfigurationDesignatedToBaseAgentConfig]

    agent_name: Literal["BaseAgent"]


AutoEvaluationAgentEvaluationTaskConfigurationDesignatedTo: TypeAlias = Union[
    AutoEvaluationAgentEvaluationTaskConfigurationDesignatedToApeAgent,
    AutoEvaluationAgentEvaluationTaskConfigurationDesignatedToIfAgent,
    AutoEvaluationAgentEvaluationTaskConfigurationDesignatedToTruthfulnessAgent,
    AutoEvaluationAgentEvaluationTaskConfigurationDesignatedToBaseAgent,
]


class AutoEvaluationAgentEvaluationTaskConfiguration(TypedDict, total=False):
    definition: Required[str]

    name: Required[str]

    output_rules: Required[SequenceNotStr[str]]

    data_fields: SequenceNotStr[str]

    designated_to: AutoEvaluationAgentEvaluationTaskConfigurationDesignatedTo

    output_type: Literal["text", "integer", "float", "boolean"]

    output_values: SequenceNotStr[Union[str, float, bool]]


class AutoEvaluationAgentEvaluationTask(TypedDict, total=False):
    configuration: Required[AutoEvaluationAgentEvaluationTaskConfiguration]

    alias: str
    """Alias to title the results column. Defaults to the `auto_evaluation_agent`"""

    task_type: Literal["auto_evaluation.agent"]


class ContributorEvaluationQuestionTaskConfiguration(TypedDict, total=False):
    layout: Required["ContainerParam"]

    question_id: Required[str]

    queue_id: str
    """The contributor annotation queue to include this task in. Defaults to `default`"""

    required: bool
    """Whether the question is required to be answered"""


class ContributorEvaluationQuestionTask(TypedDict, total=False):
    configuration: Required[ContributorEvaluationQuestionTaskConfiguration]

    alias: str
    """Alias to title the results column.

    Defaults to the `contributor_evaluation_question`
    """

    task_type: Literal["contributor_evaluation.question"]


EvaluationTaskParam: TypeAlias = Union[
    ChatCompletionEvaluationTask,
    GenericInferenceEvaluationTask,
    ApplicationVariantV1EvaluationTask,
    AgentexOutputEvaluationTask,
    MetricEvaluationTask,
    AutoEvaluationQuestionTask,
    AutoEvaluationGuidedDecodingEvaluationTask,
    AutoEvaluationAgentEvaluationTask,
    ContributorEvaluationQuestionTask,
]

from .container_param import ContainerParam
