"""
Test Phase 2: Command Execution Refactor & Queue Integration

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from embed_client.response_normalizer import ResponseNormalizer
from embed_client.async_client import (
    EmbeddingServiceAsyncClient,
    EmbeddingServiceAPIError,
)


class TestResponseNormalizer:
    """Test ResponseNormalizer."""

    def test_normalize_immediate_response(self):
        """Test normalization of immediate response."""
        adapter_response = {
            "mode": "immediate",
            "command": "embed",
            "result": {"embeddings": [[0.1, 0.2, 0.3]]},
            "queued": False,
        }

        normalized = ResponseNormalizer.normalize_command_response(adapter_response)

        assert "result" in normalized
        assert normalized["result"]["success"] is True
        assert "data" in normalized["result"]
        assert normalized["result"]["data"] == {"embeddings": [[0.1, 0.2, 0.3]]}

    def test_normalize_immediate_response_already_legacy(self):
        """Test normalization when response is already in legacy format."""
        adapter_response = {
            "mode": "immediate",
            "command": "embed",
            "result": {"success": True, "data": {"embeddings": [[0.1, 0.2, 0.3]]}},
            "queued": False,
        }

        normalized = ResponseNormalizer.normalize_command_response(adapter_response)

        assert normalized["result"]["success"] is True
        assert "embeddings" in normalized["result"]["data"]

    def test_normalize_queued_response(self):
        """Test normalization of queued response."""
        adapter_response = {
            "mode": "queued",
            "command": "embed",
            "job_id": "job-123",
            "status": "completed",
            "result": {"embeddings": [[0.1, 0.2, 0.3]]},
            "queued": True,
        }

        normalized = ResponseNormalizer.normalize_command_response(adapter_response)

        assert "result" in normalized
        assert normalized["result"]["success"] is True
        assert normalized["result"]["data"]["job_id"] == "job-123"
        assert normalized["result"]["data"]["status"] == "completed"

    def test_normalize_queue_status(self):
        """Test normalization of queue status."""
        queue_status = {
            "status": "running",
            "result": {"progress": 50},
            "data": {"job_id": "job-123"},
        }

        normalized = ResponseNormalizer.normalize_queue_status(queue_status)

        assert normalized["status"] == "running"
        assert normalized["result"] == {"progress": 50}
        assert normalized["exists"] is True

    def test_extract_error_from_adapter(self):
        """Test error extraction from adapter exception."""
        error = RuntimeError("Test error message")

        error_dict = ResponseNormalizer.extract_error_from_adapter(error)

        assert "error" in error_dict
        assert error_dict["error"]["code"] == -32000
        assert "Test error message" in error_dict["error"]["message"]


class TestQueueOperations:
    """Test queue operations with adapter transport."""

    @pytest.mark.asyncio
    async def test_job_status_with_adapter(self):
        """Test job_status method with adapter transport."""
        client = EmbeddingServiceAsyncClient(
            config_dict={
                "server": {"host": "http://localhost", "port": 8001},
                "client": {"timeout": 30.0},
            }
        )

        # Mock adapter transport
        mock_status = {
            "status": "completed",
            "result": {"embeddings": [[0.1, 0.2]]},
            "data": {"job_id": "test-job"},
        }

        with patch.object(client._adapter_transport, "queue_get_job_status", new_callable=AsyncMock) as mock_get_status:
            mock_get_status.return_value = mock_status

            async with client:
                status = await client.job_status("test-job")

                assert status["status"] == "completed"
                assert status["exists"] is True
                mock_get_status.assert_called_once_with("test-job")

    @pytest.mark.asyncio
    async def test_cancel_command_with_adapter(self):
        """Test cancel_command method with adapter transport."""
        client = EmbeddingServiceAsyncClient(
            config_dict={
                "server": {"host": "http://localhost", "port": 8001},
                "client": {"timeout": 30.0},
            }
        )

        with patch.object(client._adapter_transport, "queue_stop_job", new_callable=AsyncMock) as mock_stop:
            with patch.object(client._adapter_transport, "queue_delete_job", new_callable=AsyncMock) as mock_delete:
                mock_delete.return_value = {"success": True}

                async with client:
                    result = await client.cancel_command("test-job")

                    mock_stop.assert_called_once_with("test-job")
                    mock_delete.assert_called_once_with("test-job")
                    assert result["success"] is True

    @pytest.mark.asyncio
    async def test_list_queued_commands_with_adapter(self):
        """Test list_queued_commands method with adapter transport."""
        client = EmbeddingServiceAsyncClient(
            config_dict={
                "server": {"host": "http://localhost", "port": 8001},
                "client": {"timeout": 30.0},
            }
        )

        mock_result = {
            "data": {
                "jobs": [
                    {"job_id": "job-1", "status": "pending"},
                    {"job_id": "job-2", "status": "running"},
                ],
                "total_count": 2,
            }
        }

        with patch.object(client._adapter_transport, "queue_list_jobs", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = mock_result

            async with client:
                result = await client.list_queued_commands(status="pending")

                mock_list.assert_called_once_with(status="pending", job_type="command_execution")
                assert len(result["data"]["jobs"]) == 2

    @pytest.mark.asyncio
    async def test_list_queued_commands_with_limit(self):
        """Test list_queued_commands with limit."""
        client = EmbeddingServiceAsyncClient(
            config_dict={
                "server": {"host": "http://localhost", "port": 8001},
                "client": {"timeout": 30.0},
            }
        )

        mock_result = {
            "data": {
                "jobs": [{"job_id": f"job-{i}", "status": "pending"} for i in range(10)],
                "total_count": 10,
            }
        }

        with patch.object(client._adapter_transport, "queue_list_jobs", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = mock_result

            async with client:
                result = await client.list_queued_commands(limit=5)

                assert len(result["data"]["jobs"]) == 5
                assert result["data"]["total_count"] == 5

    @pytest.mark.asyncio
    async def test_get_job_logs_with_adapter(self):
        """Test get_job_logs method with adapter transport."""
        client = EmbeddingServiceAsyncClient(
            config_dict={
                "server": {"host": "http://localhost", "port": 8001},
                "client": {"timeout": 30.0},
            }
        )

        mock_logs = {
            "job_id": "test-job",
            "stdout": ["Line 1", "Line 2"],
            "stderr": [],
            "stdout_lines": 2,
            "stderr_lines": 0,
        }

        with patch.object(client._adapter_transport, "queue_get_job_logs", new_callable=AsyncMock) as mock_logs_method:
            mock_logs_method.return_value = mock_logs

            async with client:
                result = await client.get_job_logs("test-job")

                mock_logs_method.assert_called_once_with("test-job")
                assert result["job_id"] == "test-job"
                assert len(result["stdout"]) == 2


class TestCommandExecution:
    """Test command execution with normalization."""

    @pytest.mark.asyncio
    async def test_cmd_with_adapter_immediate_response(self):
        """Test cmd method with adapter immediate response."""
        client = EmbeddingServiceAsyncClient(
            config_dict={
                "server": {"host": "http://localhost", "port": 8001},
                "client": {"timeout": 30.0},
            }
        )

        mock_response = {
            "mode": "immediate",
            "command": "embed",
            "result": {"success": True, "data": {"embeddings": [[0.1, 0.2, 0.3]]}},
            "queued": False,
        }

        with patch.object(client._adapter_transport, "execute_command_unified", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = mock_response

            async with client:
                result = await client.cmd("embed", {"texts": ["test"]})

                assert "result" in result
                assert result["result"]["success"] is True
                mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_cmd_with_adapter_queued_response(self):
        """Test cmd method with adapter queued response."""
        client = EmbeddingServiceAsyncClient(
            config_dict={
                "server": {"host": "http://localhost", "port": 8001},
                "client": {"timeout": 30.0},
            }
        )

        mock_response = {
            "mode": "queued",
            "command": "embed",
            "job_id": "job-123",
            "status": "completed",
            "result": {"success": True, "data": {"embeddings": [[0.1, 0.2, 0.3]]}},
            "queued": True,
        }

        with patch.object(client._adapter_transport, "execute_command_unified", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = mock_response

            async with client:
                result = await client.cmd("embed", {"texts": ["test"]})

                assert "result" in result
                assert result["result"]["success"] is True
                # For completed jobs, result should contain the data directly
                assert "data" in result["result"]
                assert "embeddings" in result["result"]["data"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
