import sys
import types
import pytest
import asyncio
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_example_async_usage(monkeypatch):
    # Подменяем sys.argv для передачи base_url и порта
    monkeypatch.setattr(
        sys,
        "argv",
        ["example_async_usage.py", "--base-url", "http://test", "--port", "8001"],
    )

    # Создаем мок клиента с правильными ответами
    mock_client = AsyncMock()
    mock_client.health.return_value = {"status": "ok"}
    mock_client.cmd.side_effect = [
        # Первый вызов cmd("embed", params={"texts": ["hello world", "test embedding"]})
        {
            "result": {
                "success": True,
                "data": {
                    "embeddings": [
                        [0.1, 0.2, 0.3, 0.4, 0.5],  # для "hello world"
                        [0.6, 0.7, 0.8, 0.9, 1.0],  # для "test embedding"
                    ]
                },
            }
        },
        # Второй вызов cmd("health")
        {"result": {"status": "healthy"}},
        # Третий вызов cmd("") - должен выбросить исключение
        None,  # Этот вызов не достигнется, так как выбросится исключение
    ]

    # Настраиваем мок для пустой команды
    from embed_client.async_client import EmbeddingServiceAPIError

    def cmd_side_effect(command, params=None):
        if command == "embed":
            return {
                "result": {
                    "success": True,
                    "data": {
                        "embeddings": [
                            [0.1, 0.2, 0.3, 0.4, 0.5],
                            [0.6, 0.7, 0.8, 0.9, 1.0],
                        ]
                    },
                }
            }
        elif command == "health":
            return {"result": {"status": "healthy"}}
        elif command == "":
            raise EmbeddingServiceAPIError("API error: {'code': -32602, 'message': 'Command is required'}")
        else:
            return {"result": "ok"}

    mock_client.cmd.side_effect = cmd_side_effect

    # Мокаем контекстный менеджер и сам клиент
    with patch("embed_client.example_async_usage.EmbeddingServiceAsyncClient") as mock_client_class:
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

        # Импортируем и выполняем main()
        import importlib
        import embed_client.example_async_usage as example

        importlib.reload(example)
        await example.main()


@pytest.mark.asyncio
async def test_example_async_usage_no_base_url(monkeypatch):
    # Clear environment variables that might provide default values
    monkeypatch.delenv("EMBED_CLIENT_BASE_URL", raising=False)
    monkeypatch.delenv("EMBED_CLIENT_PORT", raising=False)

    # Set argv to simulate no arguments
    monkeypatch.setattr(sys, "argv", ["example_async_usage.py"])

    with patch("builtins.print") as mock_print, patch("sys.exit") as mock_exit:
        import importlib
        import embed_client.example_async_usage as example

        importlib.reload(example)
        await example.main()
        mock_print.assert_called()
        # The example should not exit because it has default values
        # Let's check that it runs successfully instead
        mock_exit.assert_not_called()
