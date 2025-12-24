# Shared Types

```python
from scale_gp_beta.types import Identity
```

# Responses

Types:

```python
from scale_gp_beta.types import Response, ResponseCreateResponse
```

Methods:

- <code title="post /v5/responses">client.responses.<a href="./src/scale_gp_beta/resources/responses.py">create</a>(\*\*<a href="src/scale_gp_beta/types/response_create_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/response_create_response.py">ResponseCreateResponse</a></code>

# Completions

Types:

```python
from scale_gp_beta.types import Completion
```

Methods:

- <code title="post /v5/completions">client.completions.<a href="./src/scale_gp_beta/resources/completions.py">create</a>(\*\*<a href="src/scale_gp_beta/types/completion_create_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/completion.py">Completion</a></code>

# Chat

## Completions

Types:

```python
from scale_gp_beta.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
    ModelDefinition,
    CompletionCreateResponse,
    CompletionModelsResponse,
)
```

Methods:

- <code title="post /v5/chat/completions">client.chat.completions.<a href="./src/scale_gp_beta/resources/chat/completions.py">create</a>(\*\*<a href="src/scale_gp_beta/types/chat/completion_create_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/chat/completion_create_response.py">CompletionCreateResponse</a></code>
- <code title="get /v5/chat/completions/models">client.chat.completions.<a href="./src/scale_gp_beta/resources/chat/completions.py">models</a>(\*\*<a href="src/scale_gp_beta/types/chat/completion_models_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/chat/completion_models_response.py">CompletionModelsResponse</a></code>

# Inference

Types:

```python
from scale_gp_beta.types import InferenceResponse, InferenceResponseChunk, InferenceCreateResponse
```

Methods:

- <code title="post /v5/inference">client.inference.<a href="./src/scale_gp_beta/resources/inference.py">create</a>(\*\*<a href="src/scale_gp_beta/types/inference_create_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/inference_create_response.py">InferenceCreateResponse</a></code>

# Questions

Types:

```python
from scale_gp_beta.types import Question
```

Methods:

- <code title="post /v5/questions">client.questions.<a href="./src/scale_gp_beta/resources/questions.py">create</a>(\*\*<a href="src/scale_gp_beta/types/question_create_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/question.py">Question</a></code>
- <code title="get /v5/questions/{question_id}">client.questions.<a href="./src/scale_gp_beta/resources/questions.py">retrieve</a>(question_id) -> <a href="./src/scale_gp_beta/types/question.py">Question</a></code>
- <code title="get /v5/questions">client.questions.<a href="./src/scale_gp_beta/resources/questions.py">list</a>(\*\*<a href="src/scale_gp_beta/types/question_list_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/question.py">SyncCursorPage[Question]</a></code>

# Files

Types:

```python
from scale_gp_beta.types import File, FileDeleteResponse, FileImportFromCloudResponse
```

Methods:

- <code title="post /v5/files">client.files.<a href="./src/scale_gp_beta/resources/files/files.py">create</a>(\*\*<a href="src/scale_gp_beta/types/file_create_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/file.py">File</a></code>
- <code title="get /v5/files/{file_id}">client.files.<a href="./src/scale_gp_beta/resources/files/files.py">retrieve</a>(file_id) -> <a href="./src/scale_gp_beta/types/file.py">File</a></code>
- <code title="patch /v5/files/{file_id}">client.files.<a href="./src/scale_gp_beta/resources/files/files.py">update</a>(file_id, \*\*<a href="src/scale_gp_beta/types/file_update_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/file.py">File</a></code>
- <code title="get /v5/files">client.files.<a href="./src/scale_gp_beta/resources/files/files.py">list</a>(\*\*<a href="src/scale_gp_beta/types/file_list_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/file.py">SyncCursorPage[File]</a></code>
- <code title="delete /v5/files/{file_id}">client.files.<a href="./src/scale_gp_beta/resources/files/files.py">delete</a>(file_id) -> <a href="./src/scale_gp_beta/types/file_delete_response.py">FileDeleteResponse</a></code>
- <code title="post /v5/files/cloud_imports">client.files.<a href="./src/scale_gp_beta/resources/files/files.py">import_from_cloud</a>(\*\*<a href="src/scale_gp_beta/types/file_import_from_cloud_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/file_import_from_cloud_response.py">FileImportFromCloudResponse</a></code>

## Content

Methods:

- <code title="get /v5/files/{file_id}/content">client.files.content.<a href="./src/scale_gp_beta/resources/files/content.py">retrieve</a>(file_id) -> object</code>

# Models

Types:

```python
from scale_gp_beta.types import InferenceModel, ModelDeleteResponse
```

Methods:

- <code title="post /v5/models">client.models.<a href="./src/scale_gp_beta/resources/models.py">create</a>(\*\*<a href="src/scale_gp_beta/types/model_create_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/inference_model.py">InferenceModel</a></code>
- <code title="get /v5/models/{model_id}">client.models.<a href="./src/scale_gp_beta/resources/models.py">retrieve</a>(model_id) -> <a href="./src/scale_gp_beta/types/inference_model.py">InferenceModel</a></code>
- <code title="patch /v5/models/{model_id}">client.models.<a href="./src/scale_gp_beta/resources/models.py">update</a>(model_id, \*\*<a href="src/scale_gp_beta/types/model_update_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/inference_model.py">InferenceModel</a></code>
- <code title="get /v5/models">client.models.<a href="./src/scale_gp_beta/resources/models.py">list</a>(\*\*<a href="src/scale_gp_beta/types/model_list_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/inference_model.py">SyncCursorPage[InferenceModel]</a></code>
- <code title="delete /v5/models/{model_id}">client.models.<a href="./src/scale_gp_beta/resources/models.py">delete</a>(model_id) -> <a href="./src/scale_gp_beta/types/model_delete_response.py">ModelDeleteResponse</a></code>

# Datasets

Types:

```python
from scale_gp_beta.types import Dataset, DatasetDeleteResponse
```

Methods:

- <code title="post /v5/datasets">client.datasets.<a href="./src/scale_gp_beta/resources/datasets.py">create</a>(\*\*<a href="src/scale_gp_beta/types/dataset_create_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/dataset.py">Dataset</a></code>
- <code title="get /v5/datasets/{dataset_id}">client.datasets.<a href="./src/scale_gp_beta/resources/datasets.py">retrieve</a>(dataset_id, \*\*<a href="src/scale_gp_beta/types/dataset_retrieve_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/dataset.py">Dataset</a></code>
- <code title="patch /v5/datasets/{dataset_id}">client.datasets.<a href="./src/scale_gp_beta/resources/datasets.py">update</a>(dataset_id, \*\*<a href="src/scale_gp_beta/types/dataset_update_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/dataset.py">Dataset</a></code>
- <code title="get /v5/datasets">client.datasets.<a href="./src/scale_gp_beta/resources/datasets.py">list</a>(\*\*<a href="src/scale_gp_beta/types/dataset_list_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/dataset.py">SyncCursorPage[Dataset]</a></code>
- <code title="delete /v5/datasets/{dataset_id}">client.datasets.<a href="./src/scale_gp_beta/resources/datasets.py">delete</a>(dataset_id) -> <a href="./src/scale_gp_beta/types/dataset_delete_response.py">DatasetDeleteResponse</a></code>

# DatasetItems

Types:

```python
from scale_gp_beta.types import (
    DatasetItem,
    DatasetItemDeleteResponse,
    DatasetItemBatchCreateResponse,
)
```

Methods:

- <code title="get /v5/dataset-items/{dataset_item_id}">client.dataset_items.<a href="./src/scale_gp_beta/resources/dataset_items.py">retrieve</a>(dataset_item_id, \*\*<a href="src/scale_gp_beta/types/dataset_item_retrieve_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/dataset_item.py">DatasetItem</a></code>
- <code title="patch /v5/dataset-items/{dataset_item_id}">client.dataset_items.<a href="./src/scale_gp_beta/resources/dataset_items.py">update</a>(dataset_item_id, \*\*<a href="src/scale_gp_beta/types/dataset_item_update_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/dataset_item.py">DatasetItem</a></code>
- <code title="get /v5/dataset-items">client.dataset_items.<a href="./src/scale_gp_beta/resources/dataset_items.py">list</a>(\*\*<a href="src/scale_gp_beta/types/dataset_item_list_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/dataset_item.py">SyncCursorPage[DatasetItem]</a></code>
- <code title="delete /v5/dataset-items/{dataset_item_id}">client.dataset_items.<a href="./src/scale_gp_beta/resources/dataset_items.py">delete</a>(dataset_item_id) -> <a href="./src/scale_gp_beta/types/dataset_item_delete_response.py">DatasetItemDeleteResponse</a></code>
- <code title="post /v5/dataset-items/batch">client.dataset_items.<a href="./src/scale_gp_beta/resources/dataset_items.py">batch_create</a>(\*\*<a href="src/scale_gp_beta/types/dataset_item_batch_create_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/dataset_item_batch_create_response.py">DatasetItemBatchCreateResponse</a></code>

# Evaluations

Types:

```python
from scale_gp_beta.types import Evaluation, EvaluationTask, ItemLocator, ItemLocatorTemplate
```

Methods:

- <code title="post /v5/evaluations">client.evaluations.<a href="./src/scale_gp_beta/resources/evaluations.py">create</a>(\*\*<a href="src/scale_gp_beta/types/evaluation_create_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/evaluation.py">Evaluation</a></code>
- <code title="get /v5/evaluations/{evaluation_id}">client.evaluations.<a href="./src/scale_gp_beta/resources/evaluations.py">retrieve</a>(evaluation_id, \*\*<a href="src/scale_gp_beta/types/evaluation_retrieve_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/evaluation.py">Evaluation</a></code>
- <code title="patch /v5/evaluations/{evaluation_id}">client.evaluations.<a href="./src/scale_gp_beta/resources/evaluations.py">update</a>(evaluation_id, \*\*<a href="src/scale_gp_beta/types/evaluation_update_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/evaluation.py">Evaluation</a></code>
- <code title="get /v5/evaluations">client.evaluations.<a href="./src/scale_gp_beta/resources/evaluations.py">list</a>(\*\*<a href="src/scale_gp_beta/types/evaluation_list_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/evaluation.py">SyncCursorPage[Evaluation]</a></code>
- <code title="delete /v5/evaluations/{evaluation_id}">client.evaluations.<a href="./src/scale_gp_beta/resources/evaluations.py">delete</a>(evaluation_id) -> <a href="./src/scale_gp_beta/types/evaluation.py">Evaluation</a></code>

# EvaluationItems

Types:

```python
from scale_gp_beta.types import Component, Container, EvaluationItem
```

Methods:

- <code title="get /v5/evaluation-items/{evaluation_item_id}">client.evaluation_items.<a href="./src/scale_gp_beta/resources/evaluation_items.py">retrieve</a>(evaluation_item_id, \*\*<a href="src/scale_gp_beta/types/evaluation_item_retrieve_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/evaluation_item.py">EvaluationItem</a></code>
- <code title="get /v5/evaluation-items">client.evaluation_items.<a href="./src/scale_gp_beta/resources/evaluation_items.py">list</a>(\*\*<a href="src/scale_gp_beta/types/evaluation_item_list_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/evaluation_item.py">SyncCursorPage[EvaluationItem]</a></code>

# Spans

Types:

```python
from scale_gp_beta.types import (
    Span,
    SpanStatus,
    SpanType,
    SpanBatchResponse,
    SpanUpsertBatchResponse,
)
```

Methods:

- <code title="post /v5/spans">client.spans.<a href="./src/scale_gp_beta/resources/spans.py">create</a>(\*\*<a href="src/scale_gp_beta/types/span_create_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/span.py">Span</a></code>
- <code title="get /v5/spans/{span_id}">client.spans.<a href="./src/scale_gp_beta/resources/spans.py">retrieve</a>(span_id) -> <a href="./src/scale_gp_beta/types/span.py">Span</a></code>
- <code title="patch /v5/spans/{span_id}">client.spans.<a href="./src/scale_gp_beta/resources/spans.py">update</a>(span_id, \*\*<a href="src/scale_gp_beta/types/span_update_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/span.py">Span</a></code>
- <code title="post /v5/spans/batch">client.spans.<a href="./src/scale_gp_beta/resources/spans.py">batch</a>(\*\*<a href="src/scale_gp_beta/types/span_batch_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/span_batch_response.py">SpanBatchResponse</a></code>
- <code title="post /v5/spans/search">client.spans.<a href="./src/scale_gp_beta/resources/spans.py">search</a>(\*\*<a href="src/scale_gp_beta/types/span_search_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/span.py">SyncCursorPage[Span]</a></code>
- <code title="put /v5/spans/batch">client.spans.<a href="./src/scale_gp_beta/resources/spans.py">upsert_batch</a>(\*\*<a href="src/scale_gp_beta/types/span_upsert_batch_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/span_upsert_batch_response.py">SpanUpsertBatchResponse</a></code>

# SpanAssessments

Types:

```python
from scale_gp_beta.types import (
    ApprovalStatus,
    AssessmentType,
    SpanAssessment,
    SpanAssessmentDeleteResponse,
)
```

Methods:

- <code title="post /v5/span-assessments">client.span_assessments.<a href="./src/scale_gp_beta/resources/span_assessments.py">create</a>(\*\*<a href="src/scale_gp_beta/types/span_assessment_create_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/span_assessment.py">SpanAssessment</a></code>
- <code title="get /v5/span-assessments/{span_assessment_id}">client.span_assessments.<a href="./src/scale_gp_beta/resources/span_assessments.py">retrieve</a>(span_assessment_id) -> <a href="./src/scale_gp_beta/types/span_assessment.py">SpanAssessment</a></code>
- <code title="patch /v5/span-assessments/{span_assessment_id}">client.span_assessments.<a href="./src/scale_gp_beta/resources/span_assessments.py">update</a>(span_assessment_id, \*\*<a href="src/scale_gp_beta/types/span_assessment_update_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/span_assessment.py">SpanAssessment</a></code>
- <code title="get /v5/span-assessments">client.span_assessments.<a href="./src/scale_gp_beta/resources/span_assessments.py">list</a>(\*\*<a href="src/scale_gp_beta/types/span_assessment_list_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/span_assessment.py">SyncAPIListPage[SpanAssessment]</a></code>
- <code title="delete /v5/span-assessments/{span_assessment_id}">client.span_assessments.<a href="./src/scale_gp_beta/resources/span_assessments.py">delete</a>(span_assessment_id) -> <a href="./src/scale_gp_beta/types/span_assessment_delete_response.py">SpanAssessmentDeleteResponse</a></code>

# Credentials

Types:

```python
from scale_gp_beta.types import Credential, CredentialSecret, CredentialDeleteResponse
```

Methods:

- <code title="post /v5/credentials">client.credentials.<a href="./src/scale_gp_beta/resources/credentials.py">create</a>(\*\*<a href="src/scale_gp_beta/types/credential_create_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/credential.py">Credential</a></code>
- <code title="get /v5/credentials/{credential_id}">client.credentials.<a href="./src/scale_gp_beta/resources/credentials.py">retrieve</a>(credential_id) -> <a href="./src/scale_gp_beta/types/credential.py">Credential</a></code>
- <code title="patch /v5/credentials/{credential_id}">client.credentials.<a href="./src/scale_gp_beta/resources/credentials.py">update</a>(credential_id, \*\*<a href="src/scale_gp_beta/types/credential_update_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/credential.py">Credential</a></code>
- <code title="get /v5/credentials">client.credentials.<a href="./src/scale_gp_beta/resources/credentials.py">list</a>(\*\*<a href="src/scale_gp_beta/types/credential_list_params.py">params</a>) -> <a href="./src/scale_gp_beta/types/credential.py">SyncCursorPage[Credential]</a></code>
- <code title="delete /v5/credentials/{credential_id}">client.credentials.<a href="./src/scale_gp_beta/resources/credentials.py">delete</a>(credential_id) -> <a href="./src/scale_gp_beta/types/credential_delete_response.py">CredentialDeleteResponse</a></code>
- <code title="post /v5/credentials/{credential_id}/secret">client.credentials.<a href="./src/scale_gp_beta/resources/credentials.py">decrypt</a>(credential_id) -> <a href="./src/scale_gp_beta/types/credential_secret.py">CredentialSecret</a></code>
- <code title="post /v5/credentials/name/{credential_name}/secret">client.credentials.<a href="./src/scale_gp_beta/resources/credentials.py">decrypt_by_name</a>(credential_name) -> <a href="./src/scale_gp_beta/types/credential_secret.py">CredentialSecret</a></code>
- <code title="get /v5/credentials/name/{credential_name}">client.credentials.<a href="./src/scale_gp_beta/resources/credentials.py">retrieve_by_name</a>(credential_name) -> <a href="./src/scale_gp_beta/types/credential.py">Credential</a></code>
