#!/usr/bin/env python3
"""
Примеры использования embed-client с различными конфигурациями безопасности.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Этот файл демонстрирует все 6 режимов безопасности, поддерживаемых embed-client:
1. HTTP - обычный HTTP без аутентификации
2. HTTP + Token - HTTP с API Key, JWT или Basic аутентификацией
3. HTTPS - HTTPS с проверкой сертификата сервера
4. HTTPS + Token - HTTPS с сертификатами сервера + аутентификация
5. mTLS - взаимный TLS с клиентскими и серверными сертификатами
6. mTLS + Roles - mTLS с контролем доступа на основе ролей
"""

import asyncio
import json
import os
from typing import Dict, Any

from embed_client.async_client import EmbeddingServiceAsyncClient
from embed_client.config import ClientConfig
from embed_client.client_factory import (
    ClientFactory, SecurityMode, create_client, create_client_from_config,
    create_client_from_env, detect_security_mode
)


async def example_1_http_plain():
    """Пример 1: HTTP - обычный HTTP без аутентификации."""
    print("=== Пример 1: HTTP - Обычный HTTP без аутентификации ===")
    
    # Способ 1: Прямое создание клиента
    async with EmbeddingServiceAsyncClient("http://localhost", 8001) as client:
        print(f"Клиент: {client.base_url}:{client.port}")
        print(f"SSL включен: {client.is_ssl_enabled()}")
        print(f"Аутентификация: {client.is_authenticated()}")
        
        # Тест проверки здоровья
        health = await client.health()
        print(f"Состояние: {health}")
    
    # Способ 2: Использование словаря конфигурации
    config_dict = {
        "server": {"host": "http://localhost", "port": 8001},
        "auth": {"method": "none"},
        "ssl": {"enabled": False}
    }
    
    async with EmbeddingServiceAsyncClient(config_dict=config_dict) as client:
        health = await client.health()
        print(f"Состояние через конфиг: {health}")
    
    # Способ 3: Использование ClientFactory
    client = ClientFactory.create_http_client("http://localhost", 8001)
    print(f"Фабричный клиент: {client.base_url}:{client.port}")
    await client.close()


async def example_2_http_token():
    """Пример 2: HTTP + Token - HTTP с аутентификацией API Key."""
    print("\n=== Пример 2: HTTP + Token - HTTP с аутентификацией API Key ===")
    
    # Способ 1: Использование метода класса with_auth
    async with EmbeddingServiceAsyncClient.with_auth(
        "http://localhost", 8001, "api_key", api_key="your_api_key"
    ) as client:
        print(f"Клиент: {client.base_url}:{client.port}")
        print(f"SSL включен: {client.is_ssl_enabled()}")
        print(f"Аутентификация: {client.is_authenticated()}")
        print(f"Метод аутентификации: {client.get_auth_method()}")
        print(f"Заголовки аутентификации: {client.get_auth_headers()}")
    
    # Способ 2: Использование словаря конфигурации
    config_dict = {
        "server": {"host": "http://localhost", "port": 8001},
        "auth": {
            "method": "api_key",
            "api_keys": {"user": "your_api_key"}
        },
        "ssl": {"enabled": False}
    }
    
    async with EmbeddingServiceAsyncClient(config_dict=config_dict) as client:
        print(f"Метод аутентификации через конфиг: {client.get_auth_method()}")
    
    # Способ 3: Использование ClientFactory
    client = ClientFactory.create_http_token_client(
        "http://localhost", 8001, "api_key", api_key="your_api_key"
    )
    print(f"Метод аутентификации фабричного клиента: {client.get_auth_method()}")
    await client.close()


async def example_3_https_plain():
    """Пример 3: HTTPS - HTTPS с проверкой сертификата сервера."""
    print("\n=== Пример 3: HTTPS - HTTPS с проверкой сертификата сервера ===")
    
    # Способ 1: Прямое создание клиента с HTTPS
    config_dict = {
        "server": {"host": "https://localhost", "port": 8443},
        "auth": {"method": "none"},
        "ssl": {
            "enabled": True,
            "verify_mode": "CERT_REQUIRED",
            "check_hostname": True,
            "check_expiry": True
        }
    }
    
    async with EmbeddingServiceAsyncClient(config_dict=config_dict) as client:
        print(f"Клиент: {client.base_url}:{client.port}")
        print(f"SSL включен: {client.is_ssl_enabled()}")
        print(f"Аутентификация: {client.is_authenticated()}")
        if client.is_ssl_enabled():
            ssl_config = client.get_ssl_config()
            print(f"Конфигурация SSL: {ssl_config}")
            protocols = client.get_supported_ssl_protocols()
            print(f"Поддерживаемые SSL протоколы: {protocols}")
    
    # Способ 2: Использование ClientFactory
    client = ClientFactory.create_https_client("https://localhost", 8443)
    print(f"Фабричный HTTPS клиент: {client.base_url}:{client.port}")
    await client.close()


async def example_4_https_token():
    """Пример 4: HTTPS + Token - HTTPS с сертификатами сервера + аутентификация."""
    print("\n=== Пример 4: HTTPS + Token - HTTPS с сертификатами сервера + аутентификация ===")
    
    # Способ 1: Использование with_auth с HTTPS
    async with EmbeddingServiceAsyncClient.with_auth(
        "https://localhost", 8443, "basic", 
        username="admin", password="secret",
        ssl_enabled=True,
        verify_mode="CERT_REQUIRED",
        check_hostname=True
    ) as client:
        print(f"Клиент: {client.base_url}:{client.port}")
        print(f"SSL включен: {client.is_ssl_enabled()}")
        print(f"Аутентификация: {client.is_authenticated()}")
        print(f"Метод аутентификации: {client.get_auth_method()}")
        print(f"Заголовки аутентификации: {client.get_auth_headers()}")
    
    # Способ 2: Использование словаря конфигурации
    config_dict = {
        "server": {"host": "https://localhost", "port": 8443},
        "auth": {
            "method": "jwt",
            "jwt": {
                "secret": "your_jwt_secret",
                "username": "admin",
                "password": "secret"
            }
        },
        "ssl": {
            "enabled": True,
            "verify_mode": "CERT_REQUIRED",
            "check_hostname": True,
            "check_expiry": True
        }
    }
    
    async with EmbeddingServiceAsyncClient(config_dict=config_dict) as client:
        print(f"Метод аутентификации JWT: {client.get_auth_method()}")
    
    # Способ 3: Использование ClientFactory
    client = ClientFactory.create_https_token_client(
        "https://localhost", 8443, "api_key", api_key="your_api_key"
    )
    print(f"Метод аутентификации фабричного HTTPS+Token клиента: {client.get_auth_method()}")
    await client.close()


async def example_5_mtls():
    """Пример 5: mTLS - взаимный TLS с клиентскими и серверными сертификатами."""
    print("\n=== Пример 5: mTLS - Взаимный TLS с клиентскими и серверными сертификатами ===")
    
    # Способ 1: Использование with_auth с сертификатами
    async with EmbeddingServiceAsyncClient.with_auth(
        "https://localhost", 8443, "certificate",
        cert_file="mtls_certificates/client/embedding-service.crt",
        key_file="mtls_certificates/client/embedding-service.key",
        ca_cert_file="mtls_certificates/ca/ca.crt",
        ssl_enabled=True,
        verify_mode="CERT_REQUIRED",
        check_hostname=True
    ) as client:
        print(f"Клиент: {client.base_url}:{client.port}")
        print(f"SSL включен: {client.is_ssl_enabled()}")
        print(f"mTLS включен: {client.is_mtls_enabled()}")
        print(f"Аутентификация: {client.is_authenticated()}")
        print(f"Метод аутентификации: {client.get_auth_method()}")
        if client.is_ssl_enabled():
            ssl_config = client.get_ssl_config()
            print(f"Конфигурация SSL: {ssl_config}")
    
    # Способ 2: Использование словаря конфигурации
    config_dict = {
        "server": {"host": "https://localhost", "port": 8443},
        "auth": {
            "method": "certificate",
            "certificate": {
                "cert_file": "mtls_certificates/client/embedding-service.crt",
                "key_file": "mtls_certificates/client/embedding-service.key",
                "ca_cert_file": "mtls_certificates/ca/ca.crt"
            }
        },
        "ssl": {
            "enabled": True,
            "verify_mode": "CERT_REQUIRED",
            "check_hostname": True,
            "check_expiry": True,
            "cert_file": "mtls_certificates/client/embedding-service.crt",
            "key_file": "mtls_certificates/client/embedding-service.key",
            "ca_cert_file": "mtls_certificates/ca/ca.crt"
        }
    }
    
    async with EmbeddingServiceAsyncClient(config_dict=config_dict) as client:
        print(f"Метод аутентификации mTLS: {client.get_auth_method()}")
        print(f"mTLS включен: {client.is_mtls_enabled()}")
    
    # Способ 3: Использование ClientFactory
    client = ClientFactory.create_mtls_client(
        "https://localhost", 
        "mtls_certificates/client/embedding-service.crt",
        "mtls_certificates/client/embedding-service.key",
        8443
    )
    print(f"Фабричный mTLS клиент: {client.is_mtls_enabled()}")
    await client.close()


async def example_6_mtls_roles():
    """Пример 6: mTLS + Roles - mTLS с контролем доступа на основе ролей."""
    print("\n=== Пример 6: mTLS + Roles - mTLS с контролем доступа на основе ролей ===")
    
    # Способ 1: Использование словаря конфигурации с ролями
    config_dict = {
        "server": {"host": "https://localhost", "port": 8443},
        "auth": {
            "method": "certificate",
            "certificate": {
                "cert_file": "mtls_certificates/client/embedding-service.crt",
                "key_file": "mtls_certificates/client/embedding-service.key",
                "ca_cert_file": "mtls_certificates/ca/ca.crt"
            }
        },
        "ssl": {
            "enabled": True,
            "verify_mode": "CERT_REQUIRED",
            "check_hostname": True,
            "check_expiry": True,
            "cert_file": "mtls_certificates/client/embedding-service.crt",
            "key_file": "mtls_certificates/client/embedding-service.key",
            "ca_cert_file": "mtls_certificates/ca/ca.crt"
        },
        "roles": ["admin", "user", "embedding-service"],
        "role_attributes": {
            "department": "IT",
            "service": "embedding",
            "permissions": ["read", "write", "embed"]
        }
    }
    
    async with EmbeddingServiceAsyncClient(config_dict=config_dict) as client:
        print(f"Клиент: {client.base_url}:{client.port}")
        print(f"SSL включен: {client.is_ssl_enabled()}")
        print(f"mTLS включен: {client.is_mtls_enabled()}")
        print(f"Аутентификация: {client.is_authenticated()}")
        print(f"Метод аутентификации: {client.get_auth_method()}")
    
    # Способ 2: Использование ClientFactory с ролями
    client = ClientFactory.create_mtls_roles_client(
        "https://localhost",
        "mtls_certificates/client/embedding-service.crt",
        "mtls_certificates/client/embedding-service.key",
        8443,
        roles=["admin", "user"],
        role_attributes={"department": "IT"}
    )
    print(f"Фабричный mTLS+Roles клиент: {client.is_mtls_enabled()}")
    await client.close()


async def example_automatic_detection():
    """Пример: Автоматическое определение режима безопасности."""
    print("\n=== Пример: Автоматическое определение режима безопасности ===")
    
    test_cases = [
        ("http://localhost", None, None, None, None, "HTTP"),
        ("http://localhost", "api_key", None, None, None, "HTTP + Token"),
        ("https://localhost", None, None, None, None, "HTTPS"),
        ("https://localhost", "api_key", None, None, None, "HTTPS + Token"),
        ("https://localhost", None, None, "cert.pem", "key.pem", "mTLS"),
        ("https://localhost", None, None, "cert.pem", "key.pem", "mTLS + Roles", {"roles": ["admin"]}),
    ]
    
    for case in test_cases:
        if len(case) == 6:
            base_url, auth_method, ssl_enabled, cert_file, key_file, expected = case
            kwargs = {}
        else:
            base_url, auth_method, ssl_enabled, cert_file, key_file, expected, kwargs = case
        
        try:
            mode = detect_security_mode(base_url, auth_method, ssl_enabled, cert_file, key_file, **kwargs)
            print(f"  {base_url} + {auth_method or 'none'} + {cert_file or 'no cert'} -> {mode} ({expected})")
        except Exception as e:
            print(f"  Ошибка определения режима для {base_url}: {e}")


async def example_configuration_files():
    """Пример: Использование файлов конфигурации."""
    print("\n=== Пример: Использование файлов конфигурации ===")
    
    # Создание примеров файлов конфигурации
    configs = {
        "http_simple.json": {
            "server": {"host": "http://localhost", "port": 8001},
            "auth": {"method": "none"},
            "ssl": {"enabled": False}
        },
        "https_token.json": {
            "server": {"host": "https://localhost", "port": 8443},
            "auth": {
                "method": "api_key",
                "api_keys": {"user": "your_api_key"}
            },
            "ssl": {
                "enabled": True,
                "verify_mode": "CERT_REQUIRED",
                "check_hostname": True
            }
        },
        "mtls_roles.json": {
            "server": {"host": "https://localhost", "port": 8443},
            "auth": {
                "method": "certificate",
                "certificate": {
                    "cert_file": "mtls_certificates/client/embedding-service.crt",
                    "key_file": "mtls_certificates/client/embedding-service.key",
                    "ca_cert_file": "mtls_certificates/ca/ca.crt"
                }
            },
            "ssl": {
                "enabled": True,
                "verify_mode": "CERT_REQUIRED",
                "check_hostname": True,
                "cert_file": "mtls_certificates/client/embedding-service.crt",
                "key_file": "mtls_certificates/client/embedding-service.key",
                "ca_cert_file": "mtls_certificates/ca/ca.crt"
            },
            "roles": ["admin", "user"],
            "role_attributes": {"department": "IT"}
        }
    }
    
    # Создание директории конфигурации, если она не существует
    os.makedirs("examples/configs", exist_ok=True)
    
    # Сохранение файлов конфигурации
    for filename, config in configs.items():
        filepath = f"examples/configs/{filename}"
        with open(filepath, "w") as f:
            json.dump(config, f, indent=2)
        print(f"Создан: {filepath}")
    
    # Пример: Загрузка конфигурации из файла
    try:
        config = ClientConfig()
        config.load_config_file("examples/configs/http_simple.json")
        
        async with EmbeddingServiceAsyncClient.from_config(config) as client:
            print(f"Загружено из файла: {client.base_url}:{client.port}")
            print(f"Метод аутентификации: {client.get_auth_method()}")
    except Exception as e:
        print(f"Ошибка загрузки файла конфигурации: {e}")


async def example_environment_variables():
    """Пример: Использование переменных окружения."""
    print("\n=== Пример: Использование переменных окружения ===")
    
    # Установка переменных окружения (в реальном использовании они устанавливаются внешне)
    env_vars = {
        "EMBED_CLIENT_BASE_URL": "http://localhost",
        "EMBED_CLIENT_PORT": "8001",
        "EMBED_CLIENT_AUTH_METHOD": "api_key",
        "EMBED_CLIENT_API_KEY": "your_api_key"
    }
    
    # Установка переменных окружения
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"Установлено {key}={value}")
    
    # Создание клиента из переменных окружения
    try:
        client = create_client_from_env()
        print(f"Клиент из окружения: {client.base_url}:{client.port}")
        print(f"Метод аутентификации: {client.get_auth_method()}")
        await client.close()
    except Exception as e:
        print(f"Ошибка создания клиента из окружения: {e}")
    
    # Очистка переменных окружения
    for key in env_vars.keys():
        if key in os.environ:
            del os.environ[key]


async def example_embedding_generation():
    """Пример: Генерация эмбеддингов с различными режимами безопасности."""
    print("\n=== Пример: Генерация эмбеддингов с различными режимами безопасности ===")
    
    texts = ["Привет, мир!", "Это тестовое предложение.", "Сервис эмбеддингов работает!"]
    
    # HTTP режим
    try:
        async with EmbeddingServiceAsyncClient("http://localhost", 8001) as client:
            result = await client.cmd("embed", {"texts": texts})
            if result.get("success"):
                print(f"HTTP режим: Сгенерировано {len(result.get('result', {}).get('data', []))} эмбеддингов")
            else:
                print(f"HTTP режим: Ошибка - {result.get('error')}")
    except Exception as e:
        print(f"Ошибка HTTP режима: {e}")
    
    # API Key режим
    try:
        async with EmbeddingServiceAsyncClient.with_auth(
            "http://localhost", 8001, "api_key", api_key="your_api_key"
        ) as client:
            result = await client.cmd("embed", {"texts": texts})
            if result.get("success"):
                print(f"API Key режим: Сгенерировано {len(result.get('result', {}).get('data', []))} эмбеддингов")
            else:
                print(f"API Key режим: Ошибка - {result.get('error')}")
    except Exception as e:
        print(f"Ошибка API Key режима: {e}")


async def main():
    """Запуск всех примеров."""
    print("🚀 Примеры безопасности embed-client")
    print("=" * 50)
    
    try:
        await example_1_http_plain()
        await example_2_http_token()
        await example_3_https_plain()
        await example_4_https_token()
        await example_5_mtls()
        await example_6_mtls_roles()
        await example_automatic_detection()
        await example_configuration_files()
        await example_environment_variables()
        await example_embedding_generation()
        
        print("\n✅ Все примеры выполнены успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка выполнения примеров: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
