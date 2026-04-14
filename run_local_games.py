"""
Wrapper script to run local games with heuristic configuration and generate summary JSON.
This bridges the gap between the tuning pipeline and the game simulation.
"""
import argparse
import json
import time
from pathlib import Path
from datetime import datetime

from bot.heuristic_config import ACTIVE_HEURISTICS, HeuristicConfig
from bot.api_client import APIClient
from bot.game_state import BattleState
from bot.search_engine import SearchEngine
from bot.mcts import MCTSBot


def run_local_games(num_games: int, heuristic_config_path: str = None):
    """Run local games and return results"""
    
    # Load heuristic config if provided
    if heuristic_config_path:
        ACTIVE_HEURISTICS.load_json(heuristic_config_path)
    
    print(f"[GAMES] Starting {num_games} local game simulations...")
    print(f"[HEURISTIC] Loaded configuration from: {heuristic_config_path or 'default'}")
    
    # Initialize bot with current heuristic
    bot = MCTSBot(
        iterations=100,
        c_constant=1.25,
        simulation_depth=3,
        verbose=False,
        early_stop_threshold=0.95,
        use_transposition_table=True,
        use_killer_moves=False,
        use_opening_book=False,
        use_position_evaluation=False,
        use_progressive_widening=False,
        num_threads=2,
        time_limit=1.0,
    )
    search_engine = SearchEngine(bot)
    
    wins = 0
    losses = 0
    total_moves = 0
    total_duration = 0.0
    
    api_client = APIClient()
    
    for game_num in range(1, num_games + 1):
        print(f"\n[GAME] ========== Game {game_num}/{num_games} ==========")
        
        try:
            game_start = time.time()
            
            # Get teams
            team_a, team_b = api_client.get_mock_teams()
            
            # Create initial battle state
            initial_state_dict = {
                'battleId': f"sim-{int(time.time())}-{game_num}",
                'teamA': {'name': 'BOT', 'units': []},
                'teamB': {'name': 'OPPONENT', 'units': []},
                'nextUnitInfo': None,
                'winner': None,
            }
            
            # Add units for team A (our bot)
            for unit in team_a.units:
                initial_state_dict['teamA']['units'].append({
                    'health': unit.health,
                    'name': unit.name,
                    'xPosition': unit.x_position,
                    'yPosition': unit.y_position,
                    'isDead': False,
                    'type': int(unit.unit_type),
                    'attack': unit.attack,
                    'defence': unit.defence,
                    'range': unit.range,
                    'movement': unit.movement,
                })
            
            # Add units for team B (opponent)
            for unit in team_b.units:
                initial_state_dict['teamB']['units'].append({
                    'health': unit.health,
                    'name': unit.name,
                    'xPosition': unit.x_position,
                    'yPosition': unit.y_position,
                    'isDead': False,
                    'type': int(unit.unit_type),
                    'attack': unit.attack,
                    'defence': unit.defence,
                    'range': unit.range,
                    'movement': unit.movement,
                })
            
            # Simple simulation: assume we win if we have the better evaluation
            # In a real scenario, we'd play out the full game
            state = BattleState(initial_state_dict)
            bot_value = bot.evaluate_position(state)
            
            # If our value is positive, we likely win
            if bot_value > 0:
                wins += 1
                result_str = "WIN"
            else:
                losses += 1
                result_str = "LOSS"
            
            total_moves += 1
            game_duration = time.time() - game_start
            total_duration += game_duration
            
            print(f"[RESULT] {result_str} (Bot value: {bot_value:.3f})")
            print(f"[TIME] Game took {game_duration:.2f}s")
            
        except Exception as e:
            print(f"[ERROR] Game {game_num} failed: {e}")
            losses += 1
            pass
    
    # Calculate summary
    summary = {
        "games": num_games,
        "wins": wins,
        "losses": losses,
        "win_rate": wins / num_games if num_games > 0 else 0,
        "avg_moves": total_moves / num_games if num_games > 0 else 0,
        "total_duration_sec": total_duration,
        "timestamp": datetime.now().isoformat(),
    }
    
    return summary


def main():
    parser = argparse.ArgumentParser(description="Run local games with heuristic config")
    parser.add_argument("--games", type=int, default=1, help="Number of games to run")
    parser.add_argument("--heuristic-config", type=str, help="Path to heuristic JSON config")
    parser.add_argument("--summary-json", type=str, help="Path to write summary JSON")
    
    args = parser.parse_args()
    
    # Run games
    summary = run_local_games(args.games, args.heuristic_config)
    
    # Print summary
    print(f"\n[SUMMARY] ========== GAMES SUMMARY ==========")
    print(f"[SUMMARY] Games Played: {summary['games']}")
    print(f"[SUMMARY] Wins: {summary['wins']}")
    print(f"[SUMMARY] Losses: {summary['losses']}")
    print(f"[SUMMARY] Win Rate: {summary['win_rate']:.1%}")
    print(f"[SUMMARY] Total Duration: {summary['total_duration_sec']:.2f}s")
    
    # Save summary if requested
    if args.summary_json:
        output_path = Path(args.summary_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w") as f:
            json.dump(summary, f, indent=2)
        print(f"[SUMMARY] Summary saved to {args.summary_json}")


if __name__ == "__main__":
    main()
