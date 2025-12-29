"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

CLI command: config validate (Configuration validation)
Supports both SimpleConfig and full configuration formats.
Uses the same ConfigValidator as server startup.
"""

from __future__ import annotations

import argparse
import json
import sys
from argparse import Namespace
from pathlib import Path

from mcp_proxy_adapter.core.validation.config_validator import ConfigValidator


def config_validate_command(args: Namespace) -> int:
    """
    Validate configuration file using ConfigValidator.
    
    This uses the same validator as server startup to ensure consistency.
    """
    config_file = Path(args.file)
    
    if not config_file.exists():
        print(f"❌ Configuration file not found: {config_file}")
        return 1
    
    try:
        # Load configuration
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in configuration file: {e}")
        return 1
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return 1
    
    # Use the same ConfigValidator as server startup
    validator = ConfigValidator(config_path=str(config_file))
    validator.config_data = config_data
    validation_results = validator.validate_config()
    
    # Separate errors and warnings
    errors = [r for r in validation_results if r.level == "error"]
    warnings = [r for r in validation_results if r.level == "warning"]
    
    if errors:
        print("❌ Validation failed:")
        for err in errors:
            section_info = f" ({err.section}" + (f".{err.key}" if err.key else "") + ")" if err.section else ""
            print(f"   - {err.message}{section_info}")
        if warnings:
            print("\n⚠️  Warnings:")
            for warn in warnings:
                section_info = f" ({warn.section}" + (f".{warn.key}" if warn.key else "") + ")" if warn.section else ""
                print(f"   - {warn.message}{section_info}")
        return 1
    
    if warnings:
        print("✅ Validation passed with warnings:")
        for warn in warnings:
            section_info = f" ({warn.section}" + (f".{warn.key}" if warn.key else "") + ")" if warn.section else ""
            print(f"   ⚠️  {warn.message}{section_info}")
        return 0
    
    print("✅ Validation OK")
    return 0


def main() -> int:
    """Main entry point for adapter-cfg-val CLI command."""
    parser = argparse.ArgumentParser(
        prog="adapter-cfg-val",
        description="Validate configuration file for MCP Proxy Adapter"
    )
    parser.add_argument(
        '--file',
        required=True,
        help='Path to configuration file'
    )
    
    args = parser.parse_args()
    return config_validate_command(args)


if __name__ == "__main__":
    sys.exit(main())

