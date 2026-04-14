import json
from pathlib import Path
from typing import Any, Dict

import config


class HeuristicConfig:
    def __init__(self):
        self.weights: Dict[str, float] = dict(config.HEURISTIC_WEIGHTS)
        self.unit_type_multipliers: Dict[str, float] = dict(config.UNIT_TYPE_MULTIPLIERS)

    def apply_overrides(self, data: Dict[str, Any]) -> None:
        if not data:
            return
        for k, v in data.get("weights", {}).items():
            self.weights[k] = float(v)
        for k, v in data.get("unit_type_multipliers", {}).items():
            self.unit_type_multipliers[k] = float(v)

    def load_json(self, path: str | None) -> None:
        if not path:
            return
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Heuristic config not found: {path}")
        with p.open("r", encoding="utf-8") as f:
            self.apply_overrides(json.load(f))

    def dump_json(self, path: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "weights": self.weights,
                    "unit_type_multipliers": self.unit_type_multipliers,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )


ACTIVE_HEURISTICS = HeuristicConfig()
