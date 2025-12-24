# Examples

This directory contains comprehensive examples demonstrating all security modes and features of embed-client.

## Files

### Security Examples
- **`security_examples.py`** - Complete examples of all 6 security modes in English
- **`security_examples_ru.py`** - Complete examples of all 6 security modes in Russian

### Configuration Examples
- **`configs/`** - Sample configuration files for different security modes

## Security Modes Demonstrated

### 1. HTTP - Plain HTTP
```python
async with EmbeddingServiceAsyncClient("http://localhost", 8001) as client:
    result = await client.health()
```

### 2. HTTP + Token - HTTP with Authentication
```python
async with EmbeddingServiceAsyncClient.with_auth(
    "http://localhost", 8001, "api_key", api_key="your_api_key"
) as client:
    result = await client.cmd("embed", {"texts": ["Hello, world!"]})
```

### 3. HTTPS - HTTPS with Server Certificate Verification
```python
config_dict = {
    "server": {"host": "https://localhost", "port": 8443},
    "auth": {"method": "none"},
    "ssl": {
        "enabled": True,
        "verify_mode": "CERT_REQUIRED",
        "check_hostname": True
    }
}
async with EmbeddingServiceAsyncClient(config_dict=config_dict) as client:
    result = await client.health()
```

### 4. HTTPS + Token - HTTPS with Authentication
```python
async with EmbeddingServiceAsyncClient.with_auth(
    "https://localhost", 8443, "basic", 
    username="admin", password="secret",
    ssl_enabled=True,
    verify_mode="CERT_REQUIRED"
) as client:
    result = await client.cmd("embed", {"texts": ["Hello, world!"]})
```

### 5. mTLS - Mutual TLS with Certificates
```python
async with EmbeddingServiceAsyncClient.with_auth(
    "https://localhost", 8443, "certificate",
    cert_file="mtls_certificates/client/embedding-service.crt",
    key_file="mtls_certificates/client/embedding-service.key",
    ca_cert_file="mtls_certificates/ca/ca.crt",
    ssl_enabled=True
) as client:
    result = await client.cmd("embed", {"texts": ["Hello, world!"]})
```

### 6. mTLS + Roles - mTLS with Role-Based Access Control
```python
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
        "cert_file": "mtls_certificates/client/embedding-service.crt",
        "key_file": "mtls_certificates/client/embedding-service.key",
        "ca_cert_file": "mtls_certificates/ca/ca.crt"
    },
    "roles": ["admin", "user"],
    "role_attributes": {"department": "IT"}
}
async with EmbeddingServiceAsyncClient(config_dict=config_dict) as client:
    result = await client.cmd("embed", {"texts": ["Hello, world!"]})
```

## Running Examples

### Prerequisites
1. Install embed-client: `pip install embed-client`
2. Ensure you have the required certificates for mTLS examples
3. Make sure the embedding service is running on the specified ports

### Running Security Examples
```bash
# English examples
python examples/security_examples.py

# Russian examples
python examples/security_examples_ru.py
```

### Configuration Files
The examples will automatically create sample configuration files in `examples/configs/`:
- `http_simple.json` - Basic HTTP configuration
- `https_token.json` - HTTPS with API key authentication
- `mtls_roles.json` - mTLS with role-based access control

## Authentication Methods

### API Key Authentication
```python
# Using with_auth method
async with EmbeddingServiceAsyncClient.with_auth(
    "http://localhost", 8001, "api_key", api_key="your_api_key"
) as client:
    pass

# Using configuration
config_dict = {
    "auth": {
        "method": "api_key",
        "api_keys": {"user": "your_api_key"}
    }
}
```

### JWT Authentication
```python
config_dict = {
    "auth": {
        "method": "jwt",
        "jwt": {
            "secret": "your_jwt_secret",
            "username": "admin",
            "password": "secret"
        }
    }
}
```

### Basic Authentication
```python
async with EmbeddingServiceAsyncClient.with_auth(
    "http://localhost", 8001, "basic", 
    username="admin", password="secret"
) as client:
    pass
```

### Certificate Authentication (mTLS)
```python
async with EmbeddingServiceAsyncClient.with_auth(
    "https://localhost", 8443, "certificate",
    cert_file="path/to/client.crt",
    key_file="path/to/client.key",
    ca_cert_file="path/to/ca.crt"
) as client:
    pass
```

## SSL/TLS Configuration

### SSL Verification Modes
- `CERT_NONE` - No certificate verification
- `CERT_OPTIONAL` - Optional certificate verification
- `CERT_REQUIRED` - Required certificate verification

### SSL Configuration Options
```python
ssl_config = {
    "enabled": True,
    "verify_mode": "CERT_REQUIRED",
    "check_hostname": True,
    "check_expiry": True,
    "cert_file": "path/to/client.crt",
    "key_file": "path/to/client.key",
    "ca_cert_file": "path/to/ca.crt"
}
```

## Client Factory Usage

### Automatic Security Mode Detection
```python
from embed_client.client_factory import detect_security_mode

mode = detect_security_mode(
    base_url="https://localhost",
    auth_method="certificate",
    cert_file="client.crt",
    key_file="client.key"
)
print(f"Detected mode: {mode}")
```

### Factory Methods
```python
from embed_client.client_factory import ClientFactory

# HTTP client
client = ClientFactory.create_http_client("http://localhost", 8001)

# HTTPS client
client = ClientFactory.create_https_client("https://localhost", 8443)

# mTLS client
client = ClientFactory.create_mtls_client(
    "https://localhost",
    "client.crt",
    "client.key",
    8443
)
```

## Environment Variables

You can configure the client using environment variables:

```bash
export EMBED_CLIENT_BASE_URL="http://localhost"
export EMBED_CLIENT_PORT="8001"
export EMBED_CLIENT_AUTH_METHOD="api_key"
export EMBED_CLIENT_API_KEY="your_api_key"
```

Then create a client:
```python
from embed_client.client_factory import create_client_from_env

client = create_client_from_env()
```

## Error Handling

All examples include proper error handling:

```python
try:
    async with EmbeddingServiceAsyncClient("http://localhost", 8001) as client:
        result = await client.health()
        print(f"Health: {result}")
except Exception as e:
    print(f"Error: {e}")
```

## Testing

To test the examples against a real server:

1. Start the embedding service on the appropriate ports
2. Update the URLs and ports in the examples to match your setup
3. Ensure you have the correct certificates for mTLS examples
4. Run the examples and verify the output

## Troubleshooting

### Common Issues

1. **Connection Refused**: Check if the embedding service is running
2. **SSL Errors**: Verify certificate paths and SSL configuration
3. **Authentication Errors**: Check API keys, usernames, and passwords
4. **Certificate Errors**: Ensure certificates are valid and properly formatted

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Support

For more information, see:
- Main README.md
- API documentation in docs/
- Test files in tests/
