#!/usr/bin/env python3
"""
Update Configuration Files with Correct Certificate Paths
This script updates all configuration files to use the correct certificate paths.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""
import json
from pathlib import Path
from typing import Dict, Any

from required_certificates import CONFIG_CERTIFICATE_MAPPINGS


class ConfigUpdater:
    """Updates configuration files with correct certificate paths."""
    
    def __init__(self):
        """Initialize the config updater."""
        self.working_dir = Path.cwd()
        self.configs_dir = self.working_dir / "configs"
    
    def print_step(self, step: str, description: str):
        """Print a formatted step header."""
        print(f"\n{'=' * 60}")
        print(f"🔧 STEP {step}: {description}")
        print(f"{'=' * 60}")
    
    def print_success(self, message: str):
        """Print a success message."""
        print(f"✅ {message}")
    
    def print_error(self, message: str):
        """Print an error message."""
        print(f"❌ {message}")
    
    def print_info(self, message: str):
        """Print an info message."""
        print(f"ℹ️  {message}")
    
    def update_config_file(self, config_file: str, certificate_mappings: Dict[str, str]) -> bool:
        """Update a single configuration file with correct certificate paths."""
        config_path = self.configs_dir / config_file
        
        if not config_path.exists():
            self.print_error(f"Configuration file not found: {config_file}")
            return False
        
        try:
            # Load configuration
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Update certificate paths
            updated = False
            for path, new_value in certificate_mappings.items():
                if self.update_nested_path(config, path, new_value):
                    updated = True
            
            if updated:
                # Save updated configuration
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                self.print_success(f"Updated {config_file}")
                return True
            else:
                self.print_info(f"No updates needed for {config_file}")
                return True
                
        except Exception as e:
            self.print_error(f"Failed to update {config_file}: {e}")
            return False
    
    def update_nested_path(self, config: Dict[str, Any], path: str, value: str) -> bool:
        """Update a nested path in configuration dictionary."""
        keys = path.split('.')
        current = config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current:
                return False
            current = current[key]
        
        # Update the target key
        target_key = keys[-1]
        if target_key in current and current[target_key] != value:
            current[target_key] = value
            return True
        
        return False
    
    def update_all_configs(self) -> bool:
        """Update all configuration files with correct certificate paths."""
        self.print_step("1", "Updating Configuration Files")
        
        success_count = 0
        total_count = len(CONFIG_CERTIFICATE_MAPPINGS)
        
        for config_file, certificate_mappings in CONFIG_CERTIFICATE_MAPPINGS.items():
            self.print_info(f"Updating {config_file}...")
            if self.update_config_file(config_file, certificate_mappings):
                success_count += 1
        
        # Print summary
        self.print_step("2", "Update Summary")
        print(f"📊 Configuration Update Results:")
        print(f"   Total configurations: {total_count}")
        print(f"   Successfully updated: {success_count}")
        print(f"   Failed: {total_count - success_count}")
        print(f"   Success rate: {(success_count/total_count)*100:.1f}%")
        
        return success_count == total_count


def main():
    """Main entry point."""
    updater = ConfigUpdater()
    
    try:
        success = updater.update_all_configs()
        if success:
            print(f"\n🎉 All configuration files updated successfully!")
        else:
            print(f"\n❌ Some configuration files failed to update")
        return success
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
