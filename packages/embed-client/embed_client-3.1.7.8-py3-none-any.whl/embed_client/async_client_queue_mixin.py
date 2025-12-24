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
        timeout: float = 60.0,
        poll_interval: float = 1.0,
    ) -> Dict[str, Any]:
        """Wait for job completion and return results."""
        try:
            status = await self.job_status(job_id)  # type: ignore[attr-defined]
            logger = logging.getLogger("EmbeddingServiceAsyncClient.wait_for_job")
            logger.debug("Initial job status: %s", status)

            start_time = time.time()

            while time.time() - start_time < timeout:
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

                await asyncio.sleep(poll_interval)
                status = await self.job_status(job_id)  # type: ignore[attr-defined]

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


__all__ = ["AsyncClientQueueMixin"]
