#!/usr/bin/env python3
"""
Configuration Checker CLI for MCP Proxy Adapter
Validates configuration files and checks for common issues.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import argparse
import json
import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_proxy_adapter.config import Config


class ConfigChecker:
    """Configuration checker with validation and analysis."""
    
    def __init__(self):
        """
        Initialize configuration checker.
        """
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
    
    def check_config_file(self, config_path: str) -> bool:
        """
        Check a configuration file for issues.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            True if config is valid, False otherwise
        """
        self.errors.clear()
        self.warnings.clear()
        self.info.clear()
        
        print(f"🔍 Checking configuration: {config_path}")
        print("=" * 60)
        
        # Check if file exists
        if not os.path.exists(config_path):
            self.errors.append(f"Configuration file not found: {config_path}")
            return False
        
        # Check if file is readable
        if not os.access(config_path, os.R_OK):
            self.errors.append(f"Configuration file is not readable: {config_path}")
            return False
        
        try:
            # Load and parse JSON
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON format: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error reading configuration file: {e}")
            return False
        
        # Load with Config class
        try:
            config = Config(config_path)
        except Exception as e:
            self.errors.append(f"Error loading configuration with Config class: {e}")
            return False
        
        # Perform checks
        self._check_basic_structure(config_data)
        self._check_server_config(config)
        self._check_security_config(config)
        self._check_ssl_config(config)
        self._check_logging_config(config)
        self._check_file_paths(config_path, config)
        self._check_port_availability(config)
        
        # Print results
        self._print_results()
        
        return len(self.errors) == 0
    
    def _check_basic_structure(self, config_data: Dict[str, Any]) -> None:
        """Check basic configuration structure."""
        required_sections = ["server", "security", "logging", "transport"]
        
        for section in required_sections:
            if section not in config_data:
                self.errors.append(f"Missing required section: {section}")
            else:
                self.info.append(f"✅ Section '{section}' present")
    
    def _check_server_config(self, config: Config) -> None:
        """Check server configuration."""
        protocol = config.get("server.protocol")
        host = config.get("server.host")
        port = config.get("server.port")
        
        if not protocol:
            self.errors.append("Server protocol not specified")
        elif protocol not in ["http", "https", "mtls"]:
            self.errors.append(f"Invalid server protocol: {protocol}")
        else:
            self.info.append(f"✅ Server protocol: {protocol}")
        
        if not host:
            self.warnings.append("Server host not specified, using default")
        else:
            self.info.append(f"✅ Server host: {host}")
        
        if not port:
            self.errors.append("Server port not specified")
        elif not isinstance(port, int) or port < 1 or port > 65535:
            self.errors.append(f"Invalid server port: {port}")
        else:
            self.info.append(f"✅ Server port: {port}")
    
    def _check_security_config(self, config: Config) -> None:
        """Check security configuration."""
        security_enabled = config.get("security.enabled", False)
        tokens = config.get("security.tokens", {})
        roles = config.get("security.roles", {})
        roles_file = config.get("security.roles_file")
        
        if security_enabled:
            self.info.append("✅ Security enabled")
            
            if not tokens and not roles and not roles_file:
                self.warnings.append("Security enabled but no authentication methods configured")
            else:
                if tokens:
                    self.info.append(f"✅ Tokens configured: {len(tokens)} tokens")
                if roles:
                    self.info.append(f"✅ Roles configured: {len(roles)} roles")
                if roles_file:
                    self.info.append(f"✅ Roles file: {roles_file}")
        else:
            self.info.append("ℹ️ Security disabled")
    
    def _check_ssl_config(self, config: Config) -> None:
        """Check SSL configuration."""
        protocol = config.get("server.protocol")
        chk_hostname = config.get("transport.ssl.chk_hostname")
        
        if protocol in ["https", "mtls"]:
            self.info.append(f"✅ SSL protocol: {protocol}")
            
            if chk_hostname is None:
                self.warnings.append("chk_hostname not specified for SSL protocol")
            elif chk_hostname:
                self.info.append("✅ Hostname checking enabled")
            else:
                self.warnings.append("Hostname checking disabled for SSL protocol")
        else:
            if chk_hostname:
                self.warnings.append("Hostname checking enabled for non-SSL protocol")
            else:
                self.info.append("✅ Hostname checking disabled for HTTP")
    
    def _check_logging_config(self, config: Config) -> None:
        """Check logging configuration."""
        log_level = config.get("logging.level")
        log_file = config.get("logging.file")
        log_dir = config.get("logging.log_dir")
        
        if log_level and log_level.upper() in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            self.info.append(f"✅ Log level: {log_level}")
        else:
            self.warnings.append(f"Invalid or missing log level: {log_level}")
        
        if log_file:
            self.info.append(f"✅ Log file: {log_file}")
        
        if log_dir:
            self.info.append(f"✅ Log directory: {log_dir}")
    
    def _check_file_paths(self, config_path: str, config: Config) -> None:
        """Check file paths in configuration."""
        config_dir = Path(config_path).parent
        
        # Check roles file
        roles_file = config.get("security.roles_file")
        if roles_file:
            roles_path = config_dir / roles_file
            if not roles_path.exists():
                self.warnings.append(f"Roles file not found: {roles_path}")
            else:
                self.info.append(f"✅ Roles file exists: {roles_path}")
        
        # Check log directory
        log_dir = config.get("logging.log_dir")
        if log_dir:
            log_path = config_dir / log_dir
            if not log_path.exists():
                self.warnings.append(f"Log directory not found: {log_path}")
            else:
                self.info.append(f"✅ Log directory exists: {log_path}")
    
    def _check_port_availability(self, config: Config) -> None:
        """Check if the configured port is available."""
        import socket
        
        port = config.get("server.port")
        if not port:
            return
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                self.info.append(f"✅ Port {port} is available")
        except OSError:
            self.warnings.append(f"Port {port} is already in use")
    
    def _print_results(self) -> None:
        """Print check results."""
        if self.info:
            print("\n📋 Information:")
            for info in self.info:
                print(f"  {info}")
        
        if self.warnings:
            print("\n⚠️ Warnings:")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if self.errors:
            print("\n❌ Errors:")
            for error in self.errors:
                print(f"  {error}")
        
        print(f"\n📊 Summary:")
        print(f"  Information: {len(self.info)}")
        print(f"  Warnings: {len(self.warnings)}")
        print(f"  Errors: {len(self.errors)}")
        
        if self.errors:
            print(f"  Status: ❌ FAILED")
        elif self.warnings:
            print(f"  Status: ⚠️ WARNINGS")
        else:
            print(f"  Status: ✅ PASSED")


def check_all_configs(config_dir: str = "./configs") -> None:
    """Check all configuration files in a directory."""
    config_dir_path = Path(config_dir)
    
    if not config_dir_path.exists():
        print(f"❌ Configuration directory not found: {config_dir}")
        return
    
    config_files = list(config_dir_path.glob("*.json"))
    
    if not config_files:
        print(f"❌ No JSON configuration files found in: {config_dir}")
        return
    
    print(f"🔍 Checking {len(config_files)} configuration files in {config_dir}")
    print("=" * 80)
    
    checker = ConfigChecker()
    total_checked = 0
    total_passed = 0
    
    for config_file in sorted(config_files):
        if checker.check_config_file(str(config_file)):
            total_passed += 1
        total_checked += 1
        print("\n" + "-" * 80 + "\n")
    
    print(f"📊 Final Summary:")
    print(f"  Total files checked: {total_checked}")
    print(f"  Passed: {total_passed}")
    print(f"  Failed: {total_checked - total_passed}")
    print(f"  Success rate: {(total_passed / total_checked * 100):.1f}%")


def validate_config_syntax(config_path: str) -> bool:
    """Validate configuration syntax only."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            json.load(f)
        print(f"✅ Configuration syntax is valid: {config_path}")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON syntax: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False


def compare_configs(config1_path: str, config2_path: str) -> None:
    """Compare two configuration files."""
    print(f"🔍 Comparing configurations:")
    print(f"  Config 1: {config1_path}")
    print(f"  Config 2: {config2_path}")
    print("=" * 60)
    
    try:
        with open(config1_path, 'r') as f:
            config1 = json.load(f)
        with open(config2_path, 'r') as f:
            config2 = json.load(f)
    except Exception as e:
        print(f"❌ Error loading configurations: {e}")
        return
    
    # Compare key sections
    sections_to_compare = ["server", "security", "logging", "transport"]
    
    for section in sections_to_compare:
        print(f"\n📋 Section: {section}")
        
        if section not in config1 and section not in config2:
            print("  Both configs missing this section")
            continue
        elif section not in config1:
            print(f"  ❌ Missing in {config1_path}")
            continue
        elif section not in config2:
            print(f"  ❌ Missing in {config2_path}")
            continue
        
        if config1[section] == config2[section]:
            print("  ✅ Identical")
        else:
            print("  ⚠️ Different")
            # Show differences for key fields
            if section == "server":
                for key in ["protocol", "host", "port"]:
                    val1 = config1[section].get(key)
                    val2 = config2[section].get(key)
                    if val1 != val2:
                        print(f"    {key}: {val1} vs {val2}")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="MCP Proxy Adapter Configuration Checker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check a single configuration file
  python check_config.py configs/http.json
  
  # Check all configurations in a directory
  python check_config.py --all
  
  # Validate JSON syntax only
  python check_config.py --syntax configs/http.json
  
  # Compare two configurations
  python check_config.py --compare configs/http.json configs/https.json
        """
    )
    
    parser.add_argument(
        "config_file",
        nargs="?",
        help="Configuration file to check"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Check all configuration files in ./configs directory"
    )
    
    parser.add_argument(
        "--syntax",
        action="store_true",
        help="Validate JSON syntax only"
    )
    
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("CONFIG1", "CONFIG2"),
        help="Compare two configuration files"
    )
    
    parser.add_argument(
        "--config-dir",
        default="./configs",
        help="Configuration directory (default: ./configs)"
    )
    
    args = parser.parse_args()
    
    if args.compare:
        compare_configs(args.compare[0], args.compare[1])
    elif args.all:
        check_all_configs(args.config_dir)
    elif args.config_file:
        if args.syntax:
            validate_config_syntax(args.config_file)
        else:
            checker = ConfigChecker()
            checker.check_config_file(args.config_file)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
