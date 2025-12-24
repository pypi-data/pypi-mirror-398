# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from scale_gp_beta import SGPClient, AsyncSGPClient
from scale_gp_beta.types import Question
from scale_gp_beta.pagination import SyncCursorPage, AsyncCursorPage

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestQuestions:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create_overload_1(self, client: SGPClient) -> None:
        question = client.questions.create(
            configuration={"choices": ["string"]},
            name="name",
            prompt="prompt",
        )
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    def test_method_create_with_all_params_overload_1(self, client: SGPClient) -> None:
        question = client.questions.create(
            configuration={
                "choices": ["string"],
                "dropdown": True,
                "multi": True,
            },
            name="name",
            prompt="prompt",
            conditions=[{"foo": "bar"}],
            question_type="categorical",
        )
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    def test_raw_response_create_overload_1(self, client: SGPClient) -> None:
        response = client.questions.with_raw_response.create(
            configuration={"choices": ["string"]},
            name="name",
            prompt="prompt",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        question = response.parse()
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    def test_streaming_response_create_overload_1(self, client: SGPClient) -> None:
        with client.questions.with_streaming_response.create(
            configuration={"choices": ["string"]},
            name="name",
            prompt="prompt",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            question = response.parse()
            assert_matches_type(Question, question, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_create_overload_2(self, client: SGPClient) -> None:
        question = client.questions.create(
            configuration={
                "max_label": "max_label",
                "min_label": "min_label",
                "steps": 1,
            },
            name="name",
            prompt="prompt",
        )
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    def test_method_create_with_all_params_overload_2(self, client: SGPClient) -> None:
        question = client.questions.create(
            configuration={
                "max_label": "max_label",
                "min_label": "min_label",
                "steps": 1,
            },
            name="name",
            prompt="prompt",
            conditions=[{"foo": "bar"}],
            question_type="rating",
        )
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    def test_raw_response_create_overload_2(self, client: SGPClient) -> None:
        response = client.questions.with_raw_response.create(
            configuration={
                "max_label": "max_label",
                "min_label": "min_label",
                "steps": 1,
            },
            name="name",
            prompt="prompt",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        question = response.parse()
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    def test_streaming_response_create_overload_2(self, client: SGPClient) -> None:
        with client.questions.with_streaming_response.create(
            configuration={
                "max_label": "max_label",
                "min_label": "min_label",
                "steps": 1,
            },
            name="name",
            prompt="prompt",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            question = response.parse()
            assert_matches_type(Question, question, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_create_overload_3(self, client: SGPClient) -> None:
        question = client.questions.create(
            name="name",
            prompt="prompt",
        )
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    def test_method_create_with_all_params_overload_3(self, client: SGPClient) -> None:
        question = client.questions.create(
            name="name",
            prompt="prompt",
            conditions=[{"foo": "bar"}],
            configuration={
                "max": 0,
                "min": 0,
            },
            question_type="number",
        )
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    def test_raw_response_create_overload_3(self, client: SGPClient) -> None:
        response = client.questions.with_raw_response.create(
            name="name",
            prompt="prompt",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        question = response.parse()
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    def test_streaming_response_create_overload_3(self, client: SGPClient) -> None:
        with client.questions.with_streaming_response.create(
            name="name",
            prompt="prompt",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            question = response.parse()
            assert_matches_type(Question, question, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_create_overload_4(self, client: SGPClient) -> None:
        question = client.questions.create(
            name="name",
            prompt="prompt",
        )
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    def test_method_create_with_all_params_overload_4(self, client: SGPClient) -> None:
        question = client.questions.create(
            name="name",
            prompt="prompt",
            conditions=[{"foo": "bar"}],
            configuration={
                "max_length": 1,
                "min_length": 0,
            },
            question_type="free_text",
        )
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    def test_raw_response_create_overload_4(self, client: SGPClient) -> None:
        response = client.questions.with_raw_response.create(
            name="name",
            prompt="prompt",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        question = response.parse()
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    def test_streaming_response_create_overload_4(self, client: SGPClient) -> None:
        with client.questions.with_streaming_response.create(
            name="name",
            prompt="prompt",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            question = response.parse()
            assert_matches_type(Question, question, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_create_overload_5(self, client: SGPClient) -> None:
        question = client.questions.create(
            configuration={"form_schema": {"foo": "bar"}},
            name="name",
            prompt="prompt",
        )
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    def test_method_create_with_all_params_overload_5(self, client: SGPClient) -> None:
        question = client.questions.create(
            configuration={"form_schema": {"foo": "bar"}},
            name="name",
            prompt="prompt",
            conditions=[{"foo": "bar"}],
            question_type="form",
        )
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    def test_raw_response_create_overload_5(self, client: SGPClient) -> None:
        response = client.questions.with_raw_response.create(
            configuration={"form_schema": {"foo": "bar"}},
            name="name",
            prompt="prompt",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        question = response.parse()
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    def test_streaming_response_create_overload_5(self, client: SGPClient) -> None:
        with client.questions.with_streaming_response.create(
            configuration={"form_schema": {"foo": "bar"}},
            name="name",
            prompt="prompt",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            question = response.parse()
            assert_matches_type(Question, question, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_create_overload_6(self, client: SGPClient) -> None:
        question = client.questions.create(
            name="name",
            prompt="prompt",
        )
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    def test_method_create_with_all_params_overload_6(self, client: SGPClient) -> None:
        question = client.questions.create(
            name="name",
            prompt="prompt",
            conditions=[{"foo": "bar"}],
            configuration={"multi": True},
            question_type="timestamp",
        )
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    def test_raw_response_create_overload_6(self, client: SGPClient) -> None:
        response = client.questions.with_raw_response.create(
            name="name",
            prompt="prompt",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        question = response.parse()
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    def test_streaming_response_create_overload_6(self, client: SGPClient) -> None:
        with client.questions.with_streaming_response.create(
            name="name",
            prompt="prompt",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            question = response.parse()
            assert_matches_type(Question, question, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_retrieve(self, client: SGPClient) -> None:
        question = client.questions.retrieve(
            "question_id",
        )
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: SGPClient) -> None:
        response = client.questions.with_raw_response.retrieve(
            "question_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        question = response.parse()
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: SGPClient) -> None:
        with client.questions.with_streaming_response.retrieve(
            "question_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            question = response.parse()
            assert_matches_type(Question, question, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: SGPClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `question_id` but received ''"):
            client.questions.with_raw_response.retrieve(
                "",
            )

    @parametrize
    def test_method_list(self, client: SGPClient) -> None:
        question = client.questions.list()
        assert_matches_type(SyncCursorPage[Question], question, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: SGPClient) -> None:
        question = client.questions.list(
            ending_before="ending_before",
            limit=1,
            sort_by="sort_by",
            sort_order="asc",
            starting_after="starting_after",
        )
        assert_matches_type(SyncCursorPage[Question], question, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: SGPClient) -> None:
        response = client.questions.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        question = response.parse()
        assert_matches_type(SyncCursorPage[Question], question, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: SGPClient) -> None:
        with client.questions.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            question = response.parse()
            assert_matches_type(SyncCursorPage[Question], question, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncQuestions:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create_overload_1(self, async_client: AsyncSGPClient) -> None:
        question = await async_client.questions.create(
            configuration={"choices": ["string"]},
            name="name",
            prompt="prompt",
        )
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    async def test_method_create_with_all_params_overload_1(self, async_client: AsyncSGPClient) -> None:
        question = await async_client.questions.create(
            configuration={
                "choices": ["string"],
                "dropdown": True,
                "multi": True,
            },
            name="name",
            prompt="prompt",
            conditions=[{"foo": "bar"}],
            question_type="categorical",
        )
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    async def test_raw_response_create_overload_1(self, async_client: AsyncSGPClient) -> None:
        response = await async_client.questions.with_raw_response.create(
            configuration={"choices": ["string"]},
            name="name",
            prompt="prompt",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        question = await response.parse()
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    async def test_streaming_response_create_overload_1(self, async_client: AsyncSGPClient) -> None:
        async with async_client.questions.with_streaming_response.create(
            configuration={"choices": ["string"]},
            name="name",
            prompt="prompt",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            question = await response.parse()
            assert_matches_type(Question, question, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_create_overload_2(self, async_client: AsyncSGPClient) -> None:
        question = await async_client.questions.create(
            configuration={
                "max_label": "max_label",
                "min_label": "min_label",
                "steps": 1,
            },
            name="name",
            prompt="prompt",
        )
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    async def test_method_create_with_all_params_overload_2(self, async_client: AsyncSGPClient) -> None:
        question = await async_client.questions.create(
            configuration={
                "max_label": "max_label",
                "min_label": "min_label",
                "steps": 1,
            },
            name="name",
            prompt="prompt",
            conditions=[{"foo": "bar"}],
            question_type="rating",
        )
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    async def test_raw_response_create_overload_2(self, async_client: AsyncSGPClient) -> None:
        response = await async_client.questions.with_raw_response.create(
            configuration={
                "max_label": "max_label",
                "min_label": "min_label",
                "steps": 1,
            },
            name="name",
            prompt="prompt",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        question = await response.parse()
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    async def test_streaming_response_create_overload_2(self, async_client: AsyncSGPClient) -> None:
        async with async_client.questions.with_streaming_response.create(
            configuration={
                "max_label": "max_label",
                "min_label": "min_label",
                "steps": 1,
            },
            name="name",
            prompt="prompt",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            question = await response.parse()
            assert_matches_type(Question, question, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_create_overload_3(self, async_client: AsyncSGPClient) -> None:
        question = await async_client.questions.create(
            name="name",
            prompt="prompt",
        )
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    async def test_method_create_with_all_params_overload_3(self, async_client: AsyncSGPClient) -> None:
        question = await async_client.questions.create(
            name="name",
            prompt="prompt",
            conditions=[{"foo": "bar"}],
            configuration={
                "max": 0,
                "min": 0,
            },
            question_type="number",
        )
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    async def test_raw_response_create_overload_3(self, async_client: AsyncSGPClient) -> None:
        response = await async_client.questions.with_raw_response.create(
            name="name",
            prompt="prompt",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        question = await response.parse()
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    async def test_streaming_response_create_overload_3(self, async_client: AsyncSGPClient) -> None:
        async with async_client.questions.with_streaming_response.create(
            name="name",
            prompt="prompt",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            question = await response.parse()
            assert_matches_type(Question, question, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_create_overload_4(self, async_client: AsyncSGPClient) -> None:
        question = await async_client.questions.create(
            name="name",
            prompt="prompt",
        )
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    async def test_method_create_with_all_params_overload_4(self, async_client: AsyncSGPClient) -> None:
        question = await async_client.questions.create(
            name="name",
            prompt="prompt",
            conditions=[{"foo": "bar"}],
            configuration={
                "max_length": 1,
                "min_length": 0,
            },
            question_type="free_text",
        )
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    async def test_raw_response_create_overload_4(self, async_client: AsyncSGPClient) -> None:
        response = await async_client.questions.with_raw_response.create(
            name="name",
            prompt="prompt",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        question = await response.parse()
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    async def test_streaming_response_create_overload_4(self, async_client: AsyncSGPClient) -> None:
        async with async_client.questions.with_streaming_response.create(
            name="name",
            prompt="prompt",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            question = await response.parse()
            assert_matches_type(Question, question, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_create_overload_5(self, async_client: AsyncSGPClient) -> None:
        question = await async_client.questions.create(
            configuration={"form_schema": {"foo": "bar"}},
            name="name",
            prompt="prompt",
        )
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    async def test_method_create_with_all_params_overload_5(self, async_client: AsyncSGPClient) -> None:
        question = await async_client.questions.create(
            configuration={"form_schema": {"foo": "bar"}},
            name="name",
            prompt="prompt",
            conditions=[{"foo": "bar"}],
            question_type="form",
        )
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    async def test_raw_response_create_overload_5(self, async_client: AsyncSGPClient) -> None:
        response = await async_client.questions.with_raw_response.create(
            configuration={"form_schema": {"foo": "bar"}},
            name="name",
            prompt="prompt",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        question = await response.parse()
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    async def test_streaming_response_create_overload_5(self, async_client: AsyncSGPClient) -> None:
        async with async_client.questions.with_streaming_response.create(
            configuration={"form_schema": {"foo": "bar"}},
            name="name",
            prompt="prompt",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            question = await response.parse()
            assert_matches_type(Question, question, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_create_overload_6(self, async_client: AsyncSGPClient) -> None:
        question = await async_client.questions.create(
            name="name",
            prompt="prompt",
        )
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    async def test_method_create_with_all_params_overload_6(self, async_client: AsyncSGPClient) -> None:
        question = await async_client.questions.create(
            name="name",
            prompt="prompt",
            conditions=[{"foo": "bar"}],
            configuration={"multi": True},
            question_type="timestamp",
        )
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    async def test_raw_response_create_overload_6(self, async_client: AsyncSGPClient) -> None:
        response = await async_client.questions.with_raw_response.create(
            name="name",
            prompt="prompt",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        question = await response.parse()
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    async def test_streaming_response_create_overload_6(self, async_client: AsyncSGPClient) -> None:
        async with async_client.questions.with_streaming_response.create(
            name="name",
            prompt="prompt",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            question = await response.parse()
            assert_matches_type(Question, question, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncSGPClient) -> None:
        question = await async_client.questions.retrieve(
            "question_id",
        )
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncSGPClient) -> None:
        response = await async_client.questions.with_raw_response.retrieve(
            "question_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        question = await response.parse()
        assert_matches_type(Question, question, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncSGPClient) -> None:
        async with async_client.questions.with_streaming_response.retrieve(
            "question_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            question = await response.parse()
            assert_matches_type(Question, question, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncSGPClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `question_id` but received ''"):
            await async_client.questions.with_raw_response.retrieve(
                "",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncSGPClient) -> None:
        question = await async_client.questions.list()
        assert_matches_type(AsyncCursorPage[Question], question, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncSGPClient) -> None:
        question = await async_client.questions.list(
            ending_before="ending_before",
            limit=1,
            sort_by="sort_by",
            sort_order="asc",
            starting_after="starting_after",
        )
        assert_matches_type(AsyncCursorPage[Question], question, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncSGPClient) -> None:
        response = await async_client.questions.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        question = await response.parse()
        assert_matches_type(AsyncCursorPage[Question], question, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncSGPClient) -> None:
        async with async_client.questions.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            question = await response.parse()
            assert_matches_type(AsyncCursorPage[Question], question, path=["response"])

        assert cast(Any, response.is_closed) is True
