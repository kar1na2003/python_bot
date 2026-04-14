"""Run batches of server games with different heuristic weights and keep the best profile."""
from __future__ import annotations

import argparse
import itertools
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from bot.heuristic_config import HeuristicConfig


def build_candidates(base: HeuristicConfig):
    knobs = {
        "kill_bonus": [160.0, 220.0, 280.0],
        "damage": [18.0, 24.0, 30.0],
        "focus_long_range": [25.0, 40.0, 60.0],
        "exposed_ranged": [-12.0, -22.0, -32.0],
        "threatened": [-10.0, -18.0, -26.0],
    }
    keys = list(knobs.keys())
    for values in itertools.product(*(knobs[k] for k in keys)):
        cfg = HeuristicConfig()
        cfg.weights = dict(base.weights)
        cfg.unit_type_multipliers = dict(base.unit_type_multipliers)
        for k, v in zip(keys, values):
            cfg.weights[k] = v
        yield cfg


def run_candidate(project_dir: Path, python_exe: str, cfg: HeuristicConfig, games: int) -> dict:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        cfg_path = td / "heuristic.json"
        summary_path = td / "summary.json"
        cfg.dump_json(str(cfg_path))

        cmd = [
            python_exe,
            "main.py",
            "--games",
            str(games),
            "--heuristic-config",
            str(cfg_path),
            "--summary-json",
            str(summary_path),
            "--quiet-actions",
        ]
        subprocess.run(cmd, cwd=project_dir, check=True)
        return json.loads(summary_path.read_text(encoding="utf-8"))


def score_summary(summary: dict) -> float:
    my = summary["my_results"]
    return my.get("WIN", 0) * 1.0 + my.get("DRAW", 0) * 0.25 - my.get("LOSS", 0) * 0.1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=6)
    parser.add_argument("--max-candidates", type=int, default=12)
    parser.add_argument("--python", type=str, default=sys.executable)
    parser.add_argument("--output", type=str, default="logs/best_heuristic.json")
    args = parser.parse_args()

    project_dir = Path(__file__).resolve().parent
    base = HeuristicConfig()

    best_score = float("-inf")
    best_cfg = None
    best_summary = None

    for idx, cfg in enumerate(build_candidates(base), start=1):
        if idx > args.max_candidates:
            break
        print(f"[tuner] candidate {idx}/{args.max_candidates}")
        summary = run_candidate(project_dir, args.python, cfg, args.games)
        score = score_summary(summary)
        print(f"[tuner] score={score:.3f} my_results={summary['my_results']}")
        if score > best_score:
            best_score = score
            best_cfg = cfg
            best_summary = summary

    if best_cfg is None:
        raise SystemExit("No candidates were evaluated")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    best_cfg.dump_json(str(out))
    print(f"[tuner] best score={best_score:.3f}")
    print(f"[tuner] wrote best config to {out}")
    print(json.dumps(best_summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
