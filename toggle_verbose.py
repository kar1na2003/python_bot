#!/usr/bin/env python3
"""
Toggle verbose mode for the MCTS bot
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def toggle_verbose(mode=None):
    """Toggle verbose mode in config.py"""

    config_path = "config.py"

    # Read current config
    with open(config_path, 'r') as f:
        content = f.read()

    # Determine new mode
    if mode is None:
        # Toggle current mode
        if 'VERBOSE_MODE = True' in content:
            new_mode = 'False'
            print("🔇 Verbose mode DISABLED")
        else:
            new_mode = 'True'
            print("🔊 Verbose mode ENABLED")
    else:
        # Set specific mode
        if mode.lower() in ['true', 'on', 'yes', '1']:
            new_mode = 'True'
            print("🔊 Verbose mode ENABLED")
        else:
            new_mode = 'False'
            print("🔇 Verbose mode DISABLED")

    # Replace the line
    old_line = 'VERBOSE_MODE = True'
    new_line = f'VERBOSE_MODE = {new_mode}'
    content = content.replace(old_line, new_line)

    old_line = 'VERBOSE_MODE = False'
    new_line = f'VERBOSE_MODE = {new_mode}'
    content = content.replace(old_line, new_line)

    # Write back
    with open(config_path, 'w') as f:
        f.write(content)

    print(f"Config updated. Run 'python main.py' to test.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        toggle_verbose(sys.argv[1])
    else:
        toggle_verbose()