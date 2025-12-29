#!/usr/bin/env python3
"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Enhanced script for setting up test environment for MCP Proxy Adapter.
Prepares the test environment with all necessary files, directories, and configurations.
Includes comprehensive documentation and validation for configuration settings.

This script accepts an output directory and copies required example files
and helper scripts into that directory, creating a ready-to-use workspace.
By default, the current working directory is used, so end-users can run
it in their project root after installing this framework in a virtual
environment.

Features:
- Comprehensive configuration documentation
- Validation of mutually exclusive settings
- Protocol-aware configuration generation
- Enhanced error handling and troubleshooting
"""
import os
import sys
import argparse
from pathlib import Path

# Import mcp_security_framework
try:
    from mcp_security_framework.schemas.config import (
        CertificateConfig,
        CAConfig,
        ServerCertConfig,
        ClientCertConfig,
    )

    SECURITY_FRAMEWORK_AVAILABLE = True
except ImportError:
    SECURITY_FRAMEWORK_AVAILABLE = False
    print("Warning: mcp_security_framework not available")

# Import setup modules
try:
    from mcp_proxy_adapter.examples.setup import (
        ConfigurationValidator,
        create_test_files,
        create_configuration_documentation,
        generate_enhanced_configurations,
        generate_certificates_with_framework,
        test_proxy_registration,
        run_full_test_suite,
        setup_test_environment,
    )
except ImportError:
    print("Warning: Setup modules not available")


def _get_package_paths() -> tuple[Path, Path]:
    """
    Get paths to the package and examples directory.

    Returns:
        Tuple of (package_path, examples_path)
    """
    # Get the directory containing this script
    script_dir = Path(__file__).parent.absolute()
    
    # Package path is the parent of examples
    package_path = script_dir.parent
    
    # Examples path
    examples_path = script_dir
    
    return package_path, examples_path


def validate_output_directory(output_dir: Path) -> bool:
    """
    Validate that the output directory is suitable for setup.

    Args:
        output_dir: Directory to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        # Check if directory exists
        if not output_dir.exists():
            print(f"📁 Creating output directory: {output_dir}")
            output_dir.mkdir(parents=True, exist_ok=True)
            return True

        # Check if directory is writable
        if not os.access(output_dir, os.W_OK):
            print(f"❌ Error: Directory {output_dir} is not writable")
            return False

        # Check if directory is empty (optional warning)
        contents = list(output_dir.iterdir())
        if contents:
            print(f"⚠️ Warning: Directory {output_dir} is not empty")
            print(f"   Found {len(contents)} items")
            response = input("   Continue anyway? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("   Setup cancelled")
                return False

        return True

    except Exception as e:
        print(f"❌ Error validating output directory: {e}")
        return False


def check_ports_available() -> bool:
    """
    Check if required ports are available.

    Returns:
        True if ports are available, False otherwise
    """
    import socket

    ports_to_check = [8080, 8443, 20005, 3005]
    unavailable_ports = []

    for port in ports_to_check:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                if result == 0:
                    unavailable_ports.append(port)
        except Exception:
            # If we can't check, assume it's available
            pass

    if unavailable_ports:
        print(f"⚠️ Warning: The following ports are in use: {unavailable_ports}")
        print("   This may cause issues when running the examples")
        response = input("   Continue anyway? (y/N): ").strip().lower()
        return response in ['y', 'yes']

    return True


def main() -> int:
    """
    Main function to set up the test environment.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Set up test environment for MCP Proxy Adapter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup_test_environment.py                    # Setup in current directory
  python setup_test_environment.py -o /path/to/test  # Setup in specific directory
  python setup_test_environment.py --no-certs        # Skip certificate generation
  python setup_test_environment.py --run-tests       # Run tests after setup
        """
    )

    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path.cwd(),
        help="Output directory for test environment (default: current directory)"
    )

    parser.add_argument(
        "--no-certs",
        action="store_true",
        help="Skip certificate generation"
    )

    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="Run tests after setup"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    print("🚀 MCP Proxy Adapter Test Environment Setup")
    print("=" * 50)

    # Validate output directory
    if not validate_output_directory(args.output_dir):
        print("❌ Setup failed: Invalid output directory")
        return 1

    # Check ports
    if not check_ports_available():
        print("❌ Setup cancelled: Port conflicts detected")
        return 1

    try:
        # Run setup
        success = setup_test_environment(args.output_dir)
        
        if not success:
            print("❌ Setup failed")
            return 1

        print("✅ Test environment setup completed successfully!")
        print(f"📁 Output directory: {args.output_dir.absolute()}")

        # Run tests if requested
        if args.run_tests:
            print("\\n🧪 Running tests...")
            test_success = run_full_test_suite(args.output_dir)
            if not test_success:
                print("⚠️ Some tests failed, but setup completed")
                return 1

        print("\\n🎉 Setup complete! You can now run the examples.")
        return 0

    except KeyboardInterrupt:
        print("\\n⚠️ Setup interrupted by user")
        return 1
    except Exception as e:
        print(f"\\n❌ Setup failed with error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
