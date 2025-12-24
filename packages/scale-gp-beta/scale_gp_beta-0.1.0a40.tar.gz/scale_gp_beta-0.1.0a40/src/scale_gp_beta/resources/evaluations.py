# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, List, Iterable
from typing_extensions import Literal, overload

import httpx

from ..types import (
    evaluation_list_params,
    evaluation_create_params,
    evaluation_update_params,
    evaluation_retrieve_params,
)
from .._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from .._utils import required_args, maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..pagination import SyncCursorPage, AsyncCursorPage
from .._base_client import AsyncPaginator, make_request_options
from ..types.evaluation import Evaluation
from ..types.evaluation_task_param import EvaluationTaskParam

__all__ = ["EvaluationsResource", "AsyncEvaluationsResource"]


class EvaluationsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> EvaluationsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/scaleapi/sgp-python-beta#accessing-raw-response-data-eg-headers
        """
        return EvaluationsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> EvaluationsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/scaleapi/sgp-python-beta#with_streaming_response
        """
        return EvaluationsResourceWithStreamingResponse(self)

    @overload
    def create(
        self,
        *,
        data: Iterable[Dict[str, object]],
        name: str,
        description: str | Omit = omit,
        files: Iterable[Dict[str, str]] | Omit = omit,
        metadata: Dict[str, object] | Omit = omit,
        tags: SequenceNotStr[str] | Omit = omit,
        tasks: Iterable[EvaluationTaskParam] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Evaluation:
        """
        Create Evaluation

        Args:
          data: Items to be evaluated

          files: Files to be associated to the evaluation

          metadata: Optional metadata key-value pairs for the evaluation

          tags: The tags associated with the entity

          tasks: Tasks allow you to augment and evaluate your data

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @overload
    def create(
        self,
        *,
        dataset_id: str,
        name: str,
        data: Iterable[evaluation_create_params.EvaluationFromDatasetCreateRequestData] | Omit = omit,
        description: str | Omit = omit,
        metadata: Dict[str, object] | Omit = omit,
        tags: SequenceNotStr[str] | Omit = omit,
        tasks: Iterable[EvaluationTaskParam] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Evaluation:
        """
        Create Evaluation

        Args:
          dataset_id: The ID of the dataset containing the items referenced by the `data` field

          data: Items to be evaluated, including references to the input dataset

          metadata: Optional metadata key-value pairs for the evaluation

          tags: The tags associated with the entity

          tasks: Tasks allow you to augment and evaluate your data

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @overload
    def create(
        self,
        *,
        data: Iterable[Dict[str, object]],
        dataset: evaluation_create_params.EvaluationWithDatasetCreateRequestDataset,
        name: str,
        description: str | Omit = omit,
        files: Iterable[Dict[str, str]] | Omit = omit,
        metadata: Dict[str, object] | Omit = omit,
        tags: SequenceNotStr[str] | Omit = omit,
        tasks: Iterable[EvaluationTaskParam] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Evaluation:
        """
        Create Evaluation

        Args:
          data: Items to be evaluated

          dataset: Create a reusable dataset from items in the `data` field

          files: Files to be associated to the evaluation

          metadata: Optional metadata key-value pairs for the evaluation

          tags: The tags associated with the entity

          tasks: Tasks allow you to augment and evaluate your data

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @required_args(["data", "name"], ["dataset_id", "name"], ["data", "dataset", "name"])
    def create(
        self,
        *,
        data: Iterable[Dict[str, object]]
        | Iterable[evaluation_create_params.EvaluationFromDatasetCreateRequestData]
        | Omit = omit,
        name: str,
        description: str | Omit = omit,
        files: Iterable[Dict[str, str]] | Omit = omit,
        metadata: Dict[str, object] | Omit = omit,
        tags: SequenceNotStr[str] | Omit = omit,
        tasks: Iterable[EvaluationTaskParam] | Omit = omit,
        dataset_id: str | Omit = omit,
        dataset: evaluation_create_params.EvaluationWithDatasetCreateRequestDataset | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Evaluation:
        return self._post(
            "/v5/evaluations",
            body=maybe_transform(
                {
                    "data": data,
                    "name": name,
                    "description": description,
                    "files": files,
                    "metadata": metadata,
                    "tags": tags,
                    "tasks": tasks,
                    "dataset_id": dataset_id,
                    "dataset": dataset,
                },
                evaluation_create_params.EvaluationCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Evaluation,
        )

    def retrieve(
        self,
        evaluation_id: str,
        *,
        include_archived: bool | Omit = omit,
        views: List[Literal["tasks"]] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Evaluation:
        """
        Get Evaluation

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not evaluation_id:
            raise ValueError(f"Expected a non-empty value for `evaluation_id` but received {evaluation_id!r}")
        return self._get(
            f"/v5/evaluations/{evaluation_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "include_archived": include_archived,
                        "views": views,
                    },
                    evaluation_retrieve_params.EvaluationRetrieveParams,
                ),
            ),
            cast_to=Evaluation,
        )

    @overload
    def update(
        self,
        evaluation_id: str,
        *,
        description: str | Omit = omit,
        name: str | Omit = omit,
        tags: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Evaluation:
        """
        Update or Restore Evaluation

        Args:
          tags: The tags associated with the entity

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @overload
    def update(
        self,
        evaluation_id: str,
        *,
        restore: Literal[True],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Evaluation:
        """
        Update or Restore Evaluation

        Args:
          restore: Set to true to restore the entity from the database.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    def update(
        self,
        evaluation_id: str,
        *,
        description: str | Omit = omit,
        name: str | Omit = omit,
        tags: SequenceNotStr[str] | Omit = omit,
        restore: Literal[True] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Evaluation:
        if not evaluation_id:
            raise ValueError(f"Expected a non-empty value for `evaluation_id` but received {evaluation_id!r}")
        return self._patch(
            f"/v5/evaluations/{evaluation_id}",
            body=maybe_transform(
                {
                    "description": description,
                    "name": name,
                    "tags": tags,
                    "restore": restore,
                },
                evaluation_update_params.EvaluationUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Evaluation,
        )

    def list(
        self,
        *,
        ending_before: str | Omit = omit,
        include_archived: bool | Omit = omit,
        limit: int | Omit = omit,
        name: str | Omit = omit,
        sort_by: str | Omit = omit,
        sort_order: Literal["asc", "desc"] | Omit = omit,
        starting_after: str | Omit = omit,
        tags: SequenceNotStr[str] | Omit = omit,
        views: List[Literal["tasks"]] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursorPage[Evaluation]:
        """
        List Evaluations

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/v5/evaluations",
            page=SyncCursorPage[Evaluation],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "ending_before": ending_before,
                        "include_archived": include_archived,
                        "limit": limit,
                        "name": name,
                        "sort_by": sort_by,
                        "sort_order": sort_order,
                        "starting_after": starting_after,
                        "tags": tags,
                        "views": views,
                    },
                    evaluation_list_params.EvaluationListParams,
                ),
            ),
            model=Evaluation,
        )

    def delete(
        self,
        evaluation_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Evaluation:
        """
        Archive Evaluation

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not evaluation_id:
            raise ValueError(f"Expected a non-empty value for `evaluation_id` but received {evaluation_id!r}")
        return self._delete(
            f"/v5/evaluations/{evaluation_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Evaluation,
        )


class AsyncEvaluationsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncEvaluationsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/scaleapi/sgp-python-beta#accessing-raw-response-data-eg-headers
        """
        return AsyncEvaluationsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncEvaluationsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/scaleapi/sgp-python-beta#with_streaming_response
        """
        return AsyncEvaluationsResourceWithStreamingResponse(self)

    @overload
    async def create(
        self,
        *,
        data: Iterable[Dict[str, object]],
        name: str,
        description: str | Omit = omit,
        files: Iterable[Dict[str, str]] | Omit = omit,
        metadata: Dict[str, object] | Omit = omit,
        tags: SequenceNotStr[str] | Omit = omit,
        tasks: Iterable[EvaluationTaskParam] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Evaluation:
        """
        Create Evaluation

        Args:
          data: Items to be evaluated

          files: Files to be associated to the evaluation

          metadata: Optional metadata key-value pairs for the evaluation

          tags: The tags associated with the entity

          tasks: Tasks allow you to augment and evaluate your data

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @overload
    async def create(
        self,
        *,
        dataset_id: str,
        name: str,
        data: Iterable[evaluation_create_params.EvaluationFromDatasetCreateRequestData] | Omit = omit,
        description: str | Omit = omit,
        metadata: Dict[str, object] | Omit = omit,
        tags: SequenceNotStr[str] | Omit = omit,
        tasks: Iterable[EvaluationTaskParam] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Evaluation:
        """
        Create Evaluation

        Args:
          dataset_id: The ID of the dataset containing the items referenced by the `data` field

          data: Items to be evaluated, including references to the input dataset

          metadata: Optional metadata key-value pairs for the evaluation

          tags: The tags associated with the entity

          tasks: Tasks allow you to augment and evaluate your data

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @overload
    async def create(
        self,
        *,
        data: Iterable[Dict[str, object]],
        dataset: evaluation_create_params.EvaluationWithDatasetCreateRequestDataset,
        name: str,
        description: str | Omit = omit,
        files: Iterable[Dict[str, str]] | Omit = omit,
        metadata: Dict[str, object] | Omit = omit,
        tags: SequenceNotStr[str] | Omit = omit,
        tasks: Iterable[EvaluationTaskParam] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Evaluation:
        """
        Create Evaluation

        Args:
          data: Items to be evaluated

          dataset: Create a reusable dataset from items in the `data` field

          files: Files to be associated to the evaluation

          metadata: Optional metadata key-value pairs for the evaluation

          tags: The tags associated with the entity

          tasks: Tasks allow you to augment and evaluate your data

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @required_args(["data", "name"], ["dataset_id", "name"], ["data", "dataset", "name"])
    async def create(
        self,
        *,
        data: Iterable[Dict[str, object]]
        | Iterable[evaluation_create_params.EvaluationFromDatasetCreateRequestData]
        | Omit = omit,
        name: str,
        description: str | Omit = omit,
        files: Iterable[Dict[str, str]] | Omit = omit,
        metadata: Dict[str, object] | Omit = omit,
        tags: SequenceNotStr[str] | Omit = omit,
        tasks: Iterable[EvaluationTaskParam] | Omit = omit,
        dataset_id: str | Omit = omit,
        dataset: evaluation_create_params.EvaluationWithDatasetCreateRequestDataset | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Evaluation:
        return await self._post(
            "/v5/evaluations",
            body=await async_maybe_transform(
                {
                    "data": data,
                    "name": name,
                    "description": description,
                    "files": files,
                    "metadata": metadata,
                    "tags": tags,
                    "tasks": tasks,
                    "dataset_id": dataset_id,
                    "dataset": dataset,
                },
                evaluation_create_params.EvaluationCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Evaluation,
        )

    async def retrieve(
        self,
        evaluation_id: str,
        *,
        include_archived: bool | Omit = omit,
        views: List[Literal["tasks"]] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Evaluation:
        """
        Get Evaluation

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not evaluation_id:
            raise ValueError(f"Expected a non-empty value for `evaluation_id` but received {evaluation_id!r}")
        return await self._get(
            f"/v5/evaluations/{evaluation_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "include_archived": include_archived,
                        "views": views,
                    },
                    evaluation_retrieve_params.EvaluationRetrieveParams,
                ),
            ),
            cast_to=Evaluation,
        )

    @overload
    async def update(
        self,
        evaluation_id: str,
        *,
        description: str | Omit = omit,
        name: str | Omit = omit,
        tags: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Evaluation:
        """
        Update or Restore Evaluation

        Args:
          tags: The tags associated with the entity

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @overload
    async def update(
        self,
        evaluation_id: str,
        *,
        restore: Literal[True],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Evaluation:
        """
        Update or Restore Evaluation

        Args:
          restore: Set to true to restore the entity from the database.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    async def update(
        self,
        evaluation_id: str,
        *,
        description: str | Omit = omit,
        name: str | Omit = omit,
        tags: SequenceNotStr[str] | Omit = omit,
        restore: Literal[True] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Evaluation:
        if not evaluation_id:
            raise ValueError(f"Expected a non-empty value for `evaluation_id` but received {evaluation_id!r}")
        return await self._patch(
            f"/v5/evaluations/{evaluation_id}",
            body=await async_maybe_transform(
                {
                    "description": description,
                    "name": name,
                    "tags": tags,
                    "restore": restore,
                },
                evaluation_update_params.EvaluationUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Evaluation,
        )

    def list(
        self,
        *,
        ending_before: str | Omit = omit,
        include_archived: bool | Omit = omit,
        limit: int | Omit = omit,
        name: str | Omit = omit,
        sort_by: str | Omit = omit,
        sort_order: Literal["asc", "desc"] | Omit = omit,
        starting_after: str | Omit = omit,
        tags: SequenceNotStr[str] | Omit = omit,
        views: List[Literal["tasks"]] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[Evaluation, AsyncCursorPage[Evaluation]]:
        """
        List Evaluations

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/v5/evaluations",
            page=AsyncCursorPage[Evaluation],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "ending_before": ending_before,
                        "include_archived": include_archived,
                        "limit": limit,
                        "name": name,
                        "sort_by": sort_by,
                        "sort_order": sort_order,
                        "starting_after": starting_after,
                        "tags": tags,
                        "views": views,
                    },
                    evaluation_list_params.EvaluationListParams,
                ),
            ),
            model=Evaluation,
        )

    async def delete(
        self,
        evaluation_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Evaluation:
        """
        Archive Evaluation

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not evaluation_id:
            raise ValueError(f"Expected a non-empty value for `evaluation_id` but received {evaluation_id!r}")
        return await self._delete(
            f"/v5/evaluations/{evaluation_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Evaluation,
        )


class EvaluationsResourceWithRawResponse:
    def __init__(self, evaluations: EvaluationsResource) -> None:
        self._evaluations = evaluations

        self.create = to_raw_response_wrapper(
            evaluations.create,
        )
        self.retrieve = to_raw_response_wrapper(
            evaluations.retrieve,
        )
        self.update = to_raw_response_wrapper(
            evaluations.update,
        )
        self.list = to_raw_response_wrapper(
            evaluations.list,
        )
        self.delete = to_raw_response_wrapper(
            evaluations.delete,
        )


class AsyncEvaluationsResourceWithRawResponse:
    def __init__(self, evaluations: AsyncEvaluationsResource) -> None:
        self._evaluations = evaluations

        self.create = async_to_raw_response_wrapper(
            evaluations.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            evaluations.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            evaluations.update,
        )
        self.list = async_to_raw_response_wrapper(
            evaluations.list,
        )
        self.delete = async_to_raw_response_wrapper(
            evaluations.delete,
        )


class EvaluationsResourceWithStreamingResponse:
    def __init__(self, evaluations: EvaluationsResource) -> None:
        self._evaluations = evaluations

        self.create = to_streamed_response_wrapper(
            evaluations.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            evaluations.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            evaluations.update,
        )
        self.list = to_streamed_response_wrapper(
            evaluations.list,
        )
        self.delete = to_streamed_response_wrapper(
            evaluations.delete,
        )


class AsyncEvaluationsResourceWithStreamingResponse:
    def __init__(self, evaluations: AsyncEvaluationsResource) -> None:
        self._evaluations = evaluations

        self.create = async_to_streamed_response_wrapper(
            evaluations.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            evaluations.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            evaluations.update,
        )
        self.list = async_to_streamed_response_wrapper(
            evaluations.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            evaluations.delete,
        )
