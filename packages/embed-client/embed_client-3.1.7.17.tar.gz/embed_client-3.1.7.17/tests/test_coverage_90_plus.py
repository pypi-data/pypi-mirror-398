#!/usr/bin/env python3
"""
Comprehensive tests to achieve 90%+ code coverage for all modules.

Tests all code paths, edge cases, and error handling.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import Dict, Any, List

from embed_client.async_client import EmbeddingServiceAsyncClient
from embed_client.async_client_api_mixin import AsyncClientAPIMixin
from embed_client.async_client_queue_mixin import AsyncClientQueueMixin
from embed_client.adapter_transport import AdapterTransport
from embed_client.exceptions import (
    EmbeddingServiceError,
    EmbeddingServiceAPIError,
    EmbeddingServiceTimeoutError,
)


BASE_CONFIG: Dict[str, Any] = {
    "server": {"host": "localhost", "port": 8001},
    "auth": {"method": "none"},
    "ssl": {"enabled": False},
}


@pytest_asyncio.fixture
async def base_client():
    """Base client fixture."""
    async with EmbeddingServiceAsyncClient(config_dict=BASE_CONFIG) as client:
        yield client


class TestAsyncClientAPIMixinCoverage:
    """Tests for AsyncClientAPIMixin to achieve 90%+ coverage."""

    @pytest.mark.asyncio
    async def test_health_error_handling(self, base_client):
        """Test health() error handling."""
        with patch.object(
            base_client._adapter_transport,
            "health",
            new_callable=AsyncMock,
            side_effect=Exception("Connection error"),
        ):
            with pytest.raises(EmbeddingServiceError, match="Health check failed"):
                await base_client.health()

    @pytest.mark.asyncio
    async def test_get_openapi_schema_error_handling(self, base_client):
        """Test get_openapi_schema() error handling."""
        with patch.object(
            base_client._adapter_transport,
            "get_openapi_schema",
            new_callable=AsyncMock,
            side_effect=Exception("Schema error"),
        ):
            with pytest.raises(EmbeddingServiceError, match="Failed to get OpenAPI schema"):
                await base_client.get_openapi_schema()

    @pytest.mark.asyncio
    async def test_get_commands_error_handling(self, base_client):
        """Test get_commands() error handling."""
        with patch.object(
            base_client._adapter_transport,
            "get_commands_list",
            new_callable=AsyncMock,
            side_effect=Exception("Commands error"),
        ):
            with pytest.raises(EmbeddingServiceError, match="Failed to get commands"):
                await base_client.get_commands()

    @pytest.mark.asyncio
    async def test_validate_texts_empty_list(self, base_client):
        """Test _validate_texts() with empty list."""
        with pytest.raises(EmbeddingServiceAPIError, match="Empty texts list"):
            base_client._validate_texts([])

    @pytest.mark.asyncio
    async def test_validate_texts_non_string(self, base_client):
        """Test _validate_texts() with non-string items."""
        with pytest.raises(EmbeddingServiceAPIError, match="Invalid input texts"):
            base_client._validate_texts(["valid", 123, "also valid"])

    @pytest.mark.asyncio
    async def test_validate_texts_empty_string(self, base_client):
        """Test _validate_texts() with empty strings."""
        with pytest.raises(EmbeddingServiceAPIError, match="Invalid input texts"):
            base_client._validate_texts(["valid", "", "   "])

    @pytest.mark.asyncio
    async def test_validate_texts_too_short(self, base_client):
        """Test _validate_texts() with too short strings."""
        with pytest.raises(EmbeddingServiceAPIError, match="Invalid input texts"):
            base_client._validate_texts(["valid", "a", "ab"])

    @pytest.mark.asyncio
    async def test_cmd_empty_command(self, base_client):
        """Test cmd() with empty command."""
        with pytest.raises(EmbeddingServiceAPIError, match="Command is required"):
            await base_client.cmd("")

    @pytest.mark.asyncio
    async def test_cmd_queued_completed_with_nested_result(self, base_client):
        """Test cmd() with queued completed result containing nested result."""
        with patch.object(
            base_client._adapter_transport,
            "execute_command_unified",
            new_callable=AsyncMock,
        ) as mock_exec:
            mock_exec.return_value = {
                "mode": "queued",
                "status": "completed",
                "result": {"result": {"success": True, "data": {"results": [[0.1]]}}},
            }

            result = await base_client.cmd("embed", {"texts": ["test"]})
            assert "result" in result

    @pytest.mark.asyncio
    async def test_cmd_queued_completed_with_dict_result(self, base_client):
        """Test cmd() with queued completed result containing dict."""
        with patch.object(
            base_client._adapter_transport,
            "execute_command_unified",
            new_callable=AsyncMock,
        ) as mock_exec:
            mock_exec.return_value = {
                "mode": "queued",
                "status": "completed",
                "result": {"success": True, "data": {"results": [[0.1]]}},
            }

            result = await base_client.cmd("embed", {"texts": ["test"]})
            assert "result" in result

    @pytest.mark.asyncio
    async def test_cmd_queued_completed_with_empty_result(self, base_client):
        """Test cmd() with queued completed result but empty result."""
        with patch.object(
            base_client._adapter_transport,
            "execute_command_unified",
            new_callable=AsyncMock,
        ) as mock_exec:
            mock_exec.return_value = {
                "mode": "queued",
                "status": "completed",
                "result": {},
            }

            result = await base_client.cmd("embed", {"texts": ["test"]})
            assert "result" in result

    @pytest.mark.asyncio
    async def test_cmd_queued_not_completed_with_job_id(self, base_client):
        """Test cmd() with queued not completed result and job_id."""
        with patch.object(
            base_client._adapter_transport,
            "execute_command_unified",
            new_callable=AsyncMock,
        ) as mock_exec:
            mock_exec.return_value = {
                "mode": "queued",
                "job_id": "test-job-123",
                "status": "running",
            }

            with patch.object(
                base_client,
                "wait_for_job",
                new_callable=AsyncMock,
            ) as mock_wait:
                mock_wait.return_value = {
                    "result": {"success": True, "data": {"results": [[0.1]]}},
                }

                result = await base_client.cmd("embed", {"texts": ["test"]})
                assert "result" in result

    @pytest.mark.asyncio
    async def test_cmd_queued_not_completed_with_data_in_result(self, base_client):
        """Test cmd() with queued result containing data."""
        with patch.object(
            base_client._adapter_transport,
            "execute_command_unified",
            new_callable=AsyncMock,
        ) as mock_exec:
            mock_exec.return_value = {
                "mode": "queued",
                "job_id": "test-job-123",
            }

            with patch.object(
                base_client,
                "wait_for_job",
                new_callable=AsyncMock,
            ) as mock_wait:
                mock_wait.return_value = {
                    "data": {"results": [[0.1]]},
                }

                result = await base_client.cmd("embed", {"texts": ["test"]})
                assert "result" in result

    @pytest.mark.asyncio
    async def test_cmd_error_in_normalized(self, base_client):
        """Test cmd() with error in normalized response."""
        with patch.object(
            base_client._adapter_transport,
            "execute_command_unified",
            new_callable=AsyncMock,
        ) as mock_exec:
            # Return non-dict result to trigger normalization path
            mock_exec.return_value = "error string"

            with patch(
                "embed_client.async_client_api_mixin.ResponseNormalizer.normalize_command_response"
            ) as mock_norm:
                mock_norm.return_value = {"error": {"code": -1, "message": "Test error"}}
                with pytest.raises(EmbeddingServiceAPIError):
                    await base_client.cmd("embed", {"texts": ["test"]})

    @pytest.mark.asyncio
    async def test_cmd_success_false_in_result(self, base_client):
        """Test cmd() with success=False in result."""
        with patch.object(
            base_client._adapter_transport,
            "execute_command_unified",
            new_callable=AsyncMock,
        ) as mock_exec:
            # Return non-dict to trigger normalization
            mock_exec.return_value = "some result"

            with patch(
                "embed_client.async_client_api_mixin.ResponseNormalizer.normalize_command_response"
            ) as mock_norm:
                mock_norm.return_value = {
                    "result": {"success": False, "error": {"message": "Test error"}},
                }
                with pytest.raises(EmbeddingServiceAPIError):
                    await base_client.cmd("embed", {"texts": ["test"]})

    @pytest.mark.asyncio
    async def test_cmd_error_in_result_data(self, base_client):
        """Test cmd() with error in result data."""
        with patch.object(
            base_client._adapter_transport,
            "execute_command_unified",
            new_callable=AsyncMock,
        ) as mock_exec:
            # Return non-dict to trigger normalization
            mock_exec.return_value = "some result"

            with patch(
                "embed_client.async_client_api_mixin.ResponseNormalizer.normalize_command_response"
            ) as mock_norm:
                mock_norm.return_value = {
                    "result": {"error": {"message": "Test error"}},
                }
                with pytest.raises(EmbeddingServiceAPIError):
                    await base_client.cmd("embed", {"texts": ["test"]})

    @pytest.mark.asyncio
    async def test_cmd_generic_exception(self, base_client):
        """Test cmd() with generic exception."""
        with patch.object(
            base_client._adapter_transport,
            "execute_command_unified",
            new_callable=AsyncMock,
            side_effect=ValueError("Test error"),
        ):
            with pytest.raises(EmbeddingServiceAPIError):
                await base_client.cmd("embed", {"texts": ["test"]})

    @pytest.mark.asyncio
    async def test_embed_with_timeout_and_immediate_result(self, base_client):
        """Test embed() with timeout but immediate result."""
        with patch.object(
            base_client._adapter_transport,
            "execute_command_unified",
            new_callable=AsyncMock,
        ) as mock_exec:
            mock_exec.return_value = {
                "mode": "immediate",
                "result": {
                    "success": True,
                    "data": {
                        "results": [
                            {"body": "test", "embedding": [0.1, 0.2, 0.3]}
                        ]
                    },
                },
            }

            result = await base_client.embed(["test"], timeout=5.0)
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_embed_with_timeout_and_queued_no_job_id(self, base_client):
        """Test embed() with timeout but queued without job_id."""
        with patch.object(
            base_client._adapter_transport,
            "execute_command_unified",
            new_callable=AsyncMock,
        ) as mock_exec:
            mock_exec.return_value = {
                "mode": "queued",
                "result": {
                    "success": True,
                    "data": {
                        "results": [
                            {"body": "test", "embedding": [0.1, 0.2, 0.3]}
                        ]
                    },
                },
            }

            result = await base_client.embed(["test"], timeout=5.0)
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_embed_extract_embeddings_fallback(self, base_client):
        """Test embed() with extract_embeddings fallback."""
        with patch.object(
            base_client._adapter_transport,
            "execute_command_unified",
            new_callable=AsyncMock,
        ) as mock_exec:
            mock_exec.return_value = {
                "mode": "queued",
                "job_id": "test-job-123",
            }

            with patch.object(
                base_client,
                "wait_for_job",
                new_callable=AsyncMock,
            ) as mock_wait:
                mock_wait.return_value = {
                    "data": [0.1, 0.2, 0.3],  # List format
                }

                with patch(
                    "embed_client.async_client_api_mixin.extract_embedding_data",
                    side_effect=ValueError("Cannot extract"),
                ):
                    result = await base_client.embed(["test"], timeout=5.0)
                    assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_embed_with_cmd_fallback(self, base_client):
        """Test embed() using cmd() fallback when timeout is None."""
        with patch.object(
            base_client,
            "cmd",
            new_callable=AsyncMock,
        ) as mock_cmd:
            mock_cmd.return_value = {
                "result": {
                    "success": True,
                    "data": {
                        "results": [
                            {"body": "test", "embedding": [0.1, 0.2, 0.3]}
                        ]
                    },
                },
            }

            result = await base_client.embed(["test"], timeout=None)
            assert isinstance(result, dict)
            mock_cmd.assert_called_once()

    @pytest.mark.asyncio
    async def test_embed_with_result_data_list(self, base_client):
        """Test embed() with result.data as list."""
        with patch.object(
            base_client,
            "cmd",
            new_callable=AsyncMock,
        ) as mock_cmd:
            mock_cmd.return_value = {
                "result": {
                    "success": True,
                    "data": [
                        {"body": "test", "embedding": [0.1, 0.2, 0.3]}
                    ],
                },
            }

            result = await base_client.embed(["test"], timeout=None)
            assert isinstance(result, dict)
            assert "results" in result


class TestAsyncClientQueueMixinCoverage:
    """Tests for AsyncClientQueueMixin to achieve 90%+ coverage."""

    @pytest.mark.asyncio
    async def test_wait_for_job_immediate_completed(self, base_client):
        """Test wait_for_job() with immediate completed status."""
        with patch.object(
            base_client,
            "job_status",
            new_callable=AsyncMock,
        ) as mock_status:
            mock_status.return_value = {
                "status": "completed",
                "result": {"data": {"results": [[0.1]]}},
            }

            result = await base_client.wait_for_job("test-job", timeout=None)
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_wait_for_job_immediate_success(self, base_client):
        """Test wait_for_job() with immediate success status."""
        with patch.object(
            base_client,
            "job_status",
            new_callable=AsyncMock,
        ) as mock_status:
            mock_status.return_value = {
                "status": "success",
                "result": {"data": {"results": [[0.1]]}},
            }

            result = await base_client.wait_for_job("test-job", timeout=None)
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_wait_for_job_immediate_done(self, base_client):
        """Test wait_for_job() with immediate done status."""
        with patch.object(
            base_client,
            "job_status",
            new_callable=AsyncMock,
        ) as mock_status:
            mock_status.return_value = {
                "status": "done",
                "result": {"data": {"results": [[0.1]]}},
            }

            result = await base_client.wait_for_job("test-job", timeout=None)
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_wait_for_job_result_with_data(self, base_client):
        """Test wait_for_job() with result containing data."""
        with patch.object(
            base_client,
            "job_status",
            new_callable=AsyncMock,
        ) as mock_status:
            mock_status.return_value = {
                "status": "completed",
                "result": {"data": {"results": [[0.1]]}},
            }

            result = await base_client.wait_for_job("test-job", timeout=5.0)
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_wait_for_job_result_without_data(self, base_client):
        """Test wait_for_job() with result without data."""
        with patch.object(
            base_client,
            "job_status",
            new_callable=AsyncMock,
        ) as mock_status:
            mock_status.return_value = {
                "status": "completed",
                "result": {"results": [[0.1]]},
            }

            result = await base_client.wait_for_job("test-job", timeout=5.0)
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_wait_for_job_failed_status(self, base_client):
        """Test wait_for_job() with failed status."""
        with patch.object(
            base_client,
            "job_status",
            new_callable=AsyncMock,
        ) as mock_status:
            mock_status.return_value = {
                "status": "failed",
                "error": {"message": "Job failed"},
            }

            with pytest.raises(EmbeddingServiceAPIError):
                await base_client.wait_for_job("test-job", timeout=5.0)

    @pytest.mark.asyncio
    async def test_wait_for_job_error_status(self, base_client):
        """Test wait_for_job() with error status."""
        with patch.object(
            base_client,
            "job_status",
            new_callable=AsyncMock,
        ) as mock_status:
            mock_status.return_value = {
                "status": "error",
                "message": "Job error",
            }

            with pytest.raises(EmbeddingServiceAPIError):
                await base_client.wait_for_job("test-job", timeout=5.0)

    @pytest.mark.asyncio
    async def test_wait_for_job_timeout(self, base_client):
        """Test wait_for_job() with timeout."""
        with patch.object(
            base_client,
            "job_status",
            new_callable=AsyncMock,
        ) as mock_status:
            mock_status.return_value = {"status": "running"}

            with pytest.raises(EmbeddingServiceTimeoutError):
                await base_client.wait_for_job("test-job", timeout=0.1, poll_interval=0.05)

    @pytest.mark.asyncio
    async def test_wait_for_job_generic_exception(self, base_client):
        """Test wait_for_job() with generic exception."""
        with patch.object(
            base_client,
            "job_status",
            new_callable=AsyncMock,
            side_effect=ValueError("Test error"),
        ):
            with pytest.raises(EmbeddingServiceError, match="Failed to wait for job"):
                await base_client.wait_for_job("test-job", timeout=5.0)

    @pytest.mark.asyncio
    async def test_job_status_error_handling(self, base_client):
        """Test job_status() error handling."""
        with patch.object(
            base_client._adapter_transport,
            "queue_get_job_status",
            new_callable=AsyncMock,
            side_effect=Exception("Status error"),
        ):
            with pytest.raises(EmbeddingServiceError, match="Failed to get job status"):
                await base_client.job_status("test-job")

    @pytest.mark.asyncio
    async def test_cancel_command_error_handling(self, base_client):
        """Test cancel_command() error handling."""
        with patch.object(
            base_client._adapter_transport,
            "queue_stop_job",
            new_callable=AsyncMock,
            side_effect=Exception("Cancel error"),
        ):
            with pytest.raises(EmbeddingServiceError, match="Failed to cancel command"):
                await base_client.cancel_command("test-job")

    @pytest.mark.asyncio
    async def test_list_queued_commands_error_handling(self, base_client):
        """Test list_queued_commands() error handling."""
        with patch.object(
            base_client._adapter_transport,
            "queue_list_jobs",
            new_callable=AsyncMock,
            side_effect=Exception("List error"),
        ):
            with pytest.raises(EmbeddingServiceError, match="Failed to list queued commands"):
                await base_client.list_queued_commands()

    @pytest.mark.asyncio
    async def test_submit_job_not_queued(self, base_client):
        """Test submit_job() when result is not queued."""
        with patch.object(
            base_client._adapter_transport,
            "execute_command_unified",
            new_callable=AsyncMock,
        ) as mock_exec:
            # submit_job returns immediate result if not queued (no job_id)
            mock_exec.return_value = {
                "mode": "immediate",
                "result": {"results": [[0.1]]},
            }

            # submit_job returns result even if not queued
            result = await base_client.submit_job("embed", {"texts": ["test"]})
            assert isinstance(result, dict)
            assert result.get("job_id") is None

    @pytest.mark.asyncio
    async def test_submit_job_exception(self, base_client):
        """Test submit_job() with exception."""
        with patch.object(
            base_client._adapter_transport,
            "execute_command_unified",
            new_callable=AsyncMock,
            side_effect=Exception("Submit error"),
        ):
            with pytest.raises(EmbeddingServiceError, match="Failed to submit job"):
                await base_client.submit_job("embed", {"texts": ["test"]})


class TestAdapterTransportCoverage:
    """Tests for AdapterTransport to achieve 90%+ coverage."""

    @pytest.mark.asyncio
    async def test_ensure_client_creates_new_client(self):
        """Test _ensure_client() creates new client."""
        transport = AdapterTransport(
            adapter_params={
                "protocol": "http",
                "host": "localhost",
                "port": 8001,
            }
        )

        client = await transport._ensure_client()
        assert client is not None
        assert transport._client is client

    @pytest.mark.asyncio
    async def test_ensure_client_returns_existing(self):
        """Test _ensure_client() returns existing client."""
        transport = AdapterTransport(
            adapter_params={
                "protocol": "http",
                "host": "localhost",
                "port": 8001,
            }
        )

        client1 = await transport._ensure_client()
        client2 = await transport._ensure_client()
        assert client1 is client2

    @pytest.mark.asyncio
    async def test_generate_token_from_config_jwt(self):
        """Test _generate_token_from_config() with JWT."""
        transport = AdapterTransport(
            adapter_params={
                "protocol": "http",
                "host": "localhost",
                "port": 8001,
                "token_header": "Authorization",
            }
        )
        transport._original_config = {"auth": {"method": "jwt"}}

        token = await transport._generate_token_from_config()
        assert token is None  # JWT handled by adapter

    @pytest.mark.asyncio
    async def test_generate_token_from_config_basic(self):
        """Test _generate_token_from_config() with Basic auth."""
        transport = AdapterTransport(
            adapter_params={
                "protocol": "http",
                "host": "localhost",
                "port": 8001,
                "token_header": "Authorization",
            }
        )
        transport._original_config = {"auth": {"method": "basic"}}

        token = await transport._generate_token_from_config()
        assert token is None  # Basic handled by adapter

    @pytest.mark.asyncio
    async def test_generate_token_from_config_none(self):
        """Test _generate_token_from_config() with no auth."""
        transport = AdapterTransport(
            adapter_params={
                "protocol": "http",
                "host": "localhost",
                "port": 8001,
            }
        )
        transport._original_config = {"auth": {"method": "none"}}

        token = await transport._generate_token_from_config()
        assert token is None

    @pytest.mark.asyncio
    async def test_close_with_client(self):
        """Test close() with existing client."""
        transport = AdapterTransport(
            adapter_params={
                "protocol": "http",
                "host": "localhost",
                "port": 8001,
            }
        )

        await transport._ensure_client()
        await transport.close()
        assert transport._client is None

    @pytest.mark.asyncio
    async def test_close_without_client(self):
        """Test close() without client."""
        transport = AdapterTransport(
            adapter_params={
                "protocol": "http",
                "host": "localhost",
                "port": 8001,
            }
        )

        await transport.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_execute_command_unified_with_status_hook(self):
        """Test execute_command_unified() with status_hook."""
        transport = AdapterTransport(
            adapter_params={
                "protocol": "http",
                "host": "localhost",
                "port": 8001,
            }
        )

        async def status_hook(status: Dict[str, Any]) -> None:
            pass

        with patch.object(
            transport,
            "_ensure_client",
            new_callable=AsyncMock,
        ) as mock_ensure:
            mock_client = AsyncMock()
            mock_client.execute_command_unified = AsyncMock(
                return_value={"mode": "immediate", "result": {"success": True}}
            )
            mock_ensure.return_value = mock_client

            result = await transport.execute_command_unified(
                "embed",
                {"texts": ["test"]},
                status_hook=status_hook,
            )
            assert isinstance(result, dict)

