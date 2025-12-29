#!/usr/bin/env python3
"""
CLI Argument Parser for MCP Proxy Adapter
Multi-level help system with detailed parameter descriptions

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import argparse


def create_main_parser() -> argparse.ArgumentParser:
    """Create top-level CLI parser with subcommands."""
    parser = argparse.ArgumentParser(prog="mcp-cli", description="MCP Proxy Adapter CLI")
    subparsers = parser.add_subparsers(dest='command', metavar='command')

    # generate
    generate_parser = subparsers.add_parser('generate', help='Generate configuration (legacy)')
    _setup_generate_parser(generate_parser)

    # testconfig
    testconfig_parser = subparsers.add_parser('testconfig', help='Validate configuration (legacy)')
    _setup_testconfig_parser(testconfig_parser)

    # sets
    sets_parser = subparsers.add_parser('sets', help='Generate preset configuration set (legacy)')
    _setup_sets_parser(sets_parser)

    # server
    server_parser = subparsers.add_parser('server', help='Run server (legacy)')
    _setup_server_parser(server_parser)

    # simple config commands (new)
    config_parser = subparsers.add_parser('config', help='Simple config utilities')
    config_sub = config_parser.add_subparsers(dest='config_command')

    # config generate
    cfg_gen = config_sub.add_parser('generate', help='Generate simple configuration')
    cfg_gen.add_argument('--protocol', required=True, choices=['http', 'https', 'mtls'], help='Server/proxy protocol')
    cfg_gen.add_argument('--with-proxy', action='store_true', help='Include proxy_client section')
    cfg_gen.add_argument('--out', default='config.json', help='Output config path (default: config.json)')
    
    # Server parameters
    cfg_gen.add_argument('--server-host', help='Server host (default: 0.0.0.0)')
    cfg_gen.add_argument('--server-port', type=int, help='Server port (default: 8080)')
    cfg_gen.add_argument('--server-cert-file', help='Server certificate file path')
    cfg_gen.add_argument('--server-key-file', help='Server key file path')
    cfg_gen.add_argument('--server-ca-cert-file', help='Server CA certificate file path')
    
    # Proxy parameters
    cfg_gen.add_argument('--proxy-host', help='Proxy host (default: localhost)')
    cfg_gen.add_argument('--proxy-port', type=int, help='Proxy port (default: 3005)')
    cfg_gen.add_argument('--proxy-cert-file', help='Proxy client certificate file path')
    cfg_gen.add_argument('--proxy-key-file', help='Proxy client key file path')
    cfg_gen.add_argument('--proxy-ca-cert-file', help='Proxy CA certificate file path')

    # config validate
    cfg_val = config_sub.add_parser('validate', help='Validate simple configuration file')
    cfg_val.add_argument('--file', required=True, help='Path to configuration file')

    # config docs
    cfg_docs = config_sub.add_parser('docs', help='Generate comprehensive configuration documentation')
    cfg_docs.add_argument('--output', '-o', help='Output file path (default: CONFIGURATION_GUIDE.md)')

    # client
    client_parser = subparsers.add_parser('client', help='HTTP/HTTPS/mTLS client for health and JSON-RPC')
    _setup_client_parser(client_parser)

    return parser


def _setup_generate_parser(parser: argparse.ArgumentParser):
    """Setup generate command parser"""
    
    # Protocol selection
    protocol_group = parser.add_argument_group(
        'Protocol Configuration',
        'Select the communication protocol and security level'
    )
    protocol_group.add_argument(
        '--protocol',
        choices=['http', 'https', 'mtls'],
        required=True,
        help='''Communication protocol:
  http  - Plain HTTP (no encryption)
  https - HTTP with SSL/TLS encryption
  mtls  - Mutual TLS with client certificate verification'''
    )
    
    # Security options
    security_group = parser.add_argument_group(
        'Security Configuration',
        'Configure authentication and authorization'
    )
    security_group.add_argument(
        '--token',
        action='store_true',
        help='Enable token-based authentication (API keys)'
    )
    security_group.add_argument(
        '--roles',
        action='store_true',
        help='Enable role-based access control (requires --token)'
    )
    
    # Server configuration
    server_group = parser.add_argument_group(
        'Server Configuration',
        'Configure server host and port settings'
    )
    server_group.add_argument(
        '--host',
        default='127.0.0.1',
        help='Server host address (default: 127.0.0.1)'
    )
    server_group.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Server port number (default: 8000)'
    )
    
    # SSL/TLS configuration
    ssl_group = parser.add_argument_group(
        'SSL/TLS Configuration',
        'Configure SSL certificates and keys (required for https/mtls)'
    )
    ssl_group.add_argument(
        '--cert-dir',
        default='./certs',
        help='Directory containing SSL certificates (default: ./certs)'
    )
    ssl_group.add_argument(
        '--key-dir',
        default='./keys',
        help='Directory containing SSL private keys (default: ./keys)'
    )
    
    # Proxy registration
    proxy_group = parser.add_argument_group(
        'Proxy Registration',
        'Configure automatic registration with MCP proxy'
    )
    proxy_group.add_argument(
        '--proxy-registration',
        action='store_true',
        help='Enable automatic proxy registration'
    )
    proxy_group.add_argument(
        '--proxy-url',
        help='Proxy URL for registration (required with --proxy-registration)'
    )
    proxy_group.add_argument(
        '--server-id',
        default='mcp_proxy_adapter',
        help='Server ID for proxy registration (default: mcp_proxy_adapter)'
    )
    
    # Output options
    output_group = parser.add_argument_group(
        'Output Configuration',
        'Configure output file and directory settings'
    )
    output_group.add_argument(
        '--output-dir',
        default='./configs',
        help='Output directory for configuration files (default: ./configs)'
    )
    output_group.add_argument(
        '--output',
        help='Output filename (without extension, auto-generated if not specified)'
    )
    output_group.add_argument(
        '--stdout',
        action='store_true',
        help='Output configuration to stdout instead of file'
    )
    output_group.add_argument(
        '--no-validate',
        action='store_true',
        help='Skip configuration validation after generation'
    )


def _setup_testconfig_parser(parser: argparse.ArgumentParser):
    """Setup testconfig command parser"""
    
    parser.add_argument(
        '--config',
        required=True,
        help='Path to configuration file to validate'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output with detailed validation results'
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Attempt to fix common configuration issues automatically'
    )


def _setup_sets_parser(parser: argparse.ArgumentParser):
    """Setup sets command parser"""
    
    # Mode selection (positional argument)
    parser.add_argument(
        'set_name',
        choices=['http', 'https', 'mtls'],
        help='''Configuration mode:
  http  - HTTP basic configuration
  https - HTTPS with SSL/TLS
  mtls  - Mutual TLS with client certificates'''
    )
    
    # Modifiers
    parser.add_argument(
        '--modifiers',
        nargs='+',
        choices=['token', 'roles'],
        help='''Configuration modifiers:
  token - Add token authentication
  roles - Add role-based access control (requires token)'''
    )
    parser.add_argument(
        '--no-dns-check',
        action='store_true',
        help='Disable DNS hostname checking (useful for Docker networks)'
    )
    
    # SSL configuration for https/mtls
    ssl_group = parser.add_argument_group('SSL Configuration')
    ssl_group.add_argument(
        '--cert-dir',
        default='./mtls_certificates/server',
        help='Directory containing SSL certificates (default: ./mtls_certificates/server)'
    )
    ssl_group.add_argument(
        '--key-dir',
        default='./mtls_certificates/server',
        help='Directory containing SSL private keys (default: ./mtls_certificates/server)'
    )
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument(
        '--output-dir',
        default='./configs',
        help='Output directory for configuration files (default: ./configs)'
    )
    output_group.add_argument(
        '--host',
        default='127.0.0.1',
        help='Server host address (default: 127.0.0.1)'
    )
    output_group.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Server port number (default: 8000)'
    )
    output_group.add_argument(
        '--proxy-url',
        help='Proxy URL for registration (auto-generated if not specified)'
    )


def _setup_server_parser(parser: argparse.ArgumentParser):
    """Setup server command parser"""
    
    parser.add_argument(
        '--config',
        required=True,
        help='Path to configuration file'
    )
    parser.add_argument(
        '--host',
        help='Override server host from configuration'
    )
    parser.add_argument(
        '--port',
        type=int,
        help='Override server port from configuration'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode with verbose logging'
    )
    parser.add_argument(
        '--reload',
        action='store_true',
        help='Enable auto-reload on configuration changes'
    )


def _setup_client_parser(parser: argparse.ArgumentParser):
    """Setup client command parser"""

    sub = parser.add_subparsers(dest='client_command')

    # health
    health = sub.add_parser('health', help='Call GET /health')
    health.add_argument('--protocol', choices=['http', 'https'], required=True, help='Connection protocol')
    health.add_argument('--host', default='127.0.0.1', help='Server host (default: 127.0.0.1)')
    health.add_argument('--port', type=int, required=True, help='Server port')
    health.add_argument('--token-header', default='X-API-Key', help='API key header name (default: X-API-Key)')
    health.add_argument('--token', help='API key token value')
    health.add_argument('--cert', help='Client cert path (for mTLS/HTTPS testing)')
    health.add_argument('--key', help='Client key path (for mTLS/HTTPS testing)')
    health.add_argument('--ca', help='CA cert path (verify server with this CA)')

    # jsonrpc
    j = sub.add_parser('jsonrpc', help='Call POST /api/jsonrpc')
    j.add_argument('--protocol', choices=['http', 'https'], required=True, help='Connection protocol')
    j.add_argument('--host', default='127.0.0.1', help='Server host (default: 127.0.0.1)')
    j.add_argument('--port', type=int, required=True, help='Server port')
    j.add_argument('--token-header', default='X-API-Key', help='API key header name (default: X-API-Key)')
    j.add_argument('--token', help='API key token value')
    j.add_argument('--cert', help='Client cert path (for mTLS/HTTPS testing)')
    j.add_argument('--key', help='Client key path (for mTLS/HTTPS testing)')
    j.add_argument('--ca', help='CA cert path (verify server with this CA)')
    j.add_argument('--method', required=True, help='JSON-RPC method')
    j.add_argument('--params', help='JSON string with params, default {}')
    j.add_argument('--id', type=int, default=1, help='Request id (default: 1)')

    # proxy register/unregister/list
    preg = sub.add_parser('proxy-register', help='Register adapter on registry')
    preg.add_argument('--proxy-url', required=True, help='Registry base URL, e.g. http://localhost:3005')
    preg.add_argument('--name', required=True, help='Adapter name')
    preg.add_argument('--url', required=True, help='Adapter base URL')
    preg.add_argument('--capabilities', nargs='*', help='Capabilities list')

    punreg = sub.add_parser('proxy-unregister', help='Unregister adapter from registry')
    punreg.add_argument('--proxy-url', required=True)
    punreg.add_argument('--name', required=True)

    plist = sub.add_parser('proxy-list', help='List registered adapters')
    plist.add_argument('--proxy-url', required=True)
