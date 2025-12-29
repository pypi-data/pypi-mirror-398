"""
Response parsing helpers for EmbeddingServiceAsyncClient.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from embed_client.response_parsers import (
    extract_bm25_tokens,
    extract_chunks,
    extract_embedding_data,
    extract_embeddings,
    extract_texts,
    extract_tokens,
)


class AsyncClientResponseMixin:
    """Mixin that provides response helper methods for async client."""

    def _format_error_response(
        self, error: str, lang: Optional[str] = None, text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format error response in a standard way."""
        response: Dict[str, Any] = {"error": f"Embedding service error: {error}"}
        if lang is not None:
            response["lang"] = lang
        if text is not None:
            response["text"] = text
        return response

    def extract_embeddings(self, result: Dict[str, Any]) -> List[List[float]]:
        """Extract embeddings from API response using shared response_parsers helper."""
        return extract_embeddings(result)

    def extract_embedding_data(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract full embedding data from API response using response_parsers."""
        return extract_embedding_data(result)

    def extract_texts(self, result: Dict[str, Any]) -> List[str]:
        """Extract original texts from API response using response_parsers."""
        return extract_texts(result)

    def extract_chunks(self, result: Dict[str, Any]) -> List[List[str]]:
        """Extract text chunks from API response using response_parsers."""
        return extract_chunks(result)

    def extract_tokens(self, result: Dict[str, Any]) -> List[List[str]]:
        """Extract tokens from API response using response_parsers."""
        return extract_tokens(result)

    def extract_bm25_tokens(self, result: Dict[str, Any]) -> List[List[str]]:
        """Extract BM25 tokens from API response using response_parsers."""
        return extract_bm25_tokens(result)


__all__ = ["AsyncClientResponseMixin"]
