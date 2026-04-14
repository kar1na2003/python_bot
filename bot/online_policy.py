from .damage import estimate_damage
from .distance import string_to_coordinate, coordinate_distance, can_attack_without_moving
from .game_state import BattleState, UserAction, UnitType


class OnlinePolicy:
    def choose_action(self, state: BattleState) -> UserAction:
        unit = state.next_unit_info.unit
        enemy_team = state.enemy_team

        if state.next_unit_info.available_attack_targets:
            best_attack = None
            best_score = -10**9

            for target_name in state.next_unit_info.available_attack_targets:
                target = state.get_unit_by_name(target_name)
                if target is None or target.is_dead:
                    continue

                dmg = estimate_damage(unit, target)
                kill_bonus = 1000 if dmg >= target.health else 0

                counter_penalty = 0.0
                if can_attack_without_moving(target, unit):
                    counter_penalty = estimate_damage(target, unit) * 0.6

                target_priority = 0
                if target.type == UnitType.LONG_RANGE:
                    target_priority += 25
                elif target.type == UnitType.SHORT_RANGE:
                    target_priority += 15
                elif target.type == UnitType.FAST:
                    target_priority += 10

                low_hp_bonus = max(0, 12 - target.health) * 8
                score = kill_bonus + dmg * 20 + target_priority + low_hp_bonus - counter_penalty * 12

                if score > best_score:
                    best_score = score
                    best_attack = UserAction.attack(target_name)

            if best_attack is not None:
                return best_attack

        if state.next_unit_info.available_destinations:
            best_move = None
            best_score = -10**9
            enemies = enemy_team.alive_units

            for dest in state.next_unit_info.available_destinations:
                x, y = string_to_coordinate(dest)
                score = 0.0

                if enemies:
                    dists = [coordinate_distance(x, y, e.x_position, e.y_position) for e in enemies]
                    nearest_enemy_dist = min(dists)
                else:
                    nearest_enemy_dist = 999

                ranged_enemies = [e for e in enemies if e.range >= 3]
                if ranged_enemies:
                    nearest_ranged = min(
                        coordinate_distance(x, y, e.x_position, e.y_position)
                        for e in ranged_enemies
                    )
                else:
                    nearest_ranged = 999

                if unit.type in (UnitType.LIGHT, UnitType.FAST):
                    score -= nearest_enemy_dist * 8
                    score -= nearest_ranged * 2
                elif unit.type == UnitType.HEAVY:
                    score -= nearest_enemy_dist * 6
                    score -= nearest_ranged * 1
                elif unit.type == UnitType.SHORT_RANGE:
                    score -= abs(nearest_enemy_dist - 3) * 7
                    score -= nearest_ranged * 2
                elif unit.type == UnitType.LONG_RANGE:
                    score -= abs(nearest_enemy_dist - 6) * 9
                    score += nearest_ranged * 2.5

                threatened_by = 0
                for e in enemies:
                    d = coordinate_distance(x, y, e.x_position, e.y_position)
                    if d <= e.range + 1.5:
                        threatened_by += 1
                score -= threatened_by * 18

                future_attack_bonus = 0
                for e in enemies:
                    d = coordinate_distance(x, y, e.x_position, e.y_position)
                    if d <= unit.range + 1.5:
                        future_attack_bonus += 20
                        if e.type == UnitType.LONG_RANGE:
                            future_attack_bonus += 15
                score += future_attack_bonus

                if state.next_unit_info.team_name == state.team_a.name:
                    score += x * 1.5
                else:
                    score += (21 - x) * 1.5

                if score > best_score:
                    best_score = score
                    best_move = UserAction.move(dest)

            if best_move is not None:
                return best_move

        return UserAction.skip()
