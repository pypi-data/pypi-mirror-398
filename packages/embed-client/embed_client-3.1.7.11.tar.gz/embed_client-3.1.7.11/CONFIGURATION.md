# Embed-Client Configuration Reference

Complete reference for embed-client configuration structure.

Author: Vasiliy Zdanovskiy  
email: vasilyvz@gmail.com

## Configuration Structure

All embed-client configurations follow a unified structure with all fields present. Fields that are not applicable for a specific security mode are set to `null`.

### Complete Configuration Schema

```json
{
  "server": {
    "host": "string (required, default: 'localhost')",
    "port": "integer (required, default: 8001)",
    "base_url": "string (optional, auto-generated)"
  },
  "client": {
    "timeout": "float (optional, default: 30.0)"
  },
  "protocol": "string (required, one of: 'http', 'https', 'mtls')",
  "auth": {
    "method": "string (required, one of: 'none', 'api_key', 'jwt', 'certificate', 'basic')",
    "api_key": {
      "key": "string (optional, can be null)",
      "header": "string (optional, default: 'X-API-Key')"
    },
    "jwt": {
      "username": "string (optional, required for jwt method)",
      "password": "string (optional, required for jwt method)",
      "secret": "string (optional, required for jwt method)",
      "expiry_hours": "integer (optional, default: 24)"
    },
    "certificate": {
      "enabled": "boolean (required, true for mtls, false otherwise)",
      "cert_file": "string (optional, required for mtls, null for http)",
      "key_file": "string (optional, required for mtls, null for http)",
      "ca_cert_file": "string (optional, required for mtls, null for http)"
    },
    "basic": {
      "username": "string (optional, required for basic method)",
      "password": "string (optional, required for basic method)"
    }
  },
  "ssl": {
    "enabled": "boolean (required, true for https/mtls, false for http)",
    "verify": "boolean (optional, default: true for https/mtls, false for http)",
    "verify_mode": "string (optional, 'CERT_REQUIRED' for mtls, 'CERT_NONE' for https)",
    "check_hostname": "boolean (optional, default: false)",
    "check_expiry": "boolean (optional, default: false)",
    "cert_file": "string (optional, required for mtls, optional for https, null for http)",
    "key_file": "string (optional, required for mtls, optional for https, null for http)",
    "ca_cert_file": "string (optional, required for mtls, optional for https, null for http)",
    "crl_file": "string (optional, can be null for all protocols)",
    "client_cert_required": "boolean (optional, true for mtls, false otherwise)"
  },
  "security": {
    "enabled": "boolean (optional, default: false)",
    "roles_enabled": "boolean (optional, default: false)",
    "roles_file": "string (optional, can be null)",
    "tokens": "object (optional, dictionary of tokens for token-based auth)",
    "roles": "object (optional, dictionary of roles and permissions)"
  },
  "logging": {
    "enabled": "boolean (optional, default: false)",
    "level": "string (optional, default: 'INFO')",
    "format": "string (optional, default log format)"
  },
  "timeout": "integer (optional, default: 30)",
  "retry_attempts": "integer (optional, default: 3)",
  "retry_delay": "integer (optional, default: 1)"
}
```

## Field Requirements by Protocol

### HTTP Protocol

- **protocol**: `"http"` (required)
- **server.host**: Required (default: `"localhost"`)
- **server.port**: Required (default: `8001`)
- **auth.method**: `"none"` or `"api_key"` or `"jwt"` or `"basic"`
- **auth.api_key.key**: Optional (can be `null`)
- **auth.certificate.cert_file**: Must be `null` (not used)
- **auth.certificate.key_file**: Must be `null` (not used)
- **auth.certificate.ca_cert_file**: Must be `null` (not used)
- **ssl.enabled**: `false` (required)
- **ssl.cert_file**: Must be `null` (not used)
- **ssl.key_file**: Must be `null` (not used)
- **ssl.ca_cert_file**: Must be `null` (not used)
- **ssl.crl_file**: Optional (can be `null`)

### HTTPS Protocol

- **protocol**: `"https"` (required)
- **server.host**: Required (default: `"localhost"`)
- **server.port**: Required (default: `8001`)
- **auth.method**: `"none"` or `"api_key"` or `"jwt"` or `"basic"`
- **auth.api_key.key**: Optional (can be `null`)
- **auth.certificate.cert_file**: Optional (can be `null`)
- **auth.certificate.key_file**: Optional (can be `null`)
- **auth.certificate.ca_cert_file**: Optional (can be `null`)
- **ssl.enabled**: `true` (required)
- **ssl.cert_file**: Optional (can be `null`)
- **ssl.key_file**: Optional (can be `null`)
- **ssl.ca_cert_file**: Optional (can be `null`)
- **ssl.crl_file**: Optional (can be `null`)

### mTLS Protocol

- **protocol**: `"mtls"` (required)
- **server.host**: Required (default: `"localhost"`)
- **server.port**: Required (default: `8001`)
- **auth.method**: `"certificate"` (required)
- **auth.api_key.key**: Optional (can be `null`, not used for mTLS auth)
- **auth.certificate.cert_file**: **Required** (must be provided)
- **auth.certificate.key_file**: **Required** (must be provided)
- **auth.certificate.ca_cert_file**: **Required** (must be provided)
- **ssl.enabled**: `true` (required)
- **ssl.cert_file**: **Required** (must be provided)
- **ssl.key_file**: **Required** (must be provided)
- **ssl.ca_cert_file**: **Required** (must be provided)
- **ssl.crl_file**: Optional (can be `null`)
- **ssl.client_cert_required**: `true` (required)

## Configuration Examples

### HTTP Configuration

```json
{
  "server": {
    "host": "localhost",
    "port": 8001
  },
  "protocol": "http",
  "auth": {
    "method": "none",
    "api_key": {
      "key": null
    },
    "certificate": {
      "enabled": false,
      "cert_file": null,
      "key_file": null,
      "ca_cert_file": null
    }
  },
  "ssl": {
    "enabled": false,
    "cert_file": null,
    "key_file": null,
    "ca_cert_file": null,
    "crl_file": null
  }
}
```

### HTTPS with Token Configuration

```json
{
  "server": {
    "host": "localhost",
    "port": 8443
  },
  "protocol": "https",
  "auth": {
    "method": "api_key",
    "api_key": {
      "key": "your-api-key-here"
    },
    "certificate": {
      "enabled": false,
      "cert_file": null,
      "key_file": null,
      "ca_cert_file": null
    }
  },
  "ssl": {
    "enabled": true,
    "verify_mode": "CERT_NONE",
    "cert_file": "/path/to/cert.crt",
    "key_file": null,
    "ca_cert_file": "/path/to/ca.crt",
    "crl_file": null
  }
}
```

### mTLS Configuration

```json
{
  "server": {
    "host": "localhost",
    "port": 8443
  },
  "protocol": "mtls",
  "auth": {
    "method": "certificate",
    "api_key": {
      "key": null
    },
    "certificate": {
      "enabled": true,
      "cert_file": "/path/to/client.crt",
      "key_file": "/path/to/client.key",
      "ca_cert_file": "/path/to/ca.crt"
    }
  },
  "ssl": {
    "enabled": true,
    "verify_mode": "CERT_REQUIRED",
    "cert_file": "/path/to/client.crt",
    "key_file": "/path/to/client.key",
    "ca_cert_file": "/path/to/ca.crt",
    "crl_file": "/path/to/crl.pem",
    "client_cert_required": true
  }
}
```

## Default Values

When creating a configuration, the following default values are used if not specified:

- **server.host**: `"localhost"`
- **server.port**: `8001`
- **client.timeout**: `30.0`
- **protocol**: Determined by SSL settings (`"http"`, `"https"`, or `"mtls"`)
- **auth.method**: `"none"`
- **auth.api_key.key**: `null`
- **auth.certificate.enabled**: `false` (except for mTLS where it's `true`)
- **ssl.enabled**: `false` (except for HTTPS/mTLS where it's `true`)
- **ssl.crl_file**: `null` (optional for all protocols)

## Field Semantics

### Protocol Field

The `protocol` field is **always present** in all configurations and indicates the transport protocol:
- `"http"`: Plain HTTP without encryption
- `"https"`: HTTPS with server certificate verification
- `"mtls"`: Mutual TLS with client and server certificates

### Token Field

The `auth.api_key.key` field is **always present** but can be `null`:
- For HTTP/HTTPS with token authentication: contains the API key
- For HTTP/HTTPS without authentication: `null`
- For mTLS: `null` (certificate-based authentication is used)

### Certificate Fields

Certificate fields behavior:
- **For HTTP**: All certificate fields (`cert_file`, `key_file`, `ca_cert_file`) must be `null`
- **For HTTPS**: Certificate fields are optional (can be `null` or provided)
- **For mTLS**: Certificate fields are **required** and must be provided

### CRL Field

The `ssl.crl_file` field is **always present** but optional:
- Can be `null` for all protocols
- If provided, must point to a valid Certificate Revocation List file
- Used for checking if certificates have been revoked

## Configuration Generator

Use `embed-config-generator` CLI tool to generate configurations:

```bash
# Generate HTTP config
embed-config-generator --mode http --host localhost --port 8001 --output config.json

# Generate HTTPS config with certificates
embed-config-generator --mode https --host localhost --port 8443 \
  --cert-file /path/to/cert.crt --ca-cert-file /path/to/ca.crt --output config.json

# Generate mTLS config with all certificates and CRL
embed-config-generator --mode mtls --host localhost --port 8443 \
  --cert-file /path/to/client.crt --key-file /path/to/client.key \
  --ca-cert-file /path/to/ca.crt --crl-file /path/to/crl.pem --output config.json
```

## Configuration Validator

Use `embed-config-validator` CLI tool to validate configurations:

```bash
# Validate single config
embed-config-validator --file config.json

# Validate all configs in directory
embed-config-validator --dir ./configs --verbose
```

## Integration with Server

When embedding the client into a server, create a separate configuration section:

```json
{
  "server": {
    "host": "localhost",
    "port": 8001
  },
  "embed_client": {
    "protocol": "mtls",
    "server": {
      "host": "embedding-service.example.com",
      "port": 8443
    },
    "auth": {
      "method": "certificate",
      "certificate": {
        "enabled": true,
        "cert_file": "/path/to/client.crt",
        "key_file": "/path/to/client.key",
        "ca_cert_file": "/path/to/ca.crt"
      }
    },
    "ssl": {
      "enabled": true,
      "cert_file": "/path/to/client.crt",
      "key_file": "/path/to/client.key",
      "ca_cert_file": "/path/to/ca.crt",
      "crl_file": "/path/to/crl.pem"
    }
  }
}
```

This allows the server to have its own configuration while the client has a separate, validated configuration section.

