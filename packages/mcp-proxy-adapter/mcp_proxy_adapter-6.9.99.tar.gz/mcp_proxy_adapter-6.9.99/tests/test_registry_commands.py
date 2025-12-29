#!/usr/bin/env python3
"""
Test script to check registry commands.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mcp_proxy_adapter'))

from mcp_proxy_adapter.commands.command_registry import registry
from mcp_proxy_adapter.commands.builtin_commands import register_builtin_commands

print("Testing registry commands...")

# Register built-in commands first
try:
    count = register_builtin_commands()
    print(f"✅ Registered {count} built-in commands")
except Exception as e:
    print(f"❌ Failed to register built-in commands: {e}")

# List all registered commands
print("\nBuilt-in commands:")
all_commands = registry.get_all_commands() if hasattr(registry, 'get_all_commands') else registry._commands
for name, command in all_commands.items():
    cmd_type = registry._command_types.get(name, "unknown")
    if cmd_type == "builtin":
        print(f"  - {name}: {command.__name__ if hasattr(command, '__name__') else command.__class__.__name__}")

builtin_count = sum(1 for t in registry._command_types.values() if t == "builtin")
print(f"\nTotal built-in commands: {builtin_count}")

# Test specific commands
test_commands = ["echo", "list", "help", "health"]
for cmd_name in test_commands:
    try:
        cmd = registry.get_command(cmd_name)
        if cmd:
            print(f"✅ {cmd_name}: {cmd.__class__.__name__}")
        else:
            print(f"❌ {cmd_name}: Not found")
    except Exception as e:
        print(f"❌ {cmd_name}: Error - {e}")

# Test registry methods
print(f"\nRegistry methods:")
try:
    echo_cmd = registry.get_command('echo')
    print(f"  - get_command('echo'): {echo_cmd.__name__ if hasattr(echo_cmd, '__name__') else echo_cmd}")
except Exception as e:
    print(f"  - get_command('echo'): Error - {e}")

try:
    has_cmd = registry.command_exists('echo') if hasattr(registry, 'command_exists') and registry._manager else ('echo' in registry._commands)
    print(f"  - command_exists('echo'): {has_cmd}")
except Exception as e:
    has_cmd = 'echo' in registry._commands
    print(f"  - command_exists('echo'): {has_cmd} (via _commands)")

all_cmds = registry.get_all_commands() if hasattr(registry, 'get_all_commands') else registry._commands
print(f"  - get_all_commands(): {list(all_cmds.keys())}")
