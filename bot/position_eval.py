"""Position evaluation with tuneable coefficients."""
from __future__ import annotations

from .distance import coordinate_distance, get_shortest_distance_value
from .game_state import BattleState, Unit, UnitType
from .heuristic_config import ACTIVE_HEURISTICS


class PositionEvaluator:
    def __init__(self):
        self.weights = ACTIVE_HEURISTICS.weights
        self.type_multipliers = ACTIVE_HEURISTICS.unit_type_multipliers
        self.center = (10, 10)

    def unit_dynamic_value(self, unit: Unit) -> float:
        type_name = UnitType.TYPES.get(unit.type, "Light")
        w = self.weights
        base = (
            w["value_base"]
            + w["value_attack"] * unit.attack
            + w["value_defence"] * unit.defence
            + w["value_range"] * unit.range
            + w["value_movement"] * unit.movement
            + w["value_health"] * max(unit.health, 0)
        )
        return base * self.type_multipliers.get(type_name, 1.0)

    def evaluate_position(self, state: BattleState, for_team: str) -> float:
        if state.is_game_over:
            if state.winner == for_team:
                return 1_000_000.0
            if state.winner is None or state.winner == "Noone":
                return 0.5
            return -1_000_000.0

        my_team = state.team_a if state.team_a.name == for_team else state.team_b
        enemy_team = state.team_b if my_team is state.team_a else state.team_a
        score = 0.0

        score += self._material_score(my_team, enemy_team)
        score += self._position_score(my_team, enemy_team)
        score += self._threat_score(my_team, enemy_team)
        score += self._mobility_score(my_team, enemy_team)
        return score

    def _material_score(self, my_team, enemy_team) -> float:
        w = self.weights
        score = 0.0
        for unit in my_team.alive_units:
            score += w["alive_unit"]
            score += self.unit_dynamic_value(unit)
            score += w["hp"] * unit.health
        for unit in enemy_team.alive_units:
            score -= w["alive_unit"]
            score -= self.unit_dynamic_value(unit)
            score -= w["hp"] * unit.health
        return score

    def _position_score(self, my_team, enemy_team) -> float:
        w = self.weights
        score = 0.0
        my_forward = 0.0
        enemy_forward = 0.0
        for unit in my_team.alive_units:
            dist_center = coordinate_distance(unit.x_position, unit.y_position, *self.center)
            score += w["center_control"] * max(0.0, 8.0 - dist_center)
            my_forward += unit.x_position if my_team.name == "TeamA" else (21 - unit.x_position)
            nearby = sum(1 for ally in my_team.alive_units if ally is not unit and get_shortest_distance_value(unit, ally) <= 3)
            score += w["cluster"] * min(nearby, 2)
            if unit.range >= 3:
                threats = sum(1 for e in enemy_team.alive_units if get_shortest_distance_value(unit, e) <= e.range + 1)
                score += w["exposed_ranged"] * threats
        for unit in enemy_team.alive_units:
            enemy_forward += unit.x_position if enemy_team.name == "TeamA" else (21 - unit.x_position)
        score += w["progress"] * (my_forward - enemy_forward)
        return score

    def _threat_score(self, my_team, enemy_team) -> float:
        w = self.weights
        score = 0.0
        for unit in my_team.alive_units:
            attack_options = 0
            for enemy in enemy_team.alive_units:
                d = get_shortest_distance_value(unit, enemy)
                if d <= unit.range:
                    attack_options += 1
                if d <= enemy.range:
                    score += w["threatened"]
            score += w["attack_option"] * attack_options
        for enemy in enemy_team.alive_units:
            attack_options = sum(1 for unit in my_team.alive_units if get_shortest_distance_value(enemy, unit) <= enemy.range)
            score -= w["attack_option"] * attack_options
        return score

    def _mobility_score(self, my_team, enemy_team) -> float:
        w = self.weights
        my_mob = sum(u.movement for u in my_team.alive_units)
        en_mob = sum(u.movement for u in enemy_team.alive_units)
        return w["mobility"] * (my_mob - en_mob)
