"""
End-game heuristics for Arena.AI bot
Specialized evaluation for late-game positions
"""
from typing import Dict, List, Optional
import math
from .game_state import BattleState, Unit
from .damage import estimate_damage
from .distance import coordinate_distance as calculate_distance

class EndGameEvaluator:
    """Specialized evaluator for end-game positions"""

    def __init__(self):
        self.endgame_threshold = 6  # Consider endgame when <= 6 units total
        self.late_endgame_threshold = 4  # Very late endgame

    def is_endgame(self, state: BattleState) -> bool:
        """Check if position is endgame"""
        all_units = state.team_a.units + state.team_b.units
        alive_units = [u for u in all_units if not u.is_dead]
        return len(alive_units) <= self.endgame_threshold

    def is_late_endgame(self, state: BattleState) -> bool:
        """Check if position is late endgame"""
        all_units = state.team_a.units + state.team_b.units
        alive_units = [u for u in all_units if not u.is_dead]
        return len(alive_units) <= self.late_endgame_threshold

    def evaluate_endgame(self, state: BattleState, for_team: str) -> float:
        """Evaluate endgame position"""
        if not self.is_endgame(state):
            return 0.0  # Not endgame, use regular evaluation

        all_units = state.team_a.units + state.team_b.units
        alive_units = [u for u in all_units if not u.is_dead]
        team_a_units = [u for u in alive_units if u.team_name == "TeamA"]
        team_b_units = [u for u in alive_units if u.team_name == "TeamB"]

        # Terminal positions
        if len(team_a_units) == 0 and len(team_b_units) == 0:
            return 0.0  # Draw
        elif len(team_a_units) == 0:
            return -1000.0 if for_team == "TeamA" else 1000.0
        elif len(team_b_units) == 0:
            return 1000.0 if for_team == "TeamA" else -1000.0

        # Material balance
        material_score = self._evaluate_material(team_a_units, team_b_units)

        # Positioning and threats
        positional_score = self._evaluate_positioning(state, team_a_units, team_b_units, for_team)

        # King safety (most valuable unit protection)
        safety_score = self._evaluate_safety(state, team_a_units, team_b_units, for_team)

        # Tempo and initiative
        tempo_score = self._evaluate_tempo(state, for_team)

        # Combine scores
        total_score = (
            material_score * 0.4 +
            positional_score * 0.3 +
            safety_score * 0.2 +
            tempo_score * 0.1
        )

        return total_score

    def _evaluate_material(self, team_a_units: List[Unit], team_b_units: List[Unit]) -> float:
        """Evaluate material balance"""
        def unit_value(unit: Unit) -> float:
            base_values = {
                "Light": 1.0,
                "Heavy": 1.3,
                "Fast": 1.1,
                "ShortRange": 1.2,
                "LongRange": 1.4
            }
            return base_values.get(unit.unit_type, 1.0) * (unit.health / 10.0)

        team_a_value = sum(unit_value(u) for u in team_a_units)
        team_b_value = sum(unit_value(u) for u in team_b_units)

        return team_a_value - team_b_value

    def _evaluate_positioning(self, state: BattleState, team_a_units: List[Unit],
                            team_b_units: List[Unit], for_team: str) -> float:
        """Evaluate unit positioning and threats"""
        score = 0.0

        # Clustering bonus (units working together)
        score += self._evaluate_clustering(team_a_units) * 0.5
        score -= self._evaluate_clustering(team_b_units) * 0.5

        # Threat evaluation
        score += self._evaluate_threats(state, team_a_units, team_b_units, for_team)

        # Control of center
        score += self._evaluate_center_control(team_a_units, team_b_units)

        return score

    def _evaluate_clustering(self, units: List[Unit]) -> float:
        """Evaluate how clustered units are"""
        if len(units) <= 1:
            return 0.0

        total_distance = 0.0
        count = 0

        for i, unit1 in enumerate(units):
            for unit2 in units[i+1:]:
                dist = calculate_distance(unit1.x_position, unit1.y_position,
                                        unit2.x_position, unit2.y_position)
                total_distance += dist
                count += 1

        if count == 0:
            return 0.0

        avg_distance = total_distance / count
        # Lower average distance = better clustering
        return max(0, 5.0 - avg_distance) * 0.2

    def _evaluate_threats(self, state: BattleState, team_a_units: List[Unit],
                         team_b_units: List[Unit], for_team: str) -> float:
        """Evaluate threats between units"""
        score = 0.0

        for attacker in team_a_units:
            for target in team_b_units:
                dist = calculate_distance(attacker.x_position, attacker.y_position,
                                        target.x_position, target.y_position)

                # Check if in range
                attack_range = self._get_attack_range(attacker)
                if dist <= attack_range:
                    damage = estimate_damage(attacker, target)
                    threat_score = min(damage / target.health, 1.0) * 0.5
                    score += threat_score

        for attacker in team_b_units:
            for target in team_a_units:
                dist = calculate_distance(attacker.x_position, attacker.y_position,
                                        target.x_position, target.y_position)

                attack_range = self._get_attack_range(attacker)
                if dist <= attack_range:
                    damage = estimate_damage(attacker, target)
                    threat_score = min(damage / target.health, 1.0) * 0.5
                    score -= threat_score

        return score

    def _evaluate_center_control(self, team_a_units: List[Unit], team_b_units: List[Unit]) -> float:
        """Evaluate control of arena center"""
        center_x, center_y = 10, 10  # Assuming 20x20 arena
        score = 0.0

        for unit in team_a_units:
            dist_to_center = calculate_distance(unit.x_position, unit.y_position, center_x, center_y)
            score += max(0, 7.0 - dist_to_center) * 0.1

        for unit in team_b_units:
            dist_to_center = calculate_distance(unit.x_position, unit.y_position, center_x, center_y)
            score -= max(0, 7.0 - dist_to_center) * 0.1

        return score

    def _evaluate_safety(self, state: BattleState, team_a_units: List[Unit],
                        team_b_units: List[Unit], for_team: str) -> float:
        """Evaluate unit safety"""
        score = 0.0

        # Find most valuable units
        team_a_valuable = max(team_a_units, key=lambda u: self._unit_value(u)) if team_a_units else None
        team_b_valuable = max(team_b_units, key=lambda u: self._unit_value(u)) if team_b_units else None

        # Protect valuable units
        if team_a_valuable:
            score += self._evaluate_unit_safety(team_a_valuable, team_b_units) * 0.3

        if team_b_valuable:
            score -= self._evaluate_unit_safety(team_b_valuable, team_a_units) * 0.3

        return score

    def _evaluate_unit_safety(self, unit: Unit, enemy_units: List[Unit]) -> float:
        """Evaluate safety of a specific unit"""
        safety_score = 1.0  # Base safety

        for enemy in enemy_units:
            dist = calculate_distance(unit.x_position, unit.y_position,
                                    enemy.x_position, enemy.y_position)

            attack_range = self._get_attack_range(enemy)
            if dist <= attack_range:
                damage = estimate_damage(enemy, unit)
                threat = min(damage / unit.health, 1.0)
                safety_score -= threat * 0.5

        return max(0, safety_score)

    def _evaluate_tempo(self, state: BattleState, for_team: str) -> float:
        """Evaluate tempo and initiative"""
        if not state.next_unit_info:
            return 0.0

        next_team = state.next_unit_info.team_name
        tempo_bonus = 0.2 if next_team == for_team else -0.2

        return tempo_bonus

    def _get_attack_range(self, unit: Unit) -> float:
        """Get attack range for unit type"""
        ranges = {
            "Light": 1.5,
            "Heavy": 1.5,
            "Fast": 1.5,
            "ShortRange": 2.0,
            "LongRange": 3.0
        }
        return ranges.get(unit.unit_type, 1.5)

    def _unit_value(self, unit: Unit) -> float:
        """Calculate unit value for endgame"""
        base_values = {
            "Light": 1.0,
            "Heavy": 1.3,
            "Fast": 1.1,
            "ShortRange": 1.2,
            "LongRange": 1.4
        }
        return base_values.get(unit.unit_type, 1.0) * (unit.health / 10.0)

# Global instance
endgame_evaluator = EndGameEvaluator()

def get_endgame_evaluator():
    """Get the global endgame evaluator instance"""
    return endgame_evaluator