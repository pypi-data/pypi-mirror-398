#!/usr/bin/env python3
"""
Additional tests for async_client_api_mixin.py to achieve 90%+ coverage.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

from embed_client.async_client import EmbeddingServiceAsyncClient
from embed_client.exceptions import EmbeddingServiceAPIError


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


class TestAPIMixin90Plus:
    """Tests to achieve 90%+ coverage for async_client_api_mixin.py."""

    @pytest.mark.asyncio
    async def test_cmd_job_result_with_result_key(self, base_client):
        """Test cmd() with job_result containing 'result' key."""
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
                    "result": {"success": True, "data": {"results": [[0.1]]}},
                }

                result = await base_client.cmd("embed", {"texts": ["test"]})
                assert "result" in result

    @pytest.mark.asyncio
    async def test_cmd_job_result_with_data_key(self, base_client):
        """Test cmd() with job_result containing 'data' key."""
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
                assert result["result"]["success"] is True

    @pytest.mark.asyncio
    async def test_cmd_job_result_non_dict(self, base_client):
        """Test cmd() with job_result as non-dict."""
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
                mock_wait.return_value = "string result"

                result = await base_client.cmd("embed", {"texts": ["test"]})
                assert "result" in result
                assert result["result"]["success"] is True

    @pytest.mark.asyncio
    async def test_cmd_normalized_return(self, base_client):
        """Test cmd() returning normalized response."""
        with patch.object(
            base_client._adapter_transport,
            "execute_command_unified",
            new_callable=AsyncMock,
        ) as mock_exec:
            mock_exec.return_value = "some result"

            with patch(
                "embed_client.async_client_api_mixin.ResponseNormalizer.normalize_command_response"
            ) as mock_norm:
                mock_norm.return_value = {
                    "result": {"success": True, "data": {"results": [[0.1]]}},
                }

                result = await base_client.cmd("embed", {"texts": ["test"]})
                assert "result" in result

    @pytest.mark.asyncio
    async def test_embed_with_config_object_get_all(self, base_client):
        """Test embed() with config object using get_all()."""
        from embed_client.config import ClientConfig

        config = ClientConfig()
        config.set("server.host", "localhost")
        config.set("server.port", 8001)
        config.set("auth.method", "none")
        config.set("ssl.enabled", False)

        async with EmbeddingServiceAsyncClient(config=config) as client:
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

                result = await client.embed(
                    ["test"],
                    host="test-host",
                    timeout=None,
                )

                assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_embed_with_crl_file_override(self, base_client):
        """Test embed() with crl_file override."""
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
                crl_file="/path/to/crl.pem",
                timeout=None,
            )

            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_embed_with_model_override(self, base_client):
        """Test embed() with model parameter."""
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

            result = await base_client.embed(["test"], model="test-model", timeout=None)
            assert isinstance(result, dict)
            # Check that model was passed to cmd
            call_args = mock_cmd.call_args
            # call_args is (args, kwargs), where args[0] is command, kwargs contains params
            # cmd is called as cmd(command, params=params, validate_texts=False)
            if call_args.kwargs and "params" in call_args.kwargs:
                params = call_args.kwargs["params"]
            else:
                params = call_args[0][1] if len(call_args[0]) > 1 else {}
            assert params.get("model") == "test-model"

    @pytest.mark.asyncio
    async def test_embed_with_dimension_override(self, base_client):
        """Test embed() with dimension parameter."""
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

            result = await base_client.embed(["test"], dimension=384, timeout=None)
            assert isinstance(result, dict)
            # Check that dimension was passed to cmd
            call_args = mock_cmd.call_args
            # call_args is (args, kwargs), where args[0] is command, kwargs contains params
            # cmd is called as cmd(command, params=params, validate_texts=False)
            if call_args.kwargs and "params" in call_args.kwargs:
                params = call_args.kwargs["params"]
            else:
                params = call_args[0][1] if len(call_args[0]) > 1 else {}
            assert params.get("dimension") == 384

    @pytest.mark.asyncio
    async def test_embed_with_extra_params(self, base_client):
        """Test embed() with extra_params."""
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

            result = await base_client.embed(
                ["test"], extra_param="value", timeout=None
            )
            assert isinstance(result, dict)
            # Check that extra_param was passed
            call_args = mock_cmd.call_args
            # call_args is (args, kwargs), where args[0] is command, kwargs contains params
            # cmd is called as cmd(command, params=params, validate_texts=False)
            if call_args.kwargs and "params" in call_args.kwargs:
                params = call_args.kwargs["params"]
            else:
                params = call_args[0][1] if len(call_args[0]) > 1 else {}
            assert params.get("extra_param") == "value"

    @pytest.mark.asyncio
    async def test_embed_result_with_nested_results(self, base_client):
        """Test embed() with result containing nested results."""
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
                    "data": {
                        "data": {
                            "results": [
                                {"body": "test", "embedding": [0.1, 0.2, 0.3]}
                            ]
                        }
                    }
                }

                result = await base_client.embed(["test"], timeout=5.0)
                assert isinstance(result, dict)
                assert "results" in result

    @pytest.mark.asyncio
    async def test_embed_result_with_nested_embeddings(self, base_client):
        """Test embed() with result containing nested embeddings."""
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
                    "data": {
                        "data": {
                            "embeddings": [[0.1, 0.2, 0.3]]
                        }
                    }
                }

                result = await base_client.embed(["test"], timeout=5.0)
                assert isinstance(result, dict)
                assert "embeddings" in result

    @pytest.mark.asyncio
    async def test_embed_extract_embedding_data_fallback(self, base_client):
        """Test embed() with extract_embedding_data fallback."""
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
                            {"body": "test", "embedding": [0.1], "tokens": ["test"], "bm25_tokens": ["test"]}
                        ]
                    },
                },
            }

            result = await base_client.embed(["test"], timeout=None)
            assert isinstance(result, dict)
            # Should use extract_embedding_data or extract_embeddings fallback
            assert "results" in result or "embeddings" in result

    @pytest.mark.asyncio
    async def test_embed_extract_embeddings_fallback(self, base_client):
        """Test embed() with extract_embeddings fallback."""
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
                            {"body": "test", "embedding": [0.1], "tokens": ["test"], "bm25_tokens": ["test"]}
                        ]
                    },
                },
            }

            result = await base_client.embed(["test"], timeout=None)
            assert isinstance(result, dict)
            # Should use extract_embeddings fallback
            assert "results" in result or "embeddings" in result

    @pytest.mark.asyncio
    async def test_embed_result_data_as_list(self, base_client):
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

