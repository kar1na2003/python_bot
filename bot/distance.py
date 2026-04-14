"""
Distance Calculator - Implements arena distance and movement logic
"""

import math
from typing import Tuple, List
from .game_state import Unit, Team


DIAGONAL_PENALTY = 1.5


def coordinate_distance(x1: int, y1: int, x2: int, y2: int) -> float:
    """
    Calculate shortest distance between two coordinates.
    Uses Chebyshev distance (like chess king) but with diagonal penalty.
    """
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    
    # Both directions equally, diagonal costs 1.5
    if dx == 0 or dy == 0:
        return max(dx, dy)
    
    # Diagonal movement
    min_dim = min(dx, dy)
    max_dim = max(dx, dy)
    return min_dim * DIAGONAL_PENALTY + (max_dim - min_dim)


def get_shortest_distance_value(unit1: Unit, unit2: Unit) -> float:
    """Get distance between two units"""
    return coordinate_distance(unit1.x_position, unit1.y_position, 
                              unit2.x_position, unit2.y_position)


def get_distance_to_position(unit: Unit, x: int, y: int) -> float:
    """Get distance from unit to position"""
    return coordinate_distance(unit.x_position, unit.y_position, x, y)


def is_near(unit1: Unit, unit2: Unit) -> bool:
    """Check if units are adjacent (Chebyshev distance <= 1)"""
    dx = abs(unit2.x_position - unit1.x_position)
    dy = abs(unit2.y_position - unit1.y_position)
    return max(dx, dy) <= 1


def can_attack_without_moving(attacker: Unit, target: Unit) -> bool:
    """Check if attacker can hit target without moving"""
    # Melee range (adjacent)
    if is_near(attacker, target):
        return True
    
    # Ranged attack (within range, accounting for diagonal penalty)
    distance = get_shortest_distance_value(attacker, target)
    if distance <= attacker.range + (DIAGONAL_PENALTY - 1):
        return True
    
    return False


def can_attack_with_movement(attacker: Unit, target: Unit) -> bool:
    """Check if attacker can reach and attack target with full movement"""
    distance = get_shortest_distance_value(attacker, target)
    return distance <= attacker.range + attacker.movement + (DIAGONAL_PENALTY - 1)


def find_valid_targets(attacker: Unit, team: Team) -> List[Unit]:
    """Find all units in a team that attacker can hit without moving"""
    targets = []
    for unit in team.alive_units:
        if can_attack_without_moving(attacker, unit):
            targets.append(unit)
    return targets


def get_movement_step(from_val: int, to_val: int) -> int:
    """Calculate single step movement (-1, 0, or 1)"""
    if from_val > to_val:
        return -1
    elif from_val < to_val:
        return 1
    return 0


def move(unit: Unit, x: int, y: int):
    """Move unit to new position"""
    unit.x_position = x
    unit.y_position = y


def get_available_destinations(unit: Unit, all_units: List[Unit], 
                               arena_width: int = 20, arena_height: int = 20) -> List[Tuple[int, int]]:
    """
    Get all valid movement destinations for a unit.
    Returns list of (x, y) coordinates the unit can reach using its movement.
    """
    occupied = {(u.x_position, u.y_position) for u in all_units if u is not unit}
    available = []
    
    for x in range(1, arena_width + 1):
        for y in range(1, arena_height + 1):
            # Skip occupied cells
            if (x, y) in occupied:
                continue
            
            # Check if reachable within movement range
            distance = get_distance_to_position(unit, x, y)
            if distance <= unit.movement:
                available.append((x, y))
    
    return available


def coordinate_to_string(x: int, y: int) -> str:
    """Convert (x, y) coordinates to string format like 'A1', 'B2', etc."""
    # x is 1-20, columns A-T
    # y is 1-20, rows 1-20
    if not (1 <= x <= 20 and 1 <= y <= 20):
        raise ValueError(f"Invalid coordinates: ({x}, {y})")
    
    col_letter = chr(ord('A') + x - 1)  # A-T
    row_number = str(y)
    return f"{col_letter}{row_number}"


def string_to_coordinate(pos_str: str) -> Tuple[int, int]:
    """Convert string format 'A1' to (x, y) coordinates"""
    if len(pos_str) < 2:
        raise ValueError(f"Invalid position string: {pos_str}")
    
    col_letter = pos_str[0].upper()
    row_number = int(pos_str[1:])
    
    x = ord(col_letter) - ord('A') + 1
    if not (1 <= x <= 20 and 1 <= row_number <= 20):
        raise ValueError(f"Invalid position: {pos_str}")
    
    return (x, row_number)
