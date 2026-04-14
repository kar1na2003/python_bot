"""
Damage Calculator - Implements damage calculation and type advantages
"""

import random
from .game_state import Unit, UnitType


def calculate_damage(attacker: Unit, target: Unit) -> int:
    """
    Calculate damage from attacker to target.
    Implements exact damage calculation logic from C# server.
    """
    attack = attacker.attack
    defence = target.defence
    
    attacker_type = attacker.type
    target_type = target.type
    
    # Light vs Heavy bonus
    if attacker_type == UnitType.LIGHT and target_type == UnitType.HEAVY:
        if random.random() < 0.10:
            attack += 1
    
    # Light vs Fast evade
    if attacker_type == UnitType.LIGHT and target_type == UnitType.FAST:
        if random.random() < 0.03:
            return 0  # Evaded!
    
    # Heavy vs Fast bonus
    if attacker_type == UnitType.HEAVY and target_type == UnitType.FAST:
        if random.random() < 0.05:
            attack += 1
    
    # ShortRange type advantages
    if attacker_type == UnitType.SHORT_RANGE:
        if target_type == UnitType.HEAVY:
            if random.random() < 0.03:
                defence -= 3
        elif target_type == UnitType.LIGHT:
            if random.random() < 0.07:
                defence -= 2
        elif target_type == UnitType.FAST:
            if random.random() < 0.85:
                defence -= 1
        elif target_type == UnitType.LONG_RANGE:
            if random.random() < 0.75:
                defence += 1
    
    # LongRange type advantages
    if attacker_type == UnitType.LONG_RANGE:
        if target_type == UnitType.HEAVY:
            defence += 6
        elif target_type == UnitType.LIGHT:
            if random.random() < 0.75:
                defence -= 2
        elif target_type == UnitType.FAST:
            if random.random() < 0.72:
                defence -= 2
    
    # Base damage calculation
    damage = attack - defence
    if damage < 1:
        damage = 1
    
    # Random multiplier (0.9 - 1.1)
    random_multiplier = 0.9 + (random.random() * 0.2)
    final_damage = int(damage * random_multiplier)
    
    return max(1, final_damage)


def estimate_damage(attacker: Unit, target: Unit) -> float:
    """
    Estimate average damage without randomness.
    Useful for greedy evaluation without running many simulations.
    """
    attack = float(attacker.attack)
    defence = float(target.defence)
    
    # Average random effects
    # This is a simplified estimate
    avg_multiplier = 1.0
    
    base_damage = attack - defence
    if base_damage < 1:
        base_damage = 1
    
    return base_damage * avg_multiplier
