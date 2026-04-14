"""
Transposition Table - Cache for game state evaluations
"""

import hashlib
from typing import Dict, Optional, Tuple
from .game_state import BattleState


class TranspositionTable:
    """Cache for game state evaluations to avoid recomputation"""

    def __init__(self, max_size: int = 100000):
        self.table: Dict[str, Tuple[float, int]] = {}  # state_hash -> (value, visits)
        self.max_size = max_size

    def _hash_state(self, state: BattleState) -> str:
        """Create hash for game state"""
        # Create a string representation of key state elements
        state_str = f"{state.team_a.name}:{state.team_b.name}:"

        # Add unit positions and health
        for team in [state.team_a, state.team_b]:
            for unit in sorted(team.units, key=lambda u: u.name):
                pos = unit.position
                state_str += f"{unit.name}:{pos[0]},{pos[1]}:{unit.health}:"

        # Add current turn info
        if state.next_unit_info:
            state_str += f"{state.next_unit_info.team_name}:{state.next_unit_info.unit.name}"

        return hashlib.md5(state_str.encode()).hexdigest()

    def lookup(self, state: BattleState) -> Optional[Tuple[float, int]]:
        """Get cached value and visits for state"""
        state_hash = self._hash_state(state)
        return self.table.get(state_hash)

    def store(self, state: BattleState, value: float, visits: int):
        """Store evaluation in cache"""
        if len(self.table) >= self.max_size:
            # Remove oldest entries (simple FIFO)
            oldest_keys = list(self.table.keys())[:self.max_size // 10]
            for key in oldest_keys:
                del self.table[key]

        state_hash = self._hash_state(state)
        self.table[state_hash] = (value, visits)

    def clear(self):
        """Clear the transposition table"""
        self.table.clear()

    def size(self) -> int:
        """Get current table size"""
        return len(self.table)