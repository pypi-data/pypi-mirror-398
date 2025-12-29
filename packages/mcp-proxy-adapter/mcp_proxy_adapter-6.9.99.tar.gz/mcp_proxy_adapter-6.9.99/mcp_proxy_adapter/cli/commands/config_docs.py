"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

CLI command: config docs (Generate comprehensive configuration documentation)
"""

from __future__ import annotations

import argparse
import sys
from argparse import Namespace
from pathlib import Path
from typing import Optional


def config_docs_command(args: Namespace) -> int:
    """
    Generate comprehensive configuration documentation with examples.
    
    Args:
        args: Parsed argparse namespace with output path.
        
    Returns:
        Exit status code (0 on success).
    """
    output_path = Path(args.output) if args.output else Path("CONFIGURATION_GUIDE.md")
    
    docs_content = generate_configuration_guide()
    
    try:
        output_path.write_text(docs_content, encoding="utf-8")
        print(f"✅ Configuration guide generated: {output_path}")
        return 0
    except Exception as e:
        print(f"❌ Error writing documentation: {e}", file=sys.stderr)
        return 1


def generate_configuration_guide() -> str:
    """Generate comprehensive configuration documentation."""
    
    return """# MCP Proxy Adapter - Configuration Guide

**Author:** Vasiliy Zdanovskiy  
**Email:** vasilyvz@gmail.com

## 📋 Table of Contents

1. [Overview](#overview)
2. [Configuration Structure](#configuration-structure)
3. [Server Configuration](#server-configuration)
4. [Registration Configuration](#registration-configuration)
5. [Authentication Configuration](#authentication-configuration)
6. [Queue Manager Configuration](#queue-manager-configuration)
7. [Common Patterns](#common-patterns)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Overview

MCP Proxy Adapter uses a simple, unified configuration format based on JSON. All configuration is organized into logical sections: `server`, `registration`, `auth`, and `queue_manager`.

### Configuration File Format

The configuration file is a JSON file with the following structure:

```json
{
  "server": { ... },
  "client": { ... },
  "registration": { ... },
  "auth": { ... },
  "queue_manager": { ... }
}
```

---

## Configuration Structure

### Complete Configuration Example

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "protocol": "http",
    "servername": "localhost",
    "debug": false,
    "log_level": "INFO",
    "log_dir": "./logs",
    "ssl": {
      "cert": "./certs/server.crt",
      "key": "./certs/server.key",
      "ca": "./certs/ca.crt",
      "crl": "./certs/crl.pem",
      "dnscheck": false
    }
  },
  "client": {
    "enabled": false,
    "protocol": "http",
    "ssl": null
  },
  "registration": {
    "enabled": true,
    "protocol": "http",
    "register_url": "http://localhost:3005/register",
    "unregister_url": "http://localhost:3005/unregister",
    "heartbeat_interval": 30,
    "auto_on_startup": true,
    "auto_on_shutdown": true,
    "server_id": "my-server-id",
    "server_name": "My Server",
    "ssl": {
      "cert": "./certs/client.crt",
      "key": "./certs/client.key",
      "ca": "./certs/ca.crt",
      "dnscheck": true
    },
    "heartbeat": {
      "url": "http://localhost:3005/proxy/heartbeat",
      "interval": 30
    }
  },
  "auth": {
    "use_token": false,
    "use_roles": false,
    "tokens": {},
    "roles": {}
  },
  "queue_manager": {
    "enabled": true,
    "in_memory": true,
    "registry_path": null,
    "shutdown_timeout": 30.0,
    "max_concurrent_jobs": 10,
    "max_queue_size": null,
    "per_job_type_limits": null
  }
}
```

---

## Server Configuration

The `server` section configures the main server endpoint that listens for incoming connections.

### Required Fields

- `host` (string): Server host address (e.g., "0.0.0.0" or "localhost")
- `port` (integer): Server port number (e.g., 8080)
- `protocol` (string): Protocol type - must be one of: `"http"`, `"https"`, `"mtls"`
- `servername` (string): DNS name of the server (used for SSL/TLS)

### Optional Fields

- `debug` (boolean): Enable debug mode (default: `false`)
- `log_level` (string): Logging level - `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"CRITICAL"` (default: `"INFO"`)
- `log_dir` (string): Directory for log files (default: `"./logs"`)
- `ssl` (object): SSL/TLS configuration (required for `https` and `mtls` protocols)

### SSL Configuration

The `ssl` object within `server` contains:

- `cert` (string): Path to server certificate file (required for `https`/`mtls`)
- `key` (string): Path to server private key file (required for `https`/`mtls`)
- `ca` (string): Path to CA certificate file (required for `mtls`, optional for `https`)
- `crl` (string, optional): Path to Certificate Revocation List file
- `dnscheck` (boolean): Enable DNS/hostname verification (default: `false` for server)

### ✅ Correct Examples

#### HTTP Server (Basic)

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "protocol": "http",
    "servername": "localhost"
  }
}
```

#### HTTPS Server

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8443,
    "protocol": "https",
    "servername": "example.com",
    "ssl": {
      "cert": "./certs/server.crt",
      "key": "./certs/server.key",
      "ca": "./certs/ca.crt",
      "dnscheck": true
    }
  }
}
```

#### mTLS Server

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8443,
    "protocol": "mtls",
    "servername": "example.com",
    "ssl": {
      "cert": "./certs/server.crt",
      "key": "./certs/server.key",
      "ca": "./certs/ca.crt",
      "dnscheck": false
    }
  }
}
```

### ❌ Incorrect Examples

#### Missing Required Fields

```json
{
  "server": {
    "port": 8080
    // ❌ Missing: host, protocol, servername
  }
}
```

#### Invalid Protocol

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "protocol": "ftp",  // ❌ Invalid: must be http, https, or mtls
    "servername": "localhost"
  }
}
```

#### HTTPS Without SSL Configuration

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8443,
    "protocol": "https",  // ❌ Requires ssl section
    "servername": "example.com"
    // ❌ Missing: ssl configuration
  }
}
```

#### mTLS Without CA Certificate

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8443,
    "protocol": "mtls",
    "servername": "example.com",
    "ssl": {
      "cert": "./certs/server.crt",
      "key": "./certs/server.key"
      // ❌ Missing: ca (required for mTLS)
    }
  }
}
```

---

## Registration Configuration

The `registration` section configures how the server registers with the proxy server.

### Required Fields (when enabled)

- `enabled` (boolean): Enable/disable registration
- `protocol` (string): Protocol for proxy communication - `"http"`, `"https"`, or `"mtls"`
- `register_url` (string): Full URL for registration endpoint (e.g., `"http://localhost:3005/register"`)
- `unregister_url` (string): Full URL for unregistration endpoint (e.g., `"http://localhost:3005/unregister"`)
- `heartbeat_interval` (integer): Heartbeat interval in seconds (must be positive)
- `heartbeat` (object): Heartbeat configuration with `url` and `interval`

### Optional Fields

- `auto_on_startup` (boolean): Automatically register on server startup (default: `true`)
- `auto_on_shutdown` (boolean): Automatically unregister on server shutdown (default: `true`)
- `server_id` (string): Unique server identifier
- `server_name` (string): Human-readable server name
- `ssl` (object): SSL/TLS configuration for proxy communication (required for `https`/`mtls`)

### URL Scheme Requirements

**Critical:** The URL scheme in `register_url`, `unregister_url`, and `heartbeat.url` **must match** the `protocol`:

- If `protocol` is `"http"` → URLs must start with `"http://"`
- If `protocol` is `"https"` or `"mtls"` → URLs must start with `"https://"`

### ✅ Correct Examples

#### HTTP Registration

```json
{
  "registration": {
    "enabled": true,
    "protocol": "http",
    "register_url": "http://localhost:3005/register",
    "unregister_url": "http://localhost:3005/unregister",
    "heartbeat_interval": 30,
    "heartbeat": {
      "url": "http://localhost:3005/proxy/heartbeat",
      "interval": 30
    }
  }
}
```

#### HTTPS Registration

```json
{
  "registration": {
    "enabled": true,
    "protocol": "https",
    "register_url": "https://proxy.example.com:3005/register",
    "unregister_url": "https://proxy.example.com:3005/unregister",
    "heartbeat_interval": 30,
    "ssl": {
      "cert": "./certs/client.crt",
      "key": "./certs/client.key",
      "ca": "./certs/ca.crt",
      "dnscheck": true
    },
    "heartbeat": {
      "url": "https://proxy.example.com:3005/proxy/heartbeat",
      "interval": 30
    }
  }
}
```

#### mTLS Registration

```json
{
  "registration": {
    "enabled": true,
    "protocol": "mtls",
    "register_url": "https://proxy.example.com:3005/register",
    "unregister_url": "https://proxy.example.com:3005/unregister",
    "heartbeat_interval": 30,
    "ssl": {
      "cert": "./certs/client.crt",
      "key": "./certs/client.key",
      "ca": "./certs/ca.crt",
      "dnscheck": false
    },
    "heartbeat": {
      "url": "https://proxy.example.com:3005/proxy/heartbeat",
      "interval": 30
    }
  }
}
```

### ❌ Incorrect Examples

#### Protocol Mismatch in URLs

```json
{
  "registration": {
    "enabled": true,
    "protocol": "https",
    "register_url": "http://localhost:3005/register",  // ❌ Wrong scheme: should be https://
    "unregister_url": "http://localhost:3005/unregister",  // ❌ Wrong scheme
    "heartbeat": {
      "url": "http://localhost:3005/proxy/heartbeat"  // ❌ Wrong scheme
    }
  }
}
```

#### Missing Required URLs

```json
{
  "registration": {
    "enabled": true,
    "protocol": "http"
    // ❌ Missing: register_url, unregister_url, heartbeat
  }
}
```

#### HTTPS Without SSL Configuration

```json
{
  "registration": {
    "enabled": true,
    "protocol": "https",  // ❌ Requires ssl section
    "register_url": "https://localhost:3005/register",
    "unregister_url": "https://localhost:3005/unregister"
    // ❌ Missing: ssl configuration
  }
}
```

#### Invalid Heartbeat Interval

```json
{
  "registration": {
    "enabled": true,
    "protocol": "http",
    "register_url": "http://localhost:3005/register",
    "unregister_url": "http://localhost:3005/unregister",
    "heartbeat_interval": -1,  // ❌ Must be positive integer
    "heartbeat": {
      "url": "http://localhost:3005/proxy/heartbeat",
      "interval": 0  // ❌ Must be positive integer
    }
  }
}
```

---

## Authentication Configuration

The `auth` section configures authentication and authorization.

### Fields

- `use_token` (boolean): Enable token-based authentication
- `use_roles` (boolean): Enable role-based authorization (requires `use_token: true`)
- `tokens` (object): Mapping of token values to role lists
- `roles` (object): Mapping of role names to permission lists

### ✅ Correct Examples

#### Token Authentication

```json
{
  "auth": {
    "use_token": true,
    "use_roles": false,
    "tokens": {
      "admin-secret-key": ["*"],
      "user-token-123": ["read", "write"]
    },
    "roles": {}
  }
}
```

#### Token + Roles Authentication

```json
{
  "auth": {
    "use_token": true,
    "use_roles": true,
    "tokens": {
      "admin-key": ["admin"],
      "user-key": ["user", "reader"]
    },
    "roles": {
      "admin": ["*"],
      "user": ["read", "write"],
      "reader": ["read"]
    }
  }
}
```

#### No Authentication

```json
{
  "auth": {
    "use_token": false,
    "use_roles": false,
    "tokens": {},
    "roles": {}
  }
}
```

### ❌ Incorrect Examples

#### Roles Without Tokens

```json
{
  "auth": {
    "use_token": false,
    "use_roles": true,  // ❌ use_roles requires use_token: true
    "tokens": {},
    "roles": {
      "admin": ["*"]
    }
  }
}
```

#### Token Referencing Non-Existent Role

```json
{
  "auth": {
    "use_token": true,
    "use_roles": true,
    "tokens": {
      "my-token": ["admin", "nonexistent"]  // ❌ "nonexistent" role not defined
    },
    "roles": {
      "admin": ["*"]
      // ❌ Missing: "nonexistent" role definition
    }
  }
}
```

---

## Queue Manager Configuration

The `queue_manager` section configures the job queue system.

### Fields

- `enabled` (boolean): Enable/disable queue manager (default: `true`)
- `in_memory` (boolean): Use in-memory queue (default: `true`)
- `registry_path` (string, optional): Path to persistent registry file (ignored if `in_memory: true`)
- `shutdown_timeout` (float): Graceful shutdown timeout in seconds (default: `30.0`)
- `max_concurrent_jobs` (integer): Maximum concurrent jobs (default: `10`)
- `max_queue_size` (integer, optional): Global maximum queue size (if reached, oldest job is deleted)
- `per_job_type_limits` (object, optional): Per-job-type limits (e.g., `{"command_execution": 100, "data_processing": 50}`)

### ✅ Correct Examples

#### In-Memory Queue (Default)

```json
{
  "queue_manager": {
    "enabled": true,
    "in_memory": true,
    "max_concurrent_jobs": 10,
    "shutdown_timeout": 30.0
  }
}
```

#### Persistent Queue

```json
{
  "queue_manager": {
    "enabled": true,
    "in_memory": false,
    "registry_path": "./queue_registry.json",
    "max_concurrent_jobs": 20,
    "shutdown_timeout": 60.0
  }
}
```

#### Queue with Limits

```json
{
  "queue_manager": {
    "enabled": true,
    "in_memory": true,
    "max_concurrent_jobs": 10,
    "max_queue_size": 1000,
    "per_job_type_limits": {
      "command_execution": 100,
      "data_processing": 50,
      "api_call": 200
    }
  }
}
```

### ❌ Incorrect Examples

#### Persistent Queue Without Registry Path

```json
{
  "queue_manager": {
    "enabled": true,
    "in_memory": false,  // ❌ Requires registry_path
    "max_concurrent_jobs": 10
    // ❌ Missing: registry_path
  }
}
```

#### Invalid Concurrent Jobs

```json
{
  "queue_manager": {
    "enabled": true,
    "in_memory": true,
    "max_concurrent_jobs": 0  // ❌ Must be at least 1
  }
}
```

#### Invalid Per-Job-Type Limit

```json
{
  "queue_manager": {
    "enabled": true,
    "in_memory": true,
    "per_job_type_limits": {
      "command_execution": -1  // ❌ Must be positive integer
    }
  }
}
```

---

## Common Patterns

### Pattern 1: Simple HTTP Server with Registration

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "protocol": "http",
    "servername": "localhost"
  },
  "registration": {
    "enabled": true,
    "protocol": "http",
    "register_url": "http://localhost:3005/register",
    "unregister_url": "http://localhost:3005/unregister",
    "heartbeat_interval": 30,
    "heartbeat": {
      "url": "http://localhost:3005/proxy/heartbeat",
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

### Pattern 2: HTTPS Server with Token Authentication

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8443,
    "protocol": "https",
    "servername": "example.com",
    "ssl": {
      "cert": "./certs/server.crt",
      "key": "./certs/server.key",
      "ca": "./certs/ca.crt",
      "dnscheck": true
    }
  },
  "registration": {
    "enabled": true,
    "protocol": "https",
    "register_url": "https://proxy.example.com:3005/register",
    "unregister_url": "https://proxy.example.com:3005/unregister",
    "heartbeat_interval": 30,
    "ssl": {
      "cert": "./certs/client.crt",
      "key": "./certs/client.key",
      "ca": "./certs/ca.crt",
      "dnscheck": true
    },
    "heartbeat": {
      "url": "https://proxy.example.com:3005/proxy/heartbeat",
      "interval": 30
    }
  },
  "auth": {
    "use_token": true,
    "use_roles": false,
    "tokens": {
      "admin-secret-key": ["*"]
    },
    "roles": {}
  }
}
```

### Pattern 3: mTLS with Roles

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8443,
    "protocol": "mtls",
    "servername": "example.com",
    "ssl": {
      "cert": "./certs/server.crt",
      "key": "./certs/server.key",
      "ca": "./certs/ca.crt",
      "dnscheck": false
    }
  },
  "registration": {
    "enabled": true,
    "protocol": "mtls",
    "register_url": "https://proxy.example.com:3005/register",
    "unregister_url": "https://proxy.example.com:3005/unregister",
    "heartbeat_interval": 30,
    "ssl": {
      "cert": "./certs/client.crt",
      "key": "./certs/client.key",
      "ca": "./certs/ca.crt",
      "dnscheck": false
    },
    "heartbeat": {
      "url": "https://proxy.example.com:3005/proxy/heartbeat",
      "interval": 30
    }
  },
  "auth": {
    "use_token": true,
    "use_roles": true,
    "tokens": {
      "admin-key": ["admin"],
      "user-key": ["user"]
    },
    "roles": {
      "admin": ["*"],
      "user": ["read", "write"]
    }
  }
}
```

---

## Best Practices

### 1. Use Full URLs for Registration

✅ **Correct:**
```json
{
  "registration": {
    "register_url": "https://proxy.example.com:3005/register"
  }
}
```

❌ **Incorrect:**
```json
{
  "registration": {
    "host": "proxy.example.com",
    "port": 3005,
    "register_endpoint": "/register"
  }
}
```

### 2. Match Protocol and URL Schemes

✅ **Correct:**
```json
{
  "registration": {
    "protocol": "https",
    "register_url": "https://proxy.example.com/register"
  }
}
```

❌ **Incorrect:**
```json
{
  "registration": {
    "protocol": "https",
    "register_url": "http://proxy.example.com/register"  // ❌ Scheme mismatch
  }
}
```

### 3. Use SSL Configuration for Secure Protocols

✅ **Correct:**
```json
{
  "server": {
    "protocol": "https",
    "ssl": {
      "cert": "./certs/server.crt",
      "key": "./certs/server.key",
      "ca": "./certs/ca.crt"
    }
  }
}
```

❌ **Incorrect:**
```json
{
  "server": {
    "protocol": "https"
    // ❌ Missing SSL configuration
  }
}
```

### 4. Set Appropriate Heartbeat Intervals

✅ **Correct:**
```json
{
  "registration": {
    "heartbeat_interval": 30,  // 30 seconds is reasonable
    "heartbeat": {
      "interval": 30
    }
  }
}
```

❌ **Incorrect:**
```json
{
  "registration": {
    "heartbeat_interval": 1,  // ❌ Too frequent, may cause load
    "heartbeat": {
      "interval": 3600  // ❌ Too infrequent, may cause timeout
    }
  }
}
```

### 5. Use Descriptive Server Names

✅ **Correct:**
```json
{
  "registration": {
    "server_id": "production-server-01",
    "server_name": "Production Server 01"
  }
}
```

❌ **Incorrect:**
```json
{
  "registration": {
    "server_id": "srv1",  // ❌ Not descriptive
    "server_name": "Server"  // ❌ Too generic
  }
}
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Registration Fails

**Symptoms:** Server cannot register with proxy

**Possible Causes:**
- URL scheme doesn't match protocol
- SSL configuration missing for HTTPS/mTLS
- Network connectivity issues
- Invalid certificate paths

**Solution:**
```json
// ✅ Ensure protocol matches URL scheme
{
  "registration": {
    "protocol": "https",
    "register_url": "https://proxy.example.com/register",  // Must be https://
    "ssl": {
      "cert": "./certs/client.crt",  // Ensure file exists
      "key": "./certs/client.key",
      "ca": "./certs/ca.crt"
    }
  }
}
```

#### Issue 2: SSL Certificate Errors

**Symptoms:** SSL handshake failures

**Possible Causes:**
- Certificate file not found
- Invalid certificate format
- CA certificate missing for mTLS
- Hostname mismatch

**Solution:**
```json
// ✅ For mTLS, ensure CA is provided
{
  "server": {
    "protocol": "mtls",
    "ssl": {
      "cert": "./certs/server.crt",  // Verify file exists
      "key": "./certs/server.key",
      "ca": "./certs/ca.crt",  // Required for mTLS
      "dnscheck": false  // Set to false if hostname doesn't match
    }
  }
}
```

#### Issue 3: Authentication Failures

**Symptoms:** Requests rejected with 401/403

**Possible Causes:**
- Token not provided in request
- Token not in tokens dictionary
- Role not defined
- use_roles enabled without use_token

**Solution:**
```json
// ✅ Ensure tokens and roles are properly configured
{
  "auth": {
    "use_token": true,
    "use_roles": true,
    "tokens": {
      "my-token": ["admin"]  // Token must exist
    },
    "roles": {
      "admin": ["*"]  // Role must be defined
    }
  }
}
```

#### Issue 4: Queue Manager Issues

**Symptoms:** Jobs not processing, queue full

**Possible Causes:**
- max_concurrent_jobs too low
- max_queue_size reached
- Invalid per_job_type_limits

**Solution:**
```json
// ✅ Adjust queue limits appropriately
{
  "queue_manager": {
    "enabled": true,
    "max_concurrent_jobs": 20,  // Increase if needed
    "max_queue_size": 1000,  // Set limit or null for unlimited
    "per_job_type_limits": {
      "command_execution": 100  // Ensure positive integers
    }
  }
}
```

---

## Validation

Always validate your configuration before deployment:

```bash
adapter-cfg-val config.json
```

This will check:
- Required fields are present
- Protocol and URL scheme consistency
- SSL configuration completeness
- File paths exist
- Data types are correct
- Authentication configuration is valid

---

## Quick Reference

### Required Fields by Section

**Server:**
- `host`, `port`, `protocol`, `servername`
- `ssl` (if protocol is `https` or `mtls`)

**Registration (when enabled):**
- `enabled`, `protocol`, `register_url`, `unregister_url`, `heartbeat_interval`, `heartbeat`
- `ssl` (if protocol is `https` or `mtls`)

**Auth:**
- All fields have defaults, but `tokens` and `roles` should be populated if `use_token` is true

**Queue Manager:**
- All fields have defaults

### Protocol Requirements

| Protocol | Server SSL Required | Registration SSL Required | CA Required |
|----------|---------------------|---------------------------|-------------|
| `http`   | No                  | No                        | No          |
| `https`  | Yes                 | Yes (if enabled)          | Optional    |
| `mtls`   | Yes                 | Yes (if enabled)          | Yes         |

### URL Scheme Rules

- `protocol: "http"` → URLs must use `http://`
- `protocol: "https"` or `"mtls"` → URLs must use `https://`

---

**Last Updated:** 2025-11-22  
**Version:** 1.0.0

"""


def main() -> int:
    """Main entry point for adapter-cfg-docs CLI command."""
    parser = argparse.ArgumentParser(
        prog="adapter-cfg-docs",
        description="Generate comprehensive configuration documentation for MCP Proxy Adapter"
    )
    parser.add_argument(
        '--output',
        '-o',
        type=str,
        help='Output file path (default: CONFIGURATION_GUIDE.md)'
    )
    
    args = parser.parse_args()
    return config_docs_command(args)


if __name__ == "__main__":
    sys.exit(main())

