"""
Parallel MCTS - Multi-threaded Monte Carlo Tree Search
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional
from copy import deepcopy
from .mcts_node import MCTSNode
from .game_state import BattleState, UserAction
from .simulator import GameSimulator


class ParallelMCTS:
    """Parallel MCTS using multiple threads"""

    def __init__(self, num_threads: int = 4, iterations_per_thread: int = 250,
                 c_constant: float = 1.414, simulation_depth: Optional[int] = None,
                 verbose: bool = False, early_stop_threshold: float = 0.9):
        self.num_threads = num_threads
        self.iterations_per_thread = iterations_per_thread
        self.total_iterations = num_threads * iterations_per_thread
        self.c_constant = c_constant
        self.simulation_depth = simulation_depth
        self.verbose = verbose
        self.early_stop_threshold = early_stop_threshold

    def select_best_action(self, state: BattleState) -> UserAction:
        """Select best action using parallel MCTS"""
        start_time = time.time()

        # Create shared root node
        root = MCTSNode(state)
        team_name = state.next_unit_info.team_name if state.next_unit_info else "TeamA"

        # Results from each thread
        thread_results = []

        def run_mcts_thread(thread_id: int) -> dict:
            """Run MCTS iterations in a single thread"""
            local_root = MCTSNode(deepcopy(state))
            local_team_name = team_name

            results = {
                'thread_id': thread_id,
                'iterations': 0,
                'node_stats': {}  # action_key -> (visits, value)
            }

            for i in range(self.iterations_per_thread):
                node = local_root

                # Selection
                while not node.is_terminal() and node.is_fully_expanded():
                    node = max(
                        node.children.values(),
                        key=lambda n: n.ucb1(self.c_constant)
                    )

                # Expansion
                if not node.is_terminal() and not node.is_fully_expanded():
                    action = node.untried_actions.pop()
                    next_state = GameSimulator.apply_action(node.state, action)
                    child = MCTSNode(next_state, parent=node, action=action)
                    action_key = str(action.to_dict())
                    node.children[action_key] = child
                    node = child

                # Simulation
                if not node.is_terminal():
                    winner = GameSimulator.simulate_random_playout(
                        node.state,
                        max_depth=self.simulation_depth
                    )
                    reward = 1.0 if winner == local_team_name else 0.0
                else:
                    reward = node.reward_for_team(local_team_name)

                # Backpropagation
                backprop_node = node
                while backprop_node is not None:
                    backprop_node.visits += 1
                    backprop_node.value += reward
                    backprop_node = backprop_node.parent

                results['iterations'] += 1

            # Collect statistics from this thread
            for action_key, child in local_root.children.items():
                if action_key not in results['node_stats']:
                    results['node_stats'][action_key] = [0, 0.0]  # visits, value
                results['node_stats'][action_key][0] += child.visits
                results['node_stats'][action_key][1] += child.value

            return results

        # Run threads in parallel
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = [executor.submit(run_mcts_thread, i) for i in range(self.num_threads)]

            for future in as_completed(futures):
                try:
                    result = future.result()
                    thread_results.append(result)
                except Exception as e:
                    print(f"Thread failed: {e}")

        # Aggregate results from all threads
        action_stats = {}  # action_key -> (total_visits, total_value)

        for result in thread_results:
            for action_key, (visits, value) in result['node_stats'].items():
                if action_key not in action_stats:
                    action_stats[action_key] = [0, 0.0]
                action_stats[action_key][0] += visits
                action_stats[action_key][1] += value

        # Find best action
        if not action_stats:
            return UserAction.skip()

        best_action_key = max(action_stats.keys(),
                            key=lambda k: action_stats[k][0])  # Most visits

        best_visits, best_value = action_stats[best_action_key]

        # Reconstruct the action from the key
        # This is a bit hacky - in practice you'd want to store the action object
        import json
        action_dict = json.loads(best_action_key)
        best_action = UserAction.from_dict(action_dict)

        elapsed = time.time() - start_time

        if self.verbose:
            win_rate = best_value / best_visits if best_visits > 0 else 0
            print(f"Parallel MCTS completed in {elapsed:.2f}s")
            print(f"Total iterations: {self.total_iterations}")
            print(f"Best action: {best_action.action_type}")
            print(f"Visits: {best_visits}, Win rate: {win_rate:.2%}")

        return best_action