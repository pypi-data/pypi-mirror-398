# Формат запроса и результата Embedding Service API (порт 8001)

> **Важно**: API формат не изменился! Добавилась только поддержка различных режимов безопасности (HTTP, HTTPS, аутентификация). Все команды и форматы ответов остались прежними.

## Запрос на получение эмбеддингов (batch)

**POST** `/cmd`

```json
{
  "command": "embed",
  "params": {
    "texts": [
      "строка1",
      "строка2",
      "..."
    ],
    "model": "опционально, имя модели",
    "dimension": "опционально, размерность вектора"
  }
}
```

- `texts` — массив строк (обязательный)
- `model` — имя модели (опционально)
- `dimension` — размерность вектора (опционально)

---

## Формат успешного ответа (НОВЫЙ ФОРМАТ)

```json
{
  "result": {
    "success": true,
    "data": {
      "embeddings": [[0.1, 0.2, 0.3, ...], [0.4, 0.5, 0.6, ...]],
      "results": [
      {
        "body": "строка1",
        "embedding": [0.1, 0.2, 0.3, ...],
          "tokens": ["token1", "token2", ...],
          "bm25_tokens": ["bm25_token1", "bm25_token2", ...]
      },
      {
        "body": "строка2", 
        "embedding": [0.4, 0.5, 0.6, ...],
          "tokens": ["token3", "token4", ...],
          "bm25_tokens": ["bm25_token3", "bm25_token4", ...]
      }
    ]
    }
  }
}
```

Каждый объект в массиве `results` содержит:
- `body` — исходный текст
- `embedding` — векторное представление (массив чисел float)
- `tokens` — массив токенов текста (массив строк)
- `bm25_tokens` — массив BM25 токенов (массив строк)

---

## Формат ошибки (остается прежним)

```json
{
  "error": {
    "code": -32601,
    "message": "Команда 'not_a_command' не найдена"
  }
}
```
- `code` — код ошибки (например, -32601 — команда не найдена)
- `message` — текстовое описание ошибки

---

## Пример запроса на несколько текстов

```json
{
  "command": "embed",
  "params": {
    "texts": ["vector one", "vector two", "vector three"]
  }
}
```

## Пример успешного ответа (НОВЫЙ ФОРМАТ)

```json
{
  "result": {
    "success": true,
    "data": {
      "embeddings": [[0.1, 0.2, 0.3, ...], [0.4, 0.5, 0.6, ...], [0.7, 0.8, 0.9, ...]],
      "results": [
      {
        "body": "vector one",
        "embedding": [0.1, 0.2, 0.3, ...],
          "tokens": ["vector", "one"],
          "bm25_tokens": ["vector", "one"]
      },
      {
        "body": "vector two",
        "embedding": [0.4, 0.5, 0.6, ...],
          "tokens": ["vector", "two"],
          "bm25_tokens": ["vector", "two"]
      },
      {
        "body": "vector three",
        "embedding": [0.7, 0.8, 0.9, ...],
          "tokens": ["vector", "three"],
          "bm25_tokens": ["vector", "three"]
      }
    ]
    }
  }
}
```

## Пример ошибки

```json
{
  "error": {
    "code": -32601,
    "message": "Команда 'not_a_command' не найдена"
  }
}
```

## Input Validation

The API performs validation of input texts before processing:

1. Empty texts list is not allowed
2. Empty strings or strings containing only whitespace are not allowed
3. Text must be at least 2 characters long after stripping whitespace

If validation fails, the API returns an error response with:
- Error code: -32602 (Invalid params)
- Error message: "Invalid input texts"
- Details: List of specific validation errors for each invalid text

Example error response:
```json
{
    "error": {
        "code": -32602,
        "message": "Invalid input texts",
        "details": [
            "Text at index 0 is empty or contains only whitespace",
            "Text at index 1 is too short (minimum 2 characters)"
        ]
    }
}
```

## Миграция с предыдущего формата

**Старый формат (устарел):**
```json
{
  "result": {
    "success": true,
    "data": {
      "embeddings": [
        [0.1, 0.2, ...],
        [0.3, 0.4, ...],
        ...
      ]
    }
  }
}
```

**Новый формат:**
```json
{
  "result": {
    "success": true,
    "data": {
      "embeddings": [[0.1, 0.2, ...], [0.3, 0.4, ...], ...],
      "results": [
      {
        "body": "исходный текст",
        "embedding": [0.1, 0.2, ...],
          "tokens": ["token1", "token2", ...],
          "bm25_tokens": ["bm25_token1", "bm25_token2", ...]
      },
      ...
    ]
    }
  }
}
```

Основные изменения:
- `data` теперь объект с полями `embeddings` и `results`
- `embeddings` содержит массив векторов (старый формат для совместимости)
- `results` содержит массив объектов с полной информацией
- Каждый элемент содержит вектор, исходный текст, токены и BM25 токены
- Поле `chunks` заменено на `tokens` и добавлено `bm25_tokens`

---

## Режимы безопасности и SSL/TLS

### Поддерживаемые режимы безопасности

Клиент поддерживает следующие режимы безопасности:

#### 1. HTTP (без аутентификации)
```python
client = EmbeddingServiceAsyncClient(
    base_url="http://localhost",
    port=8001
)
```

#### 2. HTTP + Token (с аутентификацией)
```python
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

#### 3. HTTPS (с сертификатами сервера)
```python
config = ClientConfig.create_https_config(
    "https://localhost", 9443,
    ca_cert_file="certs/ca.crt"
)
```

#### 4. HTTPS + Token (HTTPS с аутентификацией)
```python
config = ClientConfig.create_https_token_config(
    "https://localhost", 9443, {"user": "api_key_123"},
    ca_cert_file="certs/ca.crt"
)
```

#### 5. mTLS (взаимная аутентификация)
```python
config = ClientConfig.create_mtls_config(
    "https://localhost", 9443,
    cert_file="certs/client.crt",
    key_file="keys/client.key",
    ca_cert_file="certs/ca.crt"
)
```

#### 6. mTLS + Roles (mTLS с ролевой моделью)
```python
config = ClientConfig.create_mtls_roles_config(
    "https://localhost", 9443,
    cert_file="certs/client.crt",
    key_file="keys/client.key",
    ca_cert_file="certs/ca.crt",
    roles_config_file="configs/roles.json"
)
```

### SSL/TLS конфигурация

#### Параметры SSL/TLS

```python
ssl_config = {
    "enabled": True,
    "verify_mode": "CERT_REQUIRED",  # CERT_NONE, CERT_OPTIONAL, CERT_REQUIRED
    "check_hostname": True,
    "check_expiry": True,
    "ca_cert_file": "certs/ca.crt",
    "cert_file": "certs/client.crt",  # для mTLS
    "key_file": "keys/client.key"     # для mTLS
}
```

#### Режимы проверки сертификатов

- **CERT_NONE**: Не проверять сертификаты (не рекомендуется для продакшена)
- **CERT_OPTIONAL**: Проверять сертификаты, если они предоставлены
- **CERT_REQUIRED**: Обязательная проверка сертификатов (рекомендуется)

#### Проверка SSL/TLS статуса

```python
# Проверка включен ли SSL
if client.is_ssl_enabled():
    print("SSL/TLS включен")

# Проверка mTLS
if client.is_mtls_enabled():
    print("mTLS включен")

# Получение SSL конфигурации
ssl_config = client.get_ssl_config()
print(f"SSL конфигурация: {ssl_config}")

# Получение поддерживаемых протоколов
protocols = client.get_supported_ssl_protocols()
print(f"Поддерживаемые протоколы: {protocols}")

# Валидация SSL конфигурации
errors = client.validate_ssl_config()
if errors:
    print(f"Ошибки SSL конфигурации: {errors}")
```

### Примеры использования

#### Командная строка

```bash
# HTTP с API ключом
python embed_client/example_async_usage.py \
  --base-url http://localhost --port 8001 \
  --auth-method api_key --api-key admin_key_123

# HTTPS с отключенной проверкой SSL
python embed_client/example_async_usage.py \
  --base-url https://localhost --port 9443 \
  --ssl-verify-mode CERT_NONE

# mTLS с пользовательским CA сертификатом
python embed_client/example_async_usage.py \
  --base-url https://localhost --port 9443 \
  --cert-file certs/client.crt --key-file keys/client.key \
  --ca-cert-file certs/ca.crt
```

#### Программное использование

```python
import asyncio
from embed_client.async_client import EmbeddingServiceAsyncClient
from embed_client.config import ClientConfig

async def main():
    # Создание конфигурации для mTLS
    config = ClientConfig.create_mtls_config(
        "https://localhost", 9443,
        cert_file="certs/client.crt",
        key_file="keys/client.key",
        ca_cert_file="certs/ca.crt"
    )
    
    # Создание клиента
    async with EmbeddingServiceAsyncClient.from_config(config) as client:
        # Проверка SSL статуса
        print(f"SSL включен: {client.is_ssl_enabled()}")
        print(f"mTLS включен: {client.is_mtls_enabled()}")
        
        # Выполнение запроса
        result = await client.cmd("embed", params={"texts": ["test"]})
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

### Безопасность

#### Рекомендации по безопасности

1. **Используйте HTTPS** для продакшена
2. **Включите проверку сертификатов** (CERT_REQUIRED)
3. **Используйте mTLS** для критически важных систем
4. **Регулярно обновляйте сертификаты**
5. **Храните приватные ключи в безопасном месте**

#### Обработка ошибок SSL/TLS

```python
try:
    async with EmbeddingServiceAsyncClient.from_config(config) as client:
        result = await client.cmd("embed", params={"texts": ["test"]})
except EmbeddingServiceConnectionError as e:
    if "SSL" in str(e) or "certificate" in str(e).lower():
        print("Ошибка SSL/TLS соединения")
    else:
        print("Ошибка сетевого соединения")
except Exception as e:
    print(f"Неожиданная ошибка: {e}")
``` 