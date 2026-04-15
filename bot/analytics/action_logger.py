import csv
import os

class ActionLogger:
    """Logs detailed per-turn actions for Data Analytics dashboards."""
    
    def __init__(self, filepath="logs/detailed_actions.csv"):
        self.filepath = filepath
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        # Створюємо файл із заголовками, якщо його ще немає
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "game_id", "team", "unit_name", "unit_type", 
                    "action_type", "target", "health", "position"
                ])

    def log_action(self, game_id, team, unit_name, unit_type, action_type, target, health, position):
        """Appends a single unit's action to the detailed dataset."""
        with open(self.filepath, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([game_id, team, unit_name, unit_type, action_type, target, health, position])

def export_summary_csv(game_id: int, winner: str, is_victory: bool, filepath="logs/matches_summary.csv"):
    """Exports a simplified match summary to CSV for quick analytics."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    file_exists = os.path.exists(filepath)
    with open(filepath, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["game_id", "winner", "is_victory"])
        writer.writerow([game_id, winner, is_victory])