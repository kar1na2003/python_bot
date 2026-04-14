# Heuristic Analysis and Tuning Pipeline

Complete workflow to analyze your bot's current heuristic, tune it for better performance, and generate CSV reports with visualizations.

## Overview

This pipeline performs the following steps:

1. **Analysis Phase**: Run games with your current heuristic and measure baseline performance
2. **Tuning Phase**: Test multiple heuristic configurations (grid search) to find improvements
3. **Reporting Phase**: Generate CSV files with performance metrics and weight changes
4. **Visualization Phase** (Optional): Create plots and an HTML dashboard

## Scripts

### 1. `analyze_and_tune_pipeline.py` - Main Pipeline

The core script that orchestrates the entire workflow.

**Usage:**

```bash
# Full pipeline with 5 games before tuning and 5 after
python analyze_and_tune_pipeline.py

# Quick test with 2 games before and 2 games after
python analyze_and_tune_pipeline.py --games-before 2 --games-after 2

# Skip tuning, just analyze current heuristic
python analyze_and_tune_pipeline.py --skip-tune --games-before 10

# Custom output directory
python analyze_and_tune_pipeline.py --output-dir ./my_reports
```

**Arguments:**

- `--games-before` (int, default: 5) - Number of games to run before tuning
- `--games-after` (int, default: 5) - Number of games to run after tuning (per candidate)
- `--skip-tune` - Skip the tuning phase, only analyze current heuristic
- `--output-dir` (path) - Directory for output CSV and report files

**Output Files:**

- `performance_TIMESTAMP.csv` - Win rates, game metrics over iterations
- `heuristic_weights_TIMESTAMP.csv` - Weight values for each heuristic component
- `before_after_comparison_TIMESTAMP.csv` - Side-by-side comparison of before/after phases
- `summary_report_TIMESTAMP.txt` - Human-readable summary with key metrics
- `best_tuned_heuristic.json` - Best heuristic configuration found

### 2. `visualize_results.py` - Visualization Tool

Creates plots and dashboards from the CSV results.

**Usage:**

```bash
# Visualize latest results in reports/ directory
python visualize_results.py

# Visualize specific CSV file
python visualize_results.py --csv reports/performance_20260415_120000.csv

# Generate only performance plots
python visualize_results.py --type performance

# Use custom reports directory
python visualize_results.py --reports-dir ./my_reports
```

**Arguments:**

- `--csv` (path) - Specific CSV file to visualize
- `--reports-dir` (path, default: reports/) - Directory containing CSV files
- `--type` (performance/weights/all, default: all) - Type of visualization

**Output:**

- `plot_performance.png` - Win rate trends over iterations
- `plot_weights.png` - Heuristic weight changes over iterations
- `dashboard.html` - Basic HTML dashboard summarizing results

### 3. `quick_tune_test.py` - Quick Test Version

Lightweight version for quick testing with fewer games.

**Usage:**

```bash
# Default: 2 games before, 2 after
python quick_tune_test.py

# Custom game counts
python quick_tune_test.py --games-before 3 --games-after 3
```

## Workflow Examples

### Example 1: Complete Analysis (Recommended)

```bash
# 1. Run the full pipeline (10-15 minutes depending on game duration)
python analyze_and_tune_pipeline.py --games-before 5 --games-after 5

# 2. Visualize results
python visualize_results.py

# 3. Review the CSV files in reports/ directory
# 4. Check summary_report_TIMESTAMP.txt for key insights
```

### Example 2: Quick Testing

```bash
# Test pipeline quickly with minimal games
python quick_tune_test.py

# Review results
python visualize_results.py
```

### Example 3: Analyze Only (No Tuning)

```bash
# Run 20 games with current heuristic, no tuning
python analyze_and_tune_pipeline.py --skip-tune --games-before 20

# Useful for: establishing baseline, stability testing
```

### Example 4: Focused Tuning

```bash
# Run just 3 games per phase to find promising direction quickly
python analyze_and_tune_pipeline.py --games-before 3 --games-after 3

# Review results
python visualize_results.py

# If promising, run again with more games:
python analyze_and_tune_pipeline.py --games-before 10 --games-after 10
```

## CSV Output Files Explained

### `performance_*.csv`

Metrics for each iteration of the pipeline:

| Column | Description |
|--------|-------------|
| iteration | Sequential iteration number |
| timestamp | When the game(s) were run |
| label | Phase identifier (e.g., current_iteration_1, tuned_candidate_5) |
| games_run | Number of games played |
| wins | Number of games won |
| losses | Number of games lost |
| win_rate | Win percentage (0.0-1.0) |
| avg_moves | Average number of moves per game |
| total_duration_sec | Total time spent playing |

### `heuristic_weights_*.csv`

Records all heuristic weight values per iteration:

| Column | Description |
|--------|-------------|
| iteration | Iteration number |
| timestamp | When tested |
| label | Phase identifier |
| [weight_name] | Value of each weight parameter |

**Example weight columns:**
- alive_unit, hp, attack_option, mobility
- center_control, progress, cluster, focus_long_range
- damage, kill_bonus, exposed_ranged, threatened

### `before_after_comparison_*.csv`

Direct comparison of performance before and after tuning:

| Column | Description |
|--------|-------------|
| phase | Either "BEFORE_TUNING" or "AFTER_TUNING" |
| iteration | Iteration within that phase |
| label | Configuration identifier |
| games_run, wins, losses | Game outcomes |
| win_rate | Success percentage |
| avg_moves | Average game length |

### `summary_report_*.txt`

Human-readable summary including:
- Best win rate achieved before tuning
- Best win rate achieved after tuning
- Winning heuristic weights
- Overall improvement percentage
- Total games played

## Understanding Results

### Key Metrics

1. **Win Rate**: Primary metric for heuristic quality
   - Improvement of 5-10% is significant
   - Improvement of 10%+ is excellent

2. **Weight Changes**: Shows how weights were adjusted
   - Large changes indicate important optimization factors
   - Small changes may indicate already-optimal values

3. **Average Moves**: Game length
   - Shorter games aren't always better (could be losing quickly)
   - Consider in context with win rate

### Interpretation Guide

**Good tuning results:**
- ✅ Win rate improved 5%+ after tuning
- ✅ Weight changes are logical (e.g., kill_bonus increased)
- ✅ Improvement is consistent across multiple runs

**Inconclusive results:**
- ⚠️ Win rate barely changed (±2%)
- ⚠️ Large variance between runs
- → Run more games (increase --games-before/after)

**Bad tuning results:**
- ❌ Win rate decreased significantly
- ❌ Erratic changes in metrics
- → Review weight search space in analyze_and_tune_pipeline.py

## Customizing the Tuning Search Space

To change which weights are tuned, edit `analyze_and_tune_pipeline.py`:

```python
def build_candidate_configs(base: HeuristicConfig, search_space: Dict = None):
    if search_space is None:
        search_space = {
            "kill_bonus": [160.0, 220.0, 280.0],      # Current ± range
            "damage": [18.0, 24.0, 30.0],
            # Add or modify weights here
        }
```

**Tips:**
- 3 values per weight = 3^N candidates (grows exponentially)
- Start with fewer, wider-ranged options
- Refine search space based on previous results

## Troubleshooting

### Games are taking too long
**Solution:** Reduce `--games-before` and `--games-after` to 2-3 for quick testing

### Out of memory errors
**Solution:** 
- Reduce number of games
- Reduce number of candidate configurations
- Close other applications

### CSV files are empty
**Solution:**
- Check that main.py runs successfully: `python main.py --games 1`
- Verify heuristic configuration is valid
- Check logs/ directory for error messages

### Matplotlib import error
**Solution:** Install visualization dependencies:
```bash
pip install matplotlib
```
(Optional, but needed for visualizations)

## Performance Tips

1. **Iterate gradually**: 
   - Start with 2-3 games per phase for direction finding
   - Once promising area found, increase to 10+ games

2. **Parallel runs not supported**:
   - Pipeline runs sequentially
   - Can run multiple instances with `--output-dir` to track separately

3. **Game simulation time**:
   - Games take time based on MCTS iterations and simulation depth
   - Check config.py for MCTS_ITERATIONS
   - Reduce for faster iterations, increase for better search

## Example Output

After running the pipeline, your reports/ directory will contain:

```
reports/
  ├── performance_20260415_100000.csv          # 10 rows, 8 columns
  ├── heuristic_weights_20260415_100000.csv    # 10 rows, 13+ columns
  ├── before_after_comparison_20260415_100000.csv
  ├── summary_report_20260415_100000.txt        # Human-readable summary
  ├── best_tuned_heuristic.json                 # Best config found
  ├── plot_performance.png                      # (If visualize_results.py run)
  ├── plot_weights.png                          # (If visualize_results.py run)
  └── dashboard.html                            # (If visualize_results.py run)
```

## Integration

Once you've found good heuristics:

1. **Review** `best_tuned_heuristic.json`
2. **Copy** the weights to `config.py` or save as new profile
3. **Validate** with more games if needed
4. **Deploy** to your bot

## Next Steps

1. Run: `python analyze_and_tune_pipeline.py`
2. Review results in reports/ directory
3. Generate plots: `python visualize_results.py`
4. Iterate based on findings
5. Deploy best configuration

---

**For questions or bugs**, check the script comments or run with `-h` flag for help.
