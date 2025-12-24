# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Union, Optional
from datetime import datetime
from typing_extensions import Literal, Annotated, TypeAlias

from .._utils import PropertyInfo
from .._models import BaseModel
from .shared.identity import Identity

__all__ = [
    "Question",
    "CategoricalQuestion",
    "CategoricalQuestionConfiguration",
    "RatingQuestion",
    "RatingQuestionConfiguration",
    "NumberQuestion",
    "NumberQuestionConfiguration",
    "FreeTextQuestion",
    "FreeTextQuestionConfiguration",
    "FormQuestion",
    "FormQuestionConfiguration",
    "TimestampQuestion",
    "TimestampQuestionConfiguration",
]


class CategoricalQuestionConfiguration(BaseModel):
    choices: List[str]
    """Categorical answer choices (must contain at least one entry)"""

    dropdown: Optional[bool] = None
    """Whether the question is displayed as a dropdown in the UI."""

    multi: Optional[bool] = None
    """Whether the question allows multiple answers."""


class CategoricalQuestion(BaseModel):
    id: str
    """Unique identifier of the entity"""

    configuration: CategoricalQuestionConfiguration

    created_at: datetime
    """ISO-timestamp when the entity was created"""

    created_by: Identity
    """The identity that created the entity."""

    name: str

    prompt: str
    """user-facing question prompt"""

    conditions: Optional[List[Dict[str, object]]] = None
    """Conditions for the question to be shown"""

    object: Optional[Literal["question"]] = None

    question_type: Optional[Literal["categorical"]] = None


class RatingQuestionConfiguration(BaseModel):
    max_label: str
    """Label shown for the maximum rating"""

    min_label: str
    """Label shown for the minimum rating"""

    steps: int
    """Number of discrete points on the scale (e.g., 5 for a 1–5 scale)"""


class RatingQuestion(BaseModel):
    id: str
    """Unique identifier of the entity"""

    configuration: RatingQuestionConfiguration

    created_at: datetime
    """ISO-timestamp when the entity was created"""

    created_by: Identity
    """The identity that created the entity."""

    name: str

    prompt: str
    """user-facing question prompt"""

    conditions: Optional[List[Dict[str, object]]] = None
    """Conditions for the question to be shown"""

    object: Optional[Literal["question"]] = None

    question_type: Optional[Literal["rating"]] = None


class NumberQuestionConfiguration(BaseModel):
    max: Optional[float] = None
    """Maximum value for the number"""

    min: Optional[float] = None
    """Minimum value for the number"""


class NumberQuestion(BaseModel):
    id: str
    """Unique identifier of the entity"""

    created_at: datetime
    """ISO-timestamp when the entity was created"""

    created_by: Identity
    """The identity that created the entity."""

    name: str

    prompt: str
    """user-facing question prompt"""

    conditions: Optional[List[Dict[str, object]]] = None
    """Conditions for the question to be shown"""

    configuration: Optional[NumberQuestionConfiguration] = None

    object: Optional[Literal["question"]] = None

    question_type: Optional[Literal["number"]] = None


class FreeTextQuestionConfiguration(BaseModel):
    max_length: Optional[int] = None
    """Maximum characters allowed"""

    min_length: Optional[int] = None
    """Minimum characters required"""


class FreeTextQuestion(BaseModel):
    id: str
    """Unique identifier of the entity"""

    created_at: datetime
    """ISO-timestamp when the entity was created"""

    created_by: Identity
    """The identity that created the entity."""

    name: str

    prompt: str
    """user-facing question prompt"""

    conditions: Optional[List[Dict[str, object]]] = None
    """Conditions for the question to be shown"""

    configuration: Optional[FreeTextQuestionConfiguration] = None

    object: Optional[Literal["question"]] = None

    question_type: Optional[Literal["free_text"]] = None


class FormQuestionConfiguration(BaseModel):
    form_schema: Dict[str, object]
    """The JSON schema of the desired form object"""


class FormQuestion(BaseModel):
    id: str
    """Unique identifier of the entity"""

    configuration: FormQuestionConfiguration

    created_at: datetime
    """ISO-timestamp when the entity was created"""

    created_by: Identity
    """The identity that created the entity."""

    name: str

    prompt: str
    """user-facing question prompt"""

    conditions: Optional[List[Dict[str, object]]] = None
    """Conditions for the question to be shown"""

    object: Optional[Literal["question"]] = None

    question_type: Optional[Literal["form"]] = None


class TimestampQuestionConfiguration(BaseModel):
    multi: Optional[bool] = None
    """Whether to allow multiple timestamps"""


class TimestampQuestion(BaseModel):
    id: str
    """Unique identifier of the entity"""

    created_at: datetime
    """ISO-timestamp when the entity was created"""

    created_by: Identity
    """The identity that created the entity."""

    name: str

    prompt: str
    """user-facing question prompt"""

    conditions: Optional[List[Dict[str, object]]] = None
    """Conditions for the question to be shown"""

    configuration: Optional[TimestampQuestionConfiguration] = None

    object: Optional[Literal["question"]] = None

    question_type: Optional[Literal["timestamp"]] = None


Question: TypeAlias = Annotated[
    Union[CategoricalQuestion, RatingQuestion, NumberQuestion, FreeTextQuestion, FormQuestion, TimestampQuestion],
    PropertyInfo(discriminator="question_type"),
]
