#!/usr/bin/env python3
"""
Additional tests for AdapterTransport to achieve 90%+ coverage.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from embed_client.adapter_transport import AdapterTransport


@pytest_asyncio.fixture
async def transport():
    """Transport fixture."""
    transport = AdapterTransport(
        adapter_params={
            "protocol": "http",
            "host": "localhost",
            "port": 8001,
        }
    )
    yield transport
    await transport.close()


class TestAdapterTransportCoverage:
    """Tests for AdapterTransport to achieve 90%+ coverage."""

    @pytest.mark.asyncio
    async def test_execute_command_with_cmd_endpoint(self, transport):
        """Test execute_command() with use_cmd_endpoint=True."""
        with patch.object(
            transport,
            "_ensure_client",
            new_callable=AsyncMock,
        ) as mock_ensure:
            mock_client = AsyncMock()
            mock_client.cmd_call = AsyncMock(
                return_value={"success": True, "result": {"data": "test"}}
            )
            mock_ensure.return_value = mock_client

            result = await transport.execute_command(
                "embed", {"texts": ["test"]}, use_cmd_endpoint=True
            )
            assert isinstance(result, dict)
            mock_client.cmd_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_command_without_cmd_endpoint(self, transport):
        """Test execute_command() with use_cmd_endpoint=False."""
        with patch.object(
            transport,
            "_ensure_client",
            new_callable=AsyncMock,
        ) as mock_ensure:
            mock_client = AsyncMock()
            mock_client.execute_command = AsyncMock(
                return_value={"success": True, "result": {"data": "test"}}
            )
            mock_ensure.return_value = mock_client

            result = await transport.execute_command(
                "embed", {"texts": ["test"]}, use_cmd_endpoint=False
            )
            assert isinstance(result, dict)
            mock_client.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_command_unified_no_auto_poll(self, transport):
        """Test execute_command_unified() with auto_poll=False."""
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
                auto_poll=False,
            )
            assert isinstance(result, dict)
            # When auto_poll=False, it calls client.execute_command_unified directly
            mock_client.execute_command_unified.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_command_unified_queued_timeout_none(self, transport):
        """Test execute_command_unified() with queued mode and timeout=None."""
        with patch.object(
            transport,
            "_ensure_client",
            new_callable=AsyncMock,
        ) as mock_ensure:
            mock_client = AsyncMock()
            mock_client.execute_command_unified = AsyncMock(
                return_value={
                    "mode": "queued",
                    "job_id": "test-job-123",
                }
            )
            mock_ensure.return_value = mock_client

            result = await transport.execute_command_unified(
                "embed",
                {"texts": ["test"]},
                auto_poll=True,
                timeout=None,
            )
            assert isinstance(result, dict)
            assert result.get("mode") == "queued"

    @pytest.mark.asyncio
    async def test_execute_command_unified_queued_timeout_zero(self, transport):
        """Test execute_command_unified() with queued mode and timeout=0."""
        with patch.object(
            transport,
            "_ensure_client",
            new_callable=AsyncMock,
        ) as mock_ensure:
            mock_client = AsyncMock()
            mock_client.execute_command_unified = AsyncMock(
                return_value={
                    "mode": "queued",
                    "job_id": "test-job-123",
                }
            )
            mock_ensure.return_value = mock_client

            with patch.object(
                transport,
                "queue_get_job_status",
                new_callable=AsyncMock,
            ) as mock_status:
                mock_status.return_value = {"status": "running"}

                # This will wait indefinitely, so we'll timeout the test
                import asyncio
                try:
                    result = await asyncio.wait_for(
                        transport.execute_command_unified(
                            "embed",
                            {"texts": ["test"]},
                            auto_poll=True,
                            timeout=0,
                            poll_interval=0.01,
                        ),
                        timeout=0.1,
                    )
                except asyncio.TimeoutError:
                    # Expected - timeout=0 means wait indefinitely
                    pass

    @pytest.mark.asyncio
    async def test_execute_command_unified_queued_with_status_hook(self, transport):
        """Test execute_command_unified() with queued mode and status_hook."""
        async def status_hook(status: Dict[str, Any]) -> None:
            pass

        with patch.object(
            transport,
            "_ensure_client",
            new_callable=AsyncMock,
        ) as mock_ensure:
            mock_client = AsyncMock()
            mock_client.execute_command_unified = AsyncMock(
                return_value={
                    "mode": "queued",
                    "job_id": "test-job-123",
                }
            )
            mock_ensure.return_value = mock_client

            with patch.object(
                transport,
                "queue_get_job_status",
                new_callable=AsyncMock,
            ) as mock_status:
                mock_status.return_value = {
                    "status": "completed",
                    "result": {"data": {"results": [[0.1]]}},
                }

                result = await transport.execute_command_unified(
                    "embed",
                    {"texts": ["test"]},
                    auto_poll=True,
                    timeout=5.0,
                    status_hook=status_hook,
                )
                assert isinstance(result, dict)
                assert result.get("status") == "completed"

    @pytest.mark.asyncio
    async def test_execute_command_unified_queued_failed(self, transport):
        """Test execute_command_unified() with queued mode and failed status."""
        with patch.object(
            transport,
            "_ensure_client",
            new_callable=AsyncMock,
        ) as mock_ensure:
            mock_client = AsyncMock()
            mock_client.execute_command_unified = AsyncMock(
                return_value={
                    "mode": "queued",
                    "job_id": "test-job-123",
                }
            )
            mock_ensure.return_value = mock_client

            with patch.object(
                transport,
                "queue_get_job_status",
                new_callable=AsyncMock,
            ) as mock_status:
                mock_status.return_value = {
                    "status": "failed",
                    "result": {"error": "Job failed"},
                }

                result = await transport.execute_command_unified(
                    "embed",
                    {"texts": ["test"]},
                    auto_poll=True,
                    timeout=5.0,
                )
                assert isinstance(result, dict)
                assert result.get("status") == "failed"

    @pytest.mark.asyncio
    async def test_execute_command_unified_queued_timeout(self, transport):
        """Test execute_command_unified() with queued mode and timeout."""
        with patch.object(
            transport,
            "_ensure_client",
            new_callable=AsyncMock,
        ) as mock_ensure:
            mock_client = AsyncMock()
            mock_client.execute_command_unified = AsyncMock(
                return_value={
                    "mode": "queued",
                    "job_id": "test-job-123",
                }
            )
            mock_ensure.return_value = mock_client

            with patch.object(
                transport,
                "queue_get_job_status",
                new_callable=AsyncMock,
            ) as mock_status:
                mock_status.return_value = {"status": "running"}

                result = await transport.execute_command_unified(
                    "embed",
                    {"texts": ["test"]},
                    auto_poll=True,
                    timeout=0.1,
                    poll_interval=0.05,
                )
                assert isinstance(result, dict)
                assert result.get("status") == "timeout"

    @pytest.mark.asyncio
    async def test_queue_get_job_status(self, transport):
        """Test queue_get_job_status()."""
        with patch.object(
            transport,
            "_ensure_client",
            new_callable=AsyncMock,
        ) as mock_ensure:
            mock_client = AsyncMock()
            mock_client.queue_get_job_status = AsyncMock(
                return_value={"status": "completed", "result": {"data": "test"}}
            )
            mock_ensure.return_value = mock_client

            result = await transport.queue_get_job_status("test-job-123")
            assert isinstance(result, dict)
            assert result.get("status") == "completed"

    @pytest.mark.asyncio
    async def test_queue_list_jobs(self, transport):
        """Test queue_list_jobs()."""
        with patch.object(
            transport,
            "_ensure_client",
            new_callable=AsyncMock,
        ) as mock_ensure:
            mock_client = AsyncMock()
            mock_client.queue_list_jobs = AsyncMock(
                return_value={"data": {"jobs": [], "total_count": 0}}
            )
            mock_ensure.return_value = mock_client

            result = await transport.queue_list_jobs(status="queued")
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_queue_stop_job(self, transport):
        """Test queue_stop_job()."""
        with patch.object(
            transport,
            "_ensure_client",
            new_callable=AsyncMock,
        ) as mock_ensure:
            mock_client = AsyncMock()
            mock_client.queue_stop_job = AsyncMock(
                return_value={"success": True}
            )
            mock_ensure.return_value = mock_client

            result = await transport.queue_stop_job("test-job-123")
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_queue_delete_job(self, transport):
        """Test queue_delete_job()."""
        with patch.object(
            transport,
            "_ensure_client",
            new_callable=AsyncMock,
        ) as mock_ensure:
            mock_client = AsyncMock()
            mock_client.queue_delete_job = AsyncMock(
                return_value={"success": True}
            )
            mock_ensure.return_value = mock_client

            result = await transport.queue_delete_job("test-job-123")
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_queue_get_job_logs(self, transport):
        """Test queue_get_job_logs()."""
        with patch.object(
            transport,
            "_ensure_client",
            new_callable=AsyncMock,
        ) as mock_ensure:
            mock_client = AsyncMock()
            mock_client.queue_get_job_logs = AsyncMock(
                return_value={"logs": ["log1", "log2"]}
            )
            mock_ensure.return_value = mock_client

            result = await transport.queue_get_job_logs("test-job-123")
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_commands_list(self, transport):
        """Test get_commands_list()."""
        with patch.object(
            transport,
            "_ensure_client",
            new_callable=AsyncMock,
        ) as mock_ensure:
            mock_client = AsyncMock()
            mock_client.get_commands_list = AsyncMock(
                return_value={"commands": ["embed", "health"]}
            )
            mock_ensure.return_value = mock_client

            result = await transport.get_commands_list()
            assert isinstance(result, dict)

