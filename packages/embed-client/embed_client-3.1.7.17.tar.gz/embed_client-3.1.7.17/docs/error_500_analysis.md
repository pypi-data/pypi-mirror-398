# Анализ ошибки 500 при запросе OpenAPI схемы

## Описание проблемы

При выполнении теста `test_real_openapi` в файле `tests/test_async_client_real.py` возникает ошибка HTTP 500 при запросе OpenAPI схемы от сервера.

## Детали ошибки

### Запрос
- **URL**: `http://localhost:8001/openapi.json`
- **Метод**: GET
- **Клиент**: `EmbeddingServiceAsyncClient`

### Ответ сервера
- **Статус**: 500 Internal Server Error
- **Заголовки**:
  ```
  Content-Length: 174
  Content-Type: application/json
  x-request-id: 4997d9f6-4147-45bf-869f-08458b247999
  x-process-time: 0.001s
  Date: Sat, 06 Sep 2025 23:28:55 GMT
  Server: hypercorn-h11
  ```
- **Тело ответа**:
  ```json
  {
    "error": "Protocol validation error",
    "message": "[Errno 2] No such file or directory: '/usr/local/lib/python3.10/site-packages/mcp_proxy_adapter/schemas/openapi_schema.json'"
  }
  ```

### Код ошибки
```python
aiohttp.client_exceptions.ClientResponseError: 500, message='', url='http://localhost:8001/openapi.json'
```

## Анализ

### Причина ошибки

**ОСНОВНАЯ ПРИЧИНА**: Отсутствует файл OpenAPI схемы

Сервер пытается загрузить файл OpenAPI схемы по пути:
```
/usr/local/lib/python3.10/site-packages/mcp_proxy_adapter/schemas/openapi_schema.json
```

Но файл не существует, что приводит к ошибке:
```
[Errno 2] No such file or directory
```

### Детали проблемы

1. **Отсутствующий файл**
   - Файл `openapi_schema.json` не найден в пакете `mcp_proxy_adapter`
   - Путь указывает на системную установку Python 3.10
   - Возможно, пакет установлен не полностью или поврежден

2. **Проблема с установкой пакета**
   - `mcp_proxy_adapter` может быть установлен не полностью
   - Отсутствуют файлы схем в пакете
   - Проблема с версией пакета

### Время обработки
- **x-process-time**: 0.002s - очень быстрое время обработки, что указывает на раннее завершение запроса с ошибкой

### Контекст тестирования

Тест выполняется в рамках интеграционного тестирования с реальным сервером:

```python
@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_openapi(real_client):
    if not await is_service_available():
        pytest.skip("Real service on localhost:8001 is not available.")
    result = await real_client.get_openapi_schema()
```

## Рекомендации по исправлению

### 1. Проверка установки пакета mcp_proxy_adapter
```bash
# Проверить установку пакета
pip show mcp_proxy_adapter

# Проверить содержимое пакета
ls -la /usr/local/lib/python3.10/site-packages/mcp_proxy_adapter/

# Проверить наличие файлов схем
ls -la /usr/local/lib/python3.10/site-packages/mcp_proxy_adapter/schemas/
```

### 2. Переустановка пакета
```bash
# Переустановить пакет
pip uninstall mcp_proxy_adapter
pip install mcp_proxy_adapter

# Или установить из исходников
pip install -e /path/to/mcp_proxy_adapter
```

### 3. Проверка версии Python
```bash
# Проверить версию Python сервера
python --version

# Убедиться, что используется правильная версия
which python
```

### 4. Создание отсутствующего файла
Если файл действительно отсутствует, можно создать заглушку:
```bash
# Создать директорию
mkdir -p /usr/local/lib/python3.10/site-packages/mcp_proxy_adapter/schemas/

# Создать базовую OpenAPI схему
cat > /usr/local/lib/python3.10/site-packages/mcp_proxy_adapter/schemas/openapi_schema.json << 'EOF'
{
  "openapi": "3.0.0",
  "info": {
    "title": "Embedding Service API",
    "version": "1.0.0"
  },
  "paths": {
    "/health": {
      "get": {
        "summary": "Health check",
        "responses": {
          "200": {
            "description": "Service is healthy"
          }
        }
      }
    }
  }
}
EOF
```

### 5. Обновление теста для обработки ошибки
```python
@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_openapi(real_client):
    if not await is_service_available():
        pytest.skip("Real service on localhost:8001 is not available.")
    
    try:
        result = await real_client.get_openapi_schema()
        assert result is not None
    except EmbeddingServiceHTTPError as e:
        if e.status == 500 and "No such file or directory" in str(e):
            pytest.skip(f"OpenAPI schema file missing on server: {e}")
        else:
            raise
```

## Статус

- **Тип**: Интеграционная ошибка
- **Приоритет**: Низкий (не влияет на основную функциональность)
- **Влияние**: Только на интеграционные тесты
- **Решение**: ✅ **РЕШЕНО** - исправлена установка пакета `mcp_proxy_adapter`
- **Статус**: ✅ **ИСПРАВЛЕНО** - файл OpenAPI схемы восстановлен
- **Дата исправления**: 2025-09-06

## Результаты исправления

### ✅ Подтверждение исправления

После исправления сервера:

1. **OpenAPI схема доступна**:
   ```bash
   curl -s http://localhost:8001/openapi.json | jq .info.title
   # Результат: "MCP Proxy Adapter"
   ```

2. **Все интеграционные тесты проходят**:
   ```bash
   pytest tests/test_async_client_real.py -v
   # Результат: 9 passed in 7.55s
   ```

3. **Полная OpenAPI схема возвращается**:
   - Версия: OpenAPI 3.0.2
   - Название: "MCP Proxy Adapter"
   - Доступные эндпоинты: `/cmd`, `/health`, `/openapi.json`, `/api/commands`
   - Поддерживаемые команды: embed, models, help, health, config, reload, settings, load, unload, plugins, transport_management, proxy_registration, echo, roletest

### 📊 Статистика тестов

- **Всего интеграционных тестов**: 9
- **Прошедших тестов**: 9 ✅
- **Неудачных тестов**: 0 ❌
- **Время выполнения**: 7.55s

## Связанные файлы

- `tests/test_async_client_real.py` - тест, вызывающий ошибку
- `embed_client/async_client.py` - метод `get_openapi_schema()`
- `tests/conftest.py` - конфигурация тестов

---

**Автор**: Vasiliy Zdanovskiy  
**Email**: vasilyvz@gmail.com  
**Дата**: 2025-09-06
