# MCP Proxy Adapter

**Author:** Vasiliy Zdanovskiy  
**Email:** vasilyvz@gmail.com

## Overview

MCP Proxy Adapter is a comprehensive framework for building JSON-RPC API servers with built-in security, SSL/TLS support, and proxy registration capabilities. It provides a unified interface for command execution, protocol management, and security enforcement.

## Features

- **JSON-RPC API**: Full JSON-RPC 2.0 support with built-in commands
- **Security Framework**: Integrated authentication, authorization, and SSL/TLS
- **Protocol Management**: HTTP, HTTPS, and mTLS protocol support
- **Proxy Registration**: Automatic registration with proxy servers
- **Command System**: Extensible command registry with built-in commands
- **Configuration Management**: Comprehensive configuration with environment variable overrides
- **Queue-Backed Commands**: Fire-and-forget execution for long-running operations (NLP pipelines, ML inference, etc.)
  - HTTP layer returns `job_id` immediately without blocking
  - Heavy processing runs in separate worker processes
  - Client polls job status independently without HTTP timeout constraints
  - Supports operations that take minutes or hours to complete

## Quick Start

1. **Installation**:
   ```bash
   pip install mcp-proxy-adapter
   ```

2. **Generate Configuration**:
   ```bash
   # Generate a simple HTTP configuration
   adapter-cfg-gen --protocol http --out config.json
   
   # Generate HTTPS configuration with proxy registration
   adapter-cfg-gen --protocol https --with-proxy --out config.json
   
   # Generate mTLS configuration with custom certificates
   adapter-cfg-gen --protocol mtls \
     --server-cert-file ./certs/server.crt \
     --server-key-file ./certs/server.key \
     --server-ca-cert-file ./certs/ca.crt \
     --out config.json
   ```

3. **Validate Configuration**:
   ```bash
   # Validate configuration file
   adapter-cfg-val --file config.json
   ```

4. **Start Server**:
   ```bash
   # Use the generated configuration
   python -m mcp_proxy_adapter --config config.json
   # Or use the main CLI
   mcp-proxy-adapter config validate --file config.json
   mcp-proxy-adapter server --config config.json
   ```

5. **Access the API**:
   - Health check: `GET http://localhost:8000/health`
   - JSON-RPC: `POST http://localhost:8000/api/jsonrpc`
   - REST API: `POST http://localhost:8000/cmd`
   - Documentation: `http://localhost:8000/docs`

## Queue-Backed Commands (Fire-and-Forget Execution)

Starting from version 6.9.96+, mcp-proxy-adapter supports **fire-and-forget execution** for queue-backed commands. This enables reliable handling of long-running operations (NLP pipelines, ML inference, data processing, etc.) without HTTP timeout constraints.

### How It Works

1. **Client submits command** via JSON-RPC or REST API
2. **Server enqueues job** and returns `job_id` immediately (typically < 1 second)
3. **Heavy processing** runs inside a separate queue worker process
4. **Client polls job status** independently using `queue_get_job_status(job_id)`
5. **No HTTP timeout issues** - the initial request completes quickly, and polling uses separate requests

### Client Usage Example

```python
import asyncio
from mcp_proxy_adapter.client.jsonrpc_client.client import JsonRpcClient

async def main():
    # For mTLS or slow networks, increase HTTP timeout
    client = JsonRpcClient(
        protocol="mtls",
        host="127.0.0.1",
        port=8080,
        cert="/path/to/cert.crt",
        key="/path/to/key.key",
        ca="/path/to/ca.crt",
        timeout=60.0,  # HTTP client timeout: 60 seconds (default: 30.0)
    )
    
    try:
        # Execute queue-backed command with automatic polling
        result = await client.execute_command_unified(
            command="chunk",  # Your long-running command
            params={"text": "Very long text...", "window": 3},
            auto_poll=True,      # Automatically poll until completion
            poll_interval=1.0,   # Check status every 1 second
            timeout=600.0,       # Overall timeout: 10 minutes
        )
        
        print(f"Job completed: {result['status']}")
        print(f"Result: {result['result']}")
        
    except TimeoutError:
        print("Job did not complete within timeout")
    finally:
        await client.close()

asyncio.run(main())
```

**Note:** The `timeout` parameter in `JsonRpcClient` controls the HTTP client timeout for all requests (including status polling). For mTLS connections or slow networks, you may need to increase this value. You can also set it via the `MCP_PROXY_ADAPTER_HTTP_TIMEOUT` environment variable.

### HTTP Timeout Configuration

The HTTP client timeout can be configured in three ways (in order of precedence):

1. **Constructor parameter** (highest priority):
   ```python
   client = JsonRpcClient(timeout=60.0)  # 60 seconds
   ```

2. **Environment variable**:
   ```bash
   export MCP_PROXY_ADAPTER_HTTP_TIMEOUT=60.0
   ```

3. **Default value**: 30.0 seconds (if neither parameter nor environment variable is set)

This timeout applies to all HTTP requests including:
- Command execution
- Status polling (`queue_get_job_status`)
- Health checks
- Proxy registration

For mTLS connections or slow networks, consider increasing the timeout to avoid `httpx.ReadTimeout` errors.

### Server-Side Command Definition

To enable queue execution for a command, set `use_queue = True`:

```python
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult

class ChunkCommand(Command):
    """Example: Long-running NLP chunking command."""
    
    name = "chunk"
    descr = "Chunk long text into smaller pieces"
    use_queue = True  # CRITICAL: Enable queue execution
    
    @classmethod
    def get_schema(cls):
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "window": {"type": "integer", "default": 3},
            },
            "required": ["text"],
        }
    
    async def execute(self, text: str, window: int = 3, **kwargs):
        # Heavy processing happens here
        # This runs in a separate process, not in HTTP handler
        chunks = process_text(text, window)
        return SuccessResult(data={"chunks": chunks})
```

### Advanced Features

- **Manual Polling**: Get `job_id` immediately and poll status manually
- **Progress Hooks**: Receive progress updates via callback functions
- **Parallel Execution**: Submit multiple commands and poll them concurrently
- **Error Handling**: Proper handling of job failures, timeouts, and network errors

For detailed examples, see:
- `mcp_proxy_adapter/examples/queue_fire_and_forget_example.py`
- `mcp_proxy_adapter/examples/queue_integration_example.py`

### Requirements

- `mcp-proxy-adapter >= 6.9.96`
- `queuemgr >= 1.0.13` (for configurable control-plane timeouts and `start_job_background` support)

## Configuration

The adapter uses a comprehensive JSON configuration file (`config.json`) that includes all available options. **All features are disabled by default** and must be explicitly enabled. The configuration system has **NO default values** - all configuration must be explicitly specified.

### Configuration Sections

#### 1. `uuid` (Root Level)
**Type**: `string` (UUID4 format)  
**Required**: YES  
**Description**: Unique identifier for the server instance  
**Format**: `xxxxxxxx-xxxx-4xxx-xxxx-xxxxxxxxxxxx`

```json
{
  "uuid": "123e4567-e89b-42d3-a456-426614174000"
}
```

#### 2. `server` Section
**Required**: YES  
**Description**: Core server configuration settings

| Field | Type | Required | Description | Allowed Values |
|-------|------|----------|-------------|----------------|
| `host` | string | YES | Server host address | Any valid IP or hostname |
| `port` | integer | YES | Server port number | 1-65535 |
| `protocol` | string | YES | Server protocol | `"http"`, `"https"`, `"mtls"` |
| `debug` | boolean | YES | Enable debug mode | `true`, `false` |
| `log_level` | string | YES | Logging level | `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"` |

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "protocol": "http",
    "debug": false,
    "log_level": "INFO"
  }
}
```

#### 3. `logging` Section
**Required**: YES  
**Description**: Logging configuration settings

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `level` | string | YES | Log level (`"INFO"`, `"DEBUG"`, `"WARNING"`, `"ERROR"`) |
| `log_dir` | string | YES | Directory for log files |
| `log_file` | string | YES | Main log file name |
| `error_log_file` | string | YES | Error log file name |
| `access_log_file` | string | YES | Access log file name |
| `max_file_size` | string/integer | YES | Maximum log file size (`"10MB"` or `10485760`) |
| `backup_count` | integer | YES | Number of backup log files |
| `format` | string | YES | Log message format (Python logging format string) |
| `date_format` | string | YES | Date format for logs |
| `console_output` | boolean | YES | Enable console logging |
| `file_output` | boolean | YES | Enable file logging |

```json
{
  "logging": {
    "level": "INFO",
    "log_dir": "./logs",
    "log_file": "mcp_proxy_adapter.log",
    "error_log_file": "mcp_proxy_adapter_error.log",
    "access_log_file": "mcp_proxy_adapter_access.log",
    "max_file_size": "10MB",
    "backup_count": 5,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "console_output": true,
    "file_output": true
  }
}
```

#### 4. `commands` Section
**Required**: YES  
**Description**: Command management configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `auto_discovery` | boolean | YES | Enable automatic command discovery |
| `commands_directory` | string | YES | Directory for command files |
| `catalog_directory` | string | YES | Directory for command catalog |
| `plugin_servers` | array | YES | List of plugin server URLs |
| `auto_install_dependencies` | boolean | YES | Auto-install command dependencies |
| `enabled_commands` | array | YES | List of enabled commands |
| `disabled_commands` | array | YES | List of disabled commands |
| `custom_commands_path` | string | YES | Path to custom commands |

```json
{
  "commands": {
    "auto_discovery": true,
    "commands_directory": "./commands",
    "catalog_directory": "./catalog",
    "plugin_servers": [],
    "auto_install_dependencies": true,
    "enabled_commands": ["health", "echo", "help"],
    "disabled_commands": [],
    "custom_commands_path": "./commands"
  }
}
```

#### 5. `transport` Section
**Required**: YES  
**Description**: Transport layer configuration

| Field | Type | Required | Description | Allowed Values |
|-------|------|----------|-------------|----------------|
| `type` | string | YES | Transport type | `"http"`, `"https"`, `"mtls"` |
| `port` | integer/null | YES | Transport port (can be null) | 1-65535 or `null` |
| `verify_client` | boolean | YES | Enable client certificate verification | `true`, `false` |
| `chk_hostname` | boolean | YES | Enable hostname checking | `true`, `false` |

**Nested Section**: `transport.ssl` (when SSL/TLS is enabled)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `enabled` | boolean | Conditional | Enable SSL/TLS |
| `cert_file` | string | Conditional | Path to SSL certificate file |
| `key_file` | string | Conditional | Path to SSL private key file |
| `ca_cert` | string | Optional | Path to CA certificate file |
| `verify_client` | boolean | Optional | Verify client certificates |
| `verify_ssl` | boolean | Optional | Verify SSL certificates |
| `verify_hostname` | boolean | Optional | Verify hostname in certificate |
| `verify_mode` | string | Optional | SSL verification mode: `"CERT_NONE"`, `"CERT_OPTIONAL"`, `"CERT_REQUIRED"` |

```json
{
  "transport": {
    "type": "https",
    "port": 8443,
    "verify_client": false,
    "chk_hostname": true,
    "ssl": {
      "enabled": true,
      "cert_file": "./certs/server.crt",
      "key_file": "./certs/server.key",
      "ca_cert": "./certs/ca.crt",
      "verify_ssl": true,
      "verify_hostname": true,
      "verify_mode": "CERT_REQUIRED"
    }
  }
}
```

#### 6. `ssl` Section (Root Level)
**Required**: Conditional (required for HTTPS/mTLS protocols)  
**Description**: SSL/TLS configuration for server

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `enabled` | boolean | YES | Enable SSL/TLS |
| `cert_file` | string | YES | Path to SSL certificate file |
| `key_file` | string | YES | Path to SSL private key file |
| `ca_cert` | string | Optional | Path to CA certificate file (required for mTLS) |

```json
{
  "ssl": {
    "enabled": true,
    "cert_file": "./certs/server.crt",
    "key_file": "./certs/server.key",
    "ca_cert": "./certs/ca.crt"
  }
}
```

#### 7. `proxy_registration` Section
**Required**: YES  
**Description**: Proxy server registration configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `enabled` | boolean | YES | Enable proxy registration |
| `proxy_url` | string | YES | Proxy server URL |
| `server_id` | string | YES | Unique server identifier |
| `server_name` | string | YES | Human-readable server name |
| `description` | string | YES | Server description |
| `version` | string | YES | Server version |
| `protocol` | string | Conditional | Registration protocol: `"http"`, `"https"`, `"mtls"` |
| `registration_timeout` | integer | YES | Registration timeout in seconds |
| `retry_attempts` | integer | YES | Number of retry attempts |
| `retry_delay` | integer | YES | Delay between retries in seconds |
| `auto_register_on_startup` | boolean | YES | Auto-register on startup |
| `auto_unregister_on_shutdown` | boolean | YES | Auto-unregister on shutdown |
| `uuid` | string | Optional | UUID for registration (UUID4 format) |

**Nested Section**: `proxy_registration.ssl` (when using HTTPS/mTLS)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `enabled` | boolean | Conditional | Enable SSL for registration |
| `verify_ssl` | boolean | Conditional | Verify proxy SSL certificate |
| `verify_hostname` | boolean | Conditional | Verify proxy hostname |
| `verify_mode` | string | Conditional | SSL verification mode |
| `ca_cert` | string | Conditional | Path to CA certificate |
| `cert_file` | string | Conditional | Path to client certificate (for mTLS) |
| `key_file` | string | Conditional | Path to client key (for mTLS) |

**Nested Section**: `proxy_registration.heartbeat`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `enabled` | boolean | Optional | Enable heartbeat |
| `interval` | integer | Optional | Heartbeat interval in seconds |
| `timeout` | integer | Optional | Heartbeat timeout in seconds |
| `retry_attempts` | integer | Optional | Number of retry attempts |
| `retry_delay` | integer | Optional | Delay between retries |
| `url` | string | Optional | Heartbeat endpoint URL |

```json
{
  "proxy_registration": {
    "enabled": true,
    "proxy_url": "https://proxy.example.com:3005",
    "server_id": "my-server-001",
    "server_name": "My MCP Server",
    "description": "Production MCP server",
    "version": "1.0.0",
    "protocol": "mtls",
    "registration_timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 5,
    "auto_register_on_startup": true,
    "auto_unregister_on_shutdown": true,
    "ssl": {
      "enabled": true,
      "verify_ssl": true,
      "verify_hostname": false,
      "verify_mode": "CERT_REQUIRED",
      "ca_cert": "./certs/ca.crt",
      "cert_file": "./certs/client.crt",
      "key_file": "./certs/client.key"
    },
    "heartbeat": {
      "enabled": true,
      "interval": 30,
      "timeout": 10,
      "retry_attempts": 3,
      "retry_delay": 5,
      "url": "/heartbeat"
    }
  }
}
```

#### 8. `security` Section
**Required**: YES  
**Description**: Security framework configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `enabled` | boolean | YES | Enable security framework |
| `tokens` | object | YES | Token-based authentication configuration |
| `roles` | object | YES | Role-based access control configuration |
| `roles_file` | string/null | YES | Path to roles configuration file |

**Nested Section**: `security.tokens`

| Field | Type | Description |
|-------|------|-------------|
| `admin` | string | Administrator token |
| `user` | string | User token |
| `readonly` | string | Read-only token |
| *(custom)* | string | Custom token names |

**Nested Section**: `security.roles`

| Field | Type | Description |
|-------|------|-------------|
| `admin` | array | Administrator role permissions |
| `user` | array | User role permissions |
| `readonly` | array | Read-only role permissions |
| *(custom)* | array | Custom role names |

```json
{
  "security": {
    "enabled": true,
    "tokens": {
      "admin": "admin-secret-key",
      "user": "user-secret-key",
      "readonly": "readonly-secret-key"
    },
    "roles": {
      "admin": ["*"],
      "user": ["health", "echo"],
      "readonly": ["health"]
    },
    "roles_file": null
  }
}
```

#### 9. `roles` Section
**Required**: YES  
**Description**: Role-based access control configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `enabled` | boolean | YES | Enable RBAC |
| `config_file` | string/null | YES | Path to roles configuration file |
| `default_policy` | object | YES | Default policy settings |
| `auto_load` | boolean | YES | Auto-load roles on startup |
| `validation_enabled` | boolean | YES | Enable role validation |

**Nested Section**: `roles.default_policy`

| Field | Type | Description |
|-------|------|-------------|
| `deny_by_default` | boolean | Deny access by default |
| `require_role_match` | boolean | Require exact role match |
| `case_sensitive` | boolean | Case-sensitive role matching |
| `allow_wildcard` | boolean | Allow wildcard permissions |

```json
{
  "roles": {
    "enabled": false,
    "config_file": null,
    "default_policy": {
      "deny_by_default": true,
      "require_role_match": true,
      "case_sensitive": false,
      "allow_wildcard": true
    },
    "auto_load": true,
    "validation_enabled": true
  }
}
```

#### 10. `debug` Section
**Required**: YES  
**Description**: Debug mode configuration

| Field | Type | Required | Description | Allowed Values |
|-------|------|----------|-------------|----------------|
| `enabled` | boolean | YES | Enable debug mode | `true`, `false` |
| `level` | string | YES | Debug level | `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"` |

```json
{
  "debug": {
    "enabled": false,
    "level": "WARNING"
  }
}
```

### Protocol-Specific Requirements

#### HTTP Protocol
**Required Sections**: `server`, `logging`, `commands`, `transport`, `debug`, `security`, `roles`  
**SSL Required**: NO  
**Client Verification**: NO

#### HTTPS Protocol
**Required Sections**: All sections + `ssl`  
**SSL Required**: YES  
**Client Verification**: NO  
**Required Files**: 
- `ssl.cert_file` - Server certificate
- `ssl.key_file` - Server private key

#### mTLS Protocol
**Required Sections**: All sections + `ssl`  
**SSL Required**: YES  
**Client Verification**: YES  
**Required Files**: 
- `ssl.cert_file` - Server certificate
- `ssl.key_file` - Server private key
- `ssl.ca_cert` - CA certificate for client verification

### Configuration Validation

The framework automatically validates configuration on load:
- **Required sections**: All mandatory configuration sections are present
- **Required keys**: All required keys within sections are present
- **Type validation**: All values have correct data types
- **File existence**: All referenced files exist (when features are enabled)
- **Feature dependencies**: All feature dependencies are satisfied
- **UUID format**: UUID4 format validation
- **Certificate validation**: Certificate format, expiration, key matching

### Complete Configuration Example

```json
{
  "uuid": "123e4567-e89b-42d3-a456-426614174000",
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "protocol": "mtls",
    "debug": false,
    "log_level": "INFO"
  },
  "logging": {
    "level": "INFO",
    "log_dir": "./logs",
    "log_file": "mcp_proxy_adapter.log",
    "error_log_file": "mcp_proxy_adapter_error.log",
    "access_log_file": "mcp_proxy_adapter_access.log",
    "max_file_size": "10MB",
    "backup_count": 5,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "console_output": true,
    "file_output": true
  },
  "commands": {
    "auto_discovery": true,
    "commands_directory": "./commands",
    "catalog_directory": "./catalog",
    "plugin_servers": [],
    "auto_install_dependencies": true,
    "enabled_commands": ["health", "echo", "help"],
    "disabled_commands": [],
    "custom_commands_path": "./commands"
  },
  "transport": {
    "type": "mtls",
    "port": 8443,
    "verify_client": true,
    "chk_hostname": true,
    "ssl": {
      "enabled": true,
      "cert_file": "./certs/server.crt",
      "key_file": "./certs/server.key",
      "ca_cert": "./certs/ca.crt",
      "verify_ssl": true,
      "verify_hostname": true,
      "verify_mode": "CERT_REQUIRED"
    }
  },
  "ssl": {
    "enabled": true,
    "cert_file": "./certs/server.crt",
    "key_file": "./certs/server.key",
    "ca_cert": "./certs/ca.crt"
  },
  "proxy_registration": {
    "enabled": true,
    "proxy_url": "https://proxy.example.com:3005",
    "server_id": "my-server-001",
    "server_name": "My MCP Server",
    "description": "Production MCP server",
    "version": "1.0.0",
    "protocol": "mtls",
    "registration_timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 5,
    "auto_register_on_startup": true,
    "auto_unregister_on_shutdown": true,
    "ssl": {
      "enabled": true,
      "verify_ssl": true,
      "verify_hostname": false,
      "verify_mode": "CERT_REQUIRED",
      "ca_cert": "./certs/ca.crt",
      "cert_file": "./certs/client.crt",
      "key_file": "./certs/client.key"
    },
    "heartbeat": {
      "enabled": true,
      "interval": 30,
      "timeout": 10,
      "retry_attempts": 3,
      "retry_delay": 5,
      "url": "/heartbeat"
    }
  },
  "debug": {
    "enabled": false,
    "level": "WARNING"
  },
  "security": {
    "enabled": true,
    "tokens": {
      "admin": "admin-secret-key",
      "user": "user-secret-key",
      "readonly": "readonly-secret-key"
    },
    "roles": {
      "admin": ["*"],
      "user": ["health", "echo"],
      "readonly": ["health"]
    },
    "roles_file": null
  },
  "roles": {
    "enabled": false,
    "config_file": null,
    "default_policy": {
      "deny_by_default": true,
      "require_role_match": true,
      "case_sensitive": false,
      "allow_wildcard": true
    },
    "auto_load": true,
    "validation_enabled": true
  }
}
```

For more detailed configuration documentation, see `docs/EN/ALL_CONFIG_SETTINGS.md`.

### SimpleConfig Format

The framework supports a simplified configuration format (`SimpleConfig`) that provides a minimal, explicit configuration model with three main sections: **server**, **client**, and **registration**. Each section can operate independently with its own protocol (HTTP, HTTPS, or mTLS), certificates, keys, and CRL (Certificate Revocation List).

#### SimpleConfig Structure

```json
{
  "server": { ... },
  "client": { ... },
  "registration": { ... },
  "auth": { ... }
}
```

#### 1. `server` Section

**Purpose**: Server endpoint configuration (listening for incoming connections)

| Field | Type | Required | Description | Allowed Values |
|-------|------|----------|-------------|----------------|
| `host` | string | YES | Server host address | Any valid IP or hostname |
| `port` | integer | YES | Server port number | 1-65535 |
| `protocol` | string | YES | Server protocol | `"http"`, `"https"`, `"mtls"` |
| `cert_file` | string | Conditional | Server certificate file path | Valid file path (required for HTTPS/mTLS) |
| `key_file` | string | Conditional | Server private key file path | Valid file path (required for HTTPS/mTLS) |
| `ca_cert_file` | string | Conditional | CA certificate file path | Valid file path (required for mTLS if `use_system_ca=false`) |
| `crl_file` | string | Optional | Certificate Revocation List file path | Valid CRL file path |
| `use_system_ca` | boolean | NO | Allow system CA store when `ca_cert_file` is not provided | `true`, `false` (default: `false`) |
| `log_dir` | string | NO | Directory for log files | Valid directory path (default: `"./logs"`) |

**Protocol Requirements**:
- **HTTP**: No certificates required
- **HTTPS**: `cert_file` and `key_file` are optional but recommended. If one is specified, both must be provided.
- **mTLS**: `cert_file` and `key_file` are required. `ca_cert_file` is required if `use_system_ca=false` (default).

**CRL Validation**:
- If `crl_file` is specified, it must:
  - Exist and be accessible
  - Be a valid CRL file format (PEM or DER)
  - Not be expired (checked against `next_update` field)
  - Pass format validation
- If CRL validation fails, the server will log an error and stop

**Example**:
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "protocol": "mtls",
    "cert_file": "./certs/server.crt",
    "key_file": "./certs/server.key",
    "ca_cert_file": "./certs/ca.crt",
    "crl_file": "./certs/server.crl",
    "use_system_ca": false,
    "log_dir": "./logs"
  }
}
```

#### 2. `client` Section

**Purpose**: Client configuration (for connecting to external servers)

| Field | Type | Required | Description | Allowed Values |
|-------|------|----------|-------------|----------------|
| `enabled` | boolean | NO | Enable client configuration | `true`, `false` (default: `false`) |
| `protocol` | string | Conditional | Client protocol | `"http"`, `"https"`, `"mtls"` (default: `"http"`) |
| `cert_file` | string | Conditional | Client certificate file path | Valid file path (required for mTLS when enabled) |
| `key_file` | string | Conditional | Client private key file path | Valid file path (required for mTLS when enabled) |
| `ca_cert_file` | string | Conditional | CA certificate file path | Valid file path (required for mTLS if `use_system_ca=false`) |
| `crl_file` | string | Optional | Certificate Revocation List file path | Valid CRL file path |
| `use_system_ca` | boolean | NO | Allow system CA store when `ca_cert_file` is not provided | `true`, `false` (default: `false`) |

**Protocol Requirements**:
- **HTTP**: No certificates required
- **HTTPS**: `cert_file` and `key_file` are optional but recommended. If one is specified, both must be provided.
- **mTLS**: `cert_file` and `key_file` are required when `enabled=true`. `ca_cert_file` is required if `use_system_ca=false` (default).

**CRL Validation**:
- Same validation rules as `server` section
- If `crl_file` is specified and validation fails, the client connection will fail

**Example**:
```json
{
  "client": {
    "enabled": true,
    "protocol": "mtls",
    "cert_file": "./certs/client.crt",
    "key_file": "./certs/client.key",
    "ca_cert_file": "./certs/ca.crt",
    "crl_file": "./certs/client.crl",
    "use_system_ca": false
  }
}
```

#### 3. `registration` Section

**Purpose**: Proxy registration configuration (for registering with proxy server)

| Field | Type | Required | Description | Allowed Values |
|-------|------|----------|-------------|----------------|
| `enabled` | boolean | NO | Enable proxy registration | `true`, `false` (default: `false`) |
| `host` | string | Conditional | Proxy server host | Valid hostname or IP (required when enabled) |
| `port` | integer | Conditional | Proxy server port | 1-65535 (required when enabled, default: `3005`) |
| `protocol` | string | Conditional | Registration protocol | `"http"`, `"https"`, `"mtls"` (default: `"http"`) |
| `server_id` | string | Optional | Server identifier for registration | Valid string (preferred over `server_name`) |
| `server_name` | string | Optional | Legacy server name | Valid string (deprecated, use `server_id`) |
| `cert_file` | string | Conditional | Registration certificate file path | Valid file path (required for mTLS when enabled) |
| `key_file` | string | Conditional | Registration private key file path | Valid file path (required for mTLS when enabled) |
| `ca_cert_file` | string | Conditional | CA certificate file path | Valid file path (required for mTLS if `use_system_ca=false`) |
| `crl_file` | string | Optional | Certificate Revocation List file path | Valid CRL file path |
| `use_system_ca` | boolean | NO | Allow system CA store when `ca_cert_file` is not provided | `true`, `false` (default: `false`) |
| `register_endpoint` | string | NO | Registration endpoint path | Valid path (default: `"/register"`) |
| `unregister_endpoint` | string | NO | Unregistration endpoint path | Valid path (default: `"/unregister"`) |
| `auto_on_startup` | boolean | NO | Auto-register on startup | `true`, `false` (default: `true`) |
| `auto_on_shutdown` | boolean | NO | Auto-unregister on shutdown | `true`, `false` (default: `true`) |
| `heartbeat` | object | NO | Heartbeat configuration | See HeartbeatConfig below |

**Heartbeat Configuration** (`registration.heartbeat`):

| Field | Type | Required | Description | Default |
|-------|------|----------|-------------|---------|
| `endpoint` | string | NO | Heartbeat endpoint path | `"/heartbeat"` |
| `interval` | integer | NO | Heartbeat interval in seconds | `30` |

**Protocol Requirements**:
- **HTTP**: No certificates required
- **HTTPS**: `cert_file` and `key_file` are optional but recommended. If one is specified, both must be provided.
- **mTLS**: `cert_file` and `key_file` are required when `enabled=true`. `ca_cert_file` is required if `use_system_ca=false` (default).

**CRL Validation**:
- Same validation rules as `server` section
- If `crl_file` is specified and validation fails, registration will fail

**Example**:
```json
{
  "registration": {
    "enabled": true,
    "host": "localhost",
    "port": 3005,
    "protocol": "mtls",
    "server_id": "my-server-001",
    "cert_file": "./certs/registration.crt",
    "key_file": "./certs/registration.key",
    "ca_cert_file": "./certs/ca.crt",
    "crl_file": "./certs/registration.crl",
    "use_system_ca": false,
    "register_endpoint": "/register",
    "unregister_endpoint": "/unregister",
    "auto_on_startup": true,
    "auto_on_shutdown": true,
    "heartbeat": {
      "endpoint": "/heartbeat",
      "interval": 30
    }
  }
}
```

#### 4. `auth` Section

**Purpose**: Authentication and authorization configuration

| Field | Type | Required | Description | Allowed Values |
|-------|------|----------|-------------|----------------|
| `use_token` | boolean | NO | Enable token-based authentication | `true`, `false` (default: `false`) |
| `use_roles` | boolean | NO | Enable role-based authorization | `true`, `false` (default: `false`) |
| `tokens` | object | Conditional | Token-to-role mapping | Object with token strings as keys and role arrays as values (required if `use_token=true`) |
| `roles` | object | Conditional | Role-to-command mapping | Object with role strings as keys and command arrays as values (required if `use_roles=true`) |

**Note**: `use_roles` requires `use_token=true`

**Example**:
```json
{
  "auth": {
    "use_token": true,
    "use_roles": true,
    "tokens": {
      "admin-secret-key": ["admin"],
      "user-secret-key": ["user"],
      "readonly-secret-key": ["readonly"]
    },
    "roles": {
      "admin": ["*"],
      "user": ["health", "echo"],
      "readonly": ["health"]
    }
  }
}
```

#### Complete SimpleConfig Example

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "protocol": "mtls",
    "cert_file": "./certs/server.crt",
    "key_file": "./certs/server.key",
    "ca_cert_file": "./certs/ca.crt",
    "crl_file": "./certs/server.crl",
    "use_system_ca": false,
    "log_dir": "./logs"
  },
  "client": {
    "enabled": true,
    "protocol": "mtls",
    "cert_file": "./certs/client.crt",
    "key_file": "./certs/client.key",
    "ca_cert_file": "./certs/ca.crt",
    "crl_file": "./certs/client.crl",
    "use_system_ca": false
  },
  "registration": {
    "enabled": true,
    "host": "localhost",
    "port": 3005,
    "protocol": "mtls",
    "server_id": "my-server-001",
    "cert_file": "./certs/registration.crt",
    "key_file": "./certs/registration.key",
    "ca_cert_file": "./certs/ca.crt",
    "crl_file": "./certs/registration.crl",
    "use_system_ca": false,
    "register_endpoint": "/register",
    "unregister_endpoint": "/unregister",
    "auto_on_startup": true,
    "auto_on_shutdown": true,
    "heartbeat": {
      "endpoint": "/heartbeat",
      "interval": 30
    }
  },
  "auth": {
    "use_token": false,
    "use_roles": false,
    "tokens": {},
    "roles": {}
  }
}
```

#### CRL Validation Details

**Certificate Revocation List (CRL)** validation is performed for all sections (`server`, `client`, `registration`) when a `crl_file` is specified:

1. **File Existence**: The CRL file must exist and be accessible
2. **Format Validation**: The file must be a valid CRL in PEM or DER format
3. **Expiration Check**: The CRL must not be expired (checked against the `next_update` field)
4. **Certificate Revocation Check**: If the CRL is valid, certificates are checked against it to ensure they are not revoked

**Error Handling**:
- If CRL file is specified but not found: **Error logged, server stops**
- If CRL file is not a valid CRL format: **Error logged, server stops**
- If CRL is expired: **Error logged, server stops**
- If certificate is revoked according to CRL: **Error logged, server stops**

**CRL Validation Process**:
1. Check file exists → If not: Error and stop
2. Validate CRL format (PEM/DER) → If invalid: Error and stop
3. Check CRL expiration (`next_update`) → If expired: Error and stop
4. Check certificate serial number against CRL → If revoked: Error and stop

#### Generating SimpleConfig

Use the `adapter-cfg-gen` command to generate SimpleConfig files:

```bash
# Generate HTTP configuration
adapter-cfg-gen --protocol http --out config.json

# Generate HTTPS configuration with server certificates
adapter-cfg-gen --protocol https \
  --server-cert-file ./certs/server.crt \
  --server-key-file ./certs/server.key \
  --out config.json

# Generate mTLS configuration with all three sections
adapter-cfg-gen --protocol mtls \
  --server-cert-file ./certs/server.crt \
  --server-key-file ./certs/server.key \
  --server-ca-cert-file ./certs/ca.crt \
  --server-crl-file ./certs/server.crl \
  --client-enabled \
  --client-protocol mtls \
  --client-cert-file ./certs/client.crt \
  --client-key-file ./certs/client.key \
  --client-ca-cert-file ./certs/ca.crt \
  --client-crl-file ./certs/client.crl \
  --with-proxy \
  --registration-protocol mtls \
  --registration-cert-file ./certs/registration.crt \
  --registration-key-file ./certs/registration.key \
  --registration-ca-cert-file ./certs/ca.crt \
  --registration-crl-file ./certs/registration.crl \
  --out config.json
```

#### Validating SimpleConfig

Use the `adapter-cfg-val` command to validate SimpleConfig files:

```bash
# Validate configuration file
adapter-cfg-val --file config.json
```

The validator checks:
- Required fields are present
- File paths exist and are accessible
- Certificate-key pairs match
- Certificates are not expired
- CRL files are valid and not expired
- Certificates are not revoked according to CRL
- Certificate chains are valid

## Built-in Commands

- `health` - Server health check
- `echo` - Echo test command
- `config` - Configuration management
- `help` - Command help and documentation
- `reload` - Configuration reload
- `settings` - Settings management
- `load`/`unload` - Command loading/unloading
- `plugins` - Plugin management
- `proxy_registration` - Proxy registration control
- `transport_management` - Transport protocol management
- `role_test` - Role-based access testing

## Custom Commands with Queue Execution

Commands that use `use_queue=True` execute in child processes via the queue system. This is essential for:
- **CUDA compatibility**: CUDA requires multiprocessing spawn mode (not fork)
- **Long-running tasks**: Non-blocking execution of time-consuming operations
- **Resource isolation**: Commands run in separate processes

### ⚠️ Critical: Spawn Mode Registration

When using `use_queue=True`, commands execute in **child processes** (spawn mode). Child processes start with a fresh Python interpreter and **do not inherit** the parent process's command registry. You must ensure commands are registered in child processes.

### Registration Methods

#### Method 1: Module-Level Auto-Registration (Recommended)

Register commands automatically when the module is imported:

```python
# In your_command_module.py
from mcp_proxy_adapter.commands.command_registry import registry
from mcp_proxy_adapter.commands.base import Command, CommandResult

class MyQueueCommand(Command):
    """Command that executes via queue."""
    name = "my_queue_command"
    descr = "My queue command"
    use_queue = True  # Enable queue execution
    
    async def execute(self, message: str = "default", **kwargs) -> CommandResult:
        """Execute command."""
        return CommandResult(success=True, data={"message": message})

def _auto_register_commands():
    """Auto-register commands when module is imported."""
    try:
        registry.get_command("my_queue_command")
    except KeyError:
        registry.register(MyQueueCommand, "custom")

# Execute on import
_auto_register_commands()
```

Then register the module for auto-import:

```python
# In your main.py or application entry point
from mcp_proxy_adapter.commands.hooks import register_auto_import_module

# Register module for auto-import in child processes
register_auto_import_module("your_package.your_command_module")
```

#### Method 2: Hook-Based Registration (Automatic Module Path Extraction)

When you register a hook function, the module path is automatically extracted and stored:

```python
# In your main.py
from mcp_proxy_adapter.commands.hooks import register_custom_commands_hook
from mcp_proxy_adapter.commands.command_registry import registry

def register_my_commands(registry_instance):
    """Register custom commands via hook."""
    from your_package.your_command_module import MyQueueCommand
    registry_instance.register(MyQueueCommand, "custom")

# Register hook - module path is automatically extracted
register_custom_commands_hook(register_my_commands)

# Also register in main process
registry.register(MyQueueCommand, "custom")
```

The adapter automatically:
1. Extracts the module path from the hook function (`your_package.your_command_module`)
2. Stores it for auto-import in child processes
3. Imports the module in child processes before command execution

#### Method 3: Environment Variable (Fallback)

Set the `MCP_AUTO_REGISTER_MODULES` environment variable:

```bash
export MCP_AUTO_REGISTER_MODULES="your_package.your_command_module,another.module"
```

Or in your code:

```python
import os
os.environ['MCP_AUTO_REGISTER_MODULES'] = 'your_package.your_command_module'
```

### Complete Example

```python
# commands/my_queue_command.py
"""
Author: Your Name
email: your.email@example.com

Queue command example with proper registration for spawn mode.
"""
import asyncio
from typing import Any, Dict
from mcp_proxy_adapter.commands.base import Command, CommandResult
from mcp_proxy_adapter.commands.command_registry import registry

class LongRunningCommand(Command):
    """
    Long-running command that executes via queue.
    
    This command:
    - Executes in a child process (spawn mode)
    - Supports progress tracking
    - Returns result when completed
    """
    name = "long_running_task"
    descr = "Long-running task with progress updates (executes via queue)"
    use_queue = True  # Enable automatic queue execution

    async def execute(
        self,
        task_name: str = "default_task",
        duration: int = 60,
        steps: int = 10,
        **kwargs,
    ) -> CommandResult:
        """Execute long-running task with progress updates."""
        step_duration = duration / steps
        
        # Simulate work with steps
        for i in range(steps):
            await asyncio.sleep(step_duration)
        
        return CommandResult(
            success=True,
            data={
                "task_name": task_name,
                "duration": duration,
                "steps_completed": steps,
                "status": "completed",
                "message": f"Task '{task_name}' completed successfully after {duration} seconds",
            },
        )

def _auto_register_commands():
    """Auto-register commands when module is imported."""
    try:
        registry.get_command("long_running_task")
    except KeyError:
        registry.register(LongRunningCommand, "custom")

# Execute on import
_auto_register_commands()
```

```python
# main.py
from mcp_proxy_adapter.commands.command_registry import registry
from mcp_proxy_adapter.commands.hooks import register_auto_import_module
from commands.my_queue_command import LongRunningCommand

def register_all_commands():
    """Register all commands."""
    # Register in main process
    registry.register(LongRunningCommand, "custom")
    
    # Register module for auto-import in child processes (spawn mode)
    register_auto_import_module("commands.my_queue_command")
    print("✅ Long-running command registered (with spawn mode support)")

if __name__ == "__main__":
    register_all_commands()
    # Start server...
```

### Verification

To verify your command works correctly in spawn mode:

1. **Check command is registered in main process**:
   ```python
   from mcp_proxy_adapter.commands.command_registry import registry
   assert registry.command_exists("my_queue_command")
   ```

2. **Test queue execution**:
   ```python
   # Execute command via JSON-RPC
   response = requests.post(
       "http://localhost:8080/api/jsonrpc",
       json={
           "jsonrpc": "2.0",
           "method": "my_queue_command",
           "params": {"message": "test"},
           "id": 1
       }
   )
   result = response.json()
   job_id = result["result"]["job_id"]
   
   # Check job status
   status_response = requests.post(
       "http://localhost:8080/api/jsonrpc",
       json={
           "jsonrpc": "2.0",
           "method": "job_status",
           "params": {"job_id": job_id},
           "id": 2
       }
   )
   ```

### Troubleshooting

**Error: `"Command 'my_command' not found"`**

This indicates the command is not registered in the child process. Solutions:

1. **Ensure module-level auto-registration**:
   - Add `_auto_register_commands()` function to your module
   - Call it at module level (not inside a function)

2. **Register module for auto-import**:
   ```python
   register_auto_import_module("your_package.your_command_module")
   ```

3. **Check module path**:
   - Use full module path (e.g., `"my_package.commands.my_command"`)
   - Ensure the module can be imported (no circular imports)

4. **Use environment variable**:
   ```bash
   export MCP_AUTO_REGISTER_MODULES="your_package.your_command_module"
   ```

**Command executes but fails in child process**

- Check that all dependencies are available in child process
- Ensure CUDA/GPU resources are initialized in child process (not parent)
- Verify multiprocessing start method is `spawn` (required for CUDA)

### Automatic PYTHONPATH Management (6.9.89+)

**✅ NEW in 6.9.89+**: The adapter automatically manages `PYTHONPATH` for spawn mode!

The adapter now:
1. **Automatically adds application root** to `PYTHONPATH` based on `config_path`
2. **Automatically adds registered module paths** to `PYTHONPATH`
3. **Updates environment variable** so child processes inherit the paths
4. **Retries imports** with enhanced path resolution if initial import fails

**You no longer need to manually modify `PYTHONPATH` or `sys.path`!**

The adapter handles this automatically during server startup. If you still encounter import errors, check the logs for detailed information about `PYTHONPATH` and `sys.path`.

### Best Practices

1. **Always use module-level auto-registration** for commands with `use_queue=True`
2. **Register modules explicitly** using `register_auto_import_module()`
3. **Let the adapter manage PYTHONPATH** - no manual path manipulation needed
4. **Test in spawn mode** before deploying to production
5. **Use idempotent registration** (check if command exists before registering)
6. **Document registration requirements** in your command module docstrings

### Troubleshooting Import Errors

If you see `ModuleNotFoundError` in child process logs:

1. **Check logs for PYTHONPATH information**:
   ```
   CommandExecutionJob: Could not import module embed.commands: No module named 'embed'
     PYTHONPATH=/path/to/project
     sys.path (first 5)=[...]
   ```

2. **Verify module is registered**:
   ```python
   from mcp_proxy_adapter.commands.hooks import hooks
   print(hooks.get_auto_import_modules())  # Should include your module
   ```

3. **Check application path**:
   - Ensure `config_path` is provided to `create_app()` or `create_and_run_server()`
   - The adapter uses `config_path` to determine application root

4. **Manual override** (if needed):
   ```python
   import os
   os.environ['PYTHONPATH'] = '/path/to/project:' + os.environ.get('PYTHONPATH', '')
   ```

## Security Features

- **Authentication**: API keys, JWT tokens, certificate-based auth
- **Authorization**: Role-based permissions with wildcard support
- **SSL/TLS**: Full SSL/TLS and mTLS support
- **Rate Limiting**: Configurable request rate limiting
- **Security Headers**: Automatic security header injection

## Examples

The `mcp_proxy_adapter/examples/` directory contains comprehensive examples for different use cases:

- **Basic Framework**: Simple HTTP server setup
- **Full Application**: Complete application with custom commands and hooks
- **Security Testing**: Comprehensive security test suite
- **Certificate Generation**: SSL/TLS certificate management

### Test Environment Setup

The framework includes a comprehensive test environment setup that automatically creates configurations, generates certificates, and runs tests:

```bash
# Create a complete test environment with all configurations and certificates
python -m mcp_proxy_adapter.examples.setup_test_environment

# Create test environment in a specific directory
python -m mcp_proxy_adapter.examples.setup_test_environment /path/to/test/dir

# Skip certificate generation (use existing certificates)
python -m mcp_proxy_adapter.examples.setup_test_environment --skip-certs

# Skip running tests (setup only)
python -m mcp_proxy_adapter.examples.setup_test_environment --skip-tests
```

### Configuration Generation

Generate test configurations from a comprehensive template:

```bash
# Generate all test configurations
python -m mcp_proxy_adapter.examples.create_test_configs

# Generate from specific comprehensive config
python -m mcp_proxy_adapter.examples.create_test_configs --comprehensive-config config.json

# Generate specific configuration types
python -m mcp_proxy_adapter.examples.create_test_configs --types http,https,mtls
```

### Certificate Generation

Generate SSL/TLS certificates for testing:

```bash
# Generate all certificates using mcp_security_framework
python -m mcp_proxy_adapter.examples.generate_all_certificates

# Generate certificates with custom configuration
python -m mcp_proxy_adapter.examples.generate_certificates_framework --config cert_config.json
```

### Security Testing

Run comprehensive security tests:

```bash
# Run all security tests
python -m mcp_proxy_adapter.examples.run_security_tests_fixed

# Run full test suite (includes setup, config generation, certificate generation, and testing)
python -m mcp_proxy_adapter.examples.run_full_test_suite
```

### Complete Workflow Example

```bash
# 1. Install the package
pip install mcp-proxy-adapter

# 2. Create test environment (automatically runs tests)
python -m mcp_proxy_adapter.examples.setup_test_environment

# 3. Or run individual steps:
# Generate certificates
python -m mcp_proxy_adapter.examples.generate_all_certificates

# Generate configurations
python -m mcp_proxy_adapter.examples.create_test_configs

# Run security tests
python -m mcp_proxy_adapter.examples.run_security_tests_fixed

# 4. Start server with generated configuration
python -m mcp_proxy_adapter --config configs/http_simple.json
```

## Development

The project follows a modular architecture:

- `mcp_proxy_adapter/api/` - FastAPI application and handlers
- `mcp_proxy_adapter/commands/` - Command system and built-in commands
- `mcp_proxy_adapter/core/` - Core functionality and utilities
- `mcp_proxy_adapter/config.py` - Configuration management

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please contact vasilyvz@gmail.com.
