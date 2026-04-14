# Weight Tuning Guide

This directory contains two automated scripts for optimizing Arena.AI bot heuristic weights through iterative testing and analysis.

## Scripts Overview

### 1. `tune_weights.py` - Basic Weight Tuning
**Purpose**: Runs multiple iterations of weight variations and keeps the best-performing set.

**Algorithm**:
- Random mutation of weights each iteration
- Tests 5 weight variants per iteration (configurable)
- 20 games per variant to measure win rate
- Keeps the best-performing weights
- Larger mutations for critical parameters: `kill_bonus`, `damage`, `threatened`, `focus_long_range`

**Usage**:
```bash
# Run 10 iterations (default), 20 games per variant, 5 variants per iteration
python tune_weights.py

# Run 100 iterations with 15 games per variant
python tune_weights.py --iterations 100 --games 15

# Run 20 iterations with 10 variants per iteration
python tune_weights.py --iterations 20 --variants 10
```

**Time Estimate**: 
- 10 iterations × 5 variants × 20 games = 1000 games total
- ~8-12 hours depending on game speed

**Output**:
- Live progress printed to console
- Best weights saved to `logs/tune_summary.json`
- Config.py automatically updated with best weights

---

### 2. `analyze_weights.py` - Advanced Analysis with Genetic Algorithm
**Purpose**: Performs sensitivity analysis and genetic algorithm optimization for faster convergence.

**Two Modes**:

#### Mode 1: Sensitivity Analysis
- Tests each weight individually (±30%, ±15%, baseline)
- Calculates correlation coefficient between weight changes and win rate
- Shows which weights have the highest impact on performance
- Identifies "critical" weights worth tuning more aggressively

```bash
python analyze_weights.py --mode sensitivity --games 20
```

#### Mode 2: Genetic Algorithm (GA)
- Creates initial population of 10 weight sets (default)
- Evaluates fitness (win rate) for each member
- Breeds best performers (top 50%)
- Mutates survivors to create new generation
- Faster convergence than random mutation

```bash
python analyze_weights.py --mode ga --iterations 20 --population 10
```

#### Mode 3: Both (Default)
- First: Identify critical weights via sensitivity
- Then: Evolve weights using GA

```bash
python analyze_weights.py  # Runs both by default
```

**Arguments**:
- `--mode` [sensitivity|ga|both] - Analysis type
- `--iterations` - GA generations or sensitivity tests (default: 20)
- `--population` - GA population size (default: 10)
- `--games` - Games per evaluation (default: 15)

**Time Estimate**:
- Sensitivity: 20 weights × 5 tests × 15 games = 1500 games (~12 hours)
- GA (20 gen × 10 pop): 200 evaluations × 15 games = 3000 games (~24 hours)

**Output**:
- Results saved to `logs/weight_analysis.json`
- Shows weight sensitivity scores
- GA history with generation-by-generation improvement
- Config.py updated with best GA weights

---

## Weight Tuning Strategy

### Quick Tuning (2-4 hours)
```bash
python tune_weights.py --iterations 5 --games 10 --variants 3
```
Fast exploration; may miss optimal combinations.

### Balanced Tuning (8-12 hours)
```bash
python tune_weights.py --iterations 10 --games 20
# OR
python analyze_weights.py --mode ga --iterations 15 --population 8 --games 12
```
Good balance of exploration and accuracy.

### Thorough Tuning (24-48 hours)
```bash
python tune_weights.py --iterations 20 --games 20 --variants 8
# Followed by:
python analyze_weights.py --mode sensitivity --games 20
```
Find critical weights, then refine with GA.

---

## Understanding Weight Impact

### Key Weights to Monitor

**High Impact** (even small changes matter):
- `kill_bonus`: Encourages finishing weakened opponents
- `damage`: Values aggressive play
- `threatened`: Penalizes suicidal moves
- `focus_long_range`: Prioritizes ranged unit threats

**Medium Impact**:
- `hp`: Unit survivability value
- `focus_short_range`: Melee threat priority
- `focus_fast`: Speed-based threat priority
- `alive_unit`: Maintaining team size

**Low Impact** (rarely affects decisions):
- `attack_option`: Number of available moves
- `progress`: Territory control
- `cluster`: Unit clustering preference

### Interpreting Sensitivity Analysis Output

```
Testing kill_bonus...
  Correlation: +0.892 | Avg impact: 8.5% (HIGH)
```

- **Correlation +0.892**: Increasing kill_bonus increases win rate by ~89% strength
- **Avg impact 8.5%**: Win rate changes by ~8.5% on average when this weight varies
- **HIGH**: This weight is critical; GA should mutate it more

---

## Example Workflow

### Session 1: Initial Tuning (4 hours)
```bash
python tune_weights.py --iterations 8 --games 15
# Result: Find baseline best weights, win rate improved to 62%
```

### Session 2: Identify Critical Weights (3 hours)
```bash
python analyze_weights.py --mode sensitivity --games 15
# Result: Find that kill_bonus, damage, threatened have highest correlation
```

### Session 3: Refine Critical Weights (6 hours)
```bash
python analyze_weights.py --mode ga --iterations 18 --population 12 --games 10
# Result: Fine-tune critical weights, reach 68% win rate target
```

---

## Monitoring Progress

Both scripts save intermediate results:
- `logs/tune_summary.json` - Latest tuning results
- `logs/weight_analysis.json` - Sensitivity and GA data

Check these files to see:
```json
{
  "best_winrate": 0.68,
  "best_weights": {
    "kill_bonus": 340.0,
    "damage": 35.2,
    ...
  }
}
```

---

## Stopping and Resuming

Scripts save progress frequently. If interrupted (Ctrl+C):
1. Current best weights are saved to `logs/`
2. Config.py is NOT automatically updated
3. Rerun script to continue optimization
4. To apply current best weights: Copy from logs file manually or rerun script to completion

---

## Tips for Best Results

1. **Run games with a stable server**: Ensure Arena.AI C# server is running stable before tuning
2. **Use consistent --games value**: Test same number of games for fair comparison (15-20 recommended)
3. **Monitor for overfitting**: If GA wins rate plateaus, sensitivity might be better for exploration
4. **Mix strategies**: Start with GA for speed, refine with sensitivity analysis for understanding
5. **Keep baseline**: Save config.py before tuning to revert if needed

---

## Troubleshooting

**"Error running games"**: 
- Ensure Arena.AI server is running (dotnet run --project Arena.AI)
- Check that main.py can execute successfully

**"Could not find HEURISTIC_WEIGHTS"**:
- Verify config.py syntax is correct
- All weights must be in the HEURISTIC_WEIGHTS dict

**Script hangs**:
- Set longer timeout in script (default 600s per game batch)
- May indicate server crash; restart and check game logs

**Win rate not improving**:
- Initial weights may be near-optimal
- Try different mutation rates: edit mutation_rate in tune_weights.py
- Increase games per variant for more stable measurements
