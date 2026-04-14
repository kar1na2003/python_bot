"""
Comprehensive pipeline script to analyze current heuristic, tune it, and generate CSV reports.
This script:
1. Runs games with current heuristic
2. Saves heuristic config and game logs
3. Tunes heuristic using existing tune_heuristics.py
4. Runs games again with tuned heuristic
5. Generates CSV tables for visualization
"""
import argparse
import csv
import json
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import itertools

from bot.heuristic_config import HeuristicConfig
import config


PROJECT_DIR = Path(__file__).resolve().parent
PYTHON_EXE = sys.executable
REPORTS_DIR = PROJECT_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


class GameRunner:
    """Run games with a specific heuristic configuration"""
    
    def __init__(self, games: int = 5):
        self.games = games
        self.results = []
    
    def run_games(self, heuristic_config: HeuristicConfig, label: str) -> Dict[str, Any]:
        """Run games with the given heuristic and return summary"""
        print(f"\n{'='*60}")
        print(f"Running {self.games} games with heuristic: {label}")
        print(f"{'='*60}")
        
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            cfg_path = td / "heuristic.json"
            summary_path = td / "summary.json"
            
            # Save heuristic config
            heuristic_config.dump_json(str(cfg_path))
            
            # Run games using main.py (connects to server)
            cmd = [
                PYTHON_EXE,
                str(PROJECT_DIR / "main.py"),
                "--games",
                str(self.games),
                "--heuristic-config",
                str(cfg_path),
                "--summary-json",
                str(summary_path),
            ]
            
            print(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=PROJECT_DIR)
            
            if result.returncode != 0:
                print(f"Warning: game run returned exit code {result.returncode}")
            
            # Load summary if available
            summary = {}
            if summary_path.exists():
                try:
                    with summary_path.open("r") as f:
                        summary = json.load(f)
                except Exception as e:
                    print(f"Could not load summary: {e}")
            
            result_entry = {
                "timestamp": datetime.now().isoformat(),
                "label": label,
                "games_requested": self.games,
                "heuristic": heuristic_config.weights.copy(),
                "unit_type_multipliers": heuristic_config.unit_type_multipliers.copy(),
                "summary": summary,
            }
            self.results.append(result_entry)
            return result_entry


class HeuristicTuner:
    """Tune heuristic weights using grid search"""
    
    @staticmethod
    def build_candidate_configs(base: HeuristicConfig, search_space: Dict = None):
        """Generate candidate heuristic configurations"""
        if search_space is None:
            # Default search space - small variations around current values
            search_space = {
                "kill_bonus": [160.0, 220.0, 280.0],
                "damage": [18.0, 24.0, 30.0],
                "focus_long_range": [25.0, 40.0, 60.0],
                "exposed_ranged": [-12.0, -22.0, -32.0],
                "threatened": [-10.0, -18.0, -26.0],
            }
        
        keys = list(search_space.keys())
        candidates = []
        
        for values in itertools.product(*(search_space[k] for k in keys)):
            cfg = HeuristicConfig()
            cfg.weights = dict(base.weights)
            cfg.unit_type_multipliers = dict(base.unit_type_multipliers)
            
            for k, v in zip(keys, values):
                if k in cfg.weights:
                    cfg.weights[k] = v
            
            candidates.append(cfg)
        
        return candidates
    
    @staticmethod
    def select_best_config(results: List[Dict]) -> HeuristicConfig:
        """Select best performing configuration from results"""
        best_config = None
        best_win_rate = -1
        
        for result in results:
            summary = result.get("summary", {})
            wins = summary.get("wins", 0)
            games = summary.get("games", result.get("games_requested", 1))
            win_rate = wins / games if games > 0 else 0
            
            if win_rate > best_win_rate:
                best_win_rate = win_rate
                best_config = HeuristicConfig()
                best_config.weights = result["heuristic"].copy()
                best_config.unit_type_multipliers = result.get("unit_type_multipliers", {}).copy()
        
        return best_config, best_win_rate


class CSVReportGenerator:
    """Generate CSV reports for visualization"""
    
    @staticmethod
    def generate_performance_csv(results: List[Dict], output_path: Path):
        """Generate CSV with performance metrics over iterations"""
        with output_path.open("w", newline="") as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                "iteration",
                "timestamp",
                "label",
                "games_run",
                "wins",
                "losses",
                "win_rate",
                "avg_moves",
                "total_duration_sec",
            ])
            
            # Data rows
            for i, result in enumerate(results, 1):
                summary = result.get("summary", {})
                writer.writerow([
                    i,
                    result["timestamp"],
                    result["label"],
                    summary.get("games", result.get("games_requested", 0)),
                    summary.get("wins", 0),
                    summary.get("losses", 0),
                    summary.get("win_rate", 0),
                    summary.get("avg_moves", 0),
                    summary.get("total_duration_sec", 0),
                ])
        
        print(f"[OK] Performance CSV saved to {output_path}")
    
    @staticmethod
    def generate_weights_csv(results: List[Dict], output_path: Path):
        """Generate CSV with heuristic weights for each iteration"""
        if not results:
            return
        
        # Collect all weight keys
        weight_keys = set()
        for result in results:
            weight_keys.update(result["heuristic"].keys())
        weight_keys = sorted(list(weight_keys))
        
        with output_path.open("w", newline="") as f:
            writer = csv.writer(f)
            
            # Header
            header = ["iteration", "timestamp", "label"] + weight_keys
            writer.writerow(header)
            
            # Data rows
            for i, result in enumerate(results, 1):
                row = [i, result["timestamp"], result["label"]]
                for key in weight_keys:
                    row.append(result["heuristic"].get(key, ""))
                writer.writerow(row)
        
        print(f"[OK] Weights CSV saved to {output_path}")
    
    @staticmethod
    def generate_comparison_csv(before_results: List[Dict], after_results: List[Dict], output_path: Path):
        """Generate CSV comparing before and after tuning"""
        with output_path.open("w", newline="") as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                "phase",
                "iteration",
                "label",
                "games_run",
                "wins",
                "losses",
                "win_rate",
                "avg_moves",
            ])
            
            # Before tuning
            for i, result in enumerate(before_results, 1):
                summary = result.get("summary", {})
                writer.writerow([
                    "BEFORE_TUNING",
                    i,
                    result["label"],
                    summary.get("games", result.get("games_requested", 0)),
                    summary.get("wins", 0),
                    summary.get("losses", 0),
                    summary.get("win_rate", 0),
                    summary.get("avg_moves", 0),
                ])
            
            # After tuning
            for i, result in enumerate(after_results, 1):
                summary = result.get("summary", {})
                writer.writerow([
                    "AFTER_TUNING",
                    i,
                    result["label"],
                    summary.get("games", result.get("games_requested", 0)),
                    summary.get("wins", 0),
                    summary.get("losses", 0),
                    summary.get("win_rate", 0),
                    summary.get("avg_moves", 0),
                ])
        
        print(f"[OK] Comparison CSV saved to {output_path}")
    
    @staticmethod
    def generate_summary_report(results: List[Dict], best_before: HeuristicConfig, 
                               best_before_rate: float, best_after: HeuristicConfig,
                               best_after_rate: float, output_path: Path):
        """Generate summary report of the entire pipeline"""
        with output_path.open("w") as f:
            f.write("=" * 70 + "\n")
            f.write("HEURISTIC TUNING PIPELINE SUMMARY REPORT\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            
            f.write("BEFORE TUNING:\n")
            f.write(f"  Best Win Rate: {best_before_rate:.2%}\n")
            f.write(f"  Heuristic Weights:\n")
            for k, v in sorted(best_before.weights.items()):
                f.write(f"    {k}: {v}\n")
            
            f.write("\nAFTER TUNING:\n")
            f.write(f"  Best Win Rate: {best_after_rate:.2%}\n")
            f.write(f"  Heuristic Weights:\n")
            for k, v in sorted(best_after.weights.items()):
                f.write(f"    {k}: {v}\n")
            
            f.write(f"\nImprovement: {(best_after_rate - best_before_rate):.2%}\n")
            
            f.write(f"\nTotal Iterations: {len(results)}\n")
            f.write(f"Total Games: {sum(r.get('summary', {}).get('games', 0) for r in results)}\n")
        
        print(f"[OK] Summary report saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Run heuristic analysis, tune, and generate reports"
    )
    parser.add_argument("--games-before", type=int, default=5,
                       help="Number of games to run before tuning (default: 5)")
    parser.add_argument("--games-after", type=int, default=5,
                       help="Number of games to run after tuning (default: 5)")
    parser.add_argument("--tune", action="store_true", default=True,
                       help="Enable tuning phase (default: True)")
    parser.add_argument("--skip-tune", action="store_true",
                       help="Skip tuning phase")
    parser.add_argument("--output-dir", type=Path, default=REPORTS_DIR,
                       help="Output directory for CSV files")
    
    args = parser.parse_args()
    
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "=" * 70)
    print("HEURISTIC ANALYSIS AND TUNING PIPELINE")
    print("=" * 70)
    
    # Phase 1: Run games with current heuristic
    print("\nPhase 1: Analysis - Running games with CURRENT heuristic")
    runner = GameRunner(games=args.games_before)
    current_heuristic = HeuristicConfig()
    before_results = [
        runner.run_games(current_heuristic, f"current_iteration_{i}")
        for i in range(1, 2)  # Single run before tuning
    ]
    
    best_before, best_before_rate = HeuristicTuner.select_best_config(before_results)
    print(f"\nBefore tuning - Best win rate: {best_before_rate:.2%}")
    
    # Phase 2: Tune heuristic
    after_results = []
    if not args.skip_tune:
        print("\nPhase 2: Tuning - Optimizing heuristic weights")
        print("Running multiple candidate configurations...")
        
        tuner = HeuristicTuner()
        candidates = tuner.build_candidate_configs(best_before)
        
        print(f"Testing {len(candidates)} candidate configurations")
        runner_tune = GameRunner(games=args.games_after)
        
        for idx, candidate in enumerate(candidates, 1):
            print(f"\n[{idx}/{len(candidates)}] Testing candidate configuration...")
            result = runner_tune.run_games(candidate, f"tuned_candidate_{idx}")
            after_results.append(result)
        
        best_after, best_after_rate = HeuristicTuner.select_best_config(after_results)
        print(f"\nAfter tuning - Best win rate: {best_after_rate:.2%}")
        print(f"Improvement: {(best_after_rate - best_before_rate):.2%}")
        
        # Save best tuned configuration
        best_config_path = args.output_dir / "best_tuned_heuristic.json"
        best_after.dump_json(str(best_config_path))
        print(f"\n[OK] Best tuned heuristic saved to {best_config_path}")
    else:
        best_after = best_before
        best_after_rate = best_before_rate
        print("\nSkipping tuning phase as requested")
    
    # Phase 3: Generate CSV reports
    print("\nPhase 3: Generating reports...")
    generator = CSVReportGenerator()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Performance CSV
    perf_csv = args.output_dir / f"performance_{timestamp}.csv"
    all_results = before_results + after_results
    generator.generate_performance_csv(all_results, perf_csv)
    
    # Weights CSV
    weights_csv = args.output_dir / f"heuristic_weights_{timestamp}.csv"
    generator.generate_weights_csv(all_results, weights_csv)
    
    # Comparison CSV
    if after_results:
        comparison_csv = args.output_dir / f"before_after_comparison_{timestamp}.csv"
        generator.generate_comparison_csv(before_results, after_results, comparison_csv)
    
    # Summary report
    summary_txt = args.output_dir / f"summary_report_{timestamp}.txt"
    generator.generate_summary_report(all_results, best_before, best_before_rate,
                                     best_after, best_after_rate, summary_txt)
    
    # Final summary
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    print(f"\nReports generated in: {args.output_dir}")
    print(f"  - performance_{timestamp}.csv")
    print(f"  - heuristic_weights_{timestamp}.csv")
    if after_results:
        print(f"  - before_after_comparison_{timestamp}.csv")
    print(f"  - summary_report_{timestamp}.txt")
    
    print(f"\nKey Metrics:")
    print(f"  Before Tuning - Win Rate: {best_before_rate:.2%}")
    print(f"  After Tuning  - Win Rate: {best_after_rate:.2%}")
    print(f"  Improvement: {(best_after_rate - best_before_rate):.2%}")
    

if __name__ == "__main__":
    main()
