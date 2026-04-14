"""
Killer Moves Heuristic - Remember good moves for similar positions
"""

from typing import Dict, List, Set
from collections import defaultdict
from .distance import can_attack_without_moving, get_shortest_distance_value


class KillerMoves:
    """Track moves that performed well in similar situations"""

    def __init__(self, max_killers_per_situation: int = 3):
        # situation -> list of (action, score) tuples
        self.killer_moves: Dict[str, List[Tuple[UserAction, float]]] = defaultdict(list)
        self.max_killers = max_killers_per_situation

    def _get_situation_key(self, state: BattleState) -> str:
        """Create a key representing the current tactical situation"""
        if not state.next_unit_info:
            return "unknown"

        unit = state.next_unit_info.unit
        team_name = state.next_unit_info.team_name

        # Get enemy units in range
        enemy_team = state.team_b if team_name == "TeamA" else state.team_a
        enemies_in_range = []
        allies_nearby = []

        for enemy in enemy_team.alive_units:
            if can_attack_without_moving(unit, enemy):
                enemies_in_range.append((enemy.type, enemy.health))

        # Get nearby allies
        friendly_team = state.team_a if team_name == "TeamA" else state.team_b
        for ally in friendly_team.alive_units:
            if ally != unit and get_shortest_distance_value(unit, ally) <= 3:
                allies_nearby.append((ally.type, ally.health))

        # Create situation key
        situation = f"{unit.type}:{unit.health}:{len(enemies_in_range)}:{len(allies_nearby)}"

        # Add enemy types in range
        enemy_types = sorted([t for t, _ in enemies_in_range])
        situation += f":{','.join(map(str, enemy_types))}"

        return situation

    def record_killer_move(self, state: BattleState, action: UserAction, score: float):
        """Record a move that performed well"""
        situation = self._get_situation_key(state)

        # Add to killer moves for this situation
        killers = self.killer_moves[situation]
        killers.append((action, score))

        # Sort by score (best first) and keep only top N
        killers.sort(key=lambda x: x[1], reverse=True)
        self.killer_moves[situation] = killers[:self.max_killers]

    def get_killer_moves(self, state: BattleState) -> List[UserAction]:
        """Get killer moves for current situation"""
        situation = self._get_situation_key(state)
        killers = self.killer_moves.get(situation, [])
        return [action for action, _ in killers]

    def prioritize_actions(self, actions: List[UserAction], state: BattleState) -> List[UserAction]:
        """Reorder actions to try killer moves first"""
        killer_moves = set(self.get_killer_moves(state))

        # Separate killer moves from others
        killers = [a for a in actions if any(self._actions_similar(a, k) for k in killer_moves)]
        others = [a for a in actions if a not in killers]

        # Return killers first, then others
        return killers + others

    def _actions_similar(self, action1: UserAction, action2: UserAction) -> bool:
        """Check if two actions are similar"""
        if action1.action_type != action2.action_type:
            return False

        if action1.action_type == "Move":
            # Consider moves to same area similar
            if hasattr(action1, 'destination') and hasattr(action2, 'destination'):
                return action1.destination == action2.destination

        elif action1.action_type == "Attack":
            # Consider attacks on same unit type similar
            if hasattr(action1, 'target') and hasattr(action2, 'target'):
                return action1.target == action2.target

        return action1.action_type == action2.action_type  # Skip actions are similar

    def clear(self):
        """Clear all killer moves"""
        self.killer_moves.clear()