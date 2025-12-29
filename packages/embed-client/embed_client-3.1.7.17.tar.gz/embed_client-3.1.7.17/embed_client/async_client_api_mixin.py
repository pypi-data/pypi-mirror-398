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
        timeout: Optional[float] = None,
        # Connection override parameters
        host: Optional[str] = None,
        port: Optional[int] = None,
        protocol: Optional[str] = None,
        token: Optional[str] = None,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        ca_cert_file: Optional[str] = None,
        crl_file: Optional[str] = None,
        **extra_params: Any,
    ) -> Dict[str, Any]:
        """
        High-level helper for the ``embed`` command.

        This method fully hides all intermediate status polling calls.
        If a job is queued, it automatically waits for completion (if timeout is specified).

        Returns a dictionary with the following structure:
            {
                "results": [
                    {
                        "body": str,           # Original text
                        "embedding": List[float],  # Vector embedding
                        "tokens": List[str],    # Tokenized text
                        "bm25_tokens": List[str]  # BM25 tokens for search
                    },
                    ...
                ],
                "embeddings": List[List[float]],  # Alternative format (legacy)
                "model": str,                   # Model name used
                "dimension": int,               # Embedding dimension
                "device": str                   # Device used
            }

        Args:
            texts: List of texts to vectorize.
            model: Optional model name.
            dimension: Optional expected vector dimension.
            error_policy: Error handling policy (default: "continue").
            timeout: Maximum time to wait for vectorization completion in seconds.
                    If None, return immediately without waiting for completion.
                    If 0, wait indefinitely (no timeout).
                    If > 0, wait up to specified seconds.
            host: Override server host (optional).
            port: Override server port (optional).
            protocol: Override protocol - "http", "https", or "mtls" (optional).
            token: Override authentication token (optional).
            cert_file: Override client certificate file path (optional).
            key_file: Override client key file path (optional).
            ca_cert_file: Override CA certificate file path (optional).
            crl_file: Override CRL file path (optional).
            **extra_params: Additional parameters to pass to the embed command.

        Returns:
            Dictionary with embeddings data:
            - If timeout is None: May contain job_id if queued, or embeddings if immediate.
            - If timeout is specified: Complete results with embeddings.

        Raises:
            EmbeddingServiceTimeoutError: If timeout > 0 and vectorization doesn't complete in time.
            EmbeddingServiceAPIError: If vectorization fails.
            EmbeddingServiceError: If request fails.

        See project documentation for full contract description.
        """
        # Create temporary client with overridden settings if any override parameters are provided
        client_to_use = self
        if any([host, port, protocol, token, cert_file, key_file, ca_cert_file, crl_file]):
            # Import here to avoid circular dependency
            from embed_client.async_client import EmbeddingServiceAsyncClient
            
            # Get current config
            current_config = self.config_dict if hasattr(self, 'config_dict') and self.config_dict else {}
            if hasattr(self, 'config') and self.config:
                current_config = self.config.get_all()
            
            # Create new config with overrides
            new_config = current_config.copy()
            if host:
                new_config.setdefault("server", {})["host"] = host
            if port:
                new_config.setdefault("server", {})["port"] = port
            if protocol:
                new_config["protocol"] = protocol
                if protocol in ("https", "mtls"):
                    new_config.setdefault("ssl", {})["enabled"] = True
                else:
                    new_config.setdefault("ssl", {})["enabled"] = False
            
            if token:
                new_config.setdefault("auth", {}).setdefault("api_key", {})["key"] = token
                new_config.setdefault("auth", {})["method"] = "api_key"
            
            if cert_file:
                new_config.setdefault("ssl", {})["cert_file"] = cert_file
                new_config.setdefault("auth", {}).setdefault("certificate", {})["cert_file"] = cert_file
            if key_file:
                new_config.setdefault("ssl", {})["key_file"] = key_file
                new_config.setdefault("auth", {}).setdefault("certificate", {})["key_file"] = key_file
            if ca_cert_file:
                new_config.setdefault("ssl", {})["ca_cert_file"] = ca_cert_file
                new_config.setdefault("auth", {}).setdefault("certificate", {})["ca_cert_file"] = ca_cert_file
            if crl_file:
                new_config.setdefault("ssl", {})["crl_file"] = crl_file
            
            if timeout is not None:
                new_config.setdefault("client", {})["timeout"] = timeout
            
            # Create temporary client
            client_to_use = EmbeddingServiceAsyncClient(config_dict=new_config)
            await client_to_use.__aenter__()
        
        try:
            params: Dict[str, Any] = {"texts": texts}
            if model is not None:
                params["model"] = model
            if dimension is not None:
                params["dimension"] = dimension
            if error_policy:
                params["error_policy"] = error_policy
            if extra_params:
                params.update(extra_params)

            # If timeout is specified, we need to handle queue waiting manually
            # This fully hides all intermediate status polling calls
            if timeout is not None:
                # Execute command without auto-polling to get job_id
                result = await client_to_use._adapter_transport.execute_command_unified(  # type: ignore[attr-defined]
                    command="embed",
                    params=params,
                    use_cmd_endpoint=False,
                    auto_poll=False,
                )

                # Check if command was queued
                if isinstance(result, Dict) and result.get("mode") == "queued":
                    job_id = (
                        result.get("job_id")
                        or result.get("result", {}).get("job_id")
                        or result.get("result", {}).get("data", {}).get("job_id")
                        or result.get("data", {}).get("job_id")
                    )

                    if job_id:
                        # Wait for job completion with specified timeout
                        # This fully hides all intermediate status polling calls
                        job_result = await client_to_use.wait_for_job(  # type: ignore[attr-defined]
                            job_id, timeout=timeout
                        )

                        # Extract embeddings from job result
                        if isinstance(job_result, Dict):
                            # Job result may contain data in different formats
                            if "data" in job_result:
                                data = job_result["data"]
                            elif "result" in job_result:
                                data = job_result["result"]
                            else:
                                data = job_result

                            # Normalize to expected format
                            if isinstance(data, Dict):
                                if "results" in data:
                                    return data
                                if "embeddings" in data:
                                    return data
                                # Try to extract embeddings from nested structure
                                if "data" in data:
                                    nested_data = data["data"]
                                    if isinstance(nested_data, Dict):
                                        if "results" in nested_data:
                                            return nested_data
                                        if "embeddings" in nested_data:
                                            return nested_data

                            # Fallback: try to extract using parsers
                            try:
                                wrapped = {"result": {"success": True, "data": data}}
                                results = extract_embedding_data(wrapped)
                                return {"results": results}
                            except ValueError:
                                try:
                                    wrapped = {"result": {"success": True, "data": data}}
                                    embeddings = extract_embeddings(wrapped)
                                    return {"embeddings": embeddings}
                                except ValueError:
                                    return data if isinstance(data, Dict) else {"results": []}

                            return job_result if isinstance(job_result, Dict) else {"results": []}
                        else:
                            return {"results": []}

                    # If queued but no job_id, process immediate result
                    raw_result = {"result": result.get("result", result)}
                else:
                    # Not queued, process immediate result
                    raw_result = {"result": result.get("result", result)}
            else:
                # No timeout specified - use default behavior
                # This fully hides all intermediate status polling calls
                raw_result = await client_to_use.cmd("embed", params=params, validate_texts=False)

            # Extract and normalize data
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
        finally:
            # Clean up temporary client if it was created
            if client_to_use is not self and hasattr(client_to_use, '__aexit__'):
                await client_to_use.__aexit__(None, None, None)


__all__ = ["AsyncClientAPIMixin"]
