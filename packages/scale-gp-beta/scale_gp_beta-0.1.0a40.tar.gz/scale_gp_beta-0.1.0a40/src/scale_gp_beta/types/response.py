# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

import builtins
from typing import TYPE_CHECKING, Dict, List, Union, Optional
from typing_extensions import Literal, TypeAlias

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = [
    "Response",
    "Output",
    "OutputResponseOutputMessage",
    "OutputResponseOutputMessageContent",
    "OutputResponseOutputMessageContentResponseOutputText",
    "OutputResponseOutputMessageContentResponseOutputTextAnnotation",
    "OutputResponseOutputMessageContentResponseOutputTextAnnotationOpenAITypesResponsesResponseOutputTextAnnotationFileCitation",
    "OutputResponseOutputMessageContentResponseOutputTextAnnotationOpenAITypesResponsesResponseOutputTextAnnotationURLCitation",
    "OutputResponseOutputMessageContentResponseOutputTextAnnotationOpenAITypesResponsesResponseOutputTextAnnotationContainerFileCitation",
    "OutputResponseOutputMessageContentResponseOutputTextAnnotationOpenAITypesResponsesResponseOutputTextAnnotationFilePath",
    "OutputResponseOutputMessageContentResponseOutputTextLogprob",
    "OutputResponseOutputMessageContentResponseOutputTextLogprobTopLogprob",
    "OutputResponseOutputMessageContentResponseOutputRefusal",
    "OutputResponseFileSearchToolCall",
    "OutputResponseFileSearchToolCallResult",
    "OutputResponseFunctionToolCall",
    "OutputResponseFunctionWebSearch",
    "OutputResponseFunctionWebSearchAction",
    "OutputResponseFunctionWebSearchActionOpenAITypesResponsesResponseFunctionWebSearchActionSearch",
    "OutputResponseFunctionWebSearchActionOpenAITypesResponsesResponseFunctionWebSearchActionOpenPage",
    "OutputResponseFunctionWebSearchActionOpenAITypesResponsesResponseFunctionWebSearchActionFind",
    "OutputResponseComputerToolCall",
    "OutputResponseComputerToolCallAction",
    "OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionClick",
    "OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionDoubleClick",
    "OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionDrag",
    "OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionDragPath",
    "OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionKeypress",
    "OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionMove",
    "OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionScreenshot",
    "OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionScroll",
    "OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionType",
    "OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionWait",
    "OutputResponseComputerToolCallPendingSafetyCheck",
    "OutputResponseReasoningItem",
    "OutputResponseReasoningItemSummary",
    "OutputResponseReasoningItemContent",
    "OutputOpenAITypesResponsesResponseOutputItemImageGenerationCall",
    "OutputResponseCodeInterpreterToolCall",
    "OutputResponseCodeInterpreterToolCallOutput",
    "OutputResponseCodeInterpreterToolCallOutputOpenAITypesResponsesResponseCodeInterpreterToolCallOutputLogs",
    "OutputResponseCodeInterpreterToolCallOutputOpenAITypesResponsesResponseCodeInterpreterToolCallOutputImage",
    "OutputOpenAITypesResponsesResponseOutputItemLocalShellCall",
    "OutputOpenAITypesResponsesResponseOutputItemLocalShellCallAction",
    "OutputOpenAITypesResponsesResponseOutputItemMcpCall",
    "OutputOpenAITypesResponsesResponseOutputItemMcpListTools",
    "OutputOpenAITypesResponsesResponseOutputItemMcpListToolsTool",
    "OutputOpenAITypesResponsesResponseOutputItemMcpApprovalRequest",
    "OutputResponseCustomToolCall",
    "ToolChoice",
    "ToolChoiceToolChoiceAllowed",
    "ToolChoiceToolChoiceTypes",
    "ToolChoiceToolChoiceFunction",
    "ToolChoiceToolChoiceMcp",
    "ToolChoiceToolChoiceCustom",
    "Tool",
    "ToolFunctionTool",
    "ToolFileSearchTool",
    "ToolFileSearchToolFilters",
    "ToolFileSearchToolFiltersComparisonFilter",
    "ToolFileSearchToolFiltersCompoundFilter",
    "ToolFileSearchToolFiltersCompoundFilterFilter",
    "ToolFileSearchToolFiltersCompoundFilterFilterComparisonFilter",
    "ToolFileSearchToolRankingOptions",
    "ToolWebSearchTool",
    "ToolWebSearchToolUserLocation",
    "ToolComputerTool",
    "ToolMcp",
    "ToolMcpAllowedTools",
    "ToolMcpAllowedToolsMcpAllowedToolsMcpAllowedToolsFilter",
    "ToolMcpRequireApproval",
    "ToolMcpRequireApprovalMcpRequireApprovalMcpToolApprovalFilter",
    "ToolMcpRequireApprovalMcpRequireApprovalMcpToolApprovalFilterAlways",
    "ToolMcpRequireApprovalMcpRequireApprovalMcpToolApprovalFilterNever",
    "ToolCodeInterpreter",
    "ToolCodeInterpreterContainer",
    "ToolCodeInterpreterContainerCodeInterpreterContainerCodeInterpreterToolAuto",
    "ToolImageGeneration",
    "ToolImageGenerationInputImageMask",
    "ToolLocalShell",
    "ToolCustomTool",
    "ToolCustomToolFormat",
    "ToolCustomToolFormatText",
    "ToolCustomToolFormatGrammar",
    "Error",
    "IncompleteDetails",
    "InstructionsUnionMember1",
    "InstructionsUnionMember1EasyInputMessage",
    "InstructionsUnionMember1EasyInputMessageContentUnionMember1",
    "InstructionsUnionMember1EasyInputMessageContentUnionMember1ResponseInputText",
    "InstructionsUnionMember1EasyInputMessageContentUnionMember1ResponseInputImage",
    "InstructionsUnionMember1EasyInputMessageContentUnionMember1ResponseInputFile",
    "InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMessage",
    "InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMessageContent",
    "InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMessageContentResponseInputText",
    "InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMessageContentResponseInputImage",
    "InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMessageContentResponseInputFile",
    "InstructionsUnionMember1ResponseOutputMessage",
    "InstructionsUnionMember1ResponseOutputMessageContent",
    "InstructionsUnionMember1ResponseOutputMessageContentResponseOutputText",
    "InstructionsUnionMember1ResponseOutputMessageContentResponseOutputTextAnnotation",
    "InstructionsUnionMember1ResponseOutputMessageContentResponseOutputTextAnnotationOpenAITypesResponsesResponseOutputTextAnnotationFileCitation",
    "InstructionsUnionMember1ResponseOutputMessageContentResponseOutputTextAnnotationOpenAITypesResponsesResponseOutputTextAnnotationURLCitation",
    "InstructionsUnionMember1ResponseOutputMessageContentResponseOutputTextAnnotationOpenAITypesResponsesResponseOutputTextAnnotationContainerFileCitation",
    "InstructionsUnionMember1ResponseOutputMessageContentResponseOutputTextAnnotationOpenAITypesResponsesResponseOutputTextAnnotationFilePath",
    "InstructionsUnionMember1ResponseOutputMessageContentResponseOutputTextLogprob",
    "InstructionsUnionMember1ResponseOutputMessageContentResponseOutputTextLogprobTopLogprob",
    "InstructionsUnionMember1ResponseOutputMessageContentResponseOutputRefusal",
    "InstructionsUnionMember1ResponseFileSearchToolCall",
    "InstructionsUnionMember1ResponseFileSearchToolCallResult",
    "InstructionsUnionMember1ResponseComputerToolCall",
    "InstructionsUnionMember1ResponseComputerToolCallAction",
    "InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionClick",
    "InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionDoubleClick",
    "InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionDrag",
    "InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionDragPath",
    "InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionKeypress",
    "InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionMove",
    "InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionScreenshot",
    "InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionScroll",
    "InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionType",
    "InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionWait",
    "InstructionsUnionMember1ResponseComputerToolCallPendingSafetyCheck",
    "InstructionsUnionMember1OpenAITypesResponsesResponseInputItemComputerCallOutput",
    "InstructionsUnionMember1OpenAITypesResponsesResponseInputItemComputerCallOutputOutput",
    "InstructionsUnionMember1OpenAITypesResponsesResponseInputItemComputerCallOutputAcknowledgedSafetyCheck",
    "InstructionsUnionMember1ResponseFunctionWebSearch",
    "InstructionsUnionMember1ResponseFunctionWebSearchAction",
    "InstructionsUnionMember1ResponseFunctionWebSearchActionOpenAITypesResponsesResponseFunctionWebSearchActionSearch",
    "InstructionsUnionMember1ResponseFunctionWebSearchActionOpenAITypesResponsesResponseFunctionWebSearchActionOpenPage",
    "InstructionsUnionMember1ResponseFunctionWebSearchActionOpenAITypesResponsesResponseFunctionWebSearchActionFind",
    "InstructionsUnionMember1ResponseFunctionToolCall",
    "InstructionsUnionMember1OpenAITypesResponsesResponseInputItemFunctionCallOutput",
    "InstructionsUnionMember1ResponseReasoningItem",
    "InstructionsUnionMember1ResponseReasoningItemSummary",
    "InstructionsUnionMember1ResponseReasoningItemContent",
    "InstructionsUnionMember1OpenAITypesResponsesResponseInputItemImageGenerationCall",
    "InstructionsUnionMember1ResponseCodeInterpreterToolCall",
    "InstructionsUnionMember1ResponseCodeInterpreterToolCallOutput",
    "InstructionsUnionMember1ResponseCodeInterpreterToolCallOutputOpenAITypesResponsesResponseCodeInterpreterToolCallOutputLogs",
    "InstructionsUnionMember1ResponseCodeInterpreterToolCallOutputOpenAITypesResponsesResponseCodeInterpreterToolCallOutputImage",
    "InstructionsUnionMember1OpenAITypesResponsesResponseInputItemLocalShellCall",
    "InstructionsUnionMember1OpenAITypesResponsesResponseInputItemLocalShellCallAction",
    "InstructionsUnionMember1OpenAITypesResponsesResponseInputItemLocalShellCallOutput",
    "InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMcpListTools",
    "InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMcpListToolsTool",
    "InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMcpApprovalRequest",
    "InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMcpApprovalResponse",
    "InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMcpCall",
    "InstructionsUnionMember1ResponseCustomToolCallOutput",
    "InstructionsUnionMember1ResponseCustomToolCall",
    "InstructionsUnionMember1OpenAITypesResponsesResponseInputItemItemReference",
    "Prompt",
    "PromptVariables",
    "PromptVariablesResponseInputText",
    "PromptVariablesResponseInputImage",
    "PromptVariablesResponseInputFile",
    "Reasoning",
    "Text",
    "TextFormat",
    "TextFormatResponseFormatText",
    "TextFormatResponseFormatTextJsonSchemaConfig",
    "TextFormatResponseFormatJsonObject",
    "Usage",
    "UsageInputTokensDetails",
    "UsageOutputTokensDetails",
]


class OutputResponseOutputMessageContentResponseOutputTextAnnotationOpenAITypesResponsesResponseOutputTextAnnotationFileCitation(
    BaseModel
):
    file_id: str

    filename: str

    index: int

    type: Literal["file_citation"]

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


class OutputResponseOutputMessageContentResponseOutputTextAnnotationOpenAITypesResponsesResponseOutputTextAnnotationURLCitation(
    BaseModel
):
    end_index: int

    start_index: int

    title: str

    type: Literal["url_citation"]

    url: str

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


class OutputResponseOutputMessageContentResponseOutputTextAnnotationOpenAITypesResponsesResponseOutputTextAnnotationContainerFileCitation(
    BaseModel
):
    container_id: str

    end_index: int

    file_id: str

    filename: str

    start_index: int

    type: Literal["container_file_citation"]

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


class OutputResponseOutputMessageContentResponseOutputTextAnnotationOpenAITypesResponsesResponseOutputTextAnnotationFilePath(
    BaseModel
):
    file_id: str

    index: int

    type: Literal["file_path"]

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


OutputResponseOutputMessageContentResponseOutputTextAnnotation: TypeAlias = Union[
    OutputResponseOutputMessageContentResponseOutputTextAnnotationOpenAITypesResponsesResponseOutputTextAnnotationFileCitation,
    OutputResponseOutputMessageContentResponseOutputTextAnnotationOpenAITypesResponsesResponseOutputTextAnnotationURLCitation,
    OutputResponseOutputMessageContentResponseOutputTextAnnotationOpenAITypesResponsesResponseOutputTextAnnotationContainerFileCitation,
    OutputResponseOutputMessageContentResponseOutputTextAnnotationOpenAITypesResponsesResponseOutputTextAnnotationFilePath,
]


class OutputResponseOutputMessageContentResponseOutputTextLogprobTopLogprob(BaseModel):
    token: str

    bytes: List[int]

    logprob: float

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


class OutputResponseOutputMessageContentResponseOutputTextLogprob(BaseModel):
    token: str

    bytes: List[int]

    logprob: float

    top_logprobs: List[OutputResponseOutputMessageContentResponseOutputTextLogprobTopLogprob]

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


class OutputResponseOutputMessageContentResponseOutputText(BaseModel):
    annotations: List[OutputResponseOutputMessageContentResponseOutputTextAnnotation]

    text: str

    type: Literal["output_text"]

    logprobs: Optional[List[OutputResponseOutputMessageContentResponseOutputTextLogprob]] = None

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


class OutputResponseOutputMessageContentResponseOutputRefusal(BaseModel):
    refusal: str

    type: Literal["refusal"]

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


OutputResponseOutputMessageContent: TypeAlias = Union[
    OutputResponseOutputMessageContentResponseOutputText, OutputResponseOutputMessageContentResponseOutputRefusal
]


class OutputResponseOutputMessage(BaseModel):
    id: str

    content: List[OutputResponseOutputMessageContent]

    role: Literal["assistant"]

    status: Literal["in_progress", "completed", "incomplete"]

    type: Literal["message"]

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


class OutputResponseFileSearchToolCallResult(BaseModel):
    attributes: Optional[Dict[str, Union[str, float, bool]]] = None

    file_id: Optional[str] = None

    filename: Optional[str] = None

    score: Optional[float] = None

    text: Optional[str] = None

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


class OutputResponseFileSearchToolCall(BaseModel):
    id: str

    queries: List[str]

    status: Literal["in_progress", "searching", "completed", "incomplete", "failed"]

    type: Literal["file_search_call"]

    results: Optional[List[OutputResponseFileSearchToolCallResult]] = None

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


class OutputResponseFunctionToolCall(BaseModel):
    arguments: str

    call_id: str

    name: str

    type: Literal["function_call"]

    id: Optional[str] = None

    status: Optional[Literal["in_progress", "completed", "incomplete"]] = None

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


class OutputResponseFunctionWebSearchActionOpenAITypesResponsesResponseFunctionWebSearchActionSearch(BaseModel):
    query: str

    type: Literal["search"]

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


class OutputResponseFunctionWebSearchActionOpenAITypesResponsesResponseFunctionWebSearchActionOpenPage(BaseModel):
    type: Literal["open_page"]

    url: str

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


class OutputResponseFunctionWebSearchActionOpenAITypesResponsesResponseFunctionWebSearchActionFind(BaseModel):
    pattern: str

    type: Literal["find"]

    url: str

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


OutputResponseFunctionWebSearchAction: TypeAlias = Union[
    OutputResponseFunctionWebSearchActionOpenAITypesResponsesResponseFunctionWebSearchActionSearch,
    OutputResponseFunctionWebSearchActionOpenAITypesResponsesResponseFunctionWebSearchActionOpenPage,
    OutputResponseFunctionWebSearchActionOpenAITypesResponsesResponseFunctionWebSearchActionFind,
]


class OutputResponseFunctionWebSearch(BaseModel):
    id: str

    action: OutputResponseFunctionWebSearchAction

    status: Literal["in_progress", "searching", "completed", "failed"]

    type: Literal["web_search_call"]

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


class OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionClick(BaseModel):
    button: Literal["left", "right", "wheel", "back", "forward"]

    type: Literal["click"]

    x: int

    y: int

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


class OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionDoubleClick(BaseModel):
    type: Literal["double_click"]

    x: int

    y: int

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


class OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionDragPath(BaseModel):
    x: int

    y: int

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


class OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionDrag(BaseModel):
    path: List[OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionDragPath]

    type: Literal["drag"]

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


class OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionKeypress(BaseModel):
    keys: List[str]

    type: Literal["keypress"]

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


class OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionMove(BaseModel):
    type: Literal["move"]

    x: int

    y: int

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


class OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionScreenshot(BaseModel):
    type: Literal["screenshot"]

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


class OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionScroll(BaseModel):
    scroll_x: int

    scroll_y: int

    type: Literal["scroll"]

    x: int

    y: int

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


class OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionType(BaseModel):
    text: str

    type: Literal["type"]

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


class OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionWait(BaseModel):
    type: Literal["wait"]

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


OutputResponseComputerToolCallAction: TypeAlias = Union[
    OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionClick,
    OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionDoubleClick,
    OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionDrag,
    OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionKeypress,
    OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionMove,
    OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionScreenshot,
    OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionScroll,
    OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionType,
    OutputResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionWait,
]


class OutputResponseComputerToolCallPendingSafetyCheck(BaseModel):
    id: str

    code: str

    message: str

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


class OutputResponseComputerToolCall(BaseModel):
    id: str

    action: OutputResponseComputerToolCallAction

    call_id: str

    pending_safety_checks: List[OutputResponseComputerToolCallPendingSafetyCheck]

    status: Literal["in_progress", "completed", "incomplete"]

    type: Literal["computer_call"]

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


class OutputResponseReasoningItemSummary(BaseModel):
    text: str

    type: Literal["summary_text"]

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


class OutputResponseReasoningItemContent(BaseModel):
    text: str

    type: Literal["reasoning_text"]

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


class OutputResponseReasoningItem(BaseModel):
    id: str

    summary: List[OutputResponseReasoningItemSummary]

    type: Literal["reasoning"]

    content: Optional[List[OutputResponseReasoningItemContent]] = None

    encrypted_content: Optional[str] = None

    status: Optional[Literal["in_progress", "completed", "incomplete"]] = None

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


class OutputOpenAITypesResponsesResponseOutputItemImageGenerationCall(BaseModel):
    id: str

    status: Literal["in_progress", "completed", "generating", "failed"]

    type: Literal["image_generation_call"]

    result: Optional[str] = None

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


class OutputResponseCodeInterpreterToolCallOutputOpenAITypesResponsesResponseCodeInterpreterToolCallOutputLogs(
    BaseModel
):
    logs: str

    type: Literal["logs"]

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


class OutputResponseCodeInterpreterToolCallOutputOpenAITypesResponsesResponseCodeInterpreterToolCallOutputImage(
    BaseModel
):
    type: Literal["image"]

    url: str

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


OutputResponseCodeInterpreterToolCallOutput: TypeAlias = Union[
    OutputResponseCodeInterpreterToolCallOutputOpenAITypesResponsesResponseCodeInterpreterToolCallOutputLogs,
    OutputResponseCodeInterpreterToolCallOutputOpenAITypesResponsesResponseCodeInterpreterToolCallOutputImage,
]


class OutputResponseCodeInterpreterToolCall(BaseModel):
    id: str

    container_id: str

    status: Literal["in_progress", "completed", "incomplete", "interpreting", "failed"]

    type: Literal["code_interpreter_call"]

    code: Optional[str] = None

    outputs: Optional[List[OutputResponseCodeInterpreterToolCallOutput]] = None

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


class OutputOpenAITypesResponsesResponseOutputItemLocalShellCallAction(BaseModel):
    command: List[str]

    env: Dict[str, str]

    type: Literal["exec"]

    timeout_ms: Optional[int] = None

    user: Optional[str] = None

    working_directory: Optional[str] = None

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


class OutputOpenAITypesResponsesResponseOutputItemLocalShellCall(BaseModel):
    id: str

    action: OutputOpenAITypesResponsesResponseOutputItemLocalShellCallAction

    call_id: str

    status: Literal["in_progress", "completed", "incomplete"]

    type: Literal["local_shell_call"]

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


class OutputOpenAITypesResponsesResponseOutputItemMcpCall(BaseModel):
    id: str

    arguments: str

    name: str

    server_label: str

    type: Literal["mcp_call"]

    error: Optional[str] = None

    output: Optional[str] = None

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


class OutputOpenAITypesResponsesResponseOutputItemMcpListToolsTool(BaseModel):
    input_schema: object

    name: str

    annotations: Optional[object] = None

    description: Optional[str] = None

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


class OutputOpenAITypesResponsesResponseOutputItemMcpListTools(BaseModel):
    id: str

    server_label: str

    tools: List[OutputOpenAITypesResponsesResponseOutputItemMcpListToolsTool]

    type: Literal["mcp_list_tools"]

    error: Optional[str] = None

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


class OutputOpenAITypesResponsesResponseOutputItemMcpApprovalRequest(BaseModel):
    id: str

    arguments: str

    name: str

    server_label: str

    type: Literal["mcp_approval_request"]

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


class OutputResponseCustomToolCall(BaseModel):
    call_id: str

    input: str

    name: str

    type: Literal["custom_tool_call"]

    id: Optional[str] = None

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


Output: TypeAlias = Union[
    OutputResponseOutputMessage,
    OutputResponseFileSearchToolCall,
    OutputResponseFunctionToolCall,
    OutputResponseFunctionWebSearch,
    OutputResponseComputerToolCall,
    OutputResponseReasoningItem,
    OutputOpenAITypesResponsesResponseOutputItemImageGenerationCall,
    OutputResponseCodeInterpreterToolCall,
    OutputOpenAITypesResponsesResponseOutputItemLocalShellCall,
    OutputOpenAITypesResponsesResponseOutputItemMcpCall,
    OutputOpenAITypesResponsesResponseOutputItemMcpListTools,
    OutputOpenAITypesResponsesResponseOutputItemMcpApprovalRequest,
    OutputResponseCustomToolCall,
]


class ToolChoiceToolChoiceAllowed(BaseModel):
    mode: Literal["auto", "required"]

    tools: List[Dict[str, object]]

    type: Literal["allowed_tools"]

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


class ToolChoiceToolChoiceTypes(BaseModel):
    type: Literal[
        "file_search",
        "web_search_preview",
        "computer_use_preview",
        "web_search_preview_2025_03_11",
        "image_generation",
        "code_interpreter",
    ]

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


class ToolChoiceToolChoiceFunction(BaseModel):
    name: str

    type: Literal["function"]

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


class ToolChoiceToolChoiceMcp(BaseModel):
    server_label: str

    type: Literal["mcp"]

    name: Optional[str] = None

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


class ToolChoiceToolChoiceCustom(BaseModel):
    name: str

    type: Literal["custom"]

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


ToolChoice: TypeAlias = Union[
    Literal["none", "auto", "required"],
    ToolChoiceToolChoiceAllowed,
    ToolChoiceToolChoiceTypes,
    ToolChoiceToolChoiceFunction,
    ToolChoiceToolChoiceMcp,
    ToolChoiceToolChoiceCustom,
]


class ToolFunctionTool(BaseModel):
    name: str

    type: Literal["function"]

    description: Optional[str] = None

    parameters: Optional[Dict[str, object]] = None

    strict: Optional[bool] = None

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


class ToolFileSearchToolFiltersComparisonFilter(BaseModel):
    key: str

    type: Literal["eq", "ne", "gt", "gte", "lt", "lte"]

    value: Union[str, float, bool]

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


class ToolFileSearchToolFiltersCompoundFilterFilterComparisonFilter(BaseModel):
    key: str

    type: Literal["eq", "ne", "gt", "gte", "lt", "lte"]

    value: Union[str, float, bool]

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


ToolFileSearchToolFiltersCompoundFilterFilter: TypeAlias = Union[
    ToolFileSearchToolFiltersCompoundFilterFilterComparisonFilter, object
]


class ToolFileSearchToolFiltersCompoundFilter(BaseModel):
    filters: List[ToolFileSearchToolFiltersCompoundFilterFilter]

    type: Literal["and", "or"]

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


ToolFileSearchToolFilters: TypeAlias = Union[
    ToolFileSearchToolFiltersComparisonFilter, ToolFileSearchToolFiltersCompoundFilter
]


class ToolFileSearchToolRankingOptions(BaseModel):
    ranker: Optional[Literal["auto", "default-2024-11-15"]] = None

    score_threshold: Optional[float] = None

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


class ToolFileSearchTool(BaseModel):
    type: Literal["file_search"]

    vector_store_ids: List[str]

    filters: Optional[ToolFileSearchToolFilters] = None

    max_num_results: Optional[int] = None

    ranking_options: Optional[ToolFileSearchToolRankingOptions] = None

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


class ToolWebSearchToolUserLocation(BaseModel):
    type: Literal["approximate"]

    city: Optional[str] = None

    country: Optional[str] = None

    region: Optional[str] = None

    timezone: Optional[str] = None

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


class ToolWebSearchTool(BaseModel):
    type: Literal["web_search_preview", "web_search_preview_2025_03_11"]

    search_context_size: Optional[Literal["low", "medium", "high"]] = None

    user_location: Optional[ToolWebSearchToolUserLocation] = None

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


class ToolComputerTool(BaseModel):
    display_height: int

    display_width: int

    environment: Literal["windows", "mac", "linux", "ubuntu", "browser"]

    type: Literal["computer_use_preview"]

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


class ToolMcpAllowedToolsMcpAllowedToolsMcpAllowedToolsFilter(BaseModel):
    tool_names: Optional[List[str]] = None

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


ToolMcpAllowedTools: TypeAlias = Union[List[str], ToolMcpAllowedToolsMcpAllowedToolsMcpAllowedToolsFilter]


class ToolMcpRequireApprovalMcpRequireApprovalMcpToolApprovalFilterAlways(BaseModel):
    tool_names: Optional[List[str]] = None

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


class ToolMcpRequireApprovalMcpRequireApprovalMcpToolApprovalFilterNever(BaseModel):
    tool_names: Optional[List[str]] = None

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


class ToolMcpRequireApprovalMcpRequireApprovalMcpToolApprovalFilter(BaseModel):
    always: Optional[ToolMcpRequireApprovalMcpRequireApprovalMcpToolApprovalFilterAlways] = None

    never: Optional[ToolMcpRequireApprovalMcpRequireApprovalMcpToolApprovalFilterNever] = None

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


ToolMcpRequireApproval: TypeAlias = Union[
    ToolMcpRequireApprovalMcpRequireApprovalMcpToolApprovalFilter, Literal["always", "never"]
]


class ToolMcp(BaseModel):
    server_label: str

    server_url: str

    type: Literal["mcp"]

    allowed_tools: Optional[ToolMcpAllowedTools] = None

    headers: Optional[Dict[str, str]] = None

    require_approval: Optional[ToolMcpRequireApproval] = None

    server_description: Optional[str] = None

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


class ToolCodeInterpreterContainerCodeInterpreterContainerCodeInterpreterToolAuto(BaseModel):
    type: Literal["auto"]

    file_ids: Optional[List[str]] = None

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


ToolCodeInterpreterContainer: TypeAlias = Union[
    str, ToolCodeInterpreterContainerCodeInterpreterContainerCodeInterpreterToolAuto
]


class ToolCodeInterpreter(BaseModel):
    container: ToolCodeInterpreterContainer

    type: Literal["code_interpreter"]

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


class ToolImageGenerationInputImageMask(BaseModel):
    file_id: Optional[str] = None

    image_url: Optional[str] = None

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


class ToolImageGeneration(BaseModel):
    type: Literal["image_generation"]

    background: Optional[Literal["transparent", "opaque", "auto"]] = None

    input_fidelity: Optional[Literal["high", "low"]] = None

    input_image_mask: Optional[ToolImageGenerationInputImageMask] = None

    model: Optional[Literal["gpt-image-1"]] = None

    moderation: Optional[Literal["auto", "low"]] = None

    output_compression: Optional[int] = None

    output_format: Optional[Literal["png", "webp", "jpeg"]] = None

    partial_images: Optional[int] = None

    quality: Optional[Literal["low", "medium", "high", "auto"]] = None

    size: Optional[Literal["1024x1024", "1024x1536", "1536x1024", "auto"]] = None

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


class ToolLocalShell(BaseModel):
    type: Literal["local_shell"]

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


class ToolCustomToolFormatText(BaseModel):
    type: Literal["text"]

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


class ToolCustomToolFormatGrammar(BaseModel):
    definition: str

    syntax: Literal["lark", "regex"]

    type: Literal["grammar"]

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


ToolCustomToolFormat: TypeAlias = Union[ToolCustomToolFormatText, ToolCustomToolFormatGrammar]


class ToolCustomTool(BaseModel):
    name: str

    type: Literal["custom"]

    description: Optional[str] = None

    format: Optional[ToolCustomToolFormat] = None

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


Tool: TypeAlias = Union[
    ToolFunctionTool,
    ToolFileSearchTool,
    ToolWebSearchTool,
    ToolComputerTool,
    ToolMcp,
    ToolCodeInterpreter,
    ToolImageGeneration,
    ToolLocalShell,
    ToolCustomTool,
]


class Error(BaseModel):
    code: Literal[
        "server_error",
        "rate_limit_exceeded",
        "invalid_prompt",
        "vector_store_timeout",
        "invalid_image",
        "invalid_image_format",
        "invalid_base64_image",
        "invalid_image_url",
        "image_too_large",
        "image_too_small",
        "image_parse_error",
        "image_content_policy_violation",
        "invalid_image_mode",
        "image_file_too_large",
        "unsupported_image_media_type",
        "empty_image_file",
        "failed_to_download_image",
        "image_file_not_found",
    ]

    message: str

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


class IncompleteDetails(BaseModel):
    reason: Optional[Literal["max_output_tokens", "content_filter"]] = None

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


class InstructionsUnionMember1EasyInputMessageContentUnionMember1ResponseInputText(BaseModel):
    text: str

    type: Literal["input_text"]

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


class InstructionsUnionMember1EasyInputMessageContentUnionMember1ResponseInputImage(BaseModel):
    detail: Literal["low", "high", "auto"]

    type: Literal["input_image"]

    file_id: Optional[str] = None

    image_url: Optional[str] = None

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


class InstructionsUnionMember1EasyInputMessageContentUnionMember1ResponseInputFile(BaseModel):
    type: Literal["input_file"]

    file_data: Optional[str] = None

    file_id: Optional[str] = None

    file_url: Optional[str] = None

    filename: Optional[str] = None

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


InstructionsUnionMember1EasyInputMessageContentUnionMember1: TypeAlias = Union[
    InstructionsUnionMember1EasyInputMessageContentUnionMember1ResponseInputText,
    InstructionsUnionMember1EasyInputMessageContentUnionMember1ResponseInputImage,
    InstructionsUnionMember1EasyInputMessageContentUnionMember1ResponseInputFile,
]


class InstructionsUnionMember1EasyInputMessage(BaseModel):
    content: Union[str, List[InstructionsUnionMember1EasyInputMessageContentUnionMember1]]

    role: Literal["user", "assistant", "system", "developer"]

    type: Optional[Literal["message"]] = None

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


class InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMessageContentResponseInputText(BaseModel):
    text: str

    type: Literal["input_text"]

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


class InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMessageContentResponseInputImage(BaseModel):
    detail: Literal["low", "high", "auto"]

    type: Literal["input_image"]

    file_id: Optional[str] = None

    image_url: Optional[str] = None

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


class InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMessageContentResponseInputFile(BaseModel):
    type: Literal["input_file"]

    file_data: Optional[str] = None

    file_id: Optional[str] = None

    file_url: Optional[str] = None

    filename: Optional[str] = None

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


InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMessageContent: TypeAlias = Union[
    InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMessageContentResponseInputText,
    InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMessageContentResponseInputImage,
    InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMessageContentResponseInputFile,
]


class InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMessage(BaseModel):
    content: List[InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMessageContent]

    role: Literal["user", "system", "developer"]

    status: Optional[Literal["in_progress", "completed", "incomplete"]] = None

    type: Optional[Literal["message"]] = None

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


class InstructionsUnionMember1ResponseOutputMessageContentResponseOutputTextAnnotationOpenAITypesResponsesResponseOutputTextAnnotationFileCitation(
    BaseModel
):
    file_id: str

    filename: str

    index: int

    type: Literal["file_citation"]

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


class InstructionsUnionMember1ResponseOutputMessageContentResponseOutputTextAnnotationOpenAITypesResponsesResponseOutputTextAnnotationURLCitation(
    BaseModel
):
    end_index: int

    start_index: int

    title: str

    type: Literal["url_citation"]

    url: str

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


class InstructionsUnionMember1ResponseOutputMessageContentResponseOutputTextAnnotationOpenAITypesResponsesResponseOutputTextAnnotationContainerFileCitation(
    BaseModel
):
    container_id: str

    end_index: int

    file_id: str

    filename: str

    start_index: int

    type: Literal["container_file_citation"]

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


class InstructionsUnionMember1ResponseOutputMessageContentResponseOutputTextAnnotationOpenAITypesResponsesResponseOutputTextAnnotationFilePath(
    BaseModel
):
    file_id: str

    index: int

    type: Literal["file_path"]

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


InstructionsUnionMember1ResponseOutputMessageContentResponseOutputTextAnnotation: TypeAlias = Union[
    InstructionsUnionMember1ResponseOutputMessageContentResponseOutputTextAnnotationOpenAITypesResponsesResponseOutputTextAnnotationFileCitation,
    InstructionsUnionMember1ResponseOutputMessageContentResponseOutputTextAnnotationOpenAITypesResponsesResponseOutputTextAnnotationURLCitation,
    InstructionsUnionMember1ResponseOutputMessageContentResponseOutputTextAnnotationOpenAITypesResponsesResponseOutputTextAnnotationContainerFileCitation,
    InstructionsUnionMember1ResponseOutputMessageContentResponseOutputTextAnnotationOpenAITypesResponsesResponseOutputTextAnnotationFilePath,
]


class InstructionsUnionMember1ResponseOutputMessageContentResponseOutputTextLogprobTopLogprob(BaseModel):
    token: str

    bytes: List[int]

    logprob: float

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


class InstructionsUnionMember1ResponseOutputMessageContentResponseOutputTextLogprob(BaseModel):
    token: str

    bytes: List[int]

    logprob: float

    top_logprobs: List[InstructionsUnionMember1ResponseOutputMessageContentResponseOutputTextLogprobTopLogprob]

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


class InstructionsUnionMember1ResponseOutputMessageContentResponseOutputText(BaseModel):
    annotations: List[InstructionsUnionMember1ResponseOutputMessageContentResponseOutputTextAnnotation]

    text: str

    type: Literal["output_text"]

    logprobs: Optional[List[InstructionsUnionMember1ResponseOutputMessageContentResponseOutputTextLogprob]] = None

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


class InstructionsUnionMember1ResponseOutputMessageContentResponseOutputRefusal(BaseModel):
    refusal: str

    type: Literal["refusal"]

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


InstructionsUnionMember1ResponseOutputMessageContent: TypeAlias = Union[
    InstructionsUnionMember1ResponseOutputMessageContentResponseOutputText,
    InstructionsUnionMember1ResponseOutputMessageContentResponseOutputRefusal,
]


class InstructionsUnionMember1ResponseOutputMessage(BaseModel):
    id: str

    content: List[InstructionsUnionMember1ResponseOutputMessageContent]

    role: Literal["assistant"]

    status: Literal["in_progress", "completed", "incomplete"]

    type: Literal["message"]

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


class InstructionsUnionMember1ResponseFileSearchToolCallResult(BaseModel):
    attributes: Optional[Dict[str, Union[str, float, bool]]] = None

    file_id: Optional[str] = None

    filename: Optional[str] = None

    score: Optional[float] = None

    text: Optional[str] = None

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


class InstructionsUnionMember1ResponseFileSearchToolCall(BaseModel):
    id: str

    queries: List[str]

    status: Literal["in_progress", "searching", "completed", "incomplete", "failed"]

    type: Literal["file_search_call"]

    results: Optional[List[InstructionsUnionMember1ResponseFileSearchToolCallResult]] = None

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


class InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionClick(
    BaseModel
):
    button: Literal["left", "right", "wheel", "back", "forward"]

    type: Literal["click"]

    x: int

    y: int

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


class InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionDoubleClick(
    BaseModel
):
    type: Literal["double_click"]

    x: int

    y: int

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


class InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionDragPath(
    BaseModel
):
    x: int

    y: int

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


class InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionDrag(
    BaseModel
):
    path: List[
        InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionDragPath
    ]

    type: Literal["drag"]

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


class InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionKeypress(
    BaseModel
):
    keys: List[str]

    type: Literal["keypress"]

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


class InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionMove(
    BaseModel
):
    type: Literal["move"]

    x: int

    y: int

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


class InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionScreenshot(
    BaseModel
):
    type: Literal["screenshot"]

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


class InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionScroll(
    BaseModel
):
    scroll_x: int

    scroll_y: int

    type: Literal["scroll"]

    x: int

    y: int

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


class InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionType(
    BaseModel
):
    text: str

    type: Literal["type"]

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


class InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionWait(
    BaseModel
):
    type: Literal["wait"]

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


InstructionsUnionMember1ResponseComputerToolCallAction: TypeAlias = Union[
    InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionClick,
    InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionDoubleClick,
    InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionDrag,
    InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionKeypress,
    InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionMove,
    InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionScreenshot,
    InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionScroll,
    InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionType,
    InstructionsUnionMember1ResponseComputerToolCallActionOpenAITypesResponsesResponseComputerToolCallActionWait,
]


class InstructionsUnionMember1ResponseComputerToolCallPendingSafetyCheck(BaseModel):
    id: str

    code: str

    message: str

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


class InstructionsUnionMember1ResponseComputerToolCall(BaseModel):
    id: str

    action: InstructionsUnionMember1ResponseComputerToolCallAction

    call_id: str

    pending_safety_checks: List[InstructionsUnionMember1ResponseComputerToolCallPendingSafetyCheck]

    status: Literal["in_progress", "completed", "incomplete"]

    type: Literal["computer_call"]

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


class InstructionsUnionMember1OpenAITypesResponsesResponseInputItemComputerCallOutputOutput(BaseModel):
    type: Literal["computer_screenshot"]

    file_id: Optional[str] = None

    image_url: Optional[str] = None

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


class InstructionsUnionMember1OpenAITypesResponsesResponseInputItemComputerCallOutputAcknowledgedSafetyCheck(BaseModel):
    id: str

    code: Optional[str] = None

    message: Optional[str] = None

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


class InstructionsUnionMember1OpenAITypesResponsesResponseInputItemComputerCallOutput(BaseModel):
    call_id: str

    output: InstructionsUnionMember1OpenAITypesResponsesResponseInputItemComputerCallOutputOutput

    type: Literal["computer_call_output"]

    id: Optional[str] = None

    acknowledged_safety_checks: Optional[
        List[InstructionsUnionMember1OpenAITypesResponsesResponseInputItemComputerCallOutputAcknowledgedSafetyCheck]
    ] = None

    status: Optional[Literal["in_progress", "completed", "incomplete"]] = None

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


class InstructionsUnionMember1ResponseFunctionWebSearchActionOpenAITypesResponsesResponseFunctionWebSearchActionSearch(
    BaseModel
):
    query: str

    type: Literal["search"]

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


class InstructionsUnionMember1ResponseFunctionWebSearchActionOpenAITypesResponsesResponseFunctionWebSearchActionOpenPage(
    BaseModel
):
    type: Literal["open_page"]

    url: str

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


class InstructionsUnionMember1ResponseFunctionWebSearchActionOpenAITypesResponsesResponseFunctionWebSearchActionFind(
    BaseModel
):
    pattern: str

    type: Literal["find"]

    url: str

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


InstructionsUnionMember1ResponseFunctionWebSearchAction: TypeAlias = Union[
    InstructionsUnionMember1ResponseFunctionWebSearchActionOpenAITypesResponsesResponseFunctionWebSearchActionSearch,
    InstructionsUnionMember1ResponseFunctionWebSearchActionOpenAITypesResponsesResponseFunctionWebSearchActionOpenPage,
    InstructionsUnionMember1ResponseFunctionWebSearchActionOpenAITypesResponsesResponseFunctionWebSearchActionFind,
]


class InstructionsUnionMember1ResponseFunctionWebSearch(BaseModel):
    id: str

    action: InstructionsUnionMember1ResponseFunctionWebSearchAction

    status: Literal["in_progress", "searching", "completed", "failed"]

    type: Literal["web_search_call"]

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


class InstructionsUnionMember1ResponseFunctionToolCall(BaseModel):
    arguments: str

    call_id: str

    name: str

    type: Literal["function_call"]

    id: Optional[str] = None

    status: Optional[Literal["in_progress", "completed", "incomplete"]] = None

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


class InstructionsUnionMember1OpenAITypesResponsesResponseInputItemFunctionCallOutput(BaseModel):
    call_id: str

    output: str

    type: Literal["function_call_output"]

    id: Optional[str] = None

    status: Optional[Literal["in_progress", "completed", "incomplete"]] = None

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


class InstructionsUnionMember1ResponseReasoningItemSummary(BaseModel):
    text: str

    type: Literal["summary_text"]

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


class InstructionsUnionMember1ResponseReasoningItemContent(BaseModel):
    text: str

    type: Literal["reasoning_text"]

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


class InstructionsUnionMember1ResponseReasoningItem(BaseModel):
    id: str

    summary: List[InstructionsUnionMember1ResponseReasoningItemSummary]

    type: Literal["reasoning"]

    content: Optional[List[InstructionsUnionMember1ResponseReasoningItemContent]] = None

    encrypted_content: Optional[str] = None

    status: Optional[Literal["in_progress", "completed", "incomplete"]] = None

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


class InstructionsUnionMember1OpenAITypesResponsesResponseInputItemImageGenerationCall(BaseModel):
    id: str

    status: Literal["in_progress", "completed", "generating", "failed"]

    type: Literal["image_generation_call"]

    result: Optional[str] = None

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


class InstructionsUnionMember1ResponseCodeInterpreterToolCallOutputOpenAITypesResponsesResponseCodeInterpreterToolCallOutputLogs(
    BaseModel
):
    logs: str

    type: Literal["logs"]

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


class InstructionsUnionMember1ResponseCodeInterpreterToolCallOutputOpenAITypesResponsesResponseCodeInterpreterToolCallOutputImage(
    BaseModel
):
    type: Literal["image"]

    url: str

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


InstructionsUnionMember1ResponseCodeInterpreterToolCallOutput: TypeAlias = Union[
    InstructionsUnionMember1ResponseCodeInterpreterToolCallOutputOpenAITypesResponsesResponseCodeInterpreterToolCallOutputLogs,
    InstructionsUnionMember1ResponseCodeInterpreterToolCallOutputOpenAITypesResponsesResponseCodeInterpreterToolCallOutputImage,
]


class InstructionsUnionMember1ResponseCodeInterpreterToolCall(BaseModel):
    id: str

    container_id: str

    status: Literal["in_progress", "completed", "incomplete", "interpreting", "failed"]

    type: Literal["code_interpreter_call"]

    code: Optional[str] = None

    outputs: Optional[List[InstructionsUnionMember1ResponseCodeInterpreterToolCallOutput]] = None

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


class InstructionsUnionMember1OpenAITypesResponsesResponseInputItemLocalShellCallAction(BaseModel):
    command: List[str]

    env: Dict[str, str]

    type: Literal["exec"]

    timeout_ms: Optional[int] = None

    user: Optional[str] = None

    working_directory: Optional[str] = None

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


class InstructionsUnionMember1OpenAITypesResponsesResponseInputItemLocalShellCall(BaseModel):
    id: str

    action: InstructionsUnionMember1OpenAITypesResponsesResponseInputItemLocalShellCallAction

    call_id: str

    status: Literal["in_progress", "completed", "incomplete"]

    type: Literal["local_shell_call"]

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


class InstructionsUnionMember1OpenAITypesResponsesResponseInputItemLocalShellCallOutput(BaseModel):
    id: str

    output: str

    type: Literal["local_shell_call_output"]

    status: Optional[Literal["in_progress", "completed", "incomplete"]] = None

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


class InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMcpListToolsTool(BaseModel):
    input_schema: object

    name: str

    annotations: Optional[object] = None

    description: Optional[str] = None

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


class InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMcpListTools(BaseModel):
    id: str

    server_label: str

    tools: List[InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMcpListToolsTool]

    type: Literal["mcp_list_tools"]

    error: Optional[str] = None

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


class InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMcpApprovalRequest(BaseModel):
    id: str

    arguments: str

    name: str

    server_label: str

    type: Literal["mcp_approval_request"]

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


class InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMcpApprovalResponse(BaseModel):
    approval_request_id: str

    approve: bool

    type: Literal["mcp_approval_response"]

    id: Optional[str] = None

    reason: Optional[str] = None

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


class InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMcpCall(BaseModel):
    id: str

    arguments: str

    name: str

    server_label: str

    type: Literal["mcp_call"]

    error: Optional[str] = None

    output: Optional[str] = None

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


class InstructionsUnionMember1ResponseCustomToolCallOutput(BaseModel):
    call_id: str

    output: str

    type: Literal["custom_tool_call_output"]

    id: Optional[str] = None

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


class InstructionsUnionMember1ResponseCustomToolCall(BaseModel):
    call_id: str

    input: str

    name: str

    type: Literal["custom_tool_call"]

    id: Optional[str] = None

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


class InstructionsUnionMember1OpenAITypesResponsesResponseInputItemItemReference(BaseModel):
    id: str

    type: Optional[Literal["item_reference"]] = None

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


InstructionsUnionMember1: TypeAlias = Union[
    InstructionsUnionMember1EasyInputMessage,
    InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMessage,
    InstructionsUnionMember1ResponseOutputMessage,
    InstructionsUnionMember1ResponseFileSearchToolCall,
    InstructionsUnionMember1ResponseComputerToolCall,
    InstructionsUnionMember1OpenAITypesResponsesResponseInputItemComputerCallOutput,
    InstructionsUnionMember1ResponseFunctionWebSearch,
    InstructionsUnionMember1ResponseFunctionToolCall,
    InstructionsUnionMember1OpenAITypesResponsesResponseInputItemFunctionCallOutput,
    InstructionsUnionMember1ResponseReasoningItem,
    InstructionsUnionMember1OpenAITypesResponsesResponseInputItemImageGenerationCall,
    InstructionsUnionMember1ResponseCodeInterpreterToolCall,
    InstructionsUnionMember1OpenAITypesResponsesResponseInputItemLocalShellCall,
    InstructionsUnionMember1OpenAITypesResponsesResponseInputItemLocalShellCallOutput,
    InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMcpListTools,
    InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMcpApprovalRequest,
    InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMcpApprovalResponse,
    InstructionsUnionMember1OpenAITypesResponsesResponseInputItemMcpCall,
    InstructionsUnionMember1ResponseCustomToolCallOutput,
    InstructionsUnionMember1ResponseCustomToolCall,
    InstructionsUnionMember1OpenAITypesResponsesResponseInputItemItemReference,
]


class PromptVariablesResponseInputText(BaseModel):
    text: str

    type: Literal["input_text"]

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


class PromptVariablesResponseInputImage(BaseModel):
    detail: Literal["low", "high", "auto"]

    type: Literal["input_image"]

    file_id: Optional[str] = None

    image_url: Optional[str] = None

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


class PromptVariablesResponseInputFile(BaseModel):
    type: Literal["input_file"]

    file_data: Optional[str] = None

    file_id: Optional[str] = None

    file_url: Optional[str] = None

    filename: Optional[str] = None

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


PromptVariables: TypeAlias = Union[
    str, PromptVariablesResponseInputText, PromptVariablesResponseInputImage, PromptVariablesResponseInputFile
]


class Prompt(BaseModel):
    id: str

    variables: Optional[Dict[str, PromptVariables]] = None

    version: Optional[str] = None

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


class Reasoning(BaseModel):
    effort: Optional[Literal["minimal", "low", "medium", "high"]] = None

    generate_summary: Optional[Literal["auto", "concise", "detailed"]] = None

    summary: Optional[Literal["auto", "concise", "detailed"]] = None

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


class TextFormatResponseFormatText(BaseModel):
    type: Literal["text"]

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


class TextFormatResponseFormatTextJsonSchemaConfig(BaseModel):
    name: str

    schema_: Dict[str, object] = FieldInfo(alias="schema")

    type: Literal["json_schema"]

    description: Optional[str] = None

    strict: Optional[bool] = None

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


class TextFormatResponseFormatJsonObject(BaseModel):
    type: Literal["json_object"]

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


TextFormat: TypeAlias = Union[
    TextFormatResponseFormatText, TextFormatResponseFormatTextJsonSchemaConfig, TextFormatResponseFormatJsonObject
]


class Text(BaseModel):
    format: Optional[TextFormat] = None

    verbosity: Optional[Literal["low", "medium", "high"]] = None

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


class UsageInputTokensDetails(BaseModel):
    cached_tokens: int

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


class UsageOutputTokensDetails(BaseModel):
    reasoning_tokens: int

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


class Usage(BaseModel):
    input_tokens: int

    input_tokens_details: UsageInputTokensDetails

    output_tokens: int

    output_tokens_details: UsageOutputTokensDetails

    total_tokens: int

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


class Response(BaseModel):
    id: str

    created_at: float

    model: Union[
        Literal[
            "gpt-5",
            "gpt-5-mini",
            "gpt-5-nano",
            "gpt-5-2025-08-07",
            "gpt-5-mini-2025-08-07",
            "gpt-5-nano-2025-08-07",
            "gpt-5-chat-latest",
            "gpt-4.1",
            "gpt-4.1-mini",
            "gpt-4.1-nano",
            "gpt-4.1-2025-04-14",
            "gpt-4.1-mini-2025-04-14",
            "gpt-4.1-nano-2025-04-14",
            "o4-mini",
            "o4-mini-2025-04-16",
            "o3",
            "o3-2025-04-16",
            "o3-mini",
            "o3-mini-2025-01-31",
            "o1",
            "o1-2024-12-17",
            "o1-preview",
            "o1-preview-2024-09-12",
            "o1-mini",
            "o1-mini-2024-09-12",
            "gpt-4o",
            "gpt-4o-2024-11-20",
            "gpt-4o-2024-08-06",
            "gpt-4o-2024-05-13",
            "gpt-4o-audio-preview",
            "gpt-4o-audio-preview-2024-10-01",
            "gpt-4o-audio-preview-2024-12-17",
            "gpt-4o-audio-preview-2025-06-03",
            "gpt-4o-mini-audio-preview",
            "gpt-4o-mini-audio-preview-2024-12-17",
            "gpt-4o-search-preview",
            "gpt-4o-mini-search-preview",
            "gpt-4o-search-preview-2025-03-11",
            "gpt-4o-mini-search-preview-2025-03-11",
            "chatgpt-4o-latest",
            "codex-mini-latest",
            "gpt-4o-mini",
            "gpt-4o-mini-2024-07-18",
            "gpt-4-turbo",
            "gpt-4-turbo-2024-04-09",
            "gpt-4-0125-preview",
            "gpt-4-turbo-preview",
            "gpt-4-1106-preview",
            "gpt-4-vision-preview",
            "gpt-4",
            "gpt-4-0314",
            "gpt-4-0613",
            "gpt-4-32k",
            "gpt-4-32k-0314",
            "gpt-4-32k-0613",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "gpt-3.5-turbo-0301",
            "gpt-3.5-turbo-0613",
            "gpt-3.5-turbo-1106",
            "gpt-3.5-turbo-0125",
            "gpt-3.5-turbo-16k-0613",
            "o1-pro",
            "o1-pro-2025-03-19",
            "o3-pro",
            "o3-pro-2025-06-10",
            "o3-deep-research",
            "o3-deep-research-2025-06-26",
            "o4-mini-deep-research",
            "o4-mini-deep-research-2025-06-26",
            "computer-use-preview",
            "computer-use-preview-2025-03-11",
        ],
        str,
    ]

    output: List[Output]

    parallel_tool_calls: bool

    tool_choice: ToolChoice

    tools: List[Tool]

    background: Optional[bool] = None

    error: Optional[Error] = None

    incomplete_details: Optional[IncompleteDetails] = None

    instructions: Union[str, List[InstructionsUnionMember1], None] = None

    max_output_tokens: Optional[int] = None

    max_tool_calls: Optional[int] = None

    metadata: Optional[Dict[str, str]] = None

    object: Optional[Literal["response"]] = None

    previous_response_id: Optional[str] = None

    prompt: Optional[Prompt] = None

    prompt_cache_key: Optional[str] = None

    reasoning: Optional[Reasoning] = None

    safety_identifier: Optional[str] = None

    service_tier: Optional[Literal["auto", "default", "flex", "scale", "priority"]] = None

    status: Optional[Literal["completed", "failed", "in_progress", "cancelled", "queued", "incomplete"]] = None

    temperature: Optional[float] = None

    text: Optional[Text] = None

    top_logprobs: Optional[int] = None

    top_p: Optional[float] = None

    truncation: Optional[Literal["auto", "disabled"]] = None

    usage: Optional[Usage] = None

    user: Optional[str] = None

    if TYPE_CHECKING:
        # Some versions of Pydantic <2.8.0 have a bug and don’t allow assigning a
        # value to this field, so for compatibility we avoid doing it at runtime.
        __pydantic_extra__: Dict[str, builtins.object] = FieldInfo(init=False)  # pyright: ignore[reportIncompatibleVariableOverride]

        # Stub to indicate that arbitrary properties are accepted.
        # To access properties that are not valid identifiers you can use `getattr`, e.g.
        # `getattr(obj, '$type')`
        def __getattr__(self, attr: str) -> builtins.object: ...
    else:
        __pydantic_extra__: Dict[str, builtins.object]
