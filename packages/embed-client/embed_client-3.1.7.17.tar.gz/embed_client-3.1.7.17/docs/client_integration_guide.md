Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

## Embedding Service – Client Integration Guide

### 1. Transport & endpoints

**Transport**

- **Protocol**: JSON‑RPC 2.0 over HTTP(S) / mTLS
- **Typical base URL (mTLS in Docker)**: `https://<embedding-service-host>:8001`

**HTTP endpoints**

- `GET /health` – liveness / readiness check
- `POST /api/jsonrpc` – JSON‑RPC endpoint for all commands:
  - `embed`
  - `models`
  - `help`
  - other service commands

**mTLS client certificates (outside Docker)**

Use certificates from `mtls_certificates`:

- **Client certificate / key**:
  - `mtls_certificates/client/embedding-service.crt`
  - `mtls_certificates/client/embedding-service.key`
- **CA certificate**:
  - `mtls_certificates/ca/ca.crt`

When using the `embed-client` library, these paths are passed via the client configuration (`server`, `auth`, `ssl`, `security` sections) and translated into `mcp_proxy_adapter` parameters by the adapter layer.

---

### 2. JSON‑RPC `embed` request

**Endpoint & method**

- **Endpoint**: `POST /api/jsonrpc`
- **JSON‑RPC method**: `embed`

**Example request**

```json
{
  "jsonrpc": "2.0",
  "method": "embed",
  "params": {
    "texts": [
      "This is a test sentence.",
      "Another text to embed."
    ],
    "model": "all-MiniLM-L6-v2",
    "dimension": 384,
    "error_policy": "continue"
  },
  "id": 1
}
```

**Parameters**

- **`texts` (required, `string[]`)**
  - One embedding per element: `texts[i] → result[i]`
- **`model` (optional, `string`)**
  - Explicit model name (e.g. `"all-MiniLM-L6-v2"`)
  - If omitted, the service default model is used
- **`dimension` (optional, `int > 0`)**
  - Expected embedding dimension
  - Must be a positive integer; non‑positive or non‑integer values are rejected
- **`error_policy` (optional, `"fail_fast"` | `"continue"`)**
  - `"fail_fast"` – **legacy behavior**:
    - Any invalid item in the batch → **top‑level JSON‑RPC error**, no partial result
  - `"continue"` – **recommended for new clients**:
    - Top‑level call succeeds
    - For each input `texts[i]`:
      - On success → normal embedding and `error: null`
      - On validation problem → `embedding: null` + per‑item `error` object

> **Recommendation**: For all new batch integrations (SVO chunker, doc‑pipelines, etc.) always send `error_policy: "continue"`.

---

### 3. Success response shape

On success (either with `error_policy = "continue"` or `"fail_fast"` with no validation issues), the response has the following shape:

```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "data": {
      "embeddings": [
        [0.1, 0.2, 0.3, "..."],
        null
      ],
      "results": [
        {
          "body": "This is a test sentence.",
          "embedding": [0.1, 0.2, 0.3, "..."],
          "tokens": ["This", "is", "a", "test", "sentence", "."],
          "bm25_tokens": ["this", "test", "sentence"],
          "error": null
        },
        {
          "body": "   ",
          "embedding": null,
          "tokens": [],
          "bm25_tokens": [],
          "error": {
            "code": "only_special_chars",
            "message": "Text at index 1 contains only special characters"
          }
        }
      ],
      "model": "all-MiniLM-L6-v2",
      "dimension": 384
    }
  },
  "id": 1
}
```

**Positional guarantees**

- `len(data.embeddings) == len(params.texts)`
- `len(data.results)    == len(params.texts)`

Items are **positionally aligned by index**:

- Input: `texts[i]`
- Output:
  - `data.embeddings[i]` – embedding or `null`
  - `data.results[i]` – object with `body`, `embedding`, `tokens`, `bm25_tokens`, `error`

---

### 4. Top‑level error vs per‑item error

#### 4.1. Top‑level JSON‑RPC error (no `data.results`)

Top‑level error means **no embeddings at all**:

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Empty texts list provided"
  },
  "id": 1
}
```

Typical causes:

- Structurally invalid request:
  - `texts` missing or not a list
  - `dimension` non‑positive or not an integer
  - `error_policy` not in `["fail_fast", "continue"]`
- `error_policy = "fail_fast"` and at least one text fails validation

**Client behavior**

- Treat this as “no embeddings at all”
- Abort current operation and surface/log the error

#### 4.2. Per‑item errors (`error_policy = "continue"`)

With `error_policy = "continue"`:

- Top‑level call returns `result.success: true`
- For each `texts[i]`:
  - On success:
    - `embeddings[i]` is a numeric vector (list of floats)
    - `results[i].embedding` is the same vector
    - `results[i].error` is `null`
  - On validation problem:
    - `embeddings[i]` is `null`
    - `results[i].embedding` is `null`
    - `results[i].error` is an object describing the problem

Non‑exhaustive list of `results[i].error.code` values:

- `"too_short"` – empty text / only whitespace
- `"too_long"` – text exceeds max length
- `"only_special_chars"` – no letters/digits (e.g. `"!!!"`)
- `"invalid_characters"` – encoding or character set issues
- `"batch_limit_exceeded"` – batch size exceeds server limit
- `"validation_error"` – other validation issues

---

### 5. Recommended client behavior

#### 5.1. New clients (SVO chunker, doc‑pipelines, etc.)

**Always**:

- Set `error_policy: "continue"` for batch `embed` calls
- Iterate outputs **by index** and inspect per‑item errors:

```python
texts = [...]  # input batch
result = ...   # JSON-RPC result

data = result["result"]["data"]
items = data["results"]

for i, text in enumerate(texts):
    item = items[i]
    err = item["error"]

    if err is None:
        embedding = item["embedding"]
        use_embedding(text, embedding)
    else:
        log_warning(
            f"Embedding error for index {i}: "
            f"{err['code']} - {err['message']}"
        )
        # Decide how to handle:
        # - skip this item
        # - fallback to another model
        # - mark the chunk as invalid
```

**Never**:

- Assume that all `embeddings[i]` are present
- Ignore `item["error"]` when `embedding` is `null`

#### 5.2. Legacy compatibility

If the call returns a **top‑level error** (no `result.data`):

- Behave like old clients:
  - Abort operation
  - Log and surface the error to the caller

#### 5.3. Retry & batching strategy

- Prefer **smaller batches** (e.g. `32–128` items) to:
  - Limit the blast radius of transient infrastructure errors
  - Avoid hitting `batch_limit_exceeded`
- On `batch_limit_exceeded`:
  - Retry with a smaller batch size, or
  - Degrade to single‑item calls for critical items

---

### 6. Using MCP Proxy instead of direct HTTP

In many deployments the Embedding Service is accessed via **MCP Proxy**, not directly.

#### 6.1. Server side

- MCP Proxy exposes an “embedding‑service” server
- The underlying Embedding Service still speaks JSON‑RPC 2.0 on `/api/jsonrpc`
- The `embed` command’s parameters and result shape are **identical** to the direct HTTP JSON‑RPC contract

#### 6.2. Client side with `embed-client`

The `embed-client` library integrates with MCP Proxy via `mcp-proxy-adapter`:

- **Transport**
  - `EmbeddingServiceAsyncClient` uses `mcp_proxy_adapter.client.jsonrpc_client.JsonRpcClient` internally
  - All HTTP(S)/mTLS, authentication and SSL/TLS configuration are delegated to the adapter
- **Configuration**
  - You pass a standard `embed-client` config (JSON/YAML or dict) with `server`, `auth`, `ssl`, `security`, `client` sections
  - `AdapterConfigFactory` converts this config into adapter parameters (`protocol`, `host`, `port`, `token_header`, `token`, `cert`, `key`, `ca`, `check_hostname`, `timeout`)
- **Commands**
  - Low‑level: `await client.cmd("embed", params={...})`
  - The contract for `params` and `result` is exactly the one described above

Even when going through MCP Proxy, client code:

- Must distinguish top‑level errors from per‑item errors
- Must preserve positional mapping between `texts[i]` and `results[i]`

---

### 7. `embed-client` CLI

The project provides a CLI wrapper around `EmbeddingServiceAsyncClient` and the MCP Proxy adapter.

#### 7.1. Installation

```bash
pip install embed-client
```

Installed console scripts:

- `embed-vectorize` – vectorization and service utilities
- `embed-config-generator` – configuration generator for 8 security modes

#### 7.2. Basic vectorization

```bash
# Vectorize text from command line
embed-vectorize vectorize "This is a test sentence." "Another text"

# Vectorize text from file (one text per line)
embed-vectorize vectorize --file texts.txt
```

Internally, the CLI:

- Creates an `EmbeddingServiceAsyncClient` via `ClientFactory` / config
- Calls `client.cmd("embed", params={"texts": [...], "error_policy": "continue"})`
- Uses `response_parsers` to extract embeddings or full embedding data

#### 7.3. Connection & security options

```bash
# HTTP
embed-vectorize --host http://localhost --port 8001 vectorize "hello world"

# HTTPS
embed-vectorize --host https://localhost --port 8443 --ssl vectorize "hello world"

# API key
embed-vectorize --api-key your-api-key vectorize "hello world"

# mTLS
embed-vectorize \
  --ssl \
  --cert-file mtls_certificates/client/embedding-service.crt \
  --key-file  mtls_certificates/client/embedding-service.key \
  --ca-cert-file mtls_certificates/ca/ca.crt \
  vectorize "secure text"
```

CLI fully mirrors the JSON‑RPC semantics:

- Top‑level errors stop the command with a clear error message
- With `error_policy="continue"`, per‑item errors are propagated in the response and can be inspected via `--full-data`

---

### 8. Configuration generator

The `embed-config-generator` CLI generates ready‑to‑use client configs for all 8 security modes:

- `http`
- `http_token`
- `http_token_roles`
- `https`
- `https_token`
- `https_token_roles`
- `mtls`
- `mtls_roles`

#### 8.1. Generate all modes

```bash
embed-config-generator --mode all --output-dir ./configs
```

Produces:

- `http.json`
- `https.json`
- `https_token.json`
- `https_token_roles.json`
- `http_token.json`
- `http_token_roles.json`
- `mtls.json`
- `mtls_roles.json`

#### 8.2. Generate a single mode

```bash
# Simple HTTP
embed-config-generator --mode http --output ./http.json

# HTTP + token
embed-config-generator --mode http_token --api-key your-key --output ./http_token.json
```

These configs can be consumed by `EmbeddingServiceAsyncClient` either via `ClientConfig` (file‑based) or as a config dictionary.

---

### 9. Summary

- Embedding Service exposes a **JSON‑RPC `embed` command** on `/api/jsonrpc`
- Responses provide **positional alignment** between `texts[i]` and `results[i]`
- New clients should **always use `error_policy: "continue"`** and handle per‑item errors
- MCP Proxy and `embed-client` preserve the same contract while hiding transport details
- CLI tools:
  - `embed-vectorize` – quick vectorization and diagnostics
  - `embed-config-generator` – configuration generator for all 8 security modes

