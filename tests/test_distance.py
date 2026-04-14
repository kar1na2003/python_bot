"""
Test: Distance Calculations
Tests the distance and movement calculation module
"""

import unittest
from bot.distance import (
    coordinate_distance, string_to_coordinate, coordinate_to_string,
    can_attack_without_moving, get_distance_to_position
)
from bot.game_state import Unit


class TestDistanceCalculations(unittest.TestCase):
    """Test distance calculations"""
    
    def test_diagonal_penalty(self):
        """Test that diagonal movement costs 1.5"""
        # Diagonal 1 step = 1.5 cost
        dist = coordinate_distance(1, 1, 2, 2)
        self.assertEqual(dist, 1.5)
        
        # Horizontal 1 step = 1 cost
        dist = coordinate_distance(1, 1, 2, 1)
        self.assertEqual(dist, 1)
        
        # Vertical 1 step = 1 cost
        dist = coordinate_distance(1, 1, 1, 2)
        self.assertEqual(dist, 1)
    
    def test_coordinate_conversion(self):
        """Test A1 ↔ (1,1) conversion"""
        # Test A1
        x, y = string_to_coordinate("A1")
        self.assertEqual((x, y), (1, 1))
        
        # Test T20
        x, y = string_to_coordinate("T20")
        self.assertEqual((x, y), (20, 20))
        
        # Test M10
        x, y = string_to_coordinate("M10")
        self.assertEqual((x, y), (13, 10))
        
        # Test reverse
        pos = coordinate_to_string(1, 1)
        self.assertEqual(pos, "A1")
        
        pos = coordinate_to_string(20, 20)
        self.assertEqual(pos, "T20")
    
    def test_round_trip_conversion(self):
        """Test A1 → (x,y) → A1 round trip"""
        for col in 'ABCDEFGHIJKLMNOPQRST':
            for row in range(1, 21):
                original = col + str(row)
                x, y = string_to_coordinate(original)
                converted_back = coordinate_to_string(x, y)
                self.assertEqual(original, converted_back,
                               f"Failed for {original}")
    
    def test_attack_range(self):
        """Test attack range calculation"""
        attacker = Unit(
            type=0, attack=5, defence=3, range=2,
            movement=3, name="Attacker", health=10,
            x_position=5, y_position=5
        )
        
        target_close = Unit(
            type=0, attack=5, defence=3, range=1,
            movement=3, name="Target1", health=10,
            x_position=6, y_position=5  # Distance 1
        )
        
        target_far = Unit(
            type=0, attack=5, defence=3, range=1,
            movement=3, name="Target2", health=10,
            x_position=10, y_position=10  # Distance > range
        )
        
        # Melee range (adjacent)
        self.assertTrue(can_attack_without_moving(attacker, target_close))
        
        # Out of range
        self.assertFalse(can_attack_without_moving(attacker, target_far))


class TestMovementCalculations(unittest.TestCase):
    """Test movement calculations"""
    
    def test_unit_distance(self):
        """Test distance between units"""
        unit1 = Unit(
            type=0, attack=5, defence=3, range=1,
            movement=3, name="Unit1", health=10,
            x_position=1, y_position=1
        )
        
        unit2 = Unit(
            type=0, attack=5, defence=3, range=1,
            movement=3, name="Unit2", health=10,
            x_position=5, y_position=5
        )
        
        dist = get_distance_to_position(unit1, 5, 5)
        # Should be: min(4,4)*1.5 + (4-4) = 6
        self.assertEqual(dist, 6)


if __name__ == '__main__':
    unittest.main()
