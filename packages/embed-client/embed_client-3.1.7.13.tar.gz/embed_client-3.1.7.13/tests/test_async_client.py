import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from embed_client.async_client import (
    EmbeddingServiceAsyncClient,
    EmbeddingServiceAPIError,
    EmbeddingServiceHTTPError,
    EmbeddingServiceError,
    EmbeddingServiceConnectionError,
    EmbeddingServiceConfigError,
    EmbeddingServiceTimeoutError,
    EmbeddingServiceJSONError,
)
import aiohttp
import asyncio
import json
import sys
import types

# NOTE:
# These tests were originally written for the legacy aiohttp-based transport
# that used ``client._session`` and direct HTTP calls. The current
# ``EmbeddingServiceAsyncClient`` implementation has been refactored to use
# the mcp-proxy-adapter transport exclusively and no longer exposes
# ``_session`` or performs raw aiohttp calls.
# The adapter-level behaviour (JSON-RPC, error handling, timeouts, etc.)
# is now covered by:
#   - tests/test_adapter_phase1.py
#   - tests/test_adapter_phase2.py
#   - tests/test_all_security_modes.py
#   - tests/test_security_examples.py
#   - tests/test_async_client_real.py
#   - tests/test_embed_contract_8001.py
# To avoid maintaining a large set of obsolete transport-level mocks against
# internals that no longer exist, we skip this legacy module in the default
# test run.
pytestmark = pytest.mark.skip(
    reason="Legacy aiohttp-based async client tests; behaviour now covered by adapter/real-server tests"
)

BASE_URL = "http://testserver"
PORT = 1234


class MockAiohttpResponse:
    def __init__(
        self,
        json_data=None,
        status=200,
        raise_http=None,
        text_data=None,
        raise_json=None,
    ):
        self._json = json_data
        self._status = status
        self._raise_http = raise_http
        self._text = text_data
        self._raise_json = raise_json

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def json(self):
        if self._raise_json:
            raise self._raise_json
        if self._json is not None:
            return self._json
        raise ValueError("No JSON")

    async def text(self):
        return self._text or ""

    def raise_for_status(self):
        if self._raise_http:
            raise self._raise_http
        return None

    @property
    def status(self):
        return self._status


@pytest_asyncio.fixture
async def client():
    async with EmbeddingServiceAsyncClient(base_url=BASE_URL, port=PORT) as c:
        yield c


def make_url(path):
    return f"{BASE_URL}:{PORT}{path}"


@pytest.mark.asyncio
async def test_health(client):
    await client.__aenter__()
    with patch.object(client._session, "get", return_value=MockAiohttpResponse({"status": "ok"})) as mock_get:
        result = await client.health()
        assert result == {"status": "ok"}
        mock_get.assert_called_with(make_url("/health"), headers={}, timeout=client.timeout)
    await client.__aexit__(None, None, None)


@pytest.mark.asyncio
async def test_get_openapi_schema(client):
    await client.__aenter__()
    with patch.object(client._session, "get", return_value=MockAiohttpResponse({"openapi": "3.0.2"})) as mock_get:
        result = await client.get_openapi_schema()
        assert result == {"openapi": "3.0.2"}
        mock_get.assert_called_with(make_url("/openapi.json"), headers={}, timeout=client.timeout)
    await client.__aexit__(None, None, None)


@pytest.mark.asyncio
async def test_get_commands(client):
    await client.__aenter__()
    with patch.object(
        client._session,
        "get",
        return_value=MockAiohttpResponse({"commands": ["embed", "models"]}),
    ) as mock_get:
        result = await client.get_commands()
        assert result == {"commands": ["embed", "models"]}
        mock_get.assert_called_with(make_url("/api/commands"), headers={}, timeout=client.timeout)
    await client.__aexit__(None, None, None)


@pytest.mark.asyncio
async def test_cmd(client):
    await client.__aenter__()
    with patch.object(client._session, "post", return_value=MockAiohttpResponse({"result": "ok"})) as mock_post:
        result = await client.cmd("embed", params={"texts": ["abc"]})
        assert result == {"result": "ok"}
        mock_post.assert_called_with(
            make_url("/cmd"),
            json={"command": "embed", "params": {"texts": ["abc"]}},
            headers={},
            timeout=client.timeout,
        )
    await client.__aexit__(None, None, None)


@pytest.mark.asyncio
async def test_embed_high_level_uses_continue_and_returns_data(monkeypatch):
    """High-level embed helper should send error_policy=continue and return data section."""
    client = EmbeddingServiceAsyncClient(base_url="http://test", port=8001)

    called: Dict[str, Any] = {}

    async def fake_cmd(command, params=None, base_url=None, port=None, validate_texts=True):
        called["command"] = command
        called["params"] = params
        called["validate_texts"] = validate_texts
        return {
            "result": {
                "success": True,
                "data": {
                    "embeddings": [[0.1], [0.2]],
                    "results": [
                        {
                            "body": "text1",
                            "embedding": [0.1],
                            "tokens": ["text1"],
                            "bm25_tokens": ["text1"],
                            "error": None,
                        },
                        {
                            "body": "text2",
                            "embedding": [0.2],
                            "tokens": ["text2"],
                            "bm25_tokens": ["text2"],
                            "error": None,
                        },
                    ],
                    "model": "all-MiniLM-L6-v2",
                    "dimension": 1,
                },
            }
        }

    monkeypatch.setattr(client, "cmd", fake_cmd)

    texts = ["text1", "text2"]
    data = await client.embed(texts, model="all-MiniLM-L6-v2", dimension=1)

    # Validate parameters passed to cmd()
    assert called["command"] == "embed"
    assert called["params"]["texts"] == texts
    assert called["params"]["model"] == "all-MiniLM-L6-v2"
    assert called["params"]["dimension"] == 1
    assert called["params"]["error_policy"] == "continue"
    assert called["validate_texts"] is False

    # Validate returned data section
    assert data["model"] == "all-MiniLM-L6-v2"
    assert data["dimension"] == 1
    assert len(data["embeddings"]) == 2
    assert len(data["results"]) == 2
    assert data["results"][0]["body"] == "text1"


@pytest.mark.asyncio
async def test_init_requires_base_url_and_port(monkeypatch):
    # Сохраняем и очищаем переменные окружения
    monkeypatch.delenv("EMBEDDING_SERVICE_BASE_URL", raising=False)
    monkeypatch.delenv("EMBEDDING_SERVICE_PORT", raising=False)
    # Если не передано ничего и нет переменных окружения, будет дефолт
    client = EmbeddingServiceAsyncClient()
    assert client.base_url == "http://localhost"
    assert client.port == 8001
    # Если явно передан base_url и port
    client2 = EmbeddingServiceAsyncClient(base_url="http://test", port=1234)
    assert client2.base_url == "http://test"
    assert client2.port == 1234


@pytest.mark.asyncio
async def test_init_config_errors():
    """Test configuration validation in constructor."""
    # Test invalid base_url
    with pytest.raises(EmbeddingServiceConfigError) as excinfo:
        EmbeddingServiceAsyncClient(base_url="invalid_url", port=8001)
    assert "base_url must start with http://" in str(excinfo.value)

    # Test invalid port
    with pytest.raises(EmbeddingServiceConfigError) as excinfo:
        EmbeddingServiceAsyncClient(base_url="http://localhost", port=-1)
    assert "port must be a valid integer" in str(excinfo.value)

    # Test invalid port type
    with pytest.raises(EmbeddingServiceConfigError) as excinfo:
        EmbeddingServiceAsyncClient(base_url="http://localhost", port="invalid")
    assert "port must be a valid integer" in str(excinfo.value)

    # Test invalid timeout
    with pytest.raises(EmbeddingServiceConfigError) as excinfo:
        EmbeddingServiceAsyncClient(base_url="http://localhost", port=8001, timeout=-1)
    assert "timeout must be positive" in str(excinfo.value)


@pytest.mark.asyncio
async def test_cmd_empty_command(client):
    with pytest.raises(EmbeddingServiceAPIError) as excinfo:
        await client.cmd("")
    assert "Command is required" in str(excinfo.value)


@pytest.mark.asyncio
async def test_cmd_connection_error(client):
    with patch.object(
        client._session,
        "post",
        side_effect=aiohttp.ClientConnectionError("Connection failed"),
    ):
        with pytest.raises(EmbeddingServiceConnectionError) as excinfo:
            await client.cmd("embed", params={"texts": ["abc"]})
        assert "Connection error" in str(excinfo.value)


@pytest.mark.asyncio
async def test_cmd_timeout_error(client):
    with patch.object(client._session, "post", side_effect=asyncio.TimeoutError("Timeout")):
        with pytest.raises(EmbeddingServiceTimeoutError) as excinfo:
            await client.cmd("embed", params={"texts": ["abc"]})
        assert "Request timeout" in str(excinfo.value)


@pytest.mark.asyncio
async def test_cmd_server_timeout_error(client):
    with patch.object(
        client._session,
        "post",
        side_effect=aiohttp.ServerTimeoutError("Server timeout"),
    ):
        with pytest.raises(EmbeddingServiceTimeoutError) as excinfo:
            await client.cmd("embed", params={"texts": ["abc"]})
        assert "Server timeout" in str(excinfo.value)


@pytest.mark.asyncio
async def test_cmd_ssl_error(client):
    # Use a simple connection error to simulate SSL issues
    with patch.object(
        client._session,
        "post",
        side_effect=aiohttp.ClientConnectionError("SSL connection error"),
    ):
        with pytest.raises(EmbeddingServiceConnectionError) as excinfo:
            await client.cmd("embed", params={"texts": ["abc"]})
        assert "Connection error" in str(excinfo.value)


@pytest.mark.asyncio
async def test_cmd_os_error(client):
    with patch.object(client._session, "post", side_effect=aiohttp.ClientOSError("OS error")):
        with pytest.raises(EmbeddingServiceConnectionError) as excinfo:
            await client.cmd("embed", params={"texts": ["abc"]})
        assert "OS error" in str(excinfo.value)


@pytest.mark.asyncio
async def test_cmd_json_decode_error(client):
    mock_response = MockAiohttpResponse(
        raise_json=json.JSONDecodeError("Invalid JSON", "doc", 0),
        text_data="<html>error</html>",
    )
    with patch.object(client._session, "post", return_value=mock_response):
        with pytest.raises(EmbeddingServiceJSONError) as excinfo:
            await client.cmd("embed", params={"texts": ["abc"]})
        assert "Invalid JSON response" in str(excinfo.value)


@pytest.mark.asyncio
async def test_cmd_unicode_decode_error(client):
    mock_response = MockAiohttpResponse(raise_json=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid"))
    with patch.object(client._session, "post", return_value=mock_response):
        with pytest.raises(EmbeddingServiceJSONError) as excinfo:
            await client.cmd("embed", params={"texts": ["abc"]})
        assert "Invalid JSON response" in str(excinfo.value)


@pytest.mark.asyncio
async def test_cmd_http_error(client):
    with patch.object(
        client._session,
        "post",
        side_effect=aiohttp.ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=500,
            message="Internal Server Error",
        ),
    ):
        with pytest.raises(EmbeddingServiceHTTPError) as excinfo:
            await client.cmd("embed", params={"texts": ["abc"]})
        assert "HTTP 500" in str(excinfo.value)


@pytest.mark.asyncio
async def test_cmd_api_error(client):
    mock_response = MockAiohttpResponse(
        json_data={
            "result": {
                "success": False,
                "error": {"code": 123, "message": "Invalid command"},
            }
        }
    )
    with patch.object(client._session, "post", return_value=mock_response):
        with pytest.raises(EmbeddingServiceAPIError) as excinfo:
            await client.cmd("invalid_command")
        assert "Invalid command" in str(excinfo.value)


@pytest.mark.asyncio
async def test_cmd_with_lang_and_text(client):
    mock_response = MockAiohttpResponse(
        json_data={
            "result": {
                "success": False,
                "error": {"code": 123, "message": "Invalid text"},
            }
        }
    )
    with patch.object(client._session, "post", return_value=mock_response):
        with pytest.raises(EmbeddingServiceAPIError) as excinfo:
            await client.cmd("embed", params={"texts": ["test"], "lang": "en", "text": "test text"})
        assert "Invalid text" in str(excinfo.value)


@pytest.mark.asyncio
async def test_cmd_success(client):
    mock_response = MockAiohttpResponse(json_data={"result": [[1.0, 2.0, 3.0]]})
    with patch.object(client._session, "post", return_value=mock_response):
        result = await client.cmd("embed", params={"texts": ["test"]})
        assert "result" in result
        assert result["result"] == [[1.0, 2.0, 3.0]]


# Некорректные параметры: не-строка в texts
@pytest.mark.asyncio
async def test_embed_non_string_text(client):
    """Test validation of non-string values in texts list."""
    with pytest.raises(EmbeddingServiceAPIError) as excinfo:
        await client.cmd("embed", params={"texts": [123, "ok"]})
    assert "Invalid input texts" in str(excinfo.value)
    assert "Text at index 0 is not a string" in str(excinfo.value)


# Некорректные параметры: невалидный params
@pytest.mark.asyncio
async def test_embed_invalid_params_type(client):
    mock_response = MockAiohttpResponse(
        json_data={
            "result": {
                "success": False,
                "error": {"code": 422, "message": "Invalid params"},
            }
        }
    )
    with patch.object(client._session, "post", return_value=mock_response):
        with pytest.raises(EmbeddingServiceAPIError):
            await client.cmd("embed", params="not_a_dict")


# Не-JSON ответ
@pytest.mark.asyncio
async def test_non_json_response(client):
    class BadResponse(MockAiohttpResponse):
        async def json(self):
            raise ValueError("Not a JSON")

    with patch.object(
        client._session,
        "post",
        return_value=BadResponse(text_data="<html>error</html>"),
    ) as mock_post:
        with pytest.raises(EmbeddingServiceJSONError):
            await client.cmd("embed", params={"texts": ["abc"]})


# 500 ошибка сервера
@pytest.mark.asyncio
async def test_server_500_error(client):
    from aiohttp import ClientResponseError

    err = ClientResponseError(request_info=None, history=None, status=500, message="Internal Server Error")
    with patch.object(
        client._session,
        "post",
        return_value=MockAiohttpResponse(raise_http=err, status=500),
    ) as mock_post:
        with pytest.raises(EmbeddingServiceHTTPError):
            await client.cmd("embed", params={"texts": ["abc"]})


# embed без params
@pytest.mark.asyncio
async def test_embed_no_params(client):
    mock_response = MockAiohttpResponse(
        json_data={
            "result": {
                "success": False,
                "error": {"code": 422, "message": "Missing params"},
            }
        }
    )
    with patch.object(client._session, "post", return_value=mock_response):
        with pytest.raises(EmbeddingServiceAPIError):
            await client.cmd("embed")


# Вектор не той размерности (например, сервер вернул 2D массив, а ожидали 3D)
@pytest.mark.asyncio
async def test_embed_wrong_vector_shape(client):
    # Ожидаем список списков, но сервер вернул список
    with patch.object(
        client._session,
        "post",
        return_value=MockAiohttpResponse({"embeddings": [1.0, 2.0, 3.0]}),
    ) as mock_post:
        result = await client.cmd("embed", params={"texts": ["abc"]})
        vectors = result["embeddings"]
        assert isinstance(vectors, list)
        # Проверяем, что каждый элемент — список (будет False, тест покажет ошибку)
        assert all(isinstance(vec, list) for vec in vectors) is False


# Покрытие: except EmbeddingServiceHTTPError
@pytest.mark.asyncio
async def test_health_http_error(client):
    with patch.object(client._session, "get", side_effect=EmbeddingServiceHTTPError(500, "fail")):
        with pytest.raises(EmbeddingServiceHTTPError):
            await client.health()


# Покрытие: except EmbeddingServiceConnectionError
@pytest.mark.asyncio
async def test_health_connection_error(client):
    with patch.object(client._session, "get", side_effect=EmbeddingServiceConnectionError("fail")):
        with pytest.raises(EmbeddingServiceConnectionError):
            await client.health()


# Покрытие: except Exception (ValueError)
@pytest.mark.asyncio
async def test_health_unexpected_error(client):
    with patch.object(client._session, "get", side_effect=ValueError("fail")):
        with pytest.raises(EmbeddingServiceError):
            await client.health()


@pytest.mark.asyncio
async def test_health_timeout_error(client):
    with patch.object(client._session, "get", side_effect=asyncio.TimeoutError("Timeout")):
        with pytest.raises(EmbeddingServiceTimeoutError):
            await client.health()


@pytest.mark.asyncio
async def test_health_json_error(client):
    mock_response = MockAiohttpResponse(raise_json=json.JSONDecodeError("Invalid JSON", "doc", 0))
    with patch.object(client._session, "get", return_value=mock_response):
        with pytest.raises(EmbeddingServiceJSONError):
            await client.health()


@pytest.mark.asyncio
async def test_health_ssl_error(client):
    # Use a simple connection error to simulate SSL issues
    with patch.object(
        client._session,
        "get",
        side_effect=aiohttp.ClientConnectionError("SSL connection error"),
    ):
        with pytest.raises(EmbeddingServiceConnectionError):
            await client.health()


# Аналогично для get_openapi_schema
@pytest.mark.asyncio
async def test_get_openapi_schema_http_error(client):
    with patch.object(client._session, "get", side_effect=EmbeddingServiceHTTPError(500, "fail")):
        with pytest.raises(EmbeddingServiceHTTPError):
            await client.get_openapi_schema()


@pytest.mark.asyncio
async def test_get_openapi_schema_connection_error(client):
    with patch.object(client._session, "get", side_effect=EmbeddingServiceConnectionError("fail")):
        with pytest.raises(EmbeddingServiceConnectionError):
            await client.get_openapi_schema()


@pytest.mark.asyncio
async def test_get_openapi_schema_unexpected_error(client):
    with patch.object(client._session, "get", side_effect=ValueError("fail")):
        with pytest.raises(EmbeddingServiceError):
            await client.get_openapi_schema()


@pytest.mark.asyncio
async def test_get_openapi_schema_timeout_error(client):
    with patch.object(client._session, "get", side_effect=asyncio.TimeoutError("Timeout")):
        with pytest.raises(EmbeddingServiceTimeoutError):
            await client.get_openapi_schema()


@pytest.mark.asyncio
async def test_get_openapi_schema_json_error(client):
    mock_response = MockAiohttpResponse(raise_json=json.JSONDecodeError("Invalid JSON", "doc", 0))
    with patch.object(client._session, "get", return_value=mock_response):
        with pytest.raises(EmbeddingServiceJSONError):
            await client.get_openapi_schema()


# Аналогично для get_commands
@pytest.mark.asyncio
async def test_get_commands_http_error(client):
    with patch.object(client._session, "get", side_effect=EmbeddingServiceHTTPError(500, "fail")):
        with pytest.raises(EmbeddingServiceHTTPError):
            await client.get_commands()


@pytest.mark.asyncio
async def test_get_commands_connection_error(client):
    with patch.object(client._session, "get", side_effect=EmbeddingServiceConnectionError("fail")):
        with pytest.raises(EmbeddingServiceConnectionError):
            await client.get_commands()


@pytest.mark.asyncio
async def test_get_commands_unexpected_error(client):
    with patch.object(client._session, "get", side_effect=ValueError("fail")):
        with pytest.raises(EmbeddingServiceError):
            await client.get_commands()


@pytest.mark.asyncio
async def test_get_commands_timeout_error(client):
    with patch.object(client._session, "get", side_effect=asyncio.TimeoutError("Timeout")):
        with pytest.raises(EmbeddingServiceTimeoutError):
            await client.get_commands()


@pytest.mark.asyncio
async def test_get_commands_json_error(client):
    mock_response = MockAiohttpResponse(raise_json=json.JSONDecodeError("Invalid JSON", "doc", 0))
    with patch.object(client._session, "get", return_value=mock_response):
        with pytest.raises(EmbeddingServiceJSONError):
            await client.get_commands()


# Покрытие: _raise_for_status - ClientResponseError
@pytest.mark.asyncio
async def test_raise_for_status_http_error():
    from aiohttp import ClientResponseError

    client = EmbeddingServiceAsyncClient(base_url=BASE_URL, port=PORT)
    await client.__aenter__()
    resp = MagicMock()
    resp.raise_for_status.side_effect = ClientResponseError(request_info=None, history=None, status=400, message="fail")
    with pytest.raises(EmbeddingServiceHTTPError):
        await client._raise_for_status(resp)
    await client.__aexit__(None, None, None)


# Покрытие: _raise_for_status - не ClientResponseError
@pytest.mark.asyncio
async def test_raise_for_status_other_error():
    client = EmbeddingServiceAsyncClient(base_url=BASE_URL, port=PORT)
    await client.__aenter__()
    resp = MagicMock()
    resp.raise_for_status.side_effect = ValueError("fail")
    with pytest.raises(ValueError):
        await client._raise_for_status(resp)
    await client.__aexit__(None, None, None)


# Покрытие: __aenter__ и __aexit__ - ошибка при создании/закрытии сессии
@pytest.mark.asyncio
async def test_aenter_aexit_exceptions():
    client = EmbeddingServiceAsyncClient(base_url=BASE_URL, port=PORT)
    # Исключение при создании сессии
    orig = client._session
    client._session = None
    with patch("aiohttp.ClientSession", side_effect=RuntimeError("fail")):
        with pytest.raises(EmbeddingServiceError) as excinfo:
            async with client:
                pass
        assert "Failed to create HTTP session" in str(excinfo.value)

    # Исключение при закрытии сессии
    class BadSession:
        async def close(self):
            raise RuntimeError("fail")

    client._session = BadSession()
    with pytest.raises(EmbeddingServiceError) as excinfo:
        await client.__aexit__(None, None, None)
    assert "Failed to close HTTP session" in str(excinfo.value)


@pytest.mark.asyncio
async def test_make_url_error():
    client = EmbeddingServiceAsyncClient(base_url="http://localhost", port=8001)
    # Ошибка: base_url не строка
    with pytest.raises(EmbeddingServiceConfigError):
        client._make_url("/test", base_url=123)


@pytest.mark.asyncio
async def test_embed_validation():
    """Test validation of input texts for embed command."""
    client = EmbeddingServiceAsyncClient()

    # Test empty texts list
    with pytest.raises(EmbeddingServiceAPIError) as excinfo:
        await client.cmd("embed", params={"texts": []})
    assert "Empty texts list provided" in str(excinfo.value)

    # Test empty strings
    with pytest.raises(EmbeddingServiceAPIError) as excinfo:
        await client.cmd("embed", params={"texts": ["", "   "]})
    assert "Invalid input texts" in str(excinfo.value)
    assert "Text at index 0 is empty" in str(excinfo.value)
    assert "Text at index 1 is empty" in str(excinfo.value)

    # Test too short texts
    with pytest.raises(EmbeddingServiceAPIError) as excinfo:
        await client.cmd("embed", params={"texts": ["a", "b"]})
    assert "Invalid input texts" in str(excinfo.value)
    assert "Text at index 0 is too short" in str(excinfo.value)
    assert "Text at index 1 is too short" in str(excinfo.value)

    # Test mixed valid and invalid texts
    with pytest.raises(EmbeddingServiceAPIError) as excinfo:
        await client.cmd("embed", params={"texts": ["valid text", "", "   ", "a"]})
    assert "Invalid input texts" in str(excinfo.value)
    assert "Text at index 1 is empty" in str(excinfo.value)
    assert "Text at index 2 is empty" in str(excinfo.value)
    assert "Text at index 3 is too short" in str(excinfo.value)


# Additional tests for 90% coverage


@pytest.mark.asyncio
async def test_init_edge_cases():
    """Test edge cases in constructor validation."""
    # Test empty string base_url - it will use env var default "http://localhost"
    # So we need to test invalid URL format instead
    with pytest.raises(EmbeddingServiceConfigError, match="base_url must start with"):
        EmbeddingServiceAsyncClient(base_url="invalid-url", port=8001)

    # Test non-string base_url
    with pytest.raises(EmbeddingServiceConfigError, match="base_url must be a string"):
        EmbeddingServiceAsyncClient(base_url=123, port=8001)

    # Test invalid port type
    with pytest.raises(EmbeddingServiceConfigError, match="port must be a valid integer"):
        EmbeddingServiceAsyncClient(base_url="http://test", port="invalid")


@pytest.mark.asyncio
async def test_init_env_var_edge_cases(monkeypatch):
    """Test edge cases with environment variables."""
    # Test invalid port in env var
    monkeypatch.setenv("EMBEDDING_SERVICE_PORT", "invalid")
    with pytest.raises(EmbeddingServiceConfigError, match="Invalid port configuration"):
        EmbeddingServiceAsyncClient(base_url="http://test")

    # Test invalid timeout
    with pytest.raises(EmbeddingServiceConfigError, match="Invalid timeout configuration"):
        EmbeddingServiceAsyncClient(base_url="http://test", port=8001, timeout="invalid")

    # Test empty base_url from env (should use default)
    monkeypatch.delenv("EMBEDDING_SERVICE_PORT", raising=False)  # Clear invalid port
    monkeypatch.setenv("EMBEDDING_SERVICE_BASE_URL", "")
    with pytest.raises(EmbeddingServiceConfigError, match="base_url must be provided"):
        EmbeddingServiceAsyncClient()

    # Test base_url attribute error (simulate TypeError/AttributeError)
    with patch("os.getenv", side_effect=TypeError("Env error")):
        with pytest.raises(EmbeddingServiceConfigError, match="Invalid base_url configuration"):
            EmbeddingServiceAsyncClient()


@pytest.mark.asyncio
async def test_parse_json_response_edge_cases():
    """Test edge cases in JSON response parsing."""
    client = EmbeddingServiceAsyncClient(base_url="http://test", port=8001)

    # Test case where getting response text also fails
    mock_resp = AsyncMock()
    mock_resp.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
    mock_resp.text.side_effect = Exception("Failed to get text")

    await client.__aenter__()
    with pytest.raises(EmbeddingServiceJSONError, match="Failed to get response text"):
        await client._parse_json_response(mock_resp)
    await client.__aexit__(None, None, None)


@pytest.mark.asyncio
async def test_cmd_nested_error_response():
    """Test cmd with nested error response format."""
    client = EmbeddingServiceAsyncClient(base_url="http://test", port=8001)
    mock_response = MockAiohttpResponse(
        json_data={
            "result": {
                "success": False,
                "error": {"code": 123, "message": "nested error"},
            }
        }
    )
    await client.__aenter__()
    with patch.object(client._session, "post", return_value=mock_response):
        with pytest.raises(EmbeddingServiceAPIError):
            await client.cmd("embed", params={"texts": ["abc"]})
    await client.__aexit__(None, None, None)


@pytest.mark.asyncio
async def test_cmd_result_success_false_with_nested_error():
    """Test cmd with result.success=False and nested error structure."""
    client = EmbeddingServiceAsyncClient(base_url="http://test", port=8001)
    mock_response = MockAiohttpResponse(
        json_data={
            "result": {
                "success": False,
                "error": {
                    "code": -32602,
                    "message": "Invalid parameters",
                    "details": ["Parameter 'texts' is required"],
                },
            }
        }
    )
    await client.__aenter__()
    with patch.object(client._session, "post", return_value=mock_response):
        with pytest.raises(EmbeddingServiceAPIError) as excinfo:
            await client.cmd("embed", params={"texts": ["abc"]})
        assert "Invalid parameters" in str(excinfo.value)
    await client.__aexit__(None, None, None)


@pytest.mark.asyncio
async def test_specific_aiohttp_exceptions():
    """Test specific aiohttp exceptions in all methods."""
    client = EmbeddingServiceAsyncClient(base_url="http://test", port=8001)

    await client.__aenter__()
    # Test ClientResponseError in health
    with patch.object(
        client._session,
        "get",
        side_effect=aiohttp.ClientResponseError(
            request_info=MagicMock(), history=(), status=400, message="Bad Request"
        ),
    ):
        with pytest.raises(EmbeddingServiceHTTPError):
            await client.health()

    # Test asyncio.TimeoutError in get_openapi_schema
    with patch.object(client._session, "get", side_effect=asyncio.TimeoutError()):
        with pytest.raises(EmbeddingServiceTimeoutError):
            await client.get_openapi_schema()

    # Test ServerTimeoutError in get_commands (will be caught as ConnectionError due to inheritance)
    with patch.object(client._session, "get", side_effect=aiohttp.ServerTimeoutError()):
        with pytest.raises(EmbeddingServiceConnectionError):
            await client.get_commands()

    # Test ClientOSError in cmd
    with patch.object(client._session, "post", side_effect=aiohttp.ClientOSError("OS error")):
        with pytest.raises(EmbeddingServiceConnectionError):
            await client.cmd("embed", params={"texts": ["test"]})
    await client.__aexit__(None, None, None)


@pytest.mark.asyncio
async def test_aenter_session_creation_error():
    """Test error during session creation in __aenter__."""
    with patch("aiohttp.ClientSession", side_effect=Exception("Session creation failed")):
        client = EmbeddingServiceAsyncClient(base_url="http://test", port=8001)
        with pytest.raises(EmbeddingServiceError, match="Failed to create HTTP session"):
            async with client:
                pass


@pytest.mark.asyncio
async def test_aexit_session_close_error():
    """Test error during session close in __aexit__."""
    client = EmbeddingServiceAsyncClient(base_url="http://test", port=8001)

    # Enter context and then mock close to fail
    await client.__aenter__()
    client._session.close = AsyncMock(side_effect=Exception("Close failed"))

    # This should raise an exception when exiting the context
    with pytest.raises(EmbeddingServiceError, match="Failed to close HTTP session"):
        await client.__aexit__(None, None, None)


@pytest.mark.asyncio
async def test_port_none_edge_case(monkeypatch):
    """Test edge case where port is explicitly None and env var is also None."""
    # Clear env var and set it to None-like value that will cause int() to fail
    monkeypatch.delenv("EMBEDDING_SERVICE_PORT", raising=False)

    # Mock os.getenv to return None for port
    with patch(
        "os.getenv",
        side_effect=lambda key, default=None: (None if key == "EMBEDDING_SERVICE_PORT" else default),
    ):
        with pytest.raises(EmbeddingServiceConfigError, match="Invalid port configuration"):
            EmbeddingServiceAsyncClient(base_url="http://test")


@pytest.mark.asyncio
async def test_format_error_response():
    """Test error response formatting."""
    client = EmbeddingServiceAsyncClient(base_url=BASE_URL, port=PORT)

    # Test basic error
    error_resp = client._format_error_response("Test error")
    assert error_resp == {"error": "Embedding service error: Test error"}

    # Test error with lang
    error_resp = client._format_error_response("Test error", lang="en")
    assert error_resp == {"error": "Embedding service error: Test error", "lang": "en"}

    # Test error with text
    error_resp = client._format_error_response("Test error", text="sample text")
    assert error_resp == {
        "error": "Embedding service error: Test error",
        "text": "sample text",
    }

    # Test error with both lang and text
    error_resp = client._format_error_response("Test error", lang="en", text="sample text")
    assert error_resp == {
        "error": "Embedding service error: Test error",
        "lang": "en",
        "text": "sample text",
    }


@pytest.mark.asyncio
async def test_extract_embeddings_old_format():
    """Test extracting embeddings from old format responses."""
    client = EmbeddingServiceAsyncClient(base_url=BASE_URL, port=PORT)

    # Test direct embeddings field
    result = {"embeddings": [[0.1, 0.2], [0.3, 0.4]]}
    vectors = client.extract_embeddings(result)
    assert vectors == [[0.1, 0.2], [0.3, 0.4]]

    # Test result.embeddings
    result = {"result": {"embeddings": [[0.1, 0.2], [0.3, 0.4]]}}
    vectors = client.extract_embeddings(result)
    assert vectors == [[0.1, 0.2], [0.3, 0.4]]

    # Test result.data.embeddings
    result = {"result": {"data": {"embeddings": [[0.1, 0.2], [0.3, 0.4]]}}}
    vectors = client.extract_embeddings(result)
    assert vectors == [[0.1, 0.2], [0.3, 0.4]]

    # Test direct list in result
    result = {"result": [[0.1, 0.2], [0.3, 0.4]]}
    vectors = client.extract_embeddings(result)
    assert vectors == [[0.1, 0.2], [0.3, 0.4]]


@pytest.mark.asyncio
async def test_extract_embeddings_new_format():
    """Test extracting embeddings from new format responses."""
    client = EmbeddingServiceAsyncClient(base_url=BASE_URL, port=PORT)

    # Test new format: result.data[].embedding
    result = {
        "result": {
            "success": True,
            "data": [
                {"body": "text1", "embedding": [0.1, 0.2], "chunks": ["text1"]},
                {"body": "text2", "embedding": [0.3, 0.4], "chunks": ["text2"]},
            ],
        }
    }
    vectors = client.extract_embeddings(result)
    assert vectors == [[0.1, 0.2], [0.3, 0.4]]


@pytest.mark.asyncio
async def test_extract_embeddings_invalid():
    """Test extracting embeddings from invalid responses."""
    client = EmbeddingServiceAsyncClient(base_url=BASE_URL, port=PORT)

    # Test empty result
    with pytest.raises(ValueError, match="Cannot extract embeddings"):
        client.extract_embeddings({})

    # Test invalid new format item
    result = {
        "result": {
            "data": [
                {"body": "text1", "embedding": [0.1, 0.2], "chunks": ["text1"]},
                "invalid_item",  # This should cause an error
            ]
        }
    }
    with pytest.raises(ValueError, match="Invalid item format"):
        client.extract_embeddings(result)


@pytest.mark.asyncio
async def test_extract_embedding_data_new_format():
    """Test extracting full embedding data from new format responses."""
    client = EmbeddingServiceAsyncClient(base_url=BASE_URL, port=PORT)

    # Test valid new format
    result = {
        "result": {
            "success": True,
            "data": [
                {
                    "body": "text1",
                    "embedding": [0.1, 0.2],
                    "chunks": ["chunk1", "chunk2"],
                },
                {"body": "text2", "embedding": [0.3, 0.4], "chunks": ["chunk3"]},
            ],
        }
    }
    data = client.extract_embedding_data(result)
    expected = [
        {"body": "text1", "embedding": [0.1, 0.2], "chunks": ["chunk1", "chunk2"]},
        {"body": "text2", "embedding": [0.3, 0.4], "chunks": ["chunk3"]},
    ]
    assert data == expected


@pytest.mark.asyncio
async def test_extract_embedding_data_invalid():
    """Test extracting embedding data from invalid or old format responses."""
    client = EmbeddingServiceAsyncClient(base_url=BASE_URL, port=PORT)

    # Test old format (should fail)
    result = {"result": {"data": {"embeddings": [[0.1, 0.2], [0.3, 0.4]]}}}
    with pytest.raises(ValueError, match="new format required"):
        client.extract_embedding_data(result)

    # Test missing body field
    result = {"result": {"data": [{"embedding": [0.1, 0.2], "chunks": ["chunk1"]}]}}  # Missing body
    with pytest.raises(ValueError, match="missing 'body' field"):
        client.extract_embedding_data(result)

    # Test missing embedding field
    result = {"result": {"data": [{"body": "text1", "chunks": ["chunk1"]}]}}  # Missing embedding
    with pytest.raises(ValueError, match="missing 'embedding' field"):
        client.extract_embedding_data(result)

    # Test missing chunks field
    result = {"result": {"data": [{"body": "text1", "embedding": [0.1, 0.2]}]}}  # Missing chunks
    with pytest.raises(ValueError, match="missing 'chunks' or 'tokens' field"):
        client.extract_embedding_data(result)

    # Test non-dict item
    result = {"result": {"data": ["not_a_dict"]}}
    with pytest.raises(ValueError, match="is not a dictionary"):
        client.extract_embedding_data(result)


@pytest.mark.asyncio
async def test_extract_texts():
    """Test extracting texts from new format responses."""
    client = EmbeddingServiceAsyncClient(base_url=BASE_URL, port=PORT)

    result = {
        "result": {
            "data": [
                {"body": "text1", "embedding": [0.1, 0.2], "chunks": ["chunk1"]},
                {"body": "text2", "embedding": [0.3, 0.4], "chunks": ["chunk2"]},
            ]
        }
    }
    texts = client.extract_texts(result)
    assert texts == ["text1", "text2"]


@pytest.mark.asyncio
async def test_extract_chunks():
    """Test extracting chunks from new format responses."""
    client = EmbeddingServiceAsyncClient(base_url=BASE_URL, port=PORT)

    result = {
        "result": {
            "data": [
                {"body": "text1", "embedding": [0.1, 0.2], "tokens": ["text1"]},
                {"body": "text2", "embedding": [0.3, 0.4], "tokens": ["text2"]},
            ]
        }
    }
    chunks = client.extract_chunks(result)
    assert chunks == [["text1"], ["text2"]]


@pytest.mark.asyncio
async def test_extract_tokens():
    """Test extracting tokens from new format responses."""
    client = EmbeddingServiceAsyncClient(base_url=BASE_URL, port=PORT)

    result = {
        "result": {
            "data": {
                "results": [
                    {
                        "body": "text1",
                        "embedding": [0.1, 0.2],
                        "tokens": ["text1"],
                        "bm25_tokens": ["text1"],
                    },
                    {
                        "body": "text2",
                        "embedding": [0.3, 0.4],
                        "tokens": ["text2"],
                        "bm25_tokens": ["text2"],
                    },
                ]
            }
        }
    }
    tokens = client.extract_tokens(result)
    assert tokens == [["text1"], ["text2"]]


@pytest.mark.asyncio
async def test_extract_bm25_tokens():
    """Test extracting BM25 tokens from new format responses."""
    client = EmbeddingServiceAsyncClient(base_url=BASE_URL, port=PORT)

    result = {
        "result": {
            "data": {
                "results": [
                    {
                        "body": "text1",
                        "embedding": [0.1, 0.2],
                        "tokens": ["text1"],
                        "bm25_tokens": ["text1"],
                    },
                    {
                        "body": "text2",
                        "embedding": [0.3, 0.4],
                        "tokens": ["text2"],
                        "bm25_tokens": ["text2"],
                    },
                ]
            }
        }
    }
    bm25_tokens = client.extract_bm25_tokens(result)
    assert bm25_tokens == [["text1"], ["text2"]]


@pytest.mark.asyncio
async def test_close_without_open():
    client = EmbeddingServiceAsyncClient(base_url="http://localhost", port=8001)
    # Should not raise
    await client.close()


@pytest.mark.asyncio
async def test_close_after_aenter():
    client = EmbeddingServiceAsyncClient(base_url="http://localhost", port=8001)
    await client.__aenter__()
    await client.close()
    # Second close should be safe
    await client.close()


@pytest.mark.asyncio
async def test_close_in_context_manager():
    async with EmbeddingServiceAsyncClient(base_url="http://localhost", port=8001) as client:
        pass
    # After context, explicit close should be safe
    await client.close()


def test_format_error_response_all_branches():
    client = EmbeddingServiceAsyncClient()
    # Только error
    r1 = client._format_error_response("err")
    assert r1 == {"error": "Embedding service error: err"}
    # error + lang
    r2 = client._format_error_response("err", lang="en")
    assert r2["lang"] == "en"
    # error + text
    r3 = client._format_error_response("err", text="t")
    assert r3["text"] == "t"
    # error + lang + text
    r4 = client._format_error_response("err", lang="en", text="t")
    assert r4["lang"] == "en" and r4["text"] == "t"


def test_extract_embeddings_value_errors():
    client = EmbeddingServiceAsyncClient()
    # Нет embeddings и result
    with pytest.raises(ValueError):
        client.extract_embeddings({"foo": 1})
    # result не list/dict
    with pytest.raises(ValueError):
        client.extract_embeddings({"result": 123})
    # result.data не list/dict
    with pytest.raises(ValueError):
        client.extract_embeddings({"result": {"data": 123}})
    # result.data list, но item не dict
    with pytest.raises(ValueError):
        client.extract_embeddings({"result": {"data": [1, 2, 3]}})


def test_extract_embedding_data_value_errors():
    client = EmbeddingServiceAsyncClient()
    # Нет result
    with pytest.raises(ValueError):
        client.extract_embedding_data({"foo": 1})
    # result не dict
    with pytest.raises(ValueError):
        client.extract_embedding_data({"result": 123})
    # result.data не list
    with pytest.raises(ValueError):
        client.extract_embedding_data({"result": {"data": 123}})
    # item не dict
    with pytest.raises(ValueError):
        client.extract_embedding_data({"result": {"data": [1, 2, 3]}})
    # item без body/embedding/chunks
    with pytest.raises(ValueError):
        client.extract_embedding_data({"result": {"data": [{"body": "a"}]}})
    with pytest.raises(ValueError):
        client.extract_embedding_data({"result": {"data": [{"embedding": [1]}]}})
    with pytest.raises(ValueError):
        client.extract_embedding_data({"result": {"data": [{"chunks": []}]}})


def test_extract_texts_chunks_value_error():
    client = EmbeddingServiceAsyncClient()
    with pytest.raises(ValueError):
        client.extract_texts({"foo": 1})
    with pytest.raises(ValueError):
        client.extract_chunks({"foo": 1})


@pytest.mark.asyncio
async def test__parse_json_response_all_branches():
    client = EmbeddingServiceAsyncClient()

    class FakeResp:
        async def json(self):
            raise json.JSONDecodeError("bad", "doc", 0)

        async def text(self):
            return "not json"

    resp = FakeResp()
    with pytest.raises(EmbeddingServiceJSONError):
        await client._parse_json_response(resp)

    class FakeResp2:
        async def json(self):
            raise UnicodeDecodeError("utf-8", b"", 0, 1, "bad")

    with pytest.raises(EmbeddingServiceJSONError):
        await client._parse_json_response(FakeResp2())

    class FakeResp3:
        async def json(self):
            raise Exception("other")

    with pytest.raises(EmbeddingServiceJSONError):
        await client._parse_json_response(FakeResp3())

    class Good:
        async def json(self):
            return {"ok": 1}

    assert await client._parse_json_response(Good()) == {"ok": 1}


@pytest.mark.asyncio
async def test__raise_for_status_no_error():
    client = EmbeddingServiceAsyncClient()

    class Resp:
        def raise_for_status(self):
            return None

    await client._raise_for_status(Resp())


@pytest.mark.asyncio
async def test_aenter_aexit_exceptions():
    # Ошибка создания сессии
    class BadSession:
        def __init__(self, *a, **kw):
            raise RuntimeError("fail")

    orig = aiohttp.ClientSession
    aiohttp.ClientSession = BadSession
    client = EmbeddingServiceAsyncClient()
    with pytest.raises(EmbeddingServiceError):
        await client.__aenter__()
    aiohttp.ClientSession = orig

    # Ошибка закрытия сессии
    class BadSession2:
        async def close(self):
            raise RuntimeError("fail")

    client._session = BadSession2()
    with pytest.raises(EmbeddingServiceError):
        await client.__aexit__(None, None, None)


@pytest.mark.asyncio
async def test_close_error():
    client = EmbeddingServiceAsyncClient()

    class BadSession:
        async def close(self):
            raise RuntimeError("fail")

    client._session = BadSession()
    with pytest.raises(EmbeddingServiceError):
        await client.close()


def test_validate_texts_all_branches():
    client = EmbeddingServiceAsyncClient()
    # Пустой список
    with pytest.raises(EmbeddingServiceAPIError):
        client._validate_texts([])
    # Не строка
    with pytest.raises(EmbeddingServiceAPIError):
        client._validate_texts([1, "ok"])
    # Пустая строка
    with pytest.raises(EmbeddingServiceAPIError):
        client._validate_texts(["", "ok"])
    # Строка из пробелов
    with pytest.raises(EmbeddingServiceAPIError):
        client._validate_texts(["   ", "ok"])
    # Короткая строка
    with pytest.raises(EmbeddingServiceAPIError):
        client._validate_texts(["a", "ok"])


def test_example_async_usage_smoke(monkeypatch):
    import importlib
    import embed_client.example_async_usage as ex

    monkeypatch.setattr(ex, "main", lambda *a, **kw: None)
    importlib.reload(ex)
    assert hasattr(ex, "main")


def test_example_async_usage_ru_smoke(monkeypatch):
    import importlib
    import embed_client.example_async_usage_ru as ex

    monkeypatch.setattr(ex, "main", lambda *a, **kw: None)
    importlib.reload(ex)
    assert hasattr(ex, "main")


def test_init_typeerror_base_url():
    # base_url не строка, вызовет TypeError
    with pytest.raises(EmbeddingServiceConfigError):
        EmbeddingServiceAsyncClient(base_url=object())


@pytest.mark.asyncio
async def test_cmd_unexpected_exception(monkeypatch):
    client = EmbeddingServiceAsyncClient()
    await client.__aenter__()

    # Мокаем post чтобы выбрасывал неожиданный Exception
    class DummyResp:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def json(self):
            return {"result": "ok"}

        async def raise_for_status(self):
            return None

    async def bad_post(*a, **kw):
        raise RuntimeError("fail-cmd")

    client._session.post = bad_post
    with pytest.raises(EmbeddingServiceError):
        await client.cmd("embed", params={"texts": ["abc"]})
    await client.__aexit__(None, None, None)


@pytest.mark.asyncio
async def test__parse_json_response_unexpected(monkeypatch):
    client = EmbeddingServiceAsyncClient()

    class FakeResp:
        async def json(self):
            raise Exception("unexpected")

    with pytest.raises(EmbeddingServiceJSONError):
        await client._parse_json_response(FakeResp())


@pytest.mark.asyncio
async def test_close_none_session():
    client = EmbeddingServiceAsyncClient()
    # self._session = None, close должен быть noop
    client._session = None
    await client.close()


@pytest.mark.asyncio
def test_extract_embeddings_all_value_errors():
    client = EmbeddingServiceAsyncClient()
    # result.data list, item dict без embedding
    with pytest.raises(ValueError):
        client.extract_embeddings({"result": {"data": [{"foo": 1}]}})
    # result.data list, item не dict (уже есть)
    # (убран кейс с {'embedding': None})


@pytest.mark.asyncio
async def test_cmd_all_except_branches(monkeypatch):
    client = EmbeddingServiceAsyncClient()
    await client.__aenter__()

    # aiohttp.ClientResponseError
    class DummyResp:
        status = 400

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def json(self):
            return {"result": "ok"}

        def raise_for_status(self):
            raise aiohttp.ClientResponseError(request_info=None, history=None, status=400, message="fail")

    def post(*a, **kw):
        return DummyResp()

    client._session.post = post
    with pytest.raises(EmbeddingServiceHTTPError):
        await client.cmd("embed", params={"texts": ["abc"]})

    # aiohttp.ClientSSLError
    class DummyConnKey:
        ssl = True
        host = "localhost"
        port = 8001
        is_ssl = True

    def raise_ssl(*a, **kw):
        raise aiohttp.ClientSSLError(connection_key=DummyConnKey(), os_error=OSError("ssl"))

    client._session.post = raise_ssl
    with pytest.raises(EmbeddingServiceConnectionError):
        await client.cmd("embed", params={"texts": ["abc"]})

    # aiohttp.ClientOSError
    def raise_os(*a, **kw):
        raise aiohttp.ClientOSError(OSError("os"))

    client._session.post = raise_os
    with pytest.raises(EmbeddingServiceConnectionError):
        await client.cmd("embed", params={"texts": ["abc"]})
    await client.__aexit__(None, None, None)


@pytest.mark.asyncio
async def test_close_error_finally():
    client = EmbeddingServiceAsyncClient()

    class BadSession:
        async def close(self):
            raise RuntimeError("fail")

    client._session = BadSession()
    # Проверяем, что self._session = None даже при ошибке
    try:
        await client.close()
    except EmbeddingServiceError:
        pass
    assert client._session is None
