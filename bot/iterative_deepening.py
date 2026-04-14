"""
Iterative Deepening - Gradually increase search depth
"""

from typing import Optional, List
import time
from .game_state import BattleState, UserAction
from .mcts import MCTSBot
from .parallel_mcts import ParallelMCTS


class IterativeDeepeningMCTS:
    """MCTS with iterative deepening for better time management"""

    def __init__(self, base_iterations: int = 100, max_depth: int = 20,
                 time_limit: float = 5.0, use_parallel: bool = False,
                 num_threads: int = 4, c_constant: float = 1.414,
                 verbose: bool = False):
        self.base_iterations = base_iterations
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.use_parallel = use_parallel
        self.num_threads = num_threads
        self.c_constant = c_constant
        self.verbose = verbose

    def select_best_action(self, state: BattleState) -> UserAction:
        """Select best action using iterative deepening"""
        start_time = time.time()
        team_name = state.next_unit_info.team_name if state.next_unit_info else "TeamA"

        best_action = None
        best_score = -1.0

        # Iterative deepening: gradually increase depth
        for depth in range(1, self.max_depth + 1):
            remaining_time = self.time_limit - (time.time() - start_time)
            if remaining_time <= 0:
                break

            # Calculate iterations for this depth level
            # More iterations for deeper searches, but respect time limit
            iterations = min(
                self.base_iterations * depth,
                int(remaining_time * 100)  # Rough estimate: 100 iter/sec
            )

            if iterations < 10:  # Minimum iterations
                break

            # Create MCTS bot for this depth
            if self.use_parallel:
                mcts = ParallelMCTS(
                    num_threads=self.num_threads,
                    iterations_per_thread=iterations // self.num_threads,
                    c_constant=self.c_constant,
                    simulation_depth=depth,
                    verbose=False
                )
            else:
                mcts = MCTSBot(
                    iterations=iterations,
                    c_constant=self.c_constant,
                    simulation_depth=depth,
                    verbose=False
                )

            # Run search
            action = mcts.select_best_action(state)

            # Evaluate this action (simplified - just check if it's better than previous)
            # In a real implementation, you'd want to track the best action across depths
            current_score = self._evaluate_action_quality(state, action, team_name)

            if current_score > best_score:
                best_score = current_score
                best_action = action

            if self.verbose:
                elapsed = time.time() - start_time
                print(f"Depth {depth}: {iterations} iter, score {current_score:.3f}, time {elapsed:.2f}s")

            # Early exit if we found a very good move
            if current_score > 0.8:
                break

        if best_action is None:
            # Fallback: quick search
            mcts = MCTSBot(iterations=50, simulation_depth=3, verbose=False)
            best_action = mcts.select_best_action(state)

        elapsed = time.time() - start_time
        if self.verbose:
            print(f"Iterative deepening completed in {elapsed:.2f}s")
            print(f"Final action: {best_action.action_type}")

        return best_action

    def _evaluate_action_quality(self, state: BattleState, action: UserAction, team_name: str) -> float:
        """Simple evaluation of action quality (0.0 to 1.0)"""
        # This is a simplified evaluation - in practice you'd want more sophisticated heuristics

        if action.action_type == "Skip":
            return 0.1  # Skipping is usually bad

        elif action.action_type == "Move":
            # Evaluate move quality based on positioning
            if hasattr(action, 'destination'):
                # Simple: prefer moves toward center
                dest_x, dest_y = self._parse_coordinate(action.destination)
                center_distance = abs(dest_x - 10) + abs(dest_y - 10)
                center_score = max(0, 1.0 - center_distance / 20.0)
                return 0.3 + center_score * 0.4

        elif action.action_type == "Attack":
            # Evaluate attack quality
            if hasattr(action, 'target'):
                # Simple: attacking is generally good
                return 0.7

        return 0.5  # Neutral

    def _parse_coordinate(self, coord: str) -> tuple:
        """Parse coordinate like 'A1' to (x, y)"""
        if len(coord) < 2:
            return (10, 10)  # Default center

        col = ord(coord[0].upper()) - ord('A') + 1
        row = int(coord[1:]) if coord[1:].isdigit() else 10

        return (col, row)