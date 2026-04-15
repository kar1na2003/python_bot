from typing import Dict, Any

class StateDataExtractor:
    """Extracts raw game state into structured numerical features for ML."""

    @staticmethod
    def extract_features(game_state: Any) -> Dict[str, float]:
        return {
            "turn_number": getattr(game_state, "turn_number", 0),
            "my_units_count": len(getattr(game_state, "my_units", [])),
            "enemy_units_count": len(getattr(game_state, "enemy_units", [])),
            "health_pool": sum(u.health for u in getattr(game_state, "my_units", []) if hasattr(u, 'health'))
        }