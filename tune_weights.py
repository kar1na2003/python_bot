"""
Automated heuristic weight tuner - runs games and optimizes weights for maximum win rate
"""
import json
import subprocess
import time
import sys
from pathlib import Path
from copy import deepcopy
import numpy as np

CONFIG_PATH = Path(__file__).parent / "config.py"
LOG_FILE = Path(__file__).parent / "logs" / "tune_summary.json"

BASE_WEIGHTS = {
    "alive_unit": 150.0,
    "hp": 20.0,
    "threatened": -30.0,
    "attack_option": 15.0,
    "mobility": 1.2,
    "center_control": 1.5,
    "progress": 1.0,
    "cluster": 2.0,
    "exposed_ranged": -35.0,
    "kill_bonus": 300.0,
    "damage": 30.0,
    "counter_damage": -20.0,
    "focus_long_range": 60.0,
    "focus_short_range": 25.0,
    "focus_fast": 18.0,
    "value_base": 10.0,
    "value_attack": 8.0,
    "value_defence": 6.0,
    "value_range": 9.0,
    "value_movement": 3.0,
    "value_health": 5.5,
}

def update_config_weights(weights_dict):
    """Update the config.py file with new weights"""
    config_content = CONFIG_PATH.read_text()
    
    # Create the new weights string
    weights_str = "HEURISTIC_WEIGHTS = {\n"
    for key, val in weights_dict.items():
        weights_str += f'    "{key}": {val},\n'
    weights_str += "}\n"
    
    # Find and replace the HEURISTIC_WEIGHTS block
    import re
    pattern = r'HEURISTIC_WEIGHTS = \{[^}]+\}'
    config_content = re.sub(pattern, weights_str.rstrip('\n'), config_content, flags=re.DOTALL)
    
    CONFIG_PATH.write_text(config_content)

def run_games(num_games: int = 20) -> dict:
    """Run N games and extract win/loss counts from logs"""
    print(f"Running {num_games} games...")
    
    cmd = [sys.executable, "main.py", str(num_games), "--quiet-actions"]
    result = subprocess.run(
        cmd,
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True,
        timeout=600
    )
    
    if result.returncode != 0:
        print(f"Error running games: {result.stderr}")
        return {"wins": 0, "losses": 0, "draws": 0}
    
    # Parse the log output
    output = result.stdout + result.stderr
    wins = output.count("Result: WIN")
    losses = output.count("Result: LOSS")
    draws = output.count("Result: DRAW")
    
    return {"wins": wins, "losses": losses, "draws": draws}

def calculate_winrate(results: dict) -> float:
    """Calculate win rate from results"""
    total = results["wins"] + results["losses"] + results["draws"]
    if total == 0:
        return 0.0
    return results["wins"] / total

def generate_variants(base_weights: dict, mutation_rate: float = 0.15, num_variants: int = 5) -> list:
    """Generate weight variants by mutating the base weights"""
    variants = []
    
    # Keep the base
    variants.append(deepcopy(base_weights))
    
    # Generate mutations
    critical_keys = ["kill_bonus", "damage", "threatened", "focus_long_range"]
    
    for _ in range(num_variants - 1):
        variant = deepcopy(base_weights)
        
        for key in variant.keys():
            if np.random.random() < mutation_rate:
                # Larger mutations for critical keys
                mutate_factor = 1.0 + np.random.uniform(-0.3, 0.3)
                if key in critical_keys:
                    mutate_factor = 1.0 + np.random.uniform(-0.4, 0.4)
                
                variant[key] = max(0.1, variant[key] * mutate_factor)
        
        variants.append(variant)
    
    return variants

def tune_weights(iterations: int = 10, games_per_variant: int = 20, variants_per_iteration: int = 5):
    """Main tuning loop"""
    best_weights = deepcopy(BASE_WEIGHTS)
    best_winrate = 0.0
    history = []
    
    print(f"Starting weight tuning: {iterations} iterations, {games_per_variant} games/variant")
    print("=" * 70)
    
    for iteration in range(iterations):
        print(f"\n[ITERATION {iteration + 1}/{iterations}]")
        print(f"Current best win rate: {best_winrate:.1%} (win_rate)")
        print(f"Generating {variants_per_iteration} weight variants...")
        
        variants = generate_variants(best_weights, mutation_rate=0.2, num_variants=variants_per_iteration)
        iteration_results = []
        
        for v_idx, variant in enumerate(variants):
            print(f"\n  Variant {v_idx + 1}/{len(variants)}...")
            
            # Update config
            update_config_weights(variant)
            
            # Run games
            results = run_games(games_per_variant)
            winrate = calculate_winrate(results)
            
            print(f"    Wins: {results['wins']}, Losses: {results['losses']}, Draws: {results['draws']}")
            print(f"    Win rate: {winrate:.1%}")
            
            iteration_results.append({
                "variant": v_idx,
                "winrate": winrate,
                "results": results,
                "weights": deepcopy(variant)
            })
            
            # Update best if this is better
            if winrate > best_winrate:
                best_winrate = winrate
                best_weights = deepcopy(variant)
                print(f"    ✓ NEW BEST! Updated best weights (win rate: {best_winrate:.1%})")
            
            time.sleep(1)  # Brief pause between variants
        
        # Sort by winrate
        iteration_results.sort(key=lambda x: x["winrate"], reverse=True)
        
        print(f"\n  ➤ Iteration best: {iteration_results[0]['winrate']:.1%}")
        
        history.append({
            "iteration": iteration + 1,
            "best_winrate": best_winrate,
            "best_weights": best_weights,
            "variants_tested": iteration_results
        })
        
        # Save progress
        save_progress(history, best_weights, best_winrate)
    
    print("\n" + "=" * 70)
    print(f"TUNING COMPLETE")
    print(f"Final best win rate: {best_winrate:.1%}")
    print(f"Final best weights:")
    for key, val in sorted(best_weights.items()):
        print(f"  {key}: {val}")
    
    return best_weights, best_winrate

def save_progress(history: list, best_weights: dict, best_winrate: float):
    """Save tuning progress to file"""
    summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "best_winrate": best_winrate,
        "best_weights": best_weights,
        "history_length": len(history),
        "last_iteration": history[-1] if history else None
    }
    
    LOG_FILE.parent.mkdir(exist_ok=True)
    with open(LOG_FILE, "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nProgress saved to {LOG_FILE}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Tune heuristic weights for Arena.AI bot")
    parser.add_argument("--iterations", type=int, default=10, help="Number of tuning iterations")
    parser.add_argument("--games", type=int, default=20, help="Games per weight variant")
    parser.add_argument("--variants", type=int, default=5, help="Variants per iteration")
    args = parser.parse_args()
    
    try:
        best_weights, best_winrate = tune_weights(
            iterations=args.iterations,
            games_per_variant=args.games,
            variants_per_iteration=args.variants
        )
        
        # Update config with best weights
        update_config_weights(best_weights)
        print(f"\nConfig updated with best weights (win rate: {best_winrate:.1%})")
        
    except KeyboardInterrupt:
        print("\nTuning interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error during tuning: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
