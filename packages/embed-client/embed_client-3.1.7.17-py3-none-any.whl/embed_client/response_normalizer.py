"""
Response Normalizer

This module provides functions to normalize adapter responses to legacy format.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Any, Dict


class ResponseNormalizer:
    """
    Normalizes adapter responses to legacy format expected by EmbeddingServiceAsyncClient.

    Adapter returns responses in format:
    - Immediate: {"mode": "immediate", "command": "...", "result": {...}, "queued": False}
    - Queued: {"mode": "queued", "job_id": "...", "status": "...", "result": {...}, "queued": True}

    Legacy format expected:
    - {"result": {"success": bool, "data": {...}}}
    - {"error": {"code": int, "message": str, "details": ...}}
    """

    @staticmethod
    def normalize_command_response(adapter_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize adapter command response to legacy format.

        Args:
            adapter_response: Response from adapter execute_command_unified

        Returns:
            Normalized response in legacy format
        """
        mode = adapter_response.get("mode", "immediate")

        if mode == "queued":
            return ResponseNormalizer._normalize_queued_response(adapter_response)
        else:
            return ResponseNormalizer._normalize_immediate_response(adapter_response)

    @staticmethod
    def _normalize_immediate_response(
        adapter_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Normalize immediate response."""
        result = adapter_response.get("result", {})

        # If result is already in legacy format, return as-is
        if isinstance(result, dict) and ("success" in result or "data" in result):
            return {"result": result}

        # Wrap in legacy format
        return {"result": {"success": True, "data": result}}

    @staticmethod
    def _normalize_queued_response(adapter_response: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize queued response."""
        result = adapter_response.get("result")
        status = adapter_response.get("status", "unknown")
        job_id = adapter_response.get("job_id")

        # If result is already in legacy format, return as-is
        if isinstance(result, dict) and ("success" in result or "data" in result):
            # Add job metadata if available
            if job_id and "data" in result:
                result["data"]["job_id"] = job_id
                result["data"]["status"] = status
            return {"result": result}

        # Wrap in legacy format with job metadata
        data: Dict[str, Any]
        if isinstance(result, dict):
            data = result
        else:
            data = {}

        normalized: Dict[str, Any] = {
            "result": {
                "success": status in ("completed", "success"),
                "data": data,
            }
        }

        # Add job metadata
        if job_id:
            data["job_id"] = job_id
            data["status"] = status

        return normalized

    @staticmethod
    def extract_error_from_adapter(adapter_error: Exception) -> Dict[str, Any]:
        """
        Extract error information from adapter exception.

        Args:
            adapter_error: Exception raised by adapter

        Returns:
            Error dictionary in legacy format
        """
        error_msg = str(adapter_error)

        # Try to extract structured error if available
        if hasattr(adapter_error, "error"):
            error_data = adapter_error.error
            if isinstance(error_data, dict):
                return {"error": error_data}

        # Default error format
        return {"error": {"code": -32000, "message": error_msg, "details": None}}

    @staticmethod
    def normalize_queue_status(queue_status: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize queue status response to legacy format.

        Args:
            queue_status: Queue status from adapter (can be from queue_get_job_status or embed_job_status)

        Returns:
            Normalized status in legacy format
        """
        # Handle embed_job_status format
        if "result" in queue_status and isinstance(queue_status["result"], dict):
            result_data = queue_status["result"]
            if result_data.get("success") and "data" in result_data:
                data = result_data["data"]
                status = data.get("status", "unknown")
                # Check if done flag is set (embed_job_status specific)
                if data.get("done", False) and status == "completed":
                    status = "completed"
                result = data.get("result")
                return {
                    "status": status,
                    "result": result,
                    "exists": data.get("exists", True),
                }

        # Extract status from nested structures (standard queue format)
        status = queue_status.get("status")
        if not status:
            status = (
                queue_status.get("data", {}).get("status")
                or queue_status.get("result", {}).get("status")
                or queue_status.get("result", {}).get("data", {}).get("status")
                or "unknown"
            )

        # Extract result
        result = queue_status.get("result")
        if not result:
            result = queue_status.get("data", {}).get("result") or queue_status.get(
                "data", {}
            )

        return {"status": status, "result": result, "exists": status != "unknown"}
