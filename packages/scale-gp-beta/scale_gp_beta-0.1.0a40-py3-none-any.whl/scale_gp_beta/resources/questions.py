# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Any, Dict, Iterable, cast
from typing_extensions import Literal, overload

import httpx

from ..types import question_list_params, question_create_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
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
from ..types.question import Question

__all__ = ["QuestionsResource", "AsyncQuestionsResource"]


class QuestionsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> QuestionsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/scaleapi/sgp-python-beta#accessing-raw-response-data-eg-headers
        """
        return QuestionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> QuestionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/scaleapi/sgp-python-beta#with_streaming_response
        """
        return QuestionsResourceWithStreamingResponse(self)

    @overload
    def create(
        self,
        *,
        configuration: question_create_params.CategoricalQuestionRequestConfiguration,
        name: str,
        prompt: str,
        conditions: Iterable[Dict[str, object]] | Omit = omit,
        question_type: Literal["categorical"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Question:
        """
        Create Question

        Args:
          prompt: user-facing question prompt

          conditions: Conditions for the question to be shown

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
        configuration: question_create_params.RatingQuestionRequestConfiguration,
        name: str,
        prompt: str,
        conditions: Iterable[Dict[str, object]] | Omit = omit,
        question_type: Literal["rating"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Question:
        """
        Create Question

        Args:
          prompt: user-facing question prompt

          conditions: Conditions for the question to be shown

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
        name: str,
        prompt: str,
        conditions: Iterable[Dict[str, object]] | Omit = omit,
        configuration: question_create_params.NumberQuestionRequestConfiguration | Omit = omit,
        question_type: Literal["number"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Question:
        """
        Create Question

        Args:
          prompt: user-facing question prompt

          conditions: Conditions for the question to be shown

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
        name: str,
        prompt: str,
        conditions: Iterable[Dict[str, object]] | Omit = omit,
        configuration: question_create_params.FreeTextQuestionRequestConfiguration | Omit = omit,
        question_type: Literal["free_text"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Question:
        """
        Create Question

        Args:
          prompt: user-facing question prompt

          conditions: Conditions for the question to be shown

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
        configuration: question_create_params.FormQuestionRequestConfiguration,
        name: str,
        prompt: str,
        conditions: Iterable[Dict[str, object]] | Omit = omit,
        question_type: Literal["form"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Question:
        """
        Create Question

        Args:
          prompt: user-facing question prompt

          conditions: Conditions for the question to be shown

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
        name: str,
        prompt: str,
        conditions: Iterable[Dict[str, object]] | Omit = omit,
        configuration: question_create_params.TimestampQuestionRequestConfiguration | Omit = omit,
        question_type: Literal["timestamp"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Question:
        """
        Create Question

        Args:
          prompt: user-facing question prompt

          conditions: Conditions for the question to be shown

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @required_args(["configuration", "name", "prompt"], ["name", "prompt"])
    def create(
        self,
        *,
        configuration: question_create_params.CategoricalQuestionRequestConfiguration
        | question_create_params.RatingQuestionRequestConfiguration
        | question_create_params.NumberQuestionRequestConfiguration
        | question_create_params.FreeTextQuestionRequestConfiguration
        | question_create_params.FormQuestionRequestConfiguration
        | question_create_params.TimestampQuestionRequestConfiguration
        | Omit = omit,
        name: str,
        prompt: str,
        conditions: Iterable[Dict[str, object]] | Omit = omit,
        question_type: Literal["categorical"]
        | Literal["rating"]
        | Literal["number"]
        | Literal["free_text"]
        | Literal["form"]
        | Literal["timestamp"]
        | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Question:
        return cast(
            Question,
            self._post(
                "/v5/questions",
                body=maybe_transform(
                    {
                        "configuration": configuration,
                        "name": name,
                        "prompt": prompt,
                        "conditions": conditions,
                        "question_type": question_type,
                    },
                    question_create_params.QuestionCreateParams,
                ),
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(Any, Question),  # Union types cannot be passed in as arguments in the type system
            ),
        )

    def retrieve(
        self,
        question_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Question:
        """
        Get Question

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not question_id:
            raise ValueError(f"Expected a non-empty value for `question_id` but received {question_id!r}")
        return cast(
            Question,
            self._get(
                f"/v5/questions/{question_id}",
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(Any, Question),  # Union types cannot be passed in as arguments in the type system
            ),
        )

    def list(
        self,
        *,
        ending_before: str | Omit = omit,
        limit: int | Omit = omit,
        sort_by: str | Omit = omit,
        sort_order: Literal["asc", "desc"] | Omit = omit,
        starting_after: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursorPage[Question]:
        """
        List Questions

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/v5/questions",
            page=SyncCursorPage[Question],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "ending_before": ending_before,
                        "limit": limit,
                        "sort_by": sort_by,
                        "sort_order": sort_order,
                        "starting_after": starting_after,
                    },
                    question_list_params.QuestionListParams,
                ),
            ),
            model=cast(Any, Question),  # Union types cannot be passed in as arguments in the type system
        )


class AsyncQuestionsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncQuestionsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/scaleapi/sgp-python-beta#accessing-raw-response-data-eg-headers
        """
        return AsyncQuestionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncQuestionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/scaleapi/sgp-python-beta#with_streaming_response
        """
        return AsyncQuestionsResourceWithStreamingResponse(self)

    @overload
    async def create(
        self,
        *,
        configuration: question_create_params.CategoricalQuestionRequestConfiguration,
        name: str,
        prompt: str,
        conditions: Iterable[Dict[str, object]] | Omit = omit,
        question_type: Literal["categorical"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Question:
        """
        Create Question

        Args:
          prompt: user-facing question prompt

          conditions: Conditions for the question to be shown

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
        configuration: question_create_params.RatingQuestionRequestConfiguration,
        name: str,
        prompt: str,
        conditions: Iterable[Dict[str, object]] | Omit = omit,
        question_type: Literal["rating"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Question:
        """
        Create Question

        Args:
          prompt: user-facing question prompt

          conditions: Conditions for the question to be shown

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
        name: str,
        prompt: str,
        conditions: Iterable[Dict[str, object]] | Omit = omit,
        configuration: question_create_params.NumberQuestionRequestConfiguration | Omit = omit,
        question_type: Literal["number"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Question:
        """
        Create Question

        Args:
          prompt: user-facing question prompt

          conditions: Conditions for the question to be shown

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
        name: str,
        prompt: str,
        conditions: Iterable[Dict[str, object]] | Omit = omit,
        configuration: question_create_params.FreeTextQuestionRequestConfiguration | Omit = omit,
        question_type: Literal["free_text"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Question:
        """
        Create Question

        Args:
          prompt: user-facing question prompt

          conditions: Conditions for the question to be shown

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
        configuration: question_create_params.FormQuestionRequestConfiguration,
        name: str,
        prompt: str,
        conditions: Iterable[Dict[str, object]] | Omit = omit,
        question_type: Literal["form"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Question:
        """
        Create Question

        Args:
          prompt: user-facing question prompt

          conditions: Conditions for the question to be shown

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
        name: str,
        prompt: str,
        conditions: Iterable[Dict[str, object]] | Omit = omit,
        configuration: question_create_params.TimestampQuestionRequestConfiguration | Omit = omit,
        question_type: Literal["timestamp"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Question:
        """
        Create Question

        Args:
          prompt: user-facing question prompt

          conditions: Conditions for the question to be shown

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @required_args(["configuration", "name", "prompt"], ["name", "prompt"])
    async def create(
        self,
        *,
        configuration: question_create_params.CategoricalQuestionRequestConfiguration
        | question_create_params.RatingQuestionRequestConfiguration
        | question_create_params.NumberQuestionRequestConfiguration
        | question_create_params.FreeTextQuestionRequestConfiguration
        | question_create_params.FormQuestionRequestConfiguration
        | question_create_params.TimestampQuestionRequestConfiguration
        | Omit = omit,
        name: str,
        prompt: str,
        conditions: Iterable[Dict[str, object]] | Omit = omit,
        question_type: Literal["categorical"]
        | Literal["rating"]
        | Literal["number"]
        | Literal["free_text"]
        | Literal["form"]
        | Literal["timestamp"]
        | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Question:
        return cast(
            Question,
            await self._post(
                "/v5/questions",
                body=await async_maybe_transform(
                    {
                        "configuration": configuration,
                        "name": name,
                        "prompt": prompt,
                        "conditions": conditions,
                        "question_type": question_type,
                    },
                    question_create_params.QuestionCreateParams,
                ),
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(Any, Question),  # Union types cannot be passed in as arguments in the type system
            ),
        )

    async def retrieve(
        self,
        question_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Question:
        """
        Get Question

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not question_id:
            raise ValueError(f"Expected a non-empty value for `question_id` but received {question_id!r}")
        return cast(
            Question,
            await self._get(
                f"/v5/questions/{question_id}",
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(Any, Question),  # Union types cannot be passed in as arguments in the type system
            ),
        )

    def list(
        self,
        *,
        ending_before: str | Omit = omit,
        limit: int | Omit = omit,
        sort_by: str | Omit = omit,
        sort_order: Literal["asc", "desc"] | Omit = omit,
        starting_after: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[Question, AsyncCursorPage[Question]]:
        """
        List Questions

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/v5/questions",
            page=AsyncCursorPage[Question],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "ending_before": ending_before,
                        "limit": limit,
                        "sort_by": sort_by,
                        "sort_order": sort_order,
                        "starting_after": starting_after,
                    },
                    question_list_params.QuestionListParams,
                ),
            ),
            model=cast(Any, Question),  # Union types cannot be passed in as arguments in the type system
        )


class QuestionsResourceWithRawResponse:
    def __init__(self, questions: QuestionsResource) -> None:
        self._questions = questions

        self.create = to_raw_response_wrapper(
            questions.create,
        )
        self.retrieve = to_raw_response_wrapper(
            questions.retrieve,
        )
        self.list = to_raw_response_wrapper(
            questions.list,
        )


class AsyncQuestionsResourceWithRawResponse:
    def __init__(self, questions: AsyncQuestionsResource) -> None:
        self._questions = questions

        self.create = async_to_raw_response_wrapper(
            questions.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            questions.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            questions.list,
        )


class QuestionsResourceWithStreamingResponse:
    def __init__(self, questions: QuestionsResource) -> None:
        self._questions = questions

        self.create = to_streamed_response_wrapper(
            questions.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            questions.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            questions.list,
        )


class AsyncQuestionsResourceWithStreamingResponse:
    def __init__(self, questions: AsyncQuestionsResource) -> None:
        self._questions = questions

        self.create = async_to_streamed_response_wrapper(
            questions.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            questions.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            questions.list,
        )
