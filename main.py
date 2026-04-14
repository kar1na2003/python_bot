"""Main entry point for Arena.AI Python Bot."""
from __future__ import annotations

import argparse
import json
import logging
import threading
import time
from pathlib import Path

import config
from bot.api_client import APIClient
from bot.game_state import BattleState
from bot.heuristic_config import ACTIVE_HEURISTICS
from bot.mcts import MCTSBot
from bot.search_engine import SearchEngine
from bot.signalr_client import ArenaSignalRClient


logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(config.LOG_FILE), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

for noisy_name in ["SignalRCoreClient", "signalrcore", "websocket", "urllib3"]:
    noisy_logger = logging.getLogger(noisy_name)
    noisy_logger.handlers.clear()
    noisy_logger.propagate = False
    noisy_logger.setLevel(logging.CRITICAL + 1)
    noisy_logger.disabled = True


class BotController:
    def __init__(self):
        self.api_client = APIClient()
        self.mcts_bot = MCTSBot(
            iterations=config.MCTS_ITERATIONS,
            c_constant=config.UCB1_C_CONSTANT,
            simulation_depth=config.SIMULATION_DEPTH,
            verbose=False,
            early_stop_threshold=config.EARLY_STOP_THRESHOLD,
            use_transposition_table=config.USE_TRANSPOSITION_TABLE,
            use_killer_moves=config.USE_KILLER_MOVES,
            use_opening_book=config.USE_OPENING_BOOK,
            use_position_evaluation=config.USE_POSITION_EVAL,
            use_progressive_widening=config.USE_PROGRESSIVE_WIDENING,
            num_threads=config.NUM_THREADS,
            time_limit=config.TIME_LIMIT,
        )
        self.search_engine = SearchEngine(self.mcts_bot)
        self.signalr_client = ArenaSignalRClient(config.SERVER_URL)

        self._stop_event = threading.Event()
        self._processing_turn = threading.Lock()

        self._last_turn_signature = None
        self._last_action_payload = None

        self.last_winner = None
        self.current_invite_id = None
        self.my_team = None
        self.move_number = 0
        self.last_move_seconds = 0.0
        self.last_result = "UNKNOWN"

        self.awaiting_action_result = False
        self.last_action_sent_at = 0.0
        self.last_action_type = None
        self.last_progress_time = time.time()
        self.watchdog_timeout_sec = 4.0
        self.watchdog_retry_count = 0
        self.watchdog_retry_limit = 3
        
        self.server_stalled = False

    def _watchdog_loop(self):
        while not self._stop_event.is_set():
            time.sleep(0.5)

            if not self.awaiting_action_result:
                continue

            elapsed = time.time() - self.last_action_sent_at
            if elapsed <= self.watchdog_timeout_sec:
                continue

            # після кількох retry припиняємо гру, а не висимо вічно
            if self.watchdog_retry_count >= self.watchdog_retry_limit:
                logger.error(
                    "Watchdog: server did not respond after %d retries. Marking game as stalled.",
                    self.watchdog_retry_limit
                )
                self.awaiting_action_result = False
                self.server_stalled = True
                self.last_result = "UNKNOWN"
                self.last_winner = None
                self._stop_event.set()
                return

            logger.warning(
                "Watchdog: no response for %.2fs -> retry %d/%d",
                elapsed,
                self.watchdog_retry_count + 1,
                self.watchdog_retry_limit,
            )

            if self._last_action_payload is not None:
                ok = self.signalr_client.send_action(
                    self._last_action_payload,
                    self.last_action_type
                )
                if ok:
                    self.last_action_sent_at = time.time()
                    self.watchdog_retry_count += 1
                else:
                    logger.error("Watchdog resend failed")
                    self.awaiting_action_result = False
                    self.server_stalled = True
                    self.last_result = "UNKNOWN"
                    self.last_winner = None
                    self._stop_event.set()
                    return
                
    def start(self):
        logger.info("Creating PvB battle invite automatically...")
        invite_id = self.api_client.create_pvb_battle()
        self.current_invite_id = invite_id
        self.my_team = "TeamA"  # PvB invites assign the external player to TeamA
        logger.info("Invite created: %s", invite_id)

        self.signalr_client.set_pending_handler(self.handle_pending_movement)
        self.signalr_client.set_winner_handler(self.handle_winner)

        logger.info("Connecting to /play hub...")
        self.signalr_client.connect()

        logger.info("Trying to join invite...")
        if not self.signalr_client.join(invite_id):
            logger.error("Could not join invite")
            return False

        threading.Thread(target=self._watchdog_loop, daemon=True).start()

        logger.info("Join request sent through 'Join'. Waiting for hub events...")
        return True

    def _pick_fallback_action(self, state: BattleState):
        next_info = state.next_unit_info

        if next_info.available_attack_targets:
            target = next_info.available_attack_targets[0]
            return {"actionType": "Attack", "destination": None, "target": target}, "Attack"

        if next_info.available_destinations:
            dest = next_info.available_destinations[0]
            return {"actionType": "Move", "destination": dest, "target": None}, "Move"

        return {"actionType": "Skip", "destination": None, "target": None}, "Skip"

    def _sanitize_action(self, state: BattleState, action):
        next_info = state.next_unit_info
        payload = action.to_dict()
        action_type = action.action_type

        legal_targets = set(next_info.available_attack_targets)
        legal_destinations = set(next_info.available_destinations)

        if action_type == "Attack":
            target = payload.get("target")
            if target in legal_targets:
                return payload, action_type

            logger.warning(
                "Illegal Attack chosen: %r not in %r -> fallback",
                target, sorted(legal_targets)
            )
            return self._pick_fallback_action(state)

        if action_type == "Move":
            dest = payload.get("destination")
            if dest in legal_destinations:
                return payload, action_type

            logger.warning(
                "Illegal Move chosen: %r not in legal destinations -> fallback",
                dest
            )
            return self._pick_fallback_action(state)

        if action_type == "Skip":
            if legal_targets or legal_destinations:
                logger.warning(
                    "Skip chosen while legal actions exist (targets=%d, moves=%d) -> fallback",
                    len(legal_targets),
                    len(legal_destinations),
                )
                return self._pick_fallback_action(state)
            return payload, action_type

        logger.warning("Unknown action type %r -> fallback", action_type)
        return self._pick_fallback_action(state)

    def run_single_game(self):
        self.server_stalled = False
        self._stop_event.clear()
        self._last_turn_signature = None
        self._last_action_payload = None
        self.last_winner = None
        self.my_team = None
        self.move_number = 0
        self.last_move_seconds = 0.0
        self.last_result = "UNKNOWN"
        self.current_invite_id = None

        self.awaiting_action_result = False
        self.last_action_sent_at = 0.0
        self.last_action_type = None
        self.last_progress_time = time.time()
        self.watchdog_retry_count = 0

        if not self.start():
            return None

        try:
            while not self._stop_event.is_set():
                time.sleep(0.25)
            if self.server_stalled:
                logger.error("Game ended due to server stall")
            return self.last_winner
        finally:
            self.signalr_client.stop()

    def handle_winner(self, winner: str, raw_args=None):
        self.awaiting_action_result = False
        self.last_progress_time = time.time()

        self.last_winner = winner
        if self.my_team is None:
            self.last_result = "UNKNOWN"
        elif winner == self.my_team:
            self.last_result = "WIN"
        elif winner in (None, "Noone"):
            self.last_result = "DRAW"
        else:
            self.last_result = "LOSS"

        logger.info(
            "Game over. Winner: %s | My team: %s | Result: %s",
            winner, self.my_team, self.last_result,
        )
        if config.PRINT_FULL_PAYLOADS:
            logger.info("Final payload: %s", raw_args)
        self._stop_event.set()

    def handle_pending_movement(self, payload: dict):
        self.awaiting_action_result = False
        self.last_progress_time = time.time()
        self.watchdog_retry_count = 0

        if self._stop_event.is_set():
            return
        if not self._processing_turn.acquire(blocking=False):
            return

        try:
            state = BattleState.from_dict(payload)

            if self.my_team is None:
                self.my_team = state.next_unit_info.team_name
                logger.info("Detected my team: %s", self.my_team)

            unit = state.next_unit_info.unit
            signature = (
                state.battle_id,
                state.next_unit_info.team_name,
                unit.name,
                unit.x_position,
                unit.y_position,
                tuple(state.next_unit_info.available_destinations),
                tuple(state.next_unit_info.available_attack_targets),
            )

            if signature == self._last_turn_signature:
                logger.info("Duplicate PendingMovement -> resend previous action")
                if self._last_action_payload is not None:
                    self.awaiting_action_result = True
                    self.last_action_sent_at = time.time()
                    ok = self.signalr_client.send_action(
                        self._last_action_payload,
                        self.last_action_type
                    )
                    if not ok:
                        logger.error("Failed to resend previous action")
                        self.awaiting_action_result = False
                        self._stop_event.set()
                return

            self._last_turn_signature = signature
            self.move_number += 1

            t0 = time.perf_counter()
            raw_action = self.search_engine.choose_action(state)
            elapsed = time.perf_counter() - t0
            self.last_move_seconds = elapsed

            action_payload, action_type = self._sanitize_action(state, raw_action)

            self._last_action_payload = action_payload
            self.last_action_type = action_type

            logger.info(
                "Move #%d | Team=%s | Unit=%s | Action=%s | Time=%.3fs",
                self.move_number,
                state.next_unit_info.team_name,
                unit.name,
                action_payload,
                elapsed,
            )

            self.awaiting_action_result = True
            self.last_action_sent_at = time.time()

            ok = self.signalr_client.send_action(action_payload, action_type)
            if not ok:
                logger.error("Failed to send action: %s", action_payload)
                self.awaiting_action_result = False
                self._stop_event.set()

        except Exception as e:
            logger.exception("Failed to process pending movement: %s", e)
            self.awaiting_action_result = False
            self._stop_event.set()
        finally:
            self._processing_turn.release()

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("games_pos", nargs="?", type=int, default=None, help="Number of games to play")
    parser.add_argument("-g", "--games", dest="games", type=int, default=None, help="Number of games to play")
    parser.add_argument("--heuristic-config", type=str, default=None, help="Path to heuristic JSON overrides")
    parser.add_argument("--summary-json", type=str, default=None, help="Optional path to write summary JSON")
    parser.add_argument("--quiet-actions", action="store_true", help="Hide action logs and suppress SignalR event output")

    args = parser.parse_args()
    args.games = args.games if args.games is not None else (args.games_pos if args.games_pos is not None else 1)
    return args


def main():
    args = parse_args()
    if args.heuristic_config:
        ACTIVE_HEURISTICS.load_json(args.heuristic_config)
        logger.info("Loaded heuristic overrides from %s", args.heuristic_config)
    if args.quiet_actions:
        config.PRINT_GAME_ACTIONS = False
        config.PRINT_HUB_EVENTS = False
        logging.getLogger().setLevel(logging.WARNING)

    print("Starting bot...")
    logger.info("=" * 50)
    logger.info("Arena.AI Python Bot")
    logger.info("=" * 50)

    logger.info("Checking server health at %s...", config.SERVER_URL)
    health_result = APIClient.health_check(config.SERVER_URL)
    print(f"Health check result: {health_result}")

    if not health_result:
        logger.error("Server is not reachable")
        return

    controller = BotController()
    results = {"TeamA": 0, "TeamB": 0, "Noone": 0, None: 0}
    my_results = {"WIN": 0, "LOSS": 0, "DRAW": 0, "UNKNOWN": 0}

    try:
        for i in range(args.games):
            logger.info("=" * 50)
            logger.info("Starting game %d / %d", i + 1, args.games)
            logger.info("=" * 50)

            winner = controller.run_single_game()
            results[winner] = results.get(winner, 0) + 1
            my_results[controller.last_result] = my_results.get(controller.last_result, 0) + 1

            logger.info(
                "Finished game %d / %d. Winner: %s | My team: %s | Result: %s",
                i + 1,
                args.games,
                winner,
                controller.my_team,
                controller.last_result,
            )
            time.sleep(0.5)

        logger.info("=" * 50)
        logger.info("FINAL RESULTS")
        logger.info("TeamA wins: %d", results.get("TeamA", 0))
        logger.info("TeamB wins: %d", results.get("TeamB", 0))
        logger.info("Draws (Noone): %d", results.get("Noone", 0))
        logger.info("Unknown winners: %d", results.get(None, 0))
        logger.info("My wins: %d", my_results.get("WIN", 0))
        logger.info("My losses: %d", my_results.get("LOSS", 0))
        logger.info("My draws: %d", my_results.get("DRAW", 0))
        logger.info("My unknown: %d", my_results.get("UNKNOWN", 0))
        logger.info("=" * 50)

        if args.summary_json:
            summary = {
                "winner_counts": {str(k): v for k, v in results.items()},
                "my_results": my_results,
                "games": args.games,
                "weights": ACTIVE_HEURISTICS.weights,
                "unit_type_multipliers": ACTIVE_HEURISTICS.unit_type_multipliers,
            }
            path = Path(args.summary_json)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
            logger.info("Wrote summary JSON to %s", path)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        controller._stop_event.set()
        controller.signalr_client.stop()


if __name__ == "__main__":
    main()
