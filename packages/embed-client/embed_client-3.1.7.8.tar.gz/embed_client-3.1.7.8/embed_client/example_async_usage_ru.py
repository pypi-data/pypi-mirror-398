"""
Пример использования EmbeddingServiceAsyncClient со всеми режимами безопасности и ClientFactory.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Этот пример показывает:
- как собрать конфигурацию из аргументов CLI, файлов и переменных окружения;
- как создавать клиентов для всех режимов безопасности через `ClientFactory`;
- как запускать демонстрационные сценарии в режиме `--demo-mode`.
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Any, Dict

from embed_client.async_client import (
    EmbeddingServiceAsyncClient,
    EmbeddingServiceConfigError,
)
from embed_client.config import ClientConfig
from embed_client.client_factory import ClientFactory, create_client
from embed_client.example_async_usage_ru_demo import (
    run_client_examples,
    demonstrate_security_modes,
    demonstrate_automatic_detection,
)


def get_params() -> Any:
    """Парсинг аргументов командной строки и переменных окружения для конфигурации клиента."""
    parser = argparse.ArgumentParser(
        description="Пример Embedding Service Async Client - Все режимы безопасности"
    )

    # Базовые параметры подключения
    parser.add_argument("--base-url", "-b", help="Базовый URL сервиса эмбеддингов")
    parser.add_argument("--port", "-p", type=int, help="Порт сервиса эмбеддингов")
    parser.add_argument("--config", "-c", help="Путь к файлу конфигурации")

    # Режим фабрики клиентов
    parser.add_argument(
        "--factory-mode",
        choices=[
            "auto",
            "http",
            "http_token",
            "https",
            "https_token",
            "mtls",
            "mtls_roles",
        ],
        default="auto",
        help="Режим фабрики клиентов (auto для автоматического определения)",
    )

    # Параметры аутентификации
    parser.add_argument(
        "--auth-method",
        choices=["none", "api_key", "jwt", "basic", "certificate"],
        default="none",
        help="Метод аутентификации",
    )
    parser.add_argument("--api-key", help="API ключ для аутентификации api_key")
    parser.add_argument("--jwt-secret", help="JWT секрет для аутентификации jwt")
    parser.add_argument(
        "--jwt-username", help="JWT имя пользователя для аутентификации jwt"
    )
    parser.add_argument("--jwt-password", help="JWT пароль для аутентификации jwt")
    parser.add_argument(
        "--username", help="Имя пользователя для базовой аутентификации"
    )
    parser.add_argument("--password", help="Пароль для базовой аутентификации")
    parser.add_argument(
        "--cert-file", help="Файл сертификата для аутентификации certificate"
    )
    parser.add_argument("--key-file", help="Файл ключа для аутентификации certificate")

    # Параметры SSL/TLS
    parser.add_argument(
        "--ssl-verify-mode",
        choices=["CERT_NONE", "CERT_OPTIONAL", "CERT_REQUIRED"],
        default="CERT_REQUIRED",
        help="Режим проверки SSL сертификатов",
    )
    parser.add_argument(
        "--ssl-check-hostname",
        action="store_true",
        default=True,
        help="Включить проверку имени хоста SSL",
    )
    parser.add_argument(
        "--ssl-check-expiry",
        action="store_true",
        default=True,
        help="Включить проверку срока действия SSL сертификатов",
    )
    parser.add_argument("--ca-cert-file", help="Файл CA сертификата для проверки SSL")

    # Контроль доступа на основе ролей (для mTLS + Roles)
    parser.add_argument(
        "--roles", help="Список ролей через запятую для режима mTLS + Roles"
    )
    parser.add_argument(
        "--role-attributes", help="JSON строка атрибутов ролей для режима mTLS + Roles"
    )

    # Дополнительные параметры
    parser.add_argument(
        "--timeout", type=float, default=30.0, help="Таймаут запроса в секундах"
    )
    parser.add_argument(
        "--demo-mode",
        action="store_true",
        help="Запуск в демо режиме (показать все режимы безопасности)",
    )

    args = parser.parse_args()

    # Если предоставлен файл конфигурации, загружаем его
    if args.config:
        try:
            config = ClientConfig()
            config.load_config_file(args.config)
            return config
        except Exception as e:
            print(f"Ошибка загрузки файла конфигурации {args.config}: {e}")
            sys.exit(1)

    # Иначе строим конфигурацию из аргументов и переменных окружения
    base_url = args.base_url or os.environ.get(
        "EMBED_CLIENT_BASE_URL", "http://localhost"
    )
    port = args.port or int(os.environ.get("EMBED_CLIENT_PORT", "8001"))

    if not base_url or not port:
        print(
            "Ошибка: base_url и port должны быть предоставлены через аргументы "
            "--base-url/--port или переменные окружения EMBED_CLIENT_BASE_URL/"
            "EMBED_CLIENT_PORT."
        )
        sys.exit(1)

    # Строим словарь конфигурации
    config_dict: Dict[str, Any] = {
        "server": {"host": base_url, "port": port},
        "client": {"timeout": args.timeout},
        "auth": {"method": args.auth_method},
    }

    # Добавляем конфигурацию аутентификации
    if args.auth_method == "api_key":
        api_key = args.api_key or os.environ.get("EMBED_CLIENT_API_KEY")
        if api_key:
            config_dict["auth"]["api_keys"] = {"user": api_key}
        else:
            print("Предупреждение: API ключ не предоставлен для аутентификации api_key")

    elif args.auth_method == "jwt":
        jwt_secret = args.jwt_secret or os.environ.get("EMBED_CLIENT_JWT_SECRET")
        jwt_username = args.jwt_username or os.environ.get("EMBED_CLIENT_JWT_USERNAME")
        jwt_password = args.jwt_password or os.environ.get("EMBED_CLIENT_JWT_PASSWORD")

        if jwt_secret and jwt_username and jwt_password:
            config_dict["auth"]["jwt"] = {
                "secret": jwt_secret,
                "username": jwt_username,
                "password": jwt_password,
            }
        else:
            print("Предупреждение: JWT учетные данные не полностью предоставлены")

    elif args.auth_method == "basic":
        username = args.username or os.environ.get("EMBED_CLIENT_USERNAME")
        password = args.password or os.environ.get("EMBED_CLIENT_PASSWORD")

        if username and password:
            config_dict["auth"]["basic"] = {"username": username, "password": password}
        else:
            print(
                "Предупреждение: Учетные данные базовой аутентификации не полностью предоставлены"
            )

    elif args.auth_method == "certificate":
        cert_file = args.cert_file or os.environ.get("EMBED_CLIENT_CERT_FILE")
        key_file = args.key_file or os.environ.get("EMBED_CLIENT_KEY_FILE")

        if cert_file and key_file:
            config_dict["auth"]["certificate"] = {
                "cert_file": cert_file,
                "key_file": key_file,
            }
        else:
            print("Предупреждение: Файлы сертификатов не полностью предоставлены")

    # Добавляем конфигурацию SSL если используется HTTPS или предоставлены SSL параметры
    if (
        base_url.startswith("https://")
        or args.ssl_verify_mode != "CERT_REQUIRED"
        or args.ca_cert_file
    ):
        config_dict["ssl"] = {
            "enabled": True,
            "verify_mode": args.ssl_verify_mode,
            "check_hostname": args.ssl_check_hostname,
            "check_expiry": args.ssl_check_expiry,
        }

        if args.ca_cert_file:
            config_dict["ssl"]["ca_cert_file"] = args.ca_cert_file

        # Добавляем клиентские сертификаты для mTLS
        if args.cert_file:
            config_dict["ssl"]["cert_file"] = args.cert_file
        if args.key_file:
            config_dict["ssl"]["key_file"] = args.key_file

    # Добавляем контроль доступа на основе ролей для mTLS + Roles
    if args.roles:
        roles = [role.strip() for role in args.roles.split(",")]
        config_dict["roles"] = roles

    if args.role_attributes:
        try:
            role_attributes = json.loads(args.role_attributes)
            config_dict["role_attributes"] = role_attributes
        except json.JSONDecodeError:
            print("Предупреждение: Неверный JSON в role_attributes")

    return config_dict


async def main():
    try:
        config = get_params()

        # Проверяем, запрошен ли демо режим
        if hasattr(config, "demo_mode") and config.demo_mode:
            await demonstrate_security_modes()
            await demonstrate_automatic_detection()
            return

        # Создаем клиент на основе режима фабрики
        if isinstance(config, ClientConfig):
            # Использование объекта конфигурации
            client = EmbeddingServiceAsyncClient.from_config(config)
        else:
            # Использование словаря конфигурации
            factory_mode = getattr(config, "factory_mode", "auto")

            if factory_mode == "auto":
                # Автоматическое определение
                client = create_client(
                    config["server"]["host"],
                    config["server"]["port"],
                    auth_method=config["auth"]["method"],
                    **{
                        k: v
                        for k, v in config.items()
                        if k not in ["server", "auth", "ssl", "client"]
                    },
                )
            else:
                # Конкретный метод фабрики
                base_url = config["server"]["host"]
                port = config["server"]["port"]
                auth_method = config["auth"]["method"]

                if factory_mode == "http":
                    client = ClientFactory.create_http_client(base_url, port)
                elif factory_mode == "http_token":
                    client = ClientFactory.create_http_token_client(
                        base_url, port, auth_method, **config.get("auth", {})
                    )
                elif factory_mode == "https":
                    client = ClientFactory.create_https_client(base_url, port)
                elif factory_mode == "https_token":
                    client = ClientFactory.create_https_token_client(
                        base_url, port, auth_method, **config.get("auth", {})
                    )
                elif factory_mode == "mtls":
                    cert_file = config.get("ssl", {}).get(
                        "cert_file", "client_cert.pem"
                    )
                    key_file = config.get("ssl", {}).get("key_file", "client_key.pem")
                    client = ClientFactory.create_mtls_client(
                        base_url, cert_file, key_file, port
                    )
                elif factory_mode == "mtls_roles":
                    cert_file = config.get("ssl", {}).get(
                        "cert_file", "client_cert.pem"
                    )
                    key_file = config.get("ssl", {}).get("key_file", "client_key.pem")
                    roles = config.get("roles", ["admin"])
                    role_attributes = config.get("role_attributes", {})
                    client = ClientFactory.create_mtls_roles_client(
                        base_url, cert_file, key_file, port, roles, role_attributes
                    )
                else:
                    client = EmbeddingServiceAsyncClient(config_dict=config)

        print("Конфигурация клиента:")
        print(f"  Базовый URL: {client.base_url}")
        print(f"  Порт: {client.port}")
        print(f"  Аутентификация: {client.get_auth_method()}")
        print(f"  Аутентифицирован: {client.is_authenticated()}")
        if client.is_authenticated():
            headers = client.get_auth_headers()
            print(f"  Заголовки аутентификации: {headers}")
        print(f"  SSL включен: {client.is_ssl_enabled()}")
        print(f"  mTLS включен: {client.is_mtls_enabled()}")
        if client.is_ssl_enabled():
            ssl_config = client.get_ssl_config()
            print(f"  SSL конфигурация: {ssl_config}")
            protocols = client.get_supported_ssl_protocols()
            print(f"  Поддерживаемые SSL протоколы: {protocols}")
        print()

        # Пример явного открытия/закрытия
        print("Пример явного открытия/закрытия сессии:")
        await client.close()
        print("Сессия закрыта явно (пример ручного закрытия).\n")

        # Использование контекстного менеджера
        if isinstance(config, ClientConfig):
            async with EmbeddingServiceAsyncClient.from_config(config) as client:
                await run_client_examples(client)
        else:
            async with EmbeddingServiceAsyncClient(config_dict=config) as client:
                await run_client_examples(client)

    except EmbeddingServiceConfigError as e:
        print(f"Ошибка конфигурации: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
