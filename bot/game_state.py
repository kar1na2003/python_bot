"""
Game State Models - Represents game entities and state
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from copy import deepcopy
import json


# Unit Types Enum
class UnitType:
    LIGHT = 0
    HEAVY = 1
    FAST = 2
    SHORT_RANGE = 3
    LONG_RANGE = 4
    
    TYPES = {
        0: "Light",
        1: "Heavy",
        2: "Fast",
        3: "ShortRange",
        4: "LongRange"
    }


class ActionType:
    MOVE = "Move"
    ATTACK = "Attack"
    SKIP = "Skip"


@dataclass
class Unit:
    """Represents a single combat unit"""
    type: int  # 0-4 UnitType
    attack: int
    defence: int
    range: int
    movement: int
    name: str
    health: int
    x_position: int = 0
    y_position: int = 0
    
    @property
    def is_dead(self) -> bool:
        return self.health <= 0
    
    @property
    def position(self) -> tuple:
        return (self.x_position, self.y_position)
    
    def deep_copy(self) -> 'Unit':
        """Create a deep copy of this unit"""
        return Unit(
            type=self.type,
            attack=self.attack,
            defence=self.defence,
            range=self.range,
            movement=self.movement,
            name=self.name,
            health=self.health,
            x_position=self.x_position,
            y_position=self.y_position
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "type": UnitType.TYPES[self.type],
            "attack": self.attack,
            "defence": self.defence,
            "range": self.range,
            "movement": self.movement,
            "name": self.name,
            "health": self.health,
            "xPosition": self.x_position,
            "yPosition": self.y_position,
            "isDead": self.is_dead
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'Unit':
        """Create Unit from dictionary (JSON)"""
        # Handle type parsing (could be string or int)
        unit_type = data.get('type')
        if isinstance(unit_type, str):
            # Find type by name
            unit_type = next(k for k, v in UnitType.TYPES.items() if v == unit_type)
        
        return Unit(
            type=unit_type,
            attack=data.get('attack', 0),
            defence=data.get('defence', 0),
            range=data.get('range', 0),
            movement=data.get('movement', 0),
            name=data.get('name', ''),
            health=data.get('health', 10),
            x_position=data.get('xPosition', 0),
            y_position=data.get('yPosition', 0)
        )


@dataclass
class Team:
    """Represents a team of units"""
    name: str
    units: List[Unit] = field(default_factory=list)
    
    @property
    def alive_units(self) -> List[Unit]:
        """Get list of alive units"""
        return [u for u in self.units if not u.is_dead]
    
    @property
    def is_anyone_alive(self) -> bool:
        """Check if team has any alive units"""
        return len(self.alive_units) > 0
    
    def deep_copy(self) -> 'Team':
        """Create a deep copy of this team"""
        return Team(
            name=self.name,
            units=[u.deep_copy() for u in self.units]
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "units": [u.to_dict() for u in self.units],
            "aliveUnits": [u.to_dict() for u in self.alive_units],
            "isAnyoneAlive": self.is_anyone_alive
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'Team':
        """Create Team from dictionary (JSON)"""
        units = [Unit.from_dict(u) for u in data.get('units', [])]
        return Team(
            name=data.get('name', ''),
            units=units
        )


@dataclass
class NextUnitInfo:
    """Information about the unit whose turn it is"""
    team_name: str
    unit: Unit
    available_destinations: List[str]  # e.g., ["A1", "B2", ...]
    available_attack_targets: List[str]  # Unit names
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "teamName": self.team_name,
            "unit": self.unit.to_dict(),
            "availableDestinations": self.available_destinations,
            "availableAttackTarget": self.available_attack_targets
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'NextUnitInfo':
        """Create NextUnitInfo from dictionary (JSON)"""
        return NextUnitInfo(
            team_name=data.get('teamName', ''),
            unit=Unit.from_dict(data.get('unit', {})),
            available_destinations=data.get('availableDestinations', []),
            available_attack_targets=data.get('availableAttackTarget', [])
        )


@dataclass
class BattleState:
    """Represents the current state of a battle"""
    battle_id: str
    team_a: Team
    team_b: Team
    next_unit_info: NextUnitInfo
    winner: Optional[str] = None
    
    def deep_copy(self) -> 'BattleState':
        """Create a deep copy of the battle state"""
        return BattleState(
            battle_id=self.battle_id,
            team_a=self.team_a.deep_copy(),
            team_b=self.team_b.deep_copy(),
            next_unit_info=NextUnitInfo(
                team_name=self.next_unit_info.team_name,
                unit=self.next_unit_info.unit.deep_copy(),
                available_destinations=self.next_unit_info.available_destinations.copy(),
                available_attack_targets=self.next_unit_info.available_attack_targets.copy()
            ),
            winner=self.winner
        )
    
    @property
    def is_game_over(self) -> bool:
        """Check if game is over"""
        return self.winner is not None
    
    @property
    def current_team(self) -> Team:
        """Get the team whose turn it is"""
        return self.team_a if self.next_unit_info.team_name == self.team_a.name else self.team_b
    
    @property
    def enemy_team(self) -> Team:
        """Get the enemy team"""
        return self.team_b if self.next_unit_info.team_name == self.team_a.name else self.team_a
    
    def get_unit_by_name(self, name: str) -> Optional[Unit]:
        """Find unit by name in either team"""
        for unit in self.team_a.units + self.team_b.units:
            if unit.name == name:
                return unit
        return None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "battleId": self.battle_id,
            "teamA": self.team_a.to_dict(),
            "teamB": self.team_b.to_dict(),
            "nextUnitInfo": self.next_unit_info.to_dict(),
            "winner": self.winner
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'BattleState':
        """Create BattleState from dictionary (JSON)"""
        team_a = Team.from_dict(data.get('teamA', {}))
        team_b = Team.from_dict(data.get('teamB', {}))
        next_unit_info = NextUnitInfo.from_dict(data.get('nextUnitInfo', {}))
        
        # Ensure the Unit in NextUnitInfo references the actual unit in team
        if next_unit_info.unit:
            actual_unit = None
            if next_unit_info.team_name == team_a.name:
                actual_unit = next((u for u in team_a.units if u.name == next_unit_info.unit.name), None)
            else:
                actual_unit = next((u for u in team_b.units if u.name == next_unit_info.unit.name), None)
            
            if actual_unit:
                next_unit_info.unit = actual_unit
        
        return BattleState(
            battle_id=data.get('battleId', ''),
            team_a=team_a,
            team_b=team_b,
            next_unit_info=next_unit_info,
            winner=data.get('winner')
        )


@dataclass
@dataclass(frozen=True)
class UserAction:
    """Represents an action a player takes"""
    action_type: str  # ActionType.MOVE, ActionType.ATTACK, ActionType.SKIP
    destination: Optional[str] = None  # For move actions, e.g., "A1"
    target: Optional[str] = None  # For attack actions, unit name
    
    @staticmethod
    def skip() -> 'UserAction':
        """Create a skip action"""
        return UserAction(action_type=ActionType.SKIP)
    
    @staticmethod
    def move(destination: str) -> 'UserAction':
        """Create a move action"""
        return UserAction(action_type=ActionType.MOVE, destination=destination)
    
    @staticmethod
    def attack(target: str) -> 'UserAction':
        """Create an attack action"""
        return UserAction(action_type=ActionType.ATTACK, target=target)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "actionType": self.action_type,
            "destination": self.destination,
            "target": self.target
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
