import json
import logging
import time
from typing import Callable, Optional

import config
from signalrcore.hub_connection_builder import HubConnectionBuilder

logger = logging.getLogger(__name__)


class ArenaSignalRClient:
    def __init__(self, server_url: str):
        self.server_url = server_url.rstrip("/")
        self.hub_url = f"{self.server_url}/play"
        self.connection = None
        self.connected = False

        self._pending_handler: Optional[Callable] = None
        self._joined_handler: Optional[Callable] = None
        self._winner_handler: Optional[Callable] = None
        self._generic_handler: Optional[Callable] = None

    def set_pending_handler(self, handler: Callable):
        self._pending_handler = handler

    def set_joined_handler(self, handler: Callable):
        self._joined_handler = handler

    def set_winner_handler(self, handler: Callable):
        self._winner_handler = handler

    def set_generic_handler(self, handler: Callable):
        self._generic_handler = handler

    def connect(self):
        logger.info(f"Connecting to SignalR hub: {self.hub_url}")

        self.connection = (
            HubConnectionBuilder()
            .with_url(self.hub_url)
            .configure_logging(logging.INFO)
            .build()
        )

        self.connection.on_open(self._on_open)
        self.connection.on_close(self._on_close)
        self.connection.on_error(self._on_error)

        self.connection.on("Joined", self._handle_joined)
        self.connection.on("PendingMovement", self._handle_pending_movement)

        # Можливі події завершення бою
        self.connection.on("Winner", self._handle_winner)
        self.connection.on("BattleEnded", self._handle_battle_ended)
        self.connection.on("GameEnd", self._handle_game_end)
        self.connection.on("GameEnded", self._handle_game_end)
        self.connection.on("Ended", self._handle_ended)

        for event_name in [
            "ReceiveMessage",
            "GameState",
            "BattleState",
            "Update",
            "ActionResult",
            "Connected",
            "BattleStarted",
            "TurnStarted",
            "YourTurn",
            "GameEnd",
        ]:
            self.connection.on(event_name, self._make_generic_handler(event_name))

        self.connection.start()

        timeout = time.time() + 10
        while not self.connected and time.time() < timeout:
            time.sleep(0.1)

        if not self.connected:
            raise RuntimeError("Could not connect to SignalR hub")

    def stop(self):
        if self.connection:
            try:
                self.connection.stop()
            except Exception as e:
                logger.error(f"Error stopping SignalR connection: {e}")

    def _on_open(self):
        self.connected = True
        logger.info("SignalR hub connected")

    def _on_close(self):
        self.connected = False
        logger.info("SignalR hub disconnected")

    def _on_error(self, error):
        try:
            logger.error(
                "SignalR error: type=%s content=%r",
                type(error).__name__,
                getattr(error, "__dict__", error),
            )
        except Exception:
            logger.error(f"SignalR error: {error!r}")

    def _handle_joined(self, args):
        if config.PRINT_HUB_EVENTS:
            logger.info(f"[HUB EVENT] Joined: {args}")
        if self._joined_handler:
            try:
                self._joined_handler(args)
            except Exception as e:
                logger.exception(f"Joined handler failed: {e}")

    def _handle_pending_movement(self, args):
        if config.PRINT_HUB_EVENTS:
            logger.info(f"[HUB EVENT] PendingMovement: {args}")

        try:
            payload = args[0] if isinstance(args, list) and args else args
            pretty = json.dumps(payload, indent=2, ensure_ascii=False, default=str)
            if config.PRINT_HUB_EVENTS:
                logger.info(f"[HUB EVENT PRETTY] PendingMovement:\n{pretty}")

            # якщо winner приходить прямо всередині PendingMovement
            if isinstance(payload, dict) and payload.get("winner") is not None:
                self._emit_winner(payload.get("winner"), payload)
        except Exception:
            pass

        if self._pending_handler:
            try:
                payload = args[0] if isinstance(args, list) and len(args) > 0 else args
                self._pending_handler(payload)
            except Exception as e:
                logger.exception(f"PendingMovement handler failed: {e}")

    def _handle_winner(self, args):
        if config.PRINT_HUB_EVENTS:
            logger.info(f"[HUB EVENT] Winner: {args}")
        winner = args[0] if isinstance(args, list) and args else args
        self._emit_winner(winner, args)

    def _handle_battle_ended(self, args):
        if config.PRINT_HUB_EVENTS:
            logger.info(f"[HUB EVENT] BattleEnded: {args}")
        winner = self._extract_winner(args)
        self._emit_winner(winner, args)

    def _handle_game_ended(self, args):
        if config.PRINT_HUB_EVENTS:
            logger.info(f"[HUB EVENT] GameEnded: {args}")
        winner = self._extract_winner(args)
        self._emit_winner(winner, args)

    def _handle_game_end(self, args):
        if config.PRINT_HUB_EVENTS:
            logger.info(f"[HUB EVENT] GameEnd: {args}")
        winner = self._extract_winner(args)
        self._emit_winner(winner, args)

    def _handle_ended(self, args):
        if config.PRINT_HUB_EVENTS:
            logger.info(f"[HUB EVENT] Ended: {args}")
        winner = self._extract_winner(args)
        self._emit_winner(winner, args)

    def _emit_winner(self, winner, raw_args=None):
        if self._winner_handler:
            try:
                self._winner_handler(winner, raw_args)
            except TypeError:
                # якщо в main.py handler приймає 1 аргумент
                try:
                    self._winner_handler(winner)
                except Exception as e:
                    logger.exception(f"Winner handler failed: {e}")
            except Exception as e:
                logger.exception(f"Winner handler failed: {e}")

    def _extract_winner(self, args):
        payload = args[0] if isinstance(args, list) and args else args
        if isinstance(payload, dict):
            return payload.get("winner") or payload.get("teamName") or payload.get("name")
        return payload

    def _make_generic_handler(self, event_name: str):
        def handler(args):
            logger.info(f"[HUB EVENT] {event_name}: {args}")
            if self._generic_handler:
                try:
                    self._generic_handler(event_name, args)
                except Exception as e:
                    logger.exception(f"Generic handler failed for {event_name}: {e}")
        return handler

    def join(self, invite_id: str) -> bool:
        try:
            logger.info(f"Trying hub method 'Join' with invite_id={invite_id}")
            self.connection.send("Join", [invite_id])
            return True
        except Exception as e:
            logger.error(f"Hub method 'Join' failed: {e}")
            return False

    def try_join_invite(self, invite_id: str) -> bool:
        return self.join(invite_id)

    def send_action(self, action_payload: dict, action_type: str = None) -> bool:
        try:
            logger.info(
                f"Sending action via 'Act': action_type={action_type}, payload={action_payload}"
            )
            self.connection.send("Act", [action_payload])
            return True
        except Exception as e:
            logger.error(f"Failed to send action: {e}")
            return False