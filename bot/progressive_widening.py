"""
Progressive Widening - Expand search tree gradually
"""

from typing import Dict, List, Optional
import math
import random
from .game_state import BattleState, UserAction
from .simulator import GameSimulator


class ProgressiveWideningNode:
    """Node with progressive widening for action expansion"""

    def __init__(self, state: BattleState, parent: Optional['ProgressiveWideningNode'] = None,
                 action: Optional[UserAction] = None):
        self.state = state
        self.parent = parent
        self.action = action
        self.children: Dict[str, 'ProgressiveWideningNode'] = {}
        self.visits = 0
        self.value = 0.0

        # Progressive widening: start with few actions, expand gradually
        self.all_actions = GameSimulator.get_valid_actions(state)
        random.shuffle(self.all_actions)
        self.expanded_actions = 0  # How many actions we've tried to expand

    def should_expand_more(self) -> bool:
        """Check if we should expand more actions based on visits"""
        if self.expanded_actions >= len(self.all_actions):
            return False

        # Progressive widening formula: expand when visits > k * expanded^2
        # This ensures we focus on promising branches first
        k = 2.0  # Widening parameter
        return self.visits > k * (self.expanded_actions ** 2)

    def get_next_action_to_expand(self) -> Optional[UserAction]:
        """Get next action to try expanding"""
        if self.expanded_actions >= len(self.all_actions):
            return None

        action = self.all_actions[self.expanded_actions]
        self.expanded_actions += 1
        return action

    def ucb1(self, c: float = 1.414) -> float:
        """Calculate UCB1 value"""
        if self.visits == 0:
            return float('inf')

        exploitation = self.value / self.visits
        exploration = c * math.sqrt(math.log(self.parent.visits) / self.visits) if self.parent else 0

        return exploitation + exploration

    def is_terminal(self) -> bool:
        """Check if this is an end state"""
        return self.state.is_game_over

    def reward_for_team(self, team_name: str) -> float:
        """Get reward for a specific team"""
        if not self.state.is_game_over:
            return 0.0
        return 1.0 if self.state.winner == team_name else 0.0


class ProgressiveWideningMCTS:
    """MCTS with progressive widening for efficient exploration"""

    def __init__(self, iterations: int = 1000, c_constant: float = 1.414,
                 simulation_depth: Optional[int] = None, verbose: bool = False,
                 early_stop_threshold: float = 0.9):
        self.iterations = iterations
        self.c_constant = c_constant
        self.simulation_depth = simulation_depth
        self.verbose = verbose
        self.early_stop_threshold = early_stop_threshold

    def select_best_action(self, state: BattleState) -> UserAction:
        """Select best action using progressive widening MCTS"""
        root = ProgressiveWideningNode(state)
        team_name = state.next_unit_info.team_name if state.next_unit_info else "TeamA"

        for i in range(self.iterations):
            node = root

            # Selection with progressive widening
            while not node.is_terminal():
                if node.should_expand_more():
                    # Expand a new action
                    action = node.get_next_action_to_expand()
                    if action:
                        next_state = GameSimulator.apply_action(node.state, action)
                        child = ProgressiveWideningNode(next_state, parent=node, action=action)
                        action_key = str(action.to_dict())
                        node.children[action_key] = child
                        node = child
                        break
                elif node.children:
                    # Select best child using UCB1
                    node = max(
                        node.children.values(),
                        key=lambda n: n.ucb1(self.c_constant)
                    )
                else:
                    # No children yet, stay at this node
                    break

            # Simulation
            if not node.is_terminal():
                winner = GameSimulator.simulate_random_playout(
                    node.state,
                    max_depth=self.simulation_depth
                )
                reward = 1.0 if winner == team_name else 0.0
            else:
                reward = node.reward_for_team(team_name)

            # Backpropagation
            while node is not None:
                node.visits += 1
                node.value += reward
                node = node.parent

            # Early stopping check
            if root.children and i >= 50:
                best_win_rate = max((child.value / child.visits for child in root.children.values()), default=0)
                if best_win_rate >= self.early_stop_threshold:
                    if self.verbose:
                        print(f"Early stop at iteration {i+1}: win rate {best_win_rate:.2%}")
                    break

            if self.verbose and (i + 1) % 200 == 0:
                expanded_total = sum(len(node.children) for node in self._get_all_nodes(root))
                print(f"MCTS iteration {i + 1}/{self.iterations}, expanded actions: {expanded_total}")

        # Select best child
        if not root.children:
            return UserAction.skip()

        best_child = max(root.children.values(), key=lambda n: n.visits)

        if self.verbose:
            print(f"Best action selected: {best_child.action.action_type}")
            print(f"  Visits: {best_child.visits}")
            print(f"  Win rate: {best_child.value / best_child.visits:.2%}")

        return best_child.action

    def _get_all_nodes(self, root: ProgressiveWideningNode) -> List[ProgressiveWideningNode]:
        """Get all nodes in the tree for statistics"""
        nodes = [root]
        to_visit = list(root.children.values())

        while to_visit:
            node = to_visit.pop()
            nodes.append(node)
            to_visit.extend(node.children.values())

        return nodes