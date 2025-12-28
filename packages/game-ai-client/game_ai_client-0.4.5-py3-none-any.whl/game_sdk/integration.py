"""
Lightweight integration contract and helpers for wiring any game into the SDK.

Games provide a small spec (create_game, state_to_game, game_to_state) and we
wrap it in a generic adapter so callers (self-play, workers, etc.) do not need
game-specific adapters.
"""
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from .ai_client import ApplyMoveFn, TurnBasedGame, make_apply_move_fn

State = Dict[str, Any]
Move = Dict[str, Any]


@dataclass
class GameIntegrationSpec:
    """
    Minimal contract a game should expose to work with the SDK.
      - create_game: produce a fresh game object
      - state_to_game: convert generic state -> game object
      - game_to_state: convert game object -> generic state (uses prev_state metadata)
      - default_players: optional factory for players list (ids + symbols, etc.)
      - move_evaluator: optional hook for heuristic simulations
    """
    create_game: Callable[[], TurnBasedGame]
    state_to_game: Callable[[State], TurnBasedGame]
    game_to_state: Callable[[TurnBasedGame, State], State]
    default_players: Optional[Callable[[], List[Dict[str, Any]]]] = None
    move_evaluator: Optional[Callable[[State, List[Move], Any], Any]] = None


class GenericGameAdapter:
    """
    Game-agnostic adapter built from a GameIntegrationSpec.
    Exposes the trio expected by SelfPlayRunner:
      - create_game()
      - apply_move(game, move)
      - build_state(game, players, turn_index, move_count)
    """

    def __init__(self, spec: GameIntegrationSpec, game_id: str):
        self.spec = spec
        self.game_id = game_id
        # State-level apply_move used by AIGameClient/MCTS
        self._state_apply_move: ApplyMoveFn = make_apply_move_fn(
            state_to_game=spec.state_to_game,
            game_to_state=spec.game_to_state,
        )

    def create_game(self) -> TurnBasedGame:
        return self.spec.create_game()

    def apply_move(self, game: TurnBasedGame, move: Move) -> TurnBasedGame:
        # Delegate to the game's own move implementation
        return game.move(move)

    def build_state(
        self,
        game: TurnBasedGame,
        players: List[Dict[str, Any]],
        current_player_idx: int,
        move_count: int,
    ) -> State:
        """
        Convert a game object into the generic state format expected by the SDK.
        """
        prev_state = {
            "game_id": self.game_id,
            "players": players,
            "turn_index": current_player_idx,
            "extra": {"move_count": move_count},
        }
        state = self.spec.game_to_state(game, prev_state)

        # Ensure required fields are present
        state.setdefault("game_id", self.game_id)
        state.setdefault("players", players)
        state.setdefault("turn_index", current_player_idx)
        state.setdefault("extra", {"move_count": move_count})
        state["extra"].setdefault("move_count", move_count)

        # CRITICAL: Ensure legal_moves is populated if game is not terminal
        # This is required for MCTS to function properly
        if "legal_moves" not in state:
            # If game_to_state didn't provide legal_moves, get them directly from the game
            if not game.is_game_over():
                state["legal_moves"] = game.get_legal_actions()
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"legal_moves was missing from state for non-terminal game. "
                    f"Retrieved {len(state['legal_moves'])} moves from game.get_legal_actions(). "
                    f"Consider updating game_to_state() to include legal_moves."
                )
            else:
                state["legal_moves"] = []
        elif not state.get("is_terminal", False) and not state["legal_moves"]:
            # legal_moves exists but is empty for non-terminal game - populate it from the game
            if not game.is_game_over():
                state["legal_moves"] = game.get_legal_actions()
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"legal_moves was empty for non-terminal game. "
                    f"Retrieved {len(state['legal_moves'])} moves from game.get_legal_actions(). "
                    f"This may indicate a bug in game_to_state()."
                )
            else:
                state["legal_moves"] = []

        return state

    def default_players(self) -> Optional[List[Dict[str, Any]]]:
        if self.spec.default_players:
            return self.spec.default_players()
        return None

    def state_apply_move_fn(self) -> ApplyMoveFn:
        """
        Apply-move function at the generic state level (state, move) -> new state.
        Used by MCTS / AIGameClient to simulate moves.
        """
        return self._state_apply_move


def load_integration(module_path: str, attr: str = "GAME_INTEGRATION") -> GameIntegrationSpec:
    """
    Import a GameIntegrationSpec from a module.
      - Primary: module.<attr> (default: GAME_INTEGRATION)
      - Fallback: module.create_integration()
    """
    import importlib

    module = importlib.import_module(module_path)

    if hasattr(module, attr):
        spec = getattr(module, attr)
        if isinstance(spec, GameIntegrationSpec):
            return spec
        raise TypeError(f"{module_path}.{attr} is not a GameIntegrationSpec")

    if hasattr(module, "create_integration"):
        spec = module.create_integration()
        if isinstance(spec, GameIntegrationSpec):
            return spec
        raise TypeError(f"{module_path}.create_integration() did not return GameIntegrationSpec")

    raise AttributeError(f"{module_path} does not expose {attr} or create_integration()")
