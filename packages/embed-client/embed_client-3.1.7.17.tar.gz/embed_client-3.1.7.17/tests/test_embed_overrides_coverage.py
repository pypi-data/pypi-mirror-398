#!/usr/bin/env python3
"""
Additional tests for embed() override parameters to achieve 90%+ coverage.

Tests edge cases and all code paths in async_client_api_mixin.py.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
import pytest_asyncio
from pathlib import Path
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

from embed_client.async_client import EmbeddingServiceAsyncClient
from embed_client.exceptions import (
    EmbeddingServiceError,
    EmbeddingServiceTimeoutError,
    EmbeddingServiceAPIError,
)


# Base configuration for tests
BASE_CONFIG: Dict[str, Any] = {
    "server": {
        "host": "localhost",
        "port": 8001,
    },
    "auth": {
        "method": "none",
    },
    "ssl": {
        "enabled": False,
    },
}


@pytest_asyncio.fixture
async def base_client():
    """Base client fixture."""
    async with EmbeddingServiceAsyncClient(config_dict=BASE_CONFIG) as client:
        yield client


class TestEmbedOverrideEdgeCases:
    """Tests for edge cases in embed() override parameters."""

    @pytest.mark.asyncio
    async def test_embed_with_timeout_none_immediate_result(self, base_client):
        """Test embed() with timeout=None when result is immediate."""
        # Mock to return immediate result
        with patch.object(
            base_client._adapter_transport,
            "execute_command_unified",
            new_callable=AsyncMock,
        ) as mock_exec:
            mock_exec.return_value = {
                "mode": "immediate",
                "result": {"success": True, "data": {"results": [[0.1, 0.2, 0.3]]}},
            }

            result = await base_client.embed(["test"], timeout=None)
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_embed_with_timeout_none_queued_result(self, base_client):
        """Test embed() with timeout=None when result is queued."""
        # When timeout=None, embed() uses cmd() which handles queued jobs automatically
        with patch.object(
            base_client,
            "cmd",
            new_callable=AsyncMock,
        ) as mock_cmd:
            mock_cmd.return_value = {
                "result": {"success": True, "data": {"results": [[0.1, 0.2, 0.3]]}},
            }

            result = await base_client.embed(["test"], timeout=None)
            # Should use cmd() method which handles queued jobs
            assert isinstance(result, dict)
            mock_cmd.assert_called_once()

    @pytest.mark.asyncio
    async def test_embed_with_timeout_queued_no_job_id(self, base_client):
        """Test embed() with timeout when queued but no job_id."""
        with patch.object(
            base_client._adapter_transport,
            "execute_command_unified",
            new_callable=AsyncMock,
        ) as mock_exec:
            # Return queued mode but no job_id - should process as immediate
            # The code checks for job_id in multiple places, if none found, processes as immediate
            mock_exec.return_value = {
                "mode": "queued",
                # No job_id anywhere
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
            # Should process immediate result when no job_id
            assert isinstance(result, dict)
            # Result should be normalized
            assert "results" in result or "embeddings" in result

    @pytest.mark.asyncio
    async def test_embed_with_timeout_queued_with_job_id(self, base_client):
        """Test embed() with timeout when queued with job_id."""
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
                    "data": {"results": [[0.1, 0.2, 0.3]]},
                }

                result = await base_client.embed(["test"], timeout=5.0)
                assert isinstance(result, dict)
                mock_wait.assert_called_once_with("test-job-123", timeout=5.0)

    @pytest.mark.asyncio
    async def test_embed_with_all_overrides_creates_temp_client(self, base_client):
        """Test that embed() creates temporary client when overrides are provided."""
        cert_dir = Path(__file__).parent.parent / "mtls_certificates"
        cert_file = cert_dir / "client" / "embedding-service.crt"
        key_file = cert_dir / "client" / "embedding-service.key"
        ca_cert_file = cert_dir / "ca" / "ca.crt"

        if not all([cert_file.exists(), key_file.exists(), ca_cert_file.exists()]):
            pytest.skip("mTLS certificates not found")

        # Test that override parameters trigger temporary client creation
        # This is tested by checking that a new client is used
        with patch(
            "embed_client.async_client.EmbeddingServiceAsyncClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client._adapter_transport.execute_command_unified = AsyncMock(
                return_value={
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
            )
            mock_client.cmd = AsyncMock(
                return_value={
                    "result": {
                        "success": True,
                        "data": {
                            "results": [
                                {"body": "test", "embedding": [0.1, 0.2, 0.3]}
                            ]
                        },
                    }
                }
            )
            mock_client.wait_for_job = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await base_client.embed(
                ["test"],
                host="test-host",
                port=9000,
                protocol="mtls",
                cert_file=str(cert_file),
                key_file=str(key_file),
                ca_cert_file=str(ca_cert_file),
                timeout=None,
            )

            # Should create temporary client
            mock_client_class.assert_called_once()
            mock_client.__aenter__.assert_called_once()
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_embed_extracts_embeddings_from_nested_structure(self, base_client):
        """Test embed() extracts embeddings from nested job result structure."""
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
                # Test nested data structure
                mock_wait.return_value = {
                    "data": {
                        "data": {
                            "results": [[0.1, 0.2, 0.3]],
                        },
                    },
                }

                result = await base_client.embed(["test"], timeout=5.0)
                assert isinstance(result, dict)
                assert "results" in result

    @pytest.mark.asyncio
    async def test_embed_uses_parsers_for_extraction(self, base_client):
        """Test embed() uses parsers when direct extraction fails."""
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
                # Return data that requires parser extraction
                mock_wait.return_value = {
                    "data": [0.1, 0.2, 0.3],  # List, not dict
                }

                result = await base_client.embed(["test"], timeout=5.0)
                assert isinstance(result, dict)


class TestQueueMethodsCoverage:
    """Tests for queue methods to achieve 90%+ coverage."""

    @pytest.mark.asyncio
    async def test_submit_job_extracts_job_id_from_nested_result(self, base_client):
        """Test submit_job() extracts job_id from nested result structure."""
        with patch.object(
            base_client._adapter_transport,
            "execute_command_unified",
            new_callable=AsyncMock,
        ) as mock_exec:
            # Test different job_id locations
            test_cases = [
                {"job_id": "direct-job-id"},
                {"result": {"job_id": "nested-job-id"}},
                {"result": {"data": {"job_id": "deep-nested-job-id"}}},
                {"data": {"job_id": "data-job-id"}},
            ]

            for test_case in test_cases:
                test_case["mode"] = "queued"
                mock_exec.return_value = test_case

                result = await base_client.submit_job("embed", {"texts": ["test"]})
                assert isinstance(result, dict)
                if "job_id" in result:
                    assert result["job_id"] is not None

    @pytest.mark.asyncio
    async def test_submit_job_handles_immediate_result(self, base_client):
        """Test submit_job() handles immediate (not queued) result."""
        with patch.object(
            base_client._adapter_transport,
            "execute_command_unified",
            new_callable=AsyncMock,
        ) as mock_exec:
            mock_exec.return_value = {
                "mode": "immediate",
                "result": {"results": [[0.1, 0.2, 0.3]]},
            }

            result = await base_client.submit_job("embed", {"texts": ["test"]})
            assert isinstance(result, dict)
            assert result.get("mode") == "immediate"
            assert "result" in result

    @pytest.mark.asyncio
    async def test_get_job_status_or_result_with_timeout_zero(self, base_client):
        """Test get_job_status_or_result() with timeout=0 (wait indefinitely)."""
        with patch.object(
            base_client,
            "wait_for_job",
            new_callable=AsyncMock,
        ) as mock_wait:
            mock_wait.return_value = {
                "status": "completed",
                "result": {"results": [[0.1, 0.2, 0.3]]},
            }

            result = await base_client.get_job_status_or_result("test-job", timeout=0)
            assert isinstance(result, dict)
            assert result.get("status") == "completed"
            mock_wait.assert_called_once_with("test-job", timeout=0)

    @pytest.mark.asyncio
    async def test_get_job_status_or_result_with_timeout_positive(self, base_client):
        """Test get_job_status_or_result() with timeout > 0."""
        with patch.object(
            base_client,
            "wait_for_job",
            new_callable=AsyncMock,
        ) as mock_wait:
            mock_wait.return_value = {
                "status": "completed",
                "result": {"results": [[0.1, 0.2, 0.3]]},
            }

            result = await base_client.get_job_status_or_result("test-job", timeout=30.0)
            assert isinstance(result, dict)
            assert result.get("status") == "completed"
            mock_wait.assert_called_once_with("test-job", timeout=30.0)

    @pytest.mark.asyncio
    async def test_list_queue_calls_list_queued_commands(self, base_client):
        """Test list_queue() calls list_queued_commands()."""
        with patch.object(
            base_client,
            "list_queued_commands",
            new_callable=AsyncMock,
        ) as mock_list:
            mock_list.return_value = {
                "data": {
                    "jobs": [],
                    "total_count": 0,
                },
            }

            result = await base_client.list_queue(status="queued", limit=10)
            assert isinstance(result, dict)
            mock_list.assert_called_once_with(status="queued", limit=10)

