#!/usr/bin/env python3
"""
Data analysis and comparison utilities for heuristic tuning results.
Provides detailed statistical analysis of CSV output files.
"""
import csv
import json
from pathlib import Path
from typing import List, Dict, Tuple
from statistics import mean, stdev, median


class ResultsAnalyzer:
    """Analyze and compare heuristic tuning results"""
    
    def __init__(self, csv_path: Path):
        self.csv_path = csv_path
        self.rows = []
        self._load_csv()
    
    def _load_csv(self):
        """Load CSV file"""
        with self.csv_path.open("r") as f:
            reader = csv.DictReader(f)
            self.rows = list(reader)
    
    def get_before_after_split(self) -> Tuple[List[Dict], List[Dict]]:
        """Split results into before and after tuning phases"""
        before = []
        after = []
        
        for row in self.rows:
            label = row.get("label", "")
            if "current" in label or "before" in label.lower():
                before.append(row)
            else:
                after.append(row)
        
        return before, after
    
    def calculate_statistics(self, rows: List[Dict]) -> Dict:
        """Calculate statistics for a set of rows"""
        if not rows:
            return {}
        
        win_rates = [float(r.get("win_rate", 0)) for r in rows]
        avg_moves = [float(r.get("avg_moves", 0)) for r in rows if r.get("avg_moves")]
        total_games = sum(int(r.get("games_run", 0)) for r in rows)
        total_wins = sum(int(r.get("wins", 0)) for r in rows)
        
        return {
            "total_games": total_games,
            "total_wins": total_wins,
            "win_rates": win_rates,
            "avg_win_rate": mean(win_rates) if win_rates else 0,
            "median_win_rate": median(win_rates) if win_rates else 0,
            "min_win_rate": min(win_rates) if win_rates else 0,
            "max_win_rate": max(win_rates) if win_rates else 0,
            "std_win_rate": stdev(win_rates) if len(win_rates) > 1 else 0,
            "avg_moves": mean(avg_moves) if avg_moves else 0,
        }
    
    def compare_phases(self) -> Dict:
        """Compare before and after phases"""
        before, after = self.get_before_after_split()
        
        before_stats = self.calculate_statistics(before)
        after_stats = self.calculate_statistics(after)
        
        improvement = after_stats.get("avg_win_rate", 0) - before_stats.get("avg_win_rate", 0)
        improvement_pct = (improvement / before_stats["avg_win_rate"] * 100 if before_stats["avg_win_rate"] > 0 else 0)
        
        return {
            "before": before_stats,
            "after": after_stats,
            "improvement_rate": improvement,
            "improvement_percent": improvement_pct,
        }
    
    def find_best_configuration(self) -> Tuple[Dict, float]:
        """Find the best performing configuration"""
        best_row = None
        best_rate = -1
        
        for row in self.rows:
            rate = float(row.get("win_rate", 0))
            if rate > best_rate:
                best_rate = rate
                best_row = row
        
        return best_row, best_rate
    
    def print_summary(self):
        """Print a formatted summary of results"""
        comparison = self.compare_phases()
        best_row, best_rate = self.find_best_configuration()
        
        print("\n" + "="*70)
        print("RESULTS SUMMARY")
        print("="*70)
        
        before = comparison["before"]
        after = comparison["after"]
        
        print(f"\n[DATA] BEFORE TUNING:")
        print(f"  Games Played:     {before['total_games']}")
        print(f"  Total Wins:       {before['total_wins']}")
        print(f"  Avg Win Rate:     {before['avg_win_rate']:.1%}")
        print(f"  Median:           {before['median_win_rate']:.1%}")
        print(f"  Range:            {before['min_win_rate']:.1%} - {before['max_win_rate']:.1%}")
        if before['std_win_rate'] > 0:
            print(f"  Std Dev:          {before['std_win_rate']:.1%}")
        
        print(f"\n[DATA] AFTER TUNING:")
        print(f"  Games Played:     {after['total_games']}")
        print(f"  Total Wins:       {after['total_wins']}")
        print(f"  Avg Win Rate:     {after['avg_win_rate']:.1%}")
        print(f"  Median:           {after['median_win_rate']:.1%}")
        print(f"  Range:            {after['min_win_rate']:.1%} - {after['max_win_rate']:.1%}")
        if after['std_win_rate'] > 0:
            print(f"  Std Dev:          {after['std_win_rate']:.1%}")
        
        improvement = comparison["improvement_rate"]
        improvement_pct = comparison["improvement_percent"]
        
        print(f"\n[RESULT] IMPROVEMENT:")
        print(f"  Absolute:         {improvement:+.1%}")
        print(f"  Relative:         {improvement_pct:+.1f}%")
        
        if improvement > 0.05:
            print(f"  Assessment:       [OK] SIGNIFICANT IMPROVEMENT")
        elif improvement > 0:
            print(f"  Assessment:       [INFO] MODEST IMPROVEMENT")
        elif improvement > -0.05:
            print(f"  Assessment:       [WARNING] MINIMAL CHANGE")
        else:
            print(f"  Assessment:       [ERROR] PERFORMANCE DECREASED")
        
        if best_row:
            print(f"\n[BEST] BEST CONFIGURATION:")
            print(f"  Label:            {best_row.get('label')}")
            print(f"  Win Rate:         {best_rate:.1%}")
            print(f"  Games:            {best_row.get('games_run')}")


def print_analysis():
    """Analyze latest results"""
    reports_dir = Path("reports")
    
    # Find latest performance CSV
    latest_csv = None
    for f in reports_dir.glob("performance_*.csv"):
        if latest_csv is None or f.stat().st_mtime > latest_csv.stat().st_mtime:
            latest_csv = f
    
    if not latest_csv:
        print("[ERROR] No results found. Run a pipeline first.")
        return
    
    analyzer = ResultsAnalyzer(latest_csv)
    analyzer.print_summary()


if __name__ == "__main__":
    print_analysis()
