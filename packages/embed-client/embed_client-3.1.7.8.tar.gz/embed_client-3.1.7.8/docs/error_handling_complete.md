# Полная обработка ошибок в EmbeddingServiceAsyncClient

## Обзор

Клиент `EmbeddingServiceAsyncClient` теперь обрабатывает **ВСЕ** типы ошибок, выбрасывая соответствующие исключения для каждой категории проблем.

## Иерархия исключений

```python
EmbeddingServiceError (базовое исключение)
├── EmbeddingServiceConfigError      # Ошибки конфигурации
├── EmbeddingServiceConnectionError  # Сетевые ошибки
├── EmbeddingServiceHTTPError        # HTTP ошибки (4xx, 5xx)
├── EmbeddingServiceTimeoutError     # Таймауты
├── EmbeddingServiceJSONError        # Ошибки парсинга JSON
└── EmbeddingServiceAPIError         # Ошибки API/JSON-RPC
```

## Типы обрабатываемых ошибок

### 1. Ошибки конфигурации (`EmbeddingServiceConfigError`)
- Неверный `base_url` (не http:// или https://)
- Неверный `port` (не число, вне диапазона 1-65535)
- Неверный `timeout` (не число или отрицательный)
- Ошибки создания URL
- Ошибки переменных окружения

### 2. Сетевые ошибки (`EmbeddingServiceConnectionError`)
- `aiohttp.ClientConnectionError` - проблемы подключения
- `aiohttp.ClientSSLError` - SSL/TLS ошибки
- `aiohttp.ClientOSError` - ошибки операционной системы
- Ошибки DNS, прокси, сетевых интерфейсов

### 3. HTTP ошибки (`EmbeddingServiceHTTPError`)
- `aiohttp.ClientResponseError` - HTTP 4xx, 5xx ошибки
- Содержит код статуса и сообщение

### 4. Ошибки таймаута (`EmbeddingServiceTimeoutError`)
- `asyncio.TimeoutError` - общие таймауты
- `aiohttp.ServerTimeoutError` - таймауты сервера
- Превышение лимитов времени запроса

### 5. Ошибки JSON (`EmbeddingServiceJSONError`)
- `json.JSONDecodeError` - невалидный JSON
- `UnicodeDecodeError` - проблемы кодировки
- Неожиданные ошибки парсинга

### 6. API ошибки (`EmbeddingServiceAPIError`)
- Ошибки JSON-RPC протокола
- Валидация входных данных
- Логические ошибки API

### 7. Ошибки сессии (`EmbeddingServiceError`)
- Ошибки создания HTTP сессии
- Ошибки закрытия сессии
- Прочие неожиданные ошибки

## Примеры использования

```python
from embed_client.async_client import (
    EmbeddingServiceAsyncClient,
    EmbeddingServiceConfigError,
    EmbeddingServiceConnectionError,
    EmbeddingServiceTimeoutError,
    EmbeddingServiceAPIError,
    EmbeddingServiceError
)

try:
    async with EmbeddingServiceAsyncClient(
        base_url="http://localhost", 
        port=8001,
        timeout=30.0
    ) as client:
        result = await client.cmd("embed", params={"texts": ["test"]})
        
except EmbeddingServiceConfigError as e:
    print(f"Configuration error: {e}")
    
except EmbeddingServiceConnectionError as e:
    print(f"Network/connection error: {e}")
    
except EmbeddingServiceTimeoutError as e:
    print(f"Timeout error: {e}")
    
except EmbeddingServiceAPIError as e:
    print(f"API error: {e}")
    
except EmbeddingServiceError as e:
    print(f"General service error: {e}")
```

## Ключевые улучшения

1. **Полная типизация ошибок** - каждый тип ошибки имеет свой класс исключения
2. **Валидация конфигурации** - проверка параметров при создании клиента
3. **Timeout поддержка** - настраиваемые таймауты для всех запросов
4. **JSON парсинг** - безопасный парсинг с подробными ошибками
5. **Порядок обработки** - правильная последовательность catch блоков
6. **Сохранение контекста** - все исключения сохраняют оригинальную причину (`from e`)

## Тестирование

Добавлено **45 тестов**, покрывающих все типы ошибок:
- Тесты конфигурации
- Тесты сетевых ошибок  
- Тесты таймаутов
- Тесты JSON парсинга
- Тесты API ошибок
- Тесты создания/закрытия сессии

## Обратная совместимость

Все изменения обратно совместимы:
- Существующий код продолжает работать
- Добавлены новые типы исключений
- Улучшена диагностика ошибок
- Сохранена функциональность API

## Заключение

Теперь клиент выбрасывает исключения на **ЛЮБУЮ** ошибку:
- ✅ Сетевые ошибки
- ✅ HTTP ошибки  
- ✅ JSON-RPC ошибки
- ✅ Ошибки сервера
- ✅ Ошибки настроек
- ✅ Таймауты
- ✅ SSL ошибки
- ✅ Ошибки парсинга
- ✅ Ошибки сессии

Никаких "тихих" ошибок больше нет! 