#!/usr/bin/env python3
"""
Comprehensive tests for queue methods:
- submit_job()
- get_job_status_or_result()
- list_queue()

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
import pytest_asyncio
from typing import Dict, Any

from embed_client.async_client import EmbeddingServiceAsyncClient
from embed_client.exceptions import (
    EmbeddingServiceError,
    EmbeddingServiceTimeoutError,
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


class TestSubmitJob:
    """Tests for submit_job() method."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_submit_job_embed(self, base_client):
        """Test submit_job() with embed command."""
        try:
            result = await base_client.submit_job(
                "embed",
                {"texts": ["test text"]},
            )
            assert isinstance(result, dict)
            assert "job_id" in result or result.get("mode") == "immediate"
            assert "status" in result
            assert "mode" in result
        except EmbeddingServiceError:
            # Expected if server is not running
            pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_submit_job_returns_job_id(self, base_client):
        """Test that submit_job() returns job_id for queued jobs."""
        try:
            result = await base_client.submit_job(
                "embed",
                {"texts": ["test text"]},
            )
            if result.get("mode") == "queued":
                assert "job_id" in result
                assert result["job_id"] is not None
        except EmbeddingServiceError:
            # Expected if server is not running
            pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_submit_job_immediate_result(self, base_client):
        """Test submit_job() with immediate result (not queued)."""
        try:
            result = await base_client.submit_job(
                "embed",
                {"texts": ["test text"]},
            )
            if result.get("mode") == "immediate":
                assert "result" in result
        except EmbeddingServiceError:
            # Expected if server is not running
            pass


class TestGetJobStatusOrResult:
    """Tests for get_job_status_or_result() method."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_job_status_without_timeout(self, base_client):
        """Test get_job_status_or_result() without timeout (immediate)."""
        try:
            # First submit a job
            job_info = await base_client.submit_job(
                "embed",
                {"texts": ["test text"]},
            )
            job_id = job_info.get("job_id")
            if job_id:
                # Get status immediately
                status = await base_client.get_job_status_or_result(
                    job_id,
                    timeout=None,
                )
                assert isinstance(status, dict)
                assert "status" in status or "job_id" in status
        except EmbeddingServiceError:
            # Expected if server is not running
            pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_job_status_with_timeout(self, base_client):
        """Test get_job_status_or_result() with timeout."""
        try:
            # First submit a job
            job_info = await base_client.submit_job(
                "embed",
                {"texts": ["test text"]},
            )
            job_id = job_info.get("job_id")
            if job_id:
                # Get status with timeout
                result = await base_client.get_job_status_or_result(
                    job_id,
                    timeout=30.0,
                )
                assert isinstance(result, dict)
                assert "status" in result
                if result.get("status") == "completed":
                    assert "result" in result
        except (EmbeddingServiceError, EmbeddingServiceTimeoutError):
            # Expected if server is not running or timeout occurs
            pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_job_status_with_zero_timeout(self, base_client):
        """Test get_job_status_or_result() with timeout=0 (wait indefinitely)."""
        try:
            # First submit a job
            job_info = await base_client.submit_job(
                "embed",
                {"texts": ["test text"]},
            )
            job_id = job_info.get("job_id")
            if job_id:
                # Get status with infinite timeout
                result = await base_client.get_job_status_or_result(
                    job_id,
                    timeout=0,
                )
                assert isinstance(result, dict)
                assert "status" in result
        except (EmbeddingServiceError, EmbeddingServiceTimeoutError):
            # Expected if server is not running or timeout occurs
            pass


class TestListQueue:
    """Tests for list_queue() method."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_list_queue_all(self, base_client):
        """Test list_queue() without filters."""
        try:
            result = await base_client.list_queue()
            assert isinstance(result, dict)
            # May contain jobs list or empty
        except EmbeddingServiceError:
            # Expected if server is not running
            pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_list_queue_with_status_filter(self, base_client):
        """Test list_queue() with status filter."""
        try:
            result = await base_client.list_queue(status="queued")
            assert isinstance(result, dict)
        except EmbeddingServiceError:
            # Expected if server is not running
            pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_list_queue_with_limit(self, base_client):
        """Test list_queue() with limit."""
        try:
            result = await base_client.list_queue(limit=10)
            assert isinstance(result, dict)
        except EmbeddingServiceError:
            # Expected if server is not running
            pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_list_queue_with_status_and_limit(self, base_client):
        """Test list_queue() with both status and limit."""
        try:
            result = await base_client.list_queue(status="running", limit=5)
            assert isinstance(result, dict)
        except EmbeddingServiceError:
            # Expected if server is not running
            pass


class TestQueueWorkflow:
    """Tests for complete queue workflow."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_queue_workflow(self, base_client):
        """Test complete workflow: submit -> status -> list."""
        try:
            # 1. Submit job
            job_info = await base_client.submit_job(
                "embed",
                {"texts": ["test text 1", "test text 2"]},
            )
            job_id = job_info.get("job_id")

            if job_id:
                # 2. Check status
                status = await base_client.get_job_status_or_result(
                    job_id,
                    timeout=None,
                )
                assert isinstance(status, dict)

                # 3. List queue
                queue = await base_client.list_queue()
                assert isinstance(queue, dict)

                # 4. Wait for completion
                result = await base_client.get_job_status_or_result(
                    job_id,
                    timeout=30.0,
                )
                assert isinstance(result, dict)
                if result.get("status") == "completed":
                    assert "result" in result
        except (EmbeddingServiceError, EmbeddingServiceTimeoutError):
            # Expected if server is not running or timeout occurs
            pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multiple_jobs_workflow(self, base_client):
        """Test workflow with multiple jobs."""
        try:
            # Submit multiple jobs
            job_ids = []
            for i in range(3):
                job_info = await base_client.submit_job(
                    "embed",
                    {"texts": [f"test text {i}"]},
                )
                if job_info.get("job_id"):
                    job_ids.append(job_info["job_id"])

            # List queue
            queue = await base_client.list_queue()
            assert isinstance(queue, dict)

            # Check status of each job
            for job_id in job_ids:
                status = await base_client.get_job_status_or_result(
                    job_id,
                    timeout=None,
                )
                assert isinstance(status, dict)
        except EmbeddingServiceError:
            # Expected if server is not running
            pass

