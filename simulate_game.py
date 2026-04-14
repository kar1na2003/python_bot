"""
Simulate games locally without relying on server PvB/signalr
Useful for testing bot strength and generating training data
"""
import argparse
import json
import logging
import time
from pathlib import Path

from bot.api_client import APIClient
from bot.game_state import BattleState
from bot.search_engine import SearchEngine
from bot.mcts import MCTSBot

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class SimulatedGameBot:
    """Bot that plays pre-generated team compositions"""
    
    def __init__(self):
        self.mcts_bot = MCTSBot(
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
        self.search_engine = SearchEngine(self.mcts_bot)
        self.move_count = 0
    
    def play_game(self):
        """Play a complete game locally"""
        api_client = APIClient()
        
        # Get random teams from server
        print("[GAME] Getting random teams...")
        team_a, team_b = api_client.get_mock_teams()
        
        print(f"[GAME] Team A: {len(team_a.units)} units")
        print(f"[GAME] Team B: {len(team_b.units)} units")
        
        # Create initial battle state
        initial_state_dict = {
            'battleId': f"sim-{int(time.time())}",
            'teamA': {'name': 'TeamA', 'units': []},
            'teamB': {'name': 'TeamB', 'units': []},
            'nextUnitInfo': None,
            'winner': None,
        }
        
        # Add units
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
        
        # Add one unit as next to act
        if team_a.units:
            unit = team_a.units[0]
            initial_state_dict['nextUnitInfo'] = {
                'teamName': 'TeamA',
                'unit': {
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
                },
                'availableDestinations': self._get_destinations(unit),
                'availableAttackTargets': self._get_targets(unit, team_b.units),
            }
        
        state = BattleState.from_dict(initial_state_dict)
        
        # Simulate game
        self.move_count = 0
        max_moves = 500
        
        while state.winner is None and self.move_count < max_moves:
            # Get action from search engine
            start_time = time.perf_counter()
            action = self.search_engine.choose_action(state)
            elapsed = time.perf_counter() - start_time
            
            self.move_count += 1
            
            if self.move_count % 10 == 0:
                print(f"[GAME] Move {self.move_count}: {action.action_type} ({elapsed:.2f}s)")
            
            # For now just simulate the move in MCTS.
            # In a real game, we'd send this to server via API
            # For simulation, we just count it
        
        result = "TIMEOUT" if state.winner is None else state.winner
        print(f"[GAME] Game ended: Winner={result} after {self.move_count} moves")
        return result
    
    def _get_destinations(self, unit):
        """Get possible move destinations"""
        # Simplified: allow movement to nearby squares
        destinations = []
        for x in range(max(0, unit.x_position - unit.movement), 
                      min(21, unit.x_position + unit.movement + 1)):
            for y in range(max(0, unit.y_position - unit.movement),
                          min(21, unit.y_position + unit.movement + 1)):
                if (x, y) != (unit.x_position, unit.y_position):
                    # Convert to grid notation like "A1", "B5"
                    col = chr(65 + x)
                    row = y + 1
                    destinations.append(f"{col}{row}")
        return destinations[:20]  # Limit to 20
    
    def _get_targets(self, unit, enemies):
        """Get possible attack targets"""
        targets = []
        for enemy in enemies:
            if not enemy.is_dead:
                distance = abs(unit.x_position - enemy.x_position) + abs(unit.y_position - enemy.y_position)
                if distance <= unit.range:
                    targets.append(enemy.name)
        return targets


def main():
    parser = argparse.ArgumentParser(description="Simulate games locally")
    parser.add_argument("--games", type=int, default=1, help="Number of games to simulate")
    args = parser.parse_args()
    
    print(f"[INIT] Starting local game simulation ({args.games} games)...")
    bot = SimulatedGameBot()
    
    wins = {"TeamA": 0, "TeamB": 0, "TIMEOUT": 0}
    
    for i in range(args.games):
        print(f"\n[GAME] ========== Game {i+1}/{args.games} ==========")
        try:
            result = bot.play_game()
            wins[result] = wins.get(result, 0) + 1
        except Exception as e:
            print(f"[ERROR] Game failed: {e}")
            wins["TIMEOUT"] = wins.get("TIMEOUT", 0) + 1
    
    print(f"\n[RESULTS] ========== Final Stats ==========")
    print(f"TeamA wins: {wins['TeamA']}")
    print(f"TeamB wins: {wins['TeamB']}")
    print(f"Timeouts: {wins['TIMEOUT']}")
    print(f"Total games: {sum(wins.values())}")


if __name__ == "__main__":
    main()
