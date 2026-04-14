"""
Game Simulator - Simulates game mechanics and state transitions
"""

from typing import List, Tuple, Optional
from copy import deepcopy
from .game_state import BattleState, Unit, UserAction, ActionType
from .distance import (
    get_distance_to_position, can_attack_without_moving, 
    get_available_destinations, string_to_coordinate, coordinate_to_string,
    move, is_near
)
from .damage import calculate_damage


class GameSimulator:
    """Simulates game mechanics and applies actions to battle state"""
    
    @staticmethod
    def get_valid_actions(state: BattleState) -> List[UserAction]:
        """Get all valid actions for current unit"""
        if state.is_game_over:
            return []
        
        actions = []
        unit = state.next_unit_info.unit
        
        # Add all valid move actions
        for dest in state.next_unit_info.available_destinations:
            actions.append(UserAction.move(dest))
        
        # Add all valid attack actions
        for target in state.next_unit_info.available_attack_targets:
            actions.append(UserAction.attack(target))
        
        # Always can skip
        actions.append(UserAction.skip())
        
        return actions
    
    @staticmethod
    def apply_action(state: BattleState, action: UserAction) -> BattleState:
        """Apply an action to game state and return new state"""
        new_state = state.deep_copy()
        
        if action.action_type == ActionType.SKIP:
            GameSimulator._finish_unit_turn(new_state)
            return new_state
        
        if action.action_type == ActionType.MOVE:
            if not GameSimulator._execute_move(new_state, action.destination):
                # Invalid move - skip turn
                GameSimulator._finish_unit_turn(new_state)
            return new_state
        
        if action.action_type == ActionType.ATTACK:
            if not GameSimulator._execute_attack(new_state, action.target):
                # Invalid attack - skip turn
                GameSimulator._finish_unit_turn(new_state)
            return new_state
        
        # Unknown action type, skip
        GameSimulator._finish_unit_turn(new_state)
        return new_state
    
    @staticmethod
    def _execute_move(state: BattleState, destination: str) -> bool:
        """Execute move action. Returns True if successful."""
        if destination not in state.next_unit_info.available_destinations:
            return False
        
        try:
            x, y = string_to_coordinate(destination)
        except (ValueError, IndexError):
            return False
        
        unit = state.next_unit_info.unit
        move(unit, x, y)
        
        # After moving, check available attacks
        targets = GameSimulator._get_available_attack_targets(state, unit)
        if targets:
            # Can now attack
            state.next_unit_info.available_destinations = []
            state.next_unit_info.available_attack_targets = targets
        else:
            # No targets, finish turn
            GameSimulator._finish_unit_turn(state)
        
        return True
    
    @staticmethod
    def _execute_attack(state: BattleState, target_name: str) -> bool:
        """Execute attack action. Returns True if successful."""
        if target_name not in state.next_unit_info.available_attack_targets:
            return False
        
        attacker = state.next_unit_info.unit
        target = state.get_unit_by_name(target_name)
        
        if not target or target.is_dead:
            return False
        
        # Calculate damage
        damage = calculate_damage(attacker, target)
        target.health -= damage
        
        # Check if target died
        if target.is_dead:
            # Update game winner if needed
            GameSimulator._check_and_update_winner(state)
            GameSimulator._finish_unit_turn(state)
            return True
        
        # Counter-attack logic
        if can_attack_without_moving(target, attacker):
            counter_damage = calculate_damage(target, attacker)
            counter_damage = counter_damage // 2  # Counter does half damage
            attacker.health -= counter_damage
            
            if attacker.is_dead:
                GameSimulator._check_and_update_winner(state)
        
        # Finish turn after attack
        GameSimulator._finish_unit_turn(state)
        return True
    
    @staticmethod
    def _get_available_attack_targets(state: BattleState, unit: Unit) -> List[str]:
        """Get list of units that can be attacked"""
        enemy_team = state.enemy_team
        targets = []
        
        for enemy in enemy_team.alive_units:
            if can_attack_without_moving(unit, enemy):
                targets.append(enemy.name)
        
        return targets
    
    @staticmethod
    def _finish_unit_turn(state: BattleState):
        """Move to next unit's turn"""
        GameSimulator._update_next_unit(state)
    
    @staticmethod
    def _update_next_unit(state: BattleState):
        """Calculate and set the next unit to act"""
        alive_units = [u for u in state.team_a.units + state.team_b.units if not u.is_dead]
        if not alive_units:
            GameSimulator._check_and_update_winner(state)
            return

        # Sort by movement descending and preserve original ordering for ties
        ordered_units = sorted(
            enumerate(alive_units),
            key=lambda item: (-item[1].movement, item[0])
        )
        ordered_units = [unit for _, unit in ordered_units]

        current_name = state.next_unit_info.unit.name
        try:
            current_index = next(i for i, unit in enumerate(ordered_units) if unit.name == current_name)
        except StopIteration:
            current_index = -1

        next_index = (current_index + 1) % len(ordered_units)
        next_unit = ordered_units[next_index]

        next_team = state.team_a if next_unit in state.team_a.units else state.team_b

        state.next_unit_info.unit = next_unit
        state.next_unit_info.team_name = next_team.name
        state.next_unit_info.available_destinations = GameSimulator._get_available_destinations(state, next_unit)
        state.next_unit_info.available_attack_targets = GameSimulator._get_available_attack_targets(state, next_unit)
    
    @staticmethod
    def _get_available_destinations(state: BattleState, unit: Unit) -> List[str]:
        """Get all valid movement destinations"""
        all_units = state.team_a.units + state.team_b.units
        valid_positions = get_available_destinations(unit, all_units)
        
        # Convert to string format
        destinations = []
        for x, y in valid_positions:
            try:
                dest_str = coordinate_to_string(x, y)
                destinations.append(dest_str)
            except ValueError:
                pass
        
        return destinations
    
    @staticmethod
    def _check_and_update_winner(state: BattleState):
        """Check if game is over and update winner"""
        if not state.team_a.is_anyone_alive:
            state.winner = state.team_b.name
        elif not state.team_b.is_anyone_alive:
            state.winner = state.team_a.name
    
    @staticmethod
    def simulate_random_playout(state: BattleState, max_depth: Optional[int] = None) -> str:
        """
        Run a random simulation from current state until game ends.
        Returns the winner name.
        """
        sim_state = state.deep_copy()
        depth = 0
        
        while not sim_state.is_game_over:
            if max_depth and depth >= max_depth:
                # Decide winner based on unit advantage
                team_a_score = len(sim_state.team_a.alive_units) * 10 + sum(u.health for u in sim_state.team_a.alive_units)
                team_b_score = len(sim_state.team_b.alive_units) * 10 + sum(u.health for u in sim_state.team_b.alive_units)
                
                if team_a_score > team_b_score:
                    return sim_state.team_a.name
                elif team_b_score > team_a_score:
                    return sim_state.team_b.name
                else:
                    return sim_state.team_a.name  # Tie
            
            # Get valid actions
            actions = GameSimulator.get_valid_actions(sim_state)
            if not actions:
                break
            
            # Choose random action
            action = random.choice(actions)
            sim_state = GameSimulator.apply_action(sim_state, action)
            depth += 1
        
        return sim_state.winner or "Draw"


import random
