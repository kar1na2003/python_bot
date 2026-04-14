"""
Utility script to quickly run common pipeline workflows and analyze results.
"""
import subprocess
import sys
from pathlib import Path
import csv
from datetime import datetime
from typing import List, Dict


PROJECT_DIR = Path(__file__).resolve().parent
PYTHON_EXE = sys.executable
REPORTS_DIR = PROJECT_DIR / "reports"


def run_command(cmd: List[str], description: str = "") -> bool:
    """Run a shell command and return success status"""
    if description:
        print(f"\n{'='*70}")
        print(f"{description}")
        print(f"{'='*70}")
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_DIR)
    return result.returncode == 0


def workflow_quick_test():
    """Quick test: 2 games before, 2 after - ~5 minutes"""
    print("\n[LAUNCHER] QUICK TEST WORKFLOW - ~5 minutes")
    success = run_command(
        [PYTHON_EXE, "analyze_and_tune_pipeline.py", 
         "--games-before", "2", "--games-after", "2"],
        "Step 1/3: Running analysis and tuning pipeline..."
    )
    
    if success:
        run_command(
            [PYTHON_EXE, "visualize_results.py"],
            "Step 2/3: Generating visualizations..."
        )
        print("\n[OK] Quick test complete! Check reports/ directory")
    else:
        print("\n[ERROR] Pipeline failed")


def workflow_full_analysis():
    """Full analysis: 10 games before, 10 after - ~20 minutes"""
    print("\n[LAUNCHER] FULL ANALYSIS WORKFLOW - ~20 minutes")
    success = run_command(
        [PYTHON_EXE, "analyze_and_tune_pipeline.py",
         "--games-before", "10", "--games-after", "10"],
        "Step 1/3: Running full analysis pipeline..."
    )
    
    if success:
        run_command(
            [PYTHON_EXE, "visualize_results.py"],
            "Step 2/3: Generating visualizations..."
        )
        run_command(
            [PYTHON_EXE, "-c", "from analyzer_utils import print_analysis; print_analysis()"],
            "Step 3/3: Analyzing results..."
        )
        print("\n[OK] Full analysis complete!")
    else:
        print("\n[ERROR] Pipeline failed")


def workflow_baseline_only():
    """Baseline only: 20 games with current heuristic"""
    print("\n[LAUNCHER] BASELINE EVALUATION WORKFLOW - ~15 minutes")
    success = run_command(
        [PYTHON_EXE, "analyze_and_tune_pipeline.py",
         "--skip-tune", "--games-before", "20"],
        "Evaluating current heuristic over 20 games..."
    )
    
    if success:
        print("\n[OK] Baseline evaluation complete!")
        print("[INFO] Run visualize_results.py to see performance trends")
    else:
        print("\n[ERROR] Evaluation failed")


def workflow_focused_tuning():
    """Focused tuning: 5 games before/after for iterative refinement"""
    print("\n[LAUNCHER] FOCUSED TUNING WORKFLOW - ~13 minutes")
    success = run_command(
        [PYTHON_EXE, "analyze_and_tune_pipeline.py",
         "--games-before", "5", "--games-after", "5"],
        "Running focused tuning iteration..."
    )
    
    if success:
        run_command(
            [PYTHON_EXE, "visualize_results.py"],
            "Generating visualizations..."
        )
        print("\n[OK] Tuning iteration complete!")
        print("[TIP] Run this multiple times to iteratively improve")
    else:
        print("\n[ERROR] Tuning failed")


def analyze_latest_results():
    """Analyze the latest results in reports/"""
    print("\n[ANALYSIS] ANALYZING LATEST RESULTS")
    print("="*70)
    
    perf_csv = None
    for f in REPORTS_DIR.glob("performance_*.csv"):
        if perf_csv is None or f.stat().st_mtime > perf_csv.stat().st_mtime:
            perf_csv = f
    
    if not perf_csv:
        print("[ERROR] No results found. Run a pipeline first.")
        return
    
    print(f"[INFO] Latest results: {perf_csv.name}")
    print()
    
    # Read CSV
    rows = []
    with perf_csv.open("r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        print("No data in CSV")
        return
    
    # Find phase boundary
    before_count = 0
    for i, row in enumerate(rows):
        if "current" in row.get("label", ""):
            before_count = i + 1
        else:
            break
    
    # Calculate statistics
    before_rows = rows[:before_count]
    after_rows = rows[before_count:]
    
    def calc_stats(data):
        if not data:
            return None, None, None
        win_rates = [float(r.get("win_rate", 0)) for r in data]
        avg_win = sum(win_rates) / len(win_rates)
        best_win = max(win_rates)
        worst_win = min(win_rates)
        return avg_win, best_win, worst_win
    
    before_avg, before_best, before_worst = calc_stats(before_rows)
    after_avg, after_best, after_worst = calc_stats(after_rows)
    
    # Print results
    if before_avg is not None:
        print("[DATA] BEFORE TUNING:")
        print(f"  Average Win Rate: {before_avg:.1%}")
        print(f"  Best:             {before_best:.1%}")
        print(f"  Worst:            {before_worst:.1%}")
        print(f"  Games Played:     {sum(int(r.get('games_run', 0)) for r in before_rows)}")
        print()
    
    if after_avg is not None:
        print("[DATA] AFTER TUNING:")
        print(f"  Average Win Rate: {after_avg:.1%}")
        print(f"  Best:             {after_best:.1%}")
        print(f"  Worst:            {after_worst:.1%}")
        print(f"  Games Played:     {sum(int(r.get('games_run', 0)) for r in after_rows)}")
        print()
    
    if before_avg and after_avg:
        improvement = after_avg - before_avg
        print(f"[RESULT] IMPROVEMENT: {improvement:+.1%}")
        if improvement > 0.05:
            print("[OK] Significant improvement found!")
        elif improvement > 0:
            print("[INFO] Modest improvement - run more iterations for confirmation")
        elif improvement > -0.05:
            print("[WARNING] No clear improvement - try adjusting search space")
        else:
            print("[ERROR] Performance decreased - review weight changes")
    
    # Check for best tuned heuristic
    best_heuristic = REPORTS_DIR / "best_tuned_heuristic.json"
    if best_heuristic.exists():
        print(f"\n[SAVED] Best heuristic saved to: {best_heuristic.name}")


def list_reports():
    """List all available reports"""
    print("\n[FILES] AVAILABLE REPORTS")
    print("="*70)
    
    if not REPORTS_DIR.exists():
        print("Reports directory not found")
        return
    
    csv_files = sorted(REPORTS_DIR.glob("*.csv"))
    txt_files = sorted(REPORTS_DIR.glob("*.txt"))
    json_files = sorted(REPORTS_DIR.glob("*.json"))
    png_files = sorted(REPORTS_DIR.glob("*.png"))
    
    if csv_files:
        print("\n[CSV] CSV Files:")
        for f in csv_files:
            size_kb = f.stat().st_size / 1024
            print(f"  * {f.name} ({size_kb:.1f} KB)")
    
    if txt_files:
        print("\n[TXT] Reports:")
        for f in txt_files:
            print(f"  * {f.name}")
    
    if json_files:
        print("\n[JSON] Heuristics:")
        for f in json_files:
            print(f"  * {f.name}")
    
    if png_files:
        print("\n[PNG] Visualizations:")
        for f in png_files:
            print(f"  * {f.name}")
    
    if not (csv_files or txt_files or json_files or png_files):
        print("No reports found. Run a pipeline first.")


def show_help():
    """Show available workflows"""
    help_text = """
=================================================================================
           HEURISTIC ANALYSIS & TUNING PIPELINE - QUICK LAUNCHER
=================================================================================

WORKFLOWS:

  1. quick-test         Quick test with minimal games (2 before, 2 after)
                        TIME: ~5 minutes
                        
  2. focused           Focused tuning iteration (5 before, 5 after)
                        TIME: ~13 minutes
                        
  3. full              Full analysis with many games (10 before, 10 after)
                        TIME: ~20 minutes
                        
  4. baseline          Evaluate current heuristic (20 games, no tuning)
                        TIME: ~15 minutes

UTILITIES:

  5. analyze           Analyze and print latest results summary
  
  6. list              List all available reports
  
  7. visualize         Generate plots from latest results
  
  8. help              Show this message

EXAMPLES:

  python pipeline_launcher.py quick-test     # Start with quick test
  python pipeline_launcher.py focused        # Run focused tuning
  python pipeline_launcher.py analyze        # Check latest results
  python pipeline_launcher.py list           # See all reports
  
WORKFLOW SUGGESTIONS:

  For beginners:
    1. Run: python pipeline_launcher.py quick-test
    2. Review: python pipeline_launcher.py analyze
    3. Visualize: python pipeline_launcher.py visualize
    4. Iterate: python pipeline_launcher.py focused

  For optimization:
    1. Run: python pipeline_launcher.py full
    2. Analyze: python pipeline_launcher.py analyze
    3. Check reports/ for detailed CSV files
    4. Deploy best configuration
    
=================================================================================
"""
    print(help_text)


def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    commands = {
        "quick-test": workflow_quick_test,
        "quick": workflow_quick_test,
        "focused": workflow_focused_tuning,
        "focus": workflow_focused_tuning,
        "full": workflow_full_analysis,
        "baseline": workflow_baseline_only,
        "analyze": analyze_latest_results,
        "list": list_reports,
        "visualize": lambda: run_command([PYTHON_EXE, "visualize_results.py"], "Generating visualizations..."),
        "help": show_help,
        "-h": show_help,
        "--help": show_help,
    }
    
    if command in commands:
        try:
            commands[command]()
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        print("Run 'python pipeline_launcher.py help' for available commands")
        sys.exit(1)


if __name__ == "__main__":
    main()
