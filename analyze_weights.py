"""
Advanced weight analysis - detects correlations between individual weight values and win rates
Uses genetic algorithm-style selection for faster convergence
"""
import json
import subprocess
import sys
import time
from pathlib import Path
from copy import deepcopy
import numpy as np
from collections import defaultdict

CONFIG_PATH = Path(__file__).parent / "config.py"
RESULTS_LOG = Path(__file__).parent / "logs" / "weight_analysis.json"

def update_config_weights(weights_dict):
    """Update the config.py file with new weights"""
    config_content = CONFIG_PATH.read_text()
    
    weights_str = "HEURISTIC_WEIGHTS = {\n"
    for key, val in weights_dict.items():
        weights_str += f'    "{key}": {val},\n'
    weights_str += "}\n"
    
    import re
    pattern = r'HEURISTIC_WEIGHTS = \{[^}]+\}'
    config_content = re.sub(pattern, weights_str.rstrip('\n'), config_content, flags=re.DOTALL)
    
    CONFIG_PATH.write_text(config_content)

def run_games(num_games: int = 20) -> dict:
    """Run N games and extract results"""
    print(f"  Running {num_games} games...", end="", flush=True)
    
    cmd = [sys.executable, "main.py", str(num_games), "--quiet-actions"]
    result = subprocess.run(
        cmd,
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True,
        timeout=600
    )
    
    output = result.stdout + result.stderr
    wins = output.count("Result: WIN")
    losses = output.count("Result: LOSS")
    draws = output.count("Result: DRAW")
    
    winrate = wins / (wins + losses + draws) if (wins + losses + draws) > 0 else 0.0
    print(f" {wins}W-{losses}L-{draws}D = {winrate:.0%}")
    
    return {"wins": wins, "losses": losses, "draws": draws, "winrate": winrate}

def single_weight_sensitivity(base_weights: dict, games: int = 20) -> dict:
    """Test how sensitive win rate is to changes in each individual weight"""
    print("\nPerforming single-weight sensitivity analysis...")
    print("=" * 70)
    
    sensitivity = defaultdict(list)
    baseline_results = run_games(games)
    baseline_winrate = baseline_results["winrate"]
    
    print(f"Baseline win rate: {baseline_winrate:.1%}\n")
    
    for weight_key in sorted(base_weights.keys()):
        print(f"Testing {weight_key}...")
        
        original_val = base_weights[weight_key]
        test_values = [
            original_val * 0.7,
            original_val * 0.85,
            original_val,
            original_val * 1.15,
            original_val * 1.3,
        ]
        
        for test_val in test_values:
            variant = deepcopy(base_weights)
            variant[weight_key] = test_val
            
            update_config_weights(variant)
            results = run_games(games)
            
            delta = results["winrate"] - baseline_winrate
            sensitivity[weight_key].append({
                "value": test_val,
                "relative": test_val / original_val,
                "winrate": results["winrate"],
                "delta": delta
            })
            
            time.sleep(0.5)
        
        # Calculate correlation coefficient for this weight
        values = [s["relative"] for s in sensitivity[weight_key]]
        deltas = [s["delta"] for s in sensitivity[weight_key]]
        
        if len(values) > 1:
            correlation = np.corrcoef(values, deltas)[0, 1]
            avg_delta = np.mean(np.abs(deltas))
            sensitivity[weight_key].append({
                "correlation": correlation,
                "avg_impact": avg_delta
            })
            
            impact_level = "HIGH" if avg_delta > 0.05 else "MEDIUM" if avg_delta > 0.02 else "LOW"
            print(f"  Correlation: {correlation:+.3f} | Avg impact: {avg_delta:.1%} ({impact_level})\n")
    
    return sensitivity

def genetic_algorithm_tune(base_weights: dict, iterations: int = 20, population: int = 10, games: int = 15):
    """Use genetic algorithm to evolve weights toward better win rate"""
    print("\nStarting genetic algorithm optimization...")
    print("=" * 70)
    
    # Initialize population
    population_members = []
    for i in range(population):
        if i == 0:
            member = deepcopy(base_weights)
        else:
            member = deepcopy(base_weights)
            for key in member:
                member[key] *= np.random.uniform(0.8, 1.2)
        population_members.append({"weights": member, "winrate": 0})
    
    history = []
    best_overall = {"weights": base_weights, "winrate": 0}
    
    for gen in range(iterations):
        print(f"\n[GENERATION {gen + 1}/{iterations}] Evaluating population...")
        
        # Evaluate population
        for idx, member in enumerate(population_members):
            print(f"  Individual {idx + 1}/{population}: ", end="")
            update_config_weights(member["weights"])
            results = run_games(games)
            member["winrate"] = results["winrate"]
            
            if member["winrate"] > best_overall["winrate"]:
                best_overall = deepcopy(member)
                print(f" {member['winrate']:.0%} ✓ NEW BEST")
            else:
                print(f" {member['winrate']:.0%}")
            
            time.sleep(0.5)
        
        # Sort by winrate
        population_members.sort(key=lambda x: x["winrate"], reverse=True)
        
        print(f"\nGeneration {gen + 1} Top 3:")
        for i in range(min(3, len(population_members))):
            print(f"  #{i+1}: {population_members[i]['winrate']:.0%}")
        
        # Breeding - keep top 50%, mutate to create new
        survivors = population_members[:population // 2]
        new_members = []
        
        while len(survivors) + len(new_members) < population:
            parent = survivors[np.random.randint(0, len(survivors))]
            child = deepcopy(parent)
            
            # Mutate child
            for key in child["weights"]:
                if np.random.random() < 0.3:
                    mutation = np.random.uniform(0.9, 1.1)
                    child["weights"][key] = max(0.1, child["weights"][key] * mutation)
            
            new_members.append(child)
        
        population_members = survivors + new_members[:population - len(survivors)]
        
        history.append({
            "generation": gen + 1,
            "best_winrate": best_overall["winrate"],
            "population_avg": np.mean([m["winrate"] for m in population_members])
        })
        
        print(f"Best so far: {best_overall['winrate']:.0%}")
    
    return best_overall, history

def load_current_weights() -> dict:
    """Load current weights from config.py"""
    config_content = CONFIG_PATH.read_text()
    
    import re
    match = re.search(r'HEURISTIC_WEIGHTS = \{([^}]+)\}', config_content, re.DOTALL)
    if not match:
        print("Error: Could not find HEURISTIC_WEIGHTS in config.py")
        return {}
    
    weights_text = match.group(1)
    weights = {}
    
    for line in weights_text.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            match = re.match(r'"([^"]+)":\s*([\d.]+)', line)
            if match:
                weights[match.group(1)] = float(match.group(2))
    
    return weights

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze weight correlations and optimize using GA")
    parser.add_argument("--mode", choices=["sensitivity", "ga", "both"], default="both",
                        help="Analysis mode: sensitivity analysis, genetic algorithm, or both")
    parser.add_argument("--iterations", type=int, default=20, help="Iterations/generations")
    parser.add_argument("--population", type=int, default=10, help="Population size for GA")
    parser.add_argument("--games", type=int, default=15, help="Games per evaluation")
    args = parser.parse_args()
    
    try:
        # Load current weights
        current_weights = load_current_weights()
        if not current_weights:
            print("Could not load weights from config")
            sys.exit(1)
        
        print(f"Loaded {len(current_weights)} weights from config")
        
        results = {}
        
        if args.mode in ["sensitivity", "both"]:
            results["sensitivity"] = single_weight_sensitivity(current_weights, args.games)
        
        if args.mode in ["ga", "both"]:
            best_member, ga_history = genetic_algorithm_tune(
                current_weights,
                iterations=args.iterations,
                population=args.population,
                games=args.games
            )
            
            results["ga"] = {
                "best_weights": best_member["weights"],
                "best_winrate": best_member["winrate"],
                "history": ga_history
            }
            
            # Update config with best weights
            update_config_weights(best_member["weights"])
            print(f"\nConfig updated with GA best weights (win rate: {best_member['winrate']:.0%})")
        
        # Save results
        RESULTS_LOG.parent.mkdir(exist_ok=True)
        with open(RESULTS_LOG, "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nResults saved to {RESULTS_LOG}")
        
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
