# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Iterable
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .._types import SequenceNotStr

__all__ = [
    "ResponseCreateParams",
    "InputUnionMember1",
    "InputUnionMember1EasyInputMessageParam",
    "InputUnionMember1EasyInputMessageParamContentUnionMember1",
    "InputUnionMember1EasyInputMessageParamContentUnionMember1ResponseInputTextParam",
    "InputUnionMember1EasyInputMessageParamContentUnionMember1ResponseInputImageParam",
    "InputUnionMember1EasyInputMessageParamContentUnionMember1ResponseInputFileParam",
    "InputUnionMember1OpenAITypesResponsesResponseInputParamMessage",
    "InputUnionMember1OpenAITypesResponsesResponseInputParamMessageContent",
    "InputUnionMember1OpenAITypesResponsesResponseInputParamMessageContentResponseInputTextParam",
    "InputUnionMember1OpenAITypesResponsesResponseInputParamMessageContentResponseInputImageParam",
    "InputUnionMember1OpenAITypesResponsesResponseInputParamMessageContentResponseInputFileParam",
    "InputUnionMember1ResponseOutputMessageParam",
    "InputUnionMember1ResponseOutputMessageParamContent",
    "InputUnionMember1ResponseOutputMessageParamContentResponseOutputTextParam",
    "InputUnionMember1ResponseOutputMessageParamContentResponseOutputTextParamAnnotation",
    "InputUnionMember1ResponseOutputMessageParamContentResponseOutputTextParamAnnotationOpenAITypesResponsesResponseOutputTextParamAnnotationFileCitation",
    "InputUnionMember1ResponseOutputMessageParamContentResponseOutputTextParamAnnotationOpenAITypesResponsesResponseOutputTextParamAnnotationURLCitation",
    "InputUnionMember1ResponseOutputMessageParamContentResponseOutputTextParamAnnotationOpenAITypesResponsesResponseOutputTextParamAnnotationContainerFileCitation",
    "InputUnionMember1ResponseOutputMessageParamContentResponseOutputTextParamAnnotationOpenAITypesResponsesResponseOutputTextParamAnnotationFilePath",
    "InputUnionMember1ResponseOutputMessageParamContentResponseOutputTextParamLogprob",
    "InputUnionMember1ResponseOutputMessageParamContentResponseOutputTextParamLogprobTopLogprob",
    "InputUnionMember1ResponseOutputMessageParamContentResponseOutputRefusalParam",
    "InputUnionMember1ResponseFileSearchToolCallParam",
    "InputUnionMember1ResponseFileSearchToolCallParamResult",
    "InputUnionMember1ResponseComputerToolCallParam",
    "InputUnionMember1ResponseComputerToolCallParamAction",
    "InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionClick",
    "InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionDoubleClick",
    "InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionDrag",
    "InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionDragPath",
    "InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionKeypress",
    "InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionMove",
    "InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionScreenshot",
    "InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionScroll",
    "InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionType",
    "InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionWait",
    "InputUnionMember1ResponseComputerToolCallParamPendingSafetyCheck",
    "InputUnionMember1OpenAITypesResponsesResponseInputParamComputerCallOutput",
    "InputUnionMember1OpenAITypesResponsesResponseInputParamComputerCallOutputOutput",
    "InputUnionMember1OpenAITypesResponsesResponseInputParamComputerCallOutputAcknowledgedSafetyCheck",
    "InputUnionMember1ResponseFunctionWebSearchParam",
    "InputUnionMember1ResponseFunctionWebSearchParamAction",
    "InputUnionMember1ResponseFunctionWebSearchParamActionOpenAITypesResponsesResponseFunctionWebSearchParamActionSearch",
    "InputUnionMember1ResponseFunctionWebSearchParamActionOpenAITypesResponsesResponseFunctionWebSearchParamActionOpenPage",
    "InputUnionMember1ResponseFunctionWebSearchParamActionOpenAITypesResponsesResponseFunctionWebSearchParamActionFind",
    "InputUnionMember1ResponseFunctionToolCallParam",
    "InputUnionMember1OpenAITypesResponsesResponseInputParamFunctionCallOutput",
    "InputUnionMember1ResponseReasoningItemParam",
    "InputUnionMember1ResponseReasoningItemParamSummary",
    "InputUnionMember1ResponseReasoningItemParamContent",
    "InputUnionMember1OpenAITypesResponsesResponseInputParamImageGenerationCall",
    "InputUnionMember1ResponseCodeInterpreterToolCallParam",
    "InputUnionMember1ResponseCodeInterpreterToolCallParamOutput",
    "InputUnionMember1ResponseCodeInterpreterToolCallParamOutputOpenAITypesResponsesResponseCodeInterpreterToolCallParamOutputLogs",
    "InputUnionMember1ResponseCodeInterpreterToolCallParamOutputOpenAITypesResponsesResponseCodeInterpreterToolCallParamOutputImage",
    "InputUnionMember1OpenAITypesResponsesResponseInputParamLocalShellCall",
    "InputUnionMember1OpenAITypesResponsesResponseInputParamLocalShellCallAction",
    "InputUnionMember1OpenAITypesResponsesResponseInputParamLocalShellCallOutput",
    "InputUnionMember1OpenAITypesResponsesResponseInputParamMcpListTools",
    "InputUnionMember1OpenAITypesResponsesResponseInputParamMcpListToolsTool",
    "InputUnionMember1OpenAITypesResponsesResponseInputParamMcpApprovalRequest",
    "InputUnionMember1OpenAITypesResponsesResponseInputParamMcpApprovalResponse",
    "InputUnionMember1OpenAITypesResponsesResponseInputParamMcpCall",
    "InputUnionMember1ResponseCustomToolCallOutputParam",
    "InputUnionMember1ResponseCustomToolCallParam",
    "InputUnionMember1OpenAITypesResponsesResponseInputParamItemReference",
]


class ResponseCreateParams(TypedDict, total=False):
    input: Required[Union[str, Iterable[InputUnionMember1]]]

    model: Required[str]
    """model specified as `model_vendor/model`, for example `openai/gpt-4o`"""

    include: SequenceNotStr[str]
    """Which fields to include in the response"""

    instructions: str
    """Instructions for the response generation"""

    max_output_tokens: int
    """Maximum number of output tokens"""

    metadata: Dict[str, object]
    """Metadata for the response"""

    parallel_tool_calls: bool
    """Whether to enable parallel tool calls"""

    previous_response_id: str
    """ID of the previous response for chaining"""

    reasoning: Dict[str, object]
    """Reasoning configuration for the response"""

    store: bool
    """Whether to store the response"""

    stream: bool
    """Whether to stream the response"""

    temperature: float
    """Sampling temperature for randomness control"""

    text: Dict[str, object]
    """Text configuration parameters"""

    tool_choice: Union[str, Dict[str, object]]
    """Tool choice configuration"""

    tools: Iterable[Dict[str, object]]
    """Tools available for the response"""

    top_p: float
    """Top-p sampling parameter"""

    truncation: Literal["auto", "disabled"]
    """Truncation configuration"""


class InputUnionMember1EasyInputMessageParamContentUnionMember1ResponseInputTextParam(TypedDict, total=False):
    text: Required[str]

    type: Required[Literal["input_text"]]


class InputUnionMember1EasyInputMessageParamContentUnionMember1ResponseInputImageParam(TypedDict, total=False):
    detail: Required[Literal["low", "high", "auto"]]

    type: Required[Literal["input_image"]]

    file_id: str

    image_url: str


class InputUnionMember1EasyInputMessageParamContentUnionMember1ResponseInputFileParam(TypedDict, total=False):
    type: Required[Literal["input_file"]]

    file_data: str

    file_id: str

    file_url: str

    filename: str


InputUnionMember1EasyInputMessageParamContentUnionMember1: TypeAlias = Union[
    InputUnionMember1EasyInputMessageParamContentUnionMember1ResponseInputTextParam,
    InputUnionMember1EasyInputMessageParamContentUnionMember1ResponseInputImageParam,
    InputUnionMember1EasyInputMessageParamContentUnionMember1ResponseInputFileParam,
]


class InputUnionMember1EasyInputMessageParam(TypedDict, total=False):
    content: Required[Union[str, Iterable[InputUnionMember1EasyInputMessageParamContentUnionMember1]]]

    role: Required[Literal["user", "assistant", "system", "developer"]]

    type: Literal["message"]


class InputUnionMember1OpenAITypesResponsesResponseInputParamMessageContentResponseInputTextParam(
    TypedDict, total=False
):
    text: Required[str]

    type: Required[Literal["input_text"]]


class InputUnionMember1OpenAITypesResponsesResponseInputParamMessageContentResponseInputImageParam(
    TypedDict, total=False
):
    detail: Required[Literal["low", "high", "auto"]]

    type: Required[Literal["input_image"]]

    file_id: str

    image_url: str


class InputUnionMember1OpenAITypesResponsesResponseInputParamMessageContentResponseInputFileParam(
    TypedDict, total=False
):
    type: Required[Literal["input_file"]]

    file_data: str

    file_id: str

    file_url: str

    filename: str


InputUnionMember1OpenAITypesResponsesResponseInputParamMessageContent: TypeAlias = Union[
    InputUnionMember1OpenAITypesResponsesResponseInputParamMessageContentResponseInputTextParam,
    InputUnionMember1OpenAITypesResponsesResponseInputParamMessageContentResponseInputImageParam,
    InputUnionMember1OpenAITypesResponsesResponseInputParamMessageContentResponseInputFileParam,
]


class InputUnionMember1OpenAITypesResponsesResponseInputParamMessage(TypedDict, total=False):
    content: Required[Iterable[InputUnionMember1OpenAITypesResponsesResponseInputParamMessageContent]]

    role: Required[Literal["user", "system", "developer"]]

    status: Literal["in_progress", "completed", "incomplete"]

    type: Literal["message"]


class InputUnionMember1ResponseOutputMessageParamContentResponseOutputTextParamAnnotationOpenAITypesResponsesResponseOutputTextParamAnnotationFileCitation(
    TypedDict, total=False
):
    file_id: Required[str]

    filename: Required[str]

    index: Required[int]

    type: Required[Literal["file_citation"]]


class InputUnionMember1ResponseOutputMessageParamContentResponseOutputTextParamAnnotationOpenAITypesResponsesResponseOutputTextParamAnnotationURLCitation(
    TypedDict, total=False
):
    end_index: Required[int]

    start_index: Required[int]

    title: Required[str]

    type: Required[Literal["url_citation"]]

    url: Required[str]


class InputUnionMember1ResponseOutputMessageParamContentResponseOutputTextParamAnnotationOpenAITypesResponsesResponseOutputTextParamAnnotationContainerFileCitation(
    TypedDict, total=False
):
    container_id: Required[str]

    end_index: Required[int]

    file_id: Required[str]

    filename: Required[str]

    start_index: Required[int]

    type: Required[Literal["container_file_citation"]]


class InputUnionMember1ResponseOutputMessageParamContentResponseOutputTextParamAnnotationOpenAITypesResponsesResponseOutputTextParamAnnotationFilePath(
    TypedDict, total=False
):
    file_id: Required[str]

    index: Required[int]

    type: Required[Literal["file_path"]]


InputUnionMember1ResponseOutputMessageParamContentResponseOutputTextParamAnnotation: TypeAlias = Union[
    InputUnionMember1ResponseOutputMessageParamContentResponseOutputTextParamAnnotationOpenAITypesResponsesResponseOutputTextParamAnnotationFileCitation,
    InputUnionMember1ResponseOutputMessageParamContentResponseOutputTextParamAnnotationOpenAITypesResponsesResponseOutputTextParamAnnotationURLCitation,
    InputUnionMember1ResponseOutputMessageParamContentResponseOutputTextParamAnnotationOpenAITypesResponsesResponseOutputTextParamAnnotationContainerFileCitation,
    InputUnionMember1ResponseOutputMessageParamContentResponseOutputTextParamAnnotationOpenAITypesResponsesResponseOutputTextParamAnnotationFilePath,
]


class InputUnionMember1ResponseOutputMessageParamContentResponseOutputTextParamLogprobTopLogprob(
    TypedDict, total=False
):
    token: Required[str]

    bytes: Required[Iterable[int]]

    logprob: Required[float]


class InputUnionMember1ResponseOutputMessageParamContentResponseOutputTextParamLogprob(TypedDict, total=False):
    token: Required[str]

    bytes: Required[Iterable[int]]

    logprob: Required[float]

    top_logprobs: Required[
        Iterable[InputUnionMember1ResponseOutputMessageParamContentResponseOutputTextParamLogprobTopLogprob]
    ]


class InputUnionMember1ResponseOutputMessageParamContentResponseOutputTextParam(TypedDict, total=False):
    annotations: Required[Iterable[InputUnionMember1ResponseOutputMessageParamContentResponseOutputTextParamAnnotation]]

    text: Required[str]

    type: Required[Literal["output_text"]]

    logprobs: Iterable[InputUnionMember1ResponseOutputMessageParamContentResponseOutputTextParamLogprob]


class InputUnionMember1ResponseOutputMessageParamContentResponseOutputRefusalParam(TypedDict, total=False):
    refusal: Required[str]

    type: Required[Literal["refusal"]]


InputUnionMember1ResponseOutputMessageParamContent: TypeAlias = Union[
    InputUnionMember1ResponseOutputMessageParamContentResponseOutputTextParam,
    InputUnionMember1ResponseOutputMessageParamContentResponseOutputRefusalParam,
]


class InputUnionMember1ResponseOutputMessageParam(TypedDict, total=False):
    id: Required[str]

    content: Required[Iterable[InputUnionMember1ResponseOutputMessageParamContent]]

    role: Required[Literal["assistant"]]

    status: Required[Literal["in_progress", "completed", "incomplete"]]

    type: Required[Literal["message"]]


class InputUnionMember1ResponseFileSearchToolCallParamResult(TypedDict, total=False):
    attributes: Dict[str, Union[str, float, bool]]

    file_id: str

    filename: str

    score: float

    text: str


class InputUnionMember1ResponseFileSearchToolCallParam(TypedDict, total=False):
    id: Required[str]

    queries: Required[SequenceNotStr[str]]

    status: Required[Literal["in_progress", "searching", "completed", "incomplete", "failed"]]

    type: Required[Literal["file_search_call"]]

    results: Iterable[InputUnionMember1ResponseFileSearchToolCallParamResult]


class InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionClick(
    TypedDict, total=False
):
    button: Required[Literal["left", "right", "wheel", "back", "forward"]]

    type: Required[Literal["click"]]

    x: Required[int]

    y: Required[int]


class InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionDoubleClick(
    TypedDict, total=False
):
    type: Required[Literal["double_click"]]

    x: Required[int]

    y: Required[int]


class InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionDragPath(
    TypedDict, total=False
):
    x: Required[int]

    y: Required[int]


class InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionDrag(
    TypedDict, total=False
):
    path: Required[
        Iterable[
            InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionDragPath
        ]
    ]

    type: Required[Literal["drag"]]


class InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionKeypress(
    TypedDict, total=False
):
    keys: Required[SequenceNotStr[str]]

    type: Required[Literal["keypress"]]


class InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionMove(
    TypedDict, total=False
):
    type: Required[Literal["move"]]

    x: Required[int]

    y: Required[int]


class InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionScreenshot(
    TypedDict, total=False
):
    type: Required[Literal["screenshot"]]


class InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionScroll(
    TypedDict, total=False
):
    scroll_x: Required[int]

    scroll_y: Required[int]

    type: Required[Literal["scroll"]]

    x: Required[int]

    y: Required[int]


class InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionType(
    TypedDict, total=False
):
    text: Required[str]

    type: Required[Literal["type"]]


class InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionWait(
    TypedDict, total=False
):
    type: Required[Literal["wait"]]


InputUnionMember1ResponseComputerToolCallParamAction: TypeAlias = Union[
    InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionClick,
    InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionDoubleClick,
    InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionDrag,
    InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionKeypress,
    InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionMove,
    InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionScreenshot,
    InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionScroll,
    InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionType,
    InputUnionMember1ResponseComputerToolCallParamActionOpenAITypesResponsesResponseComputerToolCallParamActionWait,
]


class InputUnionMember1ResponseComputerToolCallParamPendingSafetyCheck(TypedDict, total=False):
    id: Required[str]

    code: Required[str]

    message: Required[str]


class InputUnionMember1ResponseComputerToolCallParam(TypedDict, total=False):
    id: Required[str]

    action: Required[InputUnionMember1ResponseComputerToolCallParamAction]

    call_id: Required[str]

    pending_safety_checks: Required[Iterable[InputUnionMember1ResponseComputerToolCallParamPendingSafetyCheck]]

    status: Required[Literal["in_progress", "completed", "incomplete"]]

    type: Required[Literal["computer_call"]]


class InputUnionMember1OpenAITypesResponsesResponseInputParamComputerCallOutputOutput(TypedDict, total=False):
    type: Required[Literal["computer_screenshot"]]

    file_id: str

    image_url: str


class InputUnionMember1OpenAITypesResponsesResponseInputParamComputerCallOutputAcknowledgedSafetyCheck(
    TypedDict, total=False
):
    id: Required[str]

    code: str

    message: str


class InputUnionMember1OpenAITypesResponsesResponseInputParamComputerCallOutput(TypedDict, total=False):
    call_id: Required[str]

    output: Required[InputUnionMember1OpenAITypesResponsesResponseInputParamComputerCallOutputOutput]

    type: Required[Literal["computer_call_output"]]

    id: str

    acknowledged_safety_checks: Iterable[
        InputUnionMember1OpenAITypesResponsesResponseInputParamComputerCallOutputAcknowledgedSafetyCheck
    ]

    status: Literal["in_progress", "completed", "incomplete"]


class InputUnionMember1ResponseFunctionWebSearchParamActionOpenAITypesResponsesResponseFunctionWebSearchParamActionSearch(
    TypedDict, total=False
):
    query: Required[str]

    type: Required[Literal["search"]]


class InputUnionMember1ResponseFunctionWebSearchParamActionOpenAITypesResponsesResponseFunctionWebSearchParamActionOpenPage(
    TypedDict, total=False
):
    type: Required[Literal["open_page"]]

    url: Required[str]


class InputUnionMember1ResponseFunctionWebSearchParamActionOpenAITypesResponsesResponseFunctionWebSearchParamActionFind(
    TypedDict, total=False
):
    pattern: Required[str]

    type: Required[Literal["find"]]

    url: Required[str]


InputUnionMember1ResponseFunctionWebSearchParamAction: TypeAlias = Union[
    InputUnionMember1ResponseFunctionWebSearchParamActionOpenAITypesResponsesResponseFunctionWebSearchParamActionSearch,
    InputUnionMember1ResponseFunctionWebSearchParamActionOpenAITypesResponsesResponseFunctionWebSearchParamActionOpenPage,
    InputUnionMember1ResponseFunctionWebSearchParamActionOpenAITypesResponsesResponseFunctionWebSearchParamActionFind,
]


class InputUnionMember1ResponseFunctionWebSearchParam(TypedDict, total=False):
    id: Required[str]

    action: Required[InputUnionMember1ResponseFunctionWebSearchParamAction]

    status: Required[Literal["in_progress", "searching", "completed", "failed"]]

    type: Required[Literal["web_search_call"]]


class InputUnionMember1ResponseFunctionToolCallParam(TypedDict, total=False):
    arguments: Required[str]

    call_id: Required[str]

    name: Required[str]

    type: Required[Literal["function_call"]]

    id: str

    status: Literal["in_progress", "completed", "incomplete"]


class InputUnionMember1OpenAITypesResponsesResponseInputParamFunctionCallOutput(TypedDict, total=False):
    call_id: Required[str]

    output: Required[str]

    type: Required[Literal["function_call_output"]]

    id: str

    status: Literal["in_progress", "completed", "incomplete"]


class InputUnionMember1ResponseReasoningItemParamSummary(TypedDict, total=False):
    text: Required[str]

    type: Required[Literal["summary_text"]]


class InputUnionMember1ResponseReasoningItemParamContent(TypedDict, total=False):
    text: Required[str]

    type: Required[Literal["reasoning_text"]]


class InputUnionMember1ResponseReasoningItemParam(TypedDict, total=False):
    id: Required[str]

    summary: Required[Iterable[InputUnionMember1ResponseReasoningItemParamSummary]]

    type: Required[Literal["reasoning"]]

    content: Iterable[InputUnionMember1ResponseReasoningItemParamContent]

    encrypted_content: str

    status: Literal["in_progress", "completed", "incomplete"]


class InputUnionMember1OpenAITypesResponsesResponseInputParamImageGenerationCall(TypedDict, total=False):
    id: Required[str]

    result: Required[str]

    status: Required[Literal["in_progress", "completed", "generating", "failed"]]

    type: Required[Literal["image_generation_call"]]


class InputUnionMember1ResponseCodeInterpreterToolCallParamOutputOpenAITypesResponsesResponseCodeInterpreterToolCallParamOutputLogs(
    TypedDict, total=False
):
    logs: Required[str]

    type: Required[Literal["logs"]]


class InputUnionMember1ResponseCodeInterpreterToolCallParamOutputOpenAITypesResponsesResponseCodeInterpreterToolCallParamOutputImage(
    TypedDict, total=False
):
    type: Required[Literal["image"]]

    url: Required[str]


InputUnionMember1ResponseCodeInterpreterToolCallParamOutput: TypeAlias = Union[
    InputUnionMember1ResponseCodeInterpreterToolCallParamOutputOpenAITypesResponsesResponseCodeInterpreterToolCallParamOutputLogs,
    InputUnionMember1ResponseCodeInterpreterToolCallParamOutputOpenAITypesResponsesResponseCodeInterpreterToolCallParamOutputImage,
]


class InputUnionMember1ResponseCodeInterpreterToolCallParam(TypedDict, total=False):
    id: Required[str]

    code: Required[str]

    container_id: Required[str]

    outputs: Required[Iterable[InputUnionMember1ResponseCodeInterpreterToolCallParamOutput]]

    status: Required[Literal["in_progress", "completed", "incomplete", "interpreting", "failed"]]

    type: Required[Literal["code_interpreter_call"]]


class InputUnionMember1OpenAITypesResponsesResponseInputParamLocalShellCallAction(TypedDict, total=False):
    command: Required[SequenceNotStr[str]]

    env: Required[Dict[str, str]]

    type: Required[Literal["exec"]]

    timeout_ms: int

    user: str

    working_directory: str


class InputUnionMember1OpenAITypesResponsesResponseInputParamLocalShellCall(TypedDict, total=False):
    id: Required[str]

    action: Required[InputUnionMember1OpenAITypesResponsesResponseInputParamLocalShellCallAction]

    call_id: Required[str]

    status: Required[Literal["in_progress", "completed", "incomplete"]]

    type: Required[Literal["local_shell_call"]]


class InputUnionMember1OpenAITypesResponsesResponseInputParamLocalShellCallOutput(TypedDict, total=False):
    id: Required[str]

    output: Required[str]

    type: Required[Literal["local_shell_call_output"]]

    status: Literal["in_progress", "completed", "incomplete"]


class InputUnionMember1OpenAITypesResponsesResponseInputParamMcpListToolsTool(TypedDict, total=False):
    input_schema: Required[object]

    name: Required[str]

    annotations: object

    description: str


class InputUnionMember1OpenAITypesResponsesResponseInputParamMcpListTools(TypedDict, total=False):
    id: Required[str]

    server_label: Required[str]

    tools: Required[Iterable[InputUnionMember1OpenAITypesResponsesResponseInputParamMcpListToolsTool]]

    type: Required[Literal["mcp_list_tools"]]

    error: str


class InputUnionMember1OpenAITypesResponsesResponseInputParamMcpApprovalRequest(TypedDict, total=False):
    id: Required[str]

    arguments: Required[str]

    name: Required[str]

    server_label: Required[str]

    type: Required[Literal["mcp_approval_request"]]


class InputUnionMember1OpenAITypesResponsesResponseInputParamMcpApprovalResponse(TypedDict, total=False):
    approval_request_id: Required[str]

    approve: Required[bool]

    type: Required[Literal["mcp_approval_response"]]

    id: str

    reason: str


class InputUnionMember1OpenAITypesResponsesResponseInputParamMcpCall(TypedDict, total=False):
    id: Required[str]

    arguments: Required[str]

    name: Required[str]

    server_label: Required[str]

    type: Required[Literal["mcp_call"]]

    error: str

    output: str


class InputUnionMember1ResponseCustomToolCallOutputParam(TypedDict, total=False):
    call_id: Required[str]

    output: Required[str]

    type: Required[Literal["custom_tool_call_output"]]

    id: str


class InputUnionMember1ResponseCustomToolCallParam(TypedDict, total=False):
    call_id: Required[str]

    input: Required[str]

    name: Required[str]

    type: Required[Literal["custom_tool_call"]]

    id: str


class InputUnionMember1OpenAITypesResponsesResponseInputParamItemReference(TypedDict, total=False):
    id: Required[str]

    type: Literal["item_reference"]


InputUnionMember1: TypeAlias = Union[
    InputUnionMember1EasyInputMessageParam,
    InputUnionMember1OpenAITypesResponsesResponseInputParamMessage,
    InputUnionMember1ResponseOutputMessageParam,
    InputUnionMember1ResponseFileSearchToolCallParam,
    InputUnionMember1ResponseComputerToolCallParam,
    InputUnionMember1OpenAITypesResponsesResponseInputParamComputerCallOutput,
    InputUnionMember1ResponseFunctionWebSearchParam,
    InputUnionMember1ResponseFunctionToolCallParam,
    InputUnionMember1OpenAITypesResponsesResponseInputParamFunctionCallOutput,
    InputUnionMember1ResponseReasoningItemParam,
    InputUnionMember1OpenAITypesResponsesResponseInputParamImageGenerationCall,
    InputUnionMember1ResponseCodeInterpreterToolCallParam,
    InputUnionMember1OpenAITypesResponsesResponseInputParamLocalShellCall,
    InputUnionMember1OpenAITypesResponsesResponseInputParamLocalShellCallOutput,
    InputUnionMember1OpenAITypesResponsesResponseInputParamMcpListTools,
    InputUnionMember1OpenAITypesResponsesResponseInputParamMcpApprovalRequest,
    InputUnionMember1OpenAITypesResponsesResponseInputParamMcpApprovalResponse,
    InputUnionMember1OpenAITypesResponsesResponseInputParamMcpCall,
    InputUnionMember1ResponseCustomToolCallOutputParam,
    InputUnionMember1ResponseCustomToolCallParam,
    InputUnionMember1OpenAITypesResponsesResponseInputParamItemReference,
]
