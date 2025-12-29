#!/usr/bin/env python3
"""
Final tests to achieve 90%+ coverage for all modules.

Covers remaining edge cases and code paths.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from typing import Dict, Any

from embed_client.async_client import EmbeddingServiceAsyncClient
from embed_client.exceptions import EmbeddingServiceAPIError
from embed_client.exceptions import EmbeddingServiceError


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


class TestFinalCoverage:
    """Final tests to achieve 90%+ coverage."""

    @pytest.mark.asyncio
    async def test_embed_with_config_object(self, base_client):
        """Test embed() with config object instead of config_dict."""
        # Create client with config object
        from embed_client.config import ClientConfig
        
        config = ClientConfig()
        config.set("server.host", "localhost")
        config.set("server.port", 8001)
        config.set("auth.method", "none")
        config.set("ssl.enabled", False)
        
        async with EmbeddingServiceAsyncClient(config=config) as client:
            with patch.object(
                client._adapter_transport,
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

                result = await client.embed(["test"], timeout=None)
                assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_embed_with_all_certificate_overrides(self, base_client):
        """Test embed() with all certificate overrides."""
        from pathlib import Path
        
        cert_dir = Path(__file__).parent.parent / "mtls_certificates"
        cert_file = cert_dir / "client" / "embedding-service.crt"
        key_file = cert_dir / "client" / "embedding-service.key"
        ca_cert_file = cert_dir / "ca" / "ca.crt"
        crl_file = cert_dir / "crl" / "crl.pem" if (cert_dir / "crl").exists() else None

        if not all([cert_file.exists(), key_file.exists(), ca_cert_file.exists()]):
            pytest.skip("mTLS certificates not found")

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
                crl_file=str(crl_file) if crl_file else None,
                timeout=None,
            )

            assert isinstance(result, dict)
            mock_client_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_embed_with_https_protocol(self, base_client):
        """Test embed() with https protocol."""
        with patch(
            "embed_client.async_client.EmbeddingServiceAsyncClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
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
            mock_client_class.return_value = mock_client

            result = await base_client.embed(
                ["test"],
                protocol="https",
                timeout=None,
            )

            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_embed_with_http_protocol(self, base_client):
        """Test embed() with http protocol."""
        with patch(
            "embed_client.async_client.EmbeddingServiceAsyncClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
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
            mock_client_class.return_value = mock_client

            result = await base_client.embed(
                ["test"],
                protocol="http",
                timeout=None,
            )

            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_wait_for_job_with_zero_timeout_infinite_loop(self, base_client):
        """Test wait_for_job() with timeout=0 (infinite wait)."""
        call_count = 0
        
        async def mock_job_status(job_id: str) -> Dict[str, Any]:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return {"status": "running"}
            return {
                "status": "completed",
                "result": {"data": {"results": [[0.1]]}},
            }

        with patch.object(
            base_client,
            "job_status",
            new_callable=AsyncMock,
            side_effect=mock_job_status,
        ):
            result = await base_client.wait_for_job("test-job", timeout=0, poll_interval=0.01)
            assert isinstance(result, dict)
            assert call_count >= 3

    @pytest.mark.asyncio
    async def test_wait_for_job_initial_failed(self, base_client):
        """Test wait_for_job() with initial failed status."""
        with patch.object(
            base_client,
            "job_status",
            new_callable=AsyncMock,
        ) as mock_status:
            mock_status.return_value = {
                "status": "failed",
                "error": {"message": "Job failed"},
            }

            # timeout=None returns immediately, but should still check for failed status
            with pytest.raises(EmbeddingServiceAPIError):
                await base_client.wait_for_job("test-job", timeout=5.0)

    @pytest.mark.asyncio
    async def test_wait_for_job_initial_error(self, base_client):
        """Test wait_for_job() with initial error status."""
        with patch.object(
            base_client,
            "job_status",
            new_callable=AsyncMock,
        ) as mock_status:
            mock_status.return_value = {
                "status": "error",
                "message": "Job error",
            }

            # timeout=None returns immediately, but should still check for error status
            with pytest.raises(EmbeddingServiceAPIError):
                await base_client.wait_for_job("test-job", timeout=5.0)

    @pytest.mark.asyncio
    async def test_wait_for_job_zero_timeout_failed(self, base_client):
        """Test wait_for_job() with timeout=0 and failed status."""
        call_count = 0
        
        async def mock_job_status(job_id: str) -> Dict[str, Any]:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                return {"status": "running"}
            return {
                "status": "failed",
                "error": {"message": "Job failed"},
            }

        with patch.object(
            base_client,
            "job_status",
            new_callable=AsyncMock,
            side_effect=mock_job_status,
        ):
            with pytest.raises(EmbeddingServiceAPIError):
                await base_client.wait_for_job("test-job", timeout=0, poll_interval=0.01)

    @pytest.mark.asyncio
    async def test_list_queued_commands_with_limit(self, base_client):
        """Test list_queued_commands() with limit."""
        with patch.object(
            base_client._adapter_transport,
            "queue_list_jobs",
            new_callable=AsyncMock,
        ) as mock_list:
            mock_list.return_value = {
                "data": {
                    "jobs": [
                        {"id": "job1", "status": "queued"},
                        {"id": "job2", "status": "queued"},
                        {"id": "job3", "status": "queued"},
                    ],
                    "total_count": 3,
                },
            }

            result = await base_client.list_queued_commands(limit=2)
            assert isinstance(result, dict)
            assert len(result.get("data", {}).get("jobs", [])) == 2

    @pytest.mark.asyncio
    async def test_list_queued_commands_without_limit(self, base_client):
        """Test list_queued_commands() without limit."""
        with patch.object(
            base_client._adapter_transport,
            "queue_list_jobs",
            new_callable=AsyncMock,
        ) as mock_list:
            mock_list.return_value = {
                "data": {
                    "jobs": [
                        {"id": "job1", "status": "queued"},
                    ],
                    "total_count": 1,
                },
            }

            result = await base_client.list_queued_commands()
            assert isinstance(result, dict)
            assert len(result.get("data", {}).get("jobs", [])) == 1

    @pytest.mark.asyncio
    async def test_adapter_transport_ensure_client_with_token_generation(self):
        """Test _ensure_client() with token generation."""
        from embed_client.adapter_transport import AdapterTransport
        
        transport = AdapterTransport(
            adapter_params={
                "protocol": "http",
                "host": "localhost",
                "port": 8001,
                "token_header": "Authorization",
            }
        )
        transport._original_config = {"auth": {"method": "jwt"}}

        with patch(
            "embed_client.adapter_transport.JsonRpcClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            client = await transport._ensure_client()
            assert client is not None

    @pytest.mark.asyncio
    async def test_adapter_transport_ensure_client_without_token_header(self):
        """Test _ensure_client() without token_header."""
        from embed_client.adapter_transport import AdapterTransport
        
        transport = AdapterTransport(
            adapter_params={
                "protocol": "http",
                "host": "localhost",
                "port": 8001,
            }
        )

        with patch(
            "embed_client.adapter_transport.JsonRpcClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            client = await transport._ensure_client()
            assert client is not None

    @pytest.mark.asyncio
    async def test_adapter_transport_ensure_client_without_original_config(self):
        """Test _ensure_client() without original_config."""
        from embed_client.adapter_transport import AdapterTransport
        
        transport = AdapterTransport(
            adapter_params={
                "protocol": "http",
                "host": "localhost",
                "port": 8001,
                "token_header": "Authorization",
            }
        )
        transport._original_config = None

        with patch(
            "embed_client.adapter_transport.JsonRpcClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            client = await transport._ensure_client()
            assert client is not None

    @pytest.mark.asyncio
    async def test_adapter_transport_execute_command_unified_queued_success(self, base_client):
        """Test execute_command_unified() with queued mode and success status."""
        with patch.object(
            base_client._adapter_transport,
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
                base_client._adapter_transport,
                "queue_get_job_status",
                new_callable=AsyncMock,
            ) as mock_status:
                mock_status.return_value = {
                    "status": "success",
                    "result": {"data": {"results": [[0.1]]}},
                }

                result = await base_client._adapter_transport.execute_command_unified(
                    "embed",
                    {"texts": ["test"]},
                    auto_poll=True,
                    timeout=5.0,
                )
                assert isinstance(result, dict)
                assert result.get("status") == "success"

    @pytest.mark.asyncio
    async def test_adapter_transport_execute_command_unified_queued_done(self, base_client):
        """Test execute_command_unified() with queued mode and done status."""
        with patch.object(
            base_client._adapter_transport,
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
                base_client._adapter_transport,
                "queue_get_job_status",
                new_callable=AsyncMock,
            ) as mock_status:
                mock_status.return_value = {
                    "status": "done",
                    "result": {"data": {"results": [[0.1]]}},
                }

                result = await base_client._adapter_transport.execute_command_unified(
                    "embed",
                    {"texts": ["test"]},
                    auto_poll=True,
                    timeout=5.0,
                )
                assert isinstance(result, dict)
                assert result.get("status") == "done"

