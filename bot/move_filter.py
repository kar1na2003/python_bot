from typing import List

from .damage import estimate_damage
from .distance import string_to_coordinate, coordinate_distance
from .game_state import BattleState, UserAction, UnitType


class MoveFilter:
    def __init__(self, move_limit: int, attack_limit: int):
        self.move_limit = move_limit
        self.attack_limit = attack_limit

    def filter_actions(self, state: BattleState, actions: List[UserAction]) -> List[UserAction]:
        attacks = [a for a in actions if a.action_type == 'Attack']
        moves = [a for a in actions if a.action_type == 'Move']
        skips = [a for a in actions if a.action_type == 'Skip']

        attacks.sort(key=lambda a: self._score_attack(state, a), reverse=True)
        moves.sort(key=lambda a: self._score_move(state, a), reverse=True)

        result = attacks[: self.attack_limit] + moves[: self.move_limit]
        if skips and not result:
            result.extend(skips[:1])
        return result or actions[:]

    def _score_attack(self, state: BattleState, action: UserAction) -> float:
        attacker = state.next_unit_info.unit
        target = state.get_unit_by_name(action.target) if action.target else None
        if target is None or target.is_dead:
            return -1e9
        dmg = estimate_damage(attacker, target)
        kill_bonus = 1000.0 if dmg >= target.health else 0.0
        ranged_bonus = 80.0 if target.type == UnitType.LONG_RANGE else 0.0
        short_bonus = 35.0 if target.type == UnitType.SHORT_RANGE else 0.0
        low_hp_bonus = max(0.0, 10.0 - target.health) * 8.0
        return kill_bonus + dmg * 30.0 + ranged_bonus + short_bonus + low_hp_bonus

    def _score_move(self, state: BattleState, action: UserAction) -> float:
        unit = state.next_unit_info.unit
        if not action.destination:
            return -1e9
        x, y = string_to_coordinate(action.destination)
        enemies = state.enemy_team.alive_units
        if not enemies:
            return 0.0
        nearest = min(coordinate_distance(x, y, e.x_position, e.y_position) for e in enemies)
        ranged_enemies = [e for e in enemies if e.range >= 3]
        nearest_ranged = min((coordinate_distance(x, y, e.x_position, e.y_position) for e in ranged_enemies), default=999.0)
        threatened = sum(1 for e in enemies if coordinate_distance(x, y, e.x_position, e.y_position) <= e.range + 1.5)
        score = 0.0
        if unit.type in (UnitType.LIGHT, UnitType.FAST):
            score -= nearest * 7.0
        elif unit.type == UnitType.HEAVY:
            score -= nearest * 5.5
        elif unit.type == UnitType.SHORT_RANGE:
            score -= abs(nearest - 3.0) * 6.0
        else:
            score -= abs(nearest - 6.0) * 7.5
            score += min(nearest_ranged, 10.0) * 2.5
        score -= threatened * 12.0
        score += sum(15.0 for e in enemies if coordinate_distance(x, y, e.x_position, e.y_position) <= unit.range + 1.5)
        return score
