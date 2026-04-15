import csv
import os
import time

class MctsTelemetry:
    """Collects performance metrics of the MCTS engine."""

    def __init__(self, filepath="logs/mcts_metrics.csv"):
        self.filepath = filepath
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w', newline='') as f:
                csv.writer(f).writerow(["timestamp", "turn", "iterations", "time_ms", "score"])

    def log(self, turn: int, iters: int, time_ms: float, score: float):
        with open(self.filepath, 'a', newline='') as f:
            csv.writer(f).writerow([time.time(), turn, iters, time_ms, score])