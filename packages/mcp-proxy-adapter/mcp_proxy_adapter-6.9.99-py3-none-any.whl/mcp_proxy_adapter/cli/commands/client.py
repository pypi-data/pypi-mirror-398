"""
MCP Client Command

Client CLI for calling health and JSON-RPC endpoints in various modes.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from mcp_proxy_adapter.client.proxy import ProxyClient


def _build_base_url(protocol: str, host: str, port: int) -> str:
    """
    Construct base URL for HTTP/HTTPS requests.

    Args:
        protocol: Connection protocol (http/https).
        host: Target host.
        port: Target port.

    Returns:
        Fully qualified base URL.
    """
    scheme = "https" if protocol == "https" else "http"
    return f"{scheme}://{host}:{port}"


def _request_kwargs(protocol: str, token_header: Optional[str], token: Optional[str],
                    cert: Optional[str], key: Optional[str], ca: Optional[str]) -> Dict[str, Any]:
    """
    Build keyword arguments for requests/httpx based on auth/protocol options.

    Args:
        protocol: Connection protocol (http/https).
        token_header: Custom header for API token.
        token: Token value.
        cert: Path to client certificate.
        key: Path to client key.
        ca: Path to CA bundle.

    Returns:
        Dictionary with request kwargs (headers, timeout, SSL options).
    """
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if token_header and token:
        headers[token_header] = token

    kwargs: Dict[str, Any] = {"headers": headers, "timeout": 10}

    if protocol == "https":
        if cert and key:
            kwargs["cert"] = (cert, key)
        # For examples we allow self-signed; if CA provided, use it, otherwise disable verification
        if ca:
            kwargs["verify"] = str(Path(ca))
        else:
            kwargs["verify"] = False

    return kwargs


def client_command(args) -> int:
    """Dispatch client subcommands."""
    protocol = args.protocol
    host = args.host
    port = args.port
    base = _build_base_url(protocol, host, port)
    kwargs = _request_kwargs(
        protocol,
        getattr(args, "token_header", None),
        getattr(args, "token", None),
        getattr(args, "cert", None),
        getattr(args, "key", None),
        getattr(args, "ca", None),
    )

    try:
        if args.client_command == "health":
            resp = requests.get(f"{base}/health", **kwargs)
            print(json.dumps(resp.json(), ensure_ascii=False))
            return 0 if resp.ok else 1

        if args.client_command == "jsonrpc":
            payload: Dict[str, Any] = {
                "jsonrpc": "2.0",
                "method": args.method,
                "params": json.loads(args.params) if args.params else {},
                "id": args.id,
            }
            resp = requests.post(f"{base}/api/jsonrpc", data=json.dumps(payload), **kwargs)
            print(json.dumps(resp.json(), ensure_ascii=False))
            return 0 if resp.ok else 1

        if args.client_command == "proxy-register":
            pc = ProxyClient(args.proxy_url)
            res = pc.register(args.name, args.url, capabilities=args.capabilities or [], metadata=None)
            print(json.dumps(res, ensure_ascii=False))
            return 0

        if args.client_command == "proxy-unregister":
            pc = ProxyClient(args.proxy_url)
            res = pc.unregister(args.name)
            print(json.dumps(res, ensure_ascii=False))
            return 0

        if args.client_command == "proxy-list":
            pc = ProxyClient(args.proxy_url)
            res = pc.list_servers()
            print(json.dumps(res, ensure_ascii=False))
            return 0

        print("Available: client health|jsonrpc")
        return 1

    except Exception as exc:  # noqa: BLE001 (keep simple CLI handling)
        print(f"❌ Client error: {exc}")
        return 1


