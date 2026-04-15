import json
from datetime import datetime

def export_summary(winner: str, turns: int, team_id: str, filepath="logs/summary.jsonl"):
    """Aggregates match results into JSON-lines format for Big Data tools."""
    data = {
        "date": datetime.utcnow().isoformat(),
        "my_team": team_id,
        "winner": winner,
        "win": winner == team_id,
        "turns": turns
    }
    with open(filepath, 'a') as f:
        f.write(json.dumps(data) + '\n')