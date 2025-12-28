import uuid
import json
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .rabbitmq import RabbitMQ
else:
    try:
        from .rabbitmq import RabbitMQ
    except ImportError:
        RabbitMQ = None


class GameClient:
    """
    Small helper class that abstracts communication between a game
    and our platform.

    Instead of actually doing the communication we are just printing a payload for now.
    """

    def __init__(
            self,
            game_id: str,
            api_key: str,
            base_url: str = "http://localhost:8000",
            message_bus: Optional[Any] = None,
            queue_name: Optional[str] = None,
    ):
        self.game_id = game_id
        self.api_key = api_key
        self.base_url = base_url
        self._bus = message_bus
        self._queue_name = "game_events"

    def _post(self, path: str, payload: Dict[str, Any]) -> None:
        message = {
            "path": path,
            "payload": payload,
        }

        if self._bus is None:
            print(f"[GameClient] POST {self.base_url}{path}")
            print(json.dumps(payload, indent=2))
            return

        self._bus.publish(self._queue_name, message)

    def start_match(
        self,
        players: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Register a new match on the platform and return a match_id.
        """
        match_id = str(uuid.uuid4())

        payload = {
            "game_id": self.game_id,
            "match_id": match_id,
            "players": players,
            "metadata": metadata or {},
        }

        self._post("/api/games/start", payload)
        return match_id

    def log_move(
        self,
        match_id: str,
        state: Dict[str, Any],
        move: Dict[str, Any],
        heuristic_value: Optional[float] = None,
    ) -> None:
        """
        Log a single move together with the current game state.
        """
        payload = {
            "game_id": self.game_id,
            "match_id": match_id,
            "state": state,
            "move": move,
        }

        if heuristic_value is not None:
            payload["heuristic_value"] = heuristic_value

        self._post("/api/games/move", payload)

    def log_event(
        self,
        match_id: str,
        event_type: str,
        payload: Dict[str, Any],
    ) -> None:
        """
        Generic logging hook for extra events that are not moves.
        """
        event = {
            "game_id": self.game_id,
            "match_id": match_id,
            "event_type": event_type,
            "payload": payload,
        }
        self._post("/api/games/event", event)

    def end_match(
        self,
        match_id: str,
        result: str,
        final_state: Dict[str, Any],
    ) -> None:
        """
        Mark the match as finished on the platform and log the final state.
        """
        payload = {
            "game_id": self.game_id,
            "match_id": match_id,
            "result": result,  # e.g. "P1_WIN", "P2_WIN", "DRAW"
            "final_state": final_state,
        }
        self._post("/api/games/end", payload)
