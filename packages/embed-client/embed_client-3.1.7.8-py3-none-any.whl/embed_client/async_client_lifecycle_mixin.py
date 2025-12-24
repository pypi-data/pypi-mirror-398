"""
Lifecycle management mixin for EmbeddingServiceAsyncClient.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

from typing import Any, Optional, Type

from embed_client.exceptions import EmbeddingServiceError


class AsyncClientLifecycleMixin:
    """Mixin that provides async context manager and explicit close support."""

    async def __aenter__(self) -> Any:
        """Open underlying adapter transport when entering async context."""
        try:
            await self._adapter_transport.__aenter__()  # type: ignore[attr-defined]
            return self
        except Exception as exc:  # noqa: BLE001
            raise EmbeddingServiceError(f"Failed to create transport: {exc}") from exc

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Any,
    ) -> None:
        """Close underlying adapter transport when leaving async context."""
        if getattr(self, "_adapter_transport", None) is None:
            return
        try:
            await self._adapter_transport.__aexit__(exc_type, exc, tb)  # type: ignore[attr-defined]
        except Exception as exc_inner:  # noqa: BLE001
            raise EmbeddingServiceError(
                f"Failed to close adapter transport: {exc_inner}"
            ) from exc_inner

    async def close(self) -> None:
        """
        Close the underlying adapter transport explicitly.

        This method allows the user to manually close the transport used by the client.
        It is safe to call multiple times; if the transport is already closed or was
        never opened, nothing happens.
        """
        if getattr(self, "_adapter_transport", None) is None:
            return
        try:
            await self._adapter_transport.close()  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001
            raise EmbeddingServiceError(
                f"Failed to close adapter transport: {exc}"
            ) from exc


__all__ = ["AsyncClientLifecycleMixin"]
