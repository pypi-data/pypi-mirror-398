"""
Game Registration Helpers for GenericImplDemo SDK

This module provides utilities to help game developers properly register
their games for self-play, tournaments, and AI integration.
"""

from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass
from .integration import GameIntegrationSpec, TurnBasedGame


def register_game(
    game_name: str,
    create_game: Callable[[], TurnBasedGame],
    state_to_game: Callable[[Dict[str, Any]], TurnBasedGame],
    game_to_state: Callable[[TurnBasedGame, Dict[str, Any]], Dict[str, Any]],
    default_players: Optional[Callable[[], List[Dict[str, Any]]]] = None,
    move_evaluator: Optional[Callable] = None,
) -> GameIntegrationSpec:
    """
    Register a game with the GenericImplDemo SDK.

    This creates a GameIntegrationSpec that makes your game compatible with:
    - Self-play workers
    - Tournament systems
    - AI training pipelines
    - MCTS agents

    Args:
        game_name: Name of your game (e.g., "tictactoe", "chess")
        create_game: Function that creates a new game instance
        state_to_game: Function to convert generic state dict → game object
        game_to_state: Function to convert game object → generic state dict
        default_players: Optional function that returns default player config
        move_evaluator: Optional heuristic for move evaluation

    Returns:
        GameIntegrationSpec that can be exported as GAME_INTEGRATION

    Example:
        ```python
        from game_sdk import register_game
        from my_game import MyGame

        def create_game():
            return MyGame()

        def state_to_game(state):
            return MyGame.from_state(state)

        def game_to_state(game, prev_state):
            return {
                "game_id": prev_state["game_id"],
                "board": game.board,
                "players": game.players,
                "turn_index": game.current_player_idx,
                "legal_moves": game.get_legal_actions(),
                ...
            }

        # Register the game
        GAME_INTEGRATION = register_game(
            game_name="my_game",
            create_game=create_game,
            state_to_game=state_to_game,
            game_to_state=game_to_state
        )
        ```

    Important:
        - game_to_state MUST include "legal_moves" for non-terminal states
        - Use build_generic_state() utility to ensure correct format
        - Export as GAME_INTEGRATION in your ai_integration.py module
    """
    # Validate game_name
    if not game_name or not isinstance(game_name, str):
        raise ValueError(f"game_name must be a non-empty string, got: {game_name}")

    # Create the integration spec
    spec = GameIntegrationSpec(
        create_game=create_game,
        state_to_game=state_to_game,
        game_to_state=game_to_state,
        default_players=default_players,
        move_evaluator=move_evaluator,
    )

    # Store metadata
    spec._game_name = game_name  # For debugging/logging

    return spec


def validate_integration(spec: GameIntegrationSpec, game_name: str = None) -> Dict[str, Any]:
    """
    Validate that a GameIntegrationSpec is correctly implemented.

    This checks:
    - All required functions are present
    - Functions have correct signatures
    - State format includes required fields
    - legal_moves is populated for non-terminal states

    Args:
        spec: The GameIntegrationSpec to validate
        game_name: Optional game name for better error messages

    Returns:
        Validation report with issues and warnings

    Example:
        ```python
        from game_sdk import validate_integration
        from ai_integration import GAME_INTEGRATION

        report = validate_integration(GAME_INTEGRATION, "tictactoe")
        if report["errors"]:
            print("Errors:", report["errors"])
        if report["warnings"]:
            print("Warnings:", report["warnings"])
        ```
    """
    report = {
        "game_name": game_name or getattr(spec, "_game_name", "unknown"),
        "valid": True,
        "errors": [],
        "warnings": [],
    }

    # Check required functions
    if not spec.create_game:
        report["errors"].append("Missing create_game function")
        report["valid"] = False

    if not spec.state_to_game:
        report["errors"].append("Missing state_to_game function")
        report["valid"] = False

    if not spec.game_to_state:
        report["errors"].append("Missing game_to_state function")
        report["valid"] = False

    # Try to create a game and validate state format
    if spec.create_game and spec.game_to_state:
        try:
            game = spec.create_game()

            # Check if game has required methods
            if not hasattr(game, "get_legal_actions"):
                report["errors"].append(
                    "Game object must have get_legal_actions() method"
                )
                report["valid"] = False

            if not hasattr(game, "is_game_over"):
                report["errors"].append(
                    "Game object must have is_game_over() method"
                )
                report["valid"] = False

            if not hasattr(game, "move"):
                report["errors"].append(
                    "Game object must have move(action) method"
                )
                report["valid"] = False

            # Try to build a state
            if hasattr(game, "get_legal_actions") and hasattr(game, "is_game_over"):
                prev_state = {
                    "game_id": "test",
                    "players": [{"id": "P1"}, {"id": "P2"}],
                    "turn_index": 0,
                    "extra": {"move_count": 0},
                }

                state = spec.game_to_state(game, prev_state)

                # Validate state format
                required_fields = ["game_id", "players", "turn_index"]
                for field in required_fields:
                    if field not in state:
                        report["errors"].append(
                            f"game_to_state must include '{field}' in state"
                        )
                        report["valid"] = False

                # Check legal_moves
                if not game.is_game_over():
                    if "legal_moves" not in state:
                        report["errors"].append(
                            "game_to_state must include 'legal_moves' for non-terminal states"
                        )
                        report["valid"] = False
                    elif not state["legal_moves"]:
                        report["warnings"].append(
                            "legal_moves is empty for non-terminal game - may be a bug"
                        )

        except Exception as e:
            report["errors"].append(f"Failed to validate game creation: {e}")
            report["valid"] = False

    # Check optional features
    if not spec.default_players:
        report["warnings"].append(
            "No default_players function - self-play will need explicit player config"
        )

    return report


def create_ai_integration_template(game_name: str) -> str:
    """
    Generate a template ai_integration.py file for a new game.

    Args:
        game_name: Name of the game (e.g., "chess", "checkers")

    Returns:
        String containing template code

    Example:
        ```python
        from game_sdk import create_ai_integration_template

        template = create_ai_integration_template("mygame")
        with open("ai_integration.py", "w") as f:
            f.write(template)
        ```
    """
    game_class = f"{game_name.capitalize()}Game"

    template = f'''"""
AI Integration module for {game_name.capitalize()} with Game AI Client SDK.
Contains adapters to convert between generic SDK state and {game_class} instances.
"""

from typing import Dict, Any, List
from game_sdk import register_game, build_generic_state
from game_sdk.integration import GameIntegrationSpec
from {game_name}_game import {game_class}


def state_to_game_{game_name}(state: Dict[str, Any]) -> {game_class}:
    """
    Convert generic SDK state to {game_class} instance.

    Args:
        state: Generic state dictionary

    Returns:
        {game_class} instance
    """
    # TODO: Implement conversion from state dict to game object
    # Extract relevant fields from state and construct game
    raise NotImplementedError("Implement state_to_game_{game_name}")


def game_to_state_{game_name}(game: {game_class}, prev_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert {game_class} instance to generic SDK state.

    Args:
        game: {game_class} instance
        prev_state: Previous state (for game_id, move_count, etc.)

    Returns:
        Generic state dictionary
    """
    # Determine game status
    finished = game.is_game_over()

    # Compute legal moves (REQUIRED for MCTS)
    legal_moves = [] if finished else game.get_legal_actions()

    # Compute result if finished
    result_map = None
    if finished:
        # TODO: Map game result to player rewards
        # Example: {{"P1": 1.0, "P2": -1.0}} for P1 win
        pass

    # Build state using SDK utility
    return build_generic_state(
        game_id=prev_state["game_id"],
        board=game.board,  # TODO: Adapt to your game's board representation
        players=prev_state["players"],
        current_player_symbol=game.current_player_symbol,  # TODO: Adapt
        move_count=prev_state.get("extra", {{}}).get("move_count", 0) + 1,
        finished=finished,
        legal_moves=legal_moves,  # CRITICAL: Must be populated!
        result=result_map
    )


def default_players() -> List[Dict[str, Any]]:
    """Default two-player setup for self-play."""
    return [
        {{"id": "P1", "type": "ai_mcts", "symbol": "X"}},
        {{"id": "P2", "type": "ai_mcts", "symbol": "O"}},
    ]


def create_game() -> {game_class}:
    """Create a fresh game instance with default setup."""
    return {game_class}.create_initial_game(default_players())


# Register the game (REQUIRED for self-play discovery)
GAME_INTEGRATION = register_game(
    game_name="{game_name}",
    create_game=create_game,
    state_to_game=state_to_game_{game_name},
    game_to_state=game_to_state_{game_name},
    default_players=default_players,
)
'''

    return template


# Export all public APIs
__all__ = [
    "register_game",
    "validate_integration",
    "create_ai_integration_template",
]
