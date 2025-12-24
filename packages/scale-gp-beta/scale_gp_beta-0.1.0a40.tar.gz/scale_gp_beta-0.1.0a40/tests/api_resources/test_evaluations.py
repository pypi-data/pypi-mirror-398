# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from scale_gp_beta import SGPClient, AsyncSGPClient
from scale_gp_beta.types import (
    Evaluation,
)
from scale_gp_beta.pagination import SyncCursorPage, AsyncCursorPage

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestEvaluations:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create_overload_1(self, client: SGPClient) -> None:
        evaluation = client.evaluations.create(
            data=[{"foo": "bar"}],
            name="name",
        )
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    def test_method_create_with_all_params_overload_1(self, client: SGPClient) -> None:
        evaluation = client.evaluations.create(
            data=[{"foo": "bar"}],
            name="name",
            description="description",
            files=[{"foo": "string"}],
            metadata={"foo": "bar"},
            tags=["string"],
            tasks=[
                {
                    "configuration": {
                        "messages": [{"foo": "bar"}],
                        "model": "model",
                        "audio": {"foo": "bar"},
                        "frequency_penalty": 0,
                        "function_call": {"foo": "bar"},
                        "functions": [{"foo": "bar"}],
                        "logit_bias": {"foo": 0},
                        "logprobs": True,
                        "max_completion_tokens": 0,
                        "max_tokens": 0,
                        "metadata": {"foo": "string"},
                        "modalities": ["string"],
                        "n": 0,
                        "parallel_tool_calls": True,
                        "prediction": {"foo": "bar"},
                        "presence_penalty": 0,
                        "reasoning_effort": "reasoning_effort",
                        "response_format": {"foo": "bar"},
                        "seed": 0,
                        "stop": "stop",
                        "store": True,
                        "temperature": 0,
                        "tool_choice": "tool_choice",
                        "tools": [{"foo": "bar"}],
                        "top_k": 0,
                        "top_logprobs": 0,
                        "top_p": 0,
                    },
                    "alias": "alias",
                    "task_type": "chat_completion",
                }
            ],
        )
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    def test_raw_response_create_overload_1(self, client: SGPClient) -> None:
        response = client.evaluations.with_raw_response.create(
            data=[{"foo": "bar"}],
            name="name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluation = response.parse()
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    def test_streaming_response_create_overload_1(self, client: SGPClient) -> None:
        with client.evaluations.with_streaming_response.create(
            data=[{"foo": "bar"}],
            name="name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluation = response.parse()
            assert_matches_type(Evaluation, evaluation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_create_overload_2(self, client: SGPClient) -> None:
        evaluation = client.evaluations.create(
            dataset_id="dataset_id",
            name="name",
        )
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    def test_method_create_with_all_params_overload_2(self, client: SGPClient) -> None:
        evaluation = client.evaluations.create(
            dataset_id="dataset_id",
            name="name",
            data=[{"dataset_item_id": "dataset_item_id"}],
            description="description",
            metadata={"foo": "bar"},
            tags=["string"],
            tasks=[
                {
                    "configuration": {
                        "messages": [{"foo": "bar"}],
                        "model": "model",
                        "audio": {"foo": "bar"},
                        "frequency_penalty": 0,
                        "function_call": {"foo": "bar"},
                        "functions": [{"foo": "bar"}],
                        "logit_bias": {"foo": 0},
                        "logprobs": True,
                        "max_completion_tokens": 0,
                        "max_tokens": 0,
                        "metadata": {"foo": "string"},
                        "modalities": ["string"],
                        "n": 0,
                        "parallel_tool_calls": True,
                        "prediction": {"foo": "bar"},
                        "presence_penalty": 0,
                        "reasoning_effort": "reasoning_effort",
                        "response_format": {"foo": "bar"},
                        "seed": 0,
                        "stop": "stop",
                        "store": True,
                        "temperature": 0,
                        "tool_choice": "tool_choice",
                        "tools": [{"foo": "bar"}],
                        "top_k": 0,
                        "top_logprobs": 0,
                        "top_p": 0,
                    },
                    "alias": "alias",
                    "task_type": "chat_completion",
                }
            ],
        )
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    def test_raw_response_create_overload_2(self, client: SGPClient) -> None:
        response = client.evaluations.with_raw_response.create(
            dataset_id="dataset_id",
            name="name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluation = response.parse()
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    def test_streaming_response_create_overload_2(self, client: SGPClient) -> None:
        with client.evaluations.with_streaming_response.create(
            dataset_id="dataset_id",
            name="name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluation = response.parse()
            assert_matches_type(Evaluation, evaluation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_create_overload_3(self, client: SGPClient) -> None:
        evaluation = client.evaluations.create(
            data=[{"foo": "bar"}],
            dataset={"name": "name"},
            name="name",
        )
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    def test_method_create_with_all_params_overload_3(self, client: SGPClient) -> None:
        evaluation = client.evaluations.create(
            data=[{"foo": "bar"}],
            dataset={
                "name": "name",
                "description": "description",
                "keys": ["string"],
                "tags": ["string"],
            },
            name="name",
            description="description",
            files=[{"foo": "string"}],
            metadata={"foo": "bar"},
            tags=["string"],
            tasks=[
                {
                    "configuration": {
                        "messages": [{"foo": "bar"}],
                        "model": "model",
                        "audio": {"foo": "bar"},
                        "frequency_penalty": 0,
                        "function_call": {"foo": "bar"},
                        "functions": [{"foo": "bar"}],
                        "logit_bias": {"foo": 0},
                        "logprobs": True,
                        "max_completion_tokens": 0,
                        "max_tokens": 0,
                        "metadata": {"foo": "string"},
                        "modalities": ["string"],
                        "n": 0,
                        "parallel_tool_calls": True,
                        "prediction": {"foo": "bar"},
                        "presence_penalty": 0,
                        "reasoning_effort": "reasoning_effort",
                        "response_format": {"foo": "bar"},
                        "seed": 0,
                        "stop": "stop",
                        "store": True,
                        "temperature": 0,
                        "tool_choice": "tool_choice",
                        "tools": [{"foo": "bar"}],
                        "top_k": 0,
                        "top_logprobs": 0,
                        "top_p": 0,
                    },
                    "alias": "alias",
                    "task_type": "chat_completion",
                }
            ],
        )
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    def test_raw_response_create_overload_3(self, client: SGPClient) -> None:
        response = client.evaluations.with_raw_response.create(
            data=[{"foo": "bar"}],
            dataset={"name": "name"},
            name="name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluation = response.parse()
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    def test_streaming_response_create_overload_3(self, client: SGPClient) -> None:
        with client.evaluations.with_streaming_response.create(
            data=[{"foo": "bar"}],
            dataset={"name": "name"},
            name="name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluation = response.parse()
            assert_matches_type(Evaluation, evaluation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_retrieve(self, client: SGPClient) -> None:
        evaluation = client.evaluations.retrieve(
            evaluation_id="evaluation_id",
        )
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    def test_method_retrieve_with_all_params(self, client: SGPClient) -> None:
        evaluation = client.evaluations.retrieve(
            evaluation_id="evaluation_id",
            include_archived=True,
            views=["tasks"],
        )
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: SGPClient) -> None:
        response = client.evaluations.with_raw_response.retrieve(
            evaluation_id="evaluation_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluation = response.parse()
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: SGPClient) -> None:
        with client.evaluations.with_streaming_response.retrieve(
            evaluation_id="evaluation_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluation = response.parse()
            assert_matches_type(Evaluation, evaluation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: SGPClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `evaluation_id` but received ''"):
            client.evaluations.with_raw_response.retrieve(
                evaluation_id="",
            )

    @parametrize
    def test_method_update_overload_1(self, client: SGPClient) -> None:
        evaluation = client.evaluations.update(
            evaluation_id="evaluation_id",
        )
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    def test_method_update_with_all_params_overload_1(self, client: SGPClient) -> None:
        evaluation = client.evaluations.update(
            evaluation_id="evaluation_id",
            description="description",
            name="name",
            tags=["string"],
        )
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    def test_raw_response_update_overload_1(self, client: SGPClient) -> None:
        response = client.evaluations.with_raw_response.update(
            evaluation_id="evaluation_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluation = response.parse()
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    def test_streaming_response_update_overload_1(self, client: SGPClient) -> None:
        with client.evaluations.with_streaming_response.update(
            evaluation_id="evaluation_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluation = response.parse()
            assert_matches_type(Evaluation, evaluation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update_overload_1(self, client: SGPClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `evaluation_id` but received ''"):
            client.evaluations.with_raw_response.update(
                evaluation_id="",
            )

    @parametrize
    def test_method_update_overload_2(self, client: SGPClient) -> None:
        evaluation = client.evaluations.update(
            evaluation_id="evaluation_id",
            restore=True,
        )
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    def test_raw_response_update_overload_2(self, client: SGPClient) -> None:
        response = client.evaluations.with_raw_response.update(
            evaluation_id="evaluation_id",
            restore=True,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluation = response.parse()
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    def test_streaming_response_update_overload_2(self, client: SGPClient) -> None:
        with client.evaluations.with_streaming_response.update(
            evaluation_id="evaluation_id",
            restore=True,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluation = response.parse()
            assert_matches_type(Evaluation, evaluation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update_overload_2(self, client: SGPClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `evaluation_id` but received ''"):
            client.evaluations.with_raw_response.update(
                evaluation_id="",
                restore=True,
            )

    @parametrize
    def test_method_list(self, client: SGPClient) -> None:
        evaluation = client.evaluations.list()
        assert_matches_type(SyncCursorPage[Evaluation], evaluation, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: SGPClient) -> None:
        evaluation = client.evaluations.list(
            ending_before="ending_before",
            include_archived=True,
            limit=1,
            name="name",
            sort_by="sort_by",
            sort_order="asc",
            starting_after="starting_after",
            tags=["string"],
            views=["tasks"],
        )
        assert_matches_type(SyncCursorPage[Evaluation], evaluation, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: SGPClient) -> None:
        response = client.evaluations.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluation = response.parse()
        assert_matches_type(SyncCursorPage[Evaluation], evaluation, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: SGPClient) -> None:
        with client.evaluations.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluation = response.parse()
            assert_matches_type(SyncCursorPage[Evaluation], evaluation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_delete(self, client: SGPClient) -> None:
        evaluation = client.evaluations.delete(
            "evaluation_id",
        )
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: SGPClient) -> None:
        response = client.evaluations.with_raw_response.delete(
            "evaluation_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluation = response.parse()
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: SGPClient) -> None:
        with client.evaluations.with_streaming_response.delete(
            "evaluation_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluation = response.parse()
            assert_matches_type(Evaluation, evaluation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: SGPClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `evaluation_id` but received ''"):
            client.evaluations.with_raw_response.delete(
                "",
            )


class TestAsyncEvaluations:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create_overload_1(self, async_client: AsyncSGPClient) -> None:
        evaluation = await async_client.evaluations.create(
            data=[{"foo": "bar"}],
            name="name",
        )
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    async def test_method_create_with_all_params_overload_1(self, async_client: AsyncSGPClient) -> None:
        evaluation = await async_client.evaluations.create(
            data=[{"foo": "bar"}],
            name="name",
            description="description",
            files=[{"foo": "string"}],
            metadata={"foo": "bar"},
            tags=["string"],
            tasks=[
                {
                    "configuration": {
                        "messages": [{"foo": "bar"}],
                        "model": "model",
                        "audio": {"foo": "bar"},
                        "frequency_penalty": 0,
                        "function_call": {"foo": "bar"},
                        "functions": [{"foo": "bar"}],
                        "logit_bias": {"foo": 0},
                        "logprobs": True,
                        "max_completion_tokens": 0,
                        "max_tokens": 0,
                        "metadata": {"foo": "string"},
                        "modalities": ["string"],
                        "n": 0,
                        "parallel_tool_calls": True,
                        "prediction": {"foo": "bar"},
                        "presence_penalty": 0,
                        "reasoning_effort": "reasoning_effort",
                        "response_format": {"foo": "bar"},
                        "seed": 0,
                        "stop": "stop",
                        "store": True,
                        "temperature": 0,
                        "tool_choice": "tool_choice",
                        "tools": [{"foo": "bar"}],
                        "top_k": 0,
                        "top_logprobs": 0,
                        "top_p": 0,
                    },
                    "alias": "alias",
                    "task_type": "chat_completion",
                }
            ],
        )
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    async def test_raw_response_create_overload_1(self, async_client: AsyncSGPClient) -> None:
        response = await async_client.evaluations.with_raw_response.create(
            data=[{"foo": "bar"}],
            name="name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluation = await response.parse()
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    async def test_streaming_response_create_overload_1(self, async_client: AsyncSGPClient) -> None:
        async with async_client.evaluations.with_streaming_response.create(
            data=[{"foo": "bar"}],
            name="name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluation = await response.parse()
            assert_matches_type(Evaluation, evaluation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_create_overload_2(self, async_client: AsyncSGPClient) -> None:
        evaluation = await async_client.evaluations.create(
            dataset_id="dataset_id",
            name="name",
        )
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    async def test_method_create_with_all_params_overload_2(self, async_client: AsyncSGPClient) -> None:
        evaluation = await async_client.evaluations.create(
            dataset_id="dataset_id",
            name="name",
            data=[{"dataset_item_id": "dataset_item_id"}],
            description="description",
            metadata={"foo": "bar"},
            tags=["string"],
            tasks=[
                {
                    "configuration": {
                        "messages": [{"foo": "bar"}],
                        "model": "model",
                        "audio": {"foo": "bar"},
                        "frequency_penalty": 0,
                        "function_call": {"foo": "bar"},
                        "functions": [{"foo": "bar"}],
                        "logit_bias": {"foo": 0},
                        "logprobs": True,
                        "max_completion_tokens": 0,
                        "max_tokens": 0,
                        "metadata": {"foo": "string"},
                        "modalities": ["string"],
                        "n": 0,
                        "parallel_tool_calls": True,
                        "prediction": {"foo": "bar"},
                        "presence_penalty": 0,
                        "reasoning_effort": "reasoning_effort",
                        "response_format": {"foo": "bar"},
                        "seed": 0,
                        "stop": "stop",
                        "store": True,
                        "temperature": 0,
                        "tool_choice": "tool_choice",
                        "tools": [{"foo": "bar"}],
                        "top_k": 0,
                        "top_logprobs": 0,
                        "top_p": 0,
                    },
                    "alias": "alias",
                    "task_type": "chat_completion",
                }
            ],
        )
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    async def test_raw_response_create_overload_2(self, async_client: AsyncSGPClient) -> None:
        response = await async_client.evaluations.with_raw_response.create(
            dataset_id="dataset_id",
            name="name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluation = await response.parse()
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    async def test_streaming_response_create_overload_2(self, async_client: AsyncSGPClient) -> None:
        async with async_client.evaluations.with_streaming_response.create(
            dataset_id="dataset_id",
            name="name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluation = await response.parse()
            assert_matches_type(Evaluation, evaluation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_create_overload_3(self, async_client: AsyncSGPClient) -> None:
        evaluation = await async_client.evaluations.create(
            data=[{"foo": "bar"}],
            dataset={"name": "name"},
            name="name",
        )
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    async def test_method_create_with_all_params_overload_3(self, async_client: AsyncSGPClient) -> None:
        evaluation = await async_client.evaluations.create(
            data=[{"foo": "bar"}],
            dataset={
                "name": "name",
                "description": "description",
                "keys": ["string"],
                "tags": ["string"],
            },
            name="name",
            description="description",
            files=[{"foo": "string"}],
            metadata={"foo": "bar"},
            tags=["string"],
            tasks=[
                {
                    "configuration": {
                        "messages": [{"foo": "bar"}],
                        "model": "model",
                        "audio": {"foo": "bar"},
                        "frequency_penalty": 0,
                        "function_call": {"foo": "bar"},
                        "functions": [{"foo": "bar"}],
                        "logit_bias": {"foo": 0},
                        "logprobs": True,
                        "max_completion_tokens": 0,
                        "max_tokens": 0,
                        "metadata": {"foo": "string"},
                        "modalities": ["string"],
                        "n": 0,
                        "parallel_tool_calls": True,
                        "prediction": {"foo": "bar"},
                        "presence_penalty": 0,
                        "reasoning_effort": "reasoning_effort",
                        "response_format": {"foo": "bar"},
                        "seed": 0,
                        "stop": "stop",
                        "store": True,
                        "temperature": 0,
                        "tool_choice": "tool_choice",
                        "tools": [{"foo": "bar"}],
                        "top_k": 0,
                        "top_logprobs": 0,
                        "top_p": 0,
                    },
                    "alias": "alias",
                    "task_type": "chat_completion",
                }
            ],
        )
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    async def test_raw_response_create_overload_3(self, async_client: AsyncSGPClient) -> None:
        response = await async_client.evaluations.with_raw_response.create(
            data=[{"foo": "bar"}],
            dataset={"name": "name"},
            name="name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluation = await response.parse()
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    async def test_streaming_response_create_overload_3(self, async_client: AsyncSGPClient) -> None:
        async with async_client.evaluations.with_streaming_response.create(
            data=[{"foo": "bar"}],
            dataset={"name": "name"},
            name="name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluation = await response.parse()
            assert_matches_type(Evaluation, evaluation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncSGPClient) -> None:
        evaluation = await async_client.evaluations.retrieve(
            evaluation_id="evaluation_id",
        )
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    async def test_method_retrieve_with_all_params(self, async_client: AsyncSGPClient) -> None:
        evaluation = await async_client.evaluations.retrieve(
            evaluation_id="evaluation_id",
            include_archived=True,
            views=["tasks"],
        )
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncSGPClient) -> None:
        response = await async_client.evaluations.with_raw_response.retrieve(
            evaluation_id="evaluation_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluation = await response.parse()
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncSGPClient) -> None:
        async with async_client.evaluations.with_streaming_response.retrieve(
            evaluation_id="evaluation_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluation = await response.parse()
            assert_matches_type(Evaluation, evaluation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncSGPClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `evaluation_id` but received ''"):
            await async_client.evaluations.with_raw_response.retrieve(
                evaluation_id="",
            )

    @parametrize
    async def test_method_update_overload_1(self, async_client: AsyncSGPClient) -> None:
        evaluation = await async_client.evaluations.update(
            evaluation_id="evaluation_id",
        )
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    async def test_method_update_with_all_params_overload_1(self, async_client: AsyncSGPClient) -> None:
        evaluation = await async_client.evaluations.update(
            evaluation_id="evaluation_id",
            description="description",
            name="name",
            tags=["string"],
        )
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    async def test_raw_response_update_overload_1(self, async_client: AsyncSGPClient) -> None:
        response = await async_client.evaluations.with_raw_response.update(
            evaluation_id="evaluation_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluation = await response.parse()
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    async def test_streaming_response_update_overload_1(self, async_client: AsyncSGPClient) -> None:
        async with async_client.evaluations.with_streaming_response.update(
            evaluation_id="evaluation_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluation = await response.parse()
            assert_matches_type(Evaluation, evaluation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update_overload_1(self, async_client: AsyncSGPClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `evaluation_id` but received ''"):
            await async_client.evaluations.with_raw_response.update(
                evaluation_id="",
            )

    @parametrize
    async def test_method_update_overload_2(self, async_client: AsyncSGPClient) -> None:
        evaluation = await async_client.evaluations.update(
            evaluation_id="evaluation_id",
            restore=True,
        )
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    async def test_raw_response_update_overload_2(self, async_client: AsyncSGPClient) -> None:
        response = await async_client.evaluations.with_raw_response.update(
            evaluation_id="evaluation_id",
            restore=True,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluation = await response.parse()
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    async def test_streaming_response_update_overload_2(self, async_client: AsyncSGPClient) -> None:
        async with async_client.evaluations.with_streaming_response.update(
            evaluation_id="evaluation_id",
            restore=True,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluation = await response.parse()
            assert_matches_type(Evaluation, evaluation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update_overload_2(self, async_client: AsyncSGPClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `evaluation_id` but received ''"):
            await async_client.evaluations.with_raw_response.update(
                evaluation_id="",
                restore=True,
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncSGPClient) -> None:
        evaluation = await async_client.evaluations.list()
        assert_matches_type(AsyncCursorPage[Evaluation], evaluation, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncSGPClient) -> None:
        evaluation = await async_client.evaluations.list(
            ending_before="ending_before",
            include_archived=True,
            limit=1,
            name="name",
            sort_by="sort_by",
            sort_order="asc",
            starting_after="starting_after",
            tags=["string"],
            views=["tasks"],
        )
        assert_matches_type(AsyncCursorPage[Evaluation], evaluation, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncSGPClient) -> None:
        response = await async_client.evaluations.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluation = await response.parse()
        assert_matches_type(AsyncCursorPage[Evaluation], evaluation, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncSGPClient) -> None:
        async with async_client.evaluations.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluation = await response.parse()
            assert_matches_type(AsyncCursorPage[Evaluation], evaluation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_delete(self, async_client: AsyncSGPClient) -> None:
        evaluation = await async_client.evaluations.delete(
            "evaluation_id",
        )
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncSGPClient) -> None:
        response = await async_client.evaluations.with_raw_response.delete(
            "evaluation_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluation = await response.parse()
        assert_matches_type(Evaluation, evaluation, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncSGPClient) -> None:
        async with async_client.evaluations.with_streaming_response.delete(
            "evaluation_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluation = await response.parse()
            assert_matches_type(Evaluation, evaluation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncSGPClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `evaluation_id` but received ''"):
            await async_client.evaluations.with_raw_response.delete(
                "",
            )
