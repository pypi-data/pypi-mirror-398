"""
Queue and job management methods for EmbeddingServiceAsyncClient.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, Optional

from embed_client.exceptions import (
    EmbeddingServiceAPIError,
    EmbeddingServiceError,
    EmbeddingServiceTimeoutError,
)
from embed_client.response_normalizer import ResponseNormalizer


class AsyncClientQueueMixin:
    """Mixin that provides queue-related operations for the async client."""

    async def wait_for_job(
        self,
        job_id: str,
        timeout: Optional[float] = 60.0,
        poll_interval: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Wait for job completion and return results.

        Args:
            job_id: Job ID to wait for.
            timeout: Maximum time to wait in seconds.
                    If None, return immediately without waiting.
                    If 0, wait indefinitely (no timeout).
                    Default: 60.0 seconds.
            poll_interval: Time between queue status checks in seconds.
                          Default: 1.0 second.

        Returns:
            Job result data.

        Raises:
            EmbeddingServiceTimeoutError: If timeout > 0 and job doesn't complete in time.
            EmbeddingServiceAPIError: If job fails.
            EmbeddingServiceError: If waiting fails.
        """
        try:
            status = await self.job_status(job_id)  # type: ignore[attr-defined]
            logger = logging.getLogger("EmbeddingServiceAsyncClient.wait_for_job")
            logger.debug("Initial job status: %s", status)

            # If timeout is None, return immediately without waiting
            if timeout is None:
                return status

            # Check initial status - job might already be completed
            current_status = status.get("status", "unknown")
            if current_status in ("completed", "success", "done"):
                result = status.get("result")
                if result:
                    if isinstance(result, Dict) and "data" in result:
                        return result["data"]
                    return result
                return status

            if current_status in ("failed", "error"):
                error = status.get("error", status.get("message", "Job failed"))
                raise EmbeddingServiceAPIError({"message": str(error)})

            # If timeout is 0, wait indefinitely
            if timeout == 0:
                while True:
                    await asyncio.sleep(poll_interval)
                    status = await self.job_status(job_id)  # type: ignore[attr-defined]
                    current_status = status.get("status", "unknown")
                    logger.debug(
                        "Job %s status: %s, full status: %s", job_id, current_status, status
                    )

                    if current_status in ("completed", "success", "done"):
                        result = status.get("result")
                        if result:
                            if isinstance(result, Dict) and "data" in result:
                                return result["data"]
                            return result
                        return status
                    if current_status in ("failed", "error"):
                        error = status.get("error", status.get("message", "Job failed"))
                        raise EmbeddingServiceAPIError({"message": str(error)})

            # Wait with timeout
            start_time = time.time()

            while time.time() - start_time < timeout:
                await asyncio.sleep(poll_interval)
                status = await self.job_status(job_id)  # type: ignore[attr-defined]
                current_status = status.get("status", "unknown")
                logger.debug(
                    "Job %s status: %s, full status: %s", job_id, current_status, status
                )

                if current_status in ("completed", "success", "done"):
                    result = status.get("result")
                    if result:
                        if isinstance(result, Dict) and "data" in result:
                            return result["data"]
                        return result
                    return status
                if current_status in ("failed", "error"):
                    error = status.get("error", status.get("message", "Job failed"))
                    raise EmbeddingServiceAPIError({"message": str(error)})

            raise EmbeddingServiceTimeoutError(
                f"Job {job_id} did not complete within {timeout} seconds"
            )
        except (EmbeddingServiceTimeoutError, EmbeddingServiceAPIError):
            raise
        except Exception as exc:  # noqa: BLE001
            raise EmbeddingServiceError(f"Failed to wait for job: {exc}") from exc

    async def job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status from the queue."""
        try:
            status = await self._adapter_transport.queue_get_job_status(job_id)  # type: ignore[attr-defined]
            normalized = ResponseNormalizer.normalize_queue_status(status)
            logger = logging.getLogger("EmbeddingServiceAsyncClient.job_status")
            logger.debug("Raw status: %s, Normalized: %s", status, normalized)
            return normalized
        except Exception as exc:  # noqa: BLE001
            raise EmbeddingServiceError(f"Failed to get job status: {exc}") from exc

    async def cancel_command(self, job_id: str) -> Dict[str, Any]:
        """Cancel a command execution in queue."""
        try:
            await self._adapter_transport.queue_stop_job(job_id)  # type: ignore[attr-defined]
            return await self._adapter_transport.queue_delete_job(job_id)  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001
            raise EmbeddingServiceError(f"Failed to cancel command: {exc}") from exc

    async def list_queued_commands(
        self,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """List commands currently in the queue."""
        try:
            result = await self._adapter_transport.queue_list_jobs(  # type: ignore[attr-defined]
                status=status,
                job_type="command_execution",
            )

            if limit and "data" in result:
                jobs = result.get("data", {}).get("jobs", [])
                if len(jobs) > limit:
                    result["data"]["jobs"] = jobs[:limit]
                    result["data"]["total_count"] = limit

            return result
        except Exception as exc:  # noqa: BLE001
            raise EmbeddingServiceError(
                f"Failed to list queued commands: {exc}"
            ) from exc

    async def get_job_logs(self, job_id: str) -> Dict[str, Any]:
        """Get job logs (stdout/stderr) from the queue."""
        try:
            return await self._adapter_transport.queue_get_job_logs(job_id)  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001
            raise EmbeddingServiceError(f"Failed to get job logs: {exc}") from exc

    async def submit_job(
        self,
        command: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Submit a job to the queue and return job ID.

        This method submits a command to the queue without waiting for completion.
        Use get_job_status_or_result() to check status or get results.

        Args:
            command: Command name to execute (e.g., "embed").
            params: Command parameters dictionary.

        Returns:
            Dictionary with job information:
            - job_id: Job identifier for status checking
            - status: Initial job status (usually "queued" or "pending")
            - mode: "queued" if job was queued

        Raises:
            EmbeddingServiceError: If job submission fails.
        """
        try:
            result = await self._adapter_transport.execute_command_unified(  # type: ignore[attr-defined]
                command=command,
                params=params or {},
                use_cmd_endpoint=False,
                auto_poll=False,
            )

            # Extract job_id from result
            job_id = (
                result.get("job_id")
                or result.get("result", {}).get("job_id")
                or result.get("result", {}).get("data", {}).get("job_id")
                or result.get("data", {}).get("job_id")
            )

            if job_id:
                return {
                    "job_id": job_id,
                    "status": result.get("status", "queued"),
                    "mode": "queued",
                }
            else:
                # If not queued, return immediate result
                return {
                    "job_id": None,
                    "status": "completed",
                    "mode": "immediate",
                    "result": result.get("result", result),
                }
        except Exception as exc:  # noqa: BLE001
            raise EmbeddingServiceError(f"Failed to submit job: {exc}") from exc

    async def get_job_status_or_result(
        self,
        job_id: str,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Get job status or result if job is completed.

        This method checks job status and returns result if job is completed.
        If timeout is specified and job is not completed, waits up to timeout seconds.

        Args:
            job_id: Job identifier from submit_job().
            timeout: Optional timeout in seconds. If None, returns current status immediately.
                    If 0, waits indefinitely. If > 0, waits up to specified seconds.

        Returns:
            Dictionary with job status and result:
            - status: Job status ("queued", "pending", "running", "completed", "failed", "error")
            - result: Job result data (if completed)
            - job_id: Job identifier

        Raises:
            EmbeddingServiceTimeoutError: If timeout > 0 and job doesn't complete in time.
            EmbeddingServiceAPIError: If job fails.
            EmbeddingServiceError: If status check fails.
        """
        if timeout is None:
            # Return current status immediately
            return await self.job_status(job_id)  # type: ignore[attr-defined]
        else:
            # Wait for completion with timeout
            result = await self.wait_for_job(job_id, timeout=timeout)  # type: ignore[attr-defined]
            return {
                "status": "completed",
                "result": result,
                "job_id": job_id,
            }

    async def list_queue(
        self,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get list of jobs in the queue.

        This is an alias for list_queued_commands() for consistency.

        Args:
            status: Optional status filter ("queued", "running", "completed", "failed").
            limit: Optional limit on number of jobs to return.

        Returns:
            Dictionary with queue information:
            - jobs: List of job dictionaries
            - total_count: Total number of jobs (if limit is specified, may be less)

        Raises:
            EmbeddingServiceError: If queue listing fails.
        """
        return await self.list_queued_commands(status=status, limit=limit)  # type: ignore[attr-defined]


__all__ = ["AsyncClientQueueMixin"]
