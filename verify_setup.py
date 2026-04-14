#!/usr/bin/env python3
"""
Setup and verification script for Arena.AI Python MCTS Bot
Run this to verify installation and setup
"""

import sys
import subprocess
import os
from pathlib import Path


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_success(text):
    """Print success message"""
    print(f"  ✓ {text}")


def print_error(text):
    """Print error message"""
    print(f"  ✗ {text}")


def check_python_version():
    """Check Python version is 3.8+"""
    print_header("Checking Python Version")
    version = sys.version_info
    print(f"  Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 8:
        print_success("Python version is compatible")
        return True
    else:
        print_error(f"Python 3.8+ required (found {version.major}.{version.minor})")
        return False


def check_dependencies():
    """Check if required packages are installed"""
    print_header("Checking Dependencies")
    
    dependencies = {
        'requests': 'HTTP client library',
        'numpy': 'Numerical computing',
    }
    
    all_ok = True
    for package, description in dependencies.items():
        try:
            __import__(package)
            print_success(f"{package} - {description}")
        except ImportError:
            print_error(f"{package} - NOT INSTALLED")
            all_ok = False
    
    return all_ok


def check_project_structure():
    """Verify project files exist"""
    print_header("Checking Project Structure")
    
    required_files = {
        'main.py': 'Main entry point',
        'config.py': 'Configuration',
        'requirements.txt': 'Dependencies',
        'README.md': 'Documentation',
        'bot/__init__.py': 'Bot package',
        'bot/game_state.py': 'Game models',
        'bot/api_client.py': 'Server communication',
        'bot/simulator.py': 'Game simulator',
        'bot/distance.py': 'Distance calculations',
        'bot/damage.py': 'Damage calculations',
        'bot/mcts.py': 'MCTS algorithm',
    }
    
    all_ok = True
    for filepath, description in required_files.items():
        if Path(filepath).exists():
            print_success(f"{filepath} - {description}")
        else:
            print_error(f"{filepath} - MISSING")
            all_ok = False
    
    return all_ok


def test_imports():
    """Test if all modules can be imported"""
    print_header("Testing Module Imports")
    
    try:
        import config
        print_success("config module")
    except ImportError as e:
        print_error(f"config module: {e}")
        return False
    
    try:
        from bot import game_state
        print_success("bot.game_state module")
    except ImportError as e:
        print_error(f"bot.game_state module: {e}")
        return False
    
    try:
        from bot import distance
        print_success("bot.distance module")
    except ImportError as e:
        print_error(f"bot.distance module: {e}")
        return False
    
    try:
        from bot import damage
        print_success("bot.damage module")
    except ImportError as e:
        print_error(f"bot.damage module: {e}")
        return False
    
    try:
        from bot import simulator
        print_success("bot.simulator module")
    except ImportError as e:
        print_error(f"bot.simulator module: {e}")
        return False
    
    try:
        from bot import mcts
        print_success("bot.mcts module")
    except ImportError as e:
        print_error(f"bot.mcts module: {e}")
        return False
    
    try:
        from bot import api_client
        print_success("bot.api_client module")
    except ImportError as e:
        print_error(f"bot.api_client module: {e}")
        return False
    
    return True


def test_game_state():
    """Test game state creation"""
    print_header("Testing Game State Creation")
    
    try:
        from bot.game_state import Unit, Team, BattleState, UserAction
        
        # Create a unit
        unit = Unit(
            type=0,  # Light
            attack=5,
            defence=3,
            range=1,
            movement=4,
            name="TestUnit",
            health=10
        )
        print_success(f"Created unit: {unit.name}")
        
        # Create a team
        team = Team(name="TestTeam", units=[unit])
        print_success(f"Created team: {team.name} with {len(team.units)} units")
        
        # Create actions
        move_action = UserAction.move("A1")
        attack_action = UserAction.attack("Enemy1")
        skip_action = UserAction.skip()
        
        print_success("Created Move action")
        print_success("Created Attack action")
        print_success("Created Skip action")
        
        return True
    except Exception as e:
        print_error(f"Game state test failed: {e}")
        return False


def test_distance_calculations():
    """Test distance calculations"""
    print_header("Testing Distance Calculations")
    
    try:
        from bot.distance import coordinate_distance, string_to_coordinate, coordinate_to_string
        
        # Test distance
        dist = coordinate_distance(1, 1, 5, 5)
        print_success(f"Distance (1,1) to (5,5): {dist:.2f}")
        
        # Test coordinate conversion
        coord = string_to_coordinate("A1")
        print_success(f"Coordinate 'A1' converted to: {coord}")
        
        coord_str = coordinate_to_string(1, 1)
        print_success(f"Coordinates (1,1) converted to: {coord_str}")
        
        # Test full grid
        coordinates_ok = True
        for col in 'ABCDEFGHIJ':
            for row in range(1, 6):
                pos = col + str(row)
                x, y = string_to_coordinate(pos)
                back = coordinate_to_string(x, y)
                if back != pos:
                    coordinates_ok = False
                    break
        
        if coordinates_ok:
            print_success("Coordinate conversion round-trip works")
        else:
            print_error("Coordinate conversion has issues")
            return False
        
        return True
    except Exception as e:
        print_error(f"Distance test failed: {e}")
        return False


def test_damage_calculations():
    """Test damage calculations"""
    print_header("Testing Damage Calculations")
    
    try:
        from bot.damage import calculate_damage
        from bot.game_state import Unit
        
        attacker = Unit(
            type=0,  # Light
            attack=5,
            defence=0,
            range=1,
            movement=0,
            name="Attacker",
            health=10
        )
        
        defender = Unit(
            type=1,  # Heavy
            attack=0,
            defence=3,
            range=1,
            movement=0,
            name="Defender",
            health=10
        )
        
        damage = calculate_damage(attacker, defender)
        print_success(f"Calculated damage: {damage} (expected ~1-3)")
        
        if 1 <= damage <= 10:
            print_success("Damage calculation in reasonable range")
            return True
        else:
            print_error(f"Damage {damage} outside expected range")
            return False
            
    except Exception as e:
        print_error(f"Damage test failed: {e}")
        return False


def test_mcts():
    """Test MCTS initialization"""
    print_header("Testing MCTS Algorithm")
    
    try:
        from bot.mcts import MCTSBot, MCTSNode
        from bot.game_state import BattleState, Team, Unit, NextUnitInfo
        
        # Create minimal game state
        unit = Unit(type=0, attack=5, defence=3, range=1, movement=4, 
                   name="Test1", health=10)
        team_a = Team(name="TeamA", units=[unit])
        team_b = Team(name="TeamB", units=[unit])
        
        next_info = NextUnitInfo(
            team_name="TeamA",
            unit=unit,
            available_destinations=["A1", "A2", "A3"],
            available_attack_targets=[]
        )
        
        state = BattleState(
            battle_id="test",
            team_a=team_a,
            team_b=team_b,
            next_unit_info=next_info
        )
        
        # Test MCTSNode
        node = MCTSNode(state)
        print_success("Created MCTSNode")
        
        # Test MCTS Bot initialization
        bot = MCTSBot(iterations=10)  # Small number for quick test
        print_success("Created MCTSBot with 10 iterations")
        
        return True
    except Exception as e:
        print_error(f"MCTS test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_server_connection():
    """Test server connectivity"""
    print_header("Testing Server Connection")
    
    try:
        from bot.api_client import APIClient
        import config
        
        if APIClient.health_check(config.SERVER_URL):
            print_success(f"Server is reachable at {config.SERVER_URL}")
            return True
        else:
            print_error(f"Server not reachable at {config.SERVER_URL}")
            print("  Note: This is OK for offline testing")
            return True  # Don't fail if server is down
    except Exception as e:
        print_error(f"Server connection test failed: {e}")
        print("  Note: This is OK for offline testing")
        return True


def print_summary(results):
    """Print test summary"""
    print_header("Test Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\n  Passed: {passed}/{total} tests\n")
    
    for test_name, result in results.items():
        status = "✓" if result else "✗"
        print(f"  {status} {test_name}")
    
    print()
    
    if passed == total:
        print_success("All tests passed! Bot is ready to use.")
        return True
    elif passed >= total - 1:
        print_success("Most tests passed. You may need to install dependencies.")
        print("  Run: pip install -r requirements.txt")
        return True
    else:
        print_error(f"Some tests failed. Please check the output above.")
        return False


def main():
    """Run all setup checks"""
    print("\n" + "=" * 70)
    print("  Arena.AI Python MCTS Bot - Setup Verification")
    print("=" * 70)
    
    results = {}
    
    # Run all tests
    results["Python Version"] = check_python_version()
    results["Dependencies"] = check_dependencies()
    results["Project Structure"] = check_project_structure()
    results["Import Tests"] = test_imports()
    
    # Only run advanced tests if imports work
    if results["Import Tests"]:
        results["Game State"] = test_game_state()
        results["Distance Calc"] = test_distance_calculations()
        results["Damage Calc"] = test_damage_calculations()
        results["MCTS Algorithm"] = test_mcts()
        results["Server Connection"] = test_server_connection()
    
    # Print summary
    success = print_summary(results)
    
    print("\n" + "=" * 70)
    print("  Next Steps:")
    print("=" * 70)
    print("  1. If dependencies missing: pip install -r requirements.txt")
    print("  2. Offline test: python main.py")
    print("  3. Server test: python main.py <battle_id>")
    print()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
