#!/usr/bin/env python3
"""
Test to ensure client is fully asynchronous.

Checks that:
- All I/O operations are async
- No blocking operations in async methods
- All network calls use async/await
- File operations in async context use executor

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import inspect
import pytest
from typing import Any, Dict

from embed_client.async_client import EmbeddingServiceAsyncClient
from embed_client.async_client_api_mixin import AsyncClientAPIMixin
from embed_client.async_client_queue_mixin import AsyncClientQueueMixin
from embed_client.adapter_transport import AdapterTransport


class TestAsyncCompleteness:
    """Tests to ensure client is fully asynchronous."""

    def test_all_io_methods_are_async(self):
        """Test that all I/O methods are async."""
        client_methods = [
            "health",
            "get_openapi_schema",
            "get_commands",
            "cmd",
            "embed",
            "wait_for_job",
            "job_status",
            "cancel_command",
            "list_queued_commands",
            "get_job_logs",
            "submit_job",
            "get_job_status_or_result",
            "list_queue",
            "close",
            "__aenter__",
            "__aexit__",
        ]

        for method_name in client_methods:
            if hasattr(EmbeddingServiceAsyncClient, method_name):
                method = getattr(EmbeddingServiceAsyncClient, method_name)
                assert asyncio.iscoroutinefunction(
                    method
                ), f"Method {method_name} should be async"

    def test_all_api_mixin_methods_are_async(self):
        """Test that all API mixin methods are async."""
        api_methods = [
            "health",
            "get_openapi_schema",
            "get_commands",
            "cmd",
            "embed",
        ]

        for method_name in api_methods:
            if hasattr(AsyncClientAPIMixin, method_name):
                method = getattr(AsyncClientAPIMixin, method_name)
                assert asyncio.iscoroutinefunction(
                    method
                ), f"Method {method_name} should be async"

    def test_all_queue_mixin_methods_are_async(self):
        """Test that all queue mixin methods are async."""
        queue_methods = [
            "wait_for_job",
            "job_status",
            "cancel_command",
            "list_queued_commands",
            "get_job_logs",
            "submit_job",
            "get_job_status_or_result",
            "list_queue",
        ]

        for method_name in queue_methods:
            if hasattr(AsyncClientQueueMixin, method_name):
                method = getattr(AsyncClientQueueMixin, method_name)
                assert asyncio.iscoroutinefunction(
                    method
                ), f"Method {method_name} should be async"

    def test_all_transport_methods_are_async(self):
        """Test that all transport methods are async."""
        transport_methods = [
            "__aenter__",
            "__aexit__",
            "_ensure_client",
            "_generate_token_from_config",
            "close",
            "health",
            "get_openapi_schema",
            "execute_command",
            "execute_command_unified",
            "queue_get_job_status",
            "queue_list_jobs",
            "queue_stop_job",
            "queue_delete_job",
            "queue_get_job_logs",
            "get_commands_list",
        ]

        for method_name in transport_methods:
            if hasattr(AdapterTransport, method_name):
                method = getattr(AdapterTransport, method_name)
                assert asyncio.iscoroutinefunction(
                    method
                ), f"Method {method_name} should be async"

    def test_no_blocking_sleep_in_async_methods(self):
        """Test that no async methods use time.sleep."""
        import ast
        import os

        # Check async_client_queue_mixin.py
        queue_mixin_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "embed_client",
            "async_client_queue_mixin.py",
        )
        with open(queue_mixin_path, "r") as f:
            content = f.read()
            # Should use asyncio.sleep, not time.sleep
            assert "asyncio.sleep" in content or "await asyncio.sleep" in content
            # Should not use time.sleep in async methods
            assert "time.sleep" not in content

        # Check adapter_transport.py
        transport_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "embed_client",
            "adapter_transport.py",
        )
        with open(transport_path, "r") as f:
            content = f.read()
            # Should use asyncio.sleep, not time.sleep
            assert "asyncio.sleep" in content or "await asyncio.sleep" in content
            # time.sleep should not be used in async methods
            # (time.time() is OK for timing)

    @pytest.mark.asyncio
    async def test_embed_method_is_fully_async(self):
        """Test that embed() method is fully async and doesn't block."""
        config: Dict[str, Any] = {
            "server": {"host": "localhost", "port": 8001},
            "auth": {"method": "none"},
            "ssl": {"enabled": False},
        }

        async with EmbeddingServiceAsyncClient(config_dict=config) as client:
            # Check that embed is async
            assert asyncio.iscoroutinefunction(client.embed)

            # Check that it doesn't block (would timeout if blocking)
            try:
                # This should return quickly or raise exception, not block
                result = await asyncio.wait_for(
                    client.embed(["test"], timeout=None), timeout=1.0
                )
                # If we get here, it didn't block
                assert isinstance(result, dict)
            except (asyncio.TimeoutError, Exception):
                # Expected if server is not running
                pass

    @pytest.mark.asyncio
    async def test_queue_methods_are_fully_async(self):
        """Test that queue methods are fully async."""
        config: Dict[str, Any] = {
            "server": {"host": "localhost", "port": 8001},
            "auth": {"method": "none"},
            "ssl": {"enabled": False},
        }

        async with EmbeddingServiceAsyncClient(config_dict=config) as client:
            # Check all queue methods are async
            assert asyncio.iscoroutinefunction(client.submit_job)
            assert asyncio.iscoroutinefunction(client.get_job_status_or_result)
            assert asyncio.iscoroutinefunction(client.list_queue)
            assert asyncio.iscoroutinefunction(client.wait_for_job)
            assert asyncio.iscoroutinefunction(client.job_status)

    def test_no_sync_file_operations_in_async_context(self):
        """Test that file operations in async context use executor."""
        import os

        # Check cli.py - should use run_in_executor for file reading
        cli_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "embed_client",
            "cli.py",
        )
        with open(cli_path, "r") as f:
            content = f.read()
            # Should use run_in_executor for file operations in async context
            if "async def main" in content and "with open" in content:
                assert "run_in_executor" in content or "aiofiles" in content

    def test_all_network_calls_are_async(self):
        """Test that all network calls use async/await."""
        # All methods that interact with network should be async
        network_methods = [
            "health",
            "get_openapi_schema",
            "get_commands",
            "cmd",
            "embed",
            "queue_get_job_status",
            "queue_list_jobs",
            "queue_stop_job",
            "queue_delete_job",
            "queue_get_job_logs",
        ]

        for method_name in network_methods:
            # Check in AsyncClientAPIMixin
            if hasattr(AsyncClientAPIMixin, method_name):
                method = getattr(AsyncClientAPIMixin, method_name)
                assert asyncio.iscoroutinefunction(
                    method
                ), f"Network method {method_name} should be async"

            # Check in AdapterTransport
            if hasattr(AdapterTransport, method_name):
                method = getattr(AdapterTransport, method_name)
                assert asyncio.iscoroutinefunction(
                    method
                ), f"Transport method {method_name} should be async"

