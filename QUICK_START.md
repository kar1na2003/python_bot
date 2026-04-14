"""
QUICK REFERENCE - Copy & Paste Commands
========================================
Copy these commands directly into your terminal for common tasks.

FASTEST START (Recommended for beginners):
"""

# python pipeline_launcher.py quick-test
# python pipeline_launcher.py analyze
# python pipeline_launcher.py visualize

"""
COMMON WORKFLOWS:

1. QUICK TEST (5 minutes) - Try it first!
   python pipeline_launcher.py quick-test

2. CHECK RESULTS
   python pipeline_launcher.py analyze

3. GENERATE PLOTS
   python pipeline_launcher.py visualize

4. LIST ALL REPORTS
   python pipeline_launcher.py list

5. RUN FULL ANALYSIS (20 minutes)
   python analyze_and_tune_pipeline.py --games-before 10 --games-after 10

6. EVALUATE CURRENT HEURISTIC (no tuning)
   python analyze_and_tune_pipeline.py --skip-tune --games-before 20

7. CUSTOM RUN
   python analyze_and_tune_pipeline.py --games-before 5 --games-after 5 --output-dir ./my_results

RESULTS FILES:
- reports/performance_*.csv         ← Win rates, game metrics
- reports/heuristic_weights_*.csv   ← Weight values
- reports/summary_report_*.txt      ← Human-readable summary
- reports/best_tuned_heuristic.json ← Best configuration found

VIEW CSV FILES:
- Open reports/*.csv in Excel, Google Sheets, or any text editor
- Or run: python -m http.server 8000 (then open http://localhost:8000/reports/)

NEXT STEPS AFTER RUNNING:
1. Run: python pipeline_launcher.py analyze
2. Review metrics in reports/ 
3. If improvement found:
   - Copy best_tuned_heuristic.json weights to config.py
   - Run more games to verify
   - Deploy to production

HELP:
python pipeline_launcher.py help          ← Show all workflows
python analyze_and_tune_pipeline.py -h    ← Show all options
python visualize_results.py -h            ← Show visualization options

EOF

# Embedded instructions below - these are just for reference

"""

╔════════════════════════════════════════════════════════════════════════════╗
║                     PIPELINE CHEAT SHEET                                   ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║ STEP 1: RUN PIPELINE                                                       ║
║ ────────────────────                                                       ║
║                                                                            ║
║   (EASIEST) Use Launcher:                                                  ║
║   $ python pipeline_launcher.py quick-test                                 ║
║                                                                            ║
║   (OR) Run Main Pipeline:                                                  ║
║   $ python analyze_and_tune_pipeline.py                                    ║
║                                                                            ║
║───────────────────────────────────────────────────────────────────────────║
║                                                                            ║
║ STEP 2: ANALYZE RESULTS                                                    ║
║ ────────────────────────                                                   ║
║                                                                            ║
║   $ python pipeline_launcher.py analyze                                    ║
║   or                                                                       ║
║   $ python analyzer_utils.py                                               ║
║                                                                            ║
║───────────────────────────────────────────────────────────────────────────║
║                                                                            ║
║ STEP 3: VISUALIZE RESULTS                                                  ║
║ ──────────────────────────                                                 ║
║                                                                            ║
║   $ python pipeline_launcher.py visualize                                  ║
║   $ python visualize_results.py                                            ║
║                                                                            ║
║───────────────────────────────────────────────────────────────────────────║
║                                                                            ║
║ STEP 4: REVIEW CSV FILES                                                   ║
║ ──────────────────────────                                                 ║
║                                                                            ║
║   Open files in reports/:                                                  ║
║   └─ performance_TIMESTAMP.csv      (Win rates, metrics)                    ║
║   └─ heuristic_weights_*.csv        (Weight values)                         ║
║   └─ before_after_comparison_*.csv  (Before/after comparison)               ║
║   └─ summary_report_*.txt           (Text summary)                          ║
║   └─ best_tuned_heuristic.json      (Best config)                           ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝

COMMON SCENARIOS:

📊 I want to quickly test the pipeline:
   $ python pipeline_launcher.py quick-test
   $ python pipeline_launcher.py analyze

⚡ I want to find the best heuristic (takes ~20 min):
   $ python pipeline_launcher.py full
   $ python pipeline_launcher.py analyze
   $ python pipeline_launcher.py visualize

🔄 I want to iteratively tune (run multiple times):
   $ python pipeline_launcher.py focused
   $ python pipeline_launcher.py analyze
   (repeat to iterate)

📈 I want detailed statistics:
   $ python analyzer_utils.py
   (or) $ python pipeline_launcher.py analyze

🎨 I want to see plots:
   $ python pipeline_launcher.py visualize
   (opens PNG files and HTML dashboard)

🔍 I want to understand what happened:
   $ cat reports/summary_report_*.txt
   (or) open reports/best_tuned_heuristic.json

COLOR OUTPUT MEANINGS:
✅ - Success, good result
⚠️  - Warning, investigate
❌ - Failed or bad result
📊 - Data/results
🎯 - Key finding
💾 - File saved
📈 - Chart/visualization
⏱️ - Time estimate

---
For detailed guide, see: PIPELINE_GUIDE.md
For direct Python API, see: analyze_and_tune_pipeline.py
"""
