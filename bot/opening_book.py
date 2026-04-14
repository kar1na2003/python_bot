"""
Opening Book - Pre-computed optimal moves for early game positions
"""

from typing import Dict, List, Optional
from .game_state import BattleState, UserAction, Unit, UnitType


class OpeningBook:
    """Pre-computed opening moves for common early-game positions"""

    def __init__(self):
        self.opening_moves: Dict[str, List[UserAction]] = {}
        self._initialize_openings()

    def _initialize_openings(self):
        """Initialize common opening patterns"""
        # Early game patterns (first 3-5 moves per team)

        # Pattern 1: Scout deployment - get vision early
        self.opening_moves["scout_start"] = [
            UserAction.move("C3"),  # Move scout to center-left
            UserAction.move("D4"),  # Alternative: center
        ]

        # Pattern 2: Heavy positioning - control key areas
        self.opening_moves["heavy_start"] = [
            UserAction.move("B2"),  # Position for defense
            UserAction.move("C2"),  # Alternative: forward defense
        ]

        # Pattern 3: Fast unit harassment - pressure enemy
        self.opening_moves["fast_start"] = [
            UserAction.move("E2"),   # Flank left
            UserAction.move("A4"),   # Flank right
        ]

        # Pattern 4: Long range positioning - control from distance
        self.opening_moves["longrange_start"] = [
            UserAction.move("B5"),  # High ground
            UserAction.move("C4"),  # Central control
        ]

        # Pattern 5: Short range aggression - close and attack
        self.opening_moves["shortrange_start"] = [
            UserAction.move("D2"),  # Forward position
            UserAction.move("B3"),  # Alternative angle
        ]

    def _get_opening_key(self, state: BattleState) -> Optional[str]:
        """Determine which opening pattern applies"""
        if not state.next_unit_info:
            return None

        unit = state.next_unit_info.unit
        team_name = state.next_unit_info.team_name

        # Only use opening book in very early game
        total_moves_made = 0
        for team in [state.team_a, state.team_b]:
            for u in team.units:
                if u.position != self._get_starting_position(u, team.name):
                    total_moves_made += 1

        # Only use opening book if < 6 total moves made
        if total_moves_made >= 6:
            return None

        # Determine unit type pattern
        unit_type_name = UnitType.TYPES.get(unit.type, "Light").lower()
        if "scout" in unit.name.lower() or unit.type == UnitType.LIGHT:
            return "scout_start"
        elif unit.type == UnitType.HEAVY:
            return "heavy_start"
        elif unit.type == UnitType.FAST:
            return "fast_start"
        elif unit.type == UnitType.LONG_RANGE:
            return "longrange_start"
        elif unit.type == UnitType.SHORT_RANGE:
            return "shortrange_start"

        return None

    def _get_starting_position(self, unit: Unit, team_name: str) -> tuple:
        """Get the starting position for a unit"""
        # This is a simplified assumption - in reality you'd need to track initial positions
        # For now, assume standard starting positions
        if team_name == "TeamA":
            return (1, 1)  # A1
        else:
            return (20, 20)  # T20

    def get_opening_moves(self, state: BattleState) -> List[UserAction]:
        """Get recommended opening moves for current position"""
        key = self._get_opening_key(state)
        if key and key in self.opening_moves:
            return self.opening_moves[key].copy()
        return []

    def is_opening_phase(self, state: BattleState) -> bool:
        """Check if we're still in opening phase"""
        return self._get_opening_key(state) is not None