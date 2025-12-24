"""
Core API methods for EmbeddingServiceAsyncClient (embed, cmd, health, etc.).

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from embed_client.exceptions import (
    EmbeddingServiceAPIError,
    EmbeddingServiceError,
)
from embed_client.response_normalizer import ResponseNormalizer
from embed_client.response_parsers import (
    extract_embedding_data,
    extract_embeddings,
)


class AsyncClientAPIMixin:
    """Mixin that provides high-level API methods for the async client."""

    async def health(
        self,
        base_url: Optional[str] = None,
        port: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Check the health of the service.

        Args:
            base_url: Override base URL (not used with adapter).
            port: Override port (not used with adapter).
        """
        del base_url, port  # kept for backward-compatible signature
        try:
            return await self._adapter_transport.health()  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001
            raise EmbeddingServiceError(f"Health check failed: {exc}") from exc

    async def get_openapi_schema(
        self,
        base_url: Optional[str] = None,
        port: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get the OpenAPI schema of the service.

        Args:
            base_url: Override base URL (not used with adapter).
            port: Override port (not used with adapter).
        """
        del base_url, port
        try:
            return await self._adapter_transport.get_openapi_schema()  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001
            raise EmbeddingServiceError(f"Failed to get OpenAPI schema: {exc}") from exc

    async def get_commands(
        self,
        base_url: Optional[str] = None,
        port: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get the list of available commands.

        Args:
            base_url: Override base URL (not used with adapter).
            port: Override port (not used with adapter).
        """
        del base_url, port
        try:
            return await self._adapter_transport.get_commands_list()  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001
            raise EmbeddingServiceError(f"Failed to get commands: {exc}") from exc

    def _validate_texts(self, texts: List[str]) -> None:
        """
        Validate input texts before sending to the API.

        Args:
            texts: List of texts to validate

        Raises:
            EmbeddingServiceAPIError: If texts are invalid
        """
        if not texts:
            raise EmbeddingServiceAPIError(
                {"code": -32602, "message": "Empty texts list provided"}
            )

        invalid_texts: List[str] = []
        for i, text in enumerate(texts):
            if not isinstance(text, str):
                invalid_texts.append(f"Text at index {i} is not a string")
                continue
            if not text or not text.strip():
                invalid_texts.append(
                    f"Text at index {i} is empty or contains only whitespace"
                )
            elif len(text.strip()) < 2:
                invalid_texts.append(
                    f"Text at index {i} is too short (minimum 2 characters)"
                )

        if invalid_texts:
            raise EmbeddingServiceAPIError(
                {
                    "code": -32602,
                    "message": "Invalid input texts",
                    "details": invalid_texts,
                }
            )

    async def cmd(
        self,
        command: str,
        params: Optional[Dict[str, Any]] = None,
        base_url: Optional[str] = None,
        port: Optional[int] = None,
        validate_texts: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute a command via JSON-RPC protocol.

        Args:
            command: Command to execute (embed, models, health, help, config).
            params: Parameters for the command.
            base_url: Override base URL (not used with adapter).
            port: Override port (not used with adapter).
            validate_texts: When True, perform local validation for ``embed`` texts
                via ``_validate_texts`` before sending the request.
        """
        del base_url, port
        if not command:
            raise EmbeddingServiceAPIError(
                {"code": -32602, "message": "Command is required"}
            )

        # Local validation for embed texts (legacy fail-fast behavior).
        # High-level helpers (e.g. embed()) may disable this to rely entirely
        # on server-side error_policy semantics.
        if validate_texts and command == "embed" and params and "texts" in params:
            self._validate_texts(params["texts"])

        logger = logging.getLogger("EmbeddingServiceAsyncClient.cmd")

        try:
            logger.info("Executing command via adapter: %s, params=%s", command, params)
            result = await self._adapter_transport.execute_command_unified(  # type: ignore[attr-defined]
                command=command,
                params=params,
                use_cmd_endpoint=False,
                auto_poll=True,
            )

            if isinstance(result, Dict):
                mode = result.get("mode", "immediate")

                # If adapter completed the job (auto_poll=True), result is already available
                if mode == "queued" and result.get("status") == "completed":
                    nested_result = result.get("result")
                    if nested_result and isinstance(nested_result, Dict):
                        if "result" in nested_result:
                            return {"result": nested_result["result"]}
                        return {"result": nested_result}
                    return {"result": result.get("result", {})}

                if mode == "immediate":
                    return {"result": result.get("result", result)}

                if mode == "queued" and not result.get("status") == "completed":
                    job_id = (
                        result.get("job_id")
                        or result.get("result", {}).get("job_id")
                        or result.get("result", {}).get("data", {}).get("job_id")
                        or result.get("data", {}).get("job_id")
                    )
                    if job_id:
                        job_result = await self.wait_for_job(job_id, timeout=60.0)  # type: ignore[attr-defined]
                        if isinstance(job_result, Dict):
                            if "result" in job_result:
                                return {"result": job_result["result"]}
                            if "data" in job_result:
                                return {
                                    "result": {
                                        "success": True,
                                        "data": job_result["data"],
                                    }
                                }
                            return {"result": {"success": True, "data": job_result}}
                        return {"result": {"success": True, "data": job_result}}

            # Normalize adapter response to legacy format
            normalized = ResponseNormalizer.normalize_command_response(result)

            if "error" in normalized:
                raise EmbeddingServiceAPIError(normalized["error"])

            if "result" in normalized:
                result_data = normalized["result"]
                if isinstance(result_data, Dict) and (
                    result_data.get("success") is False or "error" in result_data
                ):
                    raise EmbeddingServiceAPIError(
                        result_data.get("error", result_data)
                    )

            return normalized
        except EmbeddingServiceAPIError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.error("Error in adapter cmd: %s", exc, exc_info=True)
            error_dict = ResponseNormalizer.extract_error_from_adapter(exc)
            raise EmbeddingServiceAPIError(
                error_dict.get("error", {"message": str(exc)})
            ) from exc

    async def embed(
        self,
        texts: List[str],
        *,
        model: Optional[str] = None,
        dimension: Optional[int] = None,
        error_policy: str = "continue",
        **extra_params: Any,
    ) -> Dict[str, Any]:
        """
        High-level helper for the ``embed`` command.

        See project documentation for full contract description.
        """
        params: Dict[str, Any] = {"texts": texts}
        if model is not None:
            params["model"] = model
        if dimension is not None:
            params["dimension"] = dimension
        if error_policy:
            params["error_policy"] = error_policy
        if extra_params:
            params.update(extra_params)

        raw_result = await self.cmd("embed", params=params, validate_texts=False)

        data: Optional[Dict[str, Any]] = None
        if "result" in raw_result and isinstance(raw_result["result"], Dict):
            res = raw_result["result"]
            if "data" in res and isinstance(res["data"], Dict):
                data = res["data"]
            elif "data" in res and isinstance(res["data"], list):
                data = {"results": res["data"]}

        if data is None:
            try:
                results = extract_embedding_data(raw_result)
                data = {"results": results}
            except ValueError:
                embeddings = extract_embeddings(raw_result)
                data = {"embeddings": embeddings}

        return data


__all__ = ["AsyncClientAPIMixin"]
