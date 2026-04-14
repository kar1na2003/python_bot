"""
Configuration templates and customization guide for the heuristic tuning pipeline.
Modify these settings to control how the tuning works.
"""

# ============================================================================
# TUNING SEARCH SPACE CONFIGURATION
# ============================================================================
# Edit analyze_and_tune_pipeline.py, function: build_candidate_configs()
# Change the search_space dictionary to customize which weights are tuned

# CONSERVATIVE (narrow search, fewer candidates):
SEARCH_SPACE_CONSERVATIVE = {
    "kill_bonus": [200.0, 220.0, 240.0],      # 3 values
    "damage": [22.0, 24.0, 26.0],
    "focus_long_range": [35.0, 40.0, 45.0],
}
# Total candidates: 3 × 3 × 3 = 27 candidates

# MODERATE (balanced search):
SEARCH_SPACE_MODERATE = {
    "kill_bonus": [160.0, 220.0, 280.0],      # 3 values
    "damage": [18.0, 24.0, 30.0],
    "focus_long_range": [25.0, 40.0, 60.0],
    "exposed_ranged": [-12.0, -22.0, -32.0],
}
# Total candidates: 3 × 3 × 3 × 3 = 81 candidates

# AGGRESSIVE (wide search, many candidates - takes longer):
SEARCH_SPACE_AGGRESSIVE = {
    "kill_bonus": [140.0, 180.0, 220.0, 260.0, 300.0],      # 5 values
    "damage": [15.0, 20.0, 24.0, 30.0, 35.0],
    "focus_long_range": [20.0, 35.0, 50.0, 70.0],
    "exposed_ranged": [-10.0, -18.0, -28.0],
    "threatened": [-8.0, -16.0, -24.0],
}
# Total candidates: 5 × 5 × 4 × 3 × 3 = 900 candidates ⚠️ Very slow!

# ============================================================================
# USAGE EXAMPLE
# ============================================================================
# To use conservative search space, modify analyze_and_tune_pipeline.py:
#
# Line ~150, change:
#     candidates = tuner.build_candidate_configs(best_before)
# To:
#     candidates = tuner.build_candidate_configs(best_before, SEARCH_SPACE_CONSERVATIVE)

# ============================================================================
# GAME COUNT RECOMMENDATIONS
# ============================================================================

GAME_COUNTS = {
    "quick_test": {
        "before": 2,
        "after": 2,
        "duration": "~5 min",
        "purpose": "Quick validation that pipeline works",
        "command": "python pipeline_launcher.py quick-test",
    },
    "focused": {
        "before": 5,
        "after": 5,
        "duration": "~13 min",
        "purpose": "Fast iterative tuning",
        "command": "python pipeline_launcher.py focused",
    },
    "standard": {
        "before": 10,
        "after": 10,
        "duration": "~20 min",
        "purpose": "Balanced search and validation",
        "command": "python analyze_and_tune_pipeline.py",
    },
    "thorough": {
        "before": 20,
        "after": 20,
        "duration": "~40 min",
        "purpose": "High confidence in results",
        "command": "python analyze_and_tune_pipeline.py --games-before 20 --games-after 20",
    },
    "baseline_only": {
        "before": 20,
        "after": 0,
        "duration": "~15 min",
        "purpose": "Establish baseline performance",
        "command": "python analyze_and_tune_pipeline.py --skip-tune --games-before 20",
    },
}

# ============================================================================
# WEIGHT SELECTION GUIDE
# ============================================================================
# Which weights to tune depends on your goals:

WEIGHT_SELECTION = {
    "offense_focused": {
        "weights": ["kill_bonus", "damage", "attack_option"],
        "reason": "Improve ability to eliminate opponent units",
    },
    "defense_focused": {
        "weights": ["hp", "threatened", "exposed_ranged"],
        "reason": "Improve unit safety and positioning",
    },
    "positioning_focused": {
        "weights": ["center_control", "cluster", "progress"],
        "reason": "Improve tactical positioning",
    },
    "resource_efficiency": {
        "weights": ["mobility", "center_control", "focus_long_range"],
        "reason": "Improve resource and area control",
    },
    "all_around": {
        "weights": [
            "alive_unit", "hp", "attack_option", "mobility",
            "center_control", "progress", "cluster", "focus_long_range",
            "damage", "kill_bonus", "exposed_ranged", "threatened",
        ],
        "reason": "Comprehensive tuning across all factors",
    },
}

# ============================================================================
# RESULTS INTERPRETATION GUIDE
# ============================================================================

INTERPRETATION = """
HOW TO READ THE RESULTS:

1. Win Rate (Most Important)
   - > 50%:  Good
   - > 55%:  Very good
   - > 60%:  Excellent
   - Improvement of 5%+: Significant

2. Standard Deviation (Consistency)
   - < 5%:   Consistent (good)
   - 5-10%:  Variable (ok)
   - > 10%:  Highly variable (unreliable)

3. Best vs Average
   - If best >> average:  Results are inconsistent, run more games
   - If best ≈ average:   Results are stable, trust them

4. Weight Changes
   - Small changes (< 5%):  Already optimal in that area
   - Large changes (> 20%):  Major improvement opportunity
   - Opposite direction:     Try different search space

WHAT TO DO WITH RESULTS:

If improvement > 5%:
   ✅ Deploy new heuristic
   ✅ Save weights from best_tuned_heuristic.json
   ✅ Run validation on more games

If improvement 0-5%:
   ⚠️  Inconclusive - run more games
   ⚠️  Try different search space
   ⚠️  Check for variability (std dev)

If improvement < 0%:
   ❌ Don't deploy
   ❌ Keep current heuristic
   ❌ Try different tuning parameters
"""

# ============================================================================
# OPTIMIZATION TIPS
# ============================================================================

OPTIMIZATION_TIPS = """
TIPS FOR BETTER RESULTS:

1. Start Conservative
   - Use fewer weights and narrower ranges
   - Once you understand the space, expand

2. Iterate Multiple Times
   - First iteration finds general direction
   - Second iteration refines that direction
   - Third+ iteration validates and fine-tunes

3. Use Baseline Only for Initial Testing
   --skip-tune --games-before 20
   - Understand current performance first
   - Compare against this baseline

4. Watch for Plateau
   - If win rate doesn't improve after 2-3 iterations
   - Try different weights in search space

5. Combine Insights
   - Review which weights changed most
   - Those are your high-leverage parameters
   - Focus next round on those

6. Validate Results
   - Good result with 5 games? Run 20 to confirm
   - Bad result with 20 games? May be real

7. Track Long-Term
   - Keep best_tuned_heuristic.json files
   - Track version history
   - Compare across multiple tuning rounds
"""

# ============================================================================
# EXAMPLE: Quick Workflow
# ============================================================================

EXAMPLE_WORKFLOW = """
RECOMMENDED WORKFLOW FOR FIRST-TIME USERS:

Day 1 - Discovery (20 minutes):
$ python pipeline_launcher.py quick-test     # See if it works
$ python pipeline_launcher.py analyze        # Check results
$ python pipeline_launcher.py visualize      # View plots

Day 2 - Validation (20 minutes):
$ python pipeline_launcher.py focused        # Run proper tuning
$ python pipeline_launcher.py analyze        # Check if improved
$ python pipeline_launcher.py list           # Review all files

Day 3 - Deep Dive (30 minutes):
$ python analyze_and_tune_pipeline.py --games-before 10 --games-after 10
$ python analyzer_utils.py                   # Detailed statistics
$ python pipeline_launcher.py visualize      # Generate plots
(Review reports/ directory thoroughly)

Day 4+ - Iteration (varies):
Based on findings, either:
- Keep running focused iterations if improving
- Adjust search space and run full analysis
- Deploy if satisfied with results
"""

if __name__ == "__main__":
    print(__doc__)
    print("\nFor more information, see PIPELINE_GUIDE.md")
