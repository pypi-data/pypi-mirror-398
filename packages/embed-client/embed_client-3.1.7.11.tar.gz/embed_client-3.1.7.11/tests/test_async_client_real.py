"""
Real server integration tests for EmbeddingServiceAsyncClient.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
from embed_client.async_client import EmbeddingServiceAsyncClient, EmbeddingServiceAPIError
from test_async_client_real_fixtures import extract_vectors, is_service_available


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_health(real_client):
    """Test health check on real HTTP server."""
    if not await is_service_available("http"):
        pytest.skip("Real service on localhost:8001 is not available.")
    result = await real_client.health()
    assert "status" in result
    assert result["status"] in ("ok", "error")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_health_https(real_https_client):  # noqa: F811
    """Test health check on real HTTPS server."""
    if not await is_service_available("https"):
        pytest.skip("Real HTTPS service on localhost:8443 is not available.")
    result = await real_https_client.health()
    assert "status" in result
    assert result["status"] in ("ok", "error")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_health_mtls(real_mtls_client):  # noqa: F811
    """Test health check on real mTLS server."""
    if not await is_service_available("mtls"):
        pytest.skip("Real mTLS service on localhost:8001 is not available.")
    result = await real_mtls_client.health()
    assert "status" in result
    assert result["status"] in ("ok", "error")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_openapi(real_client):
    """Test OpenAPI schema retrieval on real HTTP server."""
    if not await is_service_available("http"):
        pytest.skip("Real service on localhost:8001 is not available.")
    result = await real_client.get_openapi_schema()
    assert "openapi" in result
    assert result["openapi"].startswith("3.")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_openapi_https(real_https_client):  # noqa: F811
    """Test OpenAPI schema retrieval on real HTTPS server."""
    if not await is_service_available("https"):
        pytest.skip("Real HTTPS service on localhost:8443 is not available.")
    result = await real_https_client.get_openapi_schema()
    assert "openapi" in result
    assert result["openapi"].startswith("3.")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_openapi_mtls(real_mtls_client):  # noqa: F811
    """Test OpenAPI schema retrieval on real mTLS server."""
    if not await is_service_available("mtls"):
        pytest.skip("Real mTLS service on localhost:8001 is not available.")
    result = await real_mtls_client.get_openapi_schema()
    assert "openapi" in result
    assert result["openapi"].startswith("3.")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_get_commands(real_client):
    """Test commands list retrieval on real HTTP server."""
    if not await is_service_available("http"):
        pytest.skip("Real service on localhost:8001 is not available.")
    result = await real_client.get_commands()
    assert isinstance(result, dict)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_get_commands_https(real_https_client):  # noqa: F811
    """Test commands list retrieval on real HTTPS server."""
    if not await is_service_available("https"):
        pytest.skip("Real HTTPS service on localhost:8443 is not available.")
    result = await real_https_client.get_commands()
    assert isinstance(result, dict)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_get_commands_mtls(real_mtls_client):  # noqa: F811
    """Test commands list retrieval on real mTLS server."""
    if not await is_service_available("mtls"):
        pytest.skip("Real mTLS service on localhost:8001 is not available.")
    result = await real_mtls_client.get_commands()
    assert isinstance(result, dict)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_cmd_help(real_client):
    """Test help command on real HTTP server."""
    if not await is_service_available("http"):
        pytest.skip("Real service on localhost:8001 is not available.")
    result = await real_client.cmd("help")
    assert isinstance(result, dict)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_cmd_help_https(real_https_client):  # noqa: F811
    """Test help command on real HTTPS server."""
    if not await is_service_available("https"):
        pytest.skip("Real HTTPS service on localhost:8443 is not available.")
    result = await real_https_client.cmd("help")
    assert isinstance(result, dict)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_cmd_help_mtls(real_mtls_client):  # noqa: F811
    """Test help command on real mTLS server."""
    if not await is_service_available("mtls"):
        pytest.skip("Real mTLS service on localhost:8001 is not available.")
    result = await real_mtls_client.cmd("help")
    assert isinstance(result, dict)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_embed_vector(real_client):
    """Test embedding vectorization on real HTTP server."""
    if not await is_service_available("http"):
        pytest.skip("Real service on localhost:8001 is not available.")
    texts = ["hello world", "test embedding"]
    params = {"texts": texts}
    result = await real_client.cmd("embed", params=params)
    vectors = extract_vectors(result)
    assert isinstance(vectors, list)
    assert len(vectors) == len(texts)
    assert all(isinstance(vec, list) for vec in vectors)
    assert all(isinstance(x, (float, int)) for vec in vectors for x in vec)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_embed_high_level_error_policy_continue(real_client):
    """High-level embed() should work against real HTTP server with error_policy=continue."""
    if not await is_service_available("http"):
        pytest.skip("Real service on localhost:8001 is not available.")

    texts = ["valid text", "   ", "!!!"]
    data = await real_client.embed(texts, error_policy="continue")

    # data should contain results aligned with input texts
    assert isinstance(data, dict)
    assert "results" in data
    results = data["results"]
    assert len(results) == len(texts)

    # First item is valid, others should surface per-item errors
    assert results[0]["error"] is None
    assert results[0]["embedding"] is not None

    # At least one of the invalid inputs must have an error object
    per_item_errors = [item["error"] for item in results[1:]]
    assert any(err is not None for err in per_item_errors)
    for err in per_item_errors:
        if err is not None:
            assert "code" in err
            assert "message" in err


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_embed_vector_https(real_https_client):  # noqa: F811
    """Test embedding vectorization on real HTTPS server."""
    if not await is_service_available("https"):
        pytest.skip("Real HTTPS service on localhost:8443 is not available.")
    texts = ["hello world", "test embedding"]
    params = {"texts": texts}
    result = await real_https_client.cmd("embed", params=params)
    vectors = extract_vectors(result)
    assert isinstance(vectors, list)
    assert len(vectors) == len(texts)
    assert all(isinstance(vec, list) for vec in vectors)
    assert all(isinstance(x, (float, int)) for vec in vectors for x in vec)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_embed_high_level_error_policy_continue_https(real_https_client):  # noqa: F811
    """High-level embed() should work against real HTTPS server with error_policy=continue."""
    if not await is_service_available("https"):
        pytest.skip("Real HTTPS service on localhost:8443 is not available.")

    texts = ["valid text", "   "]
    data = await real_https_client.embed(texts, error_policy="continue")

    assert isinstance(data, dict)
    assert "results" in data
    results = data["results"]
    assert len(results) == len(texts)

    # First item valid, second should surface per-item error
    assert results[0]["error"] is None
    assert results[0]["embedding"] is not None
    assert results[1]["embedding"] is None
    assert results[1]["error"] is not None
    assert "code" in results[1]["error"]
    assert "message" in results[1]["error"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_embed_vector_mtls(real_mtls_client):  # noqa: F811
    """Test embedding vectorization on real mTLS server."""
    if not await is_service_available("mtls"):
        pytest.skip("Real mTLS service on localhost:8001 is not available.")
    texts = ["hello world", "test embedding"]
    params = {"texts": texts}
    result = await real_mtls_client.cmd("embed", params=params)
    vectors = extract_vectors(result)
    assert isinstance(vectors, list)
    assert len(vectors) == len(texts)
    assert all(isinstance(vec, list) for vec in vectors)
    assert all(isinstance(x, (float, int)) for vec in vectors for x in vec)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_embed_high_level_error_policy_continue_mtls(real_mtls_client):  # noqa: F811
    """High-level embed() should work against real mTLS server with error_policy=continue."""
    if not await is_service_available("mtls"):
        pytest.skip("Real mTLS service on localhost:8001 is not available.")

    texts = ["valid text", "   "]
    data = await real_mtls_client.embed(texts, error_policy="continue")

    assert isinstance(data, dict)
    assert "results" in data
    results = data["results"]
    assert len(results) == len(texts)

    assert results[0]["error"] is None
    assert results[0]["embedding"] is not None
    assert results[1]["embedding"] is None
    assert results[1]["error"] is not None
    assert "code" in results[1]["error"]
    assert "message" in results[1]["error"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_embed_empty_texts(real_client):
    """Test embedding with empty texts list on real HTTP server."""
    if not await is_service_available("http"):
        pytest.skip("Real service on localhost:8001 is not available.")
    with pytest.raises(EmbeddingServiceAPIError) as excinfo:
        await real_client.cmd("embed", params={"texts": []})
    assert "Empty texts list provided" in str(excinfo.value)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_cmd_invalid_command(real_client):
    """Test invalid command on real HTTP server."""
    if not await is_service_available("http"):
        pytest.skip("Real service on localhost:8001 is not available.")
    with pytest.raises(EmbeddingServiceAPIError):
        await real_client.cmd("not_a_command")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_invalid_endpoint():
    """Test invalid endpoint handling (legacy test - may not work with adapter)."""
    if not await is_service_available("http"):
        pytest.skip("Real service on localhost:8001 is not available.")
    # This test uses internal _session which may not exist with adapter transport
    pytest.skip("Legacy test using internal _session; adapter handles transport")


@pytest.mark.asyncio
async def test_explicit_close_real():
    """Test explicit client close."""
    client = EmbeddingServiceAsyncClient(base_url="http://localhost", port=8001)
    await client.__aenter__()
    await client.close()
    await client.close()  # Should not raise
