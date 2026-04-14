"""
Fine-tune weights around current best configuration using gradual local search
Focuses on small mutations (±5-15%) around proven good weights
"""
import json
import subprocess
import sys
import time
from pathlib import Path
from copy import deepcopy
import numpy as np

CONFIG_PATH = Path(__file__).parent / "config.py"
RESULTS_LOG = Path(__file__).parent / "logs" / "refine_results.json"

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

def hill_climbing_refine(base_weights: dict, iterations: int = 20, games: int = 20, mutation_rate: float = 0.15):
    """Hill climbing: test small mutations, keep improving ones"""
    print("\nStarting hill climbing refinement...")
    print("=" * 70)
    
    current_best = deepcopy(base_weights)
    best_winrate = 0.0
    history = []
    
    # Test baseline first
    print(f"\n[BASELINE] Testing current weights...")
    update_config_weights(current_best)
    baseline_results = run_games(games)
    best_winrate = baseline_results["winrate"]
    print(f"Baseline win rate: {best_winrate:.1%}\n")
    
    for iteration in range(iterations):
        print(f"[ITERATION {iteration + 1}/{iterations}] Current best: {best_winrate:.1%}")
        
        # Generate neighbors (small mutations)
        neighbors = []
        for key in current_best.keys():
            for direction in [-1, +1]:
                neighbor = deepcopy(current_best)
                mutation = 1.0 + (direction * mutation_rate / 2)
                neighbor[key] = max(0.1, neighbor[key] * mutation)
                neighbors.append({"weights": neighbor, "key": key, "direction": direction})
        
        print(f"Testing {len(neighbors)} neighbor(s)...")
        iteration_improved = False
        
        for idx, neighbor_info in enumerate(neighbors):
            neighbor = neighbor_info["weights"]
            key = neighbor_info["key"]
            direction = neighbor_info["direction"]
            
            symbol = "+" if direction > 0 else "-"
            print(f"  {key} {symbol:1s}: ", end="", flush=True)
            
            update_config_weights(neighbor)
            results = run_games(games)
            winrate = results["winrate"]
            
            if winrate > best_winrate:
                best_winrate = winrate
                current_best = deepcopy(neighbor)
                iteration_improved = True
                print(f" {winrate:.0%} ✓ NEW BEST (+{(winrate-best_winrate)*100:.1f}%)")
                break  # Hill climbing: stop after first improvement
            
            time.sleep(0.2)
        
        if not iteration_improved:
            print(f"  No improvement in this iteration")
        
        history.append({
            "iteration": iteration + 1,
            "best_winrate": best_winrate,
            "improved": iteration_improved
        })
        
        print(f"Best so far: {best_winrate:.1%}")
        time.sleep(0.5)
    
    return current_best, best_winrate, history

def local_search_refine(base_weights: dict, iterations: int = 20, games: int = 20, mutation_range: float = 0.10):
    """Local search: evaluate multiple nearby points, move toward best"""
    print("\nStarting local search refinement...")
    print("=" * 70)
    
    current_best = deepcopy(base_weights)
    best_winrate = 0.0
    history = []
    
    # Test baseline first
    print(f"\n[BASELINE] Testing current weights...")
    update_config_weights(current_best)
    baseline_results = run_games(games)
    best_winrate = baseline_results["winrate"]
    print(f"Baseline win rate: {best_winrate:.1%}\n")
    
    for iteration in range(iterations):
        print(f"[ITERATION {iteration + 1}/{iterations}] Current best: {best_winrate:.1%}")
        
        # Identify "critical" weights - those that were tuned most by GA
        critical_keys = ["kill_bonus", "focus_long_range", "damage", "hp", "alive_unit"]
        
        # Test variations on critical weights
        candidates = []
        for key in critical_keys:
            for multiplier in [0.95, 0.975, 1.0, 1.025, 1.05]:
                variant = deepcopy(current_best)
                variant[key] = max(0.1, variant[key] * multiplier)
                candidates.append({"weights": variant, "key": key, "mult": multiplier})
        
        print(f"Testing {len(candidates)} critical weight variations...")
        
        best_variant = None
        best_variant_rate = best_winrate
        
        for candidate_info in candidates:
            variant = candidate_info["weights"]
            key = candidate_info["key"]
            mult = candidate_info["mult"]
            
            if mult == 1.0:
                continue  # Skip unchanged
            
            print(f"  {key} ×{mult:.3f}: ", end="", flush=True)
            
            update_config_weights(variant)
            results = run_games(games)
            winrate = results["winrate"]
            
            if winrate > best_variant_rate:
                best_variant_rate = winrate
                best_variant = deepcopy(variant)
            
            time.sleep(0.2)
        
        # Accept best variant if it improved
        if best_variant and best_variant_rate > best_winrate:
            best_winrate = best_variant_rate
            current_best = best_variant
            print(f"  ✓ Improved to {best_winrate:.0%}")
        else:
            print(f"  No improvement in this iteration")
        
        history.append({
            "iteration": iteration + 1,
            "best_winrate": best_winrate,
            "improved": best_variant is not None
        })
        
        print(f"Best so far: {best_winrate:.1%}\n")
        time.sleep(0.5)
    
    return current_best, best_winrate, history

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fine-tune weights around current best")
    parser.add_argument("--mode", choices=["hill", "local", "both"], default="local",
                        help="Refinement mode: hill climbing, local search, or both")
    parser.add_argument("--iterations", type=int, default=20, help="Refinement iterations")
    parser.add_argument("--games", type=int, default=20, help="Games per evaluation")
    parser.add_argument("--mutation", type=float, default=0.10, help="Mutation range (0.10 = +/-10%%)")
    args = parser.parse_args()
    
    try:
        # Load current weights
        current_weights = load_current_weights()
        if not current_weights:
            print("Could not load weights from config")
            sys.exit(1)
        
        print(f"Loaded {len(current_weights)} weights from config")
        
        results = {}
        
        if args.mode in ["hill", "both"]:
            best_weights, best_rate, history = hill_climbing_refine(
                current_weights,
                iterations=args.iterations,
                games=args.games,
                mutation_rate=args.mutation
            )
            results["hill_climbing"] = {
                "best_weights": best_weights,
                "best_winrate": best_rate,
                "history": history
            }
            
            if args.mode == "hill":
                update_config_weights(best_weights)
                print(f"\nConfig updated with hill climbing best weights (win rate: {best_rate:.0%})")
        
        if args.mode in ["local", "both"]:
            if args.mode == "both":
                # Use hill climbing result as starting point
                start_weights = results["hill_climbing"]["best_weights"]
            else:
                start_weights = current_weights
            
            best_weights, best_rate, history = local_search_refine(
                start_weights,
                iterations=args.iterations,
                games=args.games,
                mutation_range=args.mutation
            )
            results["local_search"] = {
                "best_weights": best_weights,
                "best_winrate": best_rate,
                "history": history
            }
            
            update_config_weights(best_weights)
            print(f"\nConfig updated with local search best weights (win rate: {best_rate:.0%})")
        
        # Save results
        RESULTS_LOG.parent.mkdir(exist_ok=True)
        with open(RESULTS_LOG, "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"Refine results saved to {RESULTS_LOG}")
        
    except KeyboardInterrupt:
        print("\nRefinement interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error during refinement: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
