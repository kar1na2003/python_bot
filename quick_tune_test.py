"""
Quick-run version of the analyze_and_tune_pipeline with minimal games for testing.
"""
import sys
from pathlib import Path

# Add parent directory to path
PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))

from analyze_and_tune_pipeline import main
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Quick test run of the heuristic tuning pipeline"
    )
    parser.add_argument("--games-before", type=int, default=2,
                       help="Games before tuning (default: 2)")
    parser.add_argument("--games-after", type=int, default=2,
                       help="Games after tuning (default: 2)")
    parser.add_argument("--candidates", type=int, default=3,
                       help="Number of candidates to test (default: 3)")
    
    args = parser.parse_args()
    
    # Override sys.argv for the main pipeline
    sys.argv = [
        sys.argv[0],
        "--games-before", str(args.games_before),
        "--games-after", str(args.games_after),
    ]
    
    main()
