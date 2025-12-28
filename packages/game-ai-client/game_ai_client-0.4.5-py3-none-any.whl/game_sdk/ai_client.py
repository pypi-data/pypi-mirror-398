from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Protocol, TypeVar, Union
from .mcts import (
    MCTSStrategy,
    GameEnv,
    SelectionStrategy,
    ExpansionStrategy,
    SimulationStrategy,
    BackpropagationStrategy,
    RandomSimulationStrategy,
    get_simulation_strategy,
    get_selection_strategy,
    get_backpropagation_strategy,
    get_expansion_strategy,
)
# Lazy import to avoid circular dependency - DynamicMCTSAgent imports from this module
# from .dynamic_mcts_agent import DynamicMCTSAgent
from .utils import build_generic_state

from .client import GameClient

try:
    from .rabbitmq import RabbitMQ
except ImportError:
    RabbitMQ = None

State = Dict[str, Any]
Move = Dict[str, Any]
ApplyMoveFn = Callable[[State, Move], State]

class TurnBasedGame(ABC):
    """
    Generic interface that any turn-based game must implement.

    This interface now matches the GameEnv Protocol, meaning any TurnBasedGame
    can be used directly with MCTS without adapters!

    Subclasses must implement:
    - current_player() - Returns current player index (0, 1, etc.)
    - get_legal_actions() - Returns list of legal moves
    - is_game_over() - Returns True if game ended
    - game_result() - Returns outcome from current player's perspective
    - move(action) - Applies move and returns new game state

    Subclasses automatically get:
    - ai_vs_ai_difficulty_selection() for AI vs AI games with different difficulties
    """

    @abstractmethod
    def current_player(self) -> int:
        """
        Return the index of the player whose turn it is.
        Typically 0 or 1 for two-player games.
        """
        ...

    @abstractmethod
    def get_legal_actions(self) -> List[Move]:
        """Return list of legal moves in the current state."""
        ...

    @abstractmethod
    def is_game_over(self) -> bool:
        """Return True if the game has ended."""
        ...

    @abstractmethod
    def game_result(self) -> float:
        """
        Return game result from the perspective of the current player.
        Typically 1.0 (win), 0.0 (draw), or -1.0 (loss).
        """
        ...

    @abstractmethod
    def move(self, action: Move) -> "TurnBasedGame":
        """
        Apply an action and return a NE
        W game state.
        """
        ...

    def get_heuristic(self) -> Optional[float]:
        """
        Optional: Return a heuristic evaluation of the current game state.

        The heuristic should typically be from the perspective of the current player,
        where positive values are favorable and negative values are unfavorable.
        However, the exact interpretation depends on your game's implementation.

        This method is used by the SDK for logging move quality when integrated
        with GameClient. If not implemented (returns None), no heuristic will be logged.

        Returns:
            float: Heuristic value for the current state, or None if not implemented

        Example:
            def get_heuristic(self) -> Optional[float]:
                # Material advantage in a board game
                return self.count_player_pieces(0) - self.count_player_pieces(1)
        """
        return None

    def ai_vs_ai_difficulty_selection(
        self,
        difficulty1: str,
        difficulty2: str,
        state_to_game_fn: Callable[[State], "TurnBasedGame"],
        game_to_state_fn: Callable[["TurnBasedGame", State], State],
        game_id: str = "game",
        verbose: bool = True,
        client: Optional["GameClient"] = None,
        match_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Play a complete AI vs AI game with different difficulty levels.

        This method allows you to run a full game where two AI agents with different
        difficulty settings play against each other using a single agent instance.

        Args:
            difficulty1: Difficulty for player 1 ("easy", "medium", or "hard")
            difficulty2: Difficulty for player 2 ("easy", "medium", or "hard")
            state_to_game_fn: Function to convert state dict to game object
            game_to_state_fn: Function to convert game object to state dict
            game_id: ID of the game (default: "game")
            verbose: Whether to print game progress (default: True)
            client: Optional GameClient for logging moves with heuristic values
            match_id: Optional match ID (if provided, uses existing match; if None, creates new match)
            metadata: Optional metadata dict to include when creating a new match (ignored if match_id provided)

        Returns:
            Dictionary with game results containing:
            - winner: Winning player symbol or None for draw
            - move_count: Total number of moves played
            - move_history: List of move records with player info and positions
            - final_game: Final game state object

        Example:
            # Create initial game
            game = TicTacToeGame(empty_board, players, "X")

            # Play AI vs AI with different difficulties
            result = game.ai_vs_ai_difficulty_selection(
                difficulty1="easy",
                difficulty2="hard",
                state_to_game_fn=state_to_game_tictactoe,
                game_to_state_fn=game_to_state_tictactoe,
                game_id="tictactoe"
            )

            print(f"Winner: {result['winner']}")
            print(f"Moves: {result['move_count']}")
        """
        # Create the apply_move function for the agent
        def apply_move_fn(state: State, move: Move) -> State:
            game = state_to_game_fn(state)
            next_game = game.move(move)
            return game_to_state_fn(next_game, state)

        # Lazy import to avoid circular dependency
        from .dynamic_mcts_agent import DynamicMCTSAgent

        # Create agent with apply_move function
        agent = DynamicMCTSAgent(apply_move_fn)

        # Assume the game has these attributes (duck typing)
        # If your game doesn't have these, you'll need to adapt
        players = getattr(self, 'players', [
            {"id": "P1", "symbol": "Player1"},
            {"id": "P2", "symbol": "Player2"}
        ])

        # Assign difficulties to players
        players_with_difficulty = [
            {**players[0], "difficulty": difficulty1},
            {**players[1], "difficulty": difficulty2}
        ]

        current_game = self
        move_history = []
        move_count = 0
        current_player_idx = 0

        # Start match if client provided and match_id not provided
        if client is not None and match_id is None:
            match_metadata = metadata or {}
            match_metadata.update({
                "difficulty1": difficulty1,
                "difficulty2": difficulty2,
                "ai_vs_ai": True
            })
            match_id = client.start_match(players_with_difficulty, metadata=match_metadata)

        if verbose:
            print("=" * 70)
            print(f"AI vs AI Game: {difficulty1.upper()} vs {difficulty2.upper()}")
            if match_id:
                print(f"Match ID: {match_id}")
            print("=" * 70)
            print()

        # Game loop
        while not current_game.is_game_over():
            current_player = players_with_difficulty[current_player_idx]
            current_difficulty = current_player["difficulty"]

            # Get legal moves
            legal_moves = current_game.get_legal_actions()
            if not legal_moves:
                break

            # Build current state
            current_player_symbol = getattr(current_game, 'current_player_symbol',
                                           players_with_difficulty[current_player_idx]["symbol"])

            state = game_to_state_fn(current_game, {
                "game_id": game_id,
                "players": players_with_difficulty,
                "turn_index": current_player_idx,
                "move_count": move_count,
                "is_terminal": False,
                "legal_moves": legal_moves
            })

            # Select move at current difficulty
            if verbose:
                print(f"Move {move_count + 1}: {current_player['id']} at '{current_difficulty}' difficulty")

            move = agent.select_move_at_difficulty(state, current_difficulty)

            if not move:
                if verbose:
                    print("  No valid move found!")
                break

            if verbose:
                pos = move.get("position", move)
                print(f"  Selected: {pos}")

            # Record move
            move_history.append({
                "player": current_player["id"],
                "move": move,
                "difficulty": current_difficulty
            })

            # Apply move
            current_game = current_game.move(move)
            move_count += 1

            # Log move to GameClient if provided
            if client is not None and match_id is not None:
                # Build state after the move
                state_after = game_to_state_fn(current_game, {
                    "game_id": game_id,
                    "players": players_with_difficulty,
                    "turn_index": current_player_idx,
                    "move_count": move_count,
                    "is_terminal": current_game.is_game_over(),
                    "legal_moves": current_game.get_legal_actions() if not current_game.is_game_over() else []
                })

                # Get heuristic from the game (if implemented)
                h_value = current_game.get_heuristic()

                # Log the move with heuristic
                client.log_move(
                    match_id=match_id,
                    state=state_after,
                    move=move,
                    heuristic_value=h_value
                )

            # Switch players
            current_player_idx = 1 - current_player_idx

            if verbose:
                print()

        # Determine winner
        winner = None
        if current_game.is_game_over():
            result = current_game.game_result()
            if result == 1:
                # Current player to move won (rare - means last player's move set up current player's win)
                winner_idx = current_player_idx
                winner = players_with_difficulty[winner_idx].get("symbol")
            elif result == -1:
                # Current player to move lost, so the previous player (who just moved) won
                winner_idx = 1 - current_player_idx
                winner = players_with_difficulty[winner_idx].get("symbol")
            # result == 0 means draw, winner stays None

        if verbose:
            print("=" * 70)
            print("Game Over!")
            print("=" * 70)
            if winner:
                winner_player = next(p for p in players_with_difficulty
                                   if p.get("symbol") == winner)
                print(f"Winner: {winner_player['id']} ({winner}) at '{winner_player['difficulty']}' difficulty")
            else:
                print("Result: Draw")
            print(f"Total moves: {move_count}")
            print()

        # End match if client provided
        if client is not None and match_id is not None:
            # Build final state for logging
            final_state = game_to_state_fn(current_game, {
                "game_id": game_id,
                "players": players_with_difficulty,
                "turn_index": current_player_idx,
                "move_count": move_count,
                "is_terminal": True,
                "legal_moves": []
            })

            # Determine result string
            result_str = "DRAW"
            if winner:
                winner_player = next((p for p in players_with_difficulty if p.get("symbol") == winner), None)
                if winner_player:
                    result_str = f"{winner_player.get('id')}_WIN"

            client.end_match(match_id, result_str, final_state)

        result_dict = {
            "winner": winner,
            "move_count": move_count,
            "move_history": move_history,
            "final_game": current_game
        }

        if match_id:
            result_dict["match_id"] = match_id

        return result_dict


class StatefulGameAdapter:
    """
    Adapter that wraps a dict-based game state to satisfy the GameEnv Protocol.

    This is for backward compatibility with code that uses dict-based states.
    For new code, use TurnBasedGame objects directly instead.

    The state dict must contain:
    - turn_index: Current player index
    - legal_moves: List of legal moves
    - is_terminal: Whether game is over
    - result: Dict mapping player IDs to outcomes (for terminal states)
    - players: List of player dicts with "id" field
    """
    def __init__(self, state: State, apply_move_fn: ApplyMoveFn):
        self._state = state
        self._apply_move_fn = apply_move_fn

    def current_player(self) -> int:
        return self._state["turn_index"]

    def get_legal_actions(self) -> List[Move]:
        moves = self._state.get("legal_moves")
        if moves is None:
            raise ValueError("state['legal_moves'] is required for MCTS.")
        # Return a copy to prevent MCTS from modifying the original state dict
        return list(moves)

    def move(self, action: Move) -> "StatefulGameAdapter":
        next_state = self._apply_move_fn(self._state, action)
        return StatefulGameAdapter(next_state, self._apply_move_fn)

    def is_game_over(self) -> bool:
        return bool(self._state.get("is_terminal", False))

    def game_result(self) -> float:
        """Return result from current player's perspective."""
        result = self._state.get("result")
        if result is None:
            return 0.0
        players = self._state["players"]
        current_player_idx = self._state["turn_index"]
        player_id = players[current_player_idx]["id"]
        return float(result.get(player_id, 0.0))


# Deprecated: Use StatefulGameAdapter or TurnBasedGame directly
class GenericGameEnv:
    """
    DEPRECATED: This class is deprecated and will be removed in a future version.
    Use StatefulGameAdapter for dict-based states, or TurnBasedGame objects directly.
    """
    def __init__(self, apply_move_fn: ApplyMoveFn):
        import warnings
        warnings.warn(
            "GenericGameEnv is deprecated. Use StatefulGameAdapter for dict-based states, "
            "or pass TurnBasedGame objects directly to MCTS.",
            DeprecationWarning
        )
        self.apply_move_fn = apply_move_fn


class AIGameClient(GameClient):
    """
    Unified client:
      - All GameClient methods (start_match, log_move, end_match, ...)
      - Plus MCTS AI:
          send_state(match_id, state)
          best_move(match_id, iterations=1000)
    """

    def __init__(
        self,
        game_id: str,
        api_key: str,
        apply_move_fn: ApplyMoveFn,
        base_url: str = "http://localhost:8000",
        exploration_c: float = 1.4,
        selection_strategy: Optional[Union[str, SelectionStrategy]] = None,
        expansion_strategy: Optional[Union[str, ExpansionStrategy]] = None,
        simulation_strategy: Optional[Union[str, SimulationStrategy]] = None,
        backpropagation_strategy: Optional[Union[str, BackpropagationStrategy]] = None,
        move_evaluator: Optional[Callable] = None,
        queue_name: Optional[str] = None,
        epsilon: float = 0.0,
    ):
        message_bus = None
        if RabbitMQ is not None:
            try:
                message_bus = RabbitMQ()
                print("[AIGameClient] Connected to RabbitMQ.")
            except Exception as e:
                print(
                     f"[AIGameClient] WARNING: could not connect to RabbitMQ ({e}). "
                    "Falling back to stdout logging."
                )
        else:
            # RabbitMQ module not available (pika not installed)
            pass

        super().__init__(game_id=game_id, api_key=api_key, base_url=base_url, message_bus=message_bus)
        self._queue_name = queue_name or "game_events"

        # Store apply_move_fn for wrapping dict states
        self._apply_move_fn = apply_move_fn

        # Resolve string-based strategies to instances
        resolved_selection: Optional[SelectionStrategy] = None
        if isinstance(selection_strategy, str):
            resolved_selection = get_selection_strategy(selection_strategy, exploration_c)
        else:
            resolved_selection = selection_strategy

        resolved_simulation: Optional[SimulationStrategy] = None
        if isinstance(simulation_strategy, str):
            resolved_simulation = get_simulation_strategy(simulation_strategy, move_evaluator=move_evaluator)
            # RAVE needs move tracking enabled
            if isinstance(resolved_simulation, RandomSimulationStrategy):
                if isinstance(resolved_selection, str) and resolved_selection.lower() == "rave":
                    resolved_simulation.track_moves = True
                elif hasattr(resolved_selection, '__class__') and 'RAVE' in resolved_selection.__class__.__name__:
                    resolved_simulation.track_moves = True
        else:
            resolved_simulation = simulation_strategy

        resolved_backprop: Optional[BackpropagationStrategy] = None
        if isinstance(backpropagation_strategy, str):
            resolved_backprop = get_backpropagation_strategy(backpropagation_strategy)
        else:
            resolved_backprop = backpropagation_strategy

        resolved_expansion: Optional[ExpansionStrategy] = None
        if isinstance(expansion_strategy, str):
            resolved_expansion = get_expansion_strategy(expansion_strategy)
        else:
            resolved_expansion = expansion_strategy

        # Plug in MCTSStrategy with optional custom phase strategies
        self._mcts = MCTSStrategy(
            selection_strategy=resolved_selection,
            expansion_strategy=resolved_expansion,
            simulation_strategy=resolved_simulation,
            backpropagation_strategy=resolved_backprop,
            exploration_c=exploration_c,
        )

        # Epsilon-greedy: probability of making a random move instead of MCTS
        # 0.0 = always use MCTS (default), 0.5 = 50% random for "easy" mode
        self._epsilon = epsilon

        # match_id -> last state
        self._states: Dict[str, State] = {}

    def send_state(self, match_id: str, state: State) -> None:
        """
        Store the latest game state for a match.
        The state must be in the generic format produced by build_generic_state.
        """
        if state["game_id"] != self.game_id:
            raise ValueError(
                f"State game_id={state['game_id']} does not match client.game_id={self.game_id}"
            )
        self._states[match_id] = state

    def best_move(self, match_id: str, iterations: int = 1000) -> Optional[Move]:
        """
        Run MCTS from the last state sent for this match and return
        one of the moves from state['legal_moves'].

        If epsilon > 0, uses epsilon-greedy: random move with probability epsilon,
        MCTS move with probability (1 - epsilon).
        """
        state = self._states.get(match_id)
        if state is None:
            raise KeyError(f"No state stored for match_id={match_id}")

        # Wrap dict state in adapter to satisfy GameEnv Protocol
        game_adapter = StatefulGameAdapter(state, self._apply_move_fn)

        if game_adapter.is_game_over():
            return None

        # Epsilon-greedy: make random move with probability epsilon
        if self._epsilon > 0:
            import random
            if random.random() < self._epsilon:
                legal_moves = self._env.legal_moves(state)
                if legal_moves:
                    return random.choice(legal_moves)

        # Uses strategy-based MCTS under the hood
        return self._mcts.search(root_state=game_adapter, iterations=iterations)

GameT = TypeVar("GameT", bound=TurnBasedGame)


def make_apply_move_fn(
    state_to_game: Callable[[State], GameT],
    game_to_state: Callable[[GameT, State], State],
) -> ApplyMoveFn:
    """
    Build an ApplyMoveFn from two small adapters:

      - state_to_game(state) -> Game
      - game_to_state(game, previous_state) -> new State

    Works for ANY game that implements TurnBasedGame.
    """

    def apply_move(state: State, move: Move) -> State:
        # 1) Convert generic state dict into a concrete game object
        game = state_to_game(state)

        # 2) Let the game apply the move using its own rules
        next_game = game.move(move)

        # 3) Convert the updated game back into generic JSON-style state
        new_state = game_to_state(next_game, state)
        return new_state

    return apply_move
