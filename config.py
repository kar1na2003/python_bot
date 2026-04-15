"""
Configuration for Arena.AI Python bot.
Server execution only. Local simulation is used only for search.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Server
SERVER_URL = "http://localhost:5222"
REQUEST_TIMEOUT = 30

# Logging / UI
LOG_LEVEL = "INFO"
LOG_FILE = str(LOG_DIR / "bot.log")
PRINT_GAME_ACTIONS = True
PRINT_FULL_PAYLOADS = False
PRINT_HUB_EVENTS = False

# Search
SEARCH_MODE = "hybrid"   # tactical | mcts | hybrid
TIME_LIMIT = 3.0
MCTS_ITERATIONS = 500
UCB1_C_CONSTANT = 1.25
SIMULATION_DEPTH = 6
NUM_THREADS = 12
EARLY_STOP_THRESHOLD = 0.90
USE_TRANSPOSITION_TABLE = True
USE_KILLER_MOVES = True
USE_OPENING_BOOK = True
USE_POSITION_EVAL = True
USE_PROGRESSIVE_WIDENING = True

# Arena constants
ARENA_WIDTH = 20
ARENA_HEIGHT = 20
UNIT_MAX_HEALTH = 10
MAX_UNITS_PER_TEAM = 8

UNIT_TYPES = {
    0: "Light",
    1: "Heavy",
    2: "Fast",
    3: "ShortRange",
    4: "LongRange",
}

BOT_NAME = "ServerSearchBot"

# Heuristic weights. These are tuneable and can be overridden from JSON.
HEURISTIC_WEIGHTS = {
    "alive_unit": 123.48677466489626,
    "hp": 20.906850448626123,
    "attack_option": 16.30049253527622,
    "mobility": 1.067414727469699,
    "center_control": 1.6809465114403919,
    "progress": 0.8232854063789168,
    "cluster": 2.335997138282249,
    "kill_bonus": 322.6942652648887,
    "damage": 34.56982101613419,
    "focus_long_range": 56.57570439572235,
    "focus_short_range": 23.25362467639711,
    "focus_fast": 19.800930302572354,
    "value_base": 8.677179172509078,
    "value_attack": 9.593355329900582,
    "value_defence": 5.011867289243151,
    "value_range": 7.424782594296541,
    "value_movement": 3.0087921863252483,
    "value_health": 6.515934276801169,
}

# Optional per-type multipliers on top of dynamic value
UNIT_TYPE_MULTIPLIERS = {
    "Light": 1.00,
    "Heavy": 1.12,
    "Fast": 1.05,
    "ShortRange": 1.10,
    "LongRange": 1.18,
}

# --- Data Engineering & Analytics Pipeline ---
ENABLE_TELEMETRY = True
TELEMETRY_EXPORT_PATH = "logs/mcts_metrics.csv"
SUMMARY_EXPORT_PATH = "logs/summary.jsonl"
