"""
Run the full Arena.AI pipeline from data generation through training, tuning, and tournament evaluation.
This script is designed to be run from the python_bot directory.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
PYTHON_EXE = sys.executable


def run_command(command, cwd=PROJECT_DIR):
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command, cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {result.returncode}: {' '.join(command)}")


def generate_data(data_path: Path, num_games: int):
    print("\n=== Generate Training Data ===")
    data_path.parent.mkdir(parents=True, exist_ok=True)
    run_command([
        PYTHON_EXE,
        "train_neural.py",
        "--generate-data",
        "--data-path",
        str(data_path),
        "--num-games",
        str(num_games),
    ])


def train_neural(data_path: Path, model_path: Path, epochs: int, batch_size: int,
                 learning_rate: float, checkpoint_interval: int, resume: bool):
    print("\n=== Train Neural Network ===")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        PYTHON_EXE,
        "train_neural.py",
        "--train",
        "--data-path",
        str(data_path),
        "--model-path",
        str(model_path),
        "--epochs",
        str(epochs),
        "--batch-size",
        str(batch_size),
        "--learning-rate",
        str(learning_rate),
        "--checkpoint-interval",
        str(checkpoint_interval),
    ]
    if resume:
        command.append("--resume")
    run_command(command)


def tune_heuristics(games: int, max_candidates: int, output_path: Path):
    print("\n=== Tune Heuristic Weights ===")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run_command([
        PYTHON_EXE,
        "tune_heuristics.py",
        "--games",
        str(games),
        "--max-candidates",
        str(max_candidates),
        "--output",
        str(output_path),
    ])


def run_tournament(mode: str, games_per_pair: int, output_path: Path):
    print("\n=== Run Tournament ===")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run_command([
        PYTHON_EXE,
        "tournament.py",
        "--mode",
        mode,
        "--games-per-pair",
        str(games_per_pair),
        "--output",
        str(output_path),
    ])


def main():
    parser = argparse.ArgumentParser(description="Run full AI training, tuning, and tournament pipeline")
    parser.add_argument("--skip-generate", action="store_true", help="Skip training data generation")
    parser.add_argument("--skip-train", action="store_true", help="Skip neural network training")
    parser.add_argument("--skip-tune", action="store_true", help="Skip heuristic tuning")
    parser.add_argument("--skip-tournament", action="store_true", help="Skip tournament evaluation")
    parser.add_argument("--num-games", type=int, default=500, help="Number of training games to generate")
    parser.add_argument("--epochs", type=int, default=100, help="Neural network training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Training batch size")
    parser.add_argument("--learning-rate", type=float, default=0.001, help="Training learning rate")
    parser.add_argument("--checkpoint-interval", type=int, default=10, help="Checkpoint interval for training")
    parser.add_argument("--resume", action="store_true", help="Resume training from latest checkpoint")
    parser.add_argument("--tune-games", type=int, default=6, help="Number of games per heuristic candidate")
    parser.add_argument("--tune-candidates", type=int, default=12, help="Number of heuristic candidates to evaluate")
    parser.add_argument("--tournament-mode", choices=["round-robin", "single-elimination"], default="round-robin", help="Tournament mode")
    parser.add_argument("--tournament-games-per-pair", type=int, default=5, help="Games per pair in round-robin tournament")
    parser.add_argument("--data-path", type=str, default="data/training_games.json", help="Training data path")
    parser.add_argument("--model-path", type=str, default="models/value_network.pth", help="Model save path")
    parser.add_argument("--heuristic-output", type=str, default="logs/best_heuristic.json", help="Heuristic config output path")
    parser.add_argument("--tournament-output", type=str, default="logs/tournament_report.json", help="Tournament report path")

    args = parser.parse_args()

    data_path = Path(args.data_path)
    model_path = Path(args.model_path)
    heuristic_output = Path(args.heuristic_output)
    tournament_output = Path(args.tournament_output)

    if not args.skip_generate:
        generate_data(data_path, args.num_games)

    if not args.skip_train:
        train_neural(
            data_path,
            model_path,
            args.epochs,
            args.batch_size,
            args.learning_rate,
            args.checkpoint_interval,
            args.resume,
        )

    if not args.skip_tune:
        tune_heuristics(args.tune_games, args.tune_candidates, heuristic_output)

    if not args.skip_tournament:
        run_tournament(args.tournament_mode, args.tournament_games_per_pair, tournament_output)

    print("\n=== Full pipeline complete ===")
    print(f"Training data: {data_path}")
    print(f"Neural model: {model_path}")
    print(f"Best heuristic config: {heuristic_output}")
    print(f"Tournament report: {tournament_output}")


if __name__ == "__main__":
    main()
