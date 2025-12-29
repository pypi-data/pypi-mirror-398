#!/usr/bin/env python3
"""
MCP Proxy Adapter CLI Application
Comprehensive command-line interface with multi-level help and configuration management

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp_proxy_adapter.cli.parser import create_main_parser  # noqa: E402


def main():
    """Main CLI entry point"""
    parser = create_main_parser()
    args = parser.parse_args()

    try:
        if args.command == 'generate':
            from mcp_proxy_adapter.cli.commands.generate import GenerateCommand
            return GenerateCommand().execute(vars(args))
        elif args.command == 'testconfig':
            from mcp_proxy_adapter.cli.commands.testconfig import TestConfigCommand
            return TestConfigCommand().execute(vars(args))
        elif args.command == 'sets':
            from mcp_proxy_adapter.cli.commands.sets import SetsCommand
            return SetsCommand().execute(vars(args))
        elif args.command == 'server':
            from mcp_proxy_adapter.cli.commands.server import ServerCommand
            return ServerCommand().execute(vars(args))
        elif args.command == 'config':
            if args.config_command == 'generate':
                from mcp_proxy_adapter.cli.commands.config_generate import config_generate_command
                return config_generate_command(args)
            if args.config_command == 'validate':
                from mcp_proxy_adapter.cli.commands.config_validate import config_validate_command
                return config_validate_command(args)
            if args.config_command == 'docs':
                from mcp_proxy_adapter.cli.commands.config_docs import config_docs_command
                return config_docs_command(args)
            print('Available: config generate|validate|docs')
            return 1
        elif args.command == 'client':
            from mcp_proxy_adapter.cli.commands.client import client_command
            return client_command(args)
        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
