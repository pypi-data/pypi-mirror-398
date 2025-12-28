"""
Event models for the gaming platform.

This module defines typed event models for communication between game services
and the platform. Events follow the platform's standardized format with:
- eventPit: ISO_LOCAL_DATE_TIME timestamp (no timezone offset)
- Strongly typed fields
- UUID support for lobby/session IDs
- JSON serialization compatible with Java backend
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID
import json


@dataclass
class DomainEvent:
    """
    Base class for all platform events.

    All events include an eventPit (timestamp) that represents when the event occurred.
    This matches the platform's Java DomainEvent structure and uses ISO_LOCAL_DATE_TIME
    formatting (no timezone offset) for compatibility with Java LocalDateTime.
    """
    event_pit: str

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert event to dictionary for serialization.

        Handles UUID conversion to string format.
        """
        data = asdict(self)
        # Convert UUIDs to strings
        for key, value in data.items():
            if isinstance(value, UUID):
                data[key] = str(value)
        return data

    def to_json(self) -> str:
        """Serialize event to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainEvent":
        """
        Create event instance from dictionary.

        Handles UUID parsing from string format.
        """
        # Parse UUIDs from strings
        for key, value in data.items():
            if key.endswith("Id") and isinstance(value, str):
                try:
                    data[key] = UUID(value)
                except (ValueError, AttributeError):
                    pass  # Keep as string if not a valid UUID

        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "DomainEvent":
        """Deserialize event from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


# ============================================================================
# OUTGOING EVENTS (Game → Platform)
# ============================================================================

@dataclass
class GameStartedEvent(DomainEvent):
    """
    Event published when a game session starts.

    Sent by game services to notify the platform that a match has begun.
    The platform uses this to track active sessions and update lobby state.

    Routing:
        Queue: game.started
        Routing Key: sdk.game.started.v1

    Attributes:
        sessionId: Unique identifier for the game session
        lobbyId: UUID of the lobby that created this session
        gameId: Identifier for the game type (e.g., "tic-tac-toe")
        playerIds: List of player IDs participating in the session
        mode: Game mode ("PvP" or "PvE")
        eventPit: ISO timestamp when the game started
    """
    session_id: str
    lobby_id: UUID
    # game_id: str
    # player_ids: list[str]
    # mode: str  # "PvP" or "PvE"


@dataclass
class GameEndedEvent(DomainEvent):
    """
    Event published when a game session ends.

    Sent by game services to notify the platform of match results.
    The platform uses this for:
    - Updating player statistics
    - Closing the session
    - Triggering post-game workflows (rewards, rankings, etc.)

    Routing:
        Queue: game.ended
        Routing Key: sdk.game.ended.v1

    Attributes:
        sessionId: Unique identifier for the game session
        lobbyId: UUID of the lobby that created this session
        gameId: Identifier for the game type
        winnerId: Player ID of the winner (None for draws)
        reason: How the game ended ("win", "draw", "forfeit", "disconnect")
        finalState: Optional game-specific final state data
        eventPit: ISO timestamp when the game ended
    """
    session_id: str
    lobby_id: UUID
    # game_id: str
    # winner_id: Optional[str]
    # reason: str  # "win", "draw", "forfeit", "disconnect"
    # final_state: Optional[Dict[str, Any]] = None


# ============================================================================
# INCOMING EVENTS (Platform → Game)
# ============================================================================

@dataclass
class LobbyOfOnePlayerIsReadyToPlayPveEvent(DomainEvent):
    """
    Event received when a PvE (Player vs Environment) lobby is ready.

    Sent by the platform's matchmaking system when a player wants to play
    against AI. The game service should:
    1. Create a new session
    2. Assign the player to a symbol/side
    3. Initialize AI opponent
    4. Publish GameStartedEvent

    Routing:
        Queue: lobby.ready.pve (or game-specific queue)
        Routing Key: platform.lobby.pve.ready.v1

    Attributes:
        lobbyId: UUID of the ready lobby
        gameId: Identifier for the game type
        playerId: Player ID of the human player
        playerName: Display name of the player
        aiDifficulty: Requested AI difficulty ("easy", "medium", "hard")
        sessionId: Pre-generated session ID from platform
        eventPit: ISO timestamp when lobby became ready
    """
    lobby_id: UUID
    player_id: str
    ai_mode: str


@dataclass
class LobbyOfTwoPlayersIsReadyToPlayPvPEvent(DomainEvent):
    """
    Event received when a PvP (Player vs Player) lobby is ready.

    Sent by the platform's matchmaking system when two players are matched.
    The game service should:
    1. Create a new session
    2. Assign players to symbols/sides
    3. Determine starting player
    4. Publish GameStartedEvent

    Routing:
        Queue: lobby.ready.pvp (or game-specific queue)
        Routing Key: platform.lobby.pvp.ready.v1

    Attributes:
        lobbyId: UUID of the ready lobby
        gameId: Identifier for the game type
        player1Id: First player's ID
        player1Name: First player's display name
        player2Id: Second player's ID
        player2Name: Second player's display name
        sessionId: Pre-generated session ID from platform
        eventPit: ISO timestamp when lobby became ready
    """
    lobby_id: UUID
    player1_idp_id: str
    player2_idp_id: str


# ============================================================================
# ML PLAYER EVENTS
# ============================================================================

@dataclass
class MLMoveRequestEvent(DomainEvent):
    """
    Event to request ML move prediction from ML Player Worker.

    Published by game when ML player needs to make a move.

    Routing:
        Exchange: sillyseal.events
        Routing Key: game.ml.move.request.v1
        Queue: ml_move_requests

    Attributes:
        session_id: Game session identifier
        game_state: Current game state with board and turn info
        model_type: ML model to use ("catboost", "xgboost", or "decision_tree")
        event_pit: ISO timestamp when request was made
    """
    session_id: str
    game_state: Dict[str, Any]
    model_type: str = "catboost"


@dataclass
class MLMoveResponseEvent(DomainEvent):
    """
    Event with ML move prediction result from ML Player Worker.

    Published by ML Player Worker after getting prediction from ML API.

    Routing:
        Exchange: sillyseal.events
        Routing Key: game.ml.move.response.v1

    Attributes:
        session_id: Game session identifier
        predicted_move: Predicted cell index (0-8 for tic-tac-toe)
        predicted_position: Predicted position as {"row": int, "col": int}
        probability: Confidence probability (0.0-1.0)
        model_type: ML model that made the prediction
        event_pit: ISO timestamp when response was sent
    """
    session_id: str
    predicted_move: int
    predicted_position: Dict[str, int]
    probability: float
    model_type: str


# ============================================================================
# EVENT UTILITIES
# ============================================================================

def parse_event(json_str: str, event_type: str) -> DomainEvent:
    """
    Parse a JSON event string into the appropriate event class.

    Args:
        json_str: JSON string containing event data
        event_type: Type of event ("game_started", "game_ended", "lobby_pve_ready", "lobby_pvp_ready")

    Returns:
        Parsed event instance

    Raises:
        ValueError: If event_type is unknown
    """
    event_map = {
        "game_started": GameStartedEvent,
        "game_ended": GameEndedEvent,
        "lobby_pve_ready": LobbyOfOnePlayerIsReadyToPlayPveEvent,
        "lobby_pvp_ready": LobbyOfTwoPlayersIsReadyToPlayPvPEvent,
        "ml_move_request": MLMoveRequestEvent,
        "ml_move_response": MLMoveResponseEvent,
    }

    if event_type not in event_map:
        raise ValueError(f"Unknown event type: {event_type}")

    event_class = event_map[event_type]
    return event_class.from_json(json_str)


def create_game_started_event(
    session_id: str,
    lobby_id: UUID,
    game_id: str,
    player_ids: list[str],
    mode: str,
    event_pit: Optional[str] = None
) -> GameStartedEvent:
    """
    Convenience factory for GameStartedEvent.

    Example:
        event = create_game_started_event(
            session_id="session-123",
            lobby_id=UUID("12345678-1234-5678-1234-567812345678"),
            game_id="tic-tac-toe",
            player_ids=["player1", "player2"],
            mode="PvP"
        )
    """
    return GameStartedEvent(
        session_id=session_id,
        lobby_id=lobby_id,
        # gameId=game_id,
        # playerIds=player_ids,
        # mode=mode,
        event_pit=event_pit or _format_event_timestamp()
    )


def create_game_ended_event(
    session_id: str,
    lobby_id: UUID,
    game_id: str,
    winner_id: Optional[str],
    reason: str,
    final_state: Optional[Dict[str, Any]] = None,
    event_pit: Optional[str] = None
) -> GameEndedEvent:
    """
    Convenience factory for GameEndedEvent.

    Example:
        event = create_game_ended_event(
            session_id="session-123",
            lobby_id=UUID("12345678-1234-5678-1234-567812345678"),
            game_id="tic-tac-toe",
            winner_id="player1",
            reason="win",
            final_state={"board": [["X", "O", ...], ...]}
        )
    """
    return GameEndedEvent(
        session_id=session_id,
        lobby_id=lobby_id,
        # game_id=game_id,
        # winnerId=winner_id,
        # reason=reason,
        # finalState=final_state,
        event_pit=event_pit or _format_event_timestamp()
    )


def _format_event_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Format event timestamp in a Java LocalDateTime-compatible form.

    Produces an ISO_LOCAL_DATE_TIME string with millisecond precision and no timezone offset.
    """
    dt = dt or datetime.now(timezone.utc)
    utc_without_tz = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return utc_without_tz.isoformat(timespec="milliseconds")
