"""Server-side move selection using tactical rules + MCTS."""
from __future__ import annotations

from .damage import estimate_damage
from .game_state import BattleState, UserAction, UnitType
from .heuristic_config import ACTIVE_HEURISTICS
from .mcts import MCTSBot
from .online_policy import OnlinePolicy
from .position_eval import PositionEvaluator


class SearchEngine:
    def __init__(self, mcts_bot: MCTSBot):
        self.mcts_bot = mcts_bot
        self.online_policy = OnlinePolicy()
        self.position_eval = PositionEvaluator()
        self.w = ACTIVE_HEURISTICS.weights

    def choose_action(self, state: BattleState) -> UserAction:
        tactical = self._maybe_take_forced_tactical(state)
        if tactical is not None:
            return tactical

        try:
            return self.mcts_bot.get_best_action(state)
        except Exception:
            return self.online_policy.choose_action(state)

    def _maybe_take_forced_tactical(self, state: BattleState) -> UserAction | None:
        unit = state.next_unit_info.unit
        best_kill = None
        best_dmg = None
        best_other = None
        best_other_score = float("-inf")
        
        for target_name in state.next_unit_info.available_attack_targets:
            target = state.get_unit_by_name(target_name)
            if target is None or target.is_dead:
                continue
            
            dmg = estimate_damage(unit, target)
            
            # Immediate kill: take it without hesitation
            if dmg >= target.health:
                if best_kill is None or dmg > best_dmg:
                    best_kill = UserAction.attack(target_name)
                    best_dmg = dmg
                continue
            
            # High-priority targets: threat reduction
            score = dmg * 25.0  # High weight on damage
            
            # Type prioritization
            if target.type == UnitType.LONG_RANGE:
                score += 40.0
            elif target.type == UnitType.SHORT_RANGE:
                score += 20.0
            elif target.type == UnitType.FAST:
                score += 15.0
            
            # Low HP is urgent target
            if target.health <= 3:
                score += 100.0
            elif target.health <= 6:
                score += 50.0
            
            if score > best_other_score:
                best_other_score = score
                best_other = UserAction.attack(target_name)
        
        # Take kill shot immediately
        if best_kill is not None:
            return best_kill
        
        # Take high-priority target if it's worth it
        if best_other_score >= 100.0:
            return best_other
        
        return None
