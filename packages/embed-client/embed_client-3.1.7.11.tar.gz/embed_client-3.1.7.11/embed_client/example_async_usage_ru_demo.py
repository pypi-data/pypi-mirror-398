"""
Вспомогательные демонстрационные функции для example_async_usage_ru.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

from typing import Any, Dict, List

from embed_client.async_client import EmbeddingServiceAsyncClient, EmbeddingServiceError
from embed_client.client_factory import ClientFactory, detect_security_mode
from embed_client.response_parsers import extract_embeddings


async def run_client_examples(client: EmbeddingServiceAsyncClient) -> None:
    """Запуск примерных операций с клиентом."""
    # Проверка здоровья сервиса
    try:
        health = await client.health()
        print("Состояние сервиса:", health)
    except EmbeddingServiceError as exc:
        print(f"Ошибка при проверке состояния сервиса: {exc}")
        return

    # Получение OpenAPI схемы
    try:
        schema = await client.get_openapi_schema()
        version = schema.get("info", {}).get("version", "unknown")
        print("Версия OpenAPI схемы:", version)
    except EmbeddingServiceError as exc:
        print(f"Ошибка при получении OpenAPI схемы: {exc}")

    # Получение списка доступных команд
    try:
        commands = await client.get_commands()
        print(f"Доступные команды: {commands}")
    except EmbeddingServiceError as exc:
        print(f"Ошибка при получении списка команд: {exc}")

    # Генерация эмбеддингов
    try:
        texts = [
            "Привет, мир!",
            "Это тестовое предложение.",
            "Сервис эмбеддингов работает!",
        ]
        result = await client.cmd("embed", {"texts": texts})

        embeddings = extract_embeddings(result)
        print(f"Сгенерировано эмбеддингов: {len(embeddings)}")
        print(
            "Размерность первого эмбеддинга:",
            len(embeddings[0]) if embeddings else 0,
        )
    except EmbeddingServiceError as exc:
        print(f"Ошибка при генерации эмбеддингов: {exc}")


async def demonstrate_security_modes() -> None:
    """Демонстрация всех режимов безопасности с использованием ClientFactory."""
    print("=== Демонстрация режимов безопасности ===")
    print("Этот пример показывает, как создавать клиентов для всех 6 режимов.")
    print(
        "Важно: примеры создают конфигурации клиентов, но не подключаются "
        "к реальным серверам."
    )

    # 1. HTTP
    print("\n1. HTTP режим (без аутентификации, без SSL):")
    print("   Использование: разработка, внутренние сети, доверенная среда")
    try:
        client = ClientFactory.create_http_client("http://localhost", 8001)
        print(f"   ✓ HTTP клиент: {client.base_url}:{client.port}")
        print(f"   ✓ SSL включён: {client.is_ssl_enabled()}")
        print(f"   ✓ Аутентифицирован: {client.is_authenticated()}")
        print(f"   ✓ Метод аутентификации: {client.get_auth_method()}")
        await client.close()
    except Exception as exc:  # noqa: BLE001
        print(f"   ✗ Ошибка: {exc}")

    # 2. HTTP + Token
    print("\n2. HTTP + Token (HTTP с API ключом):")
    print("   Использование: управление доступом к API, простая аутентификация")
    try:
        client = ClientFactory.create_http_token_client(
            "http://localhost", 8001, "api_key", api_key="demo_key"
        )
        print(f"   ✓ HTTP + Token клиент: {client.base_url}:{client.port}")
        print(f"   ✓ SSL включён: {client.is_ssl_enabled()}")
        print(f"   ✓ Аутентифицирован: {client.is_authenticated()}")
        print(f"   ✓ Метод аутентификации: {client.get_auth_method()}")
        if client.is_authenticated():
            headers = client.get_auth_headers()
            print(f"   ✓ Заголовки аутентификации: {headers}")
        await client.close()
    except Exception as exc:  # noqa: BLE001
        print(f"   ✗ Ошибка: {exc}")

    # 3. HTTPS
    print("\n3. HTTPS режим (шифрование с сертификатами сервера):")
    print("   Использование: защищённое соединение, публичные сети")
    try:
        client = ClientFactory.create_https_client("https://localhost", 9443)
        print(f"   ✓ HTTPS клиент: {client.base_url}:{client.port}")
        print(f"   ✓ SSL включён: {client.is_ssl_enabled()}")
        print(f"   ✓ Аутентифицирован: {client.is_authenticated()}")
        if client.is_ssl_enabled():
            ssl_config = client.get_ssl_config()
            print(f"   ✓ SSL конфигурация: {ssl_config}")
            protocols = client.get_supported_ssl_protocols()
            print(f"   ✓ Поддерживаемые SSL протоколы: {protocols}")
        await client.close()
    except Exception as exc:  # noqa: BLE001
        print(f"   ✗ Ошибка: {exc}")

    # 4. HTTPS + Token
    print("\n4. HTTPS + Token (HTTPS + аутентификация):")
    print("   Использование: защищённый доступ к API, production")
    try:
        client = ClientFactory.create_https_token_client(
            "https://localhost",
            9443,
            "basic",
            username="admin",
            password="secret",
        )
        print(f"   ✓ HTTPS + Token клиент: {client.base_url}:{client.port}")
        print(f"   ✓ SSL включён: {client.is_ssl_enabled()}")
        print(f"   ✓ Аутентифицирован: {client.is_authenticated()}")
        print(f"   ✓ Метод аутентификации: {client.get_auth_method()}")
        if client.is_authenticated():
            headers = client.get_auth_headers()
            print(f"   ✓ Заголовки аутентификации: {headers}")
        await client.close()
    except Exception as exc:  # noqa: BLE001
        print(f"   ✗ Ошибка: {exc}")

    # 5. mTLS
    print("\n5. mTLS (взаимная TLS, сертификаты клиента и сервера):")
    print("   Использование: максимальная безопасность, аутентификация клиента")
    try:
        client = ClientFactory.create_mtls_client(
            "https://localhost",
            "mtls_certificates/client/embedding-service.crt",
            "mtls_certificates/client/embedding-service.key",
            8443,
        )
        print(f"   ✓ mTLS клиент: {client.base_url}:{client.port}")
        print(f"   ✓ SSL включён: {client.is_ssl_enabled()}")
        print(f"   ✓ mTLS включён: {client.is_mtls_enabled()}")
        print(f"   ✓ Аутентифицирован: {client.is_authenticated()}")
        if client.is_ssl_enabled():
            ssl_config = client.get_ssl_config()
            print(f"   ✓ SSL конфигурация: {ssl_config}")
        await client.close()
    except Exception as exc:  # noqa: BLE001
        print(f"   ✗ Ошибка: {exc}")

    # 6. mTLS + Roles
    print("\n6. mTLS + Roles (mTLS + роли):")
    print("   Использование: корпоративная безопасность, права доступа по ролям")
    try:
        client = ClientFactory.create_mtls_roles_client(
            "https://localhost",
            "mtls_certificates/client/embedding-service.crt",
            "mtls_certificates/client/embedding-service.key",
            8443,
            roles=["admin", "user"],
            role_attributes={"department": "IT"},
        )
        print(f"   ✓ mTLS + Roles клиент: {client.base_url}:{client.port}")
        print(f"   ✓ SSL включён: {client.is_ssl_enabled()}")
        print(f"   ✓ mTLS включён: {client.is_mtls_enabled()}")
        print(f"   ✓ Аутентифицирован: {client.is_authenticated()}")
        if client.is_authenticated():
            headers = client.get_auth_headers()
            print(f"   ✓ Заголовки аутентификации: {headers}")
        await client.close()
    except Exception as exc:  # noqa: BLE001
        print(f"   ✗ Ошибка: {exc}")

    print("\n=== Краткое резюме режимов безопасности ===")
    print("1. HTTP: базовая связность, без безопасности")
    print("2. HTTP + Token: API ключ поверх HTTP")
    print("3. HTTPS: шифрование с сертификатами сервера")
    print("4. HTTPS + Token: шифрование + аутентификация")
    print("5. mTLS: взаимная аутентификация сертификатами")
    print("6. mTLS + Roles: сертификаты + контроль доступа по ролям")


async def demonstrate_automatic_detection() -> None:
    """Демонстрация автоматического определения режима безопасности."""
    print("\n=== Автоматическое определение режима безопасности ===")
    print(
        "Этот пример показывает, как клиент автоматически определяет "
        "подходящий режим безопасности."
    )

    test_cases: List[Any] = [
        ("http://localhost", None, None, None, None, "HTTP"),
        ("http://localhost", "api_key", None, None, None, "HTTP + Token"),
        ("https://localhost", None, None, None, None, "HTTPS"),
        ("https://localhost", "api_key", None, None, None, "HTTPS + Token"),
        ("https://localhost", None, None, "cert.pem", "key.pem", "mTLS"),
        (
            "https://localhost",
            None,
            None,
            "cert.pem",
            "key.pem",
            "mTLS + Roles",
            {"roles": ["admin"]},
        ),
    ]

    for case in test_cases:
        if len(case) == 6:
            base_url, auth_method, ssl_enabled, cert_file, key_file, expected = case
            kwargs: Dict[str, Any] = {}
        else:
            (
                base_url,
                auth_method,
                ssl_enabled,
                cert_file,
                key_file,
                expected,
                kwargs,
            ) = case

        try:
            mode = detect_security_mode(
                base_url, auth_method, ssl_enabled, cert_file, key_file, **kwargs
            )
            print(
                f"  ✓ {base_url} + {auth_method or 'none'} + "
                f"{cert_file or 'no cert'} -> {mode} ({expected})"
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  ✗ Ошибка при определении режима для {base_url}: {exc}")


async def demonstrate_with_auth_method() -> None:
    """Демонстрация метода with_auth для динамической аутентификации."""
    print("\n=== Динамическая аутентификация с помощью with_auth() ===")
    print(
        "Пример показывает, как создавать клиентов с разными методами "
        "аутентификации, используя метод класса with_auth."
    )

    auth_examples = [
        ("api_key", {"api_key": "dynamic_api_key"}, "API Key аутентификация"),
        (
            "jwt",
            {"secret": "secret", "username": "user", "password": "pass"},
            "JWT аутентификация",
        ),
        ("basic", {"username": "admin", "password": "secret"}, "Basic аутентификация"),
        (
            "certificate",
            {"cert_file": "client.crt", "key_file": "client.key"},
            "Certificate аутентификация",
        ),
    ]

    for auth_method, kwargs, description in auth_examples:
        try:
            print(f"\n{description}:")
            auth_client = EmbeddingServiceAsyncClient.with_auth(
                "http://localhost",
                8001,
                auth_method,
                **kwargs,
            )
            print(f"  ✓ Метод аутентификации: {auth_client.get_auth_method()}")
            print(f"  ✓ Аутентифицирован: {auth_client.is_authenticated()}")
            if auth_client.is_authenticated():
                headers = auth_client.get_auth_headers()
                print(f"  ✓ Заголовки аутентификации: {headers}")
            await auth_client.close()
        except Exception as exc:  # noqa: BLE001
            print(f"  ✗ Ошибка для {auth_method}: {exc}")

    print("\n✓ Демонстрация динамической аутентификации завершена.")


__all__ = [
    "run_client_examples",
    "demonstrate_security_modes",
    "demonstrate_automatic_detection",
    "demonstrate_with_auth_method",
]
