"""
Stress tests for EmbeddingServiceAsyncClient with support for new API format.

These tests verify the client's behavior under heavy load with parallel processing
of large text batches. Supports both old and new API response formats.
"""

import pytest
import pytest_asyncio
import asyncio
import time
import random
from typing import List, Dict, Any, Optional
from embed_client.async_client import (
    EmbeddingServiceAsyncClient,
    EmbeddingServiceAPIError,
    EmbeddingServiceError,
    EmbeddingServiceConnectionError,
    EmbeddingServiceTimeoutError,
    EmbeddingServiceHTTPError,
    EmbeddingServiceJSONError,
    EmbeddingServiceConfigError,
)

BASE_URL = "http://localhost"
PORT = 8001

# Constants for retry logic
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds
MAX_CONCURRENT_TASKS = 100  # Limit concurrent tasks to prevent system overload


def generate_test_texts(count: int) -> List[str]:
    """Generate test texts with unique content."""
    return [f"Test text {i} for stress testing" for i in range(count)]


def validate_result_data(data: Any) -> None:
    """Validate result data format, supporting both old and new formats."""
    # Support both old and new formats
    if isinstance(data, dict) and "embeddings" in data:
        # Old format: data.embeddings
        assert isinstance(data["embeddings"], list), f"'embeddings' is not a list: {data}"
    elif isinstance(data, list):
        # New format: data[].embedding
        for i, item in enumerate(data):
            assert isinstance(item, dict), f"Item {i} is not a dict: {item}"
            assert "body" in item, f"Item {i} missing 'body': {item}"
            assert "embedding" in item, f"Item {i} missing 'embedding': {item}"
            assert "chunks" in item, f"Item {i} missing 'chunks': {item}"
            assert isinstance(item["embedding"], list), f"Item {i} embedding is not a list: {item}"
    else:
        raise AssertionError(f"Unexpected data format: {data}")


async def process_with_retry(
    client: EmbeddingServiceAsyncClient,
    texts: List[str],
    max_retries: int = MAX_RETRIES,
    retry_delay: float = RETRY_DELAY,
) -> Dict[str, Any]:
    """
    Process texts with retry logic for handling runtime exceptions.

    Args:
        client: EmbeddingServiceAsyncClient instance
        texts: List of texts to process
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds

    Returns:
        Dict containing the result or error information
    """
    for attempt in range(max_retries):
        try:
            return await client.cmd("embed", params={"texts": texts})
        except Exception as e:
            if attempt == max_retries - 1:  # Last attempt
                return {
                    "error": f"Failed after {max_retries} attempts: {str(e)}",
                    "exception": str(e),
                    "attempts": attempt + 1,
                }
            await asyncio.sleep(retry_delay * (attempt + 1))  # Exponential backoff


async def process_batch(
    client: EmbeddingServiceAsyncClient,
    texts: List[str],
    batch_size: int,
    max_concurrent: int = MAX_CONCURRENT_TASKS,
) -> List[Dict[str, Any]]:
    """
    Process a batch of texts in parallel with controlled concurrency.

    Args:
        client: EmbeddingServiceAsyncClient instance
        texts: List of texts to process
        batch_size: Size of each batch
        max_concurrent: Maximum number of concurrent tasks

    Returns:
        List of results for each batch
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_with_semaphore(batch: List[str]) -> Dict[str, Any]:
        async with semaphore:
            return await process_with_retry(client, batch)

    tasks = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        task = asyncio.create_task(process_with_semaphore(batch))
        tasks.append(task)

    return await asyncio.gather(*tasks, return_exceptions=True)


@pytest_asyncio.fixture
async def stress_client():
    """Create a client instance for stress testing."""
    async with EmbeddingServiceAsyncClient(base_url=BASE_URL, port=PORT) as client:
        yield client


@pytest.mark.asyncio
@pytest.mark.stress
async def test_parallel_processing_new_format(stress_client):
    """Test parallel processing of 10K texts with new API format support."""
    total_texts = 10_000
    batch_size = 100  # Process 100 texts at a time
    texts = generate_test_texts(total_texts)

    start_time = time.time()
    results = await process_batch(stress_client, texts, batch_size)
    end_time = time.time()

    # Verify results
    success_count = 0
    error_count = 0
    exception_count = 0

    for result in results:
        if isinstance(result, Exception):
            exception_count += 1
            continue
        # Check for error/result
        assert ("error" in result) or ("result" in result), f"Neither 'error' nor 'result' in response: {result}"
        if "error" in result:
            error_count += 1
            if "exception" in result:
                print(f"Error with exception: {result['error']}")
        elif "result" in result:
            res = result["result"]
            assert isinstance(res, dict), f"result is not a dict: {res}"
            if "success" in res and res["success"] is False:
                error_count += 1
                if "error" in res:
                    print(f"Error in result: {res['error']}")
            else:
                success_count += 1
                assert "data" in res, f"No 'data' in result: {res}"
                data = res["data"]
                validate_result_data(data)

    # Calculate statistics
    total_time = end_time - start_time
    texts_per_second = total_texts / total_time

    print(f"\nStress Test Results (New Format):")
    print(f"Total texts processed: {total_texts}")
    print(f"Successful batches: {success_count}")
    print(f"Failed batches: {error_count}")
    print(f"Exception batches: {exception_count}")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Processing speed: {texts_per_second:.2f} texts/second")

    # Assertions
    assert success_count > 0, "No successful batches processed"
    assert total_time > 0, "Invalid processing time"
    # Allow some errors and exceptions under stress
    assert error_count + exception_count < total_texts * 0.1, "Too many errors/exceptions"


@pytest.mark.asyncio
@pytest.mark.stress
async def test_concurrent_connections_new_format(stress_client):
    """Test multiple concurrent connections with new API format support."""
    total_connections = 50
    texts_per_connection = 200
    texts = generate_test_texts(texts_per_connection)

    async def single_connection() -> Dict[str, Any]:
        try:
            async with EmbeddingServiceAsyncClient(base_url=BASE_URL, port=PORT) as client:
                return await process_with_retry(client, texts)
        except Exception as e:
            return {"error": f"Connection failed: {str(e)}", "exception": str(e)}

    start_time = time.time()
    tasks = [asyncio.create_task(single_connection()) for _ in range(total_connections)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    end_time = time.time()

    # Verify results
    success_count = 0
    error_count = 0
    exception_count = 0

    for result in results:
        if isinstance(result, Exception):
            exception_count += 1
            continue
        # Check for error/result
        assert ("error" in result) or ("result" in result), f"Neither 'error' nor 'result' in response: {result}"
        if "error" in result:
            error_count += 1
            if "exception" in result:
                print(f"Error with exception: {result['error']}")
        elif "result" in result:
            res = result["result"]
            assert isinstance(res, dict), f"result is not a dict: {res}"
            if "success" in res and res["success"] is False:
                error_count += 1
                if "error" in res:
                    print(f"Error in result: {res['error']}")
            else:
                success_count += 1
                assert "data" in res, f"No 'data' in result: {res}"
                data = res["data"]
                validate_result_data(data)

    # Calculate statistics
    total_time = end_time - start_time
    total_texts = total_connections * texts_per_connection
    texts_per_second = total_texts / total_time

    print(f"\nConcurrent Connections Test Results (New Format):")
    print(f"Total connections: {total_connections}")
    print(f"Texts per connection: {texts_per_connection}")
    print(f"Total texts processed: {total_texts}")
    print(f"Successful connections: {success_count}")
    print(f"Failed connections: {error_count}")
    print(f"Exception connections: {exception_count}")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Processing speed: {texts_per_second:.2f} texts/second")

    # Assertions
    assert success_count > 0, "No successful connections"
    assert total_time > 0, "Invalid processing time"
    # Allow some errors and exceptions under stress
    assert error_count + exception_count < total_connections * 0.2, "Too many errors/exceptions"


@pytest.mark.asyncio
@pytest.mark.stress
async def test_new_format_extraction():
    """Test extraction methods with new format data."""
    async with EmbeddingServiceAsyncClient(base_url=BASE_URL, port=PORT) as client:
        # Mock new format response
        new_format_result = {
            "result": {
                "success": True,
                "data": [
                    {
                        "body": "test text 1",
                        "embedding": [0.1, 0.2, 0.3],
                        "chunks": ["test", "text", "1"],
                    },
                    {
                        "body": "test text 2",
                        "embedding": [0.4, 0.5, 0.6],
                        "chunks": ["test", "text", "2"],
                    },
                ],
            }
        }

        # Test extraction methods
        embeddings = client.extract_embeddings(new_format_result)
        assert embeddings == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

        embedding_data = client.extract_embedding_data(new_format_result)
        assert len(embedding_data) == 2
        assert embedding_data[0]["body"] == "test text 1"
        assert embedding_data[0]["embedding"] == [0.1, 0.2, 0.3]
        assert embedding_data[0]["chunks"] == ["test", "text", "1"]

        texts = client.extract_texts(new_format_result)
        assert texts == ["test text 1", "test text 2"]

        chunks = client.extract_chunks(new_format_result)
        assert chunks == [["test", "text", "1"], ["test", "text", "2"]]


@pytest.mark.asyncio
@pytest.mark.stress
async def test_backward_compatibility():
    """Test that old format responses still work."""
    async with EmbeddingServiceAsyncClient(base_url=BASE_URL, port=PORT) as client:
        # Mock old format response
        old_format_result = {
            "result": {
                "success": True,
                "data": {"embeddings": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]},
            }
        }

        # Test extraction methods
        embeddings = client.extract_embeddings(old_format_result)
        assert embeddings == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

        # Test validation
        validate_result_data(old_format_result["result"]["data"])

        # New format methods should fail gracefully
        try:
            client.extract_embedding_data(old_format_result)
            assert False, "Should have raised ValueError for old format"
        except ValueError as e:
            assert "new format required" in str(e)
