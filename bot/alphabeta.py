import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Tuple

import config
from .game_state import BattleState, UserAction
from .move_filter import MoveFilter
from .position_eval import PositionEvaluator
from .simulator import GameSimulator


class AlphaBetaSearch:
    def __init__(self, max_depth: int, time_limit: float, use_parallel: bool = True, workers: int = 4):
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.use_parallel = use_parallel
        self.workers = workers
        self.evaluator = PositionEvaluator()
        self.move_filter = MoveFilter(config.MOVE_CANDIDATE_LIMIT, config.ATTACK_CANDIDATE_LIMIT)
        self.team_name = 'TeamA'
        self._deadline = 0.0

    def choose_action(self, state: BattleState) -> UserAction:
        self.team_name = state.next_unit_info.team_name
        self._deadline = time.time() + self.time_limit
        actions = self.move_filter.filter_actions(state, GameSimulator.get_valid_actions(state))
        if not actions:
            return UserAction.skip()

        best_action = actions[0]
        for depth in range(1, self.max_depth + 1):
            if time.time() >= self._deadline:
                break
            current = self._search_root(state, actions, depth)
            if current is not None:
                best_action = current
        return best_action

    def _search_root(self, state: BattleState, actions: List[UserAction], depth: int) -> Optional[UserAction]:
        if self.use_parallel and len(actions) > 1 and depth >= 2:
            return self._search_root_parallel(state, actions, depth)

        alpha = -math.inf
        beta = math.inf
        best_action = None
        ordered = sorted(actions, key=lambda a: self._move_order_score(state, a), reverse=True)
        for action in ordered:
            if time.time() >= self._deadline:
                break
            child = GameSimulator.apply_action(state, action)
            score = self._alphabeta(child, depth - 1, alpha, beta)
            if score > alpha:
                alpha = score
                best_action = action
        return best_action

    def _search_root_parallel(self, state: BattleState, actions: List[UserAction], depth: int) -> Optional[UserAction]:
        ordered = sorted(actions, key=lambda a: self._move_order_score(state, a), reverse=True)
        best_action = ordered[0]
        best_score = -math.inf
        with ThreadPoolExecutor(max_workers=min(self.workers, len(ordered))) as ex:
            futs = {ex.submit(self._score_root_action, state, a, depth): a for a in ordered}
            for fut in as_completed(futs):
                action = futs[fut]
                try:
                    score = fut.result()
                except Exception:
                    continue
                if score > best_score:
                    best_score = score
                    best_action = action
        return best_action

    def _score_root_action(self, state: BattleState, action: UserAction, depth: int) -> float:
        child = GameSimulator.apply_action(state, action)
        return self._alphabeta(child, depth - 1, -math.inf, math.inf)

    def _alphabeta(self, state: BattleState, depth: int, alpha: float, beta: float) -> float:
        if time.time() >= self._deadline:
            return self._evaluate(state)
        if depth <= 0 or state.is_game_over:
            return self._evaluate(state)

        actions = self.move_filter.filter_actions(state, GameSimulator.get_valid_actions(state))
        if not actions:
            return self._evaluate(state)

        maximizing = state.next_unit_info.team_name == self.team_name
        ordered = sorted(actions, key=lambda a: self._move_order_score(state, a), reverse=True)

        if maximizing:
            value = -math.inf
            for action in ordered:
                child = GameSimulator.apply_action(state, action)
                value = max(value, self._alphabeta(child, depth - 1, alpha, beta))
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            return value

        value = math.inf
        for action in ordered:
            child = GameSimulator.apply_action(state, action)
            value = min(value, self._alphabeta(child, depth - 1, alpha, beta))
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value

    def _move_order_score(self, state: BattleState, action: UserAction) -> float:
        if action.action_type == 'Attack':
            return 1000.0
        if action.action_type == 'Move':
            return 100.0
        return 0.0

    def _evaluate(self, state: BattleState) -> float:
        pos = self.evaluator.evaluate_position(state, self.team_name)
        my_team = state.team_a if self.team_name == state.team_a.name else state.team_b
        enemy = state.team_b if self.team_name == state.team_a.name else state.team_a
        my_health = sum(u.health for u in my_team.alive_units)
        enemy_health = sum(u.health for u in enemy.alive_units)
        hp_term = (my_health - enemy_health) / 80.0
        my_units = len(my_team.alive_units)
        enemy_units = len(enemy.alive_units)
        unit_term = (my_units - enemy_units) / 8.0
        return pos + hp_term * 0.5 + unit_term * 0.7
