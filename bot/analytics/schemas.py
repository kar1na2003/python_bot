from dataclasses import dataclass

@dataclass
class MatchRecord:
    """Data schema for a single match result."""
    date: str
    my_team: str
    winner: str
    win: bool
    turns: int