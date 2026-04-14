"""
Monte Carlo Tree Search (MCTS) - Higher order AI decision making
"""

import math
import random
import time
import threading
import concurrent.futures
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict

from .game_state import BattleState, Unit, UnitType, UserAction, ActionType
from .simulator import GameSimulator
from .position_eval import PositionEvaluator
from .opening_book import OpeningBook
from .killer_moves import KillerMoves
from .transposition_table import TranspositionTable
from .parallel_mcts import ParallelMCTS


from .mcts_node import MCTSNode


class MCTSBot:
    """
    Advanced Monte Carlo Tree Search Bot with multiple enhancements
    """

    def __init__(self, iterations: int = 1000, time_limit: float = 5.0, c_constant: float = 1.414,
                 simulation_depth: Optional[int] = None, verbose: bool = False,
                 early_stop_threshold: float = 0.8, use_transposition_table: bool = True,
                 use_killer_moves: bool = True, use_opening_book: bool = True,
                 use_position_evaluation: bool = True, use_progressive_widening: bool = True,
                 num_threads: int = 1):
        self.iterations = iterations
        self.time_limit = time_limit
        self.c_constant = c_constant
        self.simulation_depth = simulation_depth
        self.verbose = verbose
        self.early_stop_threshold = early_stop_threshold

        # Feature toggles
        self.use_transposition_table = use_transposition_table
        self.use_killer_moves = use_killer_moves
        self.use_opening_book = use_opening_book
        self.use_position_evaluation = use_position_evaluation
        self.use_progressive_widening = use_progressive_widening
        self.num_threads = num_threads

        # Advanced features (conditionally initialized)
        self.position_evaluator = PositionEvaluator() if use_position_evaluation else None
        self.opening_book = OpeningBook() if use_opening_book else None
        self.killer_moves = KillerMoves() if use_killer_moves else None
        self.transposition_table = TranspositionTable() if use_transposition_table else None
        # Progressive widening is now integrated directly, not as a separate class
        self.progressive_widening = use_progressive_widening
        self.parallel_mcts = ParallelMCTS(num_threads=num_threads) if num_threads > 1 else None

        # Statistics
        self.total_simulations = 0
        self.cache_hits = 0

    def get_best_action(self, state: BattleState) -> UserAction:
        """
        Get the best action using enhanced MCTS
        """
        root_team_name = state.next_unit_info.team_name
        start_time = time.time()

        # Check opening book first
        if self.opening_book:
            book_moves = self.opening_book.get_opening_moves(state)
            if book_moves:
                return random.choice(book_moves)

        # Initialize root node
        root = MCTSNode(state=state, depth=0)

        # Run MCTS iterations
        iterations_completed = 0
        for i in range(self.iterations):
            if time.time() - start_time > self.time_limit:
                break

            self._run_iteration(root, root_team_name)
            iterations_completed += 1

        # Select best action
        if not root.children:
            # No actions explored, return random valid action
            actions = GameSimulator.get_valid_actions(state)
            return random.choice(actions) if actions else self._get_skip_action(state)

        best_child = max(root.children, key=lambda c: c.visits)
        action = best_child.action

        # Update killer moves
        if action:
            self.killer_moves.record_killer_move(state, action, best_child.wins / best_child.visits)

        return action or self._get_skip_action(state)

    def _run_iteration(self, root: MCTSNode, root_team_name: str) -> None:
        """Run one MCTS iteration"""
        # Selection
        node = self._select(root)

        # Expansion
        if not node.state.is_game_over:
            node = self._expand(node)

        # Simulation
        result = self._simulate(node.state, root_team_name)

        # Backpropagation
        self._backpropagate(node, result)

    def _select(self, node: MCTSNode) -> MCTSNode:
        """Select node to expand using UCB1"""
        while node.children and not node.state.is_game_over:
            # Check transposition table
            if self.transposition_table:
                cached_result = self.transposition_table.lookup(node.state)
                if cached_result:
                    self.cache_hits += 1
                    # Use cached result
                    node.visits += 1
                    node.wins += cached_result[0]  # value
                    return node

            # Progressive widening: check if we should expand more children
            if self.progressive_widening:
                k = 2.0  # Widening parameter
                max_children = max(1, int(node.visits / k) + 1)
                if len(node.children) < max_children:
                    break  # Expand instead of selecting

            # Select best child
            best_child = node.best_child(self.c_constant)
            if best_child:
                node = best_child
            else:
                break

        return node

    def _expand(self, node: MCTSNode) -> MCTSNode:
        """Expand node by adding new child"""
        actions = GameSimulator.get_valid_actions(node.state)

        # Prioritize killer moves
        killer_actions = self.killer_moves.get_killer_moves(node.state)
        prioritized_actions = killer_actions + [a for a in actions if a not in killer_actions]

        # Progressive widening: limit children based on visits
        if self.progressive_widening:
            # Progressive widening formula: expand when visits > k * expanded^2
            k = 2.0  # Widening parameter
            max_children = max(1, int(node.visits / k) + 1)
            if len(node.children) >= max_children:
                return node
        else:
            # Standard expansion - no limit
            pass

        # Try untried actions
        tried_actions = {child.action for child in node.children}
        untried_actions = [a for a in prioritized_actions if a not in tried_actions]

        if untried_actions:
            action = random.choice(untried_actions)
            new_state = GameSimulator.apply_action(node.state, action)
            child = MCTSNode(
                state=new_state,
                parent=node,
                action=action,
                depth=node.depth + 1
            )
            node.children.append(child)
            return child

        return node

    def _simulate(self, state: BattleState, root_team_name: str) -> float:
        """Run simulation from state"""
        current_state = state
        depth = 0
        max_depth = self.simulation_depth or 50  # Prevent infinite loops

        while not current_state.is_game_over and depth < max_depth:
            # Check transposition table
            cached_result = self.transposition_table.lookup(current_state)
            if cached_result is not None:
                return cached_result[0]  # Return the value part of the tuple

            # Get possible actions
            actions = GameSimulator.get_valid_actions(current_state)
            if not actions:
                break

            # Use position evaluation for move selection
            if random.random() < 0.3:  # 30% chance to use evaluation
                action = self._select_action_by_evaluation(current_state, actions, root_team_name)
            else:
                action = random.choice(actions)

            # Apply action
            current_state = GameSimulator.apply_action(current_state, action)
            depth += 1

        # Evaluate final position
        return self._evaluate_position(current_state, root_team_name)

    def _select_action_by_evaluation(self, state: BattleState, actions: List[UserAction], root_team_name: str) -> UserAction:
        """Select action using position evaluation"""
        best_action = None
        best_score = float('-inf')

        for action in actions:
            new_state = GameSimulator.apply_action(state, action)
            score = self.position_evaluator.evaluate_position(new_state, root_team_name)
            if score > best_score:
                best_score = score
                best_action = action

        return best_action or random.choice(actions)

    def _evaluate_position(self, state: BattleState, root_team_name: str) -> float:
        """Evaluate position for the root team"""
        if state.is_game_over:
            winner = state.winner
            if winner == root_team_name:
                return 1.0
            elif winner is None or winner == "Noone":
                return 0.5
            else:
                return 0.0

        # Use position evaluator
        return self.position_evaluator.evaluate_position(state, root_team_name)

    def _backpropagate(self, node: MCTSNode, result: float) -> None:
        """Backpropagate result up the tree"""
        current = node
        while current:
            current.visits += 1
            current.wins += result
            # Update transposition table
            self.transposition_table.store(current.state, result, current.visits)
            current = current.parent

    def _get_skip_action(self, state: BattleState) -> UserAction:
        """Get a skip action when no other actions available"""
        return UserAction.skip()

    def get_statistics(self) -> Dict[str, Any]:
        """Get MCTS statistics"""
        return {
            'total_simulations': self.total_simulations,
            'cache_hits': self.cache_hits,
            'cache_hit_rate': self.cache_hits / max(1, self.total_simulations),
            'transposition_table_size': len(self.transposition_table.table),
            'killer_moves_count': len(self.killer_moves.moves)
        }


class ParallelMCTSBot(MCTSBot):
    """
    Parallel MCTS using multiple threads
    """

    def __init__(self, iterations: int = 1000, time_limit: float = 5.0, c_constant: float = 1.414, num_threads: int = 4):
        super().__init__(iterations, time_limit, c_constant)
        self.num_threads = num_threads

    def get_best_action(self, state: BattleState) -> UserAction:
        """Get best action using parallel MCTS"""
        root_team_name = state.next_unit_info.team_name
        start_time = time.time()

        # Check opening book
        if self.opening_book:
            book_moves = self.opening_book.get_opening_moves(state)
            if book_moves:
                return random.choice(book_moves)

        # Run parallel MCTS
        root = MCTSNode(state=state, depth=0)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = []
            iterations_per_thread = self.iterations // self.num_threads

            for _ in range(self.num_threads):
                future = executor.submit(self._run_parallel_iterations, root, iterations_per_thread, self.time_limit, root_team_name)
                futures.append(future)

            # Wait for completion
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result(timeout=self.time_limit)
                except concurrent.futures.TimeoutError:
                    pass

        # Select best action
        if not root.children:
            actions = GameSimulator.get_valid_actions(state)
            return random.choice(actions) if actions else self._get_skip_action(state)

        best_child = max(root.children, key=lambda c: c.visits)
        return best_child.action or self._get_skip_action(state)

    def _run_parallel_iterations(self, root: MCTSNode, iterations: int, time_limit: float, root_team_name: str) -> None:
        """Run iterations in parallel"""
        start_time = time.time()
        for _ in range(iterations):
            if time.time() - start_time > time_limit:
                break
            self._run_iteration(root, root_team_name)