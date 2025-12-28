"""
Self-Play Runner Module

Provides a generic self-play runner that works with any game implementing GameEnv.
This module is the core of the SDK's self-play infrastructure.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from game_sdk.ai_client import AIGameClient
from game_sdk.integration import GameIntegrationSpec, GenericGameAdapter
import logging

logger = logging.getLogger(__name__)


@dataclass
class SelfPlayEpisodeConfig:
    """Configuration for a single self-play episode."""
    game_id: str
    episode_index: int
    player1_iterations: int = 1000
    player2_iterations: int = 1000
    player1_strategies: Optional[Dict[str, Any]] = None
    player2_strategies: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SelfPlayTrajectory:
    """Complete trajectory of a self-play episode."""
    episode_index: int
    match_id: str
    states: List[Dict[str, Any]] = field(default_factory=list)
    moves: List[Dict[str, Any]] = field(default_factory=list)
    rewards: List[float] = field(default_factory=list)
    winner: Optional[str] = None  # "P1_WIN", "P2_WIN", "DRAW"
    total_moves: int = 0


class SelfPlayRunner:
    """
    Generic self-play runner that works with any game implementing GameEnv.

    The runner orchestrates AI vs AI matches using MCTS and logs the complete
    game trajectory for ML training.

    Usage:
        runner = SelfPlayRunner(
            game_factory=lambda: TicTacToeGame(...),
            apply_move_fn=lambda game, move: game.move(move),
            build_state_fn=lambda game, players, idx: {...},
            game_id="tictactoe",
            api_key="selfplay-key",
            base_url="http://platform:8000"
        )

        config = SelfPlayEpisodeConfig(
            game_id="tictactoe",
            episode_index=0,
            player1_iterations=1000,
            player2_iterations=1000
        )

        trajectory = runner.run_episode(config)
    """

    def __init__(
        self,
        game_factory: Callable[[], Any],
        apply_move_fn: Callable[[Any, Dict], Any],
        build_state_fn: Callable[[Any, List[Dict], int], Dict],
        game_id: str,
        api_key: str = "selfplay",
        base_url: str = "http://localhost:8000",
        exploration_c: float = 1.4,
        selection_strategy: Optional[Any] = None,
        expansion_strategy: Optional[Any] = None,
        simulation_strategy: Optional[Any] = None,
        backpropagation_strategy: Optional[Any] = None,
        queue_name: Optional[str] = None,
        on_move: Optional[Callable] = None,
        on_episode_end: Optional[Callable] = None,
        state_to_game_fn: Optional[Callable[[Dict], Any]] = None,
        game_to_state_fn: Optional[Callable[[Any, Dict], Dict]] = None,
        integration_spec: Optional[GameIntegrationSpec] = None,
        default_players_fn: Optional[Callable[[], List[Dict[str, Any]]]] = None,
    ):
        """
        Initialize self-play runner with game-specific functions.

        Args:
            game_factory: Function that creates a new game instance
            apply_move_fn: Function that applies a move to a game state
            build_state_fn: Function that converts game to generic state format
            game_id: Unique identifier for the game type
            api_key: API key for authentication
            base_url: Base URL for platform backend
            exploration_c: UCB exploration constant
            selection_strategy: MCTS selection strategy
            expansion_strategy: MCTS expansion strategy
            simulation_strategy: MCTS simulation strategy
            backpropagation_strategy: MCTS backpropagation strategy
            queue_name: RabbitMQ queue name for events
            on_move: Optional callback invoked after each move
            on_episode_end: Optional callback invoked after episode completes
        """
        self.game_id = game_id
        self.game_factory = game_factory
        # If no game-level apply_move provided, assume TurnBasedGame.move exists
        self.apply_move_fn = apply_move_fn or (lambda game, move: game.move(move))
        self.build_state_fn = build_state_fn
        self.game_id = game_id
        self.api_key = api_key
        self.base_url = base_url
        self.exploration_c = exploration_c
        self.selection_strategy = selection_strategy or "rave"
        self.expansion_strategy = expansion_strategy or "progressive_widening"
        self.simulation_strategy = simulation_strategy or "random"
        self.backpropagation_strategy = backpropagation_strategy or "solver"
        self.queue_name = queue_name
        self.on_move = on_move
        self.on_episode_end = on_episode_end
        # Integration spec takes precedence over ad-hoc converters
        self.integration_spec = integration_spec
        if integration_spec:
            self.state_to_game_fn = integration_spec.state_to_game
            self.game_to_state_fn = integration_spec.game_to_state
            self._adapter = GenericGameAdapter(integration_spec, game_id)
        else:
            self.state_to_game_fn = state_to_game_fn
            self.game_to_state_fn = game_to_state_fn
            self._adapter = None
        if self._adapter and apply_move_fn is None:
            self.apply_move_fn = self._adapter.apply_move
        self.default_players_fn = (
            default_players_fn
            or (self._adapter.default_players if self._adapter else None)
        )

        self._state_apply_move_fn = None
        if self._adapter:
            self._state_apply_move_fn = self._adapter.state_apply_move_fn()
        elif self.state_to_game_fn and self.game_to_state_fn:
            # Build state-level apply_move for MCTS if converters are provided
            from game_sdk.ai_client import make_apply_move_fn

            self._state_apply_move_fn = make_apply_move_fn(
                self.state_to_game_fn, self.game_to_state_fn
            )

    def _create_ai_client(self, player_id: str, iterations: int, strategies: Optional[Dict] = None) -> AIGameClient:
        """
        Create an AI client with specified configuration.

        Args:
            player_id: Player identifier
            iterations: MCTS iterations per move
            strategies: Optional strategy overrides

        Returns:
            Configured AIGameClient instance
        """
        if strategies is None:
            strategies = {}
        state_apply_move_fn = self._state_apply_move_fn
        if state_apply_move_fn is None:
            def state_apply_move_fn(state_dict: Dict, move: Dict) -> Dict:
                logger.warning("No state converters provided - MCTS simulations will be inaccurate")
                return state_dict

        return AIGameClient(
            game_id=self.game_id,
            api_key=f"{self.api_key}-{player_id}",
            apply_move_fn=state_apply_move_fn,
            base_url=self.base_url,
            exploration_c=strategies.get("exploration_c", self.exploration_c),
            selection_strategy=strategies.get("selection", self.selection_strategy),
            expansion_strategy=strategies.get("expansion", self.expansion_strategy),
            simulation_strategy=strategies.get("simulation", self.simulation_strategy),
            backpropagation_strategy=strategies.get("backpropagation", self.backpropagation_strategy),
            queue_name=self.queue_name,
            move_evaluator=getattr(self.integration_spec, "move_evaluator", None) if self.integration_spec else None,
        )

    def _resolve_players(self, game_state: Any) -> List[Dict[str, Any]]:
        """
        Choose a players list for self-play in order of precedence:
          1) explicit default_players_fn (or spec-provided)
          2) players attribute on the game instance
          3) fallback X/O defaults (backward compatible)
        """
        if self.default_players_fn:
            players = self.default_players_fn()
            if players:
                return players

        if hasattr(game_state, "players"):
            players_attr = getattr(game_state, "players")
            if players_attr:
                return players_attr

        return [
            {"id": "P1", "type": "ai_mcts", "symbol": "X"},
            {"id": "P2", "type": "ai_mcts", "symbol": "O"},
        ]

    def _build_state(
        self,
        game_state: Any,
        players: List[Dict[str, Any]],
        current_player_idx: int,
        move_count: int,
    ) -> Dict[str, Any]:
        """
        Build a generic state for MCTS/logging. Supports both adapter-driven
        and legacy (game, players, idx) build_state_fn signatures.
        """
        if self._adapter:
            return self._adapter.build_state(game_state, players, current_player_idx, move_count)

        try:
            return self.build_state_fn(game_state, players, current_player_idx, move_count)
        except TypeError:
            # Legacy signature without move_count
            return self.build_state_fn(game_state, players, current_player_idx)

    def run_episode(self, config: SelfPlayEpisodeConfig) -> SelfPlayTrajectory:
        """
        Run a single self-play episode.

        Args:
            config: Episode configuration

        Returns:
            SelfPlayTrajectory with complete game history
        """
        logger.info(f"Starting self-play episode {config.episode_index} for game {config.game_id}")

        # Create two AI clients (one for each player)
        client_p1 = self._create_ai_client("P1", config.player1_iterations, config.player1_strategies)
        client_p2 = self._create_ai_client("P2", config.player2_iterations, config.player2_strategies)

        # Initialize game
        game_state = self.game_factory()
        players = self._resolve_players(game_state)

        # Start match
        metadata = {
            **config.metadata,
            "episode_index": config.episode_index,
            "self_play": True,
            "player1_iterations": config.player1_iterations,
            "player2_iterations": config.player2_iterations,
        }
        match_id = client_p1.start_match(players, metadata=metadata)

        # Initialize trajectory
        trajectory = SelfPlayTrajectory(
            episode_index=config.episode_index,
            match_id=match_id
        )

        # Game loop
        current_player_idx = 0
        move_count = 0

        while not game_state.is_game_over():
            # Build generic state
            state = self._build_state(game_state, players, current_player_idx, move_count)

            # Get move from appropriate AI
            client = client_p1 if current_player_idx == 0 else client_p2
            iterations = (config.player1_iterations
                         if current_player_idx == 0
                         else config.player2_iterations)

            # Send state and compute move
            client.send_state(match_id, state)
            move = client.best_move(match_id, iterations=iterations)

            if move is None:
                logger.error(f"No valid move returned for player {current_player_idx}")
                break

            # Apply move to game
            game_state = self.apply_move_fn(game_state, move)
            move_count += 1

            # Log move
            client.log_move(match_id, state, move)

            # Store in trajectory
            trajectory.states.append(state)
            trajectory.moves.append(move)

            # Callback hook
            if self.on_move:
                try:
                    self.on_move(
                        game_id=self.game_id,
                        episode_index=config.episode_index,
                        state=state,
                        move=move,
                        player_index=current_player_idx,
                        move_count=move_count
                    )
                except Exception as e:
                    logger.error(f"Error in on_move callback: {e}")

            # Switch player
            current_player_idx = 1 - current_player_idx

        # Game over - determine winner
        result = game_state.game_result()
        p1_id = players[0].get("id", "P1")
        p2_id = players[1].get("id", "P2")

        if result == 1:
            winner_idx = current_player_idx
            winner_id = players[winner_idx].get("id", f"P{winner_idx + 1}")
            winner = f"{winner_id}_WIN"
        elif result == -1:
            winner_idx = 1 - current_player_idx
            winner_id = players[winner_idx].get("id", f"P{winner_idx + 1}")
            winner = f"{winner_id}_WIN"
        else:
            winner_idx = None
            winner_id = None
            winner = "DRAW"

        trajectory.winner = winner
        trajectory.total_moves = move_count

        # Build final state
        final_state = self._build_state(game_state, players, current_player_idx, move_count)

        # End match
        if "result" not in final_state and winner_idx is not None:
            final_state["result"] = {
                players[0].get("id", "P1"): 1.0 if winner_idx == 0 else 0.0,
                players[1].get("id", "P2"): 1.0 if winner_idx == 1 else 0.0,
            }

        # Persist the human-readable outcome; per-player scores are included in final_state when available.
        client_p1.end_match(match_id, winner, final_state)

        logger.info(f"Episode {config.episode_index} completed: {winner} in {move_count} moves")

        # Callback hook
        if self.on_episode_end:
            try:
                self.on_episode_end(
                    game_id=self.game_id,
                    episode_index=config.episode_index,
                    trajectory=trajectory
                )
            except Exception as e:
                logger.error(f"Error in on_episode_end callback: {e}")

        return trajectory

    def run_episodes(self, base_config: SelfPlayEpisodeConfig, num_episodes: int):
        """
        Run multiple self-play episodes.

        Args:
            base_config: Base configuration for episodes
            num_episodes: Number of episodes to run

        Yields:
            SelfPlayTrajectory for each episode
        """
        logger.info(f"Starting {num_episodes} self-play episodes for game {base_config.game_id}")

        for i in range(num_episodes):
            config = SelfPlayEpisodeConfig(
                game_id=base_config.game_id,
                episode_index=i,
                player1_iterations=base_config.player1_iterations,
                player2_iterations=base_config.player2_iterations,
                player1_strategies=base_config.player1_strategies,
                player2_strategies=base_config.player2_strategies,
                metadata={**base_config.metadata, "episode": i}
            )

            try:
                yield self.run_episode(config)
            except Exception as e:
                logger.error(f"Error in episode {i}: {e}")
                # Continue with next episode

        logger.info(f"Completed {num_episodes} self-play episodes for game {base_config.game_id}")


def create_selfplay_runner_from_config(
    game_factory: Callable,
    apply_move_fn: Callable,
    build_state_fn: Callable,
    config: Dict[str, Any]
) -> SelfPlayRunner:
    """
    Factory function to create SelfPlayRunner from configuration dict.

    Args:
        game_factory: Function that creates a new game instance
        apply_move_fn: Function that applies a move to a game state
        build_state_fn: Function that converts game to generic state format
        config: Configuration dictionary with keys:
            - game_id: str
            - api_key: str (optional)
            - base_url: str (optional)
            - exploration_c: float (optional)
            - selection_strategy: str (optional)
            - expansion_strategy: str (optional)
            - simulation_strategy: str (optional)
            - backpropagation_strategy: str (optional)
            - queue_name: str (optional)

    Returns:
        Configured SelfPlayRunner instance
    """
    return SelfPlayRunner(
        game_factory=game_factory,
        apply_move_fn=apply_move_fn,
        build_state_fn=build_state_fn,
        game_id=config["game_id"],
        api_key=config.get("api_key", "selfplay"),
        base_url=config.get("base_url", "http://localhost:8000"),
        exploration_c=config.get("exploration_c", 1.4),
        selection_strategy=config.get("selection_strategy"),
        expansion_strategy=config.get("expansion_strategy"),
        simulation_strategy=config.get("simulation_strategy"),
        backpropagation_strategy=config.get("backpropagation_strategy"),
        queue_name=config.get("queue_name")
    )
