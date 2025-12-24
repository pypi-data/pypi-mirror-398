"""
Response Parsers

This module provides functions to extract data from API responses.
These functions were extracted from EmbeddingServiceAsyncClient to reduce file size.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Any, Dict, List


def extract_embeddings(result: Dict[str, Any]) -> List[List[float]]:
    """
    Extract embeddings from API response, supporting both old and new formats.

    Args:
        result: API response dictionary

    Returns:
        List of embedding vectors (list of lists of floats)

    Raises:
        ValueError: If embeddings cannot be extracted from the response
    """
    # Handle direct embeddings field (old format compatibility)
    if "embeddings" in result:
        return result["embeddings"]

    # Handle result wrapper
    if "result" in result:
        res = result["result"]

        # Handle direct list in result (old format)
        if isinstance(res, list):
            return res

        if isinstance(res, dict):
            # Handle old format: result.embeddings
            if "embeddings" in res:
                return res["embeddings"]

            # Handle old format: result.data.embeddings
            if (
                "data" in res
                and isinstance(res["data"], dict)
                and "embeddings" in res["data"]
            ):
                return res["data"]["embeddings"]

            # Handle adapter format: result.data.results[].embedding
            if (
                "data" in res
                and isinstance(res["data"], dict)
                and "results" in res["data"]
            ):
                results = res["data"]["results"]
                if isinstance(results, list):
                    embeddings = []
                    for item in results:
                        if isinstance(item, dict) and "embedding" in item:
                            embeddings.append(item["embedding"])
                        else:
                            raise ValueError(
                                f"Invalid item format in adapter response: {item}"
                            )
                    return embeddings

            # Handle new format: result.data[].embedding
            if "data" in res and isinstance(res["data"], list):
                embeddings = []
                for item in res["data"]:
                    if isinstance(item, dict) and "embedding" in item:
                        embeddings.append(item["embedding"])
                    else:
                        raise ValueError(
                            f"Invalid item format in new API response: {item}"
                        )
                return embeddings

    raise ValueError(f"Cannot extract embeddings from response: {result}")


def extract_embedding_data(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract full embedding data from API response (new format only).

    Args:
        result: API response dictionary

    Returns:
        List of dictionaries with 'body', 'embedding', 'tokens', and 'bm25_tokens' fields

    Raises:
        ValueError: If data cannot be extracted or is in old format
    """
    if "result" in result and isinstance(result["result"], dict):
        res = result["result"]
        if "data" in res and isinstance(res["data"], dict) and "results" in res["data"]:
            # New format: result.data.results[]
            results = res["data"]["results"]
            if isinstance(results, list):
                # Validate that all items have required fields
                for i, item in enumerate(results):
                    if not isinstance(item, dict):
                        raise ValueError(f"Item {i} is not a dictionary: {item}")
                    if "body" not in item:
                        raise ValueError(f"Item {i} missing 'body' field: {item}")
                    if "embedding" not in item:
                        raise ValueError(f"Item {i} missing 'embedding' field: {item}")
                    if "tokens" not in item:
                        raise ValueError(f"Item {i} missing 'tokens' field: {item}")
                    if "bm25_tokens" not in item:
                        raise ValueError(
                            f"Item {i} missing 'bm25_tokens' field: {item}"
                        )

                return results

        # Legacy support for old format: result.data[]
        if "data" in res and isinstance(res["data"], list):
            # Validate that all items have required fields
            for i, item in enumerate(res["data"]):
                if not isinstance(item, dict):
                    raise ValueError(f"Item {i} is not a dictionary: {item}")
                if "body" not in item:
                    raise ValueError(f"Item {i} missing 'body' field: {item}")
                if "embedding" not in item:
                    raise ValueError(f"Item {i} missing 'embedding' field: {item}")
                # Old format had 'chunks' instead of 'tokens'
                if "chunks" not in item and "tokens" not in item:
                    raise ValueError(
                        f"Item {i} missing 'chunks' or 'tokens' field: {item}"
                    )

            return res["data"]

    raise ValueError(
        f"Cannot extract embedding data from response (new format required): {result}"
    )


def extract_texts(result: Dict[str, Any]) -> List[str]:
    """
    Extract original texts from API response (new format only).

    Args:
        result: API response dictionary

    Returns:
        List of original text strings

    Raises:
        ValueError: If texts cannot be extracted or is in old format
    """
    data = extract_embedding_data(result)
    return [item["body"] for item in data]


def extract_chunks(result: Dict[str, Any]) -> List[List[str]]:
    """
    Extract text chunks from API response (new format only).
    Note: This method now extracts 'tokens' instead of 'chunks' for compatibility.

    Args:
        result: API response dictionary

    Returns:
        List of token lists for each text

    Raises:
        ValueError: If chunks cannot be extracted or is in old format
    """
    data = extract_embedding_data(result)
    chunks = []
    for item in data:
        # New format uses 'tokens', old format used 'chunks'
        if "tokens" in item:
            chunks.append(item["tokens"])
        elif "chunks" in item:
            chunks.append(item["chunks"])
        else:
            raise ValueError(f"Item missing both 'tokens' and 'chunks' fields: {item}")
    return chunks


def extract_tokens(result: Dict[str, Any]) -> List[List[str]]:
    """
    Extract tokens from API response (new format only).

    Args:
        result: API response dictionary

    Returns:
        List of token lists for each text

    Raises:
        ValueError: If tokens cannot be extracted or is in old format
    """
    data = extract_embedding_data(result)
    return [item["tokens"] for item in data]


def extract_bm25_tokens(result: Dict[str, Any]) -> List[List[str]]:
    """
    Extract BM25 tokens from API response (new format only).

    Args:
        result: API response dictionary

    Returns:
        List of BM25 token lists for each text

    Raises:
        ValueError: If BM25 tokens cannot be extracted or is in old format
    """
    data = extract_embedding_data(result)
    return [item["bm25_tokens"] for item in data]
