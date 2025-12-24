# embed-client

Асинхронный клиент для Embedding Service API с поддержкой всех режимов безопасности.

## Возможности

- ✅ **Асинхронный API** - полная поддержка async/await
- ✅ **Все режимы безопасности** - HTTP, HTTPS, mTLS
- ✅ **Аутентификация** - API Key, JWT, Basic Auth, Certificate
- ✅ **SSL/TLS поддержка** - полная интеграция с mcp_security_framework
- ✅ **Конфигурация** - файлы конфигурации, переменные окружения, аргументы
- ✅ **Обратная совместимость** - API формат не изменился, добавлена только безопасность
- ✅ **Типизация** - 100% type-annotated код
- ✅ **Тестирование** - 84+ тестов с полным покрытием

## Quick Start: Примеры запуска

### Базовое использование

**Вариант 1: через аргументы командной строки**

```sh
# HTTP без аутентификации
python embed_client/example_async_usage.py --base-url http://localhost --port 8001

# HTTP с API ключом
python embed_client/example_async_usage.py --base-url http://localhost --port 8001 \
  --auth-method api_key --api-key admin_key_123

# HTTPS с SSL
python embed_client/example_async_usage.py --base-url https://localhost --port 9443 \
  --ssl-verify-mode CERT_REQUIRED

# mTLS с сертификатами
python embed_client/example_async_usage.py --base-url https://localhost --port 9443 \
  --cert-file certs/client.crt --key-file keys/client.key --ca-cert-file certs/ca.crt
```

**Вариант 2: через переменные окружения**

```sh
export EMBED_CLIENT_BASE_URL=http://localhost
export EMBED_CLIENT_PORT=8001
export EMBED_CLIENT_AUTH_METHOD=api_key
export EMBED_CLIENT_API_KEY=admin_key_123
python embed_client/example_async_usage.py
```

**Вариант 3: через файл конфигурации**

```sh
python embed_client/example_async_usage.py --config configs/https_token.json
```

### Режимы безопасности

#### 1. HTTP (без аутентификации)
```python
from embed_client.async_client import EmbeddingServiceAsyncClient

client = EmbeddingServiceAsyncClient(
    base_url="http://localhost",
    port=8001
)
```

#### 2. HTTP + Token
```python
from embed_client.config import ClientConfig

# API Key
config = ClientConfig.create_http_token_config(
    "http://localhost", 8001, {"user": "api_key_123"}
)

# JWT
config = ClientConfig.create_http_jwt_config(
    "http://localhost", 8001, "secret", "username", "password"
)

# Basic Auth
config = ClientConfig.create_http_basic_config(
    "http://localhost", 8001, "username", "password"
)
```

#### 3. HTTPS
```python
config = ClientConfig.create_https_config(
    "https://localhost", 9443,
    ca_cert_file="certs/ca.crt"
)
```

#### 4. mTLS (взаимная аутентификация)
```python
config = ClientConfig.create_mtls_config(
    "https://localhost", 9443,
    cert_file="certs/client.crt",
    key_file="keys/client.key",
    ca_cert_file="certs/ca.crt"
)
```

### Программное использование

```python
import asyncio
from embed_client.async_client import EmbeddingServiceAsyncClient


async def main():
    # Minimal configuration for HTTPS + token on localhost:8001 via MCP Proxy Adapter
    config_dict = {
        "server": {"host": "localhost", "port": 8001},
        "auth": {"method": "api_key", "api_keys": {"user": "user-secret-key"}},
        "ssl": {
            "enabled": True,
            "verify_mode": "CERT_NONE",
            "check_hostname": False,
            # Paths from mtls_certificates used by test environment
            "cert_file": "mtls_certificates/client/embedding-service.crt",
            "key_file": "mtls_certificates/client/embedding-service.key",
            "ca_cert_file": "mtls_certificates/ca/ca.crt",
        },
    }

    texts = ["valid text", "   ", "!!!"]

    async with EmbeddingServiceAsyncClient(config_dict=config_dict) as client:
        # High-level helper: always uses error_policy="continue"
        data = await client.embed(texts, error_policy="continue")

        # Iterate over per-item results
        for idx, item in enumerate(data["results"]):
            err = item["error"]
            if err is None:
                embedding = item["embedding"]
                print(f"{idx}: OK, embedding length={len(embedding)}")
            else:
                print(f"{idx}: ERROR {err['code']} - {err['message']}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Vectorization methods (English)

### 1. Python async client – high-level `embed()`

- Use `EmbeddingServiceAsyncClient.embed()` for batch vectorization with per-item errors.
- Always pass `error_policy="continue"` to keep positional mapping between `texts[i]` and `results[i]`.

Example (see above): run `python embed_client/example_async_usage.py` or a custom script with `EmbeddingServiceAsyncClient.embed()`.

### 2. Python async client – low-level `cmd("embed")`

- For advanced scenarios you can call `client.cmd("embed", params=...)` directly and use helpers from `response_parsers`.

```python
params = {"texts": texts, "error_policy": "continue"}
raw_result = await client.cmd("embed", params=params)
data = extract_embedding_data(raw_result)
```

### 3. CLI – `embed-vectorize`

The package installs a CLI tool for vectorization:

```bash
# HTTP (no auth) on localhost:8001
embed-config-generator --mode http --host localhost --port 8001 --output ./configs/http_8001.json
embed-vectorize --config ./configs/http_8001.json "hello world" "another text"

# HTTPS + token + mTLS certificates (recommended for production-like tests)
embed-config-generator --mode https_token --host localhost --port 8001 \
  --cert-file mtls_certificates/client/embedding-service.crt \
  --key-file mtls_certificates/client/embedding-service.key \
  --ca-cert-file mtls_certificates/ca/ca.crt \
  --output ./configs/https_token_8001.json

embed-vectorize --config ./configs/https_token_8001.json "valid text" "   " "!!!"
```

### 4. Full embed contract example on localhost:8001

For a complete contract test of `error_policy="continue"` across all 8 security modes, use:

```bash
python tests/test_embed_contract_8001.py
```

This script uses `ClientConfigGenerator` and `EmbeddingServiceAsyncClient.embed()` and is regularly validated against a real server on `localhost:8001`.

## Установка

```bash
# Установка из PyPI
pip install embed-client

# Установка в режиме разработки
git clone <repository>
cd embed-client
pip install -e .
```

## Dependencies (runtime)

- `mcp-proxy-adapter` - JSON-RPC transport for Embedding Service via MCP Proxy Adapter
- `PyJWT>=2.0.0` - JWT tokens (used for diagnostics and compatibility)
- `cryptography>=3.0.0` - certificates and crypto primitives
- `pydantic>=2.0.0` - configuration validation

## Тестирование

```bash
# Запуск всех тестов
pytest tests/

# Запуск тестов с покрытием
pytest tests/ --cov=embed_client

# Запуск конкретных тестов
pytest tests/test_async_client.py -v
pytest tests/test_config.py -v
pytest tests/test_auth.py -v
pytest tests/test_ssl_manager.py -v
```

## Документация

- [Формат API и режимы безопасности](docs/api_format.md)
- [Примеры использования](embed_client/example_async_usage.py)
- [Примеры на русском](embed_client/example_async_usage_ru.py)

## Безопасность

### Рекомендации

1. **Используйте HTTPS** для продакшена
2. **Включите проверку сертификатов** (CERT_REQUIRED)
3. **Используйте mTLS** для критически важных систем
4. **Регулярно обновляйте сертификаты**
5. **Храните приватные ключи в безопасном месте**

### Поддерживаемые протоколы

- TLS 1.2
- TLS 1.3
- SSL 3.0 (устаревший, не рекомендуется)

## Лицензия

MIT License

## Автор

**Vasiliy Zdanovskiy**  
Email: vasilyvz@gmail.com

---

**Важно:**
- Используйте `--base-url` (через дефис), а не `--base_url` (через подчеркивание).
- Значение base_url должно содержать `http://` или `https://`.
- Аргументы должны быть отдельными (через пробел), а не через `=`.