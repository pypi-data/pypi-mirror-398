"""
TestConfig Command

This module implements the testconfig command for validating configuration files.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import json
from typing import Dict, Any

try:
    from mcp_proxy_adapter.core.config_validator import ConfigValidator
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False


class TestConfigCommand:
    """Command for testing and validating configuration files."""
    
    def __init__(self):
        """Initialize the testconfig command."""
        pass
    
    def execute(self, args: Dict[str, Any]) -> int:
        """
        Execute the testconfig command.
        
        Args:
            args: Parsed command arguments
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        if not VALIDATION_AVAILABLE:
            print("❌ Configuration validation not available. Install the package to enable validation.")
            return 1
        
        config_file = args['config']
        verbose = args.get('verbose', False)
        fix_suggestions = args.get('fix_suggestions', False)
        json_output = args.get('json', False)
        
        try:
            # Load and validate configuration
            validator = ConfigValidator(config_file)
            validator.load_config()
            results = validator.validate_config()
            
            # Get validation summary
            summary = validator.get_validation_summary()
            
            if json_output:
                # Output results in JSON format
                self._output_json_results(summary, results, config_file)
            else:
                # Output human-readable results
                self._output_human_results(summary, results, config_file, verbose, fix_suggestions)
            
            # Return appropriate exit code
            return 0 if summary['is_valid'] else 1
            
        except Exception as e:
            print(f"❌ Error testing configuration: {e}")
            return 1
    
    def _output_json_results(self, summary: Dict[str, Any], results: list, config_file: str) -> None:
        """Output validation results in JSON format."""
        output = {
            "config_file": config_file,
            "summary": summary,
            "issues": []
        }
        
        for result in results:
            issue = {
                "level": result.level,
                "message": result.message,
                "section": result.section,
                "key": result.key if hasattr(result, 'key') else None,
                "suggestion": result.suggestion if hasattr(result, 'suggestion') else None
            }
            output["issues"].append(issue)
        
        print(json.dumps(output, indent=2, ensure_ascii=False))
    
    def _output_human_results(self, summary: Dict[str, Any], results: list, config_file: str, 
                            verbose: bool, fix_suggestions: bool) -> None:
        """Output validation results in human-readable format."""
        print("=" * 60)
        print("CONFIGURATION VALIDATION REPORT")
        print("=" * 60)
        print(f"Configuration file: {config_file}")
        print(f"Total issues: {summary['total_issues']}")
        print(f"Errors: {summary['errors']}")
        print(f"Warnings: {summary['warnings']}")
        print(f"Info: {summary['info']}")
        print(f"Configuration is valid: {'✅ YES' if summary['is_valid'] else '❌ NO'}")
        print("=" * 60)
        
        if results:
            print("\n📋 DETAILED ISSUES:")
            print("-" * 40)
            
            for i, result in enumerate(results, 1):
                level_symbol = {
                    "error": "❌",
                    "warning": "⚠️",
                    "info": "ℹ️"
                }.get(result.level, "❓")
                
                print(f"\n{i}. {level_symbol} [{result.level.upper()}]")
                print(f"   Message: {result.message}")
                
                if hasattr(result, 'section') and result.section:
                    location = f"{result.section}"
                    if hasattr(result, 'key') and result.key:
                        location += f".{result.key}"
                    print(f"   Location: {location}")
                
                if hasattr(result, 'suggestion') and result.suggestion:
                    print(f"   Suggestion: {result.suggestion}")
                
                if verbose:
                    print(f"   Full details: {result}")
        else:
            print("\n✅ No issues found in configuration!")
        
        if fix_suggestions and results:
            self._print_fix_suggestions(results)
    
    def _print_fix_suggestions(self, results: list) -> None:
        """Print suggestions for fixing configuration issues."""
        print("\n🔧 FIX SUGGESTIONS:")
        print("-" * 40)
        
        # Group suggestions by type
        suggestions = {
            "missing_files": [],
            "invalid_values": [],
            "missing_sections": [],
            "dependency_issues": [],
            "other": []
        }
        
        for result in results:
            if result.level == "error":
                message = result.message.lower()
                if "does not exist" in message or "not found" in message:
                    suggestions["missing_files"].append(result)
                elif "missing" in message and "section" in message:
                    suggestions["missing_sections"].append(result)
                elif "invalid" in message or "wrong type" in message:
                    suggestions["invalid_values"].append(result)
                elif "dependency" in message or "requires" in message:
                    suggestions["dependency_issues"].append(result)
                else:
                    suggestions["other"].append(result)
        
        # Print suggestions by category
        for category, issues in suggestions.items():
            if issues:
                print(f"\n📁 {category.replace('_', ' ').title()}:")
                for issue in issues:
                    print(f"  • {issue.message}")
                    if hasattr(issue, 'suggestion') and issue.suggestion:
                        print(f"    → {issue.suggestion}")
        
        print("\n💡 GENERAL RECOMMENDATIONS:")
        print("  • Use the configuration generator: mcp-proxy-adapter generate --help")
        print("  • Check the documentation: docs/EN/ALL_CONFIG_SETTINGS.md")
        print("  • Validate certificates and file paths")
        print("  • Ensure all required sections are present")


