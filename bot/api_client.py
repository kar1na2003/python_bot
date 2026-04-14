"""
API Client - Communication with Arena.AI server
"""

import requests
import json
from typing import Optional, Dict, Any
from urllib3.exceptions import InsecureRequestWarning
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(InsecureRequestWarning)

from .game_state import BattleState, UserAction
import config


class APIClient:
    """Client for communicating with Arena.AI server"""
    
    def __init__(self, server_url: str = config.SERVER_URL, timeout: int = config.REQUEST_TIMEOUT):
        self.server_url = server_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.verify = False  # Ignore SSL warnings for self-signed certs
    
    def create_random_teams(self) -> Dict[str, Any]:
        """Get random teams from server"""
        try:
            url = f"{self.server_url}/BattleCalculator/random-team"
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching random teams: {e}")
            raise
    
    def create_pvb_battle(self) -> str:
        """Create a Player vs Bot battle and get invite ID"""
        try:
            url = f"{self.server_url}/BattleCalculator/create-pvb"
            response = self.session.post(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text.strip('"')  # Remove quotes from JSON string
        except requests.RequestException as e:
            print(f"Error creating PvB battle: {e}")
            raise
    
    def create_pvp_battle(self) -> str:
        """Create a Player vs Player battle and get invite ID"""
        try:
            url = f"{self.server_url}/BattleCalculator/create-pvp"
            response = self.session.post(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text.strip('"')
        except requests.RequestException as e:
            print(f"Error creating PvP battle: {e}")
            raise
    
    def get_battle_state(self, battle_id: str) -> BattleState:
        """Get current battle state from server"""
        try:
            url = f"{self.server_url}/Battle/{battle_id}"
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return BattleState.from_dict(data)
        except requests.RequestException as e:
            print(f"Error fetching battle state: {e}")
            raise
    
    def send_action(self, battle_id: str, action: UserAction) -> bool:
        """Send action to server"""
        try:
            url = f"{self.server_url}/Battle/{battle_id}/action"
            payload = action.to_dict()
            
            response = self.session.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Error sending action: {e}")
            return False
    
    def get_battle_result(self, battle_id: str) -> Dict[str, Any]:
        """Get final battle result"""
        try:
            url = f"{self.server_url}/Battle/{battle_id}/result"
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching battle result: {e}")
            raise
    
    @staticmethod
    def create_offline_teams():
        """Create test teams for offline simulation (no server required)"""
        from .game_state import Team, Unit, UnitType
        
        # Team A - Mixed units
        team_a_units = [
            Unit(type=UnitType.LIGHT, attack=8, defence=3, range=2, movement=4, name="Scout_A1", health=15, x_position=2, y_position=2),
            Unit(type=UnitType.HEAVY, attack=10, defence=7, range=1, movement=2, name="Tank_A1", health=30, x_position=2, y_position=4),
            Unit(type=UnitType.LONG_RANGE, attack=9, defence=2, range=8, movement=2, name="Archer_A1", health=12, x_position=4, y_position=2),
        ]
        
        # Team B - Mixed units
        team_b_units = [
            Unit(type=UnitType.LIGHT, attack=8, defence=3, range=2, movement=4, name="Scout_B1", health=15, x_position=17, y_position=17),
            Unit(type=UnitType.HEAVY, attack=10, defence=7, range=1, movement=2, name="Tank_B1", health=30, x_position=17, y_position=15),
            Unit(type=UnitType.LONG_RANGE, attack=9, defence=2, range=8, movement=2, name="Archer_B1", health=12, x_position=15, y_position=17),
        ]
        
        return {
            'teamA': Team(name='Team A', units=team_a_units),
            'teamB': Team(name='Team B', units=team_b_units)
        }
    
    @staticmethod
    def health_check(server_url: str = config.SERVER_URL) -> bool:
        """Check if server is reachable by trying to get random teams"""
        try:
            response = requests.get(
                f"{server_url}/BattleCalculator/random-team",
                timeout=5,
                verify=False
            )
            return response.status_code == 200
        except:
            return False
