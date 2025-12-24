from unittest.mock import patch

import httpx
import pytest

from scale_gp_beta import SGPClient
from scale_gp_beta.lib.tracing.trace_queue_manager import TraceQueueManager


@pytest.fixture
def mock_transport() -> httpx.MockTransport:
    def handler(_request: httpx.Request):
        return httpx.Response(200, json={"ok": True})

    return httpx.MockTransport(handler)


@pytest.fixture
def real_sgp_client(mock_transport: httpx.MockTransport) -> SGPClient:
    """
    Creates a REAL SGPClient instance but with a mocked transport layer
    to prevent actual network calls.
    """
    return SGPClient(
        api_key="dummy_key",
        account_id="dummy_account_id",
        http_client=httpx.Client(transport=mock_transport),
    )


class TestRegisterClient:
    # Following 3 tests are to ensure that our monkey patch on SGPClient _prepare_request remains valid.
    # They should fail if Stainless changes some internals.
    def test_prepare_request_is_patched(self, real_sgp_client: SGPClient):
        """
        Verifies that our custom wrapper successfully replaces the '_prepare_request' method on the client instance.
        """
        original_method = real_sgp_client._prepare_request
        TraceQueueManager(worker_enabled=False, client=real_sgp_client)
        patched_method = real_sgp_client._prepare_request

        assert patched_method is not original_method
        assert patched_method.__name__ == "custom_prepare_request"

    def test_patch_calls_original_method(self, real_sgp_client: SGPClient):
        """
        Verifies that our custom wrapper correctly calls the original
        `_prepare_request` method, ensuring the chain of execution is not broken. Note that the original is default empty.
        But the user may have added something themselves.
        """
        manager = TraceQueueManager(worker_enabled=False)

        with patch.object(real_sgp_client, '_prepare_request', wraps=real_sgp_client._prepare_request) as mock_original:
            manager.register_client(real_sgp_client)

            real_sgp_client.spans.search()

            mock_original.assert_called_once()
            call_args = mock_original.call_args[0]
            assert len(call_args) == 1
            assert isinstance(call_args[0], httpx.Request)

    def test_patching_contract_against_real_client(self, real_sgp_client: SGPClient):
        """
        It ensures that our patching logic is compatible with the real client's
        method signature and request lifecycle. If Stainless changes the internal
        API, this test should fail.
        """
        TraceQueueManager(worker_enabled=False, client=real_sgp_client)

        try:
            # If `_prepare_request`'s signature changes, this line will raise an error.
            response = real_sgp_client.spans.search()
            assert response is not None
        except TypeError as e:
            pytest.fail(
                f"Contract broken! The signature of `_prepare_request` may have changed. Error: {e}"
            )
        except Exception as e:
            pytest.fail(f"An unexpected error occurred during the patched request: {e}")
