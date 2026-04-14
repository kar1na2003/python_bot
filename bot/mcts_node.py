"""
MCTS Node - Tree node for Monte Carlo Tree Search
"""

import math
from typing import List, Optional
from dataclasses import dataclass
from .game_state import BattleState, UserAction
from .simulator import GameSimulator


@dataclass
class MCTSNode:
    """MCTS Tree Node"""
    state: BattleState
    parent: Optional['MCTSNode'] = None
    children: List['MCTSNode'] = None
    action: Optional[UserAction] = None
    visits: int = 0
    wins: float = 0.0
    depth: int = 0

    def __post_init__(self):
        if self.children is None:
            self.children = []

    @property
    def value(self) -> float:
        """UCT (Upper Confidence Bound) value"""
        if self.visits == 0:
            return float('inf')
        exploitation = self.wins / self.visits
        exploration = math.sqrt(2 * math.log(self.parent.visits) / self.visits) if self.parent else 0
        return exploitation + exploration

    @property
    def win_rate(self) -> float:
        """Win rate for this node"""
        return self.wins / self.visits if self.visits > 0 else 0.0

    def is_fully_expanded(self) -> bool:
        """Check if all possible actions have been explored"""
        return len(self.children) == len(GameSimulator.get_valid_actions(self.state))

    def best_child(self, c: float = 1.414) -> Optional['MCTSNode']:
        """Select best child using UCB1 formula"""
        if not self.children:
            return None

        best_value = float('-inf')
        best_child = None

        for child in self.children:
            exploitation = child.wins / child.visits if child.visits > 0 else 0
            exploration = c * math.sqrt(math.log(self.visits) / child.visits) if child.visits > 0 else float('inf')
            value = exploitation + exploration

            if value > best_value:
                best_value = value
                best_child = child

        return best_child