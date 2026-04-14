#!/usr/bin/env python3
"""
Performance Profile Switcher for Arena.AI Python MCTS Bot
"""

import sys
import os

def switch_profile(profile_name):
    """Switch to a different performance profile"""

    valid_profiles = ["FAST", "BALANCED", "ACCURATE", "ADVANCED", "EXPERIMENTAL"]

    if profile_name.upper() not in valid_profiles:
        print(f"❌ Invalid profile: {profile_name}")
        print(f"Valid profiles: {', '.join(valid_profiles)}")
        return False

    config_path = "config.py"

    # Read current config
    with open(config_path, 'r') as f:
        content = f.read()

    # Replace the profile line
    old_line = 'PERFORMANCE_PROFILE = "FAST"  # Options: "FAST", "BALANCED", "ACCURATE"'
    new_line = f'PERFORMANCE_PROFILE = "{profile_name.upper()}"  # Options: "FAST", "BALANCED", "ACCURATE", "ADVANCED", "EXPERIMENTAL"'

    if old_line in content:
        content = content.replace(old_line, new_line)
    else:
        # Try to find and replace any existing profile
        for profile in valid_profiles:
            old_pattern = f'PERFORMANCE_PROFILE = "{profile}"'
            if old_pattern in content:
                content = content.replace(old_pattern, f'PERFORMANCE_PROFILE = "{profile_name.upper()}"')
                break

    # Write back
    with open(config_path, 'w') as f:
        f.write(content)

    print(f"✅ Switched to {profile_name.upper()} profile")
    return True

def show_profiles():
    """Show available profiles and their settings"""
    print("🚀 Arena.AI Bot Performance Profiles:")
    print()
    print("FAST (1-2 seconds per move):")
    print("  - 100 MCTS iterations")
    print("  - 5 turn simulation depth")
    print("  - Early stop at 80% win rate")
    print()
    print("BALANCED (3-5 seconds per move):")
    print("  - 500 MCTS iterations")
    print("  - 10 turn simulation depth")
    print("  - Early stop at 85% win rate")
    print()
    print("ACCURATE (5-10 seconds per move):")
    print("  - 1000 MCTS iterations")
    print("  - Full game simulation")
    print("  - Early stop at 90% win rate")
    print()
    print("ADVANCED (2-4 seconds per move):")
    print("  - 500 MCTS iterations + advanced features")
    print("  - 8 turn simulation + position evaluation")
    print("  - Transposition table, killer moves, opening book")
    print("  - Early stop at 85% win rate")
    print()
    print("EXPERIMENTAL (1-3 seconds per move):")
    print("  - 200 MCTS iterations + ALL advanced features")
    print("  - Parallel processing, iterative deepening")
    print("  - Progressive widening, position evaluation")
    print("  - Early stop at 80% win rate")
    print()
    print("Usage: python switch_profile.py <profile_name>")
    print("Example: python switch_profile.py advanced")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        show_profiles()
        sys.exit(1)

    profile = sys.argv[1].upper()
    if switch_profile(profile):
        print("🎮 Run 'python main.py' to test the new settings!")
    else:
        sys.exit(1)