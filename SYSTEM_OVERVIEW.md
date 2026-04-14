"""
COMPLETE HEURISTIC ANALYSIS & TUNING SYSTEM
============================================
Summary of all scripts and how to use them.
"""

# ==============================================================================
# FILES CREATED
# ==============================================================================

FILES = {
    "MAIN PIPELINE": {
        "analyze_and_tune_pipeline.py": {
            "purpose": "Core pipeline that runs games, tunes heuristics, generates CSVs",
            "usage": "python analyze_and_tune_pipeline.py [options]",
            "key_features": [
                "Runs games with current heuristic",
                "Tunes by testing candidates",
                "Generates 3 types of CSV reports",
                "Saves best heuristic found",
            ],
            "options": [
                "--games-before N: games before tuning (default: 5)",
                "--games-after N: games after tuning (default: 5)",
                "--skip-tune: analyze only, no tuning",
                "--output-dir PATH: custom output directory",
            ],
        },
    },
    
    "QUICK LAUNCHERS": {
        "pipeline_launcher.py": {
            "purpose": "Easy command launcher for common workflows",
            "usage": "python pipeline_launcher.py [command]",
            "commands": [
                "quick-test: 5 min quick validation",
                "focused: 13 min focused tuning",
                "full: 20 min complete analysis",
                "baseline: 15 min evaluate current heuristic",
                "analyze: print latest results summary",
                "list: show all available reports",
                "visualize: generate plots from results",
                "help: show all available commands",
            ],
        },
        "quick_tune_test.py": {
            "purpose": "Simplified quick runner with minimal games",
            "usage": "python quick_tune_test.py [--games-before N] [--games-after N]",
        },
    },
    
    "ANALYSIS & VISUALIZATION": {
        "visualize_results.py": {
            "purpose": "Create plots and HTML dashboard from CSV results",
            "usage": "python visualize_results.py [options]",
            "generates": [
                "plot_performance.png: win rate trends",
                "plot_weights.png: weight changes over time",
                "dashboard.html: interactive summary",
            ],
            "options": [
                "--csv PATH: visualize specific CSV",
                "--reports-dir PATH: custom reports directory",
                "--type performance|weights|all: what to visualize",
            ],
        },
        "analyzer_utils.py": {
            "purpose": "Statistical analysis and comparison of results",
            "usage": "python analyzer_utils.py",
            "output": [
                "Win rate statistics (mean, median, range, std dev)",
                "Before/after comparison",
                "Best configuration identification",
                "Improvement assessment",
            ],
        },
    },
    
    "DOCUMENTATION": {
        "QUICK_START.md": {
            "purpose": "Copy-paste commands for fastest results",
            "contains": [
                "Most common commands",
                "Quick reference table",
                "Common scenarios with commands",
            ],
        },
        "PIPELINE_GUIDE.md": {
            "purpose": "Comprehensive guide with detailed explanations",
            "sections": [
                "Overview of the workflow",
                "Detailed script documentation",
                "CSV file format explanations",
                "Workflow examples",
                "Troubleshooting guide",
                "Integration steps",
            ],
        },
        "TUNING_CONFIG_GUIDE.md": {
            "purpose": "Configuration and customization guide",
            "contains": [
                "Search space templates (conservative/moderate/aggressive)",
                "Game count recommendations",
                "Weight selection guidelines",
                "Results interpretation guide",
                "Example workflows",
            ],
        },
    },
}

# ==============================================================================
# OUTPUT FILES (Generated After Running Pipeline)
# ==============================================================================

OUTPUT_FILES = {
    "CSV_REPORTS": {
        "performance_TIMESTAMP.csv": {
            "format": "CSV with header row",
            "columns": [
                "iteration, timestamp, label, games_run, wins, losses, win_rate, avg_moves, total_duration_sec"
            ],
            "use_case": "Track performance over iterations, plot win rate trends",
            "rows": "One per iteration (before + after candidates)",
        },
        "heuristic_weights_TIMESTAMP.csv": {
            "format": "CSV with all weight columns",
            "columns": [
                "iteration, timestamp, label, [all weight names]"
            ],
            "use_case": "See how weights changed during tuning, identify key levers",
            "rows": "One per iteration",
        },
        "before_after_comparison_TIMESTAMP.csv": {
            "format": "CSV with phase column",
            "columns": [
                "phase, iteration, label, games_run, wins, losses, win_rate, avg_moves"
            ],
            "use_case": "Direct comparison of before tuning vs after tuning phases",
            "rows": "All before rows then all after rows",
        },
    },
    
    "TEXT_REPORTS": {
        "summary_report_TIMESTAMP.txt": {
            "format": "Human-readable text",
            "contains": [
                "Best win rate before tuning",
                "Best win rate after tuning",
                "Best heuristic weights (all of them)",
                "Overall improvement percentage",
                "Total games played",
            ],
            "use_case": "Quick review of overall results",
        },
    },
    
    "CONFIGS": {
        "best_tuned_heuristic.json": {
            "format": "JSON configuration file",
            "contains": [
                "weights object: all tuned weight values",
                "unit_type_multipliers object: multiplier values",
            ],
            "use_case": "Deploy best configuration to bot",
            "how_to_use": "Copy weights into config.py HEURISTIC_WEIGHTS",
        },
    },
    
    "PLOTS": {
        "plot_performance.png": {
            "content": "Two subplots showing win rate trend and games per iteration",
            "use_case": "Visual representation of performance improvements",
        },
        "plot_weights.png": {
            "content": "Multiple subplots for top 6 varying weights",
            "use_case": "See which weights changed most during tuning",
        },
        "dashboard.html": {
            "content": "Interactive HTML dashboard",
            "use_case": "Summary with links to all reports",
            "view_with": "Open in web browser",
        },
    },
}

# ==============================================================================
# QUICK START - 3 COMMANDS
# ==============================================================================

QUICK_START_3_STEPS = """
Step 1: Run pipeline (5-20 minutes)
$ python pipeline_launcher.py quick-test

Step 2: Check results (instant)
$ python pipeline_launcher.py analyze

Step 3: Visualize (instant)
$ python pipeline_launcher.py visualize

✅ Done! Check reports/ directory for CSV files and charts
"""

# ==============================================================================
# COMMON USAGE PATTERNS
# ==============================================================================

USAGE_PATTERNS = {
    "first_time": [
        "python pipeline_launcher.py quick-test",
        "python pipeline_launcher.py analyze",
        "python pipeline_launcher.py visualize",
        "→ Opens reports/ in file manager to explore",
    ],
    
    "full_analysis": [
        "python pipeline_launcher.py full",
        "python pipeline_launcher.py analyze",
        "python analyzer_utils.py",
        "→ Check reports/ for all data",
        "→ Review best_tuned_heuristic.json",
    ],
    
    "iterative_tuning": [
        "python pipeline_launcher.py focused",
        "python pipeline_launcher.py analyze",
        "# If good, keep weights and run again",
        "# If bad, try different search space",
        "(repeat 3-5 times)",
    ],
    
    "baseline_only": [
        "python analyze_and_tune_pipeline.py --skip-tune --games-before 20",
        "python analyzer_utils.py",
        "→ Establish current performance baseline",
    ],
    
    "custom": [
        "python analyze_and_tune_pipeline.py --games-before 7 --games-after 7 --output-dir ./my_results",
        "→ For custom game counts and output location",
    ],
}

# ==============================================================================
# WORKFLOW DURATIONS
# ==============================================================================

DURATIONS = {
    "quick-test": {
        "total_time": "~5 minutes",
        "games_total": 4,
        "best_for": "Validation, learning workflow",
    },
    "focused": {
        "total_time": "~13 minutes",
        "games_total": 170,  # 5 before + ~165 after (27 candidates × 5 each)
        "best_for": "Iterative improvement",
    },
    "full": {
        "total_time": "~20 minutes",
        "games_total": 340,  # 10 before + ~330 after
        "best_for": "Comprehensive analysis",
    },
    "baseline": {
        "total_time": "~15 minutes",
        "games_total": 20,
        "best_for": "Establish current performance",
    },
    "thorough": {
        "total_time": "~40 minutes",
        "games_total": 680,  # 20 before + ~660 after
        "best_for": "High-confidence results",
    },
}

# ==============================================================================
# INTERPRETATION QUICK GUIDE
# ==============================================================================

INTERPRETATION = """
READING YOUR RESULTS:

✅ GOOD SIGNS:
   • Win rate improved 5%+ after tuning
   • Before: 45% → After: 50%+ (5% improvement) = SIGNIFICANT
   • Low variation between runs (std dev < 5%)
   • Weight changes make logical sense

⚠️  INVESTIGATE:
   • Win rate barely changed (±2%)
   → Run more games to confirm if real or random
   • High variation (std dev > 10%)
   → Results are unstable, need more games
   • Large random-looking weight changes
   → Try different search space

❌ PROBLEMS:
   • Win rate decreased
   → Keep current heuristic, try different tuning approach
   • All weights changed drastically
   → Search space too wide, use narrower ranges
   • No patterns visible
   → May need to tune different weights

CONFIDENCE LEVELS:
   2-5 games:   Low confidence, directional only
   10-20 games: Medium confidence, reasonable to trust
   20-50 games: High confidence, very reliable
   50+ games:   Very high confidence, final validation
"""

# ==============================================================================
# FILE ORGANIZATION IN reports/
# ==============================================================================

REPORTS_DIRECTORY = """
reports/
├── performance_20260415_100000.csv              (Primary results metric)
├── heuristic_weights_20260415_100000.csv        (Weight details)
├── before_after_comparison_20260415_100000.csv  (Direct comparison)
│
├── summary_report_20260415_100000.txt           (Human-readable summary)
├── best_tuned_heuristic.json                    (Best config - Deploy this)
│
├── plot_performance.png                         (Generated by visualize_results.py)
├── plot_weights.png                             (Generated by visualize_results.py)
└── dashboard.html                               (Generated by visualize_results.py)

HOW TO USE EACH FILE:
- Open *.csv files in Excel, Google Sheets, Python, or any spreadsheet app
- Open *.txt files in any text editor
- Open *.json files to review weights
- Open *.html in web browser for summary
- View *.png files to see performance/weight trends
"""

# ==============================================================================
# NEXT STEPS AFTER RUNNING
# ==============================================================================

NEXT_STEPS = """
AFTER RUNNING THE PIPELINE:

1. REVIEW SUMMARY (30 seconds)
   $ python pipeline_launcher.py analyze
   → Read the improvement percentage

2. EXAMINE CSV FILES (5 minutes)
   Open reports/performance_*.csv in Excel
   → Look at win_rate column
   → Check if before < after

3. VIEW PLOTS (1 minute)
   $ python pipeline_launcher.py visualize
   → Open plot_performance.png
   → Look for upward trend after "Tuning Start" line

4. DECIDE ON DEPLOYMENT:
   
   IF improvement > 5%:
   ✅ DEPLOY
   • Copy weights from best_tuned_heuristic.json
   • Update config.py HEURISTIC_WEIGHTS
   • Run validation (play 20+ games)
   • Deploy to production
   
   IF improvement 0-5%:
   ⚠️  INVESTIGATE
   • Run more games (increase --games-before/after to 10)
   • Try different search space (TUNING_CONFIG_GUIDE.md)
   • Run another iteration
   
   IF improvement < 0%:
   ❌ SKIP
   • Keep current heuristic
   • Try different tuning weights
   • Review TUNING_CONFIG_GUIDE.md for ideas

5. TRACK PROGRESS (Recommended)
   • Save best_tuned_heuristic.json with version number
   • Re-run pipeline periodically
   • Compare results across versions
"""

# ==============================================================================
# TROUBLESHOOTING
# ==============================================================================

TROUBLESHOOTING = """
PROBLEM: Games are taking too long

SOLUTION:
   • Reduce games: --games-before 2 --games-after 2
   • Or use: python pipeline_launcher.py quick-test

---

PROBLEM: Memory errors or "out of memory"

SOLUTION:
   • Reduce candidate configurations being tested
   • Edit SEARCH_SPACE in analyze_and_tune_pipeline.py
   • Use SEARCH_SPACE_CONSERVATIVE template

---

PROBLEM: CSV files are empty or have no data

SOLUTION:
   • Check that main.py works: python main.py --games 1
   • Check logs/ directory for errors
   • Verify game server is running

---

PROBLEM: Can't import matplotlib (for visualizations)

SOLUTION:
   • Optional: pip install matplotlib
   • Pipeline works fine without it
   • Skip visualization step if needed

---

PROBLEM: Not seeing performance improvement

SOLUTION:
   • Run more games (increase --games-before/after)
   • Tune different weights (see TUNING_CONFIG_GUIDE.md)
   • Try different search space ranges
   • Run 2-3 iterations to find pattern

---

PROBLEM: Results are inconsistent/random

SOLUTION:
   • Increase games per phase (harder to get lucky)
   • Check for other system processes using CPU
   • Review std_win_rate in analyzer output (should be < 5%)
"""

if __name__ == "__main__":
    print(__doc__)
    print("\nFor detailed usage, see:")
    print("  - QUICK_START.md (fastest)")
    print("  - PIPELINE_GUIDE.md (comprehensive)")  
    print("  - TUNING_CONFIG_GUIDE.md (customization)")
